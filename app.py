import streamlit as st
import pandas as pd

# --- 1. 深度视觉修复：彻底解决黑色底色问题 ---
st.set_page_config(page_title="DSP 数据看板", layout="wide")

st.markdown("""
    <style>
    /* 核心：覆盖 Streamlit 全局主题变量，强制将暗色背景改为浅色 */
    :root {
        --secondary-background-color: #F0F4F8 !important; /* 筛选框背景 */
        --background-color: #FFFFFF !important;           /* 整体背景 */
        --text-color: #2D3748 !important;                /* 文字颜色 */
    }

    /* 强制全局背景 */
    .stApp { background-color: #F8FAFC !important; }
    
    /* 强制抹除表格（Dataframe）的黑色背景 */
    [data-testid="stDataFrame"], 
    [data-testid="stDataFrameGrid"],
    div[role="grid"] {
        background-color: #FFFFFF !important;
    }

    /* 筛选框（下拉框、输入框）强制浅蓝色 */
    div[data-baseweb="select"] > div, 
    div[data-baseweb="base-input"] > div,
    input {
        background-color: #E1EFFE !important;
        color: #2D3748 !important;
        border: 1px solid #BEE3F8 !important;
    }
    
    /* 大标题深蓝色 */
    .main-title { color: #003366 !important; font-weight: 800; text-align: center; }

    /* 首页上传框样式 */
    [data-testid="stFileUploader"] section {
        background-color: #0A192F !important;
        color: #FFFFFF !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. 核心计算逻辑 ---
def calculate_summary(df_in):
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
    # 首页
    st.markdown("<h1 style='color: #4A5568; text-align: center;'>🚀 DSP 智能分析中心</h1>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("请上传广告报表", type=['xlsx', 'csv'])
    if uploaded_file:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        df.columns = df.columns.str.strip()
        df.rename(columns={'Date': '日期', 'Advertiser Name': 'ADV Name'}, inplace=True)
        df['日期'] = pd.to_datetime(df['日期']).dt.date
        st.session_state.processed_data = df
        st.rerun()
else:
    # 看板界面
    st.markdown('<h1 class="main-title">📊 DSP 投放洞察看板</h1>', unsafe_allow_html=True)
    raw_df = st.session_state.processed_data

    # 筛选区
    with st.container():
        st.markdown("<div style='background-color:#E1EFFE; padding:15px; border-radius:10px; margin-bottom:20px; border:1px solid #BEE3F8;'>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([3, 3, 1])
        with c1:
            sel_adv = st.multiselect("筛选 ADV Name", sorted(raw_df['ADV Name'].unique()), default=raw_df['ADV Name'].unique())
        with c2:
            dr = st.date_input("日期范围", [raw_df['日期'].min(), raw_df['日期'].max()])
        with c3:
            st.write("")
            if st.button("🔄 重新上传"):
                st.session_state.processed_data = None
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    if len(dr) == 2:
        sdf = raw_df[(raw_df['ADV Name'].isin(sel_adv)) & (raw_df['日期'] >= dr[0]) & (raw_df['日期'] <= dr[1])]
        
        if not sdf.empty:
            summary = sdf.groupby(['ADV Name', '日期']).sum(numeric_only=True).reset_index()
            summary = calculate_summary(summary)

            # 导出按钮
            csv_data = summary.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 导出 19 列汇总表格 (CSV)", data=csv_data, file_name="DSP_Summary.csv", mime='text/csv')

            # 表格展示（强制浅色）
            st.subheader("📋 指标明细")
            final_order = [
                'ADV Name', '日期', 'Total Cost', 'Total ROAS', 'CPM', 'CPC', 'Total CPDPV', 
                'Impressions', 'Clicks', 'Total Detail Page View', 'Total Add To Cart', 
                'Total Purchases', 'Total Units Sold', 'CTR', 'Total DPVR', 'Total ATCR', 
                'Total NTB Rate', 'Total New To Brand Purchases', 'Total Sales'
            ]
            
            st.dataframe(
                summary[final_order].sort_values(['日期', 'ADV Name'], ascending=[False, True]),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "CTR": st.column_config.NumberColumn(format="%.2f%%"), 
                    "Total DPVR": st.column_config.NumberColumn(format="%.2f%%"),
                    "Total ATCR": st.column_config.NumberColumn(format="%.2f%%"),
                    "Total NTB Rate": st.column_config.NumberColumn(format="%.2f%%"),
                    "Total Cost": st.column_config.NumberColumn(format="%.2f"),
                    "Total ROAS": st.column_config.NumberColumn(format="%.2f"),
                    "CPM": st.column_config.NumberColumn(format="%.2f"),
                    "CPC": st.column_config.NumberColumn(format="%.2f"),
                    "Total Sales": st.column_config.NumberColumn(format="%.2f")
                }
            )
