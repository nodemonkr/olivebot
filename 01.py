import discord
if not discord.opus.is_loaded():
    discord.opus.load_opus('libopus.so')
from discord.ext import commands
from core import attendance, bank, rank, info, admin, randombox, shop, music, quiz_event, bracket_event
import core.betting as betting
from keepalive import keep_alive

keep_alive()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 관리자 아이디 리스트
ADMIN_IDS = [1047192081828941845]


@bot.event
async def on_ready():
    print(f"{bot.user} 봇이 로그인되었습니다!")
    try:
        synced = await bot.tree.sync()
        print(f"슬래시 명령어 {len(synced)}개 동기화 완료!")
    except Exception as e:
        print(e)


# 모듈별 슬래시 명령어 등록
attendance.setup(bot)
bank.setup(bot)
rank.setup(bot)
info.setup(bot, ADMIN_IDS)
admin.setup(bot, ADMIN_IDS)
quiz_event.setup(bot, ADMIN_IDS)
bracket_event.setup(bot, ADMIN_IDS)
# randombox.setup(bot)
betting.setup(bot)
shop.setup(bot)
music.setup(bot)
bot.run(
    "MTM4MTU5OTQxODY0NTQ4MzYwMA.GJneep.EoJkqnpa7wmjtZ2bodIrcZBs00snwE0lxpkk5w")
