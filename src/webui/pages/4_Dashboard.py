"""
Dashboard Page - 评估仪表板
展示评估分数、趋势图、执行记录
"""

import asyncio
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

# 页面配置
st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

# 导入服务
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from webui.services.api_client import APIClient
from webui.utils.config import config


def render_sidebar():
    """渲染侧边栏"""
    with st.sidebar:
        st.title(f"{config.PAGE_ICON} OpenYoung")
        st.divider()
        st.page_link("app.py", label="🏠 Home")
        st.page_link("pages/1_Agents.py", label="🤖 Agents")
        st.page_link("pages/2_Chat.py", label="💬 Chat")
        st.page_link("pages/3_Sessions.py", label="📋 Sessions")
        st.page_link("pages/5_Settings.py", label="⚙️ Settings")


async def load_executions(limit: int = 100) -> list:
    """加载执行记录"""
    client = APIClient(config.API_BASE_URL, config.API_KEY)
    try:
        result = await client.list_executions(limit=limit)
        await client.close()
        return result.get("items", [])
    except Exception as e:
        await client.close()
        return []


async def load_evaluations(limit: int = 100) -> list:
    """加载评估记录"""
    client = APIClient(config.API_BASE_URL, config.API_KEY)
    try:
        result = await client.list_evaluations(limit=limit)
        await client.close()
        return result.get("items", [])
    except Exception as e:
        await client.close()
        return []


def render_metrics_row(executions: list, evaluations: list):
    """渲染指标卡片行"""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Executions", len(executions))

    with col2:
        success_count = sum(1 for e in executions if e.get("status") == "success")
        rate = (success_count / len(executions) * 100) if executions else 0
        st.metric("Success Rate", f"{rate:.1f}%")

    with col3:
        st.metric("Total Evaluations", len(evaluations))

    with col4:
        if evaluations:
            avg_score = sum(e.get("overall_score", 0) for e in evaluations) / len(evaluations)
            st.metric("Avg Score", f"{avg_score:.2f}")
        else:
            st.metric("Avg Score", "—")


def render_trend_chart(evaluations: list):
    """渲染趋势图"""
    if not evaluations:
        st.info("No evaluation data available")
        return

    # 准备数据
    data = []
    for eval_item in evaluations:
        data.append(
            {
                "date": eval_item.get("evaluated_at", "")[:10],
                "score": eval_item.get("overall_score", 0),
                "iteration": eval_item.get("iteration", 0),
            }
        )

    if not data:
        st.info("No evaluation data available")
        return

    df = pd.DataFrame(data)

    # 趋势图
    st.subheader("📈 Score Trend")

    # 按日期分组计算平均分
    daily_avg = df.groupby("date")["score"].mean().reset_index()

    # 使用 Streamlit 折线图
    st.line_chart(daily_avg.set_index("date")["score"])

    # 显示详细数据
    with st.expander("View Raw Data"):
        st.dataframe(daily_avg, use_container_width=True)


def render_execution_table(executions: list):
    """渲染执行记录表格"""
    st.subheader("📋 Recent Executions")

    if not executions:
        st.info("No executions found")
        return

    # 准备表格数据
    table_data = []
    for exec_item in executions:
        table_data.append(
            {
                "ID": exec_item.get("run_id", "")[:20] + "...",
                "Agent": exec_item.get("agent_name", "Unknown"),
                "Status": exec_item.get("status", "unknown"),
                "Duration": f"{exec_item.get('duration_ms', 0) / 1000:.2f}s",
                "Score": f"{exec_item.get('score', 0):.2f}" if exec_item.get("score") else "—",
                "Date": exec_item.get("start_time", "")[:10],
            }
        )

    df = pd.DataFrame(table_data)

    # 显示表格
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )


def render_evaluation_details(evaluations: list):
    """渲染评估详情"""
    st.subheader("🎯 Evaluation Details")

    if not evaluations:
        st.info("No evaluations found")
        return

    # 选择展示的评估
    selected_idx = st.selectbox(
        "Select Evaluation",
        range(len(evaluations)),
        format_func=lambda i: f"Eval #{i + 1}: {evaluations[i].get('overall_score', 0):.2f}",
    )

    eval_item = evaluations[selected_idx]

    # 基本信息
    col1, col2 = st.columns(2)

    with col1:
        st.metric("Overall Score", f"{eval_item.get('overall_score', 0):.2f}")

    with col2:
        passed = "✅ Passed" if eval_item.get("passed") else "❌ Failed"
        st.write(passed)

    # 评估维度
    dimensions = eval_item.get("dimensions", [])
    if dimensions:
        st.write("### Dimensions")

        for dim in dimensions:
            with st.expander(f"{dim.get('name', 'Unknown')}: {dim.get('score', 0):.2f}"):
                st.write(f"**Score**: {dim.get('score', 0):.2f} / {dim.get('threshold', 1.0)}")
                st.write(f"**Passed**: {'✅' if dim.get('passed') else '❌'}")
                st.write(f"**Reasoning**: {dim.get('reasoning', 'N/A')}")

    # 反馈
    feedback = eval_item.get("feedback", "")
    if feedback:
        st.write("### Feedback")
        st.info(feedback)


def main():
    """主函数"""
    st.title("📊 Dashboard")

    render_sidebar()

    # 加载数据
    with st.spinner("Loading data..."):
        executions = asyncio.run(load_executions())
        evaluations = asyncio.run(load_evaluations())

    # 指标卡片
    render_metrics_row(executions, evaluations)

    st.markdown("---")

    # 标签页: 概览 | 执行记录 | 评估详情
    tab1, tab2, tab3 = st.tabs(["📈 Overview", "📋 Executions", "🎯 Evaluations"])

    with tab1:
        render_trend_chart(evaluations)

    with tab2:
        render_execution_table(executions)

    with tab3:
        render_evaluation_details(evaluations)

    # 刷新按钮
    st.markdown("---")
    if st.button("🔄 Refresh Data"):
        st.rerun()


if __name__ == "__main__":
    main()
