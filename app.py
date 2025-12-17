import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- 1. 页面配置与视觉样式 (极致清晰白底版) ---
st.set_page_config(page_title="DSP 投放洞察看板", layout="wide")

st.markdown("""
    <style>
    /* 1. 整体背景：纯白 & 全局字体：深蓝色 */
    .stApp {
        background-color: #FFFFFF !important;
    }
    
    /* 强制所有标题和标签为深海军蓝，增强阅读对比度 */
    h1, h2, h3, .stMetric label, .stMarkdown p, label {
        color: #0A192F !important;
        font-weight: 700 !important;
    }

    /* 2. 首页上传界面样式 */
    .upload-container {
        background-color: #F0F7FF;
        background-image: linear-gradient(rgba(255, 255, 255, 0.5), rgba(255, 255, 255, 0.5)), 
                          url('https://img.freepik.com/free-vector/abstract-blue-geometric-shapes-background_1035-17545.jpg');
        background-size: cover;
        padding: 50px;
        border-radius: 20px;
        text-align: center;
        border: 2px solid #D1E3FF;
    }

    /* 定制上传框：深蓝色底，白色字 */
    [data-testid="stFileUploader"] section {
        background-color: #0A192F !important;
        border: 2px dashed #3B82F6 !important;
    }
    [data-testid="stFileUploader"] section div, 
    [data-testid="stFileUploader"] section span {
        color: #FFFFFF !important;
    }

    /* 3. 看板明细表格自定义：浅蓝色底，深灰色字 */
    .stDataFrame div[data-testid="stTable"] {
        background-color: #EBF5FF !important; /* 表格浅蓝底 */
    }
    
    /* 强制调整表格内文字颜色为深灰色 */
    [data-testid="stTable"] td, [data-testid="stTable"] th {
        color: #333333 !important;
    }

    /* 4. 顶部横栏：带阴影的浅蓝灰 */
    .top-bar {
        background-color: #F8FAFC;
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 30px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }

    /* 5. 指标卡片数值颜色 */
    div[data-testid="stMetricValue"] {
        color: #003366 !important;
        font-weight: 800 !important;
    }

    [data-testid="stSidebar"] { display: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 数据处理逻辑 ---
def load_and_clean_data(file):
    if file.name.endswith('.csv'):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)
    
    df.columns = df.columns.str.strip()
    
    # 核心字段映射
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
    
    num_cols = ['Total Cost', 'Total Sales', 'Impressions', 'Clicks', 
                'Total Detail Page View', 'Total Add To Cart', 'Total Purchases', 
                'Total Units Sold', 'Total New To Brand Purchases']
    for col in num_cols:
        if col not in df.columns: df[col] = 0
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    return df

# --- 3. 逻辑控制 ---
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False

if not st.session_state.data_loaded:
    # 首页
    st.markdown('<div class="upload-container"><h1>🛰️ DSP 数据洞察大脑</h1><p style="color:#0A192F;">请在下方深蓝色区域上传报表文件</p></div>', unsafe_allow_html=True)
    st.write("")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        uploaded_file = st.file_uploader("", type=['xlsx', 'csv'])
        if uploaded_file:
            st.session_state.df = load_and_clean_data(uploaded_file)
            st.session_state.data_loaded = True
            st.rerun()
else:
    # 看板界面
    df = st.session_state.df
    st.markdown('<h1 style="color:#0A192F; font-size:32px;">📊 DSP 投放深度看板</h1>', unsafe_allow_html=True)

    # 顶部筛选横栏
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

    # 筛选与计算
    if len(date_range) == 2:
        sdf = df.loc[(df['ADV Name'].isin(selected_advs)) & (df['日期'].dt.date >= date_range[0]) & (df['日期'].dt.date <= date_range[1])]
    else:
        sdf = df[df['ADV Name'].isin(selected_advs)]

    summary = sdf.groupby(['ADV Name', '日期']).agg({
        'Total Cost': 'sum', 'Total Sales': 'sum', 'Impressions': 'sum', 'Clicks': 'sum',
        'Total Detail Page View': 'sum', 'Total Add To Cart': 'sum', 'Total Purchases': 'sum',
        'Total Units Sold': 'sum', 'Total New To Brand Purchases': 'sum'
    }).reset_index()

    # 指标计算
    summary['Total ROAS'] = (summary['Total Sales'] / summary['Total Cost']).fillna(0)
    summary['CPM'] = (summary['Total Cost'] / (summary['Impressions'] / 1000)).fillna(0)
    summary['CPC'] = (summary['Total Cost'] / summary['Clicks']).fillna(0)
    summary['CTR'] = (summary['Clicks'] / summary['Impressions']).fillna(0)
    summary['Total NTB Rate'] = (summary['Total New To Brand Purchases'] / summary['Total Purchases']).fillna(0)

    # --- 4. 核心指标卡片 (深蓝色字体) ---
    t1, t2, t3, t4, t5 = st.columns(5)
    tc, ts, ti, tp, tnb = summary['Total Cost'].sum(), summary['Total Sales'].sum(), summary['Impressions'].sum(), summary['Total Purchases'].sum(), summary['Total New To Brand Purchases'].sum()
    t1.metric("Total Cost", f"{tc:,.2f}")
    t2.metric("Total Sales", f"{ts:,.2f}")
    t3.metric("Total eCPM", f"{(tc/(ti/1000) if ti>0 else 0):.2f}")
    t4.metric("Total ROAS", f"{(ts/tc if tc>0 else 0):.2f}")
    t5.metric("Total NTBR", f"{(tnb/tp if tp>0 else 0):.2%}")

    # --- 5. 统计明细表格 (浅蓝底+深灰字) ---
    st.write("---")
    st.subheader("📋 数据统计明细表")
    order = ['ADV Name', '日期', 'Total Cost', 'Total ROAS', 'CPM', 'CPC', 'Impressions', 'Clicks', 'Total Detail Page View', 'Total Add To Cart', 'Total Purchases', 'Total Units Sold', 'CTR', 'Total NTB Rate', 'Total New To Brand Purchases', 'Total Sales']
    summary_display = summary[[c for c in order if c in summary.columns]].sort_values(['ADV Name', '日期'])
    
    # 使用 Pandas Style 注入浅蓝色背景
    st.dataframe(
        summary_display.style.set_properties(**{
            'background-color': '#EBF5FF', 
            'color': '#333333',
            'border-color': '#D1E3FF'
        }).format({
            '日期': lambda x: x.strftime('%Y-%m-%d'),
            'Total Cost': '{:.2f}', 'Total Sales': '{:.2f}', 'Total ROAS': '{:.2f}',
            'CPM': '{:.2f}', 'CPC': '{:.2f}', 'CTR': '{:.2%}', 'Total NTB Rate': '{:.2%}'
        }), 
        use_container_width=True
    )

    # --- 6. 趋势对比分析 ---
    st.write("---")
    st.subheader("📈 趋势对比分析")
    c_col1, c_col2 = st.columns(2)
    m_bar = c_col1.selectbox("柱状图 (左轴)", ['Total Cost', 'Impressions', 'Total Sales', 'Total Purchases'])
    m_line = c_col2.selectbox("折线图 (右轴)", ['Total ROAS', 'Total NTB Rate', 'CTR', 'CPM'])
    
    chart_df = summary_display.groupby('日期').agg({m_bar: 'sum', m_line: 'mean'}).reset_index()
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=chart_df['日期'], y=chart_df[m_bar], name=m_bar, marker_color='#004A99'), secondary_y=False)
    fig.add_trace(go.Scatter(x=chart_df['日期'], y=chart_df[m_line], name=m_line, line=dict(color='#E67E22', width=3)), secondary_y=True)
    fig.update_layout(
        paper_bgcolor='white', plot_bgcolor='rgba(240,247,255,0.5)',
        hovermode="x unified", margin=dict(l=20, r=20, t=30, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)
