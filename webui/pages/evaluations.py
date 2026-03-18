"""
Evaluation Page - Evaluation results and metrics display

Based on Streamlit best practices for data visualization:
- Uses render_metric_card for key metrics
- Uses render_card for evaluation results
- Provides filtering and search capabilities
"""

import streamlit as st

from webui.components.ui.metric import render_metric_card
from webui.components.ui.card import render_card, render_card_expanded
from webui.components.ui.button import render_button
from webui.utils.config import config


def render():
    """Render evaluation page"""
    st.title("Evaluation")

    # Get API client
    client = st.session_state.get("api_client")

    # Filter options
    with st.expander("Filters", expanded=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            execution_filter = st.text_input("Execution ID", "")
        with col2:
            passed_filter = st.selectbox("Pass Status", ["All", "Passed", "Failed"])
        with col3:
            score_filter = st.slider("Score Range", 0.0, 1.0, (0.0, 1.0))

    # Build query parameters
    params = {"limit": 50, "offset": 0}
    if execution_filter:
        params["execution_id"] = execution_filter

    passed_value = passed_filter if passed_filter != "All" else None
    if passed_value == "Passed":
        params["passed"] = True
    elif passed_value == "Failed":
        params["passed"] = False

    if score_filter[0] > 0:
        params["min_score"] = score_filter[0]
    if score_filter[1] < 1.0:
        params["max_score"] = score_filter[1]

    # Fetch data
    try:
        if client:
            result = client.list_evaluations(**params)
            evaluations = result.get("items", [])
            total = result.get("total", 0)
        else:
            # Demo data
            evaluations = [
                {
                    "evaluation_id": "eval_001",
                    "execution_id": "exec_001",
                    "score": 0.85,
                    "passed": True,
                    "evaluator_type": "llm_judge",
                    "created_at": "2026-03-15T10:00:00",
                },
                {
                    "evaluation_id": "eval_002",
                    "execution_id": "exec_002",
                    "score": 0.72,
                    "passed": True,
                    "evaluator_type": "llm_judge",
                    "created_at": "2026-03-15T09:30:00",
                },
                {
                    "evaluation_id": "eval_003",
                    "execution_id": "exec_003",
                    "score": 0.45,
                    "passed": False,
                    "evaluator_type": "code_eval",
                    "created_at": "2026-03-15T09:00:00",
                },
            ]
            total = len(evaluations)
    except Exception as e:
        st.error(f"Failed to load evaluations: {str(e)}")
        evaluations = []
        total = 0

    # Display metrics using render_metric_card
    st.markdown("### Overview")

    passed_count = sum(1 for e in evaluations if e.get("passed"))
    failed_count = sum(1 for e in evaluations if not e.get("passed"))
    avg_score = (
        sum(e.get("score", 0) for e in evaluations) / len(evaluations) if evaluations else 0
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        render_metric_card(
            label="Total Evaluations",
            value=total,
            help_text="Total number of evaluations run"
        )

    with col2:
        render_metric_card(
            label="Passed",
            value=passed_count,
            help_text="Evaluations that passed their criteria"
        )

    with col3:
        render_metric_card(
            label="Failed",
            value=failed_count,
            help_text="Evaluations that did not meet criteria"
        )

    with col4:
        render_metric_card(
            label="Avg Score",
            value=f"{avg_score:.2%}",
            help_text="Average score across all evaluations"
        )

    st.markdown("---")

    # Display evaluation list using render_card
    st.markdown("### Evaluation Results")

    if evaluations:
        for eval_record in evaluations:
            score = eval_record.get("score", 0)
            passed = eval_record.get("passed", False)
            status_color = "var(--success)" if passed else "var(--error)"

            with st.container():
                st.markdown(f"""
                <div style="
                    border: 1px solid var(--border);
                    border-radius: var(--radius-lg);
                    padding: var(--space-4);
                    margin-bottom: var(--space-3);
                    background: var(--background);
                ">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong style="font-size: var(--text-lg);">{eval_record.get('evaluation_id', 'N/A')}</strong>
                            <span style="color: var(--foreground-muted); margin-left: var(--space-2);">
                                Execution: {eval_record.get('execution_id', 'N/A')}
                            </span>
                        </div>
                        <div style="text-align: right;">
                            <span style="
                                display: inline-block;
                                padding: var(--space-1) var(--space-3);
                                border-radius: var(--radius-full);
                                background: {status_color};
                                color: var(--primary-foreground);
                                font-size: var(--text-sm);
                                font-weight: var(--weight-medium);
                            ">
                                {'Passed' if passed else 'Failed'}
                            </span>
                        </div>
                    </div>
                    <div style="margin-top: var(--space-3); color: var(--foreground-muted);">
                        <span>Type: {eval_record.get('evaluator_type', 'N/A')}</span>
                        <span style="margin-left: var(--space-4);">Score: {score:.2%}</span>
                        <span style="margin-left: var(--space-4);">{eval_record.get('created_at', 'N/A')}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No evaluation records found")

    # Executions section
    st.markdown("### Recent Executions")

    try:
        if client:
            exec_result = client.list_executions(limit=10)
            executions = exec_result.get("items", [])
        else:
            # Demo data
            executions = [
                {
                    "execution_id": "exec_001",
                    "agent_name": "coder",
                    "status": "success",
                    "created_at": "2026-03-15T10:00:00",
                },
                {
                    "execution_id": "exec_002",
                    "agent_name": "reviewer",
                    "status": "success",
                    "created_at": "2026-03-15T09:30:00",
                },
                {
                    "execution_id": "exec_003",
                    "agent_name": "tester",
                    "status": "failed",
                    "created_at": "2026-03-15T09:00:00",
                },
            ]
    except Exception as e:
        st.error(f"Failed to load executions: {str(e)}")
        executions = []

    if executions:
        for exec_record in executions:
            status = exec_record.get("status", "unknown")
            status_color = "var(--success)" if status == "success" else "var(--error)" if status == "failed" else "var(--info)"
            status_text = "✓ Success" if status == "success" else "✗ Failed" if status == "failed" else "⟳ Running" if status == "running" else f"○ {status}"

            with st.container():
                st.markdown(f"""
                <div style="
                    border: 1px solid var(--border-subtle);
                    border-radius: var(--radius-md);
                    padding: var(--space-3) var(--space-4);
                    margin-bottom: var(--space-2);
                    background: var(--background-muted);
                ">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong>{exec_record.get('execution_id', 'N/A')}</strong>
                            <span style="color: var(--foreground-muted); margin-left: var(--space-3);">
                                Agent: {exec_record.get('agent_name', 'N/A')}
                            </span>
                        </div>
                        <div style="display: flex; align-items: center; gap: var(--space-3);">
                            <span style="color: var(--foreground-muted); font-size: var(--text-sm);">
                                {exec_record.get('created_at', 'N/A')}
                            </span>
                            <span style="
                                padding: var(--space-1) var(--space-2);
                                border-radius: var(--radius-sm);
                                background: {status_color};
                                color: var(--primary-foreground);
                                font-size: var(--text-xs);
                            ">
                                {status_text}
                            </span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No execution records found")


# Import for type hints
from webui.services.api_client import APIClient
