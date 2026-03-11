//! Circuit Breaker - 熔断器模式实现
//!
//! 基于 Mike Gunderloy 的熔断器模式
//! 保护系统免受级联故障影响

use std::sync::atomic::{AtomicU32, Ordering};
use std::sync::Arc;
use std::time::Instant;
use tokio::sync::RwLock;
use tracing::info;

/// 熔断器状态
#[derive(Debug, Clone, PartialEq)]
pub enum CircuitState {
    Closed,      // 正常状态
    Open,        // 熔断状态
    HalfOpen,    // 半开状态（探测恢复）
}

/// 熔断器配置
#[derive(Debug, Clone)]
pub struct CircuitBreakerConfig {
    /// 触发熔断的失败次数
    pub failure_threshold: u32,
    /// 熔断恢复时间(秒)
    pub recovery_timeout_secs: u64,
    /// 半开状态需要成功的请求数
    pub half_open_requests: u32,
}

impl Default for CircuitBreakerConfig {
    fn default() -> Self {
        Self {
            failure_threshold: 3,
            recovery_timeout_secs: 30,
            half_open_requests: 1,
        }
    }
}

/// 熔断器
///
/// # Example
///
/// ```rust
/// use circuit_breaker::{CircuitBreaker, CircuitBreakerConfig};
///
/// let cb = CircuitBreaker::new(CircuitBreakerConfig::default());
/// if cb.can_execute().await {
///     // 执行请求
///     cb.record_success().await;
/// } else {
///     // 快速失败
/// }
/// ```
#[derive(Debug)]
pub struct CircuitBreaker {
    config: CircuitBreakerConfig,
    state: Arc<RwLock<CircuitState>>,
    failure_count: Arc<AtomicU32>,
    last_failure_time: Arc<RwLock<Option<Instant>>>,
    success_count: Arc<AtomicU32>,
}

impl CircuitBreaker {
    /// 创建新的熔断器
    pub fn new(config: CircuitBreakerConfig) -> Self {
        Self {
            config,
            state: Arc::new(RwLock::new(CircuitState::Closed)),
            failure_count: Arc::new(AtomicU32::new(0)),
            last_failure_time: Arc::new(RwLock::new(None)),
            success_count: Arc::new(AtomicU32::new(0)),
        }
    }

    /// 检查是否可以执行请求
    pub async fn can_execute(&self) -> bool {
        let state = self.state.read().await;
        match *state {
            CircuitState::Closed => true,
            CircuitState::Open => {
                // 检查是否应该转换到半开状态
                drop(state);
                self.try_half_open().await
            }
            CircuitState::HalfOpen => true,
        }
    }

    /// 尝试转换到半开状态
    pub async fn try_half_open(&self) -> bool {
        if let Some(last_failure) = *self.last_failure_time.read().await {
            let elapsed = last_failure.elapsed();
            if elapsed.as_secs() >= self.config.recovery_timeout_secs {
                *self.state.write().await = CircuitState::HalfOpen;
                self.success_count.store(0, Ordering::SeqCst);
                info!("Circuit breaker transitioning to HalfOpen");
                return true;
            }
        }
        false
    }

    /// 记录成功
    pub async fn record_success(&self) {
        let state = self.state.read().await;
        match *state {
            CircuitState::Closed => {
                // 成功重置失败计数
                self.failure_count.store(0, Ordering::SeqCst);
            }
            CircuitState::HalfOpen => {
                let successes = self.success_count.fetch_add(1, Ordering::SeqCst) + 1;
                if successes >= self.config.half_open_requests {
                    // 恢复关闭状态
                    *self.state.write().await = CircuitState::Closed;
                    self.failure_count.store(0, Ordering::SeqCst);
                    info!("Circuit breaker recovered to Closed");
                }
            }
            CircuitState::Open => {}
        }
    }

    /// 记录失败
    pub async fn record_failure(&self) {
        let failures = self.failure_count.fetch_add(1, Ordering::SeqCst) + 1;
        *self.last_failure_time.write().await = Some(Instant::now());

        if failures >= self.config.failure_threshold {
            *self.state.write().await = CircuitState::Open;
            info!("Circuit breaker opened after {} failures", failures);
        }
    }

    /// 获取当前状态
    pub async fn get_state(&self) -> CircuitState {
        self.state.read().await.clone()
    }

    /// 手动重置熔断器
    pub async fn reset(&self) {
        *self.state.write().await = CircuitState::Closed;
        self.failure_count.store(0, Ordering::SeqCst);
        self.success_count.store(0, Ordering::SeqCst);
        *self.last_failure_time.write().await = None;
    }
}

impl Default for CircuitBreaker {
    fn default() -> Self {
        Self::new(CircuitBreakerConfig::default())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_circuit_breaker_closed_by_default() {
        let cb = CircuitBreaker::new(CircuitBreakerConfig::default());
        let can_exec = cb.can_execute().await;
        assert!(can_exec, "Should allow execution in closed state");
    }

    #[tokio::test]
    async fn test_circuit_breaker_opens_after_threshold() {
        let cb = CircuitBreaker::new(CircuitBreakerConfig {
            failure_threshold: 3,
            ..Default::default()
        });

        // Record failures to trigger circuit open
        cb.record_failure().await;
        cb.record_failure().await;

        // Still closed, haven't reached threshold
        let can_exec = cb.can_execute().await;
        assert!(can_exec, "Should still allow execution before threshold");

        // Third failure - should open
        cb.record_failure().await;

        let state = cb.get_state().await;
        assert_eq!(state, CircuitState::Open, "Should be open after threshold");

        let can_exec = cb.can_execute().await;
        assert!(!can_exec, "Should NOT allow execution when open");
    }

    #[tokio::test]
    async fn test_circuit_breaker_recovers_on_success() {
        let cb = CircuitBreaker::new(CircuitBreakerConfig {
            failure_threshold: 2,
            half_open_requests: 1,
            recovery_timeout_secs: 0, // 立即允许转换
            ..Default::default()
        });

        // Open the circuit
        cb.record_failure().await;
        cb.record_failure().await;

        let state = cb.get_state().await;
        assert_eq!(state, CircuitState::Open);

        // Transition to half-open (timeout is 0, so it should work)
        let transitioned = cb.try_half_open().await;
        assert!(transitioned, "Should transition to half-open");

        let state = cb.get_state().await;
        assert_eq!(state, CircuitState::HalfOpen);

        // Record success
        cb.record_success().await;

        let state = cb.get_state().await;
        assert_eq!(state, CircuitState::Closed, "Should recover to closed");
    }

    #[tokio::test]
    async fn test_circuit_breaker_success_resets_failures() {
        let cb = CircuitBreaker::new(CircuitBreakerConfig::default());

        // Record some failures
        cb.record_failure().await;
        cb.record_failure().await;

        // Record success - should reset
        cb.record_success().await;

        // Now one more failure shouldn't open
        cb.record_failure().await;

        let state = cb.get_state().await;
        assert_eq!(state, CircuitState::Closed, "Should stay closed");
    }
}
