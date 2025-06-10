import discord
from discord import app_commands
from core.utils import load_data, save_data


def setup(bot, ADMIN_IDS):

    def is_admin(user_id):
        return user_id in ADMIN_IDS

    @bot.tree.command(name="지급", description="관리자가 여러 유저에게 올리브를 지급합니다.")
    @app_commands.describe(user1="올리브를 지급할 유저 1",
                           user2="올리브를 지급할 유저 2 (선택)",
                           user3="올리브를 지급할 유저 3 (선택)",
                           user4="올리브를 지급할 유저 4 (선택)",
                           user5="올리브를 지급할 유저 5 (선택)",
                           amount="지급할 올리브 개수")
    async def 지급(interaction: discord.Interaction,
                 user1: discord.Member,
                 amount: int,
                 user2: discord.Member = None,
                 user3: discord.Member = None,
                 user4: discord.Member = None,
                 user5: discord.Member = None):

        if not is_admin(interaction.user.id):
            await interaction.response.send_message("권한이 없습니다.",
                                                    ephemeral=True)
            return

        targets = [
            user for user in [user1, user2, user3, user4, user5] if user
        ]
        data = load_data()
        mentions = []

        for user in targets:
            uid = str(user.id)
            data.setdefault(uid, {"olive": 0, "last_check": ""})
            data[uid]["olive"] += amount
            mentions.append(user.mention)

        save_data(data)

        msg = f" 각 유저에게 🌿 올리브 {amount}개 지급 완료!\n" + "\n".join(mentions)
        await interaction.response.send_message(msg)

    @bot.tree.command(name="회수", description="관리자가 유저의 올리브를 회수합니다.")
    @app_commands.describe(user="올리브를 회수할 유저", amount="회수할 올리브 개수")
    async def 회수(interaction: discord.Interaction, user: discord.Member,
                 amount: int):
        if not is_admin(interaction.user.id):
            await interaction.response.send_message("권한이 없습니다.",
                                                    ephemeral=True)
            return
        user_id = str(user.id)
        data = load_data()
        data.setdefault(user_id, {"olive": 0, "last_check": ""})
        data[user_id]["olive"] = max(0, data[user_id]["olive"] - amount)
        save_data(data)
        await interaction.response.send_message(
            f"{user.mention}님의 🌿 올리브 {amount}개를 회수했습니다.")
