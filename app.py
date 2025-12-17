import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- 1. 页面配置与深度视觉定制 ---
st.set_page_config(page_title="DSP 投放洞察看板", layout="wide")

st.markdown("""
    <style>
    /* 全局背景 */
    .stApp { background-color: #F0F4F8 !important; }
    
    /* 1. 大标题：深蓝色 */
    .main-title {
        color: #003366 !important; 
        font-size: 2.2rem !important;
        font-weight: 800;
        text-align: center;
        margin-bottom: 20px;
    }

    /* 2. 首页科技感容器 */
    .upload-bg-container {
        background: linear-gradient(rgba(240, 244, 248, 0.85), rgba(240, 244, 248, 0.85)), 
                    url('https://www.transparenttextures.com/patterns/carbon-fibre.png');
        background-color: #E6F0FF;
        padding: 50px;
        border-radius: 15px;
        text-align: center;
        border: 1px solid #BEE3F8;
    }
    .upload-bg-container h1 { color: #4A5568 !important; }
    .upload-bg-container p { color: #718096 !important; }

    /* 3. 上传框：深蓝色底 */
    [data-testid="stFileUploader"] section {
        background-color: #0A192F !important;
        border: 2px dashed #3182CE !important;
        color: white !important;
    }

    /* 4. 数据看板表格：浅色底 (彻底去黑) */
    .stDataFrame, [data-testid="stDataFrameGrid"] {
        background-color: #FFFFFF !important;
        border-radius: 10px;
    }
    
    /* 筛选框和指标卡片样式 */
    .top-bar {
        background-color: #E1EFFE !important;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #BEE3F8;
        margin-bottom: 20px;
    }
    .stMetric { background-color: #FFFFFF; padding: 10px; border-radius: 10px; border: 1px solid #E2E8F0; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心计算逻辑 (防错加强版) ---
def calc_metrics(df_in):
    if df_in.empty: return df_in
    res = df_in.copy()
    # 安全除法函数
    def s_div(a, b): return (a / b).replace([float('inf'), -float('inf')], 0).fillna(0)
    
    res['Total ROAS'] = s_div(res['Total Sales'], res['Total Cost'])
    res['CPM'] = s_div(res['Total Cost'], res['Impressions'] / 1000)
    res['CPC'] = s_div(res['Total Cost'], res['Clicks'])
    res['CTR'] = s_div(res['Clicks'], res['Impressions'])
    res['Total DPVR'] = s_div(res['Total Detail Page View'], res['Impressions'])
    res['Total ATCR'] = s_div(res['Total Add To Cart'], res['Impressions'])
    res['Total NTB Rate'] = s_div(res['Total New To Brand Purchases'], res['Total Purchases'])
    res['Total CPDPV'] = s_div(res['Total Cost'], res['Total Detail Page View'])
    return res

def load_data(file):
    try:
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
        df['日期'] = pd.to_datetime(df['日期']).dt.date # 统一日期格式
        
        # 补齐可能缺失的列
        for col in list(map_dict.values())[2:]:
            if col not in df.columns: df[col] = 0
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"文件读取失败，请检查格式。错误详情: {e}")
        return None

# --- 3. 页面主逻辑 ---
if 'df' not in st.session_state: st.session_state.df = None

if st.session_state.df is None:
    st.markdown('<div class="upload-bg-container"><h1>🚀 DSP 智能数据中心</h1><p>上传报表以解锁多维度增长洞察</p></div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("", type=['xlsx', 'csv'])
    if uploaded_file:
        st.session_state.df = load_data(uploaded_file)
        st.rerun()
else:
    # 1. 标题
    st.markdown('<h1 class="main-title">📊 DSP 投放洞察看板</h1>', unsafe_allow_html=True)

    # 2. 筛选区
    df = st.session_state.df
    st.markdown('<div class="top-bar">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([3, 3, 1])
    with c1:
        advs = st.multiselect("选择广告主", sorted(df['ADV Name'].unique()), default=df['ADV Name'].unique())
    with c2:
        dr = st.date_input("选择日期范围", [df['日期'].min(), df['日期'].max()])
    with c3:
        st.write("")
        if st.button("🔄 重新上传"):
            st.session_state.df = None
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # 3. 数据过滤与计算
    if len(dr) == 2:
        mask = (df['ADV Name'].isin(advs)) & (df['日期'] >= dr[0]) & (df['日期'] <= dr[1])
        sdf = df[mask]
        
        if not sdf.empty:
            summary = sdf.groupby(['ADV Name', '日期']).sum(numeric_only=True).reset_index()
            summary = calc_metrics(summary)

            # 4. KPI 快速概览
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("总花费", f"{summary['Total Cost'].sum():,.2f}")
            k2.metric("总销售", f"{summary['Total Sales'].sum():,.2f}")
            k3.metric("总 ROAS", f"{(summary['Total Sales'].sum()/summary['Total Cost'].sum()):.2f}" if summary['Total Cost'].sum()>0 else "0.00")
            k4.metric("总订单", f"{int(summary['Total Purchases'].sum())}")

            # 5. 明细表 (严格 19 列顺序)
            st.subheader("📋 数据统计明细表")
            col_order = ['ADV Name', '日期', 'Total Cost', 'Total ROAS', 'CPM', 'CPC', 'Total CPDPV', 'Impressions', 'Clicks', 'Total Detail Page View', 'Total Add To Cart', 'Total Purchases', 'Total Units Sold', 'CTR', 'Total DPVR', 'Total ATCR', 'Total NTB Rate', 'Total New To Brand Purchases', 'Total Sales']
            
            st.dataframe(
                summary[col_order],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Total Cost": st.column_config.NumberColumn(format="%.2f"),
                    "Total ROAS": st.column_config.NumberColumn(format="%.2f"),
                    "CTR": st.column_config.NumberColumn(format="%.2%"),
                    "Total DPVR": st.column_config.NumberColumn(format="%.2%"),
                    "Total ATCR": st.column_config.NumberColumn(format="%.2%"),
                    "Total NTB Rate": st.column_config.NumberColumn(format="%.2%"),
                    "Total Purchases": st.column_config.NumberColumn(format="%d"),
                }
            )

            # 6. 趋势图 (修复报错的核心逻辑)
            st.write("---")
            st.subheader("📈 趋势对比分析")
            chart_base = summary.groupby('日期').sum(numeric_only=True).reset_index()
            chart_data = calc_metrics(chart_base)

            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_trace(go.Bar(x=chart_data['日期'], y=chart_data['Total Cost'], name="花费", marker_color='#4299E1'), secondary_y=False)
            fig.add_trace(go.Scatter(x=chart_data['日期'], y=chart_data['Total ROAS'], name="ROAS", line=dict(color='#ED8936', width=3)), secondary_y=True)
            
            fig.update_layout(
                hovermode="x unified",
                plot_bgcolor='white',
                xaxis=dict(tickfont=dict(color="gray"), showgrid=False),
                yaxis=dict(title="花费", tickfont=dict(color="gray")),
                yaxis2=dict(title="ROAS", overlaying='y', side='right', tickfont=dict(color="gray")),
                height=400, margin=dict(l=0,r=0,t=20,b=0)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("当前筛选条件下无数据，请重新选择。")
