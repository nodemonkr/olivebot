import discord
from discord.ext import commands
from core.utils import load_data, save_data
import re

state = {"active": False, "answers": [], "reward": 0, "answered": False}


def is_correct(user_input: str, answer: str) -> bool:
    """입력 정규화 비교: 기호 제거 + 소문자 처리"""
    norm = lambda s: re.sub(r"[^\w가-힣]", "", s.lower())
    return norm(user_input) == norm(answer)


def setup(bot, ADMIN_IDS):

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

        # 퀴즈 상태 초기화
        state["active"] = True
        state["answered"] = False
        state["reward"] = reward
        state["answers"] = [a.strip() for a in answer.split(",") if a.strip()]

        # 🧠 퀴즈 Embed 전송
        embed = discord.Embed(
            title="⁉️ 올리브 퀴즈가 시작됩니다",
            description=f"> **{question}**",
            color=0x3498db
        )
        embed.set_footer(text=f"정답 시 🌿 {reward}개 올리브 보상!")
        await interaction.response.defer()
        await interaction.followup.send(embed=embed)

    @bot.event
    async def on_message(message):
        if message.author.bot:
            return
        if not state["active"] or state["answered"]:
            return

        for ans in state["answers"]:
            if is_correct(message.content, ans):
                user_id = str(message.author.id)
                data = load_data()
                data.setdefault(user_id, {"olive": 0, "last_check": ""})
                data[user_id]["olive"] += state["reward"]
                save_data(data)

                state["answered"] = True
                state["active"] = False

                # 🎉 정답 Embed 전송
                embed = discord.Embed(
                    title="🎆 정답입니다 🎆",
                    description=f"{message.author.mention}님은 숨은 고수입니다☺️",
                    color=0x2ecc71
                )
                embed.add_field(name="🎁 보상", value=f"🌿 {state['reward']}개 지급 완료", inline=False)
                await message.channel.send(embed=embed)
                break
