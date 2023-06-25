from nonebot import on_command
from nonebot.rule import to_me
from nonebot.params import *

news = on_command("新闻", rule=to_me(), aliases={"找乐子", "热点"}, priority=10)


@news.handle()
async def handle_news_function(matcher: Matcher, args: Message = CommandArg()):
    if args.extract_plain_text():
        matcher.set_arg("location", args)


@news.got("location", prompt="请输入地名")
async def got_location(location: str = ArgPlainText()):
    await news.finish(f"今天{location}的天气是...")
