# -*- coding: utf-8 -*-

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path


# =====================================================
# 1. 页面设置
# =====================================================

st.set_page_config(
    page_title="Olist 电商订单管理系统",
    page_icon="📦",
    layout="wide"
)

st.title("📦 Olist 电商订单管理与物流监控系统")
st.caption("E-commerce Order Management Dashboard")

st.markdown("---")


# =====================================================
# 2. 数据文件路径
# 当前程序和 CSV 文件都在 .venv 文件夹中
# =====================================================

BASE_DIR = Path(r"C:\Users\zengy\ml4biz\.venv")
DATA_PATH = BASE_DIR / "olist_orders_dataset.csv"


# =====================================================
# 3. 读取数据
# =====================================================

@st.cache_data
def load_data(file_path):
    data = pd.read_csv(file_path)

    date_columns = [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date"
    ]

    for col in date_columns:
        if col in data.columns:
            data[col] = pd.to_datetime(
                data[col],
                errors="coerce"
            )

    return data


if not DATA_PATH.exists():
    st.error("没有找到订单数据文件！")

    st.write("程序正在寻找：")
    st.code(str(DATA_PATH))

    st.info(
        "请确认 olist_orders_dataset.csv "
        "确实放在 C:\\Users\\zengy\\ml4biz\\.venv 文件夹中。"
    )

    st.stop()


try:
    df = load_data(str(DATA_PATH))

except Exception as e:
    st.error("读取 CSV 文件失败。")
    st.exception(e)
    st.stop()


# =====================================================
# 4. 检查必要字段
# =====================================================

required_columns = [
    "order_id",
    "order_status",
    "order_purchase_timestamp"
]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:
    st.error("数据集缺少必要字段：" + ", ".join(missing_columns))
    st.stop()


# =====================================================
# 5. 订单状态分类
# =====================================================

def classify_order(row):
    status = str(row["order_status"]).strip().lower()

    carrier_date = row.get(
        "order_delivered_carrier_date",
        pd.NaT
    )

    customer_date = row.get(
        "order_delivered_customer_date",
        pd.NaT
    )

    # 已送达
    if status == "delivered":
        return "已送达"

    # 已取消
    if status == "canceled":
        return "已取消"

    # 商品不可用
    if status == "unavailable":
        return "商品不可用"

    # 已发货，尚未送达
    if pd.notna(carrier_date) and pd.isna(customer_date):
        return "已发货"

    # 已送至客户的日期存在，也视为已送达
    if pd.notna(customer_date):
        return "已送达"

    # 尚未完成发货的订单
    if status in [
        "created",
        "approved",
        "processing",
        "invoiced"
    ]:
        return "待发货"

    # 其他状态
    return "其他状态"


df["物流分类"] = df.apply(classify_order, axis=1)


# =====================================================
# 6. 超时订单判断
# =====================================================

purchase_col = "order_purchase_timestamp"
estimated_col = "order_estimated_delivery_date"
delivered_col = "order_delivered_customer_date"

if estimated_col in df.columns:
    df["是否超时"] = (
        df[estimated_col].notna()
        & df[delivered_col].isna()
        & (df[estimated_col] < pd.Timestamp.now())
        & (~df["物流分类"].isin(["已取消", "商品不可用"]))
    )
else:
    df["是否超时"] = False


# =====================================================
# 7. 侧边栏筛选
# =====================================================

st.sidebar.header("🔎 订单筛选")

status_options = [
    "全部",
    "待发货",
    "已发货",
    "已送达",
    "已取消",
    "商品不可用",
    "其他状态"
]

selected_status = st.sidebar.selectbox(
    "选择物流状态",
    status_options
)


# 日期筛选
valid_dates = df[purchase_col].dropna()

