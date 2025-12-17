import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- 1. 页面基本配置 ---
st.set_page_config(page_title="DSP 看板", layout="wide")

# 仅保留最核心的首页样式，不干扰看板界面
st.markdown("""
    <style>
    /* 首页上传框样式 */
    .stApp { background-color: #F8FAFC; }
    [data-testid="stFileUploader"] section { background-color: #0A192F !important; color: white !important; }
    .stProgress > div > div > div > div { background-color: #003366 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. 核心计算函数 (确保数据不报错) ---
def process_data(df_in):
    d = df_in.copy()
    def div(a, b): return (a / b).replace([float('inf'), -float('inf')], 0).fillna(0)
    
    # 比例指标计算
    d['Total ROAS'] = div(d['Total Sales'], d['Total Cost'])
    d['CPM'] = div(d['Total Cost'], d['Impressions'] / 1000)
    d['CPC'] = div(d['Total Cost'], d['Clicks'])
    d['Total CPDPV'] = div(d['Total Cost'], d['Total Detail Page View'])
    d['CTR'] = div(d['Clicks'], d['Impressions'])
    d['Total DPVR'] = div(d['Total Detail Page View'], d['Impressions'])
    d['Total ATCR'] = div(d['Total Add To Cart'], d['Impressions'])
    d['Total NTB Rate'] = div(d['Total New To Brand Purchases'], d['Total Purchases'])
    return d

# --- 3. 逻辑控制 ---
if 'data' not in st.session_state:
    st.session_state.data = None

if st.session_state.data is None:
    # 首页：简洁科技感
    st.markdown("<h1 style='color: #4A5568;'>🚀 DSP 智能分析中心</h1>", unsafe_allow_html=True)
    st.info("💡 请上传广告报表（支持 CSV/Excel），系统将自动为您生成 19 项核心指标明细。")
    uploaded_file = st.file_uploader("", type=['xlsx', 'csv'])
    
    if uploaded_file:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        df.columns = df.columns.str.strip()
        # 列名标准化
        df.rename(columns={'Date': '日期', 'Advertiser Name': 'ADV Name'}, inplace=True)
        df['日期'] = pd.to_datetime(df['日期']).dt.date
        
        # 数值预处理
        num_cols = ['Total Cost', 'Total Sales', 'Impressions', 'Clicks', 'Total Detail Page View', 'Total Add To Cart', 'Total Purchases', 'Total Units Sold', 'Total New To Brand Purchases']
        for col in num_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            else:
                df[col] = 0
                
        st.session_state.data = df
        st.rerun()

else:
    # 看板界面
    # 1. 大标题：深蓝色
    st.markdown("<h1 style='color: #003366;'>📊 DSP 投放洞察看板</h1>", unsafe_allow_html=True)
    
    df = st.session_state.data

    # 2. 筛选区
    with st.container():
        st.markdown("<div style='background-color:#E1EFFE; padding:15px; border-radius:10px;'>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([3, 3, 1])
        with c1:
            sel_adv = st.multiselect("筛选广告主", sorted(df['ADV Name'].unique()), default=df['ADV Name'].unique())
        with c2:
            date_range = st.date_input("统计周期", [df['日期'].min(), df['日期'].max()])
        with c3:
            st.write("")
            if st.button("🔄 重新上传"):
                st.session_state.data = None
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # 3. 数据过滤
    if len(date_range) == 2:
        sdf = df[(df['ADV Name'].isin(sel_adv)) & (df['日期'] >= date_range[0]) & (df['日期'] <= date_range[1])]
        
        if not sdf.empty:
            # 汇总与计算
            summary = sdf.groupby(['ADV Name', '日期']).sum(numeric_only=True).reset_index()
            summary = process_data(summary)

            # 4. 数据表格
            st.subheader("📋 数据统计明细表")
            # 严格 19 列顺序
            final_order = [
                'ADV Name', '日期', 'Total Cost', 'Total ROAS', 'CPM', 'CPC', 'Total CPDPV', 
                'Impressions', 'Clicks', 'Total Detail Page View', 'Total Add To Cart', 
                'Total Purchases', 'Total Units Sold', 'CTR', 'Total DPVR', 'Total ATCR', 
                'Total NTB Rate', 'Total New To Brand Purchases', 'Total Sales'
            ]
            
            st.dataframe(
                summary[final_order],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "日期": st.column_config.DateColumn(format="YYYY-MM-DD"),
                    "Total Cost": st.column_config.NumberColumn(format="%.2f"),
                    "Total ROAS": st.column_config.NumberColumn(format="%.2f"),
                    "CTR": st.column_config.NumberColumn("CTR", format="%.2%"),
                    "Total DPVR": st.column_config.NumberColumn("Total DPVR", format="%.2%"),
                    "Total ATCR": st.column_config.NumberColumn("Total ATCR", format="%.2%"),
                    "Total NTB Rate": st.column_config.NumberColumn("Total NTB Rate", format="%.2%"),
                    "Total Sales": st.column_config.NumberColumn(format="%.2f"),
                }
            )

            # 5. 趋势图
            st.write("---")
            st.subheader("📈 投放趋势对比")
            c_base = summary.groupby('日期').sum(numeric_only=True).reset_index()
            c_plot = process_data(c_base)

            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_trace(go.Bar(x=c_plot['日期'], y=c_plot['Total Cost'], name="Cost", marker_color='#4299E1'), secondary_y=False)
            fig.add_trace(go.Scatter(x=c_plot['日期'], y=c_plot['Total ROAS'], name="ROAS", line=dict(color='#ED8936', width=3)), secondary_y=True)
            
            fig.update_layout(
                hovermode="x unified",
                plot_bgcolor='white',
                height=400,
                xaxis=dict(showgrid=False),
                yaxis=dict(title="Total Cost"),
                yaxis2=dict(title="Total ROAS", overlaying='y', side='right'),
                margin=dict(l=20, r=20, t=20, b=20)
            )
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.warning("⚠️ 当前筛选条件下暂无数据。")
