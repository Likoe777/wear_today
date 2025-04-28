import streamlit as st
import random
import itertools

# --- 页面配置 ---
st.set_page_config(page_title="今天穿什么呢 · 权重版", layout="centered")

# --- 数据 ---
TOP_POOL_BASE = {
    "打底短袖": (1.0, ["基础短袖T", "运动速干T", "Polo"]),
    "打底长袖薄": (1.5, ["薄长袖T", "衬衫"]),
    "打底长袖厚": (2.5, ["加绒长袖T", "厚卫衣"]),
    "中层薄": (2.0, ["薄卫衣", "薄毛衣"]),
    "中层厚": (3.0, ["厚毛衣", "抓绒卫衣"]),
    "外套薄": (2.5, ["风衣", "牛仔夹克"]),
    "外套厚": (4.0, ["棉服", "呢大衣"]),
    "羽绒服": (5.0, ["中长羽绒服"]),
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

TEMP_TABLE = [
    (28, float("inf"), 1.0, 1.0),
    (24, 28, 2.0, 1.0),
    (20, 24, 3.0, 1.5),
    (16, 20, 4.0, 1.5),
    (12, 16, 5.0, 2.0),
    (9, 12, 6.0, 2.5),
    (6, 9, 7.0, 3.0),
    (3, 6, 8.0, 3.5),
    (-273, 3, 9.0, 4.0),
]

BIAS = {"正常": (0.0, 0.0), "怕冷": (1.0, 0.5), "怕热": (-1.0, -0.5)}

BASE_CATS = {"打底短袖", "打底长袖薄", "打底长袖厚"}
JACKET_CATS = {"外套薄", "外套厚", "羽绒服"}
MID_CATS = {"中层薄", "中层厚", "额外保暖层"}

# --- 工具函数 ---
def clamp(v, minimum=1.0):
    return max(v, minimum)

def choose_upper(pool, target, tol=0.5, max_try=30):
    items_by_cat = {cat: [(cat, name, weight)] for cat, (weight, names) in pool.items() for name in names}
    candidates = [(cat, name, pool[cat][0]) for cat in pool for name in pool[cat][1]]

    for _ in range(max_try):
        for r in range(1, 6):
            for combo in itertools.combinations(candidates, r):
                cats = [c for c, _, _ in combo]
                if cats.count(cats[0]) > 1:
                    continue
                total = sum(w for _, _, w in combo)
                diff = abs(total - target)
                has_base = any(c in BASE_CATS for c, _, _ in combo)
                bases = [c for c, _, _ in combo if c in BASE_CATS]
                jackets = [c for c, _, _ in combo if c in JACKET_CATS]
                mids = [c for c, _, _ in combo if c in MID_CATS]
                if not has_base or len(bases) != 1:
                    continue
                if any(cats.count(c) > 1 for c in cats):
                    continue
                if len(jackets) + len(mids) >= 2 and (not jackets or not mids):
                    continue
                if "打底短袖" in bases and any(j not in {"外套薄"} for j in jackets+mids):
                    continue
                if "中层薄" in mids and not jackets:
                    continue
                if diff <= tol:
                    return [combo]
    return []

def choose_bottom(pool, target, tol=0.5, feel=15.0, max_try=30):
    pool = pool.copy()
    if feel < 15:
        pool.pop("薄短", None)
    mains = [k for k in pool if k != "加层"]
    mains_items = [(c, n, pool[c][0]) for c in mains for n in pool[c][1]]
    adds = [("加层", n, pool["加层"][0]) for n in pool.get("加层", [])[1]]

    for _ in range(max_try):
        for m in mains_items:
            for add in [None] + adds:
                if add and m[0] != "厚长":
                    continue
                combo = (m,) + ((add,) if add else ())
                total = sum(w for _, _, w in combo)
                diff = abs(total - target)
                if diff <= tol:
                    return [combo]
    return []

# --- UI ---
st.title("👕 今天穿什么呢 · 权重版")

with st.form("input"):
    col1, col2 = st.columns(2)
    gender = col1.radio("性别", ["女性", "男性"], horizontal=True)
    prefer = col2.radio("体感偏好", ["正常", "怕冷", "怕热"], horizontal=True)
    feel = st.number_input("体感温度 ℃", value=15.0, format="%.1f")
    go = st.form_submit_button("生成穿搭")

if go:
    for lo, hi, up_base, dn_base in TEMP_TABLE:
        if lo <= feel < hi:
            break
    up_base += BIAS[prefer][0]
    dn_base += BIAS[prefer][1]

    top_pool = TOP_POOL_BASE.copy()
    if feel < 15:
        top_pool.pop("打底短袖", None)

    plans = []

    def mk_plan(u_t, d_t, tag):
        tops = choose_upper(top_pool, u_t, feel=feel)
        bots = choose_bottom(BOTTOM_POOL_F if gender == "女性" else BOTTOM_POOL_M, d_t, feel)
        if tops and bots:
            return tag, random.choice(tops), random.choice(bots)
        return None

    plans.append(mk_plan(up_base, dn_base, "精准匹配"))
    shift = random.choice((0.5, -0.5))
    plans.append(mk_plan(clamp(up_base + shift), clamp(dn_base + shift), f"微调 {shift:+.1f}"))

    if prefer == "怕冷":
        plans[-1] = mk_plan(up_base + 1.0, dn_base + 0.5, "加衣版")
    elif prefer == "怕热":
        plans[-1] = mk_plan(clamp(up_base - 1.0), clamp(dn_base - 0.5), "减衣版")

    valid = list(filter(None, plans))
    if not valid:
        st.warning("未找到合适搭配，请调整体感温度或偏好设置～")
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
