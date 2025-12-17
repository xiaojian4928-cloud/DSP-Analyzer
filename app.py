import streamlit as st
import pandas as pd

# --- 1. 深度视觉定制：锁定深蓝标题与浅色底色 ---
st.set_page_config(page_title="DSP 数据看板", layout="wide")

st.markdown("""
    <style>
    /* 强制背景与主题颜色，解决黑色底色问题 */
    :root {
        --secondary-background-color: #F0F4F8 !important; 
        --background-color: #FFFFFF !important;           
        --text-color: #2D3748 !important;                
    }
    .stApp { background-color: #F8FAFC !important; }
    
    /* 大标题样式：深蓝色 */
    .main-title { color: #003366 !important; font-weight: 800; text-align: center; margin-bottom: 25px; }

    /* 强制抹除表格黑色背景 */
    [data-testid="stDataFrame"], [data-testid="stDataFrameGrid"], div[role="grid"] {
        background-color: #FFFFFF !important;
    }

    /* 核心指标卡片样式 */
    .metric-card {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #E2E8F0;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }

    /* 筛选框样式 */
    div[data-baseweb="select"] > div, div[data-baseweb="base-input"] > div, input {
        background-color: #E1EFFE !important;
        color: #2D3748 !important;
        border: 1px solid #BEE3F8 !important;
    }

    /* 首页上传框样式 */
    [data-testid="stFileUploader"] section { background-color: #0A192F !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. 核心计算逻辑 ---
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

    # --- 筛选区 ---
    with st.container():
        st.markdown("<div style='background-color:#E1EFFE; padding:15px; border-radius:10px; margin-bottom:20px; border:1px solid #BEE3F8;'>", unsafe_allow_html=True)
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
        sdf = raw_df[(raw_df['ADV Name'].isin(sel_adv)) & (raw_df['日期'] >= dr[0]) & (raw_df['日期'] <= dr[1])]
        
        if not sdf.empty:
            # 基础汇总
            total_cost = sdf['Total Cost'].sum()
            total_sales = sdf['Total Sales'].sum()
            total_imps = sdf['Impressions'].sum()
            total_pur = sdf['Total Purchases'].sum()
            total_ntb_pur = sdf['Total New To Brand Purchases'].sum()
            
            # 计算汇总指标
            agg_roas = total_sales / total_cost if total_cost > 0 else 0
            agg_ecpm = (total_cost / total_imps * 1000) if total_imps > 0 else 0
            agg_ntb_rate = (total_ntb_pur / total_pur) if total_pur > 0 else 0

            # --- 4. 顶部核心指标大标题显示 ---
            st.subheader("📌 核心指标概览")
            k1, k2, k3, k4, k5 = st.columns(5)
            k1.metric("Total Cost", f"${total_cost:,.2f}")
            k2.metric("Total Sales", f"${total_sales:,.2f}")
            k3.metric("ECPM", f"${agg_ecpm:,.2f}")
            k4.metric("Total ROAS", f"{agg_roas:.2f}")
            k5.metric("Total NTB Rate", f"{agg_ntb_rate:.2%}")
            
            st.write("---")

            # --- 5. 数据表格展示 ---
            summary = sdf.groupby(['ADV Name', '日期']).sum(numeric_only=True).reset_index()
            summary = calculate_metrics(summary)

            csv_data = summary.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 导出 19 列汇总明细 (CSV)", data=csv_data, file_name="DSP_Summary.csv", mime='text/csv')

            st.subheader("📋 指标明细统计")
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
                    "Total Sales": st.column_config.NumberColumn(format="%.2f"),
                    "CPM": st.column_config.NumberColumn(format="%.2f"),
                    "CPC": st.column_config.NumberColumn(format="%.2f"),
                }
            )
        else:
            st.warning("⚠️ 所选范围内无有效数据。")
