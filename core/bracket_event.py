import discord
from discord import app_commands
import random

# 전역 상태 변수
bracket_participants = []
bracket_active = False
bracket_round = 1


def setup(bot, ADMIN_IDS):

    @bot.tree.command(name="대진시작", description="사다리식 대진 등록을 시작합니다.")
    async def 대진시작(interaction: discord.Interaction):
        global bracket_participants, bracket_active, bracket_round
        if interaction.user.id not in ADMIN_IDS:
            await interaction.response.send_message("권한이 없습니다.",
                                                    ephemeral=True)
            return
        bracket_participants = []
        bracket_active = True
        bracket_round = 1
        await interaction.response.send_message(
            "🎲 대진 등록이 시작되었습니다! `/참가`로 참가하세요.")

    @bot.tree.command(name="참가", description="대진에 참가합니다.")
    async def 참가(interaction: discord.Interaction):
        global bracket_participants
        if not bracket_active:
            await interaction.response.send_message("❌ 현재 대진 등록 중이 아닙니다.",
                                                    ephemeral=True)
            return
        user = interaction.user
        if user in bracket_participants:
            await interaction.response.send_message("이미 참가하셨습니다.",
                                                    ephemeral=True)
            return
        bracket_participants.append(user)
        await interaction.response.send_message(f"{user.mention} 대진에 참가 완료!")

    @bot.tree.command(name="대진보기", description="현재 대진 참가자 목록을 확인합니다.")
    async def 대진보기(interaction: discord.Interaction):
        if not bracket_participants:
            await interaction.response.send_message("❌ 현재 등록된 참가자가 없습니다.")
            return
        msg = "👥 **현재 참가자 목록**\n"
        for user in bracket_participants:
            msg += f"- {user.display_name}\n"
        await interaction.response.send_message(msg)

    @bot.tree.command(name="대진완료", description="무작위로 대진표를 생성합니다.")
    async def 대진완료(interaction: discord.Interaction):
        global bracket_active
        if interaction.user.id not in ADMIN_IDS:
            await interaction.response.send_message("권한이 없습니다.",
                                                    ephemeral=True)
            return
        if len(bracket_participants) < 2:
            await interaction.response.send_message(
                "❌ 참가자가 2명 이상이어야 대진표를 생성할 수 있습니다.")
            return

        bracket_active = False
        shuffled = bracket_participants.copy()
        random.shuffle(shuffled)

        result = f"🎯 **1라운드 대진표**\n"
        for i in range(0, len(shuffled) - 1, 2):
            result += f"{shuffled[i].display_name}  ⚔️  {shuffled[i + 1].display_name}\n"

        if len(shuffled) % 2 == 1:
            result += f"⚠️ {shuffled[-1].display_name}는 부전승!\n"

        await interaction.response.send_message(result)

    @bot.tree.command(name="다음라운드", description="승자 목록으로 새로운 라운드를 생성합니다.")
    @app_commands.describe(user1="다음 라운드 유저 1",
                           user2="다음 라운드 유저 2",
                           user3="다음 라운드 유저 3 (선택)",
                           user4="다음 라운드 유저 4 (선택)",
                           user5="다음 라운드 유저 5 (선택)",
                           user6="다음 라운드 유저 6 (선택)",
                           user7="다음 라운드 유저 7 (선택)",
                           user8="다음 라운드 유저 8 (선택)")
    async def 다음라운드(interaction: discord.Interaction,
                    user1: discord.Member,
                    user2: discord.Member,
                    user3: discord.Member = None,
                    user4: discord.Member = None,
                    user5: discord.Member = None,
                    user6: discord.Member = None,
                    user7: discord.Member = None,
                    user8: discord.Member = None):
        global bracket_participants, bracket_round
        if interaction.user.id not in ADMIN_IDS:
            await interaction.response.send_message("권한이 없습니다.",
                                                    ephemeral=True)
            return

        winners = [
            u
            for u in [user1, user2, user3, user4, user5, user6, user7, user8]
            if u
        ]

        if len(winners) < 2:
            await interaction.response.send_message(
                "❌ 2명 이상 입력해야 다음 라운드를 생성할 수 있습니다.", ephemeral=True)
            return

        bracket_participants = winners
        bracket_round += 1
        random.shuffle(bracket_participants)

        result = f"🎯 **{bracket_round}라운드 대진표**\n"
        for i in range(0, len(bracket_participants) - 1, 2):
            result += f"{bracket_participants[i].display_name} vs {bracket_participants[i + 1].display_name}\n"

        if len(bracket_participants) % 2 == 1:
            result += f"⚠️ {bracket_participants[-1].display_name}는 부전승!\n"

        await interaction.response.send_message(result)

    @bot.tree.command(name="대진리셋", description="대진 정보를 초기화합니다.")
    async def 대진리셋(interaction: discord.Interaction):
        global bracket_participants, bracket_active, bracket_round
        if interaction.user.id not in ADMIN_IDS:
            await interaction.response.send_message("권한이 없습니다.",
                                                    ephemeral=True)
            return

        bracket_participants = []
        bracket_active = False
        bracket_round = 1
        await interaction.response.send_message("🔄 대진 정보가 초기화되었습니다.")
