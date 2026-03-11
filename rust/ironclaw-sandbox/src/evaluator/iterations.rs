//! Iteration Control - 迭代控制模块
//!
//! 管理评估迭代流程
//! 基于 Leslie Lamport 状态机设计原则

use crate::ironclaw::{EvalDimensionInfo, DimensionResult, EvalResponse};

/// 迭代控制状态
#[derive(Debug, Clone, PartialEq)]
pub enum IterationState {
    /// 继续迭代
    Continue,
    /// 迭代通过
    Passed,
    /// 迭代失败
    Failed,
    /// 达到最大迭代次数
    MaxIterationsReached,
}

/// 迭代结果
#[derive(Debug, Clone)]
pub struct IterationResult {
    pub iteration: i32,
    pub passed: bool,
    pub overall_score: f32,
    pub results: Vec<DimensionResult>,
    pub feedback: String,
    pub should_continue: bool,
    pub remaining_iterations: i32,
    pub next_state: String,
    pub can_shutdown: bool,
}

/// 迭代控制器
#[derive(Clone)]
pub struct IterationController {
    max_iterations: i32,
}

impl IterationController {
    pub fn new(max_iterations: i32) -> Self {
        Self { max_iterations }
    }

    /// 计算加权评分
    pub fn calculate_weighted_score(
        &self,
        results: &[DimensionResult],
        dimensions: &[EvalDimensionInfo],
    ) -> f32 {
        if results.is_empty() || dimensions.is_empty() {
            return 0.0;
        }

        let mut total_score = 0.0;
        let mut total_weight = 0.0;

        for (result, dim) in results.iter().zip(dimensions.iter()) {
            total_score += result.score * dim.weight;
            total_weight += dim.weight;
        }

        if total_weight > 0.0 {
            total_score / total_weight
        } else {
            0.0
        }
    }

    /// 生成反馈
    pub fn generate_feedback(&self, results: &[DimensionResult]) -> String {
        let failed: Vec<_> = results
            .iter()
            .filter(|r| !r.passed)
            .collect();

        if failed.is_empty() {
            return "所有维度评估通过".to_string();
        }

        let feedback: Vec<_> = failed
            .iter()
            .map(|r| format!("{}: {}", r.dimension_name, r.feedback))
            .collect();

        feedback.join("; ")
    }

    /// 确定迭代状态
    pub fn determine_state(
        &self,
        passed: bool,
        current_iteration: i32,
    ) -> IterationState {
        if passed {
            IterationState::Passed
        } else if current_iteration >= self.max_iterations {
            IterationState::MaxIterationsReached
        } else {
            IterationState::Continue
        }
    }

