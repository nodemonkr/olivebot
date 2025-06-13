import asyncio
import discord
import re
import pytz
from discord.ext import tasks
from discord import TextChannel
import json, os
from datetime import datetime
from core.stock import update_stock_prices  # 수동 명령어와 동일한 함수 재사용
from discord import Embed

NEWS_FILE = "data/news_data.json"
STOCK_FILE = "data/stock_data.json"

# 서버와 채널 ID는 실제 값으로 설정
GUILD_ID = 1341012555174383637
CHANNEL_ID = 1382459782933381261

client: discord.Client = None



def load_json(path, default={}):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=2)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@tasks.loop(minutes=1)
async def auto_market_update_task():
    global last_market_message
    result = update_stock_prices()

    channel = client.get_channel(1382552491736174682)
    if channel and result:
        # 이전 메시지 삭제 시도
        try:
            if last_market_message:
                await last_market_message.delete()
        except Exception as e:
            print(f"❌ 이전 메시지 삭제 실패: {e}")

        display_lines = []

        for line in result:
            # 상승/하락률 추출 및 이모지 변환
            match = re.search(r"\(([-+]?[\d.]+%)\)", line)
            if match:
                raw = match.group(1)
                percent = raw.lstrip("+-")

                if raw.startswith("+"):
                    icon = "🔺"
                elif raw.startswith("-"):
                    icon = "🔻"
                else:
                    icon = "⏸️"

                line = line.replace(f"({raw})", f"{icon} ({percent})")
            else:
                line = f"⏸️ {line}"

            # 🫒 숫자개 → 🫒숫자개
            line = re.sub(r": (\d+)", r": 🫒\1개", line)
            line = re.sub(r"→ (\d+)", r"→ 🫒\1개", line)

            display_lines.append(line)

        # 한국 시간 기준 시각 생성
        kst = pytz.timezone("Asia/Seoul")
        now = datetime.now(kst)
        time_str = now.strftime("%Y-%m-%d %H:%M:%S")

        embed = Embed(
            title="📈 올리브 주식 시장 자동 갱신",
            description="\n".join(display_lines),
            color=0x2ecc71
        )
        embed.set_footer(text=f"자동 갱신 시각: {time_str} (KST)")

        # 새 메시지 전송 및 참조 저장
        last_market_message = await channel.send(embed=embed)
@tasks.loop(minutes=1)
async def news_broadcast_task():
    news = load_json(NEWS_FILE)
    stocks = load_json(STOCK_FILE)
    today = datetime.now().strftime("%Y-%m-%d")

    guild = client.get_guild(GUILD_ID)
    channel = guild.get_channel(CHANNEL_ID)
    any_sent = False

    for name, news_list in news.items():
        for item in news_list:
            if not item.get("applied") and item["date"] <= today:
                try:
                    msg = f"📰 **{name}** 뉴스 속보!\n{item['content']}"
                    await channel.send(msg)

                    # ✅ 뉴스 영향도에 따라 추세 적용
                    influence = item["influence"]
                    trend = (
                        "up" if influence >= 4
                        else "down" if influence <= 2
                        else stocks[name].get("trend", "up")
                    )
                    stocks[name]["trend"] = trend

                    item["applied"] = True
                    any_sent = True
                    break  # 종목당 하루 1개 뉴스만

                except Exception as e:
                    print(f"❌ 뉴스 전송 실패: {name} - {e}")

    if any_sent:
        save_json(NEWS_FILE, news)
        save_json(STOCK_FILE, stocks)

async def setup_background(bot_client):
    global client
    client = bot_client
    news_broadcast_task.start()
    auto_market_update_task.start()