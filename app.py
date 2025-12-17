import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- 1. 页面配置 ---
st.set_page_config(page_title="DSP 数据分析专业版", layout="wide")

# 自定义 CSS 隐藏默认单位显示并美化界面
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    div[data-testid="stMetricValue"] { font-size: 24px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 数据处理函数 ---
def load_and_clean_data(file):
    if file.name.endswith('.csv'):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)
    
    # 清洗列名
    df.columns = df.columns.str.strip()
    
    # 核心列名映射（根据你提供的文件结构匹配）
    mapping = {
        'Date': '日期',
        'Advertiser Name': 'ADV Name',
        'eCPDPV': 'Total CPDPV'
    }
    df.rename(columns=mapping, inplace=True)
    
    # 日期转换
    df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
    
    # 填充缺失列并确保数值化
    required_metrics = [
        'Total Cost', 'Total Sales', 'Impressions', 'Clicks', 'Total DPV', 
        'Total ATC', 'Total purchases', 'Total Units Sold', 'Total New To Brand Purchases',
        'Total CPDPV'
    ]
    for col in required_metrics:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    return df

# --- 3. 逻辑控制：上传界面 vs 看板界面 ---
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False

if not st.session_state.data_loaded:
    # 初始上传界面
    st.title("📂 DSP 数据分析系统")
    st.write("请上传您的 DSP 原始报表以开始分析")
    uploaded_file = st.file_uploader("选择 Excel 或 CSV 文件", type=['xlsx', 'csv'])
    if uploaded_file:
        st.session_state.df = load_and_clean_data(uploaded_file)
        st.session_state.data_loaded = True
        st.rerun()
else:
    # 已上传后的看板界面
    df = st.session_state.df
    
    st.sidebar.header("数据筛选与控制")
    if st.sidebar.button("🔄 重新上传新表格"):
        st.session_state.data_loaded = False
        st.rerun()

    # 筛选器：ADV Name 多选
    all_advs = sorted(df['ADV Name'].unique().tolist())
    selected_advs = st.sidebar.multiselect("选择 Advertiser Name", all_advs, default=all_advs)
    
    # 筛选器：日期范围
    min_date = df['日期'].min().date()
    max_date = df['日期'].max().date()
    date_range = st.sidebar.date_input("选择统计时间段", [min_date, max_date])

    # 执行筛选
    if len(date_range) == 2:
        mask = (df['ADV Name'].isin(selected_advs)) & \
               (df['日期'].dt.date >= date_range[0]) & (df['日期'].dt.date <= date_range[1])
        filtered_df = df.loc[mask]
    else:
        filtered_df = df[df['ADV Name'].isin(selected_advs)]

    # --- 4. 核心计算 (ADV Name + 日期) ---
    summary = filtered_df.groupby(['ADV Name', '日期']).agg({
        'Total Cost': 'sum',
        'Total Sales': 'sum',
        'Impressions': 'sum',
        'Clicks': 'sum',
        'Total DPV': 'sum',
        'Total ATC': 'sum',
        'Total purchases': 'sum',
        'Total Units Sold': 'sum',
        'Total New To Brand Purchases': 'sum',
        'Total CPDPV': 'mean' # CPDPV 通常取平均或重算，这里按你需求展示
    }).reset_index()

    # 重算比例指标
    summary['Total ROAS'] = (summary['Total Sales'] / summary['Total Cost']).fillna(0)
    summary['CPM'] = (summary['Total Cost'] / (summary['Impressions'] / 1000)).fillna(0)
    summary['CPC'] = (summary['Total Cost'] / summary['Clicks']).fillna(0)
    summary['CTR'] = (summary['Clicks'] / summary['Impressions']).fillna(0)
    summary['Total DPVR'] = (summary['Total DPV'] / summary['Impressions']).fillna(0)
    summary['Total ATCR'] = (summary['Total ATC'] / summary['Impressions']).fillna(0)
    summary['Total NTB Rate'] = (summary['Total New To Brand Purchases'] / summary['Total purchases']).fillna(0)

    # 排序并规范输出表头顺序
    final_cols = [
        'ADV Name', '日期', 'Total Cost', 'Total ROAS', 'CPM', 'CPC', 'Total CPDPV', 
        'Impressions', 'Clicks', 'Total DPV', 'Total ATC', 'Total purchases', 
        'Total Units Sold', 'CTR', 'Total DPVR', 'Total ATCR', 'Total NTB Rate', 
        'Total New To Brand Purchases', 'Total Sales'
    ]
    summary_display = summary[final_cols].sort_values(['ADV Name', '日期'])

    # --- 5. 界面展示 ---
    st.title("📊 DSP 投放看板")
    
    # KPI 顶栏
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("总消耗", f"{summary['Total Cost'].sum():,.2f}")
    k2.metric("总销售额", f"{summary['Total Sales'].sum():,.2f}")
    total_roas = summary['Total Sales'].sum() / summary['Total Cost'].sum() if summary['Total Cost'].sum() > 0 else 0
    k3.metric("总 ROAS", f"{total_roas:.2f}")
    k4.metric("总订单量", f"{int(summary['Total purchases'].sum())}")

    # 数据表格
    st.subheader("📋 统计明细表 (按广告主及日期)")
    st.dataframe(summary_display.style.format({
        '日期': lambda x: x.strftime('%Y-%m-%d'),
        'Total Cost': '{:.2f}', 'Total Sales': '{:.2f}', 'Total ROAS': '{:.2f}',
        'CPM': '{:.2f}', 'CPC': '{:.2f}', 'CTR': '{:.2%}', 'Total DPVR': '{:.2%}', 
        'Total NTB Rate': '{:.2%}'
    }), use_container_width=True)

    # 导出
    csv = summary_display.to_csv(index=False).encode('utf_8_sig')
    st.download_button("📥 导出统计明细", data=csv, file_name='DSP_Analysis_Detail.csv')

    # --- 6. 趋势对比图 (复合图表) ---
    st.subheader("📈 趋势对比分析")
    col_a, col_b = st.columns(2)
    metric_bar = col_a.selectbox("柱状图指标 (左轴)", ['Total Cost', 'Impressions', 'Clicks', 'Total Sales'], index=0)
    metric_line = col_b.selectbox("折线图指标 (右轴)", ['Total ROAS', 'CTR', 'CPC', 'Total purchases'], index=0)

    # 准备图表数据（按日期汇总选中的 ADV Name）
    chart_data = summary_display.groupby('日期').agg({metric_bar: 'sum', metric_line: 'mean' if 'R' in metric_line or 'C' in metric_line else 'sum'}).reset_index()

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=chart_data['日期'], y=chart_data[metric_bar], name=metric_bar, opacity=0.7), secondary_y=False)
    fig.add_trace(go.Scatter(x=chart_data['日期'], y=chart_data[metric_line], name=metric_line, mode='lines+markers', line=dict(width=3)), secondary_y=True)

    fig.update_layout(title_text=f"{metric_bar} 与 {metric_line} 每日趋势", hovermode="x unified")
    fig.update_yaxes(title_text=metric_bar, secondary_y=False)
    fig.update_yaxes(title_text=metric_line, secondary_y=True)
    
    st.plotly_chart(fig, use_container_width=True)
