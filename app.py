"""寶可夢冒險 — 可部署到 Streamlit Community Cloud 的回合制粉絲遊戲。

功能：選擇御三家、6 個區域野外遭遇、屬性相剋、捕捉、升級學招、進化、
4 場道館挑戰、寶可夢中心、商店、電腦箱、圖鑑、JSON 存檔/讀檔。
"""
import json
import random
import re

import streamlit as st

st.set_page_config(page_title="寶可夢冒險", page_icon="⚡", layout="centered")
S = st.session_state

SPRITE = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{}.png"
SPRITE_BACK = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/back/{}.png"

# ----------------------------------------------------------------------------
# 遊戲資料
# ----------------------------------------------------------------------------
TYPE_COLOR = {
    "一般": "#A8A878", "火": "#F08030", "水": "#6890F0", "草": "#78C850",
    "電": "#F8D030", "冰": "#98D8D8", "格鬥": "#C03028", "毒": "#A040A0",
    "地面": "#E0C068", "飛行": "#A890F0", "超能力": "#F85888", "蟲": "#A8B820",
    "岩石": "#B8A038", "幽靈": "#705898", "龍": "#7038F8",
}

# 攻擊屬性 -> {防守屬性: 倍率}，未列出者為 1 倍
TYPE_CHART = {
    "一般": {"岩石": 0.5, "幽靈": 0},
    "火": {"火": 0.5, "水": 0.5, "草": 2, "冰": 2, "蟲": 2, "岩石": 0.5, "龍": 0.5},
    "水": {"火": 2, "水": 0.5, "草": 0.5, "地面": 2, "岩石": 2, "龍": 0.5},
    "電": {"水": 2, "電": 0.5, "草": 0.5, "地面": 0, "飛行": 2, "龍": 0.5},
    "草": {"火": 0.5, "水": 2, "草": 0.5, "毒": 0.5, "地面": 2, "飛行": 0.5, "蟲": 0.5, "岩石": 2, "龍": 0.5},
    "冰": {"火": 0.5, "水": 0.5, "草": 2, "冰": 0.5, "地面": 2, "飛行": 2, "龍": 2},
    "格鬥": {"一般": 2, "冰": 2, "毒": 0.5, "飛行": 0.5, "超能力": 0.5, "蟲": 0.5, "岩石": 2, "幽靈": 0},
    "毒": {"草": 2, "毒": 0.5, "地面": 0.5, "岩石": 0.5, "幽靈": 0.5},
    "地面": {"火": 2, "電": 2, "草": 0.5, "毒": 2, "飛行": 0, "蟲": 0.5, "岩石": 2},
    "飛行": {"電": 0.5, "草": 2, "格鬥": 2, "蟲": 2, "岩石": 0.5},
    "超能力": {"格鬥": 2, "毒": 2, "超能力": 0.5},
    "蟲": {"火": 0.5, "草": 2, "格鬥": 0.5, "毒": 0.5, "飛行": 0.5, "超能力": 2, "幽靈": 0.5},
    "岩石": {"火": 2, "冰": 2, "格鬥": 0.5, "地面": 0.5, "飛行": 2, "蟲": 2},
    "幽靈": {"一般": 0, "幽靈": 2, "超能力": 2},
    "龍": {"龍": 2},
}

# 招式：(屬性, 威力, 命中率)
MOVES = {
    "撞擊": ("一般", 40, 100), "抓": ("一般", 40, 100), "拍擊": ("一般", 40, 100),
    "電光一閃": ("一般", 40, 100), "咬住": ("一般", 60, 100), "泰山壓頂": ("一般", 85, 100),
    "猛撞": ("一般", 90, 85), "破壞死光": ("一般", 120, 80),
    "火花": ("火", 40, 100), "噴射火焰": ("火", 90, 100), "大字爆炎": ("火", 110, 85),
    "水槍": ("水", 40, 100), "泡沫光線": ("水", 65, 100), "水砲": ("水", 110, 80),
    "藤鞭": ("草", 45, 100), "飛葉快刀": ("草", 55, 95), "日光束": ("草", 120, 85),
    "電擊": ("電", 40, 100), "十萬伏特": ("電", 90, 100), "打雷": ("電", 110, 70),
    "冰凍光束": ("冰", 90, 100),
    "空手劈": ("格鬥", 50, 100), "十字劈": ("格鬥", 100, 80),
    "毒針": ("毒", 35, 100), "污泥炸彈": ("毒", 90, 100),
    "挖洞": ("地面", 80, 100), "地震": ("地面", 100, 100),
    "起風": ("飛行", 40, 100), "翅膀攻擊": ("飛行", 60, 100),
    "念力": ("超能力", 50, 100), "精神強念": ("超能力", 90, 100),
    "蟲咬": ("蟲", 60, 100),
    "落石": ("岩石", 50, 90), "岩崩": ("岩石", 75, 90),
    "舌舔": ("幽靈", 30, 100), "暗影球": ("幽靈", 80, 100),
    "龍息": ("龍", 60, 100), "龍爪": ("龍", 80, 100),
}

