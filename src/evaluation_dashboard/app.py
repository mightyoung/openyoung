"""
Evaluation Dashboard - Streamlit 仪表板

Phase 1.2 评估仪表板
提供指标展示、趋势图、数据查询、导出功能
"""

from datetime import datetime, timedelta

import streamlit as st

# 页面配置
st.set_page_config(
    page_title="OpenYoung 评估平台",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


def init_session_state():
    """初始化会话状态"""
    if "refresh_interval" not in st.session_state:
        st.session_state.refresh_interval = 30
    if "filters" not in st.session_state:
        st.session_state.filters = {
            "agent_name": None,
            "status": None,
            "date_range": None,
        }


def render_metrics_cards():
    """渲染指标卡片"""
    # FIXME: 从数据库获取真实数据
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="总评估数",
            value="1,234",
            delta="+12%",
        )

    with col2:
        st.metric(
            label="通过率",
            value="87.5%",
            delta="+5.2%",
        )

    with col3:
        st.metric(
            label="平均分",
            value="0.85",
            delta="+0.08",
        )

    with col4:
        st.metric(
            label="中位数",
            value="0.88",
            delta="+0.05",
        )


def render_trend_chart():
    """渲染趋势图"""
    st.subheader("📈 评分趋势")

    # 模拟数据
    import numpy as np
    import pandas as pd

    dates = pd.date_range(end=datetime.now(), periods=30, freq="D")
    scores = np.random.uniform(0.7, 0.95, size=len(dates))
    scores = pd.Series(scores).rolling(window=3).mean()

    df = pd.DataFrame(
        {
            "日期": dates,
            "平均分": scores,
        }
    )

    # 使用 Streamlit 原生图表
    st.line_chart(df.set_index("日期")["平均分"], height=300)

    # 维度分布
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("维度分布")
        dimensions = {
            "correctness": 0.85,
            "safety": 0.92,
            "efficiency": 0.78,
            "robustness": 0.81,
        }
        st.bar_chart(pd.Series(dimensions), horizontal=True)

    with col2:
        st.subheader("通过/失败分布")
        status_data = {"通过": 87, "失败": 13}
        st.bar_chart(pd.Series(status_data))


def render_data_table():
    """渲染数据表格"""
    st.subheader("📋 执行记录")

    # 模拟数据
    import pandas as pd

    data = []
    for i in range(50):
        data.append(
            {
                "ID": f"exec_{i:04d}",
                "Agent": f"agent_{i % 5}",
                "任务": f"Task {i}",
                "状态": ["success", "failed", "running"][i % 3],
                "评分": round(0.7 + (i % 25) * 0.01, 2),
                "时间": (datetime.now() - timedelta(hours=i)).strftime("%Y-%m-%d %H:%M"),
            }
        )

    df = pd.DataFrame(data)

    # 筛选器
    col1, col2, col3 = st.columns(3)

    with col1:
        agent_filter = st.selectbox(
            "Agent 筛选",
            ["全部"] + [f"agent_{i}" for i in range(5)],
        )

    with col2:
        status_filter = st.selectbox(
            "状态筛选",
            ["全部", "success", "failed", "running"],
        )

    with col3:
        min_score = st.slider("最低评分", 0.0, 1.0, 0.0, 0.05)

    # 应用筛选
    if agent_filter != "全部":
        df = df[df["Agent"] == agent_filter]

    if status_filter != "全部":
        df = df[df["状态"] == status_filter]

    df = df[df["评分"] >= min_score]

    # 分页显示
    page_size = 10
    total_pages = (len(df) + page_size - 1) // page_size
    page = st.number_input("页码", min_value=1, max_value=max(1, total_pages), value=1)

    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size

    st.dataframe(
        df.iloc[start_idx:end_idx],
        use_container_width=True,
        hide_index=True,
    )

    st.caption(f"显示 {start_idx + 1}-{min(end_idx, len(df))} 条，共 {len(df)} 条")


def render_sidebar():
    """渲染侧边栏"""
    st.sidebar.title("⚙️ 配置")

    st.sidebar.subheader("刷新设置")
    refresh_interval = st.sidebar.slider(
        "自动刷新间隔 (秒)",
        min_value=5,
        max_value=120,
        value=st.session_state.refresh_interval,
        step=5,
    )
    st.session_state.refresh_interval = refresh_interval

    if st.sidebar.button("🔄 手动刷新"):
        st.rerun()

    st.sidebar.divider()

    st.sidebar.subheader("导出")
    export_format = st.sidebar.selectbox(
        "导出格式",
        ["JSON", "CSV", "Parquet"],
    )

    if st.sidebar.button("📥 导出数据"):
        st.sidebar.success(f"导出为 {export_format} 格式")

    st.sidebar.divider()

    st.sidebar.subheader("关于")
    st.sidebar.info("OpenYoung 评估平台 v1.0.0\n\n基于 LangSmith 最佳实践构建")


def main():
    """主函数"""
    init_session_state()

    # 标题
    st.title("📊 OpenYoung 评估平台")
    st.markdown("---")

    # 渲染指标卡片
    render_metrics_cards()

    st.markdown("---")

    # 渲染趋势图
    render_trend_chart()

    st.markdown("---")

    # 渲染数据表格
    render_data_table()


if __name__ == "__main__":
    main()
