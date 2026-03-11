//! Session Management - 会话管理模块
//!
//! 管理评估会话的生命周期
//! 基于 Leslie Lamport 状态机原则

use crate::ironclaw::{EvalPlanInfo, ExecutionResult};

/// 评估器状态
#[derive(Debug, Clone, PartialEq)]
pub enum EvaluatorStatus {
    Idle,
    Running,
    Evaluating,
    Completed,
    Failed,
}

/// 评估会话状态
#[derive(Clone)]
pub struct EvalSession {
    pub task_id: String,
    pub session_id: String,
    pub plan: Option<EvalPlanInfo>,
    pub current_iteration: i32,
    pub status: EvaluatorStatus,
    pub latest_result: Option<ExecutionResult>,
}

impl EvalSession {
    pub fn new(task_id: String, session_id: String) -> Self {
        Self {
            task_id,
            session_id,
            plan: None,
            current_iteration: 0,
            status: EvaluatorStatus::Idle,
            latest_result: None,
        }
    }

    /// 更新会话状态
    pub fn set_status(&mut self, status: EvaluatorStatus) {
        self.status = status;
    }

    /// 设置评估计划
    pub fn set_plan(&mut self, plan: EvalPlanInfo) {
        self.plan = Some(plan);
        self.status = EvaluatorStatus::Running;
    }

    /// 更新迭代次数
    pub fn increment_iteration(&mut self) {
        self.current_iteration += 1;
    }

    /// 更新最新结果
    pub fn update_result(&mut self, result: ExecutionResult) {
        self.latest_result = Some(result);
    }

    /// 检查会话是否已完成
    pub fn is_completed(&self) -> bool {
        matches!(
            self.status,
            EvaluatorStatus::Completed | EvaluatorStatus::Failed
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_session_creation() {
        let session = EvalSession::new("task-1".to_string(), "session-1".to_string());
        assert_eq!(session.task_id, "task-1");
        assert_eq!(session.session_id, "session-1");
        assert_eq!(session.status, EvaluatorStatus::Idle);
        assert_eq!(session.current_iteration, 0);
    }

    #[test]
    fn test_session_status_transition() {
        let mut session = EvalSession::new("task-1".to_string(), "session-1".to_string());
        session.set_status(EvaluatorStatus::Running);
        assert_eq!(session.status, EvaluatorStatus::Running);
    }

    #[test]
    fn test_session_iteration() {
        let mut session = EvalSession::new("task-1".to_string(), "session-1".to_string());
        assert_eq!(session.current_iteration, 0);
        session.increment_iteration();
        assert_eq!(session.current_iteration, 1);
        session.increment_iteration();
        assert_eq!(session.current_iteration, 2);
    }

    #[test]
    fn test_session_completed() {
        let mut session = EvalSession::new("task-1".to_string(), "session-1".to_string());
        assert!(!session.is_completed());

        session.set_status(EvaluatorStatus::Completed);
        assert!(session.is_completed());

        let mut session2 = EvalSession::new("task-2".to_string(), "session-2".to_string());
        session2.set_status(EvaluatorStatus::Failed);
        assert!(session2.is_completed());
    }
}
