import requests
from bs4 import BeautifulSoup
import re 
from datetime import datetime,timedelta
import pandas as pd 


data = {
    "ID": [],
    "title": [],
    "input_content": [],
}

#更改这里的数据即可，这里的数据主要是爬取网页的数量，不是最终的数据。
#最终的数据<=count*8*2
Count = 365 *5
Current = datetime.now()
counts = timedelta(days=Count)
past = Current - counts
while past <= Current:
    
    past += timedelta(days=1)
    formatted_date =past.strftime("%Y-%m/%d")
    print("time",formatted_date)
    
    naviurl = f"http://digitalpaper.stdaily.com/http_www.kjrb.com/kjrb/html/{formatted_date}/node_2.htm"
    naviresponse = requests.get(naviurl)
    html = naviresponse.content.decode("utf-8", errors="ignore")
    navisoup = BeautifulSoup(html, 'lxml')

    navi_content = navisoup.find("div" ,class_="bmname")
    if navi_content is not None:
        navi_content = navisoup.find("div" ,class_="bmname").text.strip()
        
    

    keywords = ["今日要闻", "要 闻", "理 论", "园 区", "教 育", "深 瞳", "视 点", "区 域", "广 告", "军 事", "特 刊", "综 合"]

    all_links = navisoup.find("div" ,class_="bmname")
    if all_links is not None:
        all_links = navisoup.find("div" ,class_="bmname").find_all("a")

    if all_links is not None:
        filtered_links = [(link["href"]) for link in all_links if not any(exclude_word in link.text for exclude_word in keywords)]
        
        for i in filtered_links:
            url = f"http://digitalpaper.stdaily.com/http_www.kjrb.com/kjrb/html/{formatted_date}/{i}"

            urlresponse = requests.get(url)
            html = urlresponse.content.decode("utf-8", errors="ignore")
            soup = BeautifulSoup(html, 'lxml')

            pattern = re.compile('.*content.*div.*')
            for a_tag in soup.find_all('a'):
                href = a_tag.get('href')
                if re.match(pattern, href):
                    start = href.find("_") + 1
                    end = href.find(".")
                    number = href[start:end]
                

                    articleUrl = f'http://digitalpaper.stdaily.com/http_www.kjrb.com/kjrb/html/{formatted_date}/{href}'
            
                    response = requests.get(articleUrl)
                    html_content = response.content.decode("utf-8", errors="ignore")
                    soup = BeautifulSoup(html_content, 'lxml')

                    title = soup.find('div', class_='biaoti')
                    if title is not  None:
                        title = soup.find('div', class_='biaoti').text.strip()

                    content = soup.find('div', class_='article')
                    if content is not None:
                        content = soup.find('div', class_='article').get_text(strip=True)
                        pattern = r'^广 告'
                        content_no_ads = re.sub(pattern, '', content)
                        
                        
                    data["ID"].append(formatted_date + "_" + number)
                    data["title"].append(title)
                    data["input_content"].append(content)

                # print(formatted_date + "_" + number)

                # print("标题：", title)
                # print("内容：", content)

        df = pd.DataFrame(data)
        df.to_excel("keji.xlsx", index=False)
        df_from_excel = pd.read_excel("keji.xlsx")
        num_rows = df_from_excel.shape[0]

print(f'科技日报爬取完成，共爬取【{num_rows}】条数据')
