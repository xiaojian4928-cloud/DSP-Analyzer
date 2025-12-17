import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- 1. 页面配置与视觉样式 (视觉增强版) ---
st.set_page_config(page_title="DSP 高级分析看板", layout="wide")

st.markdown("""
    <style>
    /* 整体背景：纯白 */
    .stApp {
        background-color: #FFFFFF;
        color: #000000;
    }
    
    /* 1. 首页上传界面样式：淡蓝色科技背景 */
    .upload-container {
        background-image: linear-gradient(rgba(255, 255, 255, 0.4), rgba(255, 255, 255, 0.4)), 
                          url('https://img.freepik.com/free-vector/abstract-blue-geometric-shapes-background_1035-17545.jpg');
        background-size: cover;
        background-position: center;
        padding: 80px 20px;
        border-radius: 15px;
        text-align: center;
        border: 1px solid #E0E0E0;
    }
    
    .upload-text-box {
        background-color: rgba(255, 255, 255, 0.7);
        padding: 20px;
        border-radius: 10px;
        display: inline-block;
    }

    /* 2. 顶部横栏：浅灰蓝色 */
    .top-bar {
        background-color: #F0F4F8;
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 25px;
        border: 1px solid #D1D9E6;
    }

    /* 3. 图表容器：淡蓝色底色 */
    .chart-container {
        background-color: #F4F9FF;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #E1E8F0;
        margin-top: 20px;
    }

    /* 4. 隐藏原侧边栏 */
    [data-testid="stSidebar"] {
        display: none;
    }

    /* 文字颜色修正 */
    h1, h2, h3, p, span, label {
        color: #1A1A1A !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 数据处理函数 ---
def load_and_clean_data(file):
    if file.name.endswith('.csv'):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)
    
    df.columns = df.columns.str.strip()
    
    # 字段名修正映射
    mapping = {
        'Date': '日期',
        'Advertiser Name': 'ADV Name',
        'Total Detail Page View': 'Total Detail Page View',
        'Total Add To Cart': 'Total Add To Cart',
        'Total Purchases': 'Total Purchases',
        'Total New To Brand Purchases': 'Total New To Brand Purchases',
        'Total Sales': 'Total Sales',
        'Total Cost': 'Total Cost',
        'Impressions': 'Impressions'
    }
    df.rename(columns=mapping, inplace=True)
    df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
    
    num_cols = [
        'Total Cost', 'Total Sales', 'Impressions', 'Clicks', 
        'Total Detail Page View', 'Total Add To Cart', 'Total Purchases', 
        'Total Units Sold', 'Total New To Brand Purchases'
    ]
    for col in num_cols:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    return df

# --- 3. 逻辑控制 ---
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False

if not st.session_state.data_loaded:
    # --- 首页：浅蓝色科技背景 + 黑色文字 ---
    st.markdown('''
        <div class="upload-container">
            <div class="upload-text-box">
                <h1 style="margin:0; font-size:36px;">🛰️ DSP 数据分析系统</h1>
                <p style="margin:10px 0 0 0; font-size:18px; color:#333;">智能报表解析 · 多维指标看板</p>
            </div>
        </div>
    ''', unsafe_allow_html=True)
    
    st.write("---")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        uploaded_file = st.file_uploader("📂 请选择您的 DSP 报表文件 (Excel/CSV)", type=['xlsx', 'csv'])
        if uploaded_file:
            st.session_state.df = load_and_clean_data(uploaded_file)
            st.session_state.data_loaded = True
            st.rerun()
else:
    # --- 看板界面：纯白底 + 顶部横栏 ---
    df = st.session_state.df
    st.markdown('<h1 style="padding-bottom:10px;">📊 DSP 投放洞察看板</h1>', unsafe_allow_html=True)

    # 顶部横栏
    with st.container():
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

    # 筛选逻辑
    if len(date_range) == 2:
        mask = (df['ADV Name'].isin(selected_advs)) & (df['日期'].dt.date >= date_range[0]) & (df['日期'].dt.date <= date_range[1])
        sdf = df.loc[mask]
    else:
        sdf = df[df['ADV Name'].isin(selected_advs)]

    # 聚合计算
    summary = sdf.groupby(['ADV Name', '日期']).agg({
        'Total Cost': 'sum', 'Total Sales': 'sum', 'Impressions': 'sum', 'Clicks': 'sum',
        'Total Detail Page View': 'sum', 'Total Add To Cart': 'sum', 'Total Purchases': 'sum',
        'Total Units Sold': 'sum', 'Total New To Brand Purchases': 'sum'
    }).reset_index()

    # 衍生指标
    summary['Total ROAS'] = (summary['Total Sales'] / summary['Total Cost']).fillna(0)
    summary['CPM'] = (summary['Total Cost'] / (summary['Impressions'] / 1000)).fillna(0)
    summary['CPC'] = (summary['Total Cost'] / summary['Clicks']).fillna(0)
    summary['CTR'] = (summary['Clicks'] / summary['Impressions']).fillna(0)
    summary['Total NTB Rate'] = (summary['Total New To Brand Purchases'] / summary['Total Purchases']).fillna(0)
    summary['Total DPVR'] = (summary['Total Detail Page View'] / summary['Impressions']).fillna(0)
    summary['Total ATCR'] = (summary['Total Add To Cart'] / summary['Impressions']).fillna(0)

    # --- 4. 五个核心卡片 (白色卡片样式) ---
    t1, t2, t3, t4, t5 = st.columns(5)
    tc, ts, ti, tp, tnb = summary['Total Cost'].sum(), summary['Total Sales'].sum(), summary['Impressions'].sum(), summary['Total Purchases'].sum(), summary['Total New To Brand Purchases'].sum()
    
    t1.metric("Total Cost", f"{tc:,.2f}")
    t2.metric("Total Sales", f"{ts:,.2f}")
    t3.metric("Total eCPM", f"{(tc/(ti/1000) if ti>0 else 0):.2f}")
    t4.metric("Total ROAS", f"{(ts/tc if tc>0 else 0):.2f}")
    t5.metric("Total NTBR", f"{(tnb/tp if tp>0 else 0):.2%}")

    # --- 5. 统计明细表 ---
    st.write("---")
    st.subheader("📋 统计明细明细表")
    order = ['ADV Name', '日期', 'Total Cost', 'Total ROAS', 'CPM', 'CPC', 'Impressions', 'Clicks', 'Total Detail Page View', 'Total Add To Cart', 'Total Purchases', 'Total Units Sold', 'CTR', 'Total DPVR', 'Total ATCR', 'Total NTB Rate', 'Total New To Brand Purchases', 'Total Sales']
    summary_display = summary[[c for c in order if c in summary.columns]].sort_values(['ADV Name', '日期'])
    
    st.dataframe(summary_display.style.format({
        '日期': lambda x: x.strftime('%Y-%m-%d'),
        'Total Cost': '{:.2f}', 'Total Sales': '{:.2f}', 'Total ROAS': '{:.2f}',
        'CPM': '{:.2f}', 'CPC': '{:.2f}', 'CTR': '{:.2%}', 'Total DPVR': '{:.2%}', 'Total NTB Rate': '{:.2%}'
    }), use_container_width=True)

    # --- 6. 趋势对比图 (浅蓝色底色背景) ---
    st.write("---")
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.subheader("📈 趋势对比分析")
    
    c_col1, c_col2 = st.columns(2)
    m_bar = c_col1.selectbox("柱状图 (左轴)", ['Total Cost', 'Impressions', 'Total Sales', 'Total Purchases'])
    m_line = c_col2.selectbox("折线图 (右轴)", ['Total ROAS', 'Total NTB Rate', 'CTR', 'CPM'])

    chart_df = summary_display.groupby('日期').agg({m_bar: 'sum', m_line: 'mean'}).reset_index()
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=chart_df['日期'], y=chart_df[m_bar], name=m_bar, marker_color='#1f77b4'), secondary_y=False)
    fig.add_trace(go.Scatter(x=chart_df['日期'], y=chart_df[m_line], name=m_line, line=dict(color='#ff7f0e', width=3)), secondary_y=True)
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)',
        hovermode="x unified",
        margin=dict(l=20, r=20, t=50, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
