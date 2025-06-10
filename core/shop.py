import discord
from discord import app_commands

# 상점에 등록된 아이템 목록
shop_items = {
    "지혜의서적": {
        "price": 100,
        "emoji": "📕",
        "description": "숙작 아이템"
    },
    "착취한에너지": {
        "price": 100,
        "emoji": "🔵",
        "description": "옵차 아이템"
    },
    "공허한멧돼지": {
        "price": 3000,
        "emoji": "🐗",
        "description": "안장 달린 야생 멧돼지"
    },
}


def setup(bot):

    @bot.tree.command(name="상점", description="🌿 올리브로 구매 가능한 아이템 목록을 확인합니다.")
    async def 상점(interaction: discord.Interaction):
        embed = discord.Embed(title="🛒 올리브 상점",
                              color=0x95ef63,
                              description="(1개 가격입니다 구매 문의 운영팀)")
        for name, item in shop_items.items():
            embed.add_field(
                name=f"{item['emoji']} {name} - 🌿 {item['price']}개",
                value=item['description'],
                inline=False)
        await interaction.response.send_message(embed=embed)
