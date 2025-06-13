# stock.py (적용된 주가 모델 통합 + 명령어 전체 포함)

import discord
from discord import app_commands
from discord.ext import tasks
import json, random, os
from datetime import datetime, timedelta
from core.utils import load_data, save_data
import asyncio
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from typing import List
import random

# 한글 깨짐 방지 설정
matplotlib.rcParams['font.family'] = 'Malgun Gothic'  # Windows 기준
matplotlib.rcParams['axes.unicode_minus'] = False

class StockNameConverter(app_commands.Transformer):
    async def transform(self, interaction: discord.Interaction, value: str) -> str:
        return value

    async def autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        with open("data/stock_data.json", "r", encoding="utf-8") as f:
            stock_data = json.load(f)

        return [
            app_commands.Choice(name=name, value=name)
            for name in stock_data.keys()
            if current.lower() in name.lower()
        ][:25]

DATA_FILE = "data/stock_data.json"
USER_FILE = "data/users.json"
NEWS_FILE = "data/news_data.json"
SETTINGS_FILE = "data/stock_settings.json"
TRADE_LOG_FILE = "data/trade_log.json"

ADMIN_IDS = [1047192081828941845]
MAX_USER_TOTAL_SHARES = 10

def load_json(path, default={}):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=2)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_settings():
    default = {"price_ceiling": 0.05}
    settings = load_json(SETTINGS_FILE, default)
    default.update(settings)
    return default

def update_trade_log(name: str, qty: int, action: str):
    trades = load_json(TRADE_LOG_FILE)
    trades.setdefault(name, {"buy": 0, "sell": 0})
    trades[name][action] += qty
    save_json(TRADE_LOG_FILE, trades)

def random_market_change():
    roll = random.random()
    if roll < 0.1:
        return random.uniform(+0.03, +0.05)  # 큰 상승
    elif roll < 0.3:
        return random.uniform(+0.01, +0.03)  # 중간 상승
    elif roll < 0.7:
        return random.uniform(-0.01, +0.01)  # 약한 변동
    elif roll < 0.9:
        return random.uniform(-0.03, -0.01)  # 중간 하락
    else:
        return random.uniform(-0.05, -0.03)  # 큰 하락


def update_stock_prices():
    stocks = load_json(DATA_FILE)
    trades = load_json(TRADE_LOG_FILE)
    news = load_json(NEWS_FILE)
    settings = get_settings()
    today = datetime.now().strftime("%Y-%m-%d")

    result = []
    for name, s in stocks.items():
        if s.get("delisted", False):
            continue

        tlog = trades.get(name, {})
        demand = tlog.get("buy", 0)
        supply = tlog.get("sell", 0)
        total = demand + supply if demand + supply > 0 else 1
        demand_supply_rate = (demand - supply) / total * 0.02

        manual_bias = tlog.get("bias")
        trend_bias = manual_bias if manual_bias is not None else 0

        for n in news.get(name, []):
            if not n.get("applied") and n["date"] <= today:
                trend_bias += (n["influence"] - 3) * 0.01
                n["applied"] = True

        base_change = random_market_change()
        change = base_change + demand_supply_rate + trend_bias
        change = min(max(change, -settings["price_ceiling"]), settings["price_ceiling"])

        old_price = s["price"]

        # ✅ 최초 초기값 설정
        if "initial" not in s:
            s["initial"] = old_price
        initial_price = s["initial"]

        new_price = int(old_price * (1 + change))
        new_price = max(1, min(new_price, int(initial_price * 2)))

        s["price"] = new_price
        s.setdefault("history", []).append(new_price)
        if len(s["history"]) > 10:
            s["history"] = s["history"][1:]
        s["last_updated"] = today

        result.append(f"{name}: {old_price} → {new_price} ({change*100:+.2f}%)")

        trades[name]["buy"] = 0
        trades[name]["sell"] = 0
        if manual_bias is not None:
            trades[name]["bias"] = manual_bias

    save_json(DATA_FILE, stocks)
    save_json(NEWS_FILE, news)
    save_json(TRADE_LOG_FILE, trades)
    return result
