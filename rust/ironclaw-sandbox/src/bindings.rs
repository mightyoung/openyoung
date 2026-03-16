// PyO3 Bindings for Rust Sandbox

use pyo3::prelude::*;
use pyo3::wrap_pyfunction;

// ============================================================================
// Sandbox Config
// ============================================================================

#[pyclass]
#[derive(Debug, Clone)]
pub struct PySandboxConfig {
    pub max_execution_time_ms: u64,
    pub max_memory_mb: u64,
    pub allow_network: bool,
}

#[pymethods]
impl PySandboxConfig {
    #[new]
    fn new(
        max_execution_time_ms: u64,
        max_memory_mb: u64,
        allow_network: bool,
    ) -> Self {
        Self {
            max_execution_time_ms,
            max_memory_mb,
            allow_network,
        }
    }
}

#[wrap_pyfunction]
pub fn create_sandbox_config(
    max_execution_time_ms: u64,
    max_memory_mb: u64,
    allow_network: bool,
) -> PyResult<PySandboxConfig> {
    Ok(PySandboxConfig::new(
        max_execution_time_ms,
        max_memory_mb,
        allow_network,
    ))
}

// ============================================================================
// Version Info
// ============================================================================

#[pyclass]
pub struct VersionInfo {
    pub major: u32,
    pub minor: u32,
    pub patch: u32,
}

#[pymethods]
impl VersionInfo {
    #[new]
    fn new(major: u32, minor: u32, patch: u32) -> Self {
        Self { major, minor, patch }
    }

    fn __repr__(&self) -> String {
        format!("{}.{}.{}", self.major, self.minor, self.patch)
    }
}

pub fn get_version() -> VersionInfo {
    VersionInfo::new(0, 1, 0)
}
