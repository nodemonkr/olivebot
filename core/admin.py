import os 
import discord
import zipfile
from discord import app_commands
from core.utils import load_data, save_data
from datetime import datetime

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
            await interaction.response.send_message("권한이 없습니다.", ephemeral=True)
            return

        targets = [user for user in [user1, user2, user3, user4, user5] if user]
        data = load_data()
        mentions = []

        for user in targets:
            uid = str(user.id)
            u = data.get(uid, {})
            u.setdefault("olive", 0)
            u.setdefault("last_check", "")
            u.setdefault("stocks", {})
            u["olive"] += amount
            data[uid] = u
            mentions.append(user.mention)

        save_data(data)
        msg = f"각 유저에게 🌿 올리브 {amount}개 지급 완료!\n" + "\n".join(mentions)
        await interaction.response.send_message(msg)

    @bot.tree.command(name="회수", description="관리자가 유저의 올리브를 회수합니다.")
    @app_commands.describe(user="올리브를 회수할 유저", amount="회수할 올리브 개수")
    async def 회수(interaction: discord.Interaction, user: discord.Member, amount: int):
        if not is_admin(interaction.user.id):
            await interaction.response.send_message("권한이 없습니다.", ephemeral=True)
            return

        data = load_data()
        user_id = str(user.id)
        u = data.get(user_id, {})
        u.setdefault("olive", 0)
        u.setdefault("last_check", "")
        u.setdefault("stocks", {})
        u["olive"] = max(0, u["olive"] - amount)
        data[user_id] = u
        save_data(data)

        await interaction.response.send_message(f"{user.mention}님의 🌿 올리브 {amount}개를 회수했습니다.")

    @bot.tree.command(name="백업요청", description="data 폴더의 모든 데이터를 압축하여 DM으로 전송합니다.")
    async def 백업요청(interaction: discord.Interaction):
        if interaction.user.id not in ADMIN_IDS:
            await interaction.response.send_message("관리자만 사용할 수 있습니다.", ephemeral=True)
            return

        today = datetime.now().strftime("%Y-%m-%d")
        zip_filename = f"backup_{today}.zip"

        try:
            with zipfile.ZipFile(zip_filename, "w") as zipf:
                for filename in os.listdir("data"):
                    if filename.endswith(".json"):
                        zipf.write(os.path.join("data", filename), arcname=filename)

            await interaction.user.send(file=discord.File(zip_filename))
            await interaction.response.send_message(f"✅ DM으로 `{zip_filename}` 파일을 전송했습니다.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ 전송 실패: {e}", ephemeral=True)
