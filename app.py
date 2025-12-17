import streamlit as st
import pandas as pd

# --- 1. 页面配置与视觉优化 ---
st.set_page_config(page_title="DSP 数据看板", layout="wide")

st.markdown("""
    <style>
    /* 全局浅色背景 */
    .stApp { background-color: #F8FAFC; }
    /* 大标题深蓝色 */
    .main-title { color: #003366 !important; font-size: 2.2rem; font-weight: 800; margin-bottom: 20px; }
    /* 首页上传框 */
    [data-testid="stFileUploader"] section { background-color: #0A192F !important; color: white !important; border: 2px dashed #3182CE !important; }
    /* 进度条 */
    .stProgress > div > div > div > div { background-color: #003366 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. 核心计算函数 ---
def calculate_all_metrics(df_in):
    d = df_in.copy()
    def safe_div(a, b): return (a / b).replace([float('inf'), -float('inf')], 0).fillna(0)
    
    # 自动计算各项比例指标
    d['Total ROAS'] = safe_div(d['Total Sales'], d['Total Cost'])
    d['CPM'] = safe_div(d['Total Cost'], d['Impressions'] / 1000)
    d['CPC'] = safe_div(d['Total Cost'], d['Clicks'])
    d['Total CPDPV'] = safe_div(d['Total Cost'], d['Total Detail Page View'])
    d['CTR'] = safe_div(d['Clicks'], d['Impressions'])
    d['Total DPVR'] = safe_div(d['Total Detail Page View'], d['Impressions'])
    d['Total ATCR'] = safe_div(d['Total Add To Cart'], d['Impressions'])
    d['Total NTB Rate'] = safe_div(d['Total New To Brand Purchases'], d['Total Purchases'])
    return d

# --- 3. 逻辑控制 ---
if 'data' not in st.session_state:
    st.session_state.data = None

if st.session_state.data is None:
    # --- 首页：科技感上传界面 ---
    st.markdown("<h1 style='color: #4A5568;'>🚀 DSP 数据分析中心</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #718096;'>请上传广告报表，系统将为您自动汇总 19 项核心指标。</p>", unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("", type=['xlsx', 'csv'])
    if uploaded_file:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        df.columns = df.columns.str.strip()
        # 标准化日期和名称
        df.rename(columns={'Date': '日期', 'Advertiser Name': 'ADV Name'}, inplace=True)
        df['日期'] = pd.to_datetime(df['日期']).dt.date
        
        # 初始化必备数值列，缺失则补0
        required_nums = ['Total Cost', 'Total Sales', 'Impressions', 'Clicks', 'Total Detail Page View', 'Total Add To Cart', 'Total Purchases', 'Total Units Sold', 'Total New To Brand Purchases']
        for col in required_nums:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            else:
                df[col] = 0
        st.session_state.data = df
        st.rerun()

else:
    # --- 看板界面 ---
    st.markdown('<h1 class="main-title">📊 DSP 投放洞察看板</h1>', unsafe_allow_html=True)
    
    df = st.session_state.data

    # 筛选区
    with st.container():
        st.markdown("<div style='background-color:#E1EFFE; padding:15px; border-radius:10px; margin-bottom:20px;'>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([3, 3, 1])
        with c1:
            sel_adv = st.multiselect("筛选广告主", sorted(df['ADV Name'].unique()), default=df['ADV Name'].unique())
        with c2:
            date_range = st.date_input("统计时间段", [df['日期'].min(), df['日期'].max()])
        with c3:
            st.write("")
            if st.button("🔄 重新上传"):
                st.session_state.data = None
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # 数据处理
    if len(date_range) == 2:
        sdf = df[(df['ADV Name'].isin(sel_adv)) & (df['日期'] >= date_range[0]) & (df['日期'] <= date_range[1])]
        
        if not sdf.empty:
            # 汇总数据
            summary = sdf.groupby(['ADV Name', '日期']).sum(numeric_only=True).reset_index()
            summary = calculate_all_metrics(summary)

            # 导出功能
            csv = summary.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 导出汇总表格 (CSV)",
                data=csv,
                file_name=f"DSP_Summary_{date_range[0]}_{date_range[1]}.csv",
                mime='text/csv',
            )

            # 数据明细表
            st.subheader("📋 19项核心数据统计明细")
            # 严格按照您要求的 19 列顺序
            final_order = [
                'ADV Name', '日期', 'Total Cost', 'Total ROAS', 'CPM', 'CPC', 'Total CPDPV', 
                'Impressions', 'Clicks', 'Total Detail Page View', 'Total Add To Cart', 
                'Total Purchases', 'Total Units Sold', 'CTR', 'Total DPVR', 'Total ATCR', 
                'Total NTB Rate', 'Total New To Brand Purchases', 'Total Sales'
            ]
            
            st.dataframe(
                summary[final_order].sort_values(['日期', 'ADV Name']),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "日期": st.column_config.DateColumn(format="YYYY-MM-DD"),
                    "Total Cost": st.column_config.NumberColumn(format="%.2f"),
                    "Total ROAS": st.column_config.NumberColumn(format="%.2f"),
                    "CTR": st.column_config.NumberColumn(format="%.2%"),
                    "Total DPVR": st.column_config.NumberColumn(format="%.2%"),
                    "Total ATCR": st.column_config.NumberColumn(format="%.2%"),
                    "Total NTB Rate": st.column_config.NumberColumn(format="%.2%"),
                    "Total Sales": st.column_config.NumberColumn(format="%.2f"),
                    "CPM": st.column_config.NumberColumn(format="%.2f"),
                    "CPC": st.column_config.NumberColumn(format="%.2f"),
                }
            )
        else:
            st.warning("⚠️ 当前选择范围内无数据。")
