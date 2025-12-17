import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- 1. 页面配置与深度视觉定制 ---
st.set_page_config(page_title="DSP 投放洞察看板", layout="wide")

st.markdown("""
    <style>
    /* 全局背景：浅灰蓝 */
    .stApp { background-color: #F0F4F8 !important; }
    
    /* 1. 数据看板界面大标题：深蓝色 */
    .main-title {
        color: #003366 !important; 
        font-size: 2.5rem !important;
        font-weight: 800 !important;
        margin-bottom: 20px !important;
    }

    /* 2. 首页上传界面定制 (保持您之前的科技感设置) */
    .upload-bg-container {
        background-image: linear-gradient(rgba(240, 244, 248, 0.8), rgba(240, 244, 248, 0.8)), 
                          url('https://img.freepik.com/free-vector/abstract-digital-technology-background-with-network-connection-lines_1017-25552.jpg');
        background-size: cover;
        background-position: center;
        padding: 60px 40px;
        border-radius: 20px;
        text-align: center;
        border: 1px solid #D1E3FF;
        margin-bottom: 30px;
    }
    .upload-bg-container h1 { color: #2D3748 !important; }
    .upload-bg-container p { color: #4A5568 !important; }

    /* 上传框底色：深蓝色 (保持) */
    [data-testid="stFileUploader"] section {
        background-color: #0A192F !important;
        border: 2px dashed #3182CE !important;
        border-radius: 10px;
    }
    [data-testid="stFileUploader"] section div, [data-testid="stFileUploader"] section span {
        color: #E2E8F0 !important;
    }

    /* 3. 看板表格底色：改成浅色 */
    [data-testid="stDataFrame"], [data-testid="stDataFrameGrid"], div[data-testid="stTable"] {
        background-color: #F8FAFC !important;
    }
    /* 强制表格行和单元格为浅色 */
    [data-testid="stDataFrame"] div[role="grid"] {
        background-color: #F8FAFC !important;
    }

    /* 筛选框及进度条 (保持) */
    .top-bar, .chart-filter-box {
        background-color: #E1EFFE !important;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #BEE3F8;
    }
    .stProgress > div > div > div > div { background-color: #003366 !important; }
    div[data-baseweb="select"] > div, div[data-baseweb="base-input"] > div, input {
        background-color: #EBF5FF !important;
        color: #2D3748 !important;
    }
    span[data-baseweb="tag"] { background-color: #003366 !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心计算逻辑 (保持不动) ---
def calc_metrics(df_in):
    df_res = df_in.copy()
    def safe_div(a, b): return (a / b).replace([float('inf'), -float('inf')], 0).fillna(0)
    df_res['Total ROAS'] = safe_div(df_res['Total Sales'], df_res['Total Cost'])
    df_res['CPM'] = safe_div(df_res['Total Cost'], df_res['Impressions'] / 1000)
    df_res['CPC'] = safe_div(df_res['Total Cost'], df_res['Clicks'])
    df_res['CTR'] = safe_div(df_res['Clicks'], df_res['Impressions'])
    df_res['Total DPVR'] = safe_div(df_res['Total Detail Page View'], df_res['Impressions'])
    df_res['Total ATCR'] = safe_div(df_res['Total Add To Cart'], df_res['Impressions'])
    df_res['Total NTB Rate'] = safe_div(df_res['Total New To Brand Purchases'], df_res['Total Purchases'])
    df_res['Total CPDPV'] = safe_div(df_res['Total Cost'], df_res['Total Detail Page View'])
    return df_res

def load_data(file):
    df = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
    df.columns = df.columns.str.strip()
    map_dict = {
        'Date': '日期', 'Advertiser Name': 'ADV Name',
        'Total Detail Page View': 'Total Detail Page View', 'Total Add To Cart': 'Total Add To Cart',
        'Total Purchases': 'Total Purchases', 'Total New To Brand Purchases': 'Total New To Brand Purchases',
        'Total Sales': 'Total Sales', 'Total Cost': 'Total Cost', 'Impressions': 'Impressions',
        'Clicks': 'Clicks', 'Total Units Sold': 'Total Units Sold'
    }
    df.rename(columns=map_dict, inplace=True)
    df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
    for col in map_dict.values():
        if col not in df.columns and col not in ['日期', 'ADV Name']:
            df[col] = 0
        if col not in ['日期', 'ADV Name']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

# --- 3. 页面主逻辑 ---
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False

if not st.session_state.data_loaded:
    st.markdown('<div class="upload-bg-container"><h1>🚀 DSP 智能数据中心</h1><p>上传报表以解锁多维度增长洞察</p></div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("", type=['xlsx', 'csv'])
    if uploaded_file:
        st.session_state.df = load_data(uploaded_file)
        st.session_state.data_loaded = True
        st.rerun()
else:
    # 核心修改：大标题颜色
    st.markdown('<h1 class="main-title">📊 DSP 投放洞察看板</h1>', unsafe_allow_html=True)

    st.markdown('<div class="top-bar">', unsafe_allow_html=True)
    f1, f2, f3 = st.columns([3, 3, 1])
    with f1:
        sel_advs = st.multiselect("ADV Name 筛选", sorted(df['ADV Name'].unique()), default=df['ADV Name'].unique())
    with f2:
        d_range = st.date_input("时间段", [df['日期'].min(), df['日期'].max()])
    with f3:
        st.write("")
        if st.button("🔄 重新上传"):
            st.session_state.data_loaded = False
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    mask = (df['ADV Name'].isin(sel_advs))
    if len(d_range) == 2:
        mask &= (df['日期'].dt.date >= d_range[0]) & (df['日期'].dt.date <= d_range[1])
    sdf = df[mask]
    
    summary = sdf.groupby(['ADV Name', '日期']).sum(numeric_only=True).reset_index()
    summary = calc_metrics(summary)

    st.subheader("📋 数据统计明细表")
    final_order = ['ADV Name', '日期', 'Total Cost', 'Total ROAS', 'CPM', 'CPC', 'Total CPDPV', 'Impressions', 'Clicks', 'Total Detail Page View', 'Total Add To Cart', 'Total Purchases', 'Total Units Sold', 'CTR', 'Total DPVR', 'Total ATCR', 'Total NTB Rate', 'Total New To Brand Purchases', 'Total Sales']
    valid_order = [c for c in final_order if c in summary.columns]
    summary_display = summary[valid_order].sort_values(['ADV Name', '日期'])

    # 核心修改：表格浅色底 + 百分比指标配置
    st.dataframe(
        summary_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "日期": st.column_config.DateColumn(format="YYYY-MM-DD"),
            "Total Cost": st.column_config.NumberColumn(format="%.2f"),
            "Total ROAS": st.column_config.NumberColumn(format="%.2f"),
            "CTR": st.column_config.NumberColumn(format="%.2%"),          # 百分比
            "Total DPVR": st.column_config.NumberColumn(format="%.2%"),     # 百分比
            "Total ATCR": st.column_config.NumberColumn(format="%.2%"),     # 百分比
            "Total NTB Rate": st.column_config.NumberColumn(format="%.2%"), # 百分比
            "Total Purchases": st.column_config.NumberColumn(format="%d"),
            "Total Units Sold": st.column_config.NumberColumn(format="%d"),
        }
    )

    # 趋势图逻辑 (保持不动)
    st.write("---")
    st.subheader("📈 趋势对比分析")
    st.markdown('<div class="chart-filter-box">', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    m_bar = c1.selectbox("左轴 (柱状图)", ['Total Cost', 'Impressions', 'Total Sales', 'Total Purchases'])
    m_line = c2.selectbox("右轴 (折线图)", ['Total ROAS', 'CTR', 'Total NTB Rate', 'Total DPVR', 'CPM'])
    st.markdown('</div>', unsafe_allow_html=True)

    chart_base = summary.groupby('日期').sum(numeric_only=True).reset_index()
    chart_data = calc_metrics(chart_base)

    if not chart_data.empty:
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Bar(x=chart_data['日期'], y=chart_data[m_bar], name=m_bar, marker_color='#4299E1'), secondary_y=False)
        fig.add_trace(go.Scatter(x=chart_data['日期'], y=chart_data[m_line], name=m_line, line=dict(color='#ED8936', width=4)), secondary_y=True)
        ax_style = dict(showgrid=True, gridcolor='#E2E8F0', tickfont=dict(color="#4A5568"))
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#F7FAFC', xaxis=ax_style, yaxis=ax_style, yaxis2=dict(overlaying='y', side='right', **ax_style), hovermode="x unified", height=500)
        st.plotly_chart(fig, use_container_width=True)
