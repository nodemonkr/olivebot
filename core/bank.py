import discord
from discord import app_commands
from discord.ext import commands
from core.utils import load_data, save_data


def setup(bot):
    # @bot.tree.command(name="입금", description="올리브를 입금합니다.")
    @app_commands.describe(amount="입금할 올리브 개수")
    async def 입금(interaction: discord.Interaction, amount: int):
        user_id = str(interaction.user.id)
        data = load_data()
        data.setdefault(user_id, {"olive": 0, "last_check": ""})
        data[user_id]["olive"] += amount
        save_data(data)
        await interaction.response.send_message(
            f"{interaction.user.mention} 🌿 올리브 {amount}개 입금 완료!")

    # @bot.tree.command(name="출금", description="올리브를 출금합니다.")
    @app_commands.describe(amount="출금할 올리브 개수")
    async def 출금(interaction: discord.Interaction, amount: int):
        user_id = str(interaction.user.id)
        data = load_data()
        data.setdefault(user_id, {"olive": 0, "last_check": ""})
        if data[user_id]["olive"] < amount:
            await interaction.response.send_message(
                f"{interaction.user.mention} 올리브가 부족합니다!", ephemeral=True)
        else:
            data[user_id]["olive"] -= amount
            save_data(data)
            await interaction.response.send_message(
                f"{interaction.user.mention} 🌿 올리브 {amount}개 출금 완료!")

    @bot.tree.command(name="올리브", description="내 올리브 잔액을 확인합니다.")
    async def 올리브(interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        data = load_data()
        olive = data.get(user_id, {}).get("olive", 0)
        await interaction.response.send_message(
            f"{interaction.user.mention}님의 올리브 잔액은 🌿 {olive}개입니다.")

    @bot.tree.command(name="송금", description="다른 유저에게 올리브를 송금합니다.")
    @app_commands.describe(user="송금할 대상", amount="송금할 올리브 개수")
    async def 송금(interaction: discord.Interaction, user: discord.Member,
                 amount: int):
        sender_id = str(interaction.user.id)
        receiver_id = str(user.id)
        if sender_id == receiver_id:
            await interaction.response.send_message("자기 자신에게 송금할 수 없습니다.",
                                                    ephemeral=True)
            return
        data = load_data()
        data.setdefault(sender_id, {"olive": 0, "last_check": ""})
        data.setdefault(receiver_id, {"olive": 0, "last_check": ""})
        if data[sender_id]["olive"] < amount:
            await interaction.response.send_message("올리브가 부족합니다!",
                                                    ephemeral=True)
            return
        data[sender_id]["olive"] -= amount
        data[receiver_id]["olive"] += amount
        save_data(data)
        await interaction.response.send_message(
            f"{interaction.user.mention}님이 {user.mention}님에게 🌿 올리브 {amount}개를 송금했습니다!"
        )