# 招式學習表：(等級, 招式)
L_BULBA = [(1, "撞擊"), (3, "藤鞭"), (9, "毒針"), (15, "飛葉快刀"), (24, "污泥炸彈"), (36, "日光束")]
L_CHAR = [(1, "抓"), (4, "火花"), (12, "龍息"), (17, "咬住"), (28, "噴射火焰"), (36, "龍爪"), (44, "大字爆炎")]
L_SQUIR = [(1, "撞擊"), (4, "水槍"), (10, "咬住"), (16, "泡沫光線"), (25, "冰凍光束"), (40, "水砲")]
L_CATER = [(1, "撞擊"), (7, "蟲咬")]
L_BUTTER = [(1, "撞擊"), (7, "蟲咬"), (10, "念力"), (14, "起風"), (24, "精神強念")]
L_PIDGEY = [(1, "撞擊"), (5, "起風"), (13, "電光一閃"), (21, "翅膀攻擊"), (33, "猛撞")]
L_RAT = [(1, "撞擊"), (4, "電光一閃"), (10, "咬住"), (20, "挖洞"), (30, "猛撞")]
L_PIKA = [(1, "電擊"), (1, "電光一閃"), (18, "十萬伏特"), (30, "猛撞"), (40, "打雷")]
L_JIGGLY = [(1, "拍擊"), (14, "泰山壓頂"), (30, "冰凍光束")]
L_ZUBAT = [(1, "起風"), (1, "毒針"), (10, "咬住"), (18, "翅膀攻擊"), (30, "污泥炸彈")]
L_DIG = [(1, "抓"), (8, "挖洞"), (19, "岩崩"), (30, "地震")]
L_MEOWTH = [(1, "抓"), (6, "咬住"), (15, "電光一閃"), (25, "猛撞")]
L_PSY = [(1, "抓"), (5, "水槍"), (15, "念力"), (25, "泡沫光線"), (35, "水砲")]
L_GROWL = [(1, "咬住"), (10, "火花"), (25, "噴射火焰"), (40, "大字爆炎")]
L_POLI = [(1, "水槍"), (7, "拍擊"), (19, "泡沫光線"), (30, "泰山壓頂")]
L_ABRA = [(1, "念力"), (18, "暗影球"), (26, "精神強念")]
L_MACHOP = [(1, "撞擊"), (1, "空手劈"), (15, "落石"), (30, "十字劈"), (35, "地震")]
L_GEO = [(1, "撞擊"), (6, "落石"), (15, "挖洞"), (25, "岩崩"), (36, "地震")]
L_GASTLY = [(1, "舌舔"), (10, "毒針"), (20, "暗影球"), (30, "污泥炸彈")]
L_ONIX = [(1, "撞擊"), (1, "落石"), (19, "岩崩"), (40, "地震")]
L_MAGI = [(1, "撞擊")]
L_GYARA = [(1, "撞擊"), (1, "水槍"), (20, "咬住"), (25, "龍息"), (32, "水砲"), (41, "破壞死光")]
L_EEVEE = [(1, "撞擊"), (8, "電光一閃"), (16, "咬住"), (30, "猛撞")]
L_SNOR = [(1, "撞擊"), (1, "咬住"), (10, "泰山壓頂"), (35, "破壞死光")]
L_DRAT = [(1, "撞擊"), (5, "龍息"), (25, "冰凍光束"), (30, "龍爪"), (45, "破壞死光")]
L_MEW = [(1, "念力"), (1, "精神強念"), (50, "暗影球"), (55, "冰凍光束"), (60, "十萬伏特")]


def _sp(name, types, base, learn, evo=None, catch=45):
    """base = (HP, 攻擊, 防禦, 速度)；evo = (進化等級, 進化後編號)"""
    return {"name": name, "types": types, "base": base, "learn": sorted(learn), "evo": evo, "catch": catch}


