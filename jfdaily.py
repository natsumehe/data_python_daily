import requests
import json
import re
from bs4 import BeautifulSoup
from datetime import datetime,timedelta
from typing import Union
import pandas as pd 

class Main():

    def __init__(self) -> None:
        pass

    def fetch(self, url) -> str:
        headers = {
            'accept':
            'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'user-agent': 'application/json, text/javascript, */*; q=0.01',
        }
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        r.encoding = r.apparent_encoding
        return r.text

    def getDailyNews(self) -> list[dict[str, Union[str, list[dict[str, str]]]]]:
        # # yyyy-mm-dd 格式化当天日期
        # formatted_date = datetime.now().strftime("%Y-%m-%d")

        current_date = datetime.now()

        formatted_date =current_date.strftime("%Y-%m-%d")
        naviUrl = f'https://www.shobserver.com/staticsg/data/journal/{formatted_date}/navi.json'
        

        try:
            naviData = json.loads(self.fetch(naviUrl))
            newsPages = naviData["pages"]
            print(f'「解放日报」正在处理 {formatted_date} 的 {len(newsPages)} 版新闻...')

            news = []
            for newsPage in newsPages:
                pageName = newsPage["pname"]
                pageNo = newsPage["pnumber"]
                articleList = newsPage["articleList"]
                print(
                    f'「解放日报」{pageNo} 版 - {pageName} 共有 {len(articleList)} 条新闻')
                for article in articleList:
                    title = article["title"]
                    subtitle = article["subtitle"]
                    aid = article["id"]

                    # 使用正则丢弃 title 含有广告的文章
                    if re.search(r'广告', title):
                        continue

                    articleContent, articlePictures = self.getArticle(
                        formatted_date, pageNo, aid)
                    news.append({
                        "id": f'{formatted_date}_{pageNo}-{aid}',
                        "title": title,
                        "subtitle": subtitle,
                        "content": articleContent,
                        "pictures": articlePictures
                    })

            return news

        except Exception as e:
            print(f'「解放日报」新闻列表获取失败！\n{e}')
            return []

    def getArticle(self, date, pageNo, aid) -> tuple[str, list[object]]:
        articleUrl = f'https://www.shobserver.com/staticsg/data/journal/{date}/{pageNo}/article/{aid}.json'

        articleData = json.loads(self.fetch(articleUrl))["article"]
        articleContent = BeautifulSoup(articleData["content"], 'html.parser')
        # 转换 <br> 为 \n
        for br in articleContent.find_all("br"):
            br.replace_with("\n")

        articlePictures = []
        articlePictureJson = json.loads(articleData["pincurls"])
        for articlePicture in articlePictureJson:
            url = articlePicture["url"]
            name = articlePicture["name"]
            author = articlePicture["author"]
            ttile = articlePicture["ttile"]
            articlePictures.append({
                "url": url,
                "alt": ttile,
                "title": ttile,
                "source": name,
                "author": author
            })

        print(
            f'「解放日报」已解析 {pageNo} 版 - {articleData["title"]} | 字数 {len(articleContent)} | 图片 {len(articlePictures)} 张'
        )
        return articleContent.get_text(), articlePictures

    
    def exportToExcel(self, news):
        data = {
            
             "ID": [],
             "title": [],
             # "副标题": [],
             "input_content": [],
             # "图片 URL": [],
             # "图片来源": [],
             # "图片作者": []
        }

        for article in news:
            data["ID"].append(article['id'])
            data["title"].append(article['title'])
            # data["副标题"].append(article["subtitle"])
            data["input_content"].append(article['content'])

               
        df = pd.DataFrame(data)
        df.to_excel("ceshi.xlsx", index=False)

jfdaily_spider = Main()

if __name__ == '__main__':
    spider = Main()
    news = spider.getDailyNews()
    spider.exportToExcel(news)
    print(news)