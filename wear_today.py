import streamlit as st
import random

# 定义选项
STYLE_OPTIONS = {
    "通勤": "通勤",
    "休闲": "休闲",
    "运动": "运动",
    "学院": "学院",
    "中性基础": "中性基础"
}

WEATHER_OPTIONS = {
    "晴天": "晴天",
    "多云": "多云",
    "阴天": "阴天",
    "下雨": "下雨",
    "下雪": "下雪",
    "雾": "雾",
    "大风": "大风"
}

TOP_POOLS = {
    "打底短袖": ["基础短袖T恤", "运动速干短袖", "Polo短袖"],
    "打底长袖薄": ["基础长袖T恤", "运动速干长袖", "薄款长袖衬衫"],
    "打底长袖厚": ["加绒长袖T恤", "厚卫衣", "羊毛打底衫"],
    "中层薄": ["薄卫衣", "针织开衫", "薄毛衣"],
    "中层厚": ["抓绒卫衣", "厚毛衣", "加绒衬衫"],
    "外套薄": ["轻便风衣", "牛仔夹克", "西装外套（薄）", "防风夹克"],
    "外套厚": ["羽绒服", "棉服", "羊羔毛夹克", "大衣"],
    "额外保暖层": ["羽绒背心", "加绒背心", "厚毛衣马甲"]
}

BOTTOM_POOLS_M = {
    "薄短": ["休闲短裤", "运动短裤"],
    "薄长": ["轻薄牛仔裤", "休闲长裤", "西裤"],
    "厚长": ["加绒牛仔裤", "加绒休闲裤", "加绒运动裤", "西裤（加绒）"],
    "加层": ["秋裤", "加绒打底裤"]
}

BOTTOM_POOLS_F = {
    "薄短": ["休闲短裤", "运动短裤", "短裙"],
    "薄长": ["轻薄牛仔裤", "阔腿裤", "西裤", "长裙"],
    "厚长": ["加绒牛仔裤", "加绒休闲裤", "加绒运动裤", "西裤（加绒）"],
    "加层": ["秋裤", "加绒打底裤", "保暖腿袜"]
}

SHOES_POOLS = {
    "日常": ["运动鞋", "帆布鞋"],
    "雨雪": ["防水运动鞋", "防水短靴", "雨靴"],
    "保暖": ["加绒短靴", "雪地靴", "加绒运动鞋"],
}

# 随机选取
def rand_choices(pool, count=2):
    return random.sample(pool, min(count, len(pool)))

def decide_layers(feel_temp):
    if feel_temp >= 27:
        return ["打底短袖"], "薄短"
    elif 23 <= feel_temp < 27:
        return ["打底短袖或打底长袖薄"], "薄长"
    elif 19 <= feel_temp < 23:
        return ["打底长袖薄", "外套薄"], "薄长"
    elif 15 <= feel_temp < 19:
        return ["打底长袖薄", "外套薄"], "薄长"
    elif 10 <= feel_temp < 15:
        return ["打底长袖厚", "外套薄"], "厚长"
    elif 6 <= feel_temp < 10:
        return ["打底长袖厚", "中层厚", "外套厚"], "厚长+加层"
    else:
        return ["打底长袖厚", "中层厚", "外套厚", "额外保暖层"], "厚长+加层"

def select_main_backup(pool):
    main = random.choice(pool)
    backups = rand_choices([item for item in pool if item != main])
    return main, backups

# ----------------- Streamlit 页面 -----------------

st.set_page_config(page_title="今天穿什么呢", layout="centered")

st.title("👕 今天穿什么呢")

with st.form("input_form"):
    st.subheader("基本信息")
    gender = st.radio("请选择性别", ["女性", "男性"])
    high_temp = st.number_input("请输入最高温度（℃）", format="%.1f")
    low_temp = st.number_input("请输入最低温度（℃）", format="%.1f")
    feels_like = st.number_input("如果知道体感温度可以填（可留空）", format="%.1f")
    weather = st.selectbox("请选择天气情况", list(WEATHER_OPTIONS.keys()))
    precip = st.number_input("24小时预计降水量（mm，可空）", format="%.1f")
    wind = st.number_input("平均风速（m/s，可空）", format="%.1f")
    hum = st.number_input("湿度%（可空）", format="%.1f")
    uv = st.number_input("紫外线指数（可空）", format="%.1f")

    st.subheader("体感偏好")
    bias_choice = st.radio("请选择体感偏好", ["正常", "怕冷（体感-1℃）", "怕热（体感+1℃）"])

    st.subheader("穿搭风格")
    styles = st.multiselect("选择你的风格（最多选3个）", list(STYLE_OPTIONS.keys()), default=["通勤", "休闲"])

    submitted = st.form_submit_button("🚀 生成穿搭建议")