SPECIES = {
    1: _sp("妙蛙種子", ["草", "毒"], (45, 49, 49, 45), L_BULBA, (16, 2)),
    2: _sp("妙蛙草", ["草", "毒"], (60, 62, 63, 60), L_BULBA, (32, 3)),
    3: _sp("妙蛙花", ["草", "毒"], (80, 82, 83, 80), L_BULBA),
    4: _sp("小火龍", ["火"], (39, 52, 43, 65), L_CHAR, (16, 5)),
    5: _sp("火恐龍", ["火"], (58, 64, 58, 80), L_CHAR, (36, 6)),
    6: _sp("噴火龍", ["火", "飛行"], (78, 84, 78, 100), L_CHAR + [(36, "翅膀攻擊")]),
    7: _sp("傑尼龜", ["水"], (44, 48, 65, 43), L_SQUIR, (16, 8)),
    8: _sp("卡咪龜", ["水"], (59, 63, 80, 58), L_SQUIR, (36, 9)),
    9: _sp("水箭龜", ["水"], (79, 83, 100, 78), L_SQUIR),
    10: _sp("綠毛蟲", ["蟲"], (45, 30, 35, 45), L_CATER, (7, 11), 255),
    11: _sp("鐵甲蛹", ["蟲"], (50, 20, 55, 30), L_CATER, (10, 12), 120),
    12: _sp("巴大蝶", ["蟲", "飛行"], (60, 70, 50, 70), L_BUTTER),
    16: _sp("波波", ["一般", "飛行"], (40, 45, 40, 56), L_PIDGEY, (18, 17), 255),
    17: _sp("比比鳥", ["一般", "飛行"], (63, 60, 55, 71), L_PIDGEY, (36, 18), 120),
    18: _sp("比雕", ["一般", "飛行"], (83, 80, 75, 101), L_PIDGEY),
    19: _sp("小拉達", ["一般"], (30, 56, 35, 72), L_RAT, (20, 20), 255),
    20: _sp("拉達", ["一般"], (55, 81, 60, 97), L_RAT, None, 127),
    25: _sp("皮卡丘", ["電"], (35, 55, 40, 90), L_PIKA, (30, 26), 190),
    26: _sp("雷丘", ["電"], (60, 90, 55, 110), L_PIKA, None, 75),
    39: _sp("胖丁", ["一般"], (115, 45, 20, 20), L_JIGGLY, None, 170),
    41: _sp("超音蝠", ["毒", "飛行"], (40, 45, 35, 55), L_ZUBAT, (22, 42), 255),
    42: _sp("大嘴蝠", ["毒", "飛行"], (75, 80, 70, 90), L_ZUBAT, None, 90),
    50: _sp("地鼠", ["地面"], (10, 55, 25, 95), L_DIG, (26, 51), 255),
    51: _sp("三地鼠", ["地面"], (35, 80, 50, 120), L_DIG, None, 50),
    52: _sp("喵喵", ["一般"], (40, 45, 35, 90), L_MEOWTH, None, 255),
    54: _sp("可達鴨", ["水"], (50, 60, 48, 55), L_PSY, None, 190),
    58: _sp("卡蒂狗", ["火"], (55, 70, 45, 60), L_GROWL, None, 190),
    60: _sp("蚊香蝌蚪", ["水"], (40, 50, 40, 90), L_POLI, None, 255),
    63: _sp("凱西", ["超能力"], (25, 80, 15, 90), L_ABRA, (16, 64), 200),
    64: _sp("勇基拉", ["超能力"], (40, 95, 30, 105), L_ABRA, None, 100),
    66: _sp("腕力", ["格鬥"], (70, 80, 50, 35), L_MACHOP, None, 180),
    74: _sp("小拳石", ["岩石", "地面"], (40, 80, 100, 20), L_GEO, (25, 75), 255),
    75: _sp("隆隆石", ["岩石", "地面"], (55, 95, 115, 35), L_GEO, None, 120),
    92: _sp("鬼斯", ["幽靈", "毒"], (30, 75, 35, 80), L_GASTLY, (25, 93), 190),
    93: _sp("鬼斯通", ["幽靈", "毒"], (45, 90, 45, 95), L_GASTLY, None, 90),
    95: _sp("大岩蛇", ["岩石", "地面"], (35, 45, 160, 70), L_ONIX),
    129: _sp("鯉魚王", ["水"], (20, 10, 55, 80), L_MAGI, (20, 130), 255),
    130: _sp("暴鯉龍", ["水", "飛行"], (95, 125, 79, 81), L_GYARA),
    133: _sp("伊布", ["一般"], (55, 55, 50, 55), L_EEVEE),
    143: _sp("卡比獸", ["一般"], (160, 110, 65, 30), L_SNOR, None, 25),
    147: _sp("迷你龍", ["龍"], (41, 64, 45, 50), L_DRAT, (30, 148)),
    148: _sp("哈克龍", ["龍"], (61, 84, 65, 70), L_DRAT, (55, 149)),
    149: _sp("快龍", ["龍", "飛行"], (91, 134, 95, 80), L_DRAT + [(55, "翅膀攻擊")]),
    150: _sp("超夢", ["超能力"], (106, 130, 90, 130), L_MEW, None, 3),
}

STARTERS = [1, 4, 7, 25]

# 區域：需要徽章數、等級範圍、出現的寶可夢 (編號, 權重)
AREAS = {
    "🌲 常青森林": {"req": 0, "lv": (2, 6), "desc": "新手訓練家的第一站，蟲和鳥很多。",
                   "mons": [(10, 30), (16, 30), (19, 30), (25, 8)]},
    "⛰️ 月見山": {"req": 0, "lv": (7, 13), "desc": "陰暗的洞窟，小心超音蝠。",
                 "mons": [(41, 35), (74, 30), (39, 15), (50, 15), (66, 10)]},
    "🌊 華藍海岸": {"req": 1, "lv": (12, 20), "desc": "陽光沙灘，水系寶可夢的天堂。",
                  "mons": [(129, 30), (60, 25), (54, 20), (52, 15), (58, 10)]},
    "🏚️ 紫苑塔": {"req": 2, "lv": (18, 28), "desc": "傳說有幽靈出沒的高塔……",
                 "mons": [(92, 40), (63, 20), (95, 15), (133, 10), (93, 5)]},
    "🐉 龍之谷": {"req": 3, "lv": (28, 40), "desc": "強大的龍系寶可夢棲息之地。",
                 "mons": [(147, 30), (148, 10), (130, 15), (143, 10), (42, 20), (51, 15)]},
    "❓ 未知洞窟": {"req": 4, "lv": (45, 60), "desc": "只有冠軍才能進入，據說有傳說中的寶可夢。",
                  "mons": [(150, 5), (149, 20), (64, 25), (93, 25), (75, 25)]},
}

GYMS = [
    {"name": "尼比道館", "leader": "小剛", "badge": "灰色徽章", "reward": 1500, "team": [(74, 12), (95, 14)]},
    {"name": "華藍道館", "leader": "小霞", "badge": "藍色徽章", "reward": 2500, "team": [(60, 18), (54, 21)]},
    {"name": "枯葉道館", "leader": "馬志士", "badge": "橙色徽章", "reward": 3500,
     "team": [(25, 25), (25, 26), (26, 29)]},
    {"name": "冠軍之路", "leader": "冠軍阿渡", "badge": "冠軍獎盃", "reward": 8000,
     "team": [(130, 38), (148, 38), (6, 40), (149, 45)]},
]

SHOP = {"精靈球": 200, "超級球": 600, "高級球": 1200, "傷藥": 300, "全滿藥": 1500, "活力碎片": 1500}
BALLS = {"精靈球": 1.0, "超級球": 1.5, "高級球": 2.0, "大師球": 0}
HEAL_ITEMS = ["傷藥", "全滿藥", "活力碎片"]
SAVE_KEYS = ["started", "player", "money", "badges", "party", "box", "bag", "seen", "caught"]

# ----------------------------------------------------------------------------
# 寶可夢邏輯
# ----------------------------------------------------------------------------


def name(mon):
    return SPECIES[mon["sid"]]["name"]


def types(mon):
    return SPECIES[mon["sid"]]["types"]


