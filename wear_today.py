import streamlit as st
import random
import itertools

# ────────────────── Streamlit 必须先配置 ──────────────────
st.set_page_config(page_title="今天穿什么呢 · 权重版", layout="centered")

# ───────────────────── 数据字典 ──────────────────────
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

# ──────────────────── 工具函数 ───────────────────────
def clamp(v: float, minimum: float = 1.0) -> float:
    return max(minimum, v)

def choose_upper(pool: dict, target: float, tol: float = 0.5):
    """打底×1 + 外套≥1 + 中层≥1，再可加 1 件外套"""
    bases   = [(c, n, w) for c,(w,ns) in pool.items() if c in BASE_CATS   for n in ns]
    jackets = [(c, n, w) for c,(w,ns) in pool.items() if c in JACKET_CATS for n in ns]
    mids    = [(c, n, w) for c,(w,ns) in pool.items() if c in MID_CATS    for n in ns]

    best, best_diff = [], float("inf")
    for b in bases:
        for j in jackets:
            for m in mids:
                core = (b, j, m)
                core_tot = b[2]+j[2]+m[2]
                for extra in [None]+[x for x in jackets if x != j]:
                    combo = core + ((extra,) if extra else ())
                    total = core_tot + (extra[2] if extra else 0)
                    diff  = abs(total-target)
                    if diff<=tol:
                        if diff<best_diff: best,best_diff=[combo],diff
                        elif diff==best_diff: best.append(combo)
    return best

def choose_bottom(pool: dict, target: float, tol: float = 0.5):
    """主裤 1 件 + 加层 ≤1"""
    mains_items = [(c, n, pool[c][0]) for c in pool if c!="加层" for n in pool[c][1]]
    adds = [("加层", n, pool["加层"][0]) for n in pool["加层"][1]]   # ← fixed

    best,best_diff=[],float("inf")
    for m in mains_items:
        for add in [None]+adds:
            combo = (m,) + ((add,) if add else ())
            total = m[2] + (add[2] if add else 0)
            diff  = abs(total-target)
            if diff<=tol:
                if diff<best_diff: best,best_diff=[combo],diff
                elif diff==best_diff: best.append(combo)
    return best

# ───────────────────── UI ────────────────────────
st.title("👕 今天穿什么呢 · 权重版")
with st.form("input"):
    col1,col2 = st.columns(2)
    gender = col1.radio("性别",["女性","男性"],horizontal=True)
    prefer = col2.radio("体感偏好",["正常","怕冷","怕热"],horizontal=True)
    feel   = st.number_input("体感温度 ℃",15.0,format="%.1f")
    go     = st.form_submit_button("生成穿搭")

if go:
    for lo,hi,u_t,d_t in TEMP_TABLE:
        if lo<=feel<hi: break
    u_t += BIAS[prefer][0]; d_t += BIAS[prefer][1]

    TOP_POOL = TOP_POOL_BASE.copy()
    if feel>=9: TOP_POOL.pop("额外保暖层",None)

    def mk(u,d,tag):
        tops=choose_upper(TOP_POOL,u)
        bottoms=choose_bottom(BOTTOM_POOL_F if gender=="女性" else BOTTOM_POOL_M,d)
        return (tag,random.choice(tops),random.choice(bottoms)) if tops and bottoms else None

    plans=[mk(u_t,d_t,"精准匹配")]
    shift=random.choice((0.5,-0.5))
    plans.append(mk(clamp(u_t+shift),clamp(d_t+shift),f"微调 {shift:+.1f}"))
    if prefer=="怕冷": plans[-1]=mk(u_t+1,d_t+0.5,"加衣版")
    if prefer=="怕热": plans[-1]=mk(clamp(u_t-1),clamp(d_t-0.5),"减衣版")

    valid=list(filter(None,plans))
    if not valid:
        st.warning("未找到合适的组合，请调整输入再试～")
    else:
        st.header("推荐穿搭方案")
        for tag,top,bot in valid:
            st.subheader(tag)
            st.markdown("**上身：**")
            for c,n,w in top: st.markdown(f"- {n}（{c}·{w}）")
            st.markdown("**下身：**")
            for c,n,w in bot: st.markdown(f"- {n}（{c}·{w}）")
