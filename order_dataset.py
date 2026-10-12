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
# 2. 自动读取当前文件夹中的 CSV
# =====================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_PATH = BASE_DIR / "olist_orders_dataset.csv"


@st.cache_data
def load_data(file_path):

    data = pd.read_csv(file_path)

    # 日期字段转换
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


# 检查文件是否存在
if not DATA_PATH.exists():

    st.error("找不到订单数据文件！")

    st.write("程序正在寻找：")

    st.code(str(DATA_PATH))

    st.info(
        "请确认 app.py 和 "
        "olist_orders_dataset.csv "
        "放在同一个文件夹中。"
    )

    st.stop()


# 读取数据
df = load_data(str(DATA_PATH))


# =====================================================
# 3. 检查必要字段
# =====================================================

required_columns = [
    "order_id",
    "customer_id",
    "order_status",
    "order_purchase_timestamp",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date"
]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:

    st.error(
        f"数据文件缺少必要字段：{missing_columns}"
    )

    st.stop()


# =====================================================
# 4. 数据清洗
# =====================================================

# 删除没有订单编号的记录
df = df.dropna(
    subset=["order_id"]
).copy()

# 每个订单只保留一条记录
df = df.drop_duplicates(
    subset=["order_id"],
    keep="first"
).copy()

# 统一订单状态格式
df["order_status"] = (
    df["order_status"]
    .fillna("unknown")
    .astype(str)
    .str.strip()
    .str.lower()
)


# 原始订单状态中文翻译
status_translation = {
    "created": "已创建",
    "approved": "已批准",
    "processing": "处理中",
    "invoiced": "已开票",
    "shipped": "已发货",
    "delivered": "已送达",
    "canceled": "已取消",
    "unavailable": "不可用",
    "unknown": "未知状态"
}

df["原始订单状态"] = (
    df["order_status"]
    .map(status_translation)
    .fillna("其他状态")
)


# =====================================================
# 5. 订单物流分类
# =====================================================

def classify_order(row):

    status = row["order_status"]

    carrier_date = row[
        "order_delivered_carrier_date"
    ]

    customer_date = row[
        "order_delivered_customer_date"
    ]

    # 已送达
    if status == "delivered":

        return "已送达"

    # 已取消
    elif status == "canceled":

        return "已取消"

    # 不可用
    elif status == "unavailable":

        return "不可用"

    # 有物流交接时间，但还没有送达记录
    elif (
        pd.notna(carrier_date)
        and pd.isna(customer_date)
    ):

        return "已发货"

    # 原始状态为 shipped
    elif status == "shipped":

        return "已发货"

    # 尚未交给物流公司的订单
    elif status in [
        "created",
        "approved",
        "processing",
        "invoiced"
    ]:

        return "待发货"

    # 其他状态
    else:

        return "其他状态"


df["物流分类"] = df.apply(
    classify_order,
    axis=1
)


# =====================================================
# 6. 逾期订单判断
# =====================================================

valid_purchase_dates = (
    df["order_purchase_timestamp"].dropna()
)

if valid_purchase_dates.empty:

    default_date = pd.Timestamp.today().date()

else:

    default_date = (
        valid_purchase_dates.max().date()
    )


# =====================================================
# 7. 左侧筛选栏
# =====================================================

st.sidebar.title("🔎 订单查询中心")

reference_date = st.sidebar.date_input(
    "逾期判断基准日期",
    value=default_date
)

reference_timestamp = pd.Timestamp(
    reference_date
)


# 尚未送达、未取消且超过预计送达日期
df["是否逾期"] = (
    df["order_status"].isin([
        "created",
        "approved",
        "processing",
        "invoiced",
        "shipped"
    ])
    & df["order_estimated_delivery_date"].notna()
    & (
        df["order_estimated_delivery_date"]
        < reference_timestamp
    )
)


# 选择物流分类
status_options = [
    "全部",
    "待发货",
    "已发货",
    "已送达",
    "已取消",
    "不可用",
    "其他状态"
]

