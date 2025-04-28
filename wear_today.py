import streamlit as st
import random
import itertools

# ── 必须最先调用 ────────────────────────────────────
st.set_page_config(page_title="今天穿什么呢 · 权重版", layout="centered")

"""
👕 今天穿什么呢 - 权重算法版
• 单品权重 0.5 步进
• 温度 ➜ 上/下目标权重
• 体感偏好：正常 / 怕冷(+1,+0.5) / 怕热(-1,-0.5)
• 每次输出两套（常规+加衣/减衣 / 精准+随机微调）
• 误差 ≤ ±0.5
"""

# ---------- 上身单品池 & 权重 ----------
TOP_POOLS = {
    "打底短袖":   (1.0, ["基础短袖T恤", "运动速干短袖", "Polo短袖"]),
    "打底长袖薄": (1.5, ["基础长袖T恤", "薄衬衫", "薄针织衫"]),
    "打底长袖厚": (2.5, ["加绒长袖T", "厚卫衣", "羊毛打底衫"]),
    "中层薄":     (2.0, ["薄卫衣", "薄毛衣", "针织开衫"]),
    "中层厚":     (3.0, ["厚毛衣", "抓绒卫衣", "加绒衬衫"]),
    "外套薄":     (2.5, ["轻便风衣", "牛仔夹克", "薄西装外套", "防风夹克"]),
    "外套厚":     (4.0, ["棉服", "羊羔毛夹克", "呢大衣"]),
    "羽绒服":     (5.0, ["中长羽绒服"]),  # 与外套厚不同键 → 允许双外套
    "额外保暖层": (2.5, ["羽绒背心", "加绒背心", "厚马甲"]),
}

# ---------- 下身单品池 & 权重 ----------
BOTTOM_POOLS_M = {
    "薄短": (1.0, ["休闲短裤", "运动短裤"]),
    "薄长": (1.5, ["轻薄牛仔裤", "休闲长裤", "阔腿裤", "薄西裤"]),
    "厚长": (2.5, ["加绒牛仔裤", "加绒休闲裤", "加绒运动裤", "加绒西裤"]),
    "加层": (1.5, ["秋裤", "加绒打底裤"]),
}

BOTTOM_POOLS_F = {
    "薄短": (1.0, ["休闲短裤", "运动短裤", "短裙"]),
    "薄长": (1.5, ["轻薄牛仔裤", "休闲长裤", "阔腿裤", "长裙", "薄西裤"]),
    "厚长": (2.5, ["加绒牛仔裤", "加绒休闲裤", "加绒运动裤",
                   "加绒西裤", "冬季长裙"]),
    "加层": (1.5, ["秋裤", "加绒打底裤", "保暖腿袜"]),
}

# ---------- 温度 ➜ 目标权重 ----------
TEMP_TABLE = [
    (28,  float("inf"), 1.0, 1.0),
    (24, 28,            2.0, 1.0),
    (20, 24,            3.0, 1.5),
    (16, 20,            4.0, 1.5),
    (12, 16,            5.0, 2.0),
    (9,  12,            6.0, 2.5),
    (6,  9,             7.0, 3.0),
    (3,  6,             8.0, 3.5),
    (-273, 3,           9.0, 4.0),   # ≤3℃
]

BIAS_MAP = {
    "正常": (0.0, 0.0),
    "怕冷": (1.0, 0.5),
    "怕热": (-1.0, -0.5),
}

# ---------- 工具函数 ----------
def clamp(value: float, minimum: float = 1.0) -> float:
    """权重下限保护：最薄单品权重=1.0"""
    return max(minimum, value)


def search_combos(pool_dict, target, tol=0.5, max_items=5):
    """返回贴近 target 的组合 (cat,name,weight) ，且不重复类别"""
    items = [(cat, n, w) for cat, (w, names) in pool_dict.items() for n in names]
    best, best_diff = [], float("inf")
    for r in range(1, max_items + 1):
        for combo in itertools.combinations(items, r):
            cats = [c for c, _, _ in combo]
            if len(cats) != len(set(cats)):
                continue  # 同类别重复
            total = sum(w for _, _, w in combo)
            diff = abs(total - target)
            if diff <= tol:
                if diff < best_diff:
                    best, best_diff = [combo], diff
                elif diff == best_diff:
                    best.append(combo)
    return best

# ---------- UI ----------
st.title("👕 今天穿什么呢 · 权重版")

with st.form("input"):
    col1, col2 = st.columns(2)
    with col1:
        gender = st.radio("性别", ["女性", "男性"], horizontal=True)
    with col2:
        bias_choice = st.radio("体感偏好", ["正常", "怕冷", "怕热"], horizontal=True)
    t_feel = st.number_input("体感温度 ℃", value=15.0, format="%.1f")
    submitted = st.form_submit_button("生成穿搭建议")

if submitted:
    # ---- 1. 查表读取目标 ----
    for low, high, up_base, dn_base in TEMP_TABLE:
        if low <= t_feel < high:
            break
    else:
        st.error("体感温度超出合理范围，请检查输入！")
        st.stop()

    up_delta, dn_delta = BIAS_MAP[bias_choice]

    def make_plan(u_target, d_target, label):
        tops = search_combos(TOP_POOLS, u_target)
        bottoms = search_combos(
            BOTTOM_POOLS_F if gender == "女性" else BOTTOM_POOLS_M,
            d_target
        )
        if tops and bottoms:
            return label, random.choice(tops), random.choice(bottoms)
        return None

    # ---- 2. 生成两套方案 ----
    plans = []

    # 方案 ①：精准匹配
    plans.append(make_plan(up_base, dn_base, "精准匹配"))

    # 方案 ②：随机微调 ±0.5
    shift = random.choice((0.5, -0.5))
    plans.append(make_plan(clamp(up_base + shift),
                           clamp(dn_base + shift),
                           f"微调 {shift:+.1f}"))

    # 根据体感偏好替换第二方案
    if bias_choice == "怕冷":
        plans[-1] = make_plan(up_base + up_delta,
                              dn_base + dn_delta,
                              "加衣版")
    elif bias_choice == "怕热":
        plans[-1] = make_plan(clamp(up_base + up_delta),
                              clamp(dn_base + dn_delta),
                              "减衣版")

    # ---- 3. 展示 ----
    valid = list(filter(None, plans))
    if not valid:
        st.warning("未找到符合权重的搭配，请调整温度或偏好再试～")
    else:
        st.header("推荐穿搭方案")
        for tag, top, bot in valid:
            st.subheader(tag)
            st.markdown("**上身：**")
            for cat, name, w in top:
                st.markdown(f"- {name}（{cat} · {w}）")
            st.markdown("**下身：**")
            for cat, name, w in bot:
                st.markdown(f"- {name}（{cat} · {w}）")
