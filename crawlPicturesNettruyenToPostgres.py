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

def crawlPicture(crawl_id: str):
    # open website
    reponse = openWebsite(nettruyen + crawl_id)
    dom = etree.HTML(reponse.text)
    elements = dom.xpath("//div[contains(@class,'page-chapter')]")

    photos = []
    for e in elements:
        if e[0].tag == "img":
            photos.append({
                "title": e[0].get("alt"),
                "url": "https:" + e[0].get("src")
            })
    return photos

def updatePhotos(chapter_id: str, crawl_id: str):
    # crawl dữ liệu
    photos = crawlPicture(crawl_id)

    # Thêm hình ảnh vào db
    if photos:
        for img in photos:
            # Thêm dữ liệu vào db
            cursor.execute("INSERT INTO public.photos(chapter_id, title, url) "
                           "VALUES (%s, %s, %s) ON CONFLICT (url) DO NOTHING",
                           # Đảm bảo các dữ liệu thêm vào không bị trùng lặp
                           (chapter_id, img["title"], img["url"]))
            # Đảm bảo lưu thay đổi vào cơ sở dữ liệu
            connection.commit()

            print("Thêm hình ảnh vào db thành công: " + img["title"])

        # set is_updated cua table chapters thanh false
        cursor.execute("UPDATE public.chapters SET is_updated = false WHERE id = %s", (chapter_id,))
        connection.commit()

    return

def autoUpdatePicture():
    # Lấy danh sách chapter từ supabase
    # data = supabase.table("chapters").select("id,crawl_id,is_update").eq("is_update", True).range(0, 10).execute()
    cursor.execute("SELECT id, crawl_id FROM public.chapters WHERE is_updated = true ORDER BY id ASC limit 5")
    results = cursor.fetchall()

    if results is not None:
        for row in results:
            chapter_id = row[0]
            crawl_id = row[1]
            updatePhotos(chapter_id, crawl_id)

    # updatePhotos("89", "/truyen-tranh/ta-khong-muon-lam-de-nhat/chap-187/1058120")

    return

autoUpdatePicture()
