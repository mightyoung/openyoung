//! External Evaluator Service - 外部评估器服务
//!
//! 基于 Leslie Lamport 状态机设计:
//! - 迭代状态在 Evaluator 内部闭环
//! - 无状态设计，支持横向扩展
//! - 基于 Rob Pike 简洁接口原则
//!
//! 评估维度参考 OpenYoung 评估框架:
//! - correctness: 任务是否正确完成
//! - safety: 代码/输出安全性
//! - efficiency: 资源使用效率
//! - robustness: 边界条件处理

// 子模块
mod session;
mod dimension;
mod iterations;

pub use session::{EvalSession, EvaluatorStatus};
pub use dimension::DimensionEvaluator;
pub use iterations::{IterationController, IterationState, IterationResult};

use std::sync::Arc;
use std::collections::HashMap;

use tokio::sync::RwLock;
use tonic::{Request, Response, Status};
use tokio_stream::Stream;
use tracing::info;

use crate::ironclaw::{
    evaluator_service_server::EvaluatorService,
    EvaluatorEvent, EvalResponse, EvalPlanInfo, ExecutionResult,
    EvaluatorHealthRequest, EvaluatorHealthResponse, DimensionResult,
    LogRequest, LogEntry,
};

use crate::llm_middleware::{LLMMiddleware, LLMMiddlewareConfig, ModelConfig};
use crate::logging::{self, LogLevel, Component, EventType, LogEvent, emit_evaluation_iteration, emit_task_completion};

// ============================================================
// 评估器配置
// ============================================================

#[derive(Clone)]
pub struct EvaluatorConfig {
    pub max_iterations: i32,
    pub timeout_seconds: i32,
    pub llm_api_key: String,
    pub llm_endpoint: String,
    pub llm_model: String,
}

impl Default for EvaluatorConfig {
    fn default() -> Self {
        Self {
            max_iterations: 5,
            timeout_seconds: 300,
            llm_api_key: std::env::var("OPENAI_API_KEY").unwrap_or_default(),
            llm_endpoint: std::env::var("LLM_ENDPOINT")
                .unwrap_or_else(|_| "https://api.openai.com/v1/chat/completions".to_string()),
            llm_model: std::env::var("LLM_MODEL")
                .unwrap_or_else(|_| "claude-sonnet-4-20250514".to_string()),
        }
    }
}

// ============================================================
// 评估器服务实现
// ============================================================

#[derive(Clone)]
pub struct EvaluatorServiceImpl {
    config: EvaluatorConfig,
    sessions: Arc<RwLock<HashMap<String, EvalSession>>>,
    llm_middleware: Arc<LLMMiddleware>,
    dimension_evaluator: DimensionEvaluator,
    iteration_controller: IterationController,
}

impl EvaluatorServiceImpl {
    pub fn new(config: EvaluatorConfig) -> Self {
        let middleware_config = LLMMiddlewareConfig {
            target_model: ModelConfig {
                name: config.llm_model.clone(),
                endpoint: config.llm_endpoint.clone(),
                api_key: config.llm_api_key.clone(),
                ..Default::default()
            },
            evaluator_model: ModelConfig {
                name: config.llm_model.clone(),
                endpoint: config.llm_endpoint.clone(),
                api_key: config.llm_api_key.clone(),
                ..Default::default()
            },
            ..Default::default()
        };

        let llm_middleware = Arc::new(LLMMiddleware::new(middleware_config));
        let dimension_evaluator = DimensionEvaluator::new(llm_middleware.clone());
        let iteration_controller = IterationController::new(config.max_iterations);

        Self {
            config,
            sessions: Arc::new(RwLock::new(HashMap::new())),
            llm_middleware,
            dimension_evaluator,
            iteration_controller,
        }
    }

    /// 评估单个维度
    async fn evaluate_dimension(
        &self,
        dimension: &crate::ironclaw::EvalDimensionInfo,
        result: &ExecutionResult,
    ) -> DimensionResult {
        self.dimension_evaluator.evaluate(dimension, result).await
    }

    /// 评估所有维度
    async fn evaluate_all_dimensions(
        &self,
        dimensions: &[crate::ironclaw::EvalDimensionInfo],
        result: &ExecutionResult,
    ) -> Vec<DimensionResult> {
        let mut dim_results = Vec::new();
        for dim in dimensions {
            let dim_result = self.evaluate_dimension(dim, result).await;
            dim_results.push(dim_result);
        }
        dim_results
    }
}

