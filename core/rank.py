import discord
from discord.ext import commands
from discord import app_commands
from core.utils import load_data
import asyncio

def setup(bot: commands.Bot):
    @bot.tree.command(name="랭킹", description="올리브 랭킹 Top 10")
    async def 랭킹(interaction: discord.Interaction):
        await interaction.response.defer()

        data = load_data()
        sorted_users = sorted(data.items(), key=lambda x: x[1].get("olive", 0), reverse=True)[:10]

        async def get_name(user_id):
            try:
                member = interaction.guild.get_member(int(user_id))
                if member:
                    return member.display_name
                member = await interaction.guild.fetch_member(int(user_id))
                return member.display_name
            except:
                return f"유저({user_id})"

        names = await asyncio.gather(*(get_name(uid) for uid, _ in sorted_users))

        message = "🏆 올리브 랭킹 Top 10\n"
        for i, ((uid, udata), name) in enumerate(zip(sorted_users, names), start=1):
            olive = udata.get("olive", 0)
            message += f"{i}위: {name} - 🌿 {olive}개 올리브\n"

        await interaction.followup.send(message)
