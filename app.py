import streamlit as st
import pandas as pd
import datetime

# --- 1. 视觉定制 (深灰标题 + 浅蓝表格 + 强制去黑) ---
st.set_page_config(page_title="DSP 投放看板", layout="wide")

st.markdown("""
    <style>
    :root {
        --secondary-background-color: #EBF5FF !important; 
        --background-color: #FFFFFF !important;
        --text-color: #2D3748 !important;
    }
    .stApp { background-color: #F8FAFC !important; }
    
    /* 标题与数值：深灰色 */
    .main-title { color: #4A5568 !important; font-weight: 800; text-align: center; margin-bottom: 25px; }
    [data-testid="stMetricValue"] { color: #4A5568 !important; }
    [data-testid="stMetricLabel"] > div { color: #4A5568 !important; }

    /* 表格底色：强制浅蓝色 */
    [data-testid="stDataFrame"], [data-testid="stDataFrameGrid"], div[role="grid"] {
        background-color: #EBF5FF !important;
    }

    /* 筛选框样式 */
    div[data-baseweb="select"] > div, div[data-baseweb="base-input"] > div, input {
        background-color: #F0F7FF !important;
        color: #4A5568 !important;
        border: 1px solid #BEE3F8 !important;
    }
    
    /* 上传框样式 */
    [data-testid="stFileUploader"] section { background-color: #0A192F !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. 增强型计算逻辑 (带缺失列自动补全) ---
def safe_calc(df_in):
    d = df_in.copy()
    def div(a, b):
        return (a / b).replace([float('inf'), -float('inf')], 0).fillna(0)
    
    # 基础列名及其默认值 (确保 19 列所需的全部原始数据存在)
    base_cols = {
        'Total Cost': 0, 'Total Sales': 0, 'Impressions': 0, 'Clicks': 0, 
        'Total Detail Page View': 0, 'Total Add To Cart': 0, 'Total Purchases': 0, 
        'Total Units Sold': 0, 'Total New To Brand Purchases': 0
    }
    for col, default in base_cols.items():
        if col not in d.columns:
            d[col] = default
        d[col] = pd.to_numeric(d[col], errors='coerce').fillna(0)

    # 计算 19 列中剩下的派生指标
    d['Total ROAS'] = div(d['Total Sales'], d['Total Cost'])
    d['CPM'] = div(d['Total Cost'], d['Impressions'] / 1000)
    d['CPC'] = div(d['Total Cost'], d['Clicks'])
    d['Total CPDPV'] = div(d['Total Cost'], d['Total Detail Page View'])
    d['CTR'] = div(d['Clicks'], d['Impressions'])
    d['Total DPVR'] = div(d['Total Detail Page View'], d['Impressions'])
    d['Total ATCR'] = div(d['Total Add To Cart'], d['Impressions'])
    d['Total NTB Rate'] = div(d['Total New To Brand Purchases'], d['Total Purchases'])
    return d

# --- 3. 业务流程 ---
if 'processed_df' not in st.session_state:
    st.session_state.processed_df = None

if st.session_state.processed_df is None:
    st.markdown("<h1 class='main-title'>🚀 DSP 智能分析中心</h1>", unsafe_allow_html=True)
    f = st.file_uploader("请上传广告报表 (CSV/Excel)", type=['xlsx', 'csv'])
    if f:
        try:
            df = pd.read_csv(f) if f.name.endswith('.csv') else pd.read_excel(f)
            df.columns = df.columns.str.strip()
            df.rename(columns={'Date': '日期', 'Advertiser Name': 'ADV Name'}, inplace=True)
            # 统一日期格式
            df['日期'] = pd.to_datetime(df['日期']).dt.date
            st.session_state.processed_df = df
            st.rerun()
        except Exception as e:
            st.error(f"文件读取失败，请检查格式。错误详情: {e}")

else:
    st.markdown('<h1 class="main-title">📊 DSP 投放洞察看板</h1>', unsafe_allow_html=True)
    raw = st.session_state.processed_df

    # --- 筛选区 ---
    with st.container():
        st.markdown("<div style='background-color:#EBF5FF; padding:15px; border-radius:10px; margin-bottom:20px; border:1px solid #BEE3F8;'>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([3, 3, 1])
        with c1:
            adv_list = sorted(raw['ADV Name'].unique().tolist())
            sel_adv = st.multiselect("筛选广告主", adv_list, default=adv_list)
        with c2:
            # 确保日期范围有效
            dr = st.date_input("日期范围", [raw['日期'].min(), raw['日期'].max()])
        with c3:
            st.write("")
            if st.button("🔄 重新上传"):
                st.session_state.processed_df = None
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # --- 数据逻辑展示 ---
    if len(dr) == 2:
        mask = (raw['ADV Name'].isin(sel_adv)) & (raw['日期'] >= dr[0]) & (raw['日期'] <= dr[1])
        sdf = raw[mask].copy()
        
        if not sdf.empty:
            # 1. 核心汇总计算 (先求和再除)
            t_cost = sdf['Total Cost'].sum()
            t_sales = sdf['Total Sales'].sum()
            t_imps = sdf['Impressions'].sum()
            t_pur = sdf['Total Purchases'].sum()
            t_ntb_pur = sdf['Total New To Brand Purchases'].sum()
            
            agg_roas = t_sales / t_cost if t_cost > 0 else 0
            agg_ecpm = (t_cost / (t_imps / 1000)) if t_imps > 0 else 0
            agg_ntb_rate = (t_ntb_pur / t_pur) if t_pur > 0 else 0

            # 2. 顶部 KPI 展示
            st.markdown("<h3 style='color:#4A5568;'>📌 核心指标汇总</h3>", unsafe_allow_html=True)
            k1, k2, k3, k4, k5 = st.columns(5)
            k1.metric("Total Cost", f"${t_cost:,.2f}")
            k2.metric("Total Sales", f"${t_sales:,.2f}")
            k3.metric("ECPM", f"${agg_ecpm:,.2f}")
            k4.metric("Total ROAS", f"{agg_roas:.2f}")
            k5.metric("Total NTB Rate", f"{agg_ntb_rate:.2%}")
            
            st.write("---")

            # 3. 明细表处理
            summary = sdf.groupby(['ADV Name', '日期']).sum(numeric_only=True).reset_index()
            summary = safe_calc(summary)
            # 默认排序：ADV Name 升序，日期 升序
            summary = summary.sort_values(by=['ADV Name', '日期'], ascending=[True, True])

            final_order = [
                'ADV Name', '日期', 'Total Cost', 'Total ROAS', 'CPM', 'CPC', 'Total CPDPV', 
                'Impressions', 'Clicks', 'Total Detail Page View', 'Total Add To Cart', 
                'Total Purchases', 'Total Units Sold', 'CTR', 'Total DPVR', 'Total ATCR', 
                'Total NTB Rate', 'Total New To Brand Purchases', 'Total Sales'
            ]
            
            # 4. 导出逻辑同步 (严格 19 列 + 格式同步)
            export_df = summary[final_order].copy()
            # 格式化导出数据
            for col in ['CTR', 'Total DPVR', 'Total ATCR', 'Total NTB Rate']:
                export_df[col] = export_df[col].apply(lambda x: f"{x:.2%}")
            for col in ['Total Cost', 'Total ROAS', 'CPM', 'CPC', 'Total CPDPV', 'Total Sales']:
                export_df[col] = export_df[col].apply(lambda x: f"{x:.2f}")

            st.download_button(
                "📥 导出当前筛选明细 (与看板格式同步)", 
                data=export_df.to_csv(index=False).encode('utf-8-sig'), 
                file_name=f"DSP_Summary_{dr[0]}_to_{dr[1]}.csv", 
                mime='text/csv'
            )

            # 5. 表格展示
            st.subheader("📋 指标明细统计")
            st.dataframe(
                summary[final_order],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "CTR": st.column_config.NumberColumn(format="%.2%"), 
                    "Total DPVR": st.column_config.NumberColumn(format="%.2%"),
                    "Total ATCR": st.column_config.NumberColumn(format="%.2%"),
                    "Total NTB Rate": st.column_config.NumberColumn(format="%.2%"),
                    "Total Cost": st.column_config.NumberColumn(format="%.2f"),
                    "Total Sales": st.column_config.NumberColumn(format="%.2f"),
                }
            )
        else:
            st.warning("⚠️ 筛选范围内无数据。")