def setup(bot):
    async def stock_name_autocomplete(interaction: discord.Interaction, current: str):
        stocks = load_json(DATA_FILE)
        options = [name for name in stocks if current.lower() in name.lower() and not stocks[name].get("delisted")]
        return [app_commands.Choice(name=name, value=name) for name in options[:25]]

    @bot.tree.command(name="시장갱신", description="모든 주식의 가격을 갱신합니다.")
    async def 시장갱신(interaction: discord.Interaction):
        if interaction.user.id not in ADMIN_IDS:
            await interaction.response.send_message("관리자만 사용할 수 있습니다.", ephemeral=True)
            return
        result = update_stock_prices()
        await interaction.response.send_message("\n".join(result), ephemeral=True)

    @bot.tree.command(name="주식구매", description="주식을 구매합니다.")
    @app_commands.describe(name="종목", qty="구매 수량")
    @app_commands.autocomplete(name=stock_name_autocomplete)
    async def 주식구매(interaction: discord.Interaction, name: str, qty: int):
        user_id = str(interaction.user.id)
        users = load_json(USER_FILE)
        stocks = load_json(DATA_FILE)
        settings = get_settings()

        if name not in stocks or stocks[name].get("delisted"):
            await interaction.response.send_message("존재하지 않거나 상장폐지된 종목입니다.", ephemeral=True)
            return

        user = users.setdefault(user_id, {"olive": 0, "stocks": {}})
        user.setdefault("stocks", {})
        user["stocks"] = {k: v for k, v in user["stocks"].items() if v.get("qty", 0) > 0}

        def user_total_stocks(user_data: dict) -> int:
            user_data.setdefault("stocks", {})
            return sum(p.get("qty", 0) for p in user_data["stocks"].values() if p.get("qty", 0) > 0)

        if user_total_stocks(user) + qty > MAX_USER_TOTAL_SHARES:
            await interaction.response.send_message(f"❌ 보유 가능한 총 주식 수({MAX_USER_TOTAL_SHARES}주)를 초과합니다.", ephemeral=True)
            return

        price = stocks[name]["price"]
        total = int(price * qty * (1 + settings["fee_rate"]))

        if user["olive"] < total:
            await interaction.response.send_message("❌ 올리브가 부족합니다.", ephemeral=True)
            return

        user["olive"] -= total
        holding = user["stocks"].get(name, {"qty": 0, "avg": 0})
        total_qty = holding["qty"] + qty
        holding["avg"] = int((holding["avg"] * holding["qty"] + price * qty) / total_qty)
        holding["qty"] = total_qty
        user["stocks"][name] = holding

        stocks[name]["last_trade"] = datetime.now().strftime("%Y-%m-%d")

        save_json(USER_FILE, users)
        save_json(DATA_FILE, stocks)
        update_trade_log(name, qty, "buy")

        await interaction.response.send_message(f"✅ {name} 주식 {qty}주를 구매했습니다.\n📊 평균단가: {holding['avg']} 올리브", ephemeral=True)

    @bot.tree.command(name="주식판매", description="보유한 주식을 판매합니다.")
    @app_commands.describe(name="종목", qty="판매 수량")
    @app_commands.autocomplete(name=stock_name_autocomplete)
    async def 주식판매(interaction: discord.Interaction, name: str, qty: int):
        users = load_json(USER_FILE)
        stocks = load_json(DATA_FILE)
        settings = get_settings()
        uid = str(interaction.user.id)

        if name not in stocks or stocks[name].get("delisted"):
            await interaction.response.send_message("존재하지 않는 종목입니다.", ephemeral=True)
            return

        users.setdefault(uid, {"olive": 0})
        if "stocks" not in users[uid]:
            users[uid]["stocks"] = {}

        if name not in users[uid]["stocks"]:
            await interaction.response.send_message("해당 종목을 보유하고 있지 않습니다.", ephemeral=True)
            return

        p = users[uid]["stocks"][name]
        if p["qty"] < qty:
            await interaction.response.send_message("보유 수량이 부족합니다.", ephemeral=True)
            return

        price = stocks[name]["price"]
        receive = int(price * qty * (1 - settings["fee_rate"]))
        p["qty"] -= qty

        if p["qty"] == 0:
            users[uid]["stocks"].pop(name)
        users[uid]["olive"] += receive
        stocks[name]["last_trade"] = datetime.now().strftime("%Y-%m-%d")

        save_json(USER_FILE, users)
        save_json(DATA_FILE, stocks)
        update_trade_log(name, qty, "sell")

        await interaction.response.send_message(f"✅ {name} {qty}주 판매 완료 (수령: 🫒{receive}개 올리브)", ephemeral=True)

    # ... 앞부분 생략 ...

    @bot.tree.command(name="포트폴리오", description="자신의 주식 보유 현황을 확인합니다.")
    async def 포트폴리오(interaction: discord.Interaction):
        users = load_json(USER_FILE)
        stocks = load_json(DATA_FILE)
        uid = str(interaction.user.id)
        users.setdefault(uid, {"olive": 0})
        if "stocks" not in users[uid]:
            users[uid]["stocks"] = {}

        msg = ["📂 내 포트폴리오"]
        total = 0
        for name, p in users[uid]["stocks"].items():
            if name in stocks:
                cur = stocks[name]["price"]
                eval_price = cur * p["qty"]
                diff = cur - p["avg"]
                msg.append(f"{name}: {p['qty']}주 (구매가 🫒{p['avg']} → 현재 🫒{cur} / 손익 🫒{diff:+})")
                total += eval_price
        msg.append(f"총 평가액: 🫒{total}개 올리브")
        await interaction.response.send_message("\n".join(msg), ephemeral=True)

    # @bot.tree.command(name="주식정보", description="종목의 현재가와 추세를 확인합니다.")
    # @app_commands.describe(name="조회할 종목 이름")
    # @app_commands.autocomplete(name=stock_name_autocomplete)
    # async def 주식정보(interaction: discord.Interaction, name: str):
    #     stocks = load_json(DATA_FILE)
    #     s = stocks.get(name)
    #     if not s or s.get("delisted"):
    #         await interaction.response.send_message("존재하지 않거나 상장폐지된 종목입니다.", ephemeral=True)
    #         return
    #     history = s.get("history", [s["price"]])
    #     prev = history[-2] if len(history) >= 2 else s["price"]
    #     rate = (s["price"] - prev) / prev * 100 if prev else 0
    #     msg = f"📊 {name}\n현재가: 🫒 {s['price']}개 올리브\n등락률: {rate:+.2f}%"
    #     await interaction.response.send_message(msg, ephemeral=True)

    @bot.tree.command(name="주식왕", description="수익률 기준 주식 랭킹을 보여줍니다.")
    async def 주식왕(interaction: discord.Interaction):
        await interaction.response.defer()  # 응답 예약

        users = load_data()
        stocks = load_json("data/stock_data.json")

        ranking = []
        for uid, udata in users.items():
            udata.setdefault("stocks", {})
            profit = 0
            for name, p in udata["stocks"].items():
                if name in stocks:
                    cur = stocks[name]["price"]
                    profit += (cur - p["avg"]) * p["qty"]
            ranking.append((uid, profit))

        ranking.sort(key=lambda x: x[1], reverse=True)  # 상위 10명 정렬
        top10 = ranking[:10]

        async def get_name(user_id):
            try:
                member = interaction.guild.get_member(int(user_id)) or await interaction.guild.fetch_member(int(user_id))
                return member.display_name
            except Exception:
                return f"유저({user_id})"

        names = await asyncio.gather(*(get_name(uid) for uid, _ in top10))

        msg = ["🏆 주식 수익률 랭킹"]
        for i, ((uid, profit), name) in enumerate(zip(top10, names), 1):
            msg.append(f"{i}. {name}: 수익량 -> 🫒{profit:+} 올리브")

        await interaction.followup.send("\n".join(msg), ephemeral=False)  # 전체 공개

    @bot.tree.command(name="주식종목", description="현재 상장된 모든 종목을 확인합니다.")
    async def 주식종목(interaction: discord.Interaction):
        stocks = load_json(DATA_FILE)
        msg = ["📈 현재 상장 종목:"]
        for name, info in stocks.items():
            if info.get("delisted"):
                continue
            price = info["price"]
            history = info.get("history", [price])
            prev = history[-2] if len(history) >= 2 else price
            rate = (price - prev) / prev * 100 if prev else 0
            msg.append(f"- {name}: 🫒{price}개 올리브 ({rate:+.2f}%)")
        await interaction.response.send_message("\n".join(msg))

    @bot.tree.command(name="추세설정", description="특정 종목의 추세값을 수동 설정합니다. (관리자용)")
    @app_commands.describe(name="종목명", bias="추세값 (-0.05 ~ +0.05)")
    @app_commands.autocomplete(name=stock_name_autocomplete)
    async def 추세설정(interaction: discord.Interaction, name: str, bias: float):
        if interaction.user.id not in ADMIN_IDS:
            await interaction.response.send_message("관리자만 사용할 수 있습니다.", ephemeral=True)
            return

        if not (-0.05 <= bias <= 0.05):
            await interaction.response.send_message("추세값은 -0.05에서 +0.05 사이여야 합니다.", ephemeral=True)
            return

        trades = load_json("data/trade_log.json")
        trades.setdefault(name, {"buy": 0, "sell": 0, "bias": 0.0})
        trades[name]["bias"] = round(bias, 4)
        save_json("data/trade_log.json", trades)

        await interaction.response.send_message(f"✅ {name} 종목의 추세 편향을 {bias:+.2%}로 설정했습니다.", ephemeral=True)

    @bot.tree.command(name="추세현황", description="전체 종목의 추세 및 평균을 확인합니다. (관리자 전용)")
    async def 추세현황(interaction: discord.Interaction):
        if interaction.user.id not in ADMIN_IDS:
            await interaction.response.send_message("관리자만 사용할 수 있습니다.", ephemeral=True)
            return

        trades = load_json("data/trade_log.json")
        stocks = load_json(DATA_FILE)
        result = ["📉 종목별 추세 편향 현황"]
        total = 0
        count = 0

        for name in stocks:
            bias = trades.get(name, {}).get("bias", 0.0)
            result.append(f"- {name}: {bias:+.3f}")
            total += bias
            count += 1

        if count:
            avg = total / count
            result.append(f"\n📊 전체 평균 추세 편향: {avg:+.3f}")
        else:
            result.append("⚠️ 추세 편향 데이터가 없습니다.")

        await interaction.response.send_message("\n".join(result), ephemeral=True)


    @bot.tree.command(name="보유종목", description="자신이 보유한 주식을 확인합니다. (본인만 보기)")
    async def 보유종목(interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        users = load_json(USER_FILE)
        stocks = load_json(DATA_FILE)
        user = users.get(user_id, {})
        holdings = user.get("stocks", {})

        # 자동 정리: 수량 0이거나 상장폐지된 종목 제거
        cleaned = {
            name: data
            for name, data in holdings.items()
            if data.get("qty", 0) > 0 and name in stocks and not stocks[name].get("delisted")
        }
        user["stocks"] = cleaned
        users[user_id] = user
        save_json(USER_FILE, users)

        if not cleaned:
            await interaction.response.send_message("📭 보유한 주식이 없습니다.", ephemeral=True)
            return

        msg = ["📦 보유 종목 현황"]
        for name, data in cleaned.items():
            cur_price = stocks[name]["price"]
            qty = data["qty"]
            avg = data["avg"]
            value = cur_price * qty
            profit = (cur_price - avg) * qty
            emoji = "🔺" if profit > 0 else "🔻" if profit < 0 else "⏸️"
            msg.append(f"{name}: {qty}주 | 구매가: {avg} → 현재가: {cur_price} | 평가금액: {value} ({emoji} {profit:+})")

        await interaction.response.send_message("\n".join(msg), ephemeral=True)

    @bot.tree.command(name="뉴스등록", description="뉴스를 등록해 종목 추세에 영향을 줍니다.")
    @app_commands.describe(name="종목", content="뉴스 내용", influence="호재(5)~악재(1) 강도")
    @app_commands.autocomplete(name=stock_name_autocomplete)
    async def 뉴스등록(interaction: discord.Interaction, name: str, content: str, influence: int):
        if interaction.user.id not in ADMIN_IDS:
            await interaction.response.send_message("⚠️ 관리자만 사용할 수 있습니다.", ephemeral=True)
            return

        if influence < 1 or influence > 5:
            await interaction.response.send_message("📉 영향도는 1(악재)부터 5(호재) 사이여야 합니다.", ephemeral=True)
            return

        news = load_json("data/news_data.json")
        today = datetime.now().strftime("%Y-%m-%d")

        news.setdefault(name, []).append({
            "content": content,
            "influence": influence,
            "date": today,
            "applied": False
        })

        save_json("data/news_data.json", news)
        await interaction.response.send_message(
            f"📰 **{name}** 뉴스 등록 완료!\n`{content}` (영향도: {influence})", ephemeral=True)

    @bot.tree.command(name="상장폐지", description="지정한 종목을 수동 폐지합니다.")
    @app_commands.describe(name="종목 이름")
    @app_commands.autocomplete(name=StockNameConverter().autocomplete)
    async def 상장폐지(interaction: discord.Interaction, name: str):
        if interaction.user.id not in ADMIN_IDS:
            await interaction.response.send_message("⚠️ 관리자만 사용할 수 있습니다.", ephemeral=True)
            return

        with open("data/stock_data.json", "r", encoding="utf-8") as f:
            stock_data = json.load(f)

        if name not in stock_data:
            await interaction.response.send_message("❌ 해당 종목은 존재하지 않습니다.", ephemeral=True)
            return

        del stock_data[name]

        with open("data/stock_data.json", "w", encoding="utf-8") as f:
            json.dump(stock_data, f, ensure_ascii=False, indent=2)

        await interaction.response.send_message(f"🗑️ `{name}` 종목이 상장폐지되어 데이터에서 제거되었습니다.")


    @bot.tree.command(name="뉴스삭제", description="특정 종목의 뉴스를 모두 삭제합니다.")
    @app_commands.describe(name="뉴스를 삭제할 종목 이름")
    @app_commands.autocomplete(name=stock_name_autocomplete)
    async def 뉴스삭제(interaction: discord.Interaction, name: str):
        if interaction.user.id not in ADMIN_IDS:
            await interaction.response.send_message("⚠️ 관리자만 사용할 수 있습니다.", ephemeral=True)
            return

        news = load_json("data/news_data.json")
        if name not in news or not news[name]:
            await interaction.response.send_message("해당 종목에 등록된 뉴스가 없습니다.", ephemeral=True)
            return

        del news[name]
        save_json("data/news_data.json", news)
        await interaction.response.send_message(f"🗑️ `{name}`의 모든 뉴스가 삭제되었습니다.", ephemeral=True)

    @bot.tree.command(name="뉴스전체삭제", description="모든 종목의 뉴스를 일괄 삭제합니다.")
    async def 뉴스전체삭제(interaction: discord.Interaction):
        if interaction.user.id not in ADMIN_IDS:
            await interaction.response.send_message("⚠️ 관리자만 사용할 수 있습니다.", ephemeral=True)
            return

        save_json("data/news_data.json", {})  # 빈 딕셔너리로 덮어쓰기
        await interaction.response.send_message("🧹 모든 뉴스가 초기화되었습니다.", ephemeral=True)

    @bot.tree.command(name="종목추가", description="새로운 종목을 등록합니다. (관리자 전용)")
    @app_commands.describe(name="종목명", price="초기 주가")
    async def 종목추가(interaction: discord.Interaction, name: str, price: int):
        if interaction.user.id not in ADMIN_IDS:
            await interaction.response.send_message("⚠️ 관리자만 사용할 수 있습니다.", ephemeral=True)
            return

        stocks = load_json(DATA_FILE)
        if name in stocks:
            await interaction.response.send_message("❌ 이미 존재하는 종목입니다.", ephemeral=True)
            return

        stocks[name] = {
            "price": price,
            "trend": "up",
            "bias": 0,
            "locked": False,
            "history": [],
            "trend_days": 0
        }

        save_json(DATA_FILE, stocks)
        await interaction.response.send_message(
            f"✅ `{name}` 종목이 🫒 {price} 올리브로 등록되었습니다.", ephemeral=True)


    @bot.tree.command(name="주식그래프", description="특정 종목의 가격 변동 그래프를 확인합니다.")
    @app_commands.describe(name="확인할 종목명")
    @app_commands.rename(name="종목")
    @app_commands.autocomplete(name=StockNameConverter().autocomplete)
    async def 주식그래프(interaction: discord.Interaction, name: str):
        with open("data/stock_data.json", "r", encoding="utf-8") as f:
            stock_data = json.load(f)

        if name not in stock_data:
            await interaction.response.send_message("❌ 해당 종목이 존재하지 않습니다.", ephemeral=True)
            return

        history = stock_data[name].get("history", [])
        if len(history) < 2:
            await interaction.response.send_message("📉 해당 종목은 기록된 가격 변화가 부족합니다.", ephemeral=True)
            return

        plt.style.use('ggplot')
        fig, ax = plt.subplots(figsize=(10, 5))

        x = np.arange(len(history))
        y = np.array(history)
        ax.plot(x, y, marker="o", linewidth=2.5, label=name)

        ax.set_title(f"📈 {name} 가격 변화 추이", fontsize=16, weight='bold')
        ax.set_xlabel("갱신 순서", fontsize=12)
        ax.set_ylabel("가격 (올리브)", fontsize=12)
        ax.tick_params(axis='both', labelsize=10)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=10)
        fig.tight_layout()

        path = "stock_graph.png"
        fig.savefig(path, dpi=180)
        plt.close(fig)

        await interaction.response.send_message(file=discord.File(path))