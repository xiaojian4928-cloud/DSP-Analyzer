import streamlit as st
import pandas as pd

# --- 1. 深度视觉定制：锁定深灰字体与浅蓝色表格底色 ---
st.set_page_config(page_title="DSP 数据看板", layout="wide")

st.markdown("""
    <style>
    /* 强制全局背景与主题变量 */
    :root {
        --secondary-background-color: #EBF5FF !important; 
        --background-color: #FFFFFF !important;
        --text-color: #2D3748 !important;
    }
    .stApp { background-color: #F8FAFC !important; }
    
    /* 标题及数值颜色：深灰色 */
    .main-title { color: #4A5568 !important; font-weight: 800; text-align: center; margin-bottom: 25px; }
    
    /* 强制顶部五个指标卡片的数值和标签为深灰色 */
    [data-testid="stMetricValue"] { color: #4A5568 !important; }
    [data-testid="stMetricLabel"] > div { color: #4A5568 !important; }

    /* 强制将表格底色改为浅蓝色 */
    [data-testid="stDataFrame"], [data-testid="stDataFrameGrid"] {
        background-color: #EBF5FF !important;
        border-radius: 8px;
    }
    div[data-testid="stDataFrame"] div[role="grid"] {
        background-color: #EBF5FF !important;
    }

    /* 筛选框样式 */
    div[data-baseweb="select"] > div, div[data-baseweb="base-input"] > div, input {
        background-color: #F0F7FF !important;
        color: #4A5568 !important;
        border: 1px solid #BEE3F8 !important;
    }

    /* 首页上传框样式 */
    [data-testid="stFileUploader"] section { background-color: #0A192F !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. 核心计算函数 ---
def calculate_metrics(df_in):
    d = df_in.copy()
    def safe_div(a, b): return (a / b).replace([float('inf'), -float('inf')], 0).fillna(0)
    
    d['Total ROAS'] = safe_div(d['Total Sales'], d['Total Cost'])
    d['CPM'] = safe_div(d['Total Cost'], d['Impressions'] / 1000)
    d['CPC'] = safe_div(d['Total Cost'], d['Clicks'])
    d['Total CPDPV'] = safe_div(d['Total Cost'], d['Total Detail Page View'])
    d['CTR'] = safe_div(d['Clicks'], d['Impressions'])
    d['Total DPVR'] = safe_div(d['Total Detail Page View'], d['Impressions'])
    d['Total ATCR'] = safe_div(d['Total Add To Cart'], d['Impressions'])
    d['Total NTB Rate'] = safe_div(d['Total New To Brand Purchases'], d['Total Purchases'])
    return d

# --- 3. 逻辑流程 ---
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = None

if st.session_state.processed_data is None:
    st.markdown("<h1 class='main-title'>🚀 DSP 智能分析中心</h1>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("请上传广告报表", type=['xlsx', 'csv'])
    if uploaded_file:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        df.columns = df.columns.str.strip()
        df.rename(columns={'Date': '日期', 'Advertiser Name': 'ADV Name'}, inplace=True)
        df['日期'] = pd.to_datetime(df['日期']).dt.date
        st.session_state.processed_data = df
        st.rerun()
else:
    st.markdown('<h1 class="main-title">📊 DSP 投放洞察看板</h1>', unsafe_allow_html=True)
    raw_df = st.session_state.processed_data

    # --- 筛选区 ---
    with st.container():
        st.markdown("<div style='background-color:#EBF5FF; padding:15px; border-radius:10px; margin-bottom:20px; border:1px solid #BEE3F8;'>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([3, 3, 1])
        with c1:
            sel_adv = st.multiselect("筛选广告主", sorted(raw_df['ADV Name'].unique()), default=raw_df['ADV Name'].unique())
        with c2:
            dr = st.date_input("日期范围", [raw_df['日期'].min(), raw_df['日期'].max()])
        with c3:
            st.write("")
            if st.button("🔄 重新上传"):
                st.session_state.processed_data = None
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    if len(dr) == 2:
        # 严格执行筛选逻辑
        sdf = raw_df[(raw_df['ADV Name'].isin(sel_adv)) & (raw_df['日期'] >= dr[0]) & (raw_df['日期'] <= dr[1])]
        
        if not sdf.empty:
            # 1. 顶部汇总指标计算
            total_cost = sdf['Total Cost'].sum()
            total_sales = sdf['Total Sales'].sum()
            total_imps = sdf['Impressions'].sum()
            total_pur = sdf['Total Purchases'].sum()
            total_ntb_pur = sdf['Total New To Brand Purchases'].sum()
            
            agg_roas = total_sales / total_cost if total_cost > 0 else 0
            agg_ecpm = (total_cost / (total_imps / 1000)) if total_imps > 0 else 0
            agg_ntb_rate = (total_ntb_pur / total_pur) if total_pur > 0 else 0

            # 顶部核心指标展示
            st.markdown("<h3 style='color:#4A5568;'>📌 核心指标汇总</h3>", unsafe_allow_html=True)
            k1, k2, k3, k4, k5 = st.columns(5)
            k1.metric("Total Cost", f"${total_cost:,.2f}")
            k2.metric("Total Sales", f"${total_sales:,.2f}")
            k3.metric("ECPM", f"${agg_ecpm:,.2f}")
            k4.metric("Total ROAS",
