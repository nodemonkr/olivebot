import discord
from discord import app_commands
from datetime import datetime
from core.utils import load_data, save_data
import pytz

def get_today_kst():
    kst = pytz.timezone("Asia/Seoul")
    now = datetime.now(kst)
    return now.strftime("%Y-%m-%d"), now


def setup(bot):
    @bot.tree.command(name="출석", description="오늘 출석 체크를 합니다.")
    async def 출석(interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        display_name = interaction.user.display_name
        today_str, today = get_today_kst()
        kst = pytz.timezone("Asia/Seoul")
        data = load_data()

        user = data.setdefault(user_id, {
            "olive": 0,
            "last_check": "",
            "display_name": display_name,
            "streak": 0
        })
        user["display_name"] = display_name
        user.setdefault("streak", 0)

        last_check_str = user.get("last_check", "")
        last_check = (
            kst.localize(datetime.strptime(last_check_str, "%Y-%m-%d"))
            if last_check_str else None
        )

        # ✅ 이미 출석했을 경우
        if last_check_str == today_str:
            try:
                await interaction.response.send_message(
                    f"{interaction.user.mention} 오늘은 이미 출석했어요!", ephemeral=True
                )
            except discord.InteractionResponded:
                pass
            return

        # ✅ interaction 만료 방지
        try:
            await interaction.response.defer(ephemeral=True)
        except (discord.NotFound, discord.InteractionResponded):
            return

        # ✅ 연속 출석 계산
        if last_check and (today - last_check).days == 1:
            user["streak"] += 1
        else:
            user["streak"] = 1

        streak_bonus = min(user["streak"] * 5, 150)
        total_reward = 100 + streak_bonus

        user["last_check"] = today_str
        user["olive"] += total_reward
        save_data(data)

        try:
            await interaction.followup.send(
                f"{interaction.user.mention} 출석 완료! 🌿 올리브 {total_reward}개 지급 "
                f"(기본 100 + 연속 {user['streak']}일 보너스 {streak_bonus})"
            )
        except discord.InteractionResponded:
            pass