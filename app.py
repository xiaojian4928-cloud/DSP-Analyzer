import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- 1. 页面配置与视觉样式 ---
st.set_page_config(page_title="DSP 投放洞察看板", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF !important; }
    h1, h2, h3, .stMetric label, label { color: #0A192F !important; font-weight: 700 !important; }
    
    /* 首页上传界面 */
    .upload-container {
        background-color: #F0F7FF;
        background-image: linear-gradient(rgba(255, 255, 255, 0.5), rgba(255, 255, 255, 0.5)), 
                          url('https://img.freepik.com/free-vector/abstract-blue-geometric-shapes-background_1035-17545.jpg');
        background-size: cover; padding: 50px; border-radius: 20px; text-align: center; border: 2px solid #D1E3FF;
    }
    
    /* 上传框定制 */
    [data-testid="stFileUploader"] section { background-color: #0A192F !important; border: 2px dashed #3B82F6 !important; }
    [data-testid="stFileUploader"] section div, [data-testid="stFileUploader"] section span { color: #FFFFFF !important; }
    
    /* 筛选框底色：浅蓝色 */
    .top-bar, .chart-filter-box { background-color: #EBF5FF !important; padding: 15px; border-radius: 12px; margin-bottom: 20px; border: 1px solid #C2DFFF; }
    
    /* 多选标签颜色 */
    span[data-baseweb="tag"] { background-color: #0A192F !important; color: white !important; }
    
    /* 表格样式 */
    thead tr th { background-color: #D1E9FF !important; color: #0A192F !important; }
    [data-testid="stTable"] td { background-color: #F0F8FF !important; color: #1A1A1A !important; }
    
    /* KPI 数值颜色 */
    div[data-testid="stMetricValue"] { color: #004A99 !important; font-weight: 800 !important; }
    [data-testid="stSidebar"] { display: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心计算函数 (比例指标重计算逻辑) ---
def calc_metrics(temp_df):
    """
    统一的比例指标计算公式，确保基于汇总后的数值进行除法
    """
    # 1. Total ROAS = 总销售额 / 总消耗
    temp_df['Total ROAS'] = (temp_df['Total Sales'] / temp_df['Total Cost']).replace([float('inf'), -float('inf')], 0).fillna(0)
    
    # 2. CPM = (总消耗 / 总曝光) * 1000
    temp_df['CPM'] = (temp_df['Total Cost'] / (temp_df['Impressions'] / 1000)).replace([float('inf'), -float('inf')], 0).fillna(0)
    
    # 3. CPC = 总消耗 / 总点击
    temp_df['CPC'] = (temp_df['Total Cost'] / temp_df['Clicks']).replace([float('inf'), -float('inf')], 0).fillna(0)
    
    # 4. CTR = 总点击 / 总曝光
    temp_df['CTR'] = (temp_df['Clicks'] / temp_df['Impressions']).replace([float('inf'), -float('inf')], 0).fillna(0)
    
    # 5. Total NTB Rate = 总新客单量 / 总单量
    temp_df['Total NTB Rate'] = (temp_df['Total New To Brand Purchases'] / temp_df['Total Purchases']).replace([float('inf'), -float('inf')], 0).fillna(0)
    
    # 6. DPVR & ATCR (详情页和加购率)
    if 'Total Detail Page View' in temp_df.columns:
        temp_df['Total DPVR'] = (temp_df['Total Detail Page View'] / temp_df['Impressions']).replace([float('inf'), -float('inf')], 0).fillna(0)
    if 'Total Add To Cart' in temp_df.columns:
        temp_df['Total ATCR'] = (temp_df['Total Add To Cart'] / temp_df['Impressions']).replace([float('inf'), -float('inf')], 0).fillna(0)
        
    return temp_df

def load_and_clean_data(file):
    df = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
    df.columns = df.columns.str.strip()
    mapping = {
        'Date': '日期', 'Advertiser Name': 'ADV Name',
        'Total Detail Page View': 'Total Detail Page View',
        'Total Add To Cart': 'Total Add To Cart',
        'Total Purchases': 'Total Purchases',
        'Total New To Brand Purchases': 'Total New To Brand Purchases',
        'Total Sales': 'Total Sales', 'Total Cost': 'Total Cost', 'Impressions': 'Impressions'
    }
    df.rename(columns=mapping, inplace=True)
    df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
    num_cols = ['Total Cost', 'Total Sales', 'Impressions', 'Clicks', 'Total Detail Page View', 
                'Total Add To Cart', 'Total Purchases', 'Total Units Sold', 'Total New To Brand Purchases']
    for col in num_cols:
        if col not in df.columns: df[col] = 0
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

# --- 3. 页面逻辑 ---
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False

if not st.session_state.data_loaded:
    # 首页上传界面
    st.markdown('<div class="upload-container"><h1>🛰️ DSP 数据洞察大脑</h1><p style="color:#0A192F;">数据驱动增长 · 智能解析报表</p></div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("", type=['xlsx', 'csv'])
    if uploaded_file:
        st.session_state.df = load_and_clean_data(uploaded_file)
        st.session_state.data_loaded = True
        st.rerun()
else:
    df = st.session_state.df
    st.markdown('<h1 style="color:#0A192F;">📊 DSP 投放深度看板</h1>', unsafe_allow_html=True)

    # 顶部筛选框 (浅蓝色)
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

    # 数据过滤
    if len(date_range) == 2:
        sdf = df.loc[(df['ADV Name'].isin(selected_advs)) & (df['日期'].dt.date >= date_range[0]) & (df['日期'].dt.date <= date_range[1])]
    else:
        sdf = df[df['ADV Name'].isin(selected_advs)]

    # --- 聚合逻辑 ---
    # 先聚合求和基础值
    summary = sdf.groupby(['ADV Name', '日期']).agg({
        'Total Cost': 'sum', 'Total Sales': 'sum', 'Impressions': 'sum', 'Clicks': 'sum',
        'Total Detail Page View': 'sum', 'Total Add To Cart': 'sum', 'Total Purchases': 'sum',
        'Total Units Sold': 'sum', 'Total New To Brand Purchases': 'sum'
    }).reset_index()

    # 再重新计算明细表的比例指标
    summary = calc_metrics(summary)

    # --- 4. KPI 指标 ---
    t1, t2, t3, t4, t5 = st.columns(5)
    tc, ts, ti, tp, tnb = summary['Total Cost'].sum(), summary['Total Sales'].sum(), summary['Impressions'].sum(), summary['Total Purchases'].sum(), summary['Total New To Brand Purchases'].sum()
    
    t1.metric("Total Cost", f"{tc:,.2f}")
    t2.metric("Total Sales", f"{ts:,.2f}")
    # eCPM 这里也遵循汇总重算
    t3.metric("Total eCPM", f"{(tc/(ti/1000) if ti>0 else 0):.2f}")
    t4.metric("Total ROAS", f"{(ts/tc if tc>0 else 0):.2f}")
    t5.metric("Total NTBR", f"{(tnb/tp if tp>0 else 0):.2%}")

    # --- 5. 统计明细表 ---
    st.write("---")
    st.subheader("📋 数据统计明细表")
    order = ['ADV Name', '日期', 'Total Cost', 'Total ROAS', 'CPM', 'CPC', 'Impressions', 'Clicks', 'Total Detail Page View', 'Total Add To Cart', 'Total Purchases', 'Total Units Sold', 'CTR', 'Total NTB Rate', 'Total New To Brand Purchases', 'Total Sales']
    summary_display = summary[[c for c in order if c in summary.columns]].sort_values(['ADV Name', '日期'])
    st.dataframe(summary_display.style.set_properties(**{'background-color': '#F0F8FF', 'color': '#1A1A1A', 'border-color': '#C2DFFF'}).set_table_styles([{'selector': 'th', 'props': [('background-color', '#D1E9FF'), ('color', '#0A192F'), ('font-weight', 'bold')]}]).format({'日期': lambda x: x.strftime('%Y-%m-%d'), 'Total Cost': '{:.2f}', 'Total Sales': '{:.2f}', 'Total ROAS': '{:.2f}', 'CPM': '{:.2f}', 'CPC': '{:.2f}', 'CTR': '{:.2%}', 'Total NTB Rate': '{:.2%}'}), use_container_width=True)

    # --- 6. 趋势对比分析 (修正计算逻辑) ---
    st.write("---")
    st.subheader("📈 趋势对比分析")
    st.markdown('<div class="chart-filter-box">', unsafe_allow_html=True)
    c_col1, c_col2 = st.columns(2)
    m_bar = c_col1.selectbox("柱状图 (左轴)", ['Total Cost', 'Impressions', 'Total Sales', 'Total Purchases'])
    m_line = c_col2.selectbox("折线图 (右轴)", ['Total ROAS', 'Total NTB Rate', 'CTR', 'CPM'])
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 核心：图表数据按日期求和后，必须重新计算比例指标
    chart_df = summary_display.groupby('日期').agg({
        'Total Cost': 'sum', 'Total Sales': 'sum', 'Impressions': 'sum', 
        'Clicks': 'sum', 'Total Purchases': 'sum', 'Total New To Brand Purchases': 'sum'
    }).reset_index()
    chart_df = calc_metrics(chart_df) 
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=chart_df['日期'], y=chart_df[m_bar], name=m_bar, marker_color='#004A99', opacity=0.8), secondary_y=False)
    fig.add_trace(go.Scatter(x=chart_df['日期'], y=chart_df[m_line], name=m_line, line=dict(color='#E67E22', width=4), mode='lines+markers'), secondary_y=True)
    
    # 图表外观及坐标轴文字（深灰色）
    fig.update_layout(paper_bgcolor='white', plot_bgcolor='#F8FBFF', hovermode="x unified")
    fig.update_yaxes(title_text=f"<b>{m_bar}</b>", title_font=dict(color="#333333"), tickfont=dict(color="#333333"), gridcolor='#E2E8F0', secondary_y=False)
    fig.update_yaxes(title_text=f"<b>{m_line}</b>", title_font=dict(color="#333333"), tickfont=dict(color="#333333"), secondary_y=True)
    fig.update_xaxes(tickfont=dict(color="#333333"), gridcolor='#E2E8F0')
    st.plotly_chart(fig, use_container_width=True)
