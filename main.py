from requests import (
    get_x_page_id, get_base_url, get_link_id,
    get_all_files,
    download_file, remove_from_uri_filename
)

links_file = 'links.txt'

with open(links_file, "r") as file:
    links = [line.strip() for line in file if line.strip().startswith("http")]

for link in links:
    link_id = get_link_id(link)
    if not link_id:
        continue

    x_page_id = get_x_page_id(link)
    base_url = get_base_url(x_page_id)
    files = get_all_files(link_id, x_page_id, base_url)

    count_files = len(files)
    if count_files == 0:
        continue

    if count_files == 1:
        uri, out, filename = files[0].values()
        uri = remove_from_uri_filename(uri, filename)
        download_file(uri, out, filename)
    else:
        for file in files:
            uri, out, filename = file.values()
            download_file(uri, out, filename)
