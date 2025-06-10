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