if not valid_dates.empty:
    min_date = valid_dates.min().date()
    max_date = valid_dates.max().date()

    date_range = st.sidebar.date_input(
        "下单日期范围",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
else:
    date_range = None


# 超时筛选
overdue_only = st.sidebar.checkbox(
    "只看超时订单",
    value=False
)


# 订单编号搜索
order_keyword = st.sidebar.text_input(
    "搜索订单编号",
    placeholder="输入完整或部分订单编号"
)


# =====================================================
# 8. 应用筛选条件
# =====================================================

filtered_df = df.copy()

if selected_status != "全部":
    filtered_df = filtered_df[
        filtered_df["物流分类"] == selected_status
    ]


if date_range and len(date_range) == 2:
    start_date, end_date = date_range

    filtered_df = filtered_df[
        filtered_df[purchase_col].dt.date.between(
            start_date,
            end_date
        )
    ]


if overdue_only:
    filtered_df = filtered_df[
        filtered_df["是否超时"]
    ]


if order_keyword:
    filtered_df = filtered_df[
        filtered_df["order_id"]
        .astype(str)
        .str.contains(order_keyword, case=False, na=False)
    ]


# =====================================================
# 9. 关键指标
# =====================================================

st.subheader("📊 订单运营概览")

total_orders = len(df)

pending_orders = (df["物流分类"] == "待发货").sum()
shipped_orders = (df["物流分类"] == "已发货").sum()
delivered_orders = (df["物流分类"] == "已送达").sum()
canceled_orders = (df["物流分类"] == "已取消").sum()
overdue_orders = df["是否超时"].sum()

col1, col2, col3 = st.columns(3)

col1.metric("📦 订单总量", f"{total_orders:,}")
col2.metric("🕒 待发货", f"{pending_orders:,}")
col3.metric("🚚 已发货", f"{shipped_orders:,}")

col4, col5, col6 = st.columns(3)

col4.metric("✅ 已送达", f"{delivered_orders:,}")
col5.metric("❌ 已取消", f"{canceled_orders:,}")
col6.metric("⚠️ 超时订单", f"{overdue_orders:,}")

st.markdown("---")


# =====================================================
# 10. 订单状态分布图
# =====================================================

st.subheader("📈 订单状态分析")

chart_col1, chart_col2 = st.columns(2)

status_counts = (
    df["物流分类"]
    .value_counts()
    .rename_axis("物流状态")
    .reset_index(name="订单数量")
)

with chart_col1:
    fig_pie = px.pie(
        status_counts,
        names="物流状态",
        values="订单数量",
        title="订单物流状态占比",
        hole=0.4
    )

    st.plotly_chart(
        fig_pie,
        use_container_width=True
    )


with chart_col2:
    fig_bar = px.bar(
        status_counts,
        x="物流状态",
        y="订单数量",
        title="各状态订单数量",
        text="订单数量"
    )

    fig_bar.update_traces(
        textposition="outside"
    )

    st.plotly_chart(
        fig_bar,
        use_container_width=True
    )


# =====================================================
# 11. 每月订单趋势
# =====================================================

st.subheader("📅 每月订单趋势")

monthly_df = df.dropna(
    subset=[purchase_col]
).copy()

monthly_df["下单月份"] = (
    monthly_df[purchase_col]
    .dt.to_period("M")
    .astype(str)
)

monthly_counts = (
    monthly_df.groupby("下单月份")
    .size()
    .reset_index(name="订单数量")
    .sort_values("下单月份")
)

if not monthly_counts.empty:
    fig_monthly = px.line(
        monthly_counts,
        x="下单月份",
        y="订单数量",
        markers=True,
        title="每月下单量变化"
    )

    st.plotly_chart(
        fig_monthly,
        use_container_width=True
    )
else:
    st.info("没有可用于生成月度趋势图的日期数据。")


st.markdown("---")


# =====================================================
# 12. 订单明细表
# =====================================================

st.subheader("📋 订单明细")

st.write(
    f"当前筛选条件下共有 **{len(filtered_df):,}** 条订单。"
)

display_columns = [
    "order_id",
    "物流分类",
    "order_status",
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
    "是否超时"
]

display_columns = [
    col for col in display_columns
    if col in filtered_df.columns
]

display_df = filtered_df[display_columns].copy()

rename_columns = {
    "order_id": "订单编号",
    "物流分类": "物流分类",
    "order_status": "原始订单状态",
    "order_purchase_timestamp": "下单时间",
    "order_approved_at": "订单批准时间",
    "order_delivered_carrier_date": "交给物流时间",
    "order_delivered_customer_date": "客户签收时间",
    "order_estimated_delivery_date": "预计送达时间",
    "是否超时": "是否超时"
}

display_df = display_df.rename(
    columns=rename_columns
)

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True
)


# =====================================================
# 13. 下载筛选后的订单
# =====================================================

st.subheader("📥 导出订单数据")

csv_data = display_df.to_csv(
    index=False,
    encoding="utf-8-sig"
)

st.download_button(
    label="下载当前筛选结果 CSV",
    data=csv_data,
    file_name="olist_filtered_orders.csv",
    mime="text/csv"
)


# =====================================================
# 14. 说明
# =====================================================

st.markdown("---")

st.subheader("📌 指标说明")

st.markdown(
    """
    - **待发货：** 尚未记录交给物流的订单，且订单状态属于创建、
      批准、处理中或已开票等状态。
    - **已发货：** 已记录交给物流的时间，但尚未记录客户签收时间。
    - **已送达：** 原始订单状态为 delivered，或已记录客户签收时间。
    - **已取消：** 原始订单状态为 canceled。
    - **超时订单：** 已超过预计送达日期，但尚未记录客户签收时间的订单。
    - **注意：** 本数据集是历史订单数据，超时判断基于当前电脑日期，
      不能代表实时物流状态。
    """
)

st.caption(
    "数据来源：Olist Brazilian E-Commerce Public Dataset"
)
