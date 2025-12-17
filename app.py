import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- 1. 页面配置与视觉样式 (科技感背景与白底) ---
st.set_page_config(page_title="DSP 高级分析系统", layout="wide")

st.markdown("""
    <style>
    /* 整体背景设为白色 */
    .stApp {
        background-color: #FFFFFF;
    }
    
    /* 首页上传区域的科技感背景 */
    .upload-bg {
        background-image: url('https://img.freepik.com/free-vector/abstract-technology-background_23-2148892996.jpg');
        background-size: cover;
        padding: 100px;
        border-radius: 20px;
        text-align: center;
        color: white;
    }

    /* 顶部横栏样式 */
    div[data-testid="stHorizontalBlock"] {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    
    /* 隐藏左侧默认侧边栏内容，我们改用顶部 */
    [data-testid="stSidebar"] {
        display: none;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 数据处理函数 (修正字段名) ---
def load_and_clean_data(file):
    if file.name.endswith('.csv'):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)
    
    df.columns = df.columns.str.strip()
    
    # 修正后的字段映射
    mapping = {
        'Date': '日期',
        'Advertiser Name': 'ADV Name',
        'Total Detail Page View': 'Total Detail Page View', # 确认匹配
        'Total Add To Cart': 'Total Add To Cart',
        'Total Purchases': 'Total Purchases',
        'Total New To Brand Purchases': 'Total New To Brand Purchases',
        'Total Sales': 'Total Sales',
        'Total Cost': 'Total Cost',
        'Impressions': 'Impressions'
    }
    df.rename(columns=mapping, inplace=True)
    
    df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
    
    # 确保所有数值列正确转换
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
    # --- 首页上传界面 (科技感背景) ---
    st.markdown('<div class="upload-bg"><h1>🛰️ DSP 数据大脑</h1><p>智能识别多维报表，即刻生成深度洞察</p></div>', unsafe_allow_html=True)
    st.write("")
    uploaded_file = st.file_uploader("🚀 点击或拖拽上传 DSP 原始数据 (Excel/CSV)", type=['xlsx', 'csv'])
    if uploaded_file:
        st.session_state.df = load_and_clean_data(uploaded_file)
        st.session_state.data_loaded = True
        st.rerun()
else:
    # --- 看板界面 (白底 + 顶部横栏) ---
    df = st.session_state.df
    
    # 顶部横栏布局
    st.title("📊 DSP 投放洞察看板")
    
    # 创建顶部筛选横栏
    filter_col1, filter_col2, filter_col3 = st.columns([3, 3, 1])
    
    with filter_col1:
        all_advs = sorted(df['ADV Name'].unique().tolist())
        selected_advs = st.multiselect("选择 Advertiser Name", all_advs, default=all_advs)
    
    with filter_col2:
        min_date = df['日期'].min().date()
        max_date = df['日期'].max().date()
        date_range = st.date_input("选择时间段", [min_date, max_date])
        
    with filter_col3:
        st.write("") # 占位
        if st.button("重新上传"):
            st.session_state.data_loaded = False
            st.rerun()

    # 执行筛选
    if len(date_range) == 2:
        mask = (df['ADV Name'].isin(selected_advs)) & \
               (df['日期'].dt.date >= date_range[0]) & (df['日期'].dt.date <= date_range[1])
        filtered_df = df.loc[mask]
    else:
        filtered_df = df[df['ADV Name'].isin(selected_advs)]

    # --- 4. 核心计算 ---
    summary = filtered_df.groupby(['ADV Name', '日期']).agg({
        'Total Cost': 'sum',
        'Total Sales': 'sum',
        'Impressions': 'sum',
        'Clicks': 'sum',
        'Total Detail Page View': 'sum',
        'Total Add To Cart': 'sum',
        'Total Purchases': 'sum',
        'Total Units Sold': 'sum',
        'Total New To Brand Purchases': 'sum'
    }).reset_index()

    # 计算衍生指标
    summary['Total ROAS'] = (summary['Total Sales'] / summary['Total Cost']).fillna(0)
    summary['CPM'] = (summary['Total Cost'] / (summary['Impressions'] / 1000)).fillna(0)
    summary['CPC'] = (summary['Total Cost'] / summary['Clicks']).fillna(0)
    summary['CTR'] = (summary['Clicks'] / summary['Impressions']).fillna(0)
    summary['Total NTB Rate'] = (summary['Total New To Brand Purchases'] / summary['Total Purchases']).fillna(0)
    summary['Total DPVR'] = (summary['Total Detail Page View'] / summary['Impressions']).fillna(0)
    summary['Total ATCR'] = (summary['Total Add To Cart'] / summary['Impressions']).fillna(0)

    # --- 5. 顶层五个数据卡片 ---
    t1, t2, t3, t4, t5 = st.columns(5)
    
    total_cost = summary['Total Cost'].sum()
    total_sales = summary['Total Sales'].sum()
    total_impressions = summary['Impressions'].sum()
    total_purchases = summary['Total Purchases'].sum()
    total_ntb_purchases = summary['Total New To Brand Purchases'].sum()

    t1.metric("Total Cost", f"{total_cost:,.2f}")
    t2.metric("Total Sales", f"{total_sales:,.2f}")
    
    # Total eCPM 计算
    total_ecpm = (total_cost / (total_impressions / 1000)) if total_impressions > 0 else 0
    t3.metric("Total eCPM", f"{total_ecpm:.2f}")
    
    # Total ROAS 计算
    total_roas_val = (total_sales / total_cost) if total_cost > 0 else 0
    t4.metric("Total ROAS", f"{total_roas_val:.2f}")
    
    # Total NTBR 计算
    total_ntbr = (total_ntb_purchases / total_purchases) if total_purchases > 0 else 0
    t5.metric("Total NTBR", f"{total_ntbr:.2%}")

    # --- 6. 数据表格 ---
    st.write("---")
    st.subheader("📋 统计明细表")
    
    # 定义表头顺序
    final_cols = [
        'ADV Name', '日期', 'Total Cost', 'Total ROAS', 'CPM', 'CPC', 
        'Impressions', 'Clicks', 'Total Detail Page View', 'Total Add To Cart', 
        'Total Purchases', 'Total Units Sold', 'CTR', 'Total DPVR', 'Total ATCR', 
        'Total NTB Rate', 'Total New To Brand Purchases', 'Total Sales'
    ]
    
    # 过滤掉不存在的列并排序
    display_cols = [c for c in final_cols if c in summary.columns]
    summary_display = summary[display_cols].sort_values(['ADV Name', '日期'])

    st.dataframe(summary_display.style.format({
        '日期': lambda x: x.strftime('%Y-%m-%d'),
        'Total Cost': '{:.2f}', 'Total Sales': '{:.2f}', 'Total ROAS': '{:.2f}',
        'CPM': '{:.2f}', 'CPC': '{:.2f}', 'CTR': '{:.2%}', 'Total DPVR': '{:.2%}', 
        'Total NTB Rate': '{:.2%}'
    }), use_container_width=True)

    # --- 7. 趋势图表 ---
    st.write("---")
    st.subheader("📈 综合分析图表")
    
    chart_col1, chart_col2 = st.columns(2)
    m_bar = chart_col1.selectbox("左轴指标 (柱状图)", ['Total Cost', 'Impressions', 'Total Sales', 'Total Purchases'])
    m_line = chart_col2.selectbox("右轴指标 (折线图)", ['Total ROAS', 'Total NTB Rate', 'CTR', 'CPM'])

    # 图表聚合
    chart_df = summary_display.groupby('日期').agg({m_bar: 'sum', m_line: 'mean'}).reset_index()

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=chart_df['日期'], y=chart_df[m_bar], name=m_bar, marker_color='#3366CC'), secondary_y=False)
    fig.add_trace(go.Scatter(x=chart_df['日期'], y=chart_df[m_line], name=m_line, line=dict(color='#FF9900', width=3)), secondary_y=True)
    
    fig.update_layout(hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig, use_container_width=True)
