import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- 1. 基础配置 ---
st.set_page_config(page_title="DSP 投放洞察看板", layout="wide")

# 强制注入大标题深蓝色
st.markdown("""
    <style>
    .blue-title { color: #003366 !important; font-weight: bold; font-size: 32px; }
    /* 首页背景与上传框 */
    .upload-section { background-color: #F0F4F8; padding: 30px; border-radius: 15px; border: 1px solid #D1E3FF; }
    [data-testid="stFileUploader"] section { background-color: #0A192F !important; color: white !important; }
    /* 进度条深蓝色 */
    .stProgress > div > div > div > div { background-color: #003366 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. 核心计算逻辑 ---
def get_metrics(df_in):
    d = df_in.copy()
    def safe_div(a, b): return (a / b).replace([float('inf'), -float('inf')], 0).fillna(0)
    
    # 基础列名确保（防止列名缺失导致报错）
    cols = ['Total Sales', 'Total Cost', 'Impressions', 'Clicks', 'Total Detail Page View', 'Total Add To Cart', 'Total Purchases', 'Total New To Brand Purchases']
    for c in cols:
        if c not in d.columns: d[c] = 0

    d['Total ROAS'] = safe_div(d['Total Sales'], d['Total Cost'])
    d['CPM'] = safe_div(d['Total Cost'], d['Impressions'] / 1000)
    d['CPC'] = safe_div(d['Total Cost'], d['Clicks'])
    d['Total CPDPV'] = safe_div(d['Total Cost'], d['Total Detail Page View'])
    d['CTR'] = safe_div(d['Clicks'], d['Impressions'])
    d['Total DPVR'] = safe_div(d['Total Detail Page View'], d['Impressions'])
    d['Total ATCR'] = safe_div(d['Total Add To Cart'], d['Impressions'])
    d['Total NTB Rate'] = safe_div(d['Total New To Brand Purchases'], d['Total Purchases'])
    return d

# --- 3. 业务流程 ---
if 'df_raw' not in st.session_state:
    st.session_state.df_raw = None

if st.session_state.df_raw is None:
    st.markdown('<div class="upload-section"><h1 style="color:#4A5568">🚀 DSP 投放中心</h1><p>请上传报表开始分析</p></div>', unsafe_allow_html=True)
    f = st.file_uploader("", type=['xlsx', 'csv'])
    if f:
        df = pd.read_csv(f) if f.name.endswith('.csv') else pd.read_excel(f)
        df.columns = df.columns.str.strip()
        # 映射
        m = {'Date': '日期', 'Advertiser Name': 'ADV Name'}
        df.rename(columns=m, inplace=True)
        df['日期'] = pd.to_datetime(df['日期']).dt.date
        st.session_state.df_raw = df
        st.rerun()
else:
    # A. 标题
    st.markdown('<p class="blue-title">📊 DSP 投放洞察看板</p>', unsafe_allow_html=True)
    raw = st.session_state.df_raw

    # B. 筛选
    st.markdown('<div style="background-color:#E1EFFE; padding:15px; border-radius:10px; margin-bottom:20px;">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([3,3,1])
    with c1:
        advs = st.multiselect("广告主筛选", sorted(raw['ADV Name'].unique()), default=raw['ADV Name'].unique())
    with c2:
        dates = st.date_input("统计时间段", [raw['日期'].min(), raw['日期'].max()])
    with c3:
        if st.button("重新上传"):
            st.session_state.df_raw = None
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # C. 数据处理
    if len(dates) == 2:
        mask = (raw['ADV Name'].isin(advs)) & (raw['日期'] >= dates[0]) & (raw['日期'] <= dates[1])
        sdf = raw[mask].copy()
        
        if not sdf.empty:
            # 聚合
            summary = sdf.groupby(['ADV Name', '日期']).sum(numeric_only=True).reset_index()
            summary = get_metrics(summary)

            # D. 明细表格 (严格19列顺序)
            st.subheader("📋 数据统计明细表")
            order = ['ADV Name', '日期', 'Total Cost', 'Total ROAS', 'CPM', 'CPC', 'Total CPDPV', 'Impressions', 'Clicks', 'Total Detail Page View', 'Total Add To Cart', 'Total Purchases', 'Total Units Sold', 'CTR', 'Total DPVR', 'Total ATCR', 'Total NTB Rate', 'Total New To Brand Purchases', 'Total Sales']
            
            st.dataframe(
                summary[order],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "日期": st.column_config.DateColumn(format="YYYY-MM-DD"),
                    "Total Cost": st.column_config.NumberColumn(format="%.2f"),
                    "Total Sales": st.column_config.NumberColumn(format="%.2f"),
                    "Total ROAS": st.column_config.NumberColumn(format="%.2f"),
                    "CTR": st.column_config.NumberColumn(format="%.2%"),
                    "Total DPVR": st.column_config.NumberColumn(format="%.2%"),
                    "Total ATCR": st.column_config.NumberColumn(format="%.2%"),
                    "Total NTB Rate": st.column_config.NumberColumn(format="%.2%"),
                }
            )

            # E. 趋势图
            st.write("---")
            st.subheader("📈 趋势对比分析")
            c_base = summary.groupby('日期').sum(numeric_only=True).reset_index()
            c_data = get_metrics(c_base)

            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_trace(go.Bar(x=c_data['日期'], y=c_data['Total Cost'], name="花费", marker_color='#4299E1'), secondary_y=False)
            fig.add_trace(go.Scatter(x=c_data['日期'], y=c_data['Total ROAS'], name="ROAS", line=dict(color='#ED8936', width=3)), secondary_y=True)
            
            fig.update_layout(hovermode="x unified", height=400, plot_bgcolor='white', margin=dict(l=0,r=0,t=20,b=0))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("所选范围内无数据")
