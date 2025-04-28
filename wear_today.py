import streamlit as st, random, itertools

# ───────────── Streamlit 配置 ─────────────
st.set_page_config(page_title="今天穿什么呢 · 权重版", layout="centered")

# ───────────── 单品池 ─────────────
TOP_POOL_BASE = {
    "打底短袖":   (1.0, ["基础短袖T", "运动速干T"]),
    "打底长袖薄": (1.5, ["薄长袖T", "衬衫"]),
    "打底长袖厚": (2.5, ["加绒长袖T", "厚卫衣"]),
    "中层薄":     (2.0, ["薄卫衣", "薄毛衣"]),
    "中层厚":     (3.0, ["厚毛衣", "抓绒卫衣"]),
    "外套薄":     (2.5, ["风衣", "牛仔夹克"]),
    "外套厚":     (4.0, ["棉服", "呢大衣"]),
    "羽绒服":     (5.0, ["中长羽绒服"]),
    "额外保暖层": (2.5, ["羽绒背心", "加绒背心"]),
}
BOTTOM_POOL_M = {
    "薄短": (1.0, ["休闲短裤", "运动短裤"]),
    "薄长": (1.5, ["轻薄牛仔裤", "休闲长裤"]),
    "厚长": (2.5, ["加绒牛仔裤", "加绒休闲裤"]),
    "加层": (1.5, ["秋裤"]),
}
BOTTOM_POOL_F = {
    "薄短": (1.0, ["休闲短裤", "短裙"]),
    "薄长": (1.5, ["轻薄牛仔裤", "阔腿裤"]),
    "厚长": (2.5, ["加绒牛仔裤", "冬季长裙"]),
    "加层": (1.5, ["保暖腿袜"]),
}

# ───────────── 温度 ➜ 目标权重 ─────────────
TEMP_TABLE = [
    (28, float("inf"), 1.0, 1.0),
    (24, 28, 2.0, 1.0),
    (20, 24, 3.0, 1.5),
    (16, 20, 4.0, 1.5),
    (12, 16, 5.0, 2.0),
    (9,  12, 6.0, 2.5),
    (6,  9,  7.0, 3.0),
    (3,  6,  8.0, 3.5),
    (-273, 3, 9.0, 4.0),
]
BIAS = {"正常": (0.0, 0.0), "怕冷": (1.0, 0.5), "怕热": (-1.0, -0.5)}

BASE_CATS   = {"打底短袖", "打底长袖薄", "打底长袖厚"}
JACKET_CATS = {"外套薄", "外套厚", "羽绒服"}
MID_CATS    = {"中层薄", "中层厚", "额外保暖层"}

# ───────────── 工具函数 ─────────────
def clamp(v, m=1.0): return max(m, v)

def choose_upper(pool, target, tol=0.5, max_items=5):
    """
    规则：
    • 必须 ≥1 打底
    • 外套、中层可选
    • 若出现第 2 件外套或中层 → 三层必须全
    • 组合内类别不可重复
    """
    items = [(c, n, w) for c, (w, ns) in pool.items() for n in ns]
    best, best_diff = [], float("inf")

    for r in range(1, max_items + 1):
        for combo in itertools.combinations(items, r):
            cats = [c for c, _, _ in combo]

            # ≥1 打底
            if not (set(cats) & BASE_CATS):
                continue
            # 不重复类别
            if len(cats) != len(set(cats)):
                continue

            n_outer = len([c for c in cats if c in JACKET_CATS])
            n_mid   = len([c for c in cats if c in MID_CATS])

            if (n_outer > 1 or n_mid > 1) and not (n_outer >= 1 and n_mid >= 1):
                continue  # 层叠前需三层齐

            tot  = sum(w for _, _, w in combo)
            diff = abs(tot - target)
            if diff <= tol:
                if diff < best_diff:
                    best, best_diff = [combo], diff
                elif diff == best_diff:
                    best.append(combo)
    return best

def choose_bottom(pool, target, tol=0.5):
    """主裤 1 件；加层 ≤1"""
    mains = [(c, n, pool[c][0]) for c in pool if c != "加层" for n in pool[c][1]]
    adds  = [("加层", n, pool["加层"][0]) for n in pool["加层"][1]]

    best, best_diff = [], float("inf")
    for m in mains:
        for add in [None] + adds:
            combo = (m,) + ((add,) if add else ())
            tot   = m[2] + (add[2] if add else 0)
            diff  = abs(tot - target)
            if diff <= tol:
                if diff < best_diff:
                    best, best_diff = [combo], diff
                elif diff == best_diff:
                    best.append(combo)
    return best

# ───────────── Streamlit UI ─────────────
st.title("👕 今天穿什么呢 · 权重版")
with st.form("input"):
    col1, col2 = st.columns(2)
    gender = col1.radio("性别", ["女性", "男性"], horizontal=True)
    prefer = col2.radio("体感偏好", ["正常", "怕冷", "怕热"], horizontal=True)
    feel   = st.number_input("体感温度 ℃", value=15.0, format="%.1f")
    go     = st.form_submit_button("生成穿搭")

if go:
    # 1. 目标
    for lo, hi, u_t, d_t in TEMP_TABLE:
        if lo <= feel < hi:
            break
    u_t += BIAS[prefer][0]; d_t += BIAS[prefer][1]

    # 2. 动态上身池
    TOP_POOL = TOP_POOL_BASE.copy()
    if feel >= 9:
        TOP_POOL.pop("额外保暖层", None)

    def mk(u, d, tag):
        tops = choose_upper(TOP_POOL, u)
        bots = choose_bottom(BOTTOM_POOL_F if gender == "女性" else BOTTOM_POOL_M, d)
        return (tag, random.choice(tops), random.choice(bots)) if tops and bots else None

    # 精准 + 微调 / 加衣 / 减衣
    plans = [mk(u_t, d_t, "精准匹配")]

    shift = random.choice((0.5, -0.5))
    plans.append(mk(clamp(u_t + shift), clamp(d_t + shift), f"微调 {shift:+.1f}"))
    if prefer == "怕冷":
        plans[-1] = mk(u_t + 1.0, d_t + 0.5, "加衣版")
    elif prefer == "怕热":
        plans[-1] = mk(clamp(u_t - 1.0), clamp(d_t - 0.5), "减衣版")

    plans = [p for p in plans if p]
    if not plans:
        st.warning("未找到合适的组合，请调整输入再试～")
    else:
        st.header("推荐穿搭方案")
        for tag, top, bot in plans:
            st.subheader(tag)
            st.markdown("**上身：**")
            for c, n, w in top:
                st.markdown(f"- {n}（{c}·{w}）")
            st.markdown("**下身：**")
            for c, n, w in bot:
                st.markdown(f"- {n}（{c}·{w}）")
