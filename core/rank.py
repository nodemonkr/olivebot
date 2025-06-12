import discord
from discord.ext import commands
from discord import app_commands
from core.utils import load_data

def setup(bot: commands.Bot):
    @bot.tree.command(name="랭킹", description="올리브 랭킹 상위 10명을 보여줍니다.")
    async def 랭킹(interaction: discord.Interaction):
        data = load_data()
        sorted_users = sorted(data.items(), key=lambda x: x[1].get("olive", 0), reverse=True)
        message = "🏆 올리브 랭킹 Top 10\n"

        for i, (user_id, user_data) in enumerate(sorted_users[:10], start=1):
            try:
                member = interaction.guild.get_member(int(user_id)) or await interaction.guild.fetch_member(int(user_id))
                name = member.display_name
            except:
                name = f"알 수 없음 ({user_id})"

            olive = user_data.get("olive", 0)
            message += f"{i}위: {name} - 🌿 {olive}개 올리브\n"

        await interaction.response.send_message(message)