    /// 构建迭代响应
    pub fn build_response(
        &self,
        task_id: &str,
        iteration: i32,
        results: &[DimensionResult],
        dimensions: &[EvalDimensionInfo],
    ) -> EvalResponse {
        let overall_score = self.calculate_weighted_score(results, dimensions);
        let passed = results.iter().all(|r| r.passed);
        let feedback = self.generate_feedback(results);
        let state = self.determine_state(passed, iteration);

        let (next_state, can_shutdown) = match state {
            IterationState::Passed => ("DONE".to_string(), true),
            IterationState::MaxIterationsReached => ("FAIL".to_string(), true),
            IterationState::Failed => ("FAIL".to_string(), true),
            IterationState::Continue => ("IMPROVING".to_string(), false),
        };

        let should_continue = matches!(state, IterationState::Continue);

        EvalResponse {
            task_id: task_id.to_string(),
            iteration,
            passed,
            overall_score,
            results: results.to_vec(),
            feedback,
            should_continue,
            remaining_iterations: self.max_iterations - iteration,
            current_iteration: iteration,
            next_state,
            can_shutdown,
            status: if passed { "success".to_string() } else { "improving".to_string() },
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_calculate_weighted_score() {
        let controller = IterationController::new(5);

        let results = vec![
            DimensionResult {
                dimension_name: "correctness".to_string(),
                score: 0.8,
                passed: true,
                feedback: "Good".to_string(),
            },
            DimensionResult {
                dimension_name: "safety".to_string(),
                score: 0.6,
                passed: true,
                feedback: "Ok".to_string(),
            },
        ];

        let dimensions = vec![
            EvalDimensionInfo {
                name: "correctness".to_string(),
                weight: 0.6,
                threshold: 0.5,
                criteria: "".to_string(),
                evaluation_method: "llm_judge".to_string(),
            },
            EvalDimensionInfo {
                name: "safety".to_string(),
                weight: 0.4,
                threshold: 0.5,
                criteria: "".to_string(),
                evaluation_method: "llm_judge".to_string(),
            },
        ];

        let score = controller.calculate_weighted_score(&results, &dimensions);
        // 0.8 * 0.6 + 0.6 * 0.4 = 0.48 + 0.24 = 0.72
        assert!((score - 0.72).abs() < 0.001);
    }

    #[test]
    fn test_calculate_weighted_score_empty() {
        let controller = IterationController::new(5);
        let score = controller.calculate_weighted_score(&[], &[]);
        assert_eq!(score, 0.0);
    }

    #[test]
    fn test_generate_feedback_all_passed() {
        let controller = IterationController::new(5);

        let results = vec![
            DimensionResult {
                dimension_name: "correctness".to_string(),
                score: 0.8,
                passed: true,
                feedback: "Good".to_string(),
            },
        ];

        let feedback = controller.generate_feedback(&results);
        assert_eq!(feedback, "所有维度评估通过");
    }

    #[test]
    fn test_generate_feedback_with_failures() {
        let controller = IterationController::new(5);

        let results = vec![
            DimensionResult {
                dimension_name: "correctness".to_string(),
                score: 0.8,
                passed: true,
                feedback: "Good".to_string(),
            },
            DimensionResult {
                dimension_name: "safety".to_string(),
                score: 0.3,
                passed: false,
                feedback: "Missing validation".to_string(),
            },
        ];

        let feedback = controller.generate_feedback(&results);
        assert!(feedback.contains("safety"));
        assert!(feedback.contains("Missing validation"));
    }

    #[test]
    fn test_determine_state_passed() {
        let controller = IterationController::new(5);
        let state = controller.determine_state(true, 1);
        assert_eq!(state, IterationState::Passed);
    }

    #[test]
    fn test_determine_state_max_iterations() {
        let controller = IterationController::new(5);
        let state = controller.determine_state(false, 5);
        assert_eq!(state, IterationState::MaxIterationsReached);
    }

    #[test]
    fn test_determine_state_continue() {
        let controller = IterationController::new(5);
        let state = controller.determine_state(false, 2);
        assert_eq!(state, IterationState::Continue);
    }

    #[test]
    fn test_build_response_passed() {
        let controller = IterationController::new(5);

        let results = vec![
            DimensionResult {
                dimension_name: "correctness".to_string(),
                score: 0.8,
                passed: true,
                feedback: "Good".to_string(),
            },
        ];

        let dimensions = vec![
            EvalDimensionInfo {
                name: "correctness".to_string(),
                weight: 1.0,
                threshold: 0.5,
                criteria: "".to_string(),
                evaluation_method: "llm_judge".to_string(),
            },
        ];

        let response = controller.build_response("task-1", 1, &results, &dimensions);

        assert!(response.passed);
        assert_eq!(response.next_state, "DONE");
        assert!(response.can_shutdown);
        assert!(!response.should_continue);
    }

    #[test]
    fn test_build_response_continue() {
        let controller = IterationController::new(5);

        let results = vec![
            DimensionResult {
                dimension_name: "correctness".to_string(),
                score: 0.3,
                passed: false,
                feedback: "Needs improvement".to_string(),
            },
        ];

        let dimensions = vec![
            EvalDimensionInfo {
                name: "correctness".to_string(),
                weight: 1.0,
                threshold: 0.5,
                criteria: "".to_string(),
                evaluation_method: "llm_judge".to_string(),
            },
        ];

        let response = controller.build_response("task-1", 1, &results, &dimensions);

        assert!(!response.passed);
        assert_eq!(response.next_state, "IMPROVING");
        assert!(!response.can_shutdown);
        assert!(response.should_continue);
    }
}
