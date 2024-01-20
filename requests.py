import logging
import os
import re
import time
from typing import Union
from urllib.parse import quote
from fake_useragent import UserAgent

import httpx
from tqdm import tqdm

BASE_API_URL = 'https://cloud.mail.ru/api/v2/'
DOWNLOAD_FOLDER = "Downloads"
MAX_RETRY = 5

ua = UserAgent()

headers = {
    'User-Agent': ua.random,
}


def download_file(link: str, output_path: str, filename: str, retry: int = MAX_RETRY) -> bool:
    try:
        file_path = os.path.join(DOWNLOAD_FOLDER, output_path, filename)

        with httpx.stream("GET", link, follow_redirects=True, headers=headers) as response:
            os.makedirs(os.path.join(DOWNLOAD_FOLDER, output_path), exist_ok=True)

            total_size = int(response.headers.get("content-length", 0))

            if total_size == 0:
                if retry > 0:
                    time_sleep = (MAX_RETRY - retry + 1) * 60
                    logging.warning(f"Sleep for {time_sleep} s")
                    time.sleep(time_sleep)
                    return download_file(link, output_path, filename, retry - 1)
                else:
                    raise Exception("Zero file size")

            if os.path.exists(file_path):
                downloaded_size = os.path.getsize(file_path)
                if downloaded_size == total_size:
                    logging.warning(f"File {filename} already fully downloaded.")
                    return True

            progress_bar = tqdm(total=total_size, unit='B', unit_scale=True)

            with open(file_path, 'wb') as file:
                for data in response.iter_raw():
                    file.write(data)
                    progress_bar.update(len(data))

            progress_bar.close()
            progress_bar.clear()

        return True
    except Exception as e:
        logging.error(f"Failed to download {link}: {e}")
        return False


def get_link_id(url: str) -> Union[str, bool]:
    match = re.search(r'https://cloud\.mail\.ru/public/(.+)', url)
    if not match:
        logging.error(f"Wrong link {url}")

    return match.group(1) if match else False


def get_x_page_id(url: str) -> Union[str, bool]:
    r = httpx.get(url, follow_redirects=True)
    match = re.search(r'pageId[\'"]*:[\'"]*([^"\'\s,]+)', r.text, re.S)
    return match.group(1) if match else False


def get_base_url(x_paid_id: str) -> Union[str, bool]:
    url = f'{BASE_API_URL}dispatcher?x-page-id={x_paid_id}'
    json_result = httpx.get(url, follow_redirects=True, headers=headers).json()

    try:
        weblink_get_list = json_result['body']['weblink_get']
        if isinstance(weblink_get_list, list) and weblink_get_list:
            return weblink_get_list[0]['url']
        else:
            logging.error('Unexpected response structure.')
            return False
    except KeyError as err:
        logging.error(f'Error occurred:{err}')
        return False
    except TypeError as err:
        logging.error(f'TypeError occurred:{err}')
        return False


def get_all_files(weblink: str, x_page_id: str, base_url: str, folder: str = '') -> Union[list, bool]:
    url = f'{BASE_API_URL}folder?weblink={weblink}&x-page-id={x_page_id}'
    json_result = httpx.get(url, follow_redirects=True, headers=headers).json()

    files = []
    folder = os.path.join(folder, json_result['body']['name'])

    try:
        item_list = json_result['body']['list']
    except KeyError as err:
        logging.error(f'Error occurred:{err}')
        return False
    except TypeError as err:
        logging.error(f'TypeError occurred:{err}')
        return False

    for item in item_list:
        if item['type'] == 'folder':
            new_weblink = f'{weblink}/{quote(item["name"])}'
            files_from_folder = get_all_files(new_weblink, x_page_id, base_url, folder)
            files.extend(files_from_folder)
        elif item['type'] == 'file':
            file_output = folder if folder != "/" else ""
            download_url = f'{base_url}/{weblink}/{quote(item["name"])}' if base_url else None
            files.append({"link": download_url, "output": file_output, "filename": item["name"]})

    if len(files) == 0:
        logging.warning(f"No files found for {weblink}")

    return files


def remove_from_uri_filename(uri: str, filename: str) -> str:
    return uri.replace('/' + quote(filename), '')