if submitted:
    bias_map = {"正常": 0, "怕冷（体感-1℃）": -1, "怕热（体感+1℃）": 1}
    bias = bias_map.get(bias_choice, 0)

    # ✨新增异常检测✨
    error_messages = []
    if high_temp > 60:
        error_messages.append("暂不支持为炼丹炉内的居民搭配穿搭。🔥")
    if low_temp < -50:
        error_messages.append("暂不支持为南极帝企鹅量身定制穿搭。🐧")
    if precip > 500:
        error_messages.append("暂不支持为海洋生物量身定制穿搭。🐋")
    if wind > 50:
        error_messages.append("暂不支持为龙卷风猎人配备战斗服。🌪️")
    if high_temp < low_temp:
        error_messages.append("你最高温度比最低温度还低？地球的物理法则哭了！🌏")

    if error_messages:
        for msg in error_messages:
            st.error(msg)
        st.stop()

    # --- 你的原推算体感部分继续 ---
    if feels_like == 0.0:
        feels_like_real = (high_temp + low_temp) / 2
        if weather in ("下雨", "下雪"):
            feels_like_real -= (2 if precip >= 20 else 1)
        if wind >= 8:
            feels_like_real -= 1
    else:
        feels_like_real = feels_like

    feels_like_real += bias

    st.divider()
    st.subheader("🎯 穿搭推荐结果")

    st.markdown(f"推算体感温度为：**{feels_like_real:.1f}℃**")

    up_layers, down_desc = decide_layers(feels_like_real)

    # 上身推荐
    st.markdown("#### 【上身搭配】")
    for layer in up_layers:
        if layer == "打底短袖":
            pool = TOP_POOLS.get("打底短袖", [])
            label = "打底"
        elif layer == "打底长袖薄":
            pool = TOP_POOLS.get("打底长袖薄", [])
            label = "打底"
        elif layer == "打底长袖厚":
            pool = TOP_POOLS.get("打底长袖厚", [])
            label = "打底"
        elif layer == "中层薄":
            pool = TOP_POOLS.get("中层薄", [])
            label = "中层"
        elif layer == "中层厚":
            pool = TOP_POOLS.get("中层厚", [])
            label = "中层"
        elif layer == "外套薄":
            pool = TOP_POOLS.get("外套薄", [])
            label = "外套"
        elif layer == "外套厚":
            pool = TOP_POOLS.get("外套厚", [])
            label = "外套"
        elif layer == "额外保暖层":
            pool = TOP_POOLS.get("额外保暖层", [])
            label = "额外保暖层"
        else:
            continue

        if pool:
            main, backups = select_main_backup(pool)
            st.markdown(f"- **{label}**：{main} （可替代：{', '.join(backups)})")

    # 下身推荐
    st.markdown("#### 【下身搭配】")
    bottoms = BOTTOM_POOLS_F if gender == "女性" else BOTTOM_POOLS_M
    if "短" in down_desc and "薄短" in bottoms:
        main, backups = select_main_backup(bottoms["薄短"])
        st.markdown(f"- 下装：{main} （可替代：{', '.join(backups)})")
    if "薄长" in down_desc and "薄长" in bottoms:
        main, backups = select_main_backup(bottoms["薄长"])
        st.markdown(f"- 下装：{main} （可替代：{', '.join(backups)})")
    if "厚长" in down_desc and "厚长" in bottoms:
        main, backups = select_main_backup(bottoms["厚长"])
        st.markdown(f"- 下装：{main} （可替代：{', '.join(backups)})")
    if "加层" in down_desc and "加层" in bottoms:
        main, backups = select_main_backup(bottoms["加层"])
        st.markdown(f"- 加层：{main} （可替代：{', '.join(backups)})")

    # 鞋子推荐
    st.markdown("#### 【鞋子推荐】")
    if weather in ("下雨", "下雪"):
        main, backups = select_main_backup(SHOES_POOLS["雨雪"])
    elif feels_like_real <= 5:
        main, backups = select_main_backup(SHOES_POOLS["保暖"])
    else:
        main, backups = select_main_backup(SHOES_POOLS["日常"])
    st.markdown(f"- 鞋子：{main} （可替代：{', '.join(backups)})")

    # 小提醒
    st.markdown("#### 【附加提醒】")
    if weather in ("下雨", "下雪"):
        st.markdown("- 有降水，记得带伞并穿防水鞋。")
    if feels_like_real <= 8:
        st.markdown("- 气温较低，建议增加围巾、帽子、手套等装备。")
    if wind >= 8:
        st.markdown("- 风较大，可选择防风外套。")
