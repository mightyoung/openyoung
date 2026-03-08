"""
DataIntegration - 数据追踪集成
将 RunTracker、StepRecorder 集成到 Agent 执行流程
"""

from datetime import datetime


class DataTrackerMixin:
    """数据追踪 Mixin - 混入 Agent 类实现自动追踪"""

    def __init__(self):
        self._run_tracker = None
        self._step_recorder = None
        self._current_run_id: str | None = None
        self._current_step_id: str | None = None
        self._data_dir: str = ".young"

    def enable_tracking(self, data_dir: str = ".young"):
        """启用数据追踪"""
        self._data_dir = data_dir

        # 延迟导入避免循环依赖
        from .run_tracker import RunTracker
        from .step_recorder import StepRecorder

        self._run_tracker = RunTracker(f"{data_dir}/runs.db")
        self._step_recorder = StepRecorder(f"{data_dir}/steps.db")

    def start_run_tracking(
        self,
        agent_id: str,
        task: str,
        metadata: dict = None
    ) -> str:
        """开始运行追踪"""
        if not self._run_tracker:
            return None

        run_id = self._run_tracker.start_run(
            agent_id=agent_id,
            task=task,
            metadata=metadata
        )
        self._current_run_id = run_id
        return run_id

    def complete_run_tracking(
        self,
        status: str = "success",
        error: str = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        metadata: dict = None
    ) -> bool:
        """完成运行追踪"""
        if not self._run_tracker or not self._current_run_id:
            return False

        result = self._run_tracker.complete_run(
            run_id=self._current_run_id,
            status=status,
            error=error,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            metadata=metadata
        )
        self._current_run_id = None
        return result

    def fail_run_tracking(self, error: str) -> bool:
        """标记运行失败"""
        if not self._run_tracker or not self._current_run_id:
            return False
        return self._run_tracker.fail_run(self._current_run_id, error)

    def start_step_tracking(
        self,
        step_name: str,
        step_order: int,
        tool_name: str = "",
        input_data: dict = None
    ) -> str:
        """开始步骤追踪"""
        if not self._step_recorder or not self._current_run_id:
            return None

        step_id = self._step_recorder.start_step(
            run_id=self._current_run_id,
            step_name=step_name,
            step_order=step_order,
            tool_name=tool_name,
            input_data=input_data
        )
        self._current_step_id = step_id
        return step_id

    def complete_step_tracking(
        self,
        status: str = "success",
        output_data: dict = None,
        latency_ms: int = 0,
        error: str = None
    ) -> bool:
        """完成步骤追踪"""
        if not self._step_recorder or not self._current_step_id:
            return False

        result = self._step_recorder.complete_step(
            step_id=self._current_step_id,
            status=status,
            output_data=output_data,
            latency_ms=latency_ms,
            error=error
        )
        self._current_step_id = None
        return result

    def fail_step_tracking(self, error: str) -> bool:
        """标记步骤失败"""
        if not self._step_recorder or not self._current_step_id:
            return False
        return self._step_recorder.fail_step(self._current_step_id, error)


class TrackingContext:
    """追踪上下文管理器"""

    def __init__(self, tracker: DataTrackerMixin, step_name: str, step_order: int, tool_name: str = ""):
        self._tracker = tracker
        self._step_name = step_name
        self._step_order = step_order
        self._tool_name = tool_name
        self._start_time: datetime | None = None

    async def __aenter__(self):
        self._start_time = datetime.now()

        # 开始步骤追踪
        from datetime import datetime
        input_data = {"started_at": datetime.now().isoformat()}

        if self._tracker._current_run_id:
            self._tracker.start_step_tracking(
                step_name=self._step_name,
                step_order=self._step_order,
                tool_name=self._tool_name,
                input_data=input_data
            )

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # 计算延迟
        latency_ms = 0
        if self._start_time:
            latency_ms = int((datetime.now() - self._start_time).total_seconds() * 1000)

        # 根据异常判断状态
        if exc_type is not None:
            # 有异常，标记失败
            self._tracker.fail_step_tracking(str(exc_val))
        else:
            # 正常完成
            self._tracker.complete_step_tracking(
                status="success",
                output_data={"completed_at": datetime.now().isoformat()},
                latency_ms=latency_ms
            )


# ========== 便捷函数 ==========

def track_step(tracker: DataTrackerMixin, step_name: str, step_order: int, tool_name: str = ""):
    """步骤追踪上下文管理器（同步版本）"""
    return TrackingContext(tracker, step_name, step_order, tool_name)
