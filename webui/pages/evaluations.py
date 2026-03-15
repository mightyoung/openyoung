"""
Evaluation Page - Evaluation results and metrics display

Based on Streamlit best practices for data visualization:
- Uses st.metrics for key metrics
- Uses charts for trend visualization
- Provides filtering and search capabilities
"""

import streamlit as st
from webui.utils.config import config


def render():
    """Render evaluation page"""
    st.title("📊 Evaluation")

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

    # Display metrics
    st.markdown("### Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Evaluations", total)

    with col2:
        passed_count = sum(1 for e in evaluations if e.get("passed"))
        st.metric("Passed", passed_count)

    with col3:
        failed_count = sum(1 for e in evaluations if not e.get("passed"))
        st.metric("Failed", failed_count)

    with col4:
        avg_score = (
            sum(e.get("score", 0) for e in evaluations) / len(evaluations)
            if evaluations
            else 0
        )
        st.metric("Avg Score", f"{avg_score:.2%}")

    st.markdown("---")

    # Display evaluation list
    st.markdown("### Evaluation Results")

    if evaluations:
        # Create a table-like display
        for eval_record in evaluations:
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 2, 1, 1])

                with col1:
                    st.markdown(f"**{eval_record.get('evaluation_id', 'N/A')}**")
                    st.caption(f"Execution: {eval_record.get('execution_id', 'N/A')}")

                with col2:
                    st.markdown(f"Type: {eval_record.get('evaluator_type', 'N/A')}")
                    st.caption(f"Time: {eval_record.get('created_at', 'N/A')}")

                with col3:
                    score = eval_record.get("score", 0)
                    st.metric("Score", f"{score:.2%}")

                with col4:
                    passed = eval_record.get("passed", False)
                    if passed:
                        st.success("✓ Passed")
                    else:
                        st.error("✗ Failed")

                st.markdown("---")
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
            with st.container():
                col1, col2, col3 = st.columns([2, 2, 1])

                with col1:
                    st.markdown(f"**{exec_record.get('execution_id', 'N/A')}**")

                with col2:
                    st.markdown(f"Agent: {exec_record.get('agent_name', 'N/A')}")
                    st.caption(f"Time: {exec_record.get('created_at', 'N/A')}")

                with col3:
                    status = exec_record.get("status", "unknown")
                    if status == "success":
                        st.success(f"✓ {status}")
                    elif status == "failed":
                        st.error(f"✗ {status}")
                    elif status == "running":
                        st.info(f"⟳ {status}")
                    else:
                        st.warning(f"○ {status}")

                st.markdown("---")
    else:
        st.info("No execution records found")


# Import for type hints
from webui.services.api_client import APIClient
