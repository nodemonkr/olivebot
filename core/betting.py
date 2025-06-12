import discord
from discord import app_commands
from core.utils import load_data, save_data
import json
import random

ADMIN_IDS = [1047192081828941845]  # 관리자 ID 리스트

betting_settings = {"success_rate": 0.2, "payout_multiplier": 2.0}
challenge_requests = {}  # {도전자ID: (상대ID, 베팅금액)}


def load_betting_settings():
    global betting_settings
    try:
        with open("data/betting_settings.json", "r", encoding="utf-8") as f:
            betting_settings.update(json.load(f))
    except FileNotFoundError:
        save_betting_settings()


def save_betting_settings():
    with open("data/betting_settings.json", "w", encoding="utf-8") as f:
        json.dump(betting_settings, f, ensure_ascii=False, indent=4)


def setup(bot):
    load_betting_settings()

    @bot.tree.command(name="도박", description="🌿 올리브를 걸고 도박을 합니다.")
    @app_commands.describe(amount="걸 🌿 올리브 수")
    async def 도박(interaction: discord.Interaction, amount: int):
        if amount <= 0:
            await interaction.response.send_message("금액은 1 이상이어야 합니다.",
                                                    ephemeral=True)
            return

        data = load_data()
        user_id = str(interaction.user.id)
        if user_id not in data or data[user_id]["olive"] < amount:
            await interaction.response.send_message("🌿 올리브가 부족합니다.",
                                                    ephemeral=True)
            return

        success = random.random() < betting_settings["success_rate"]
        if success:
            payout = int(amount * betting_settings["payout_multiplier"])
            data[user_id]["olive"] += payout
            result_msg = f"축하합니다! 성공하여 🌿 {payout}개의 올리브를 획득했습니다!"
        else:
            data[user_id]["olive"] -= amount
            result_msg = f"안타깝네요, 실패하여 🌿 {amount}개의 올리브를 잃었습니다."

        save_data(data)
        await interaction.response.send_message(result_msg)

    @bot.tree.command(name="대결", description="상대와 🌿 올리브를 걸고 대결을 신청합니다.")
    @app_commands.describe(opponent="대결 상대", amount="걸 🌿 올리브 금액")
    async def 대결(interaction: discord.Interaction, opponent: discord.Member,
                 amount: int):
        challenger_id = str(interaction.user.id)
        opponent_id = str(opponent.id)

        if amount <= 0:
            await interaction.response.send_message("🌿 보유 올리브가 1 이상이어야 합니다.",
                                                    ephemeral=True)
            return

        if challenger_id == opponent_id:
            await interaction.response.send_message("자기 자신과는 대결할 수 없습니다.",
                                                    ephemeral=True)
            return

        data = load_data()
        if challenger_id not in data or data[challenger_id]["olive"] < amount:
            await interaction.response.send_message("🌿 올리브가 부족합니다.",
                                                    ephemeral=True)
            return
        if opponent_id not in data or data[opponent_id]["olive"] < amount:
            await interaction.response.send_message(
                f"{opponent.display_name}님 🌿 올리브가 부족합니다.", ephemeral=True)
            return

        if challenger_id in challenge_requests:
            await interaction.response.send_message(
                "이미 대결 신청 중입니다. 상대방의 응답을 기다려주세요.", ephemeral=True)
            return

        challenge_requests[challenger_id] = (opponent_id, amount)
        await interaction.response.send_message(
            f"{opponent.mention}님, {interaction.user.display_name}님이 {amount} 🌿 올리브로 대결을 신청했습니다.\n"
            f"수락하려면 `/대결수락`, 거절하려면 `/대결거절` 명령어를 입력하세요.")

    @bot.tree.command(name="대결수락", description="대결 신청을 수락합니다.")
    async def 대결수락(interaction: discord.Interaction):
        try:
            await interaction.response.defer()

            guild = interaction.guild
            if guild is None:
                await interaction.followup.send("❌ 이 명령어는 서버 내에서만 사용 가능합니다.",
                                                ephemeral=True)
                return

            user_id = str(interaction.user.id)
            data = load_data()

            found = None
            for challenger_id, (opponent_id,
                                amount) in challenge_requests.items():
                if opponent_id == user_id:
                    found = (challenger_id, amount)
                    break

            if not found:
                await interaction.followup.send("❌ 대결 신청이 없습니다.",
                                                ephemeral=True)
                return

            challenger_id, amount = found

            if data.get(challenger_id, {}).get("olive", 0) < amount:
                challenge_requests.pop(challenger_id, None)
                await interaction.followup.send("❌ 도전자의 올리브가 부족합니다.",
                                                ephemeral=True)
                return

            if data.get(user_id, {}).get("olive", 0) < amount:
                challenge_requests.pop(challenger_id, None)
                await interaction.followup.send("❌ 수락자의 올리브가 부족합니다.",
                                                ephemeral=True)
                return

            winner_id = challenger_id if random.random() < 0.5 else user_id
            loser_id = user_id if winner_id == challenger_id else challenger_id

            data[winner_id]["olive"] += amount
            data[loser_id]["olive"] -= amount
            save_data(data)
            challenge_requests.pop(challenger_id, None)

            try:
                winner = guild.get_member(
                    int(winner_id)) or await guild.fetch_member(int(winner_id))
                loser = guild.get_member(
                    int(loser_id)) or await guild.fetch_member(int(loser_id))
            except Exception as e:
                print("❌ 유저 정보 fetch 실패:", e)
                await interaction.followup.send("⚠️ 유저 정보를 불러오는 데 실패했습니다.",
                                                ephemeral=True)
                return

            await interaction.followup.send(f"🎯 **대결 결과!**\n"
                                            f"**승자:** {winner.mention}\n"
                                            f"**패자:** {loser.mention}\n"
                                            f"🏆 🌿 {amount}개의 올리브를 획득했습니다!")

        except Exception as e:
            print("❌ 전체 예외 발생:", e)
            if not interaction.response.is_done():
                try:
                    await interaction.followup.send("⚠️ 알 수 없는 오류가 발생했습니다.")
                except:
                    pass

    @bot.tree.command(name="대결거절", description="대결 신청을 거절합니다.")
    async def 거절(interaction: discord.Interaction):
        user_id = str(interaction.user.id)

        found = None
        for challenger_id, (opponent_id, amount) in challenge_requests.items():
            if opponent_id == user_id:
                found = challenger_id
                break

        if not found:
            await interaction.response.send_message("대결 신청이 없습니다.",
                                                    ephemeral=True)
            return

        challenge_requests.pop(found)
        await interaction.response.send_message("대결 신청이 거절되었습니다.")

    @bot.tree.command(name="베팅확률", description="현재 베팅 성공 확률과 배당률을 확인합니다.")
    async def 베팅확률(interaction: discord.Interaction):
        msg = (f"현재 베팅 성공 확률: {betting_settings['success_rate']*100:.1f}%\n"
               f"배당률: {betting_settings['payout_multiplier']:.2f}배")
        await interaction.response.send_message(msg)

    @bot.tree.command(name="베팅설정", description="관리자만 베팅 확률과 배당률을 설정할 수 있습니다.")
    @app_commands.describe(success_rate="성공 확률 (0.0 ~ 1.0)",
                           payout_multiplier="배당률 (1.0 이상)")
    async def 베팅설정(interaction: discord.Interaction, success_rate: float,
                   payout_multiplier: float):
        if interaction.user.id not in ADMIN_IDS:
            await interaction.response.send_message("관리자만 사용할 수 있습니다.",
                                                    ephemeral=True)
            return
        if not (0.0 <= success_rate <= 1.0):
            await interaction.response.send_message(
                "성공 확률은 0.0 이상 1.0 이하이어야 합니다.", ephemeral=True)
            return
        if payout_multiplier < 1.0:
            await interaction.response.send_message("배당률은 1.0 이상이어야 합니다.",
                                                    ephemeral=True)
            return

        betting_settings["success_rate"] = success_rate
        betting_settings["payout_multiplier"] = payout_multiplier
        save_betting_settings()
        await interaction.response.send_message(
            f"베팅 설정이 성공적으로 변경되었습니다.\n"
            f"성공 확률: {success_rate*100:.1f}%, 배당률: {payout_multiplier:.2f}배",
            ephemeral=True)
