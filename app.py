import streamlit as st
import pandas as pd

# --- 1. 页面配置与基础样式 ---
st.set_page_config(page_title="DSP 数据看板", layout="wide")

st.markdown("""
    <style>
    /* 全局背景设为浅灰蓝，增加科技感 */
    .stApp { background-color: #F8FAFC !important; }
    
    /* 首页上传容器 */
    .upload-box {
        background-color: #FFFFFF;
        padding: 40px;
        border-radius: 15px;
        border: 1px solid #E2E8F0;
        text-align: center;
    }

    /* 上传框深蓝色背景 */
    [data-testid="stFileUploader"] section {
        background-color: #0A192F !important;
        color: white !important;
        border: 2px dashed #3182CE !important;
    }
    
    /* 调整上传框内按钮和文字颜色 */
    [data-testid="stFileUploader"] section div, 
    [data-testid="stFileUploader"] section span {
        color: #CBD5E0 !important;
    }

    /* 进度条深蓝色 */
    .stProgress > div > div > div > div { background-color: #003366 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. 核心计算逻辑 ---
def calculate_metrics(df_in):
    d = df_in.copy()
    # 安全除法
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
if 'main_data' not in st.session_state:
    st.session_state.main_data = None

if st.session_state.main_data is None:
    # --- 首页：科技感上传界面 ---
    st.markdown('<div class="upload-box">', unsafe_allow_html=True)
    st.markdown("<h1 style='color: #4A5568;'>🚀 DSP 智能分析中心</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #718096;'>请上传您的广告报表，系统将自动汇总并计算 19 项核心指标。</p>", unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("", type=['xlsx', 'csv'])
    if uploaded_file:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        df.columns = df.columns.str.strip()
        # 列名对齐
        df.rename(columns={'Date': '日期', 'Advertiser Name': 'ADV Name'}, inplace=True)
        df['日期'] = pd.to_datetime(df['日期']).dt.date
        
        # 初始化数值列
        num_cols = ['Total Cost', 'Total Sales', 'Impressions', 'Clicks', 'Total Detail Page View', 'Total Add To Cart', 'Total Purchases', 'Total Units Sold', 'Total New To Brand Purchases']
        for col in num_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            else:
                df[col] = 0
        st.session_state.main_data = df
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

else:
    # --- 看板界面 ---
    # 1. 大标题：深蓝色
    st.markdown("<h1 style='color: #003366; text-align: center;'>📊 DSP 投放洞察看板</h1>", unsafe_allow_html=True)
    
    df = st.session_state.main_data

    # 2. 筛选区
    with st.container():
        st.markdown("<div style='background-color:#E1EFFE; padding:20px; border-radius:12px; margin-bottom:25px; border: 1px solid #BEE3F8;'>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([3, 3, 1])
        with c1:
            sel_adv = st.multiselect("筛选广告主 (ADV Name)", sorted(df['ADV Name'].unique()), default=df['ADV Name'].unique())
        with c2:
            date_range = st.date_input("选择统计周期", [df['日期'].min(), df['日期'].max()])
        with c3:
            st.write("")
            if st.button("🔄 重新上传"):
                st.session_state.main_data = None
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # 3. 数据处理与展示
    if len(date_range) == 2:
        sdf = df[(df['ADV Name'].isin(sel_adv)) & (df['日期'] >= date_range[0]) & (df['日期'] <= date_range[1])]
        
        if not sdf.empty:
            # 执行汇总
            summary = sdf.groupby(['ADV Name', '日期']).sum(numeric_only=True).reset_index()
            summary = calculate_metrics(summary)

            # 导出按钮
            csv_data = summary.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 导出当前汇总表格 (CSV)",
                data=csv_data,
                file_name=f"DSP_Report_{date_range[0]}_{date_range[1]}.csv",
                mime='text/csv',
            )

            # 明细表格 (原生浅色背景)
            st.subheader("📋 核心指标明细统计")
            # 严格 19 列顺序
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
                    "日期": st.column_config.DateColumn(format="YYYY-MM-DD"),
                    "Total Cost": st.column_config.NumberColumn(format="%.2f"),
                    "Total ROAS": st.column_config.NumberColumn(format="%.2f"),
                    "CPM": st.column_config.NumberColumn(format="%.2f"),
                    "CPC": st.column_config.NumberColumn(format="%.2f"),
                    "Total CPDPV": st.column_config.NumberColumn(format="%.2f"),
                    "CTR": st.column_config.NumberColumn(format="%.2%"),          # 百分比显示
                    "Total DPVR": st.column_config.NumberColumn(format="%.2%"),     # 百分比显示
                    "Total ATCR": st.column_config.NumberColumn(format="%.2%"),     # 百分比显示
                    "Total NTB Rate": st.column_config.NumberColumn(format="%.2%"), # 百分比显示
                    "Total Sales": st.column_config.NumberColumn(format="%.2f"),
                }
            )
        else:
            st.warning("⚠️ 所选范围内无有效数据，请重新调整筛选条件。")
