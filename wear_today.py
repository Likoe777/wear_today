import streamlit as st
import random
import itertools

# ────────────────── Streamlit 必须先配置 ──────────────────
st.set_page_config(page_title="今天穿什么呢 · 权重版", layout="centered")

# ───────────────────── 数据字典 ──────────────────────
# 上身单品：键 = 类别，值 = (权重, [示例名称 …])
TOP_POOL_BASE = {
    "打底短袖":   (1.0, ["基础短袖T", "运动速干T", "Polo"]),
    "打底长袖薄": (1.5, ["薄长袖T", "衬衫"]),
    "打底长袖厚": (2.5, ["加绒长袖T", "厚卫衣"]),
    "中层薄":     (2.0, ["薄卫衣", "薄毛衣"]),
    "中层厚":     (3.0, ["厚毛衣", "抓绒卫衣"]),
    "外套薄":     (2.5, ["风衣", "牛仔夹克"]),
    "外套厚":     (4.0, ["棉服", "呢大衣"]),
    "羽绒服":     (5.0, ["中长羽绒服"]),           # 单独键，允许叠穿
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

# 温度 ➜ 目标权重表（上身 / 下身）
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

# ──────────────────── 工具函数 ───────────────────────
BASE_CATS   = {"打底短袖", "打底长袖薄", "打底长袖厚"}
JACKET_CATS = {"外套薄", "外套厚", "羽绒服"}
MID_CATS    = {"中层薄", "中层厚", "额外保暖层"}

def clamp(v: float, minimum: float = 1.0) -> float:
    """权重下限（单品最薄 = 1.0）"""
    return max(minimum, v)

def choose_upper(pool: dict, target: float, tol: float = 0.5):
    """
    三段式：1 打底 + ≥1 外套 + ≥1 中层（可再叠 1 件外套）
    返回贴近目标的组合列表
    """
    bases   = [(c, n, w) for c, (w, ns) in pool.items() if c in BASE_CATS   for n in ns]
    jackets = [(c, n, w) for c, (w, ns) in pool.items() if c in JACKET_CATS for n in ns]
    mids    = [(c, n, w) for c, (w, ns) in pool.items() if c in MID_CATS    for n in ns]

    best, best_diff = [], float("inf")
    for b in bases:
        for j in jackets:
            for m in mids:
                core = (b, j, m)  # 三层已满足
                core_tot = b[2] + j[2] + m[2]
                # 允许再加 0-1 件不同类别外套
                extra_opts = [None] + [x for x in jackets if x != j]
                for extra in extra_opts:
                    combo = core + ((extra,) if extra else ())
                    total = core_tot + (extra[2] if extra else 0)
                    diff  = abs(total - target)
                    if diff <= tol:
                        if diff < best_diff:
                            best, best_diff = [combo], diff
                        elif diff == best_diff:
                            best.append(combo)
    return best

def choose_bottom(pool: dict, target: float, tol: float = 0.5):
    """
    下身：主裤（薄短/薄长/厚长）只能 1 件，加层最多 1 件
    """
    mains = [k for k in pool if k != "加层"]
    mains_items = [(c, n, pool[c][0]) for c in mains for n in pool[c][1]]
    adds = [(c, n, pool["加层"][0]) for n in pool["加层"][1]]

    best, best_diff = [], float("inf")
    for m in mains_items:
        for add in [None] + adds:
            combo = (m,) + ((add,) if add else ())
            total = m[2] + (add[2] if add else 0)
            diff  = abs(total - target)
            if diff <= tol:
                if diff < best_diff:
                    best, best_diff = [combo], diff
                elif diff == best_diff:
                    best.append(combo)
    return best

# ───────────────────── UI ────────────────────────
st.title("👕 今天穿什么呢 · 权重版")

with st.form("input"):
    col1, col2 = st.columns(2)
    gender = col1.radio("性别", ["女性", "男性"], horizontal=True)
    prefer = col2.radio("体感偏好", ["正常", "怕冷", "怕热"], horizontal=True)
    feel   = st.number_input("体感温度 ℃", value=15.0, format="%.1f")
    go     = st.form_submit_button("生成穿搭")

if go:
    # 1. 目标权重
    for lo, hi, up_base, dn_base in TEMP_TABLE:
        if lo <= feel < hi:
            break
    up_base += BIAS[prefer][0]
    dn_base += BIAS[prefer][1]

    # 2. 动态上身池（≥9 ℃ 去掉额外保暖层）
    TOP_POOL = TOP_POOL_BASE.copy()
    if feel >= 9:
        TOP_POOL.pop("额外保暖层")

    # 3. 生成两套方案：精准 + 随机微调
    plans = []

    def mk_plan(u_t, d_t, tag):
        tops = choose_upper(TOP_POOL, u_t)
        bottoms = choose_bottom(
            BOTTOM_POOL_F if gender == "女性" else BOTTOM_POOL_M,
            d_t)
        if tops and bottoms:
            return tag, random.choice(tops), random.choice(bottoms)
        return None

    # 精准
    plans.append(mk_plan(up_base, dn_base, "精准匹配"))

    # 随机微调 ±0.5
    shift = random.choice((0.5, -0.5))
    plans.append(mk_plan(clamp(up_base + shift), clamp(dn_base + shift),
                         f"微调 {shift:+.1f}"))

    # 用偏好替换第二套
    if prefer == "怕冷":
        plans[-1] = mk_plan(up_base + 1.0, dn_base + 0.5, "加衣版")
    elif prefer == "怕热":
        plans[-1] = mk_plan(clamp(up_base - 1.0), clamp(dn_base - 0.5), "减衣版")

    # 4. 展示
    valid = list(filter(None, plans))
    if not valid:
        st.warning("未找到合适的搭配，请调整输入试试～")
    else:
        st.header("推荐穿搭方案")
        for tag, top, bot in valid:
            st.subheader(tag)
            st.markdown("**上身：**")
            for c, n, w in top:
                st.markdown(f"- {n}（{c} · {w}）")
            st.markdown("**下身：**")
            for c, n, w in bot:
                st.markdown(f"- {n}（{c} · {w}）")