selected_status = st.sidebar.selectbox(
    "选择订单分类",
    status_options
)


# 下单日期筛选
if not valid_purchase_dates.empty:

    min_date = (
        valid_purchase_dates.min().date()
    )

    max_date = (
        valid_purchase_dates.max().date()
    )

    date_range = st.sidebar.date_input(
        "下单日期范围",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

else:

    date_range = (None, None)


# 订单编号搜索
search_order = st.sidebar.text_input(
    "输入订单编号搜索",
    placeholder="请输入订单 ID"
)


# 逾期订单筛选
only_overdue = st.sidebar.checkbox(
    "只查看逾期订单",
    value=False
)


# =====================================================
# 8. 根据条件筛选订单
# =====================================================

filtered_df = df.copy()


# 根据物流分类筛选
if selected_status != "全部":

    filtered_df = filtered_df[
        filtered_df["物流分类"] == selected_status
    ]


# 根据下单日期筛选
if (
    isinstance(date_range, (tuple, list))
    and len(date_range) == 2
    and date_range[0] is not None
    and date_range[1] is not None
):

    start_date = pd.Timestamp(
        date_range[0]
    )

    end_date = (
        pd.Timestamp(date_range[1])
        + pd.Timedelta(days=1)
    )

    filtered_df = filtered_df[
        (
            filtered_df["order_purchase_timestamp"]
            >= start_date
        )
        &
        (
            filtered_df["order_purchase_timestamp"]
            < end_date
        )
    ]


# 根据订单编号搜索
if search_order.strip():

    filtered_df = filtered_df[
        filtered_df["order_id"].str.contains(
            search_order.strip(),
            case=False,
            na=False,
            regex=False
        )
    ]


# 只查看逾期订单
if only_overdue:

    filtered_df = filtered_df[
        filtered_df["是否逾期"]
    ]


# =====================================================
# 9. 顶部 KPI 指标卡片
# =====================================================

total_orders = len(df)

pending_orders = int(
    (df["物流分类"] == "待发货").sum()
)

shipped_orders = int(
    (df["物流分类"] == "已发货").sum()
)

delivered_orders = int(
    (df["物流分类"] == "已送达").sum()
)

canceled_orders = int(
    (df["物流分类"] == "已取消").sum()
)

overdue_orders = int(
    df["是否逾期"].sum()
)


st.subheader("📊 订单运营总览")

col1, col2, col3 = st.columns(3)

col1.metric(
    "📦 订单总数",
    f"{total_orders:,}"
)

col2.metric(
    "🟠 待发货订单",
    f"{pending_orders:,}"
)

col3.metric(
    "🚚 已发货订单",
    f"{shipped_orders:,}"
)


col4, col5, col6 = st.columns(3)

col4.metric(
    "✅ 已送达订单",
    f"{delivered_orders:,}"
)

col5.metric(
    "❌ 已取消订单",
    f"{canceled_orders:,}"
)

col6.metric(
    "⚠️ 逾期未送达",
    f"{overdue_orders:,}"
)


st.info(
    f"当前筛选条件下共有 "
    f"{len(filtered_df):,} 笔订单。"
)

st.markdown("---")


# =====================================================
# 10. 订单状态分析图表
# =====================================================

st.subheader("📈 订单状态分析")

chart_col1, chart_col2 = st.columns(2)


# 物流分类饼图
with chart_col1:

    status_count = (
        df["物流分类"]
        .value_counts()
        .reset_index()
    )

    status_count.columns = [
        "物流分类",
        "订单数量"
    ]

    fig_pie = px.pie(
        status_count,
        names="物流分类",
        values="订单数量",
        title="订单物流分类占比",
        hole=0.4
    )

    fig_pie.update_traces(
        textinfo="percent+label"
    )

    st.plotly_chart(
        fig_pie,
        use_container_width=True
    )


# 原始订单状态柱状图
with chart_col2:

    original_count = (
        df["原始订单状态"]
        .value_counts()
        .reset_index()
    )

    original_count.columns = [
        "原始订单状态",
        "订单数量"
    ]

    fig_bar = px.bar(
        original_count,
        x="原始订单状态",
        y="订单数量",
        title="原始订单状态分布",
        text="订单数量"
    )

    fig_bar.update_layout(
        xaxis_title="订单状态",
        yaxis_title="订单数量"
    )

    st.plotly_chart(
        fig_bar,
        use_container_width=True
    )


# =====================================================
# 11. 每月订单趋势
# =====================================================

st.subheader("📅 每月订单趋势")

monthly_data = df.dropna(
    subset=["order_purchase_timestamp"]
).copy()

monthly_data["月份"] = (
    monthly_data["order_purchase_timestamp"]
    .dt.to_period("M")
    .astype(str)
)

monthly_count = (
    monthly_data.groupby("月份")
    .size()
    .reset_index(name="订单数量")
)

fig_line = px.line(
    monthly_count,
    x="月份",
    y="订单数量",
    markers=True,
    title="每月订单数量变化"
)

fig_line.update_layout(
    xaxis_title="月份",
    yaxis_title="订单数量"
)

st.plotly_chart(
    fig_line,
    use_container_width=True
)


# =====================================================
# 12. 订单名单展示
# =====================================================

st.markdown("---")

st.subheader("📋 订单名单管理")

st.write(
    "在左侧选择订单分类、日期范围，"
    "或者输入订单编号，即可查看对应的订单名单。"
)


display_columns = [
    "order_id",
    "customer_id",
    "原始订单状态",
    "物流分类",
    "order_purchase_timestamp",
    "order_delivered_carrier_date",
    "order_estimated_delivery_date",
    "order_delivered_customer_date",
    "是否逾期"
]

display_df = filtered_df[
    display_columns
].copy()


# 修改列名为中文
display_df = display_df.rename(
    columns={
        "order_id": "订单编号",
        "customer_id": "客户编号",
        "order_purchase_timestamp": "下单时间",
        "order_delivered_carrier_date": "交给物流时间",
        "order_estimated_delivery_date": "预计送达时间",
        "order_delivered_customer_date": "实际送达时间",
        "是否逾期": "是否逾期未送达"
    }
)


# 格式化日期
date_columns = [
    "下单时间",
    "交给物流时间",
    "预计送达时间",
    "实际送达时间"
]

for col in date_columns:

    display_df[col] = pd.to_datetime(
        display_df[col],
        errors="coerce"
    ).dt.strftime("%Y-%m-%d %H:%M:%S")


st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True
)


