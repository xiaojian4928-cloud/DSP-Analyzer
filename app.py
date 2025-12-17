import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- 1. 页面配置与深度视觉定制 ---
st.set_page_config(page_title="DSP 投放洞察看板", layout="wide")

st.markdown("""
    <style>
    /* 全局背景 */
    .stApp { background-color: #FFFFFF !important; }
    h1, h2, h3, .stMetric label, label, p { color: #0A192F !important; font-weight: 700 !important; }

    /* 顶部容器 */
    .top-bar, .chart-filter-box {
        background-color: #EBF5FF !important;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 25px;
        border: 1px solid #D1E3FF;
    }

    /* 1. 修改 ADV Name 选中标签颜色：深蓝色底，白色字 */
    span[data-baseweb="tag"] {
        background-color: #003366 !important;
        color: white !important;
    }
    span[data-baseweb="tag"] span {
        color: white !important;
    }

    /* 2. 修改时间筛选框及下拉框颜色：由黑改浅蓝 */
    div[data-baseweb="select"] > div, 
    div[data-baseweb="base-input"] > div {
        background-color: #F0F8FF !important;
        color: #0A192F !important;
        border: 1px solid #C2DFFF !important;
    }
    /* 针对日期输入的特定调整 */
    div[data-testid="stDateInput"] input {
        background-color: #F0F8FF !important;
        color: #0A192F !important;
    }

    /* 3. 表格样式：浅蓝色表头 + 浅灰色网格线 */
    .stDataFrame {
        border: 1px solid #E2E8F0 !important;
    }
    /* 强制表头样式 */
    [data-testid="stTable"] thead th {
        background-color: #D1E9FF !important;
        color: #0A192F !important;
        border-bottom: 1px solid #CBD5E0 !important;
    }
    /* 单元格及浅灰色网格线 */
    [data-testid="stTable"] td {
        background-color: #F8FBFF !important;
        color: #333333 !important;
        border: 1px solid #E2E8F0 !important;
    }

    /* KPI 数值 */
    div[data-testid="stMetricValue"] { color: #004A99 !important; font-weight: 800 !important; }
    
    /* 隐藏默认序号列的辅助 CSS (在使用 st.dataframe 时) */
    [data-testid="stTable"] th:first-child, [data-testid="stTable"] td:first-child {
        display: none;
    }

    [data-testid="stSidebar"] { display: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 数据处理与计算函数 ---
def calc_metrics(temp_df):
    temp_df['Total ROAS'] = (temp_df['Total Sales'] / temp_df['Total Cost']).replace([float('inf'), -float('inf')], 0).fillna(0)
    temp_df['CPM'] = (temp_df['Total Cost'] / (temp_df['Impressions'] / 1000)).replace([float('inf'), -float('inf')], 0).fillna(0)
    temp_df['CPC'] = (temp_df['Total Cost'] / temp_df['Clicks']).replace([float('inf'), -float('inf')], 0).fillna(0)
    temp_df['CTR'] = (temp_df['Clicks'] / temp_df['Impressions']).replace([float('inf'), -float('inf')], 0).fillna(0)
    temp_df['Total NTB Rate'] = (temp_df['Total New To Brand Purchases'] / temp_df['Total Purchases']).replace([float('inf'), -float('inf')], 0).fillna(0)
    return temp_df

def load_and_clean_data(file):
    df = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
    df.columns = df.columns.str.strip()
    mapping = {
        'Date': '日期', 'Advertiser Name': 'ADV Name',
        'Total Detail Page View': 'Total Detail Page View', 'Total Add To Cart': 'Total Add To Cart',
        'Total Purchases': 'Total Purchases', 'Total New To Brand Purchases': 'Total New To Brand Purchases',
        'Total Sales': 'Total Sales', 'Total Cost': 'Total Cost', 'Impressions': 'Impressions'
    }
    df.rename(columns=mapping, inplace=True)
    df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
    num_cols = ['Total Cost', 'Total Sales', 'Impressions', 'Clicks', 'Total Detail Page View', 
                'Total Add To Cart', 'Total Purchases', 'Total Units Sold', 'Total New To Brand Purchases']
    for col in num_cols:
        if col not in df.columns: df[col] = 0
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

# --- 3. 页面逻辑 ---
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False

if not st.session_state.data_loaded:
    st.write("请在下方上传 DSP 报表文件...")
    uploaded_file = st.file_uploader("", type=['xlsx', 'csv'])
    if uploaded_file:
        st.session_state.df = load_and_clean_data(uploaded_file)
        st.session_state.data_loaded = True
        st.rerun()
else:
    df = st.session_state.df
    st.markdown('<h1>📊 DSP 投放洞察看板</h1>', unsafe_allow_html=True)

    # 1. 顶部筛选区
    st.markdown('<div class="top-bar">', unsafe_allow_html=True)
    f1, f2, f3 = st.columns([3, 3, 1])
    with f1:
        all_advs = sorted(df['ADV Name'].unique().tolist())
        selected_advs = st.multiselect("Advertiser Name 筛选", all_advs, default=all_advs)
    with f2:
        m_d, max_d = df['日期'].min().date(), df['日期'].max().date()
        date_range = st.date_input("统计时间段", [m_d, max_d])
    with f3:
        st.write("")
        if st.button("🔄 重新上传"):
            st.session_state.data_loaded = False
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # 数据过滤
    if len(date_range) == 2:
        sdf = df.loc[(df['ADV Name'].isin(selected_advs)) & (df['日期'].dt.date >= date_range[0]) & (df['日期'].dt.date <= date_range[1])]
    else:
        sdf = df[df['ADV Name'].isin(selected_advs)]

    summary = sdf.groupby(['ADV Name', '日期']).agg({
        'Total Cost': 'sum', 'Total Sales': 'sum', 'Impressions': 'sum', 'Clicks': 'sum',
        'Total Detail Page View': 'sum', 'Total Add To Cart': 'sum', 'Total Purchases': 'sum',
        'Total Units Sold': 'sum', 'Total New To Brand Purchases': 'sum'
    }).reset_index()
    summary = calc_metrics(summary)

    # --- 4. KPI 指标 ---
    t1, t2, t3, t4, t5 = st.columns(5)
    tc, ts, ti, tp, tnb = summary['Total Cost'].sum(), summary['Total Sales'].sum(), summary['Impressions'].sum(), summary['Total Purchases'].sum(), summary['Total New To Brand Purchases'].sum()
    t1.metric("Total Cost", f"{tc:,.2f}")
    t2.metric("Total Sales", f"{ts:,.2f}")
    t3.metric("Total eCPM", f"{(tc/(ti/1000) if ti>0 else 0):.2f}")
    t4.metric("Total ROAS", f"{(ts/tc if tc>0 else 0):.2f}")
    t5.metric("Total NTBR", f"{(tnb/tp if tp>0 else 0):.2%}")

    # --- 5. 数据统计明细表 (修正: 移除第一列序号 + 浅灰色网格线) ---
    st.write("---")
    st.subheader("📋 数据统计明细表")
    order = ['ADV Name', '日期', 'Total Cost', 'Total ROAS', 'CPM', 'CPC', 'Impressions', 'Clicks', 'Total Detail Page View', 'Total Add To Cart', 'Total Purchases', 'Total Units Sold', 'CTR', 'Total NTB Rate', 'Total New To Brand Purchases', 'Total Sales']
    summary_display = summary[[c for c in order if c in summary.columns]].sort_values(['ADV Name', '日期'])
    
    # 转换为适合显示的格式
    summary_display['日期'] = summary_display['日期'].dt.strftime('%Y-%m-%d')
    
    # 使用 st.dataframe 并隐藏 index
    st.dataframe(
        summary_display,
        use_container_width=True,
        hide_index=True,  # 关键：去掉第一列区号/序号列
        column_config={
            "Total Cost": st.column_config.NumberColumn(format="%.2f"),
            "Total Sales": st.column_config.NumberColumn(format="%.2f"),
            "Total ROAS": st.column_config.NumberColumn(format="%.2f"),
            "CTR": st.column_config.NumberColumn(format="%.2%"),
            "Total NTB Rate": st.column_config.NumberColumn(format="%.2%"),
        }
    )

    # --- 6. 趋势分析图 ---
    st.write("---")
    st.subheader("📈 趋势对比分析")
    st.markdown('<div class="chart-filter-box">', unsafe_allow_html=True)
    c_col1, c_col2 = st.columns(2)
    m_bar = c_col1.selectbox("柱状图指标 (左轴)", ['Total Cost', 'Impressions', 'Total Sales'])
    m_line = c_col2.selectbox("折线图指标 (右轴)", ['Total ROAS', 'Total NTB Rate', 'CTR', 'CPM'])
    st.markdown('</div>', unsafe_allow_html=True)
    
    chart_df = summary_display.groupby('日期').agg({
        'Total Cost': 'sum', 'Total Sales': 'sum', 'Impressions': 'sum', 
        'Clicks': 'sum', 'Total Purchases': 'sum', 'Total New To Brand Purchases': 'sum'
    }).reset_index()
    chart_df = calc_metrics(chart_df)
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=chart_df['日期'], y=chart_df[m_bar], name=m_bar, marker_color='#004A99'), secondary_y=False)
    fig.add_trace(go.Scatter(x=chart_df['日期'], y=chart_df[m_line], name=m_line, line=dict(color='#E67E22', width=4)), secondary_y=True)
    
    fig.update_layout(paper_bgcolor='white', plot_bgcolor='#F8FBFF', hovermode="x unified")
    fig.update_yaxes(tickfont=dict(color="#333333"), secondary_y=False)
    fig.update_yaxes(tickfont=dict(color="#333333"), secondary_y=True)
    st.plotly_chart(fig, use_container_width=True)