def stats(mon):
    hp, atk, df, spd = SPECIES[mon["sid"]]["base"]
    lv = mon["lvl"]
    return {"hp": hp * 2 * lv // 100 + lv + 10, "atk": atk * 2 * lv // 100 + 5,
            "def": df * 2 * lv // 100 + 5, "spd": spd * 2 * lv // 100 + 5}


def xp_need(lvl):
    return 8 * lvl + 20


def effectiveness(mtype, def_types):
    mult = 1.0
    for t in def_types:
        mult *= TYPE_CHART.get(mtype, {}).get(t, 1.0)
    return mult


def new_mon(sid, lvl):
    moves = []
    for lv, mv in SPECIES[sid]["learn"]:
        if lv <= lvl and mv not in moves:
            moves.append(mv)
    mon = {"sid": sid, "lvl": lvl, "xp": 0, "moves": moves[-4:]}
    mon["hp"] = stats(mon)["hp"]
    return mon


def register(sid, caught=False):
    if sid not in S.seen:
        S.seen.append(sid)
    if caught and sid not in S.caught:
        S.caught.append(sid)


def log(msg):
    if S.battle:
        S.battle["log"].append(msg)
    else:
        S.toasts.append(msg)


def learn_moves(mon):
    for lv, mv in SPECIES[mon["sid"]]["learn"]:
        if lv != mon["lvl"] or mv in mon["moves"]:
            continue
        if len(mon["moves"]) < 4:
            mon["moves"].append(mv)
            log(f"📘 {name(mon)} 學會了 **{mv}**！")
        else:
            weakest = min(mon["moves"], key=lambda m: MOVES[m][1])
            if MOVES[mv][1] > MOVES[weakest][1]:
                mon["moves"][mon["moves"].index(weakest)] = mv
                log(f"📘 {name(mon)} 忘記了 {weakest}，學會了 **{mv}**！")


def check_evo(mon):
    evo = SPECIES[mon["sid"]]["evo"]
    if evo and mon["lvl"] >= evo[0]:
        old_name, old_max = name(mon), stats(mon)["hp"]
        mon["sid"] = evo[1]
        mon["hp"] += stats(mon)["hp"] - old_max
        log(f"✨ 咦？{old_name} 進化成了 **{name(mon)}**！")
        register(mon["sid"], caught=True)
        learn_moves(mon)


def gain_xp(mon, amount):
    mon["xp"] += amount
    while mon["lvl"] < 100 and mon["xp"] >= xp_need(mon["lvl"]):
        mon["xp"] -= xp_need(mon["lvl"])
        old_max = stats(mon)["hp"]
        mon["lvl"] += 1
        mon["hp"] += stats(mon)["hp"] - old_max
        log(f"⬆️ {name(mon)} 升到了 Lv.{mon['lvl']}！")
        learn_moves(mon)
        check_evo(mon)


def heal_all():
    for m in S.party + S.box:
        m["hp"] = stats(m)["hp"]


def first_alive():
    return next((i for i, m in enumerate(S.party) if m["hp"] > 0), None)


def apply_heal(mon, item):
    """使用回復道具，成功回傳訊息，無效回傳 None。"""
    mx = stats(mon)["hp"]
    if item == "活力碎片":
        if mon["hp"] > 0:
            return None
        mon["hp"] = mx // 2
        return f"{name(mon)} 恢復了意識！"
    if mon["hp"] <= 0 or mon["hp"] >= mx:
        return None
    before = mon["hp"]
    mon["hp"] = mx if item == "全滿藥" else min(mx, mon["hp"] + 50)
    return f"{name(mon)} 回復了 {mon['hp'] - before} HP。"

# ----------------------------------------------------------------------------
# 戰鬥
# ----------------------------------------------------------------------------


def foe():
    return S.battle["enemies"][S.battle["ei"]]


def me():
    return S.party[S.battle["active"]]


def foe_prefix():
    return "野生的" if S.battle["kind"] == "wild" else f"{S.battle['leader']}的"


def calc_damage(att, dfn, move):
    mtype, power, acc = MOVES[move]
    if random.randint(1, 100) > acc:
        return None
    a, d = stats(att)["atk"], stats(dfn)["def"]
    base = ((2 * att["lvl"] / 5 + 2) * power * a / d) / 50 + 2
    stab = 1.5 if mtype in types(att) else 1.0
    eff = effectiveness(mtype, types(dfn))
    crit = random.random() < 1 / 16
    dmg = int(base * stab * eff * (1.5 if crit else 1.0) * random.uniform(0.85, 1.0))
    if eff > 0:
        dmg = max(1, dmg)
    return dmg, eff, crit


def attack(att, dfn, move, is_player):
    who = "我方的" if is_player else foe_prefix()
    log(f"{who} {name(att)} 使用了 **{move}**！")
    res = calc_damage(att, dfn, move)
    if res is None:
        log("但是沒有命中！")
        return
    dmg, eff, crit = res
    if eff == 0:
        log(f"對 {name(dfn)} 好像沒有效果……")
        return
    dfn["hp"] = max(0, dfn["hp"] - dmg)
    if crit:
        log("💥 擊中要害！")
    if eff > 1:
        log("🔥 效果絕佳！")
    elif eff < 1:
        log("效果不太好……")
    log(f"造成了 {dmg} 點傷害。")


def enemy_choose(f, m):
    if random.random() < 0.6:
        def score(mv):
            t, p, _ = MOVES[mv]
            return p * effectiveness(t, types(m)) * (1.5 if t in types(f) else 1.0)
        return max(f["moves"], key=score)
    return random.choice(f["moves"])


def start_battle(kind, enemies, intro, leader=None, gym=None):
    S.battle = {"kind": kind, "enemies": enemies, "ei": 0, "active": first_alive(),
                "log": [intro], "must_switch": False, "over": False, "result": None,
                "leader": leader, "gym": gym}
    register(enemies[0]["sid"])
    log(f"上吧！{name(me())}！")


def start_wild(area_key):
    if first_alive() is None:
        S.toasts.append("你的寶可夢都倒下了，先去寶可夢中心吧！")
        return
    area = AREAS[area_key]
    sids, weights = zip(*area["mons"])
    sid = random.choices(sids, weights)[0]
    lvl = random.randint(*area["lv"])
    start_battle("wild", [new_mon(sid, lvl)], f"野生的 **{SPECIES[sid]['name']}** (Lv.{lvl}) 跳出來了！")


def start_gym(i):
    if first_alive() is None:
        S.toasts.append("你的寶可夢都倒下了，先去寶可夢中心吧！")
        return
    gym = GYMS[i]
    enemies = [new_mon(sid, lv) for sid, lv in gym["team"]]
    start_battle("trainer", enemies,
                 f"**{gym['leader']}** 向你發起挑戰！{gym['leader']} 派出了 **{name(enemies[0])}** (Lv.{enemies[0]['lvl']})！",
                 leader=gym["leader"], gym=i)


def resolve():
    if foe()["hp"] <= 0:
        enemy_fainted()
    elif me()["hp"] <= 0:
        player_fainted()


def enemy_turn():
    f, m = foe(), me()
    attack(f, m, enemy_choose(f, m), False)
    resolve()


def enemy_fainted():
    b, f, m = S.battle, foe(), me()
    log(f"{foe_prefix()} {name(f)} 倒下了！")
    gain = int(sum(SPECIES[f["sid"]]["base"]) // 3 * f["lvl"] / 7 * (1.5 if b["kind"] == "trainer" else 1.0))
    log(f"{name(m)} 獲得了 {gain} 點經驗值。")
    gain_xp(m, gain)
    share = gain * 3 // 10
    others = [o for j, o in enumerate(S.party) if j != b["active"] and o["hp"] > 0]
    if others and share > 0:
        log(f"其他隊員透過學習裝置各獲得了 {share} 點經驗值。")
        for o in others:
            gain_xp(o, share)
    if b["ei"] + 1 < len(b["enemies"]):
        b["ei"] += 1
        nf = foe()
        register(nf["sid"])
        log(f"{b['leader']} 派出了 **{name(nf)}** (Lv.{nf['lvl']})！")
    else:
        win()


def win():
    b = S.battle
    b["over"], b["result"] = True, "win"
    if b["kind"] == "wild":
        money = b["enemies"][-1]["lvl"] * 10
        S.money += money
        log(f"💰 撿到了 {money} 元。")
        return
    gym = GYMS[b["gym"]]
    S.money += gym["reward"]
    log(f"🏆 你打敗了 {gym['leader']}！獲得 {gym['reward']} 元。")
    if S.badges == b["gym"]:
        S.badges += 1
        log(f"🎖️ 獲得了 **{gym['badge']}**！")
        if b["gym"] == len(GYMS) - 1:
            S.bag["大師球"] = S.bag.get("大師球", 0) + 1
            log("🎁 獲得了 **大師球** ×1！")
            log("🎉🎉 恭喜你成為寶可夢聯盟冠軍！「未知洞窟」已經開放！")


def player_fainted():
    b, m = S.battle, me()
    log(f"我方的 {name(m)} 倒下了！")
    if first_alive() is not None:
        b["must_switch"] = True
        log("請選擇下一隻寶可夢！")
    else:
        lost = S.money // 2
        S.money -= lost
        log(f"💀 你的寶可夢全部倒下了……慌亂中掉了 {lost} 元，被送回了寶可夢中心。")
        heal_all()
        b["over"], b["result"] = True, "lose"


def act_move(i):
    m, f = me(), foe()
    mv, fmv = m["moves"][i], enemy_choose(f, m)
    ms, fs = stats(m)["spd"], stats(f)["spd"]
    if ms > fs or (ms == fs and random.random() < 0.5):
        attack(m, f, mv, True)
        if f["hp"] > 0:
            attack(f, m, fmv, False)
    else:
        attack(f, m, fmv, False)
        if m["hp"] > 0:
            attack(m, f, mv, True)
    resolve()


def act_ball(ball):
    b, f = S.battle, foe()
    if b["kind"] != "wild" or S.bag.get(ball, 0) <= 0:
        return
    S.bag[ball] -= 1
    log(f"你丟出了 {ball}！")
    if ball == "大師球":
        p = 1.0
    else:
        mx = stats(f)["hp"]
        a = (3 * mx - 2 * f["hp"]) * SPECIES[f["sid"]]["catch"] * BALLS[ball] / (3 * mx)
        p = min(1.0, a / 255)
    if random.random() < p:
        log(f"🎉 抓到了 **{name(f)}**！")
        register(f["sid"], caught=True)
        if len(S.party) < 6:
            S.party.append(f)
        else:
            S.box.append(f)
            log("隊伍已滿，已傳送到電腦箱。")
        b["over"], b["result"] = True, "catch"
    else:
        log(random.choice(["哎呀！寶可夢掙脫了！", "可惡！差一點就抓到了！", "看起來快要抓到了……"]))
        enemy_turn()


def act_item(item):
    if S.bag.get(item, 0) <= 0:
        return
    msg = apply_heal(me(), item)
    if msg is None:
        log(f"現在使用 {item} 不會有效果。")
        return
    S.bag[item] -= 1
    log(f"使用了 {item}，{msg}")
    enemy_turn()


def act_switch(i):
    b = S.battle
    if i == b["active"] or S.party[i]["hp"] <= 0:
        return
    if b["must_switch"]:
        b["active"], b["must_switch"] = i, False
        log(f"上吧！{name(me())}！")
    else:
        log(f"回來吧，{name(me())}！上吧，{name(S.party[i])}！")
        b["active"] = i
        enemy_turn()


def act_run():
    b = S.battle
    if b["kind"] != "wild":
        log("不能從訓練家對戰中逃跑！")
        return
    if stats(me())["spd"] >= stats(foe())["spd"] or random.random() < 0.5:
        log("順利逃走了！")
        b["over"], b["result"] = True, "run"
    else:
        log("逃跑失敗！")
        enemy_turn()


def leave_battle():
    S.battle = None

# ----------------------------------------------------------------------------
# 地圖 / 選單動作
# ----------------------------------------------------------------------------


def init_state():
    if "started" in S:
        return
    S.started = False
    S.player = ""
    S.money = 3000
    S.badges = 0
    S.party, S.box = [], []
    S.bag = {"精靈球": 5, "超級球": 0, "高級球": 0, "大師球": 0, "傷藥": 3, "全滿藥": 0, "活力碎片": 0}
    S.seen, S.caught = [], []
    S.battle = None
    S.toasts = []


def start_game(sid):
    S.player = S.get("name_input", "").strip() or "小智"
    S.party = [new_mon(sid, 5)]
    register(sid, caught=True)
    S.started = True
    S.toasts.append(f"你選擇了 {SPECIES[sid]['name']}！冒險開始！")


def reset_game():
    for k in list(S.keys()):
        del S[k]


def heal_center():
    heal_all()
    S.toasts.append("👩‍⚕️ 你的寶可夢都恢復健康了！歡迎再來！")


def buy(item, qty):
    cost = SHOP[item] * qty
    if S.money < cost:
        S.toasts.append("錢不夠喔！")
        return
    S.money -= cost
    S.bag[item] = S.bag.get(item, 0) + qty
    S.toasts.append(f"買了 {item} ×{qty}")


def set_lead(i):
    S.party.insert(0, S.party.pop(i))


def deposit(i):
    if len(S.party) > 1:
        S.box.append(S.party.pop(i))


def withdraw(i):
    if len(S.party) < 6:
        S.party.append(S.box.pop(i))


def release(i):
    m = S.box.pop(i)
    S.toasts.append(f"你放生了 {name(m)}，再見了！")


def use_item_map(item, i):
    msg = apply_heal(S.party[i], item)
    if msg is None:
        S.toasts.append(f"現在使用 {item} 不會有效果。")
        return
    S.bag[item] -= 1
    S.toasts.append(msg)


def load_game():
    f = S.get("upload")
    if f is None:
        S.toasts.append("請先選擇存檔檔案。")
        return
    try:
        data = json.loads(f.getvalue().decode("utf-8"))
        for k in SAVE_KEYS:
            S[k] = data[k]
        S.battle = None
        S.toasts.append("讀檔成功！")
    except (ValueError, KeyError):
        S.toasts.append("存檔檔案格式錯誤。")

# ----------------------------------------------------------------------------
# 介面
# ----------------------------------------------------------------------------


CSS = """
<style>
.hpwrap{background:#ddd;border-radius:6px;height:12px;width:100%;overflow:hidden;margin:4px 0 2px}
.hpfill{height:100%;border-radius:6px;transition:width .4s}
.hptext{font-size:.85rem;opacity:.8}
.tb{color:#fff;padding:1px 8px;border-radius:10px;font-size:.75rem;margin-right:4px;
    text-shadow:0 1px 1px rgba(0,0,0,.4)}
.newline{background:rgba(255,213,0,.22);border-radius:4px;padding:0 4px}
.battlelog{background:rgba(127,127,127,.08);border-left:4px solid #e3350d;padding:8px 12px;
    border-radius:6px;min-height:150px;font-size:.95rem;line-height:1.6}
</style>
"""


def type_badges(ts):
    return "".join(f"<span class='tb' style='background:{TYPE_COLOR[t]}'>{t}</span>" for t in ts)


def hp_bar(mon):
    mx = stats(mon)["hp"]
    pct = mon["hp"] / mx * 100 if mx else 0
    color = "#4caf50" if pct > 50 else "#ffc107" if pct > 20 else "#f44336"
    return (f"<div class='hpwrap'><div class='hpfill' style='width:{pct:.0f}%;background:{color}'></div></div>"
            f"<div class='hptext'>HP {mon['hp']} / {mx}</div>")


def mon_header(mon):
    st.markdown(f"**{name(mon)}** &nbsp;Lv.{mon['lvl']}<br>{type_badges(types(mon))}{hp_bar(mon)}",
                unsafe_allow_html=True)


def render_start():
    st.title("⚡ 寶可夢冒險")
    st.write("歡迎來到寶可夢的世界！我是大木博士。首先，請告訴我你的名字。")
    st.text_input("訓練家名字", key="name_input", placeholder="小智")
    st.write("接著，從下面挑選你的第一隻寶可夢吧！")
    cols = st.columns(len(STARTERS))
    for col, sid in zip(cols, STARTERS):
        sp = SPECIES[sid]
        with col:
            st.image(SPRITE.format(sid), width=96)
            st.markdown(f"**{sp['name']}**<br>{type_badges(sp['types'])}", unsafe_allow_html=True)
            st.button("就決定是你了！", key=f"starter{sid}", on_click=start_game, args=(sid,),
                      use_container_width=True)
    with st.expander("📂 已經有存檔？在這裡讀取"):
        st.file_uploader("選擇存檔 (.json)", type="json", key="upload")
        st.button("讀取存檔", on_click=load_game)


def render_battle():
    b = S.battle
    f, m = foe(), me()
    title = "野生寶可夢對戰" if b["kind"] == "wild" else f"🏟️ {GYMS[b['gym']]['name']} — {b['leader']}"
    st.subheader(title)
    if b["kind"] == "trainer":
        left = len(b["enemies"]) - b["ei"]
        st.caption("對手剩餘寶可夢：" + "🔴" * left + "⚫" * (len(b["enemies"]) - left))

    c1, c2 = st.columns([3, 2])
    with c1:
        mon_header(f)
    with c2:
        st.image(SPRITE.format(f["sid"]), width=140)
    c3, c4 = st.columns([2, 3])
    with c3:
        st.image(SPRITE_BACK.format(m["sid"]), width=140)
    with c4:
        mon_header(m)
        need = xp_need(m["lvl"])
        st.progress(min(1.0, m["xp"] / need), text=f"EXP {m['xp']} / {need}")

    if b["over"]:
        label = {"win": "勝利！繼續冒險", "catch": "太好了！繼續冒險", "run": "繼續冒險",
                 "lose": "回到寶可夢中心"}[b["result"]]
        st.button(label, on_click=leave_battle, type="primary", use_container_width=True)
    elif b["must_switch"]:
        st.warning("選擇下一隻上場的寶可夢：")
        render_switch_buttons()
    else:
        render_battle_actions(b, m, f)
    render_battle_log(b)


def render_battle_log(b):
    """戰鬥訊息放在按鈕下方，本回合新增的訊息以黃色底標示。"""
    lines = b["log"][-10:]
    new_from = len(lines) - (len(b["log"]) - b.get("shown", 0))
    html = []
    for k, line in enumerate(lines):
        line = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", line)
        html.append(f"<div class='newline'>{line}</div>" if k >= new_from else f"<div>{line}</div>")
    b["shown"] = len(b["log"])
    st.markdown("**📜 戰鬥訊息**")
    st.markdown(f"<div class='battlelog'>{''.join(html)}</div>", unsafe_allow_html=True)


def render_battle_actions(b, m, f):
    st.markdown("**⚔️ 招式**（點擊即攻擊）")
    cols = st.columns(2)
    for i, mv in enumerate(m["moves"]):
        t, p, acc = MOVES[mv]
        eff = effectiveness(t, types(f))
        hint = " ⬆️" if eff > 1 else " ⬇️" if 0 < eff < 1 else " ✖️" if eff == 0 else ""
        cols[i % 2].button(f"{mv}｜{t}｜威力{p}{hint}", key=f"mv{i}", on_click=act_move, args=(i,),
                           type="primary", use_container_width=True)

    st.markdown("**🎒 背包**（數量為 0 的道具無法使用）")
    if b["kind"] == "wild":
        bcols = st.columns(4)
        for col, ball in zip(bcols, BALLS):
            col.button(f"{ball} ×{S.bag.get(ball, 0)}", key=f"ball{ball}", on_click=act_ball,
                       args=(ball,), disabled=S.bag.get(ball, 0) <= 0, use_container_width=True)
    hcols = st.columns(3)
    for col, item in zip(hcols, ["傷藥", "全滿藥"]):
        col.button(f"{item} ×{S.bag.get(item, 0)}", key=f"bi{item}", on_click=act_item, args=(item,),
                   disabled=S.bag.get(item, 0) <= 0, use_container_width=True)
    hcols[2].button("🏃 逃跑", key="run", on_click=act_run, disabled=b["kind"] != "wild",
                    use_container_width=True)

    if len(S.party) > 1:
        st.markdown("**🔄 換寶可夢**（會被對手攻擊一次）")
        render_switch_buttons()


def render_switch_buttons():
    b = S.battle
    cols = st.columns(3)
    for i, pm in enumerate(S.party):
        mx = stats(pm)["hp"]
        cols[i % 3].button(f"{name(pm)} Lv.{pm['lvl']} ({pm['hp']}/{mx})", key=f"sw{i}",
                           on_click=act_switch, args=(i,),
                           disabled=(i == b["active"] or pm["hp"] <= 0), use_container_width=True)


def render_map():
    badges = "".join("🎖️" for _ in range(S.badges)) or "—"
    st.title("⚡ 寶可夢冒險")
    c1, c2, c3 = st.columns(3)
    c1.metric("訓練家", S.player)
    c2.metric("金錢", f"₽{S.money:,}")
    c3.metric("徽章", f"{S.badges} / {len(GYMS)}")
    st.caption(f"徽章：{badges}")

    tabs = st.tabs(["🗺️ 探索", "🏟️ 道館", "🏥 中心", "🛒 商店", "🎒 隊伍", "💻 電腦", "📖 圖鑑", "💾 存檔"])
    with tabs[0]:
        render_explore()
    with tabs[1]:
        render_gyms()
    with tabs[2]:
        st.subheader("🏥 寶可夢中心")
        st.write("歡迎來到寶可夢中心！我們可以免費幫你的寶可夢恢復健康。")
        st.button("讓寶可夢休息一下", on_click=heal_center, type="primary")
    with tabs[3]:
        render_shop()
    with tabs[4]:
        render_party()
    with tabs[5]:
        render_box()
    with tabs[6]:
        render_dex()
    with tabs[7]:
        render_save()


def render_explore():
    if first_alive() is None:
        st.error("你的寶可夢都倒下了，請先到寶可夢中心！")
    for key, area in AREAS.items():
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            c1.markdown(f"**{key}** &nbsp; Lv.{area['lv'][0]}–{area['lv'][1]}<br>"
                        f"<span style='opacity:.75'>{area['desc']}</span>", unsafe_allow_html=True)
            if S.badges < area["req"]:
                c2.button(f"🔒 需{area['req']}枚徽章", key=f"area{key}", disabled=True, use_container_width=True)
            else:
                c2.button("走進草叢", key=f"area{key}", on_click=start_wild, args=(key,),
                          use_container_width=True)


def render_gyms():
    for i, gym in enumerate(GYMS):
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            team = "、".join(f"{SPECIES[s]['name'] if s in S.seen else '???'} Lv.{lv}" for s, lv in gym["team"])
            done = "✅ " if S.badges > i else ""
            c1.markdown(f"{done}**{gym['name']}** — {gym['leader']}<br>"
                        f"<span style='opacity:.75'>獎勵：{gym['badge']}、₽{gym['reward']}<br>隊伍：{team}</span>",
                        unsafe_allow_html=True)
            if S.badges < i:
                c2.button("🔒 未解鎖", key=f"gym{i}", disabled=True, use_container_width=True)
            else:
                c2.button("再戰" if S.badges > i else "挑戰！", key=f"gym{i}", on_click=start_gym, args=(i,),
                          type="secondary" if S.badges > i else "primary", use_container_width=True)


def render_shop():
    st.subheader("🛒 友好商店")
    desc = {"精靈球": "基本的捕捉道具", "超級球": "捕捉率 ×1.5", "高級球": "捕捉率 ×2",
            "傷藥": "回復 50 HP", "全滿藥": "HP 全滿", "活力碎片": "讓倒下的寶可夢復活（一半 HP）"}
    for item, price in SHOP.items():
        c1, c2, c3 = st.columns([3, 1, 1])
        c1.markdown(f"**{item}** ₽{price}　持有 {S.bag.get(item, 0)}<br>"
                    f"<span style='opacity:.7;font-size:.85rem'>{desc[item]}</span>", unsafe_allow_html=True)
        c2.button("買 1", key=f"buy1{item}", on_click=buy, args=(item, 1), use_container_width=True)
        c3.button("買 5", key=f"buy5{item}", on_click=buy, args=(item, 5), use_container_width=True)
    if S.bag.get("大師球"):
        st.info(f"🟣 大師球 ×{S.bag['大師球']}（必定捕捉成功）")


def render_party():
    st.subheader("🎒 我的隊伍")
    for i, m in enumerate(S.party):
        with st.container(border=True):
            c1, c2, c3 = st.columns([1, 3, 2])
            c1.image(SPRITE.format(m["sid"]), width=80)
            with c2:
                mon_header(m)
                s = stats(m)
                st.caption(f"攻擊 {s['atk']}｜防禦 {s['def']}｜速度 {s['spd']}｜EXP {m['xp']}/{xp_need(m['lvl'])}")
                st.caption("招式：" + "、".join(m["moves"]))
            with c3:
                if i > 0:
                    st.button("設為首發", key=f"lead{i}", on_click=set_lead, args=(i,), use_container_width=True)
                if len(S.party) > 1:
                    st.button("存入電腦", key=f"dep{i}", on_click=deposit, args=(i,), use_container_width=True)
                for item in HEAL_ITEMS:
                    if S.bag.get(item, 0) > 0:
                        st.button(f"用{item} ({S.bag[item]})", key=f"use{item}{i}", on_click=use_item_map,
                                  args=(item, i), use_container_width=True)


def render_box():
    st.subheader("💻 電腦箱")
    if not S.box:
        st.caption("電腦箱裡空空的。隊伍滿 6 隻後抓到的寶可夢會送到這裡。")
    for i, m in enumerate(S.box):
        c1, c2, c3, c4 = st.columns([1, 3, 1, 1])
        c1.image(SPRITE.format(m["sid"]), width=56)
        c2.markdown(f"**{name(m)}** Lv.{m['lvl']}<br>{type_badges(types(m))}", unsafe_allow_html=True)
        c3.button("領出", key=f"wd{i}", on_click=withdraw, args=(i,), disabled=len(S.party) >= 6)
        c4.button("放生", key=f"rl{i}", on_click=release, args=(i,))


def render_dex():
    st.subheader(f"📖 圖鑑　已見 {len(S.seen)}／已捕捉 {len(S.caught)}／共 {len(SPECIES)}")
    cols = st.columns(5)
    for k, sid in enumerate(sorted(SPECIES)):
        with cols[k % 5]:
            if sid in S.seen:
                st.image(SPRITE.format(sid), width=72)
                mark = "✅" if sid in S.caught else "👁️"
                st.caption(f"{mark} No.{sid:03d} {SPECIES[sid]['name']}")
            else:
                st.markdown("<div style='height:72px;font-size:2.4rem;text-align:center'>❓</div>",
                            unsafe_allow_html=True)
                st.caption(f"No.{sid:03d} ？？？")


def render_save():
    st.subheader("💾 存檔")
    st.write("Streamlit Cloud 不會長期保存遊戲進度（重新整理頁面就會重置），請下載存檔檔案，下次再上傳讀取。")
    data = json.dumps({k: S[k] for k in SAVE_KEYS}, ensure_ascii=False, indent=1)
    st.download_button("⬇️ 下載存檔", data, file_name=f"pokemon_save_{S.player}.json", mime="application/json",
                       type="primary")
    st.file_uploader("⬆️ 上傳存檔 (.json)", type="json", key="upload")
    st.button("讀取存檔", on_click=load_game)
    st.divider()
    st.button("🗑️ 重新開始新遊戲", on_click=reset_game)


def main():
    init_state()
    st.markdown(CSS, unsafe_allow_html=True)
    for t in S.toasts:
        st.toast(t)
    S.toasts = []
    if not S.started:
        render_start()
    elif S.battle:
        render_battle()
    else:
        render_map()
    st.caption("非官方粉絲作品，僅供學習交流。Pokémon © Nintendo / Creatures / GAME FREAK。圖片來源：PokeAPI。")


main()
