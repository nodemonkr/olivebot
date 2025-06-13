import discord
from discord.ext import commands
from core import attendance, bank, rank, info, admin, randombox, shop, quiz_event, bracket_event
import core.betting as betting
import core.stock as stock
from background_tasks import setup_background
import os
import asyncio
from keepalive import keep_alive

keep_alive()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 관리자 아이디 리스트
ADMIN_IDS = [1047192081828941845]


# @bot.event
# async def on_ready():
#     print(f"{bot.user} 봇이 로그인되었습니다!")
#     try:
#         synced = await bot.tree.sync()
#         print(f"슬래시 명령어 {len(synced)}개 동기화 완료!")
#     except Exception as e:
#         print(e)

# @bot.event
# async def on_ready():
#     print(f"✅ {bot.user} 로그인 완료!")

#     async def keep_active():
#         while True:
#             print("🟢 봇이 깨어 있습니다.")
#             await asyncio.sleep(60)

#     bot.loop.create_task(keep_active())
@bot.event
async def on_ready():
    print(f"✅ {bot.user} 로그인 완료!")

    try:
        await setup_background(bot)
        synced = await bot.tree.sync()
        print(f"🔁 슬래시 명령어 {len(synced)}개 동기화 완료!")
    except Exception as e:
        print("명령어 동기화 실패:", e)

    async def keep_active():
        while True:
            print("🟢 봇이 깨어 있습니다.")
            await asyncio.sleep(60)

    bot.loop.create_task(keep_active())

# 모듈별 슬래시 명령어 등록
attendance.setup(bot)
bank.setup(bot)
rank.setup(bot)
info.setup(bot, ADMIN_IDS)
admin.setup(bot, ADMIN_IDS)
quiz_event.setup(bot, ADMIN_IDS)
bracket_event.setup(bot, ADMIN_IDS)
# randombox.setup(bot)
stock.setup(bot)
betting.setup(bot)
shop.setup(bot)
bot.run(os.getenv("DISCORD_TOKEN_NEW"))