st.success(
    f"已展示 {len(display_df):,} 笔订单。"
)


# =====================================================
# 13. 导出 CSV 文件
# =====================================================

csv_data = display_df.to_csv(
    index=False
).encode("utf-8-sig")


st.download_button(
    label="📥 下载当前订单名单 CSV",
    data=csv_data,
    file_name="olist_orders_filtered.csv",
    mime="text/csv"
)


# =====================================================
# 14. 物流分类说明
# =====================================================

with st.expander("📖 查看物流分类与数据说明"):

    st.markdown(
        """
        ### 订单分类规则

        **待发货：**
        原始状态为 created、approved、processing
        或 invoiced 的订单。

        **已发货：**
        原始状态为 shipped，或者已经存在物流交接时间，
        但没有实际送达时间的订单。

        **已送达：**
        原始状态为 delivered 的订单。

        **已取消：**
        原始状态为 canceled 的订单。

        **不可用：**
        原始状态为 unavailable 的订单。

        **其他状态：**
        不符合以上分类规则的订单。

        ### 逾期规则

        对指定的未送达订单，如果预计送达日期早于
        侧边栏设置的判断基准日期，则标记为逾期。

        ### 数据来源

        Olist Brazilian E-Commerce Public Dataset。

        ### 注意事项

        本数据集是历史订单数据，不是实时物流接口。
        「待发货」是本 Dashboard 定义的管理分类，
        并不代表订单已经完成付款。
        """
    )


st.caption(
    "Olist 电商订单管理系统 | "
    "Streamlit + Pandas + Plotly"
)