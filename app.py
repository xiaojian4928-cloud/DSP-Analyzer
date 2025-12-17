import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- 1. 页面配置与深度视觉定制 ---
st.set_page_config(page_title="DSP 投放洞察看板", layout="wide")

st.markdown("""
    <style>
    /* 1. 全局背景：浅灰蓝 */
    .stApp { background-color: #F0F4F8 !important; }
    h1, h2, h3, label, p { color: #2D3748 !important; font-weight: 700 !important; }

    /* 2. 首页上传界面 */
    .upload-container {
        background: linear-gradient(135deg, #E6F0FF 0%, #F0F4F8 100%);
        padding: 40px;
        border-radius: 20px;
        text-align: center;
        border: 2px solid #BEE3F8;
    }

    /* 3. 上传框：深蓝色底 */
    [data-testid="stFileUploader"] section {
        background-color: #0A192F !important;
        color: white !important;
        border: 2px dashed #3182CE !important;
    }

    /* 4. 筛选框容器：浅蓝色 */
    .top-bar, .chart-filter-box {
        background-color: #E1EFFE !important;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 20px;
        border: 1px solid #BEE3F8;
    }

    /* 5. 强制去除黑色背景（针对输入框和按钮） */
    div[data-baseweb="select"] > div, 
    div[data-baseweb="base-input"] > div,
    div[data-testid="stDateInput"] div,
    input, .stButton > button {
        background-color: #EBF5FF !important;
        color: #2D3748 !important;
        border: 1px solid #CBD5E0 !important;
    }
    
    /* 6. 表格背景强制修正：由黑转浅蓝 */
    /* 针对 Streamlit 新版 Dataframe 的容器穿透 */
    [data-testid="stDataFrame"], [data-testid="stDataFrame"] > div {
        background-color: #EBF5FF !important;
    }
    .stElementContainer div { background-color: transparent !important; }

    /* 7. 指标卡片数值 */
    div[data-testid="stMetricValue"] { color: #2B6CB0 !important; font-weight: 800 !important; }
    
    [data-testid="stSidebar"] { display: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心计算函数 ---
def calc_metrics(df_input):
    temp_df = df_input.copy()
    # 使用基础列重新计算比例指标，确保准确性
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
        'Total Sales': 'Total Sales', 'Total Cost': 'Total Cost', 'Impressions': 'Impressions',
        'Clicks': 'Clicks', 'Total Units Sold': 'Total Units Sold'
    }
    df.rename(columns=mapping, inplace=True)
    df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
    
    num_cols = list(mapping.values())[2:] # 除了日期和名称外的所有数值列
    for col in num_cols:
        if col not in df.columns: df[col] = 0
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

# --- 3. 页面逻辑 ---
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False

if not st.session_state.data_loaded:
    st.markdown('<div class="upload-container"><h1>🚀 DSP 数据洞察中心</h1><p>请上传您的广告报表</p></div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("", type=['xlsx', 'csv'])
    if uploaded_file:
        st.session_state.df = load_and_clean_data(uploaded_file)
        st.session_state.data_loaded = True
        st.rerun()
else:
    df = st.session_state.df
    st.markdown('<h1>📊 DSP 投放洞察看板</h1>', unsafe_allow_html=True)

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

    if len(date_range) == 2:
        sdf = df.loc[(df['ADV Name'].isin(selected_advs)) & (df['日期'].dt.date >= date_range[0]) & (df['日期'].dt.date <= date_range[1])]
    else:
        sdf = df[df['ADV Name'].isin(selected_advs)]

    # 聚合汇总
    summary = sdf.groupby(['ADV Name', '日期']).sum(numeric_only=True).reset_index()
    summary = calc_metrics(summary)

    # KPI 区域
    t1, t2, t3, t4, t5 = st.columns(5)
    tc, ts, ti, tp, tnb = summary['Total Cost'].sum(), summary['Total Sales'].sum(), summary['Impressions'].sum(), summary['Total Purchases'].sum(), summary['Total New To Brand Purchases'].sum()
    t1.metric("Total Cost", f"{tc:,.2f}")
    t2.metric("Total Sales", f"{ts:,.2f}")
    t3.metric("Total eCPM", f"{(tc/(ti/1000) if ti>0 else 0):.2f}")
    t4.metric("Total ROAS", f"{(ts/tc if tc>0 else 0):.2f}")
    t5.metric("Total NTBR", f"{(tnb/tp if tp>0 else 0):.2%}")

    # --- 4. 数据统计明细表 (恢复表头列名与顺序) ---
    st.write("---")
    st.subheader("📋 数据统计明细表")
    
    # 严格恢复之前的表头顺序和名称
    order = ['ADV Name', '日期', 'Total Cost', 'Total ROAS', 'CPM', 'CPC', 'Impressions', 'Clicks', 'Total Detail Page View', 'Total Add To Cart', 'Total Purchases', 'Total Units Sold', 'CTR', 'Total NTB Rate', 'Total New To Brand Purchases', 'Total Sales']
    summary_display = summary[[c for c in order if c in summary.columns]].sort_values(['ADV Name', '日期'])

    st.dataframe(
        summary_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "日期": st.column_config.DateColumn("日期", format="YYYY-MM-DD"),
            "Total Cost": st.column_config.NumberColumn("Total Cost", format="%.2f"),
            "Total Sales": st.column_config.NumberColumn("Total Sales", format="%.2f"),
            "Total ROAS": st.column_config.NumberColumn("Total ROAS", format="%.2f"),
            "CPM": st.column_config.NumberColumn("CPM", format="%.2f"),
            "CPC": st.column_config.NumberColumn("CPC", format="%.2f"),
            "CTR": st.column_config.NumberColumn("CTR", format="%.2%"),
            "Total NTB Rate": st.column_config.NumberColumn("Total NTB Rate", format="%.2%"),
            "Total Purchases": st.column_config.NumberColumn("Total Purchases", format="%d"),
            "Total Units Sold": st.column_config.NumberColumn("Total Units Sold", format="%d"),
            "Total New To Brand Purchases": st.column_config.NumberColumn("Total New To Brand Purchases", format="%d"),
            "Clicks": st.column_config.NumberColumn("Clicks", format="%d"),
            "Impressions": st.column_config.NumberColumn("Impressions", format="%d"),
        }
    )

    # --- 5. 趋势分析图 ---
    st.write("---")
    st.subheader("📈 趋势对比分析")
    st.markdown('<div class="chart-filter-box">', unsafe_allow_html=True)
    c_col1, c_col2 = st.columns(2)
    m_bar = c_col1.selectbox("柱状图指标 (左轴)", ['Total Cost', 'Impressions', 'Total Sales', 'Total Purchases'])
    m_line = c_col2.selectbox("折线图指标 (右轴)", ['Total ROAS', 'Total NTB Rate', 'CTR', 'CPM'])
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 图表计算：先按日期求和基础列，再重新计算比例指标
    chart_data_base = summary.groupby('日期').sum(numeric_only=True).reset_index()
    chart_data = calc_metrics(chart_data_base)
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=chart_data['日期'], y=chart_data[m_bar], name=m_bar, marker_color='#4299E1'), secondary_y=False)
    fig.add_trace(go.Scatter(x=chart_data['日期'], y=chart_data[m_line], name=m_line, line=dict(color='#ED8936', width=4)), secondary_y=True)
    
    # 坐标轴颜色：横纵轴全部深灰色
    axis_theme = dict(showgrid=True, gridcolor='#E2E8F0', tickfont=dict(color="#4A5568"), titlefont=dict(color="#4A5568"))

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#F7FAFC', hovermode="x unified",
        xaxis=axis_theme, yaxis=axis_theme, 
        yaxis2=dict(overlaying='y', side='right', **axis_theme)
    )
    st.plotly_chart(fig, use_container_width=True)
