import discord
from discord import app_commands
from core.utils import load_data

def setup(bot, ADMIN_IDS):
    @bot.tree.command(name="정보", description="본인 또는 다른 유저의 정보를 봅니다.")
    @app_commands.describe(user="정보를 볼 유저 (관리자만 가능)")
    async def 정보(interaction: discord.Interaction, user: discord.Member = None):
        requester_id = interaction.user.id
        target = user or interaction.user
        if user and requester_id not in ADMIN_IDS:
            await interaction.response.send_message("다른 유저 정보를 보려면 관리자여야 합니다.", ephemeral=True)
            return
        data = load_data()
        user_id = str(target.id)
        user_data = data.get(user_id, {"olive": 0, "last_check": "없음"})
        msg = (
            f"📄 {target.display_name}님의 정보\n"
            f"- 🌿 올리브: {user_data.get('olive', 0)}개\n"
            f"- 마지막 출석일: {user_data.get('last_check', '없음')}"
        )
        await interaction.response.send_message(msg, ephemeral=True)


    @bot.tree.command(name="명령어", description="사용 가능한 슬래시 명령어 목록을 보여줍니다.")
    async def 명령어(interaction: discord.Interaction):
        # 기본 명령어 embed
        기본 = discord.Embed(title="📘 기본 기능", color=0x3498db)
        기본.add_field(name="/출석", value="오늘 출석 체크를 합니다.", inline=False)
        기본.add_field(name="/올리브", value="내 올리브 잔액을 확인합니다.", inline=False)
        기본.add_field(name="/송금", value="다른 유저에게 올리브를 송금합니다.", inline=False)
        기본.add_field(name="/상점", value="올리브로 구매 가능한 아이템 목록을 확인합니다.", inline=False)
        기본.add_field(name="/랭킹", value="올리브 랭킹 상위 10명을 보여줍니다.", inline=False)
        기본.add_field(name="/정보", value="본인 또는 다른 유저의 정보를 봅니다.", inline=False)

        # 도박 embed
        도박 = discord.Embed(title="🎲 도박 기능", color=0xe67e22)
        도박.add_field(name="/도박", value="올리브를 걸고 도박을 합니다.", inline=False)
        도박.add_field(name="/대결", value="상대와 올리브를 걸고 대결을 신청합니다.", inline=False)
        도박.add_field(name="/대결수락", value="상대방의 대결 신청을 수락합니다.", inline=False)
        도박.add_field(name="/대결거절", value="상대방의 대결 신청을 거절합니다.", inline=False)

        # 주식 embed
        주식 = discord.Embed(title="📈 주식 기능", color=0x2ecc71)
        주식.add_field(name="/주식구매", value="주식을 구매합니다.", inline=False)
        주식.add_field(name="/주식판매", value="보유한 주식을 판매합니다.", inline=False)
        주식.add_field(name="/주식종목", value="상장중인 종목들을 확인합니다.", inline=False)
        주식.add_field(name="/포트폴리오", value="내 주식 보유 현황을 확인합니다.", inline=False)
        주식.add_field(name="/보유종목", value="자신이 보유한 주식을 확인합니다.", inline=False)
        주식.add_field(name="/주식왕", value="수익률 기준 주식 랭킹을 보여줍니다.", inline=False)

        await interaction.response.send_message(embeds=[기본, 도박, 주식])
