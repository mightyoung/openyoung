//! Structured Logging - 结构化日志
//!
//! 基于 Cindy Sridharan 的可观测性原则
//! JSON 格式输出，便于日志聚合和分析

use serde::Serialize;
use tracing::Level;
use std::fmt;

/// 日志事件级别
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "lowercase")]
pub enum LogLevel {
    Trace,
    Debug,
    Info,
    Warn,
    Error,
}

impl From<tracing::Level> for LogLevel {
    fn from(level: Level) -> Self {
        match level {
            Level::TRACE => LogLevel::Trace,
            Level::DEBUG => LogLevel::Debug,
            Level::INFO => LogLevel::Info,
            Level::WARN => LogLevel::Warn,
            Level::ERROR => LogLevel::Error,
        }
    }
}

/// 日志组件类型
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum Component {
    TargetAgent,
    Evaluator,
    LlmMiddleware,
    CircuitBreaker,
    Security,
}

impl fmt::Display for Component {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Component::TargetAgent => write!(f, "target_agent"),
            Component::Evaluator => write!(f, "evaluator"),
            Component::LlmMiddleware => write!(f, "llm_middleware"),
            Component::CircuitBreaker => write!(f, "circuit_breaker"),
            Component::Security => write!(f, "security"),
        }
    }
}

/// 关键事件类型
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum EventType {
    // Target Agent 事件
    AgentStarted,
    AgentThinking,
    AgentAction,
    AgentObservation,
    AgentCompleted,

    // Evaluator 事件
    EvaluatorStarted,
    EvaluatorDimension,
    EvaluatorIteration,
    EvaluatorCompleted,

    // 迭代事件
    IterationPassed,
    IterationFailed,
    MaxIterationsReached,

    // 任务事件
    TaskSuccess,
    TaskFailed,

    // LLM 事件
    LlmCallStarted,
    LlmCallCompleted,
    LlmCallFailed,

    // 熔断器事件
    CircuitOpened,
    CircuitClosed,
    CircuitHalfOpen,
}

impl fmt::Display for EventType {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            EventType::AgentStarted => write!(f, "agent_started"),
            EventType::AgentThinking => write!(f, "agent_thinking"),
            EventType::AgentAction => write!(f, "agent_action"),
            EventType::AgentObservation => write!(f, "agent_observation"),
            EventType::AgentCompleted => write!(f, "agent_completed"),
            EventType::EvaluatorStarted => write!(f, "evaluator_started"),
            EventType::EvaluatorDimension => write!(f, "evaluator_dimension"),
            EventType::EvaluatorIteration => write!(f, "evaluator_iteration"),
            EventType::EvaluatorCompleted => write!(f, "evaluator_completed"),
            EventType::IterationPassed => write!(f, "iteration_passed"),
            EventType::IterationFailed => write!(f, "iteration_failed"),
            EventType::MaxIterationsReached => write!(f, "max_iterations_reached"),
            EventType::TaskSuccess => write!(f, "task_success"),
            EventType::TaskFailed => write!(f, "task_failed"),
            EventType::LlmCallStarted => write!(f, "llm_call_started"),
            EventType::LlmCallCompleted => write!(f, "llm_call_completed"),
            EventType::LlmCallFailed => write!(f, "llm_call_failed"),
            EventType::CircuitOpened => write!(f, "circuit_opened"),
            EventType::CircuitClosed => write!(f, "circuit_closed"),
            EventType::CircuitHalfOpen => write!(f, "circuit_half_open"),
        }
    }
}

/// 结构化日志事件
#[derive(Debug, Clone, Serialize)]
pub struct LogEvent {
    /// 时间戳 (ISO 8601)
    pub timestamp: String,
    /// 日志级别
    pub level: LogLevel,
    /// 组件
    pub component: Component,
    /// 事件类型
    pub event: EventType,
    /// 追踪 ID
    #[serde(skip_serializing_if = "Option::is_none")]
    pub trace_id: Option<String>,
    /// 会话 ID
    #[serde(skip_serializing_if = "Option::is_none")]
    pub session_id: Option<String>,
    /// 迭代次数
    #[serde(skip_serializing_if = "Option::is_none")]
    pub iteration: Option<i32>,
    /// 附加数据
    #[serde(skip_serializing_if = "Option::is_none")]
    pub data: Option<serde_json::Value>,
}

