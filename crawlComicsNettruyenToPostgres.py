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

class Comic:
    def __init__(self, crawl_id="", title="", thumbnails="", description="", chapter_id="", count_chapter=0) -> None:
        self.crawl_id = crawl_id
        self.title = title
        self.thumbnails = thumbnails
        self.description = description
        self.chapter_id = chapter_id
        self.count_chapter = count_chapter
        pass

def crawlComics():
    # open website
    reponse = openWebsite(nettruyen)
    dom = etree.HTML(reponse.text)
    elements = dom.xpath("//div[contains(@class,'item')]")

    comics = []
    for c in elements:
        comic = Comic()

        if c[0].tag == "figure":
            # Áp dụng biểu thức chính quy để cắt chuỗi để lấy crawl_id
            match = re.search(r"/([^/]+)$", c[0][0][0].get("href"))
            if match:
                # crawl_id = match.group(1)
                comic.crawl_id = match.group(1)

            comic.thumbnails = "https:" + c[0][0][0][0].get("data-original")
            comic.title = c[0][1][0][0].text
            comic.chapter_id = c[0][1][1].get("data-id")

            if c[1][0][2].get("class") == "box_text":
                comic.description = c[1][0][2].text

            # Lấy số lượng chapter - không chính xác
            matchChapter = re.search(r"(\d+)$", c[0][1][1][0][0].get("title"))
            if matchChapter:
                comic.count_chapter = matchChapter.group(1)

            comics.append(comic)
    return comics


def updateComics():
    # Thực hiện truy vấn SELECT
    # cursor.execute("SELECT * FROM auth.users")
    # rows = cursor.fetchall()

    # In kết quả
    # for row in rows:
    #     print(row)

    # crawl dữ liệu
    comics = crawlComics()

    # Thêm dữ liệu truyện tranh vào db
    for comic in comics:
        # insert crawls
        cursor.execute("INSERT INTO public.crawls(crawl_id, chapter_id, count_chapter) "
                       "VALUES (%s, %s, %s) ON CONFLICT (crawl_id) DO NOTHING", # Đảm bảo các dữ liệu thêm vào không bị trùng lặp
                       (comic.crawl_id, comic.chapter_id, comic.count_chapter))
        # Đảm bảo lưu thay đổi vào cơ sở dữ liệu
        connection.commit()
        # Lấy giá trị ID mới nhất bằng cách thực hiện một câu lệnh SELECT
        # cursor.execute("SELECT lastval()")
        # crawl_id = cursor.fetchone()[0]

        # Thực hiện một câu lệnh SELECT để lấy crawl_id
        cursor.execute("SELECT id FROM public.crawls WHERE crawl_id = %s",
                       (comic.crawl_id,))
        result = cursor.fetchone()

        if result is not None:
            crawl_id = result[0] # fk id
            # Kiểm tra xem crawl_id đã tồn tại trong bảng comics hay chưa
            cursor.execute("SELECT id, count_chapter FROM public.comics WHERE crawl_id = %s",
                           (crawl_id,))

            existing_comic = cursor.fetchone()

            if existing_comic is None:
                # insert comics
                cursor.execute("INSERT INTO public.comics(uid, title, description, thumbnails, crawl_id, count_chapter, slug) "
                               "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                               ('a34c55c4-9f04-490f-a876-8e5da1acc50b', comic.title, comic.description, comic.thumbnails, crawl_id, comic.count_chapter, slugify(comic.title)))
                # Đảm bảo lưu thay đổi vào cơ sở dữ liệu
                connection.commit()

                if cursor.rowcount > 0:
                    print("Insertion successful")
                else:
                    print("Insertion failed")
            else:
                # Nếu đã tồn tại thì kiểm tra xem số lượng count chapter có thay đổi hay không?
                # Nếu thay đổi thì cập nhật số lượng count chapter mới và trạng thái update thành true
                comic_id = existing_comic[0]
                count_chapter = existing_comic[1]
                if int(count_chapter) != int(comic.count_chapter):
                    cursor.execute("UPDATE public.comics SET is_updated = true, count_chapter = %s WHERE id = %s", (comic.count_chapter, comic_id,))
                    # Đảm bảo lưu thay đổi vào cơ sở dữ liệu
                    connection.commit()
                    print(f"count chapter on change: {count_chapter} to {comic.count_chapter}")

                print("comic with crawl_id already exists, skipping insertion")

    return

updateComics()