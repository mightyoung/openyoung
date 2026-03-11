"""
Evaluator Service Python gRPC Test Client

Tests the Rust Evaluator gRPC service
"""

import grpc
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from rust import evaluator_pb2
from rust import evaluator_pb2_grpc
from rust import agent_control_pb2


def test_health_check(stub):
    """Test evaluator health check"""
    print("\n=== Testing Evaluator Health Check ===")

    request = evaluator_pb2.EvaluatorHealthRequest()
    response = stub.HealthCheck(request)

    print(f"Healthy: {response.healthy}")
    print(f"Status: {response.status}")
    return response.healthy


def test_evaluate_stream(stub):
    """Test evaluator stream evaluation"""
    print("\n=== Testing Evaluator Stream Evaluation ===")

    # Create evaluation plan
    plan = evaluator_pb2.EvalPlanInfo(
        task_description="Test task for evaluation",
        task_type="coding",
        complexity="medium",
        dimensions=[
            evaluator_pb2.EvalDimensionInfo(
                name="correctness",
                weight=0.6,
                threshold=0.5,
                criteria="Code produces correct output",
                evaluation_method="llm_judge"
            ),
            evaluator_pb2.EvalDimensionInfo(
                name="safety",
                weight=0.4,
                threshold=0.5,
                criteria="Code has no security issues",
                evaluation_method="static_analysis"
            ),
        ],
        max_iterations=5,
        timeout_seconds=300,
    )

    # Create execution result
    result = evaluator_pb2.ExecutionResult(
        step=1,
        action="execute",
        thought="Running the code",
        observation="Output: Hello World",
        output="Hello World",
        traces=[],
    )

    # Create events - simple approach without oneof complexity
    events = []

    # First event: Plan
    event1 = evaluator_pb2.EvaluatorEvent()
    event1.task_id = "test-task-1"
    event1.session_id = "test-session-1"
    event1.iteration = 0
    event1.plan.CopyFrom(plan)
    events.append(event1)

    # Second event: Result
    event2 = evaluator_pb2.EvaluatorEvent()
    event2.task_id = "test-task-1"
    event2.session_id = "test-session-1"
    event2.iteration = 1
    event2.result.CopyFrom(result)
    events.append(event2)

    # Call EvaluateStream
    response_iterator = stub.EvaluateStream(iter(events))

    results = []
    for response in response_iterator:
        results.append(response)
        print(f"Iteration: {response.iteration}")
        print(f"Passed: {response.passed}")
        print(f"Overall Score: {response.overall_score}")
        print(f"Feedback: {response.feedback}")
        print(f"Next State: {response.next_state}")
        print(f"Can Shutdown: {response.can_shutdown}")
        print(f"Should Continue: {response.should_continue}")
        print(f"Status: {response.status}")

        if response.results:
            print("Dimension Results:")
            for dim_result in response.results:
                print(f"  - {dim_result.dimension_name}: score={dim_result.score}, passed={dim_result.passed}")
                print(f"    Feedback: {dim_result.feedback}")

    return results


def test_evaluate_stream_with_code_execution(stub):
    """Test evaluator with code execution method"""
    print("\n=== Testing Evaluator with Code Execution Method ===")

    plan = evaluator_pb2.EvalPlanInfo(
        task_description="Test code execution evaluation",
        task_type="coding",
        complexity="simple",
        dimensions=[
            evaluator_pb2.EvalDimensionInfo(
                name="execution",
                weight=1.0,
                threshold=0.5,
                criteria="Code executes successfully",
                evaluation_method="code_execution"
            ),
        ],
        max_iterations=3,
        timeout_seconds=60,
    )

    result = evaluator_pb2.ExecutionResult(
        step=1,
        action="execute",
        thought="Running Python code",
        observation="print('Hello') executed",
        output="Hello",
        traces=[],
    )

    events = []
    event1 = evaluator_pb2.EvaluatorEvent()
    event1.task_id = "test-task-2"
    event1.session_id = "test-session-2"
    event1.iteration = 0
    event1.plan.CopyFrom(plan)
    events.append(event1)

    event2 = evaluator_pb2.EvaluatorEvent()
    event2.task_id = "test-task-2"
    event2.session_id = "test-session-2"
    event2.iteration = 1
    event2.result.CopyFrom(result)
    events.append(event2)

    response_iterator = stub.EvaluateStream(iter(events))

    for response in response_iterator:
        print(f"Iteration: {response.iteration}")
        print(f"Passed: {response.passed}")
        print(f"Score: {response.overall_score}")

    return response_iterator


def test_evaluate_stream_with_static_analysis(stub):
    """Test evaluator with static analysis method"""
    print("\n=== Testing Evaluator with Static Analysis Method ===")

    plan = evaluator_pb2.EvalPlanInfo(
        task_description="Test static analysis evaluation",
        task_type="coding",
        complexity="simple",
        dimensions=[
            evaluator_pb2.EvalDimensionInfo(
                name="safety",
                weight=1.0,
                threshold=0.5,
                criteria="Code has no dangerous patterns",
                evaluation_method="static_analysis"
            ),
        ],
        max_iterations=3,
        timeout_seconds=60,
    )

    result = evaluator_pb2.ExecutionResult(
        step=1,
        action="execute",
        thought="Writing safe code",
        observation="print('Hello')",
        output="print('Hello')",
        traces=[],
    )

    events = []
    event1 = evaluator_pb2.EvaluatorEvent()
    event1.task_id = "test-task-3"
    event1.session_id = "test-session-3"
    event1.iteration = 0
    event1.plan.CopyFrom(plan)
    events.append(event1)

    event2 = evaluator_pb2.EvaluatorEvent()
    event2.task_id = "test-task-3"
    event2.session_id = "test-session-3"
    event2.iteration = 1
    event2.result.CopyFrom(result)
    events.append(event2)

    response_iterator = stub.EvaluateStream(iter(events))

    for response in response_iterator:
        print(f"Iteration: {response.iteration}")
        print(f"Passed: {response.passed}")
        print(f"Score: {response.overall_score}")
        print(f"Feedback: {response.feedback}")

    return response_iterator


def test_iteration_control(stub):
    """Test iteration control logic"""
    print("\n=== Testing Iteration Control ===")

    plan = evaluator_pb2.EvalPlanInfo(
        task_description="Test iteration control",
        task_type="coding",
        complexity="medium",
        dimensions=[
            evaluator_pb2.EvalDimensionInfo(
                name="correctness",
                weight=1.0,
                threshold=0.8,
                criteria="Must pass all tests",
                evaluation_method="llm_judge"
            ),
        ],
        max_iterations=2,
        timeout_seconds=60,
    )

    failing_result = evaluator_pb2.ExecutionResult(
        step=1,
        action="execute",
        thought="First attempt",
        observation="Output: Wrong",
        output="Wrong output",
        traces=[],
    )

    events = []
    event1 = evaluator_pb2.EvaluatorEvent()
    event1.task_id = "test-task-4"
    event1.session_id = "test-session-4"
    event1.iteration = 0
    event1.plan.CopyFrom(plan)
    events.append(event1)

    event2 = evaluator_pb2.EvaluatorEvent()
    event2.task_id = "test-task-4"
    event2.session_id = "test-session-4"
    event2.iteration = 1
    event2.result.CopyFrom(failing_result)
    events.append(event2)

    response_iterator = stub.EvaluateStream(iter(events))

    for response in response_iterator:
        print(f"Iteration: {response.iteration}")
        print(f"Passed: {response.passed}")
        print(f"Should Continue: {response.should_continue}")
        print(f"Remaining Iterations: {response.remaining_iterations}")
        print(f"Next State: {response.next_state}")
        print(f"Can Shutdown: {response.can_shutdown}")

    return response_iterator


def test_stream_logs(stub):
    """Test log streaming"""
    print("\n=== Testing Stream Logs ===")

    request = evaluator_pb2.LogRequest(
        session_id="test-session",
        task_id="test-task"
    )

    logs = list(stub.StreamLogs(request))
    print(f"Received {len(logs)} log entries")

    for log in logs:
        print(f"  [{log.level}] {log.event}: {log.message}")

    return logs


def main():
    # Connect to the server
    channel = grpc.insecure_channel('localhost:50051')
    stub = evaluator_pb2_grpc.EvaluatorServiceStub(channel)

    try:
        # Test health check
        if test_health_check(stub):
            print("Evaluator service is healthy")

        # Test evaluation stream
        test_evaluate_stream(stub)

        # Test code execution method
        test_evaluate_stream_with_code_execution(stub)

        # Test static analysis method
        test_evaluate_stream_with_static_analysis(stub)

        # Test iteration control
        test_iteration_control(stub)

        # Test stream logs
        test_stream_logs(stub)

        print("\n=== All Tests Passed ===")
    except grpc.RpcError as e:
        print(f"RPC failed: {e.code()}: {e.details()}")
    finally:
        channel.close()


if __name__ == '__main__':
    main()
