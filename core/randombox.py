import discord
from discord import app_commands
from core.utils import load_data, save_data
import random

def setup(bot):
    @bot.tree.command(name="랜덤박스", description="랜덤박스를 열어 올리브를 얻습니다.")
    async def 랜덤박스(interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        data = load_data()
        data.setdefault(user_id, {"olive": 0, "last_check": ""})
        reward = random.choice([0, 50, 100, 200, 500])
        data[user_id]["olive"] += reward
        save_data(data)
        if reward == 0:
            await interaction.response.send_message(f"{interaction.user.mention} 😢 꽝이에요!", ephemeral=True)
        else:
            await interaction.response.send_message(f"{interaction.user.mention} 🎉 랜덤박스에서 🌿 {reward} 올리브 획득!")
