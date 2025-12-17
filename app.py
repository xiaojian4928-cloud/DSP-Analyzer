import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. 页面基础配置 ---
st.set_page_config(page_title="DSP 数据分析工具", layout="wide")
st.title("📊 DSP 投放数据自动化分析看板")

# --- 2. 字段映射表 (解决你的表格列名和需求不一致的问题) ---
# 左边是代码需要的标准名，右边是你的 Excel/CSV 里可能出现的原始名
COLUMN_MAPPING = {
    'Date': '日期',
    'Advertiser Name': 'ADV Name',
    'Total Cost': 'Total Cost',
    'Total Sales': 'Total Sales',
    'Impressions': 'Impressions',
    'Clicks': 'Clicks',
    'Total Detail Page View': 'Total DPV',
    'Total Add To Cart': 'Total ATC',
    'Total Purchases': 'Total purchases',
    'Total Units Sold': 'Total Units Sold',
    'Total New To Brand Purchases': 'Total New To Brand Purchases'
}

# --- 3. 数据清洗与加载函数 ---
@st.cache_data
def process_data(file):
    # 读取数据
    if file.name.endswith('.csv'):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)
    
    # 清洗：去除列名空格
    df.columns = df.columns.str.strip()
    
    # 自动更名：如果表里有 'Date' 就改成 '日期'，有 'Advertiser Name' 就改成 'ADV Name'
    # 这样方便后面统一逻辑计算
    rename_dict = {v: k for k, v in COLUMN_MAPPING.items()} # 预备反向检查
    df.rename(columns={'Date': '日期', 'Advertiser Name': 'ADV Name', 'Total Detail Page View': 'Total DPV', 'Total Add To Cart': 'Total ATC', 'Total Purchases': 'Total purchases'}, inplace=True)

    # 转换日期格式
    df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
    
    # 转换数值格式（处理掉可能存在的符号）
    num_cols = ['Total Cost', 'Total Sales', 'Impressions', 'Clicks', 'Total DPV', 'Total ATC', 'Total purchases', 'Total Units Sold', 'Total New To Brand Purchases']
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        else:
            df[col] = 0
            
    return df

# --- 4. 界面交互与显示 ---
uploaded_file = st.file_uploader("第一步：上传您的 DSP 原始报表", type=['xlsx', 'csv'])

if uploaded_file:
    df = process_data(uploaded_file)
    
    # 侧边栏筛选器
    st.sidebar.header("数据筛选")
    
    # 日期范围
    min_date = df['日期'].min().date()
    max_date = df['日期'].max().date()
    selected_range = st.sidebar.date_input("选择统计时间段", [min_date, max_date])
    
    # 维度选择
    dims = st.sidebar.multiselect("选择统计维度", ['ADV Name', '日期'], default=['ADV Name'])

    if len(selected_range) == 2 and dims:
        # 数据过滤
        mask = (df['日期'].dt.date >= selected_range[0]) & (df['日期'].dt.date <= selected_range[1])
        filtered_df = df.loc[mask]

        # 核心计算：聚合
        summary = filtered_df.groupby(dims).agg({
            'Total Cost': 'sum',
            'Total Sales': 'sum',
            'Impressions': 'sum',
            'Clicks': 'sum',
            'Total DPV': 'sum',
            'Total ATC': 'sum',
            'Total purchases': 'sum',
            'Total Units Sold': 'sum',
            'Total New To Brand Purchases': 'sum'
        }).reset_index()

        # 计算比例指标 (防止除以0)
        summary['Total ROAS'] = (summary['Total Sales'] / summary['Total Cost']).fillna(0)
        summary['CPM'] = (summary['Total Cost'] / (summary['Impressions'] / 1000)).fillna(0)
        summary['CPC'] = (summary['Total Cost'] / summary['Clicks']).fillna(0)
        summary['CTR'] = (summary['Clicks'] / summary['Impressions']).fillna(0)
        summary['Total DPVR'] = (summary['Total DPV'] / summary['Impressions']).fillna(0)
        summary['Total NTB Rate'] = (summary['Total New To Brand Purchases'] / summary['Total purchases']).fillna(0)

        # 顶层卡片
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("总消耗", f"¥{summary['Total Cost'].sum():,.2f}")
        c2.metric("总销售额", f"¥{summary['Total Sales'].sum():,.2f}")
        c3.metric("整体 ROAS", f"{(summary['Total Sales'].sum() / summary['Total Cost'].sum()):.2f}")
        c4.metric("总成交数", f"{int(summary['Total purchases'].sum())}")

        # 数据表
        st.subheader("📋 统计明细")
        st.dataframe(summary.style.format({
            'Total Cost': '¥{:,.2f}', 'Total Sales': '¥{:,.2f}',
            'Total ROAS': '{:.2f}', 'CPM': '¥{:,.2f}', 'CPC': '¥{:,.2f}',
            'CTR': '{:.2%}', 'Total DPVR': '{:.2%}', 'Total NTB Rate': '{:.2%}'
        }), use_container_width=True)

        # 可视化
        st.subheader("📈 趋势对比")
        chart_col = st.selectbox("选择要查看的指标", ['Total Cost', 'Total Sales', 'Total ROAS', 'Total purchases'])
        if '日期' in dims:
            fig = px.line(summary.sort_values('日期'), x='日期', y=chart_col, color='ADV Name' if 'ADV Name' in dims else None)
        else:
            fig = px.bar(summary, x='ADV Name', y=chart_col, text_auto='.2s')
        st.plotly_chart(fig, use_container_width=True)

        # 导出
        csv = summary.to_csv(index=False).encode('utf_8_sig')
        st.download_button("📥 导出分析表格", data=csv, file_name='DSP_Analysis.csv')
    else:
        st.warning("请在左侧选择时间范围和至少一个统计维度。")

else:
    st.info("💡 请先上传文件。你可以直接把 DSP 导出的原始表格拖进来，系统会自动识别列名。")
