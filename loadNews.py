# _*_ coding: utf-8 _*_

import psycopg2 as pg2
import requests
import re
import os
from bs4 import BeautifulSoup, Comment
from shutil import rmtree

USER_AGENT = 'Mozilla/5.0'
BASE_DIR = "./articles"
ORIGIN_PATH = os.path.join(BASE_DIR, 'Origin-Data')
NAVER_NEWS_URL_REGEX = "https?://news.naver.com"

def mkdir_p(path):
    import errno
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def del_folder(path):
    try:
        rmtree(path)
    except:
        pass

def get_article_list_fromDB():
    conn = None
    article_list = []
    try:
        conn = pg2.connect(host='localhost', dbname='newsdb', user='subinkim', password='123', port='5432')  # db에 접속
        cur = conn.cursor()

        cur.execute("SELECT title, url, media FROM news_list;")
        rows = cur.fetchall()
        for row in rows:
            article_list.append(dict(title=row[0], url=row[1], media=row[2]))

    except (Exception, pg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
    return article_list


def get_text_without_children(tag):
    return ''.join(tag.find_all(text=True, recursive=False)).strip()


def parse_article_content(article_html, tag, id):
    content = ''

    div = article_html.find(tag, id=id)
    if div is None :
        raise Exception("Page Not Found")

    for element in div(text=lambda text: isinstance(text, Comment)):
        element.extract()

    divs = article_html.find_all(tag, {"id": id})

    for i in divs:
        content += get_text_without_children(i)

    return content


def save_article_content_txt(title, content, media):

    path = os.path.join(ORIGIN_PATH, media)
    mkdir_p(path)

    files = os.listdir(path)

    f = open(os.path.join(path, str(len(files)) + ".txt"), 'w', -1, "utf-8")
    f.write(title)
    f.write(content)
    f.write(media)
    f.close()


def get_article_content():
    article_list = get_article_list_fromDB()

    for article_no, article in enumerate(article_list):
        article_page_response = requests.get(article['url'], headers={'User-Agent': USER_AGENT})
        article_html = BeautifulSoup(article_page_response.text, "html.parser")

        url = article_html.find('meta', property='og:url')

        if re.match(NAVER_NEWS_URL_REGEX, url['content']) is None: continue
        print(url['content'])

        try :
            content = parse_article_content(article_html, 'div', 'articleBodyContents')
            save_article_content_txt(article['title'], content, article['media'])
        except Exception as e:
            print(e)
            pass

if __name__ == "__main__":
    del_folder(ORIGIN_PATH)
    mkdir_p(ORIGIN_PATH)

    get_article_content()

