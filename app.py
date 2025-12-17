import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime

# --- 1. 视觉样式完全修正 ---
st.set_page_config(page_title="DSP 投放看板", layout="wide")

st.markdown("""
    <style>
    /* 强制背景与标题颜色 */
    .stApp { background-color: #F0F4F8 !important; }
    .main-title { color: #003366 !important; text-align: center; font-weight: 800; font-size: 2.5rem; margin-bottom: 20px; }
    
    /* 首页科技感背景 */
    .upload-container {
        background: linear-gradient(135deg, #E6F0FF 0%, #F0F4F8 100%);
        padding: 40px; border-radius: 15px; border: 1px solid #BEE3F8; text-align: center; margin-top: 50px;
    }
    .upload-container h1, .upload-container p { color: #4A5568 !important; }

    /* 上传框深蓝色 */
    [data-testid="stFileUploader"] section { background-color: #0A192F !important; color: white !important; border: 2px dashed #3182CE !important; }
    [data-testid="stFileUploader"] label { color: #4A5568 !important; }

    /* 表格去黑：针对新版 Streamlit 的全局强制背景 */
    .stDataFrame, div[data-testid="stTable"], .stTable { background-color: #FFFFFF !important; }
    
    /* 筛选区 */
    .filter-box { background-color: #E1EFFE !important; padding: 20px; border-radius: 10px; border: 1px solid #BEE3F8; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 增强型数据处理逻辑 ---
def safe_calc(df_in):
    """确保所有比例指标在聚合后重新计算，避免报错"""
    d = df_in.copy()
    def div(a, b): return (a / b).replace([float('inf'), -float('inf')], 0).fillna(0)
    
    d['Total ROAS'] = div(d['Total Sales'], d['Total Cost'])
    d['CPM'] = div(d['Total Cost'], d['Impressions'] / 1000)
    d['CPC'] = div(d['Total Cost'], d['Clicks'])
    d['Total CPDPV'] = div(d['Total Cost'], d['Total Detail Page View'])
    d['CTR'] = div(d['Clicks'], d['Impressions'])
    d['Total DPVR'] = div(d['Total Detail Page View'], d['Impressions'])
    d['Total ATCR'] = div(d['Total Add To Cart'], d['Impressions'])
    d['Total NTB Rate'] = div(d['Total New To Brand Purchases'], d['Total Purchases'])
    return d

def clean_input_data(file):
    """清洗上传文件"""
    try:
        df = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
        df.columns = df.columns.str.strip()
        
        # 严格对齐列名
        mapping = {
            'Date': '日期', 'Advertiser Name': 'ADV Name',
            'Total Detail Page View': 'Total Detail Page View', 'Total Add To Cart': 'Total Add To Cart',
            'Total Purchases': 'Total Purchases', 'Total New To Brand Purchases': 'Total New To Brand Purchases',
            'Total Sales': 'Total Sales', 'Total Cost': 'Total Cost', 'Impressions': 'Impressions',
            'Clicks': 'Clicks', 'Total Units Sold': 'Total Units Sold'
        }
        df.rename(columns=mapping, inplace=True)
        
        # 处理日期
        df['日期'] = pd.to_datetime(df['日期']).dt.date
        
        # 补全明细表要求的 19 列中可能缺失的列
        required_cols = ['Total Detail Page View', 'Total Add To Cart', 'Total Purchases', 
                         'Total New To Brand Purchases', 'Total Sales', 'Total Cost', 
                         'Impressions', 'Clicks', 'Total Units Sold']
        for c in required_cols:
            if c not in df.columns: df[c] = 0
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
        
        return df
    except Exception as e:
        st.error(f"❌ 数据读取出错: {e}")
        return None

# --- 3. 页面渲染逻辑 ---
if 'main_df' not in st.session_state:
    st.session_state.main_df = None

# A. 上传界面
if st.session_state.main_df is None:
    st.markdown('<div class="upload-container"><h1>🚀 DSP 数据洞察中心</h1><p>请上传您的广告报表 (CSV 或 Excel)</p></div>', unsafe_allow_html=True)
    uploaded = st.file_uploader("", type=['xlsx', 'csv'])
    if uploaded:
        data = clean_input_data(uploaded)
        if data is not None:
            st.session_state.main_df = data
            st.rerun()

# B. 看板界面
else:
    st.markdown('<h1 class="main-title">📊 DSP 投放洞察看板</h1>', unsafe_allow_html=True)
    full_df = st.session_state.main_df

    # 筛选区
    st.markdown('<div class="filter-box">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([3, 3, 1])
    with col1:
        adv_list = sorted(full_df['ADV Name'].unique())
        sel_adv = st.multiselect("筛选广告主", adv_list, default=adv_list)
    with col2:
        # 预防日期选择只有一位时报错
        date_pick = st.date_input("选择时间范围", [full_df['日期'].min(), full_df['日期'].max()])
    with col3:
        st.write("")
        if st.button("🔄 重新上传"):
            st.session_state.main_df = None
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # 数据过滤逻辑：必须确保选择了完整的日期范围
    if len(date_pick) == 2:
        mask = (full_df['ADV Name'].isin(sel_adv)) & (full_df['日期'] >= date_pick[0]) & (full_df['日期'] <= date_pick[1])
        working_df = full_df[mask]
        
        if not working_df.empty:
            # 聚合并重新计算比例
            summary = working_df.groupby(['ADV Name', '日期']).sum(numeric_only=True).reset_index()
            summary = safe_calc(summary)

            # 1. KPI 展示
            k1, k2, k3, k4 = st.columns(4)
            cost_sum = summary['Total Cost'].sum()
            sales_sum = summary['Total Sales'].sum()
            k1.metric("总消耗", f"${cost_sum:,.2f}")
            k2.metric("总销售", f"${sales_sum:,.2f}")
            k3.metric("总 ROAS", f"{(sales_sum/cost_sum):.2f}" if cost_sum > 0 else "0.00")
            k4.metric("总转化订单", f"{int(summary['Total Purchases'].sum()):,}")

            # 2. 明细表：严格按照您要求的 19 列顺序
            st.subheader("📋 数据统计明细表")
            final_order = [
                'ADV Name', '日期', 'Total Cost', 'Total ROAS', 'CPM', 'CPC', 'Total CPDPV', 
                'Impressions', 'Clicks', 'Total Detail Page View', 'Total Add To Cart', 
                'Total Purchases', 'Total Units Sold', 'CTR', 'Total DPVR', 'Total ATCR', 
                'Total NTB Rate', 'Total New To Brand Purchases', 'Total Sales'
            ]
            
            # 确保列都在 summary 中
            display_cols = [c for c in final_order if c in summary.columns]
            
            st.dataframe(
                summary[display_cols].sort_values(['日期', 'ADV Name'], ascending=[False, True]),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Total Cost": st.column_config.NumberColumn(format="%.2f"),
                    "Total ROAS": st.column_config.NumberColumn(format="%.2f"),
                    "CPM": st.column_config.NumberColumn(format="%.2f"),
                    "CPC": st.column_config.NumberColumn(format="%.2f"),
                    "Total CPDPV": st.column_config.NumberColumn(format="%.2f"),
                    "CTR": st.column_config.NumberColumn(format="%.2%"),
                    "Total DPVR": st.column_config.NumberColumn(format="%.2%"),
                    "Total ATCR": st.column_config.NumberColumn(format="%.2%"),
                    "Total NTB Rate": st.column_config.NumberColumn(format="%.2%"),
                    "Total Purchases": st.column_config.NumberColumn(format="%d"),
                    "Total Units Sold": st.column_config.NumberColumn(format="%d"),
                }
            )

            # 3. 趋势图
            st.write("---")
            st.subheader("📈 投放趋势分析")
            chart_base = summary.groupby('日期').sum(numeric_only=True).reset_index()
            chart_data = safe_calc(chart_base)

            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_trace(go.Bar(x=chart_data['日期'], y=chart_data['Total Cost'], name="Cost", marker_color='#4299E1'), secondary_y=False)
            fig.add_trace(go.Scatter(x=chart_data['日期'], y=chart_data['Total ROAS'], name="ROAS", line=dict(color='#ED8936', width=3)), secondary_y=True)
            
            fig.update_layout(
                hovermode="x unified", plot_bgcolor='white', height=450,
                xaxis=dict(tickfont=dict(color="#4A5568"), showgrid=False),
                yaxis=dict(title="Total Cost", titlefont=dict(color="#4299E1")),
                yaxis2=dict(title="Total ROAS", titlefont=dict(color="#ED8936"), overlaying='y', side='right'),
                margin=dict(l=0, r=0, t=30, b=0)
            )
            st.plotly_chart(fig, use_container_width=True)

        else:
            st.info("💡 当前筛选范围内没有数据，请调整广告主或日期。")
    else:
        st.warning("⏳ 请在日期选择器中选择【开始日期】和【结束日期】。")
