import discord
from discord.ext import commands
from core.utils import load_data, save_data
import re

# 전역 상태 저장
state = {"active": False, "answers": [], "reward": 0, "answered": False, "question": ""}

def is_correct(user_input: str, answer: str) -> bool:
    """입력 정규화 비교: 기호 제거 + 소문자 처리"""
    norm = lambda s: re.sub(r"[^\w가-힣]", "", s.lower())
    return norm(user_input) == norm(answer)

def get_safe_user(users: dict, user_id: str, display_name="") -> dict:
    user = users.get(user_id, {})
    user.setdefault("olive", 0)
    user.setdefault("last_check", "")
    user.setdefault("display_name", display_name)
    user.setdefault("streak", 0)
    user.setdefault("stocks", {})
    users[user_id] = user
    return user

def setup(bot, ADMIN_IDS):

    class AnswerModal(discord.ui.Modal, title="📝 정답 입력하기"):
        user: discord.User

        def __init__(self, user):
            super().__init__()
            self.user = user
            self.answer_input = discord.ui.TextInput(
                label="정답을 입력하세요",
                placeholder="여기에 정답을 입력하세요",
                required=True,
                max_length=100
            )
            self.add_item(self.answer_input)

        async def on_submit(self, interaction: discord.Interaction):
            if not state["active"] or state["answered"]:
                await interaction.response.send_message("⏱️ 이미 종료된 퀴즈입니다.", ephemeral=True)
                return

            for ans in state["answers"]:
                if is_correct(self.answer_input.value, ans):
                    user_id = str(self.user.id)
                    data = load_data()
                    get_safe_user(data, user_id, self.user.display_name)
                    data[user_id]["olive"] += state["reward"]
                    save_data(data)

                    state["answered"] = True
                    state["active"] = False

                    embed = discord.Embed(
                        title="🎆 정답입니다 🎆",
                        description=f"{self.user.mention}님이 정답을 맞췄습니다!",
                        color=0x2ecc71
                    )
                    embed.add_field(name="📌 문제", value=state["question"], inline=False)
                    embed.add_field(name="✅ 정답", value=f"`{self.answer_input.value.strip()}`", inline=False)
                    embed.add_field(name="🎁 보상", value=f"🌿 {state['reward']}개 지급 완료", inline=False)
                    await interaction.response.send_message(embed=embed)
                    return

            await interaction.response.send_message("❌ 아쉽게도 오답입니다!", ephemeral=True)

    class AnswerButton(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)

        @discord.ui.button(label="정답 입력하기", style=discord.ButtonStyle.primary)
        async def submit(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.send_modal(AnswerModal(user=interaction.user))

    @bot.tree.command(name="퀴즈시작", description="퀴즈를 시작합니다. (관리자만 가능)")
    @discord.app_commands.describe(
        question="출제할 퀴즈 내용",
        answer="정답 (여러 개일 경우 ,로 구분)",
        reward="정답자에게 지급할 올리브 수"
    )
    async def 퀴즈시작(interaction: discord.Interaction, question: str, answer: str, reward: int):
        if interaction.user.id not in ADMIN_IDS:
            await interaction.response.send_message("⚠️ 권한이 없습니다.", ephemeral=True)
            return

        # 퀴즈 상태 설정
        state["active"] = True
        state["answered"] = False
        state["reward"] = reward
        state["question"] = question
        state["answers"] = [a.strip() for a in answer.split(",") if a.strip()]

        # 퀴즈 Embed 및 버튼 전송
        embed = discord.Embed(
            title="⁉️ 올리브 퀴즈가 시작됩니다",
            description=f"> **{question}**",
            color=0x3498db
        )
        embed.set_footer(text=f"정답 시 🌿 {reward}개 올리브 보상!")
        await interaction.response.send_message(embed=embed, view=AnswerButton())