impl LogEvent {
    /// 创建新的日志事件
    pub fn new(
        level: LogLevel,
        component: Component,
        event: EventType,
    ) -> Self {
        Self {
            timestamp: chrono::Utc::now().to_rfc3339(),
            level,
            component,
            event,
            trace_id: None,
            session_id: None,
            iteration: None,
            data: None,
        }
    }

    /// 设置追踪 ID
    pub fn with_trace_id(mut self, trace_id: impl Into<String>) -> Self {
        self.trace_id = Some(trace_id.into());
        self
    }

    /// 设置会话 ID
    pub fn with_session_id(mut self, session_id: impl Into<String>) -> Self {
        self.session_id = Some(session_id.into());
        self
    }

    /// 设置迭代次数
    pub fn with_iteration(mut self, iteration: i32) -> Self {
        self.iteration = Some(iteration);
        self
    }

    /// 设置附加数据
    pub fn with_data<T: Serialize>(mut self, data: &T) -> Self {
        self.data = serde_json::to_value(data).ok();
        self
    }

    /// 输出 JSON 字符串
    pub fn to_json(&self) -> String {
        serde_json::to_string(self).unwrap_or_default()
    }
}

// Note: LogRecorder trait removed for simplicity
// Use MemoryLogRecorder directly

/// 内存日志记录器
pub struct MemoryLogRecorder {
    sender: tokio::sync::mpsc::Sender<LogEvent>,
}

impl MemoryLogRecorder {
    pub fn new(buffer_size: usize) -> Self {
        let (sender, _receiver) = tokio::sync::mpsc::channel(buffer_size);
        Self { sender }
    }

    /// 记录日志事件
    pub fn record(&self, event: &LogEvent) {
        let _ = self.sender.try_send(event.clone());
    }
}

/// 便捷函数：创建日志事件
pub fn log_event(
    level: LogLevel,
    component: Component,
    event: EventType,
) -> LogEvent {
    LogEvent::new(level, component, event)
}

/// 评估迭代日志
pub fn log_evaluation_iteration(
    iteration: i32,
    passed: bool,
    score: f32,
    trace_id: &str,
) -> LogEvent {
    let (level, event) = if passed {
        (LogLevel::Info, EventType::IterationPassed)
    } else {
        (LogLevel::Warn, EventType::IterationFailed)
    };

    let data = serde_json::json!({
        "score": score,
        "passed": passed
    });

    LogEvent::new(level, Component::Evaluator, event)
        .with_trace_id(trace_id)
        .with_iteration(iteration)
        .with_data(&data)
}

/// 任务完成日志
pub fn log_task_completion(
    success: bool,
    total_iterations: i32,
    final_score: f32,
    trace_id: &str,
) -> LogEvent {
    let event = if success {
        EventType::TaskSuccess
    } else {
        EventType::TaskFailed
    };

    let level = if success { LogLevel::Info } else { LogLevel::Error };

    let data = serde_json::json!({
        "total_iterations": total_iterations,
        "final_score": final_score
    });

    LogEvent::new(level, Component::Evaluator, event)
        .with_trace_id(trace_id)
        .with_data(&data)
}

/// 发射结构化日志到 stdout (JSON 格式)
/// 供 Python log_consumer 消费
pub fn emit_structured_log(event: &LogEvent) {
    println!("{}", event.to_json());
}

/// 便捷函数：发射评估迭代日志
pub fn emit_evaluation_iteration(
    iteration: i32,
    passed: bool,
    score: f32,
    trace_id: &str,
) {
    let log = log_evaluation_iteration(iteration, passed, score, trace_id);
    emit_structured_log(&log);
}

/// 便捷函数：发射任务完成日志
pub fn emit_task_completion(
    success: bool,
    total_iterations: i32,
    final_score: f32,
    trace_id: &str,
) {
    let log = log_task_completion(success, total_iterations, final_score, trace_id);
    emit_structured_log(&log);
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_log_event_creation() {
        let event = LogEvent::new(
            LogLevel::Info,
            Component::Evaluator,
            EventType::EvaluatorStarted,
        );

        assert_eq!(event.level, LogLevel::Info);
        assert_eq!(event.component, Component::Evaluator);
        assert_eq!(event.event, EventType::EvaluatorStarted);
    }

    #[test]
    fn test_log_event_to_json() {
        let event = LogEvent::new(
            LogLevel::Info,
            Component::Evaluator,
            EventType::EvaluatorStarted,
        )
        .with_trace_id("task-123")
        .with_iteration(1);

        let json = event.to_json();
        assert!(json.contains("task-123"));
        assert!(json.contains("evaluator_started"));
    }
}
