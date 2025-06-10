import discord
from discord import app_commands
from datetime import datetime
from core.utils import load_data, save_data


def setup(bot):

    @bot.tree.command(name="출석", description="오늘 출석 체크를 합니다.")
    async def 출석(interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        display_name = interaction.user.display_name  # 서버 프로필명
        today = datetime.now().strftime("%Y-%m-%d")
        data = load_data()

        if user_id not in data:
            data[user_id] = {
                "olive": 0,
                "last_check": "",
                "display_name": display_name
            }
        else:
            data[user_id]["display_name"] = display_name  # 항상 최신 이름 저장

        if data[user_id]["last_check"] == today:
            await interaction.response.send_message(
                f"{interaction.user.mention} 오늘은 이미 출석했어요!", ephemeral=True)
        else:
            data[user_id]["last_check"] = today
            data[user_id]["olive"] += 100
            save_data(data)
            await interaction.response.send_message(
                f"{interaction.user.mention} 출석 완료! 🌿 올리브 100개 지급!")
