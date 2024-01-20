from requests import get_x_page_id, get_base_url, get_all_files, get_link_id, download_file, uri_one_file

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

    for file in files:
        uri, out, filename = file.values()
        uri = uri_one_file(uri, filename, count_files)
        download_file(uri, out, filename)
