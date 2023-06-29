from nonebot import require
from nonebot_plugin_apscheduler import scheduler
from nonebot import on_command
from nonebot.rule import to_me
import requests
from bs4 import BeautifulSoup
from nonebot.params import *
from nonebot.adapters.onebot.v11 import MessageSegment

require("nonebot_plugin_apscheduler")

tieba_news = on_command("贴吧", rule=to_me(), aliases={"找乐子", "热点"}, priority=10)
topic_urls = []
topics = []
page_dics_list = []


def get_html(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        return response.text
    except:
        raise Exception


def tieba_topic_spider():
    url = "http://c.tieba.baidu.com/hottopic/browse/topicList?res_type=1"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36 Edg/96.0.1054.62'
    }
    html = get_html(url, headers)
    soup = BeautifulSoup(html, "html.parser")
    topics = []
    topics_urls = []
    for m in soup.find_all(class_='topic-text'):
        topics.append(m.get_text().strip())
        topics_urls.append(m['href'])
    return topics, topics_urls


def tieba_page_spider(url, num=5):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36 Edg/96.0.1054.62'
    }
    sub_soup = BeautifulSoup(get_html(url, headers), "html.parser")
    sub_pages = []
    count = 0
    for m in sub_soup.find_all(class_="thread-item"):
        count += 1
        if count == num:
            break
        reply_num = m.find_next(class_="reply-num").text
        title = m.find_next(class_="title track-thread-title").text
        title_url = "https://tieba.baidu.com" + m.find_next(class_="title track-thread-title")["href"]
        content = m.find_next(class_="content").text
        images_urls = []
        images = m.find_next(class_="photo-wrapper")
        if images is not None:
            for image in images.find_all("img"):
                images_urls.append(image["src"])
        forum_name = m.find_next(class_="forum-name").text
        sub_page = {"title": title, "title_url": title_url, "content": content, "images_urls": images_urls,
                    "forum_name": forum_name, "reply_num": reply_num}
        sub_pages.append(sub_page)
    return sub_pages


def tieba_prompt():
    global topics, topic_urls
    msg = "请输入你感兴趣的🌶️新闻的编号:\n"
    if topics is None or topic_urls is None or len(topics) == 0 or len(topic_urls) == 0:
        topics, topic_urls = tieba_topic_spider()
    for i in range(0, len(topics)):
        if i != len(topics) - 1:
            msg += f"{i + 1}. {topics[i]}\n"
        else:
            msg += f"{i + 1}. {topics[i]}"
    return msg


@tieba_news.got("index", prompt=tieba_prompt())
async def handle_function(index: str = ArgPlainText()):
    if not index.isnumeric():
        await tieba_news.reject("请重新输入数字（仅数字即可）")
    else:
        index = int(index)
    global page_dics_list
    if page_dics_list is None or len(page_dics_list) == 0:
        dic_list = tieba_page_spider(topic_urls[index - 1])
    else:
        dic_list = page_dics_list[index - 1]

    for i in range(0, len(dic_list)):
        ret_msg = "标题：" + dic_list[i]["title"] + "\n"
        for image_url in dic_list[i]["images_urls"]:
            ret_msg += MessageSegment.image(image_url)
        ret_msg += f"\n正文：{dic_list[i]['content']} \n评论数：{dic_list[i]['reply_num']} 来自：{dic_list[i]['forum_name']} " \
                   f"\n链接：{dic_list[i]['title_url']}"
        if i != len(dic_list) - 1:
            await tieba_news.send(ret_msg)
        else:
            await tieba_news.finish(ret_msg)


@scheduler.scheduled_job("interval", minutes=30, id="job_0")
async def run_every_30_mins():
    global topics, topic_urls, page_dics_list
    topics, topic_urls = tieba_topic_spider()
    # print(topics)
    for i in range(0, 30):
        page_dics_list.append(tieba_page_spider(topic_urls[i]))


@scheduler.scheduled_job("interval", minutes=15, id="job_1")
async def clear_every_15_mins():
    global topics, topic_urls, page_dics_list
    topics = []
    topic_urls = []
    page_dics_list = []
