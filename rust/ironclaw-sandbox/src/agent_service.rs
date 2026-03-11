//! Agent Control Service - Agent 生命周期控制
//!
//! 基于分布式系统最佳实践设计:
//! - Leslie Lamport: 状态机模式
//! - Rob Pike: 简洁清晰
//! - Rust: 内存安全 + 无畏并发

use std::sync::Arc;
use std::collections::HashMap;

use tokio::sync::RwLock;
use tonic::{Request, Response, Status};
use tokio_stream::Stream;
use tracing::info;
use chrono::Utc;
use serde::{Deserialize, Serialize};

// Re-export from server module
use super::ironclaw::{
    agent_control_service_server::AgentControlService,
    AgentRequest, AgentState, TraceEntry,
    EvaluationResultRequest, EvaluationResultResponse,
    ShutdownRequest, ShutdownResponse,
    HealthCheckRequest, HealthCheckResponse,
    EvaluationPlan, AgentConfig,
};

// ============================================================
// Agent 状态管理
// ============================================================

/// Agent 运行状态
#[derive(Clone, Copy, Debug, PartialEq, Serialize, Deserialize)]
pub enum AgentRunStatus {
    Initializing,
    Running,
    Evaluating,
    Completed,
    Failed,
    ShutdownRequested,
}

/// 从 AgentRunStatus 转换为 i32 (proto3 风格)
impl From<AgentRunStatus> for i32 {
    fn from(s: AgentRunStatus) -> Self {
        match s {
            AgentRunStatus::Initializing => 1,
            AgentRunStatus::Running => 2,
            AgentRunStatus::Evaluating => 3,
            AgentRunStatus::Completed => 4,
            AgentRunStatus::Failed => 5,
            AgentRunStatus::ShutdownRequested => 7,
        }
    }
}

/// 单个 Agent 实例的状态
#[derive(Clone, Debug)]
pub struct AgentInstance {
    pub task_id: String,
    pub task_description: String,
    pub eval_plan: Option<EvaluationPlan>,
    pub config: Option<AgentConfig>,
    pub status: AgentRunStatus,
    pub current_step: i32,
    pub traces: Vec<TraceEntry>,
    pub output: String,
    pub created_at: i64,
    pub can_shutdown: bool,
}

impl AgentInstance {
    pub fn new(task_id: String, task_description: String) -> Self {
        Self {
            task_id,
            task_description,
            eval_plan: None,
            config: None,
            status: AgentRunStatus::Initializing,
            current_step: 0,
            traces: Vec::new(),
            output: String::new(),
            created_at: Utc::now().timestamp(),
            can_shutdown: false,
        }
    }

    /// 转换为 Proto 消息
    pub fn to_proto_state(&self) -> AgentState {
        AgentState {
            task_id: self.task_id.clone(),
            status: i32::from(self.status.clone()),
            current_step: self.current_step,
            current_action: self.traces.last()
                .map(|t| t.action.clone())
                .unwrap_or_default(),
            traces: self.traces.clone(),
            output: self.output.clone(),
            timestamp: Utc::now().timestamp(),
        }
    }
}

/// Agent 服务状态
pub struct AgentServiceState {
    pub agents: HashMap<String, AgentInstance>,
    pub current_task_id: Option<String>,
}

impl Default for AgentServiceState {
    fn default() -> Self {
        Self {
            agents: HashMap::new(),
            current_task_id: None,
        }
    }
}

// ============================================================
// Agent 服务实现
// ============================================================

#[derive(Clone)]
pub struct AgentServiceImpl {
    state: Arc<RwLock<AgentServiceState>>,
}

impl AgentServiceImpl {
    pub fn new() -> Self {
        Self {
            state: Arc::new(RwLock::new(AgentServiceState::default())),
        }
    }

    /// 设置 Agent 状态
    async fn set_status(&self, task_id: &str, status: AgentRunStatus) {
        let mut state = self.state.write().await;
        if let Some(agent) = state.agents.get_mut(task_id) {
            agent.status = status;
            info!("Agent {} status changed to {:?}", task_id, status);
        }
    }

    /// 获取 Agent
    async fn get_agent(&self, task_id: &str) -> Option<AgentInstance> {
        let state = self.state.read().await;
        state.agents.get(task_id).cloned()
    }
}

impl Default for AgentServiceImpl {
    fn default() -> Self {
        Self::new()
    }
}

/// 简化的评估维度解析
#[derive(Debug, Clone, Serialize, Deserialize)]
struct EvalDimensionJson {
    name: String,
    weight: f32,
    threshold: f32,
    criteria: String,
    evaluation_method: String,
    scoring_reason: String,
}

/// 简化的评估计划解析
#[derive(Debug, Clone, Serialize, Deserialize)]
struct EvalPlanJson {
    task_type: String,
    complexity: String,
    skip_evaluation: bool,
    dimensions: Vec<EvalDimensionJson>,
    max_iterations: i32,
    timeout_seconds: i32,
}

/// 简化的配置解析
#[derive(Debug, Clone, Serialize, Deserialize)]
struct AgentConfigJson {
    agent_type: String,
    model: String,
    max_steps: i32,
    environment: HashMap<String, String>,
}

// ============================================================
// 状态流实现
// ============================================================

/// Agent 状态流
pub struct AgentStateStream {
    states: Vec<AgentState>,
    index: usize,
}

impl AgentStateStream {
    fn new(states: Vec<AgentState>) -> Self {
        Self { states, index: 0 }
    }
}

impl Stream for AgentStateStream {
    type Item = Result<AgentState, Status>;

    fn poll_next(
        mut self: std::pin::Pin<&mut Self>,
        _cx: &mut std::task::Context<'_>,
    ) -> std::task::Poll<Option<Self::Item>> {
        if self.index < self.states.len() {
            let state = self.states[self.index].clone();
            self.index += 1;
            std::task::Poll::Ready(Some(Ok(state)))
        } else {
            std::task::Poll::Ready(None)
        }
    }
}

#[tonic::async_trait]
impl AgentControlService for AgentServiceImpl {
    /// 定义流类型
    type StartAgentStream = AgentStateStream;

    /// 启动 Agent 并返回状态流
    async fn start_agent(
        &self,
        request: Request<AgentRequest>,
    ) -> Result<Response<Self::StartAgentStream>, Status> {
        let req = request.into_inner();
        let task_id = req.task_id.clone();
        let task_description = req.task_description.clone();

        info!("Starting agent for task: {} - {}", task_id, task_description);

        // 直接使用 proto 消息
        let eval_plan = req.eval_plan;
        let config = req.config;

        // 创建 Agent 实例
        let mut agent = AgentInstance::new(task_id.clone(), task_description);
        agent.eval_plan = eval_plan;
        agent.config = config;
        agent.status = AgentRunStatus::Running;

        // 注册 Agent
        {
            let mut state = self.state.write().await;
            state.agents.insert(task_id.clone(), agent);
            state.current_task_id = Some(task_id.clone());
        }

        // 获取状态
        let state = self.get_agent(&task_id).await
            .ok_or_else(|| Status::not_found("Agent not found"))?;

        // 创建状态流
        let states = vec![state.to_proto_state()];
        let stream = AgentStateStream::new(states);

        Ok(Response::new(stream))
    }

    /// 提交评估结果
    async fn submit_evaluation_result(
        &self,
        request: Request<EvaluationResultRequest>,
    ) -> Result<Response<EvaluationResultResponse>, Status> {
        let req = request.into_inner();
        let task_id = &req.task_id;

        info!("Received evaluation result for task {}: passed={}, score={}",
            task_id, req.passed, req.overall_score);

        // 获取并更新 Agent
        let can_shutdown = req.passed && !req.blocking_failed;

        if can_shutdown {
            self.set_status(task_id, AgentRunStatus::Completed).await;
        } else {
            self.set_status(task_id, AgentRunStatus::Running).await;
        }

        // 更新 Agent 的 can_shutdown 标志
        {
            let mut state = self.state.write().await;
            if let Some(agent) = state.agents.get_mut(task_id) {
                agent.can_shutdown = can_shutdown;
            }
        }

        Ok(Response::new(EvaluationResultResponse {
            accepted: true,
            message: if can_shutdown {
                "评估通过，容器可以关闭".to_string()
            } else {
                "评估失败，等待重试".to_string()
            },
            can_shutdown,
        }))
    }

    /// 请求关闭
    async fn request_shutdown(
        &self,
        request: Request<ShutdownRequest>,
    ) -> Result<Response<ShutdownResponse>, Status> {
        let req = request.into_inner();
        let task_id = &req.task_id;

        info!("Shutdown requested for task {}: reason={}", task_id, req.reason);

        self.set_status(task_id, AgentRunStatus::ShutdownRequested).await;

        // 确定退出码
        let exit_code = match req.reason {
            1 => 0, // Success
            5 => 1, // EvaluationFailed
            2 => 2, // MaxIterations
            3 => 3, // Timeout
            _ => 4,
        };

        Ok(Response::new(ShutdownResponse {
            success: true,
            message: "容器已关闭".to_string(),
            exit_code,
        }))
    }

    /// 健康检查
    async fn health_check(
        &self,
        _request: Request<HealthCheckRequest>,
    ) -> Result<Response<HealthCheckResponse>, Status> {
        let state = self.state.read().await;

        let active_agents = state.agents.len();
        let status = if active_agents > 0 {
            format!("Running {} agent(s)", active_agents)
        } else {
            "Idle".to_string()
        };

        Ok(Response::new(HealthCheckResponse {
            healthy: true,
            status,
        }))
    }
}

// ============================================================
// 便捷函数
// ============================================================

pub fn create_agent_service() -> AgentServiceImpl {
    AgentServiceImpl::new()
}
