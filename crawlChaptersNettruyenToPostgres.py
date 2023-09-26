import os
from dotenv import load_dotenv

import requests
from lxml import etree
import re
from postgres import cursor, connection
from slugify import slugify

load_dotenv()

# --------------------------
# link đến trang hình ảnh của chapter
nettruyen = os.getenv("PUBLIC_NETTRUYEN_URL")

def openWebsite(domain: str):
    headersList = {
    "Accept": "*/*",
    "User-Agent": "Thunder Client (https://www.thunderclient.com)"
    }
    response = requests.request("GET", domain, data="",  headers=headersList)
    return response

def crawlChapters(crawl_id: str):
    # crawl_id là id của truyện tranh để truy vấn và lấy ra danh sách chhapter
    # Gọi api domain lấy danh sách chương
    response = openWebsite(nettruyen + "Comic/Services/ComicService.asmx/ProcessChapterList?comicId=" + crawl_id)

    return response.json()  # Assuming the response is in JSON format

def updateChapter(comic_id: str, crawl_id: str):
    # comic_id : id cua table comics, crawl_id : chapter_id cua table crawls
    # Thu thập dữ liệu
    data = crawlChapters(crawl_id)

    if len(data['chapters']):
        for chap in data['chapters']:
            # Thêm dữ liệu vào db
            cursor.execute("INSERT INTO public.chapters(comic_id, title, crawl_id) "
                           "VALUES (%s, %s, %s) ON CONFLICT (crawl_id) DO NOTHING",
                           # Đảm bảo các dữ liệu thêm vào không bị trùng lặp
                           (comic_id, chap['name'], chap['url']))
            # Đảm bảo lưu thay đổi vào cơ sở dữ liệu
            connection.commit()

            # print("Thêm chapter vào db thành công:")
            print(chap['name'])

        # set is_updated comics = false
        cursor.execute("UPDATE public.comics SET is_updated = false WHERE id = %s", (comic_id,))
        connection.commit()
        cursor.execute("UPDATE public.crawls SET is_updated = false WHERE chapter_id = %s", (crawl_id,))
        connection.commit()
    return

# func auto update
def autoUpdateChapter():
    # Lấy danh sách truyện
    cursor.execute("SELECT id, crawl_id FROM public.comics WHERE is_updated = true ORDER BY id ASC limit 5")
    results = cursor.fetchall()

    if results is not None:
        for row in results:
            comic_id = row[0] # id cua truyen tranh
            crawl_id = row[1] # crawl id fk id cua comic
            cursor.execute("SELECT chapter_id FROM public.crawls WHERE id = %s", (crawl_id,))
            crawlResult = cursor.fetchone()

            if crawlResult is not None:
                updateChapter(comic_id, crawlResult[0])

    return

autoUpdateChapter()