// ============================================================
// 评估响应流 - 支持真正的迭代控制
// ============================================================

pub struct EvalResponseStream {
    responses: Vec<EvalResponse>,
    index: usize,
}

impl EvalResponseStream {
    pub fn new(responses: Vec<EvalResponse>) -> Self {
        Self { responses, index: 0 }
    }
}

impl Stream for EvalResponseStream {
    type Item = Result<EvalResponse, Status>;

    fn poll_next(
        mut self: std::pin::Pin<&mut Self>,
        _cx: &mut std::task::Context<'_>,
    ) -> std::task::Poll<Option<Self::Item>> {
        if self.index < self.responses.len() {
            let response = self.responses[self.index].clone();
            self.index += 1;
            std::task::Poll::Ready(Some(Ok(response)))
        } else {
            std::task::Poll::Ready(None)
        }
    }
}

// ============================================================
// 迭代评估器 - 真正的闭环迭代控制
// ============================================================

/// 迭代评估器：在 Rust 端内部完成迭代控制
/// 符合 Leslie Lamport 状态机设计原则
pub struct IterativeEvaluator {
    iteration_controller: IterationController,
    dimension_evaluator: DimensionEvaluator,
}

impl IterativeEvaluator {
    pub fn new(max_iterations: i32) -> Self {
        // 创建临时的 LLM middleware（实际使用时应注入）
        let config = crate::llm_middleware::LLMMiddlewareConfig::default();
        let llm_middleware = Arc::new(crate::llm_middleware::LLMMiddleware::new(config));
        let dimension_evaluator = DimensionEvaluator::new(llm_middleware);
        let iteration_controller = IterationController::new(max_iterations);

        Self {
            iteration_controller,
            dimension_evaluator,
        }
    }

    /// 执行单次迭代评估
    pub async fn evaluate_iteration(
        &self,
        task_id: &str,
        iteration: i32,
        dimensions: &[crate::ironclaw::EvalDimensionInfo],
        result: &ExecutionResult,
    ) -> EvalResponse {
        // 评估所有维度
        let mut dim_results = Vec::new();
        for dim in dimensions {
            let dim_result = self.dimension_evaluator.evaluate(dim, result).await;
            dim_results.push(dim_result);
        }

        // 使用迭代控制器构建响应
        self.iteration_controller.build_response(
            task_id,
            iteration,
            &dim_results,
            dimensions,
        )
    }
}

// ============================================================
// gRPC 服务实现 - 支持真正的迭代控制
// ============================================================

#[tonic::async_trait]
impl EvaluatorService for EvaluatorServiceImpl {
    type EvaluateStreamStream = EvalResponseStream;
    type StreamLogsStream = tokio_stream::wrappers::ReceiverStream<Result<LogEntry, Status>>;

    /// 评估流实现 - 真正的迭代控制
    ///
    /// 流程:
    /// 1. 接收评估计划 (plan)
    /// 2. 循环接收执行结果 (result):
    ///    - 立即评估
    ///    - 发送响应 (包含 should_continue)
    ///    - 如果 should_continue=true，继续接收下一个结果
    ///    - 如果 should_continue=false，结束迭代
    /// 3. 关闭流
    async fn evaluate_stream(
        &self,
        request: Request<tonic::Streaming<EvaluatorEvent>>,
    ) -> Result<Response<Self::EvaluateStreamStream>, Status> {
        info!("evaluate_stream called");

        let mut stream = request.into_inner();

        // 步骤1: 等待第一个事件（包含评估计划）
        let first_event = match stream.message().await {
            Ok(Some(event)) => {
                info!("Received first event: {:?}", event.task_id);
                event
            }
            Ok(None) => {
                info!("Empty stream received");
                return Err(Status::invalid_argument("Empty stream"))
            }
            Err(e) => {
                info!("Stream error: {:?}", e);
                return Err(Status::invalid_argument(format!("Stream error: {}", e)))
            }
        };

        let task_id = first_event.task_id.clone();
        let session_id = first_event.session_id.clone();

        // 创建会话并解析计划
        let mut session = EvalSession::new(task_id.clone(), session_id.clone());

        // 解析评估计划
        let mut plan: Option<crate::ironclaw::EvalPlanInfo> = None;
        if let Some(event_type) = first_event.event_type {
            match event_type {
                crate::ironclaw::evaluator_event::EventType::Plan(p) => {
                    plan = Some(p.clone());
                    session.set_plan(p);
                }
                _ => {}
            }
        }

        let plan = match plan {
            Some(p) => p,
            None => {
                return Err(Status::invalid_argument("First event must contain plan"));
            }
        };

        // 注册会话
        {
            let mut sessions = self.sessions.write().await;
            sessions.insert(task_id.clone(), session.clone());
        }

        info!("Started evaluation session for task: {} with max_iterations: {}",
              task_id, plan.max_iterations);

        // 步骤2: 迭代循环 - 接收结果 → 评估 → 响应
        let mut responses: Vec<EvalResponse> = Vec::new();
        let mut iteration = 0;

        // 创建迭代评估器
        let iterative_evaluator = IterativeEvaluator::new(plan.max_iterations);

        // 迭代循环：每次接收一个结果，评估后立即返回
        loop {
            match stream.message().await {
                Ok(Some(event)) => {
                    // 检查是否是结果事件
                    if let Some(event_type) = event.event_type {
                        if let crate::ironclaw::evaluator_event::EventType::Result(result) = event_type {
                            iteration = event.iteration;

                            // 立即评估当前结果
                            let response = iterative_evaluator
                                .evaluate_iteration(
                                    &task_id,
                                    iteration,
                                    &plan.dimensions,
                                    &result,
                                )
                                .await;

                            info!("Iteration {}: passed={}, should_continue={}, next_state={}",
                                  iteration, response.passed, response.should_continue, response.next_state);

                            // 保存需要的数据用于结构化日志
                            let passed = response.passed;
                            let overall_score = response.overall_score;
                            let should_continue = response.should_continue;

                            // 发射结构化日志 (供 Python log_consumer 消费)
                            emit_evaluation_iteration(
                                iteration,
                                passed,
                                overall_score,
                                &task_id,
                            );

                            responses.push(response);

                            // 如果不应继续，退出循环
                            let last_response = responses.last().unwrap();
                            if !last_response.should_continue {
                                info!("Iteration control: stopping at iteration {}", iteration);
                                // 发射任务完成日志
                                emit_task_completion(
                                    passed,
                                    iteration,
                                    overall_score,
                                    &task_id,
                                );
                                break;
                            }
                        }
                    }
                }
                Ok(None) => {
                    info!("Stream ended normally");
                    break;
                }
                Err(e) => {
                    info!("Stream error: {:?}", e);
                    break;
                }
            }
        }

        // 步骤3: 清理会话
        {
            let mut sessions = self.sessions.write().await;
            sessions.remove(&task_id);
        }

        // 返回响应流
        let stream = EvalResponseStream::new(responses);
        Ok(Response::new(stream))
    }

    async fn health_check(
        &self,
        _request: Request<EvaluatorHealthRequest>,
    ) -> Result<Response<EvaluatorHealthResponse>, Status> {
        Ok(Response::new(EvaluatorHealthResponse {
            healthy: true,
            status: "ready".to_string(),
        }))
    }

    /// StreamLogs - 日志流
    ///
    /// 客户端订阅评估日志，支持实时进度跟踪
    async fn stream_logs(
        &self,
        request: Request<LogRequest>,
    ) -> Result<Response<Self::StreamLogsStream>, Status> {
        info!("stream_logs called");

        let req = request.into_inner();
        let session_id = req.session_id.clone();
        let task_id = req.task_id.clone();

        info!("Subscribing to logs for session: {}, task: {}", session_id, task_id);

        // 创建日志流
        // 注意：当前实现返回空流，日志通过 stdout 输出
        // 实际使用时可以从 session 中获取日志
        let (tx, rx) = tokio::sync::mpsc::channel::<Result<LogEntry, Status>>(100);

        // 返回日志流
        let stream = tokio_stream::wrappers::ReceiverStream::new(rx);

        // 发送欢迎消息
        let _ = tx.send(Ok(LogEntry {
            timestamp: chrono::Utc::now().to_rfc3339(),
            level: "info".to_string(),
            component: "evaluator".to_string(),
            event: "subscription_started".to_string(),
            message: format!("Subscribed to logs for task: {}", task_id),
            trace_id: task_id.clone(),
            session_id: session_id.clone(),
            iteration: 0,
            data: Default::default(),
        })).await;

        Ok(Response::new(stream))
    }
}

// ============================================================
// 便捷函数
// ============================================================

pub fn create_evaluator_service() -> EvaluatorServiceImpl {
    EvaluatorServiceImpl::new(EvaluatorConfig::default())
}

pub fn create_evaluator_service_with_config(config: EvaluatorConfig) -> EvaluatorServiceImpl {
    EvaluatorServiceImpl::new(config)
}
