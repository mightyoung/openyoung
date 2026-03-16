// Rust Sandbox Implementation using PyO3
// This is the core Rust library for the sandbox

use pyo3::prelude::*;
use pyo3::wrap_pyfunction;
use std::path::PathBuf;
use std::time::{Duration, Instant};

mod bindings;

// ============================================================================
// Data Structures
// ============================================================================

#[derive(Debug, Clone)]
pub struct SandboxConfig {
    pub max_execution_time_ms: u64,
    pub max_memory_mb: u64,
    pub allow_network: bool,
    pub working_dir: Option<PathBuf>,
}

impl Default for SandboxConfig {
    fn default() -> Self {
        Self {
            max_execution_time_ms: 300000, // 5 minutes
            max_memory_mb: 512,
            allow_network: false,
            working_dir: None,
        }
    }
}

#[derive(Debug, Clone)]
pub struct ExecutionResult {
    pub output: String,
    pub exit_code: i32,
    pub duration_ms: u64,
    pub error: Option<String>,
}

#[derive(Debug, Clone)]
pub struct SecurityCheckResult {
    pub safe: bool,
    pub warnings: Vec<String>,
    pub blocked: bool,
}

// ============================================================================
// Sandbox Instance
// ============================================================================

#[pyclass]
pub struct SandboxInstance {
    config: SandboxConfig,
    working_dir: PathBuf,
    start_time: Option<Instant>,
}

#[pymethods]
impl SandboxInstance {
    #[new]
    fn new(config: SandboxConfig) -> Self {
        let working_dir = config.working_dir.clone().unwrap_or_else(|| {
            std::env::temp_dir().join(format!("sandbox_{}", uuid::Uuid::new_v4()))
        });

        // Create working directory
        let _ = std::fs::create_dir_all(&working_dir);

        Self {
            config,
            working_dir,
            start_time: None,
        }
    }

    fn execute(&mut self, code: &str, language: &str) -> PyResult<ExecutionResult> {
        self.start_time = Some(Instant::now());

        // Check security first
        let security = self.check_security(code)?;
        if security.blocked {
            return Ok(ExecutionResult {
                output: String::new(),
                exit_code: 1,
                duration_ms: 0,
                error: Some("Code blocked by security policy".to_string()),
            });
        }

        // Execute based on language
        let result = match language {
            "python" => self.execute_python(code),
            "javascript" | "js" => self.execute_javascript(code),
            _ => Err(format!("Unsupported language: {}", language)),
        };

        let duration = self.start_time
            .map(|t| t.elapsed().as_millis() as u64)
            .unwrap_or(0);

        match result {
            Ok(output) => Ok(ExecutionResult {
                output,
                exit_code: 0,
                duration_ms: duration,
                error: None,
            }),
            Err(e) => Ok(ExecutionResult {
                output: String::new(),
                exit_code: 1,
                duration_ms: duration,
                error: Some(e),
            }),
        }
    }

    fn check_security(&self, code: &str) -> PyResult<SecurityCheckResult> {
        let mut warnings = Vec::new();
        let mut blocked = false;

        // Check for dangerous patterns
        let dangerous_patterns = [
            ("import os", "Imports that could access filesystem"),
            ("import sys", "System access"),
            ("subprocess", "Subprocess execution"),
            ("eval(", "Dynamic code evaluation"),
            ("exec(", "Dynamic code execution"),
            ("__import__", "Dynamic imports"),
            ("open(", "File access"),
            ("requests", "Network access"),
            ("urllib", "Network access"),
            ("socket", "Network socket access"),
        ];

        for (pattern, reason) in &dangerous_patterns {
            if code.contains(pattern) {
                warnings.push(format!("{}: {}", pattern, reason));
            }
        }

        // Block critical patterns
        if code.contains("rm -rf") || code.contains("os.remove") || code.contains("os.unlink") {
            blocked = true;
            warnings.push("File deletion detected".to_string());
        }

        let safe = !blocked && warnings.is_empty();

        Ok(SecurityCheckResult {
            safe,
            warnings,
            blocked,
        })
    }

    fn cleanup(&self) -> PyResult<()> {
        // Clean up working directory
        if self.working_dir.exists() {
            let _ = std::fs::remove_dir_all(&self.working_dir);
        }
        Ok(())
    }

    fn get_working_dir(&self) -> String {
        self.working_dir.to_string_lossy().to_string()
    }
}

impl SandboxInstance {
    fn execute_python(&self, code: &str) -> Result<String, String> {
        // Use PyO3 to execute Python code in a restricted environment
        // This is a simplified version - real implementation would use
        // a proper Python interpreter or subprocess with restrictions

        Python::with_gil(|py| {
            // Create a restricted globals dict
            let globals = py.eval("{}", None, None).unwrap().dict().unwrap();

            // Add safe builtins
            globals.set_item("print", py.eval("print", None, None).unwrap())?;
            globals.set_item("range", py.eval("range", None, None).unwrap())?;
            globals.set_item("len", py.eval("len", None, None).unwrap())?;
            globals.set_item("str", py.eval("str", None, None).unwrap())?;
            globals.set_item("int", py.eval("int", None, None).unwrap())?;
            globals.set_item("float", py.eval("float", None, None).unwrap())?;
            globals.set_item("list", py.eval("list", None, None).unwrap())?;
            globals.set_item("dict", py.eval("dict", None, None).unwrap())?;
            globals.set_item("tuple", py.eval("tuple", None, None).unwrap())?;
            globals.set_item("set", py.eval("set", None, None).unwrap())?;
            globals.set_item("bool", py.eval("bool", None, None).unwrap())?;
            globals.set_item("True", true)?;
            globals.set_item("False", false)?;
            globals.set_item("None", py.None())?;

            // Execute the code
            match py.eval(code, Some(globals), None) {
                Ok(result) => Ok(result.to_string()),
                Err(e) => Err(e.to_string()),
            }
        })
    }

    fn execute_javascript(&self, code: &str) -> Result<String, String> {
        // For JavaScript, we'd need a JS runtime
        // This is a placeholder - real implementation would use deno or quickjs
        Err("JavaScript execution not yet implemented".to_string())
    }
}

// ============================================================================
// Python Module
// ============================================================================

#[pymodule]
fn ironclaw_sandbox(m: &PyModule) -> PyResult<()> {
    m.add_class::<SandboxInstance>()?;

    // Add the config as a Python class
    m.add("SandboxConfig", wrap_pyfunction!(bindings::create_sandbox_config, m)?)?;

    Ok(())
}
