import discord
from discord.ext import commands
from core.utils import load_data, save_data

state = {"active": False, "answer": "", "reward": 0, "answered": False}


def setup(bot, ADMIN_IDS):

    @bot.tree.command(name="퀴즈시작", description="퀴즈를 시작합니다. (관리자만 가능)")
    @discord.app_commands.describe(question="출제할 퀴즈 내용",
                                   answer="정답",
                                   reward="정답자에게 지급할 올리브 수")
    async def 퀴즈시작(interaction: discord.Interaction, question: str,
                   answer: str, reward: int):
        if interaction.user.id not in ADMIN_IDS:
            await interaction.response.send_message("권한이 없습니다.",
                                                    ephemeral=True)
            return

        state["active"] = True
        state["answer"] = answer.strip().lower()
        state["reward"] = reward
        state["answered"] = False

        await interaction.response.send_message(f"🧠 퀴즈 시작!\n{question}")

    @bot.event
    async def on_message(message):
        if message.author.bot:
            return
        if not state["active"] or state["answered"]:
            return

        if message.content.strip().lower() == state["answer"]:
            user_id = str(message.author.id)
            data = load_data()
            data.setdefault(user_id, {"olive": 0, "last_check": ""})
            data[user_id]["olive"] += state["reward"]
            save_data(data)

            state["answered"] = True
            state["active"] = False

            await message.channel.send(
                f"🎉 정답입니다!! {message.author.mention}!\n🌿 {state['reward']}개 올리브 지급 완료!"
            )
