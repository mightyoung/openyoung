Tracing - OpenTelemetry/LangSmith 集成
支持导出到 OpenTelemetry、LangSmith 等追踪系统

## Classes

### `TraceSpan`

追踪跨度

**Methods:**
- `duration_ms`
- `to_dict`

### `TracingExporter`

追踪导出器基类

**Methods:**
- `export_span`
- `export_spans`

### `OpenTelemetryExporter`

OpenTelemetry 导出器

**Methods:**
- `export_span`

### `LangSmithExporter`

LangSmith 导出器

**Methods:**
- `export_span`

### `ConsoleExporter`

控制台导出器（调试用）

**Methods:**
- `export_span`

### `MultiExporter`

多导出器组合

**Methods:**
- `add_exporter`
- `export_span`

### `TracingContext`

追踪上下文管理器

### `TracingManager`

追踪管理器

**Methods:**
- `add_exporter`
- `start_span`
- `end_span`
- `trace`
- `export_all`

## Functions

### `get_tracing_manager()`

获取追踪管理器

### `create_otel_exporter()`

创建 OpenTelemetry 导出器

### `create_langsmith_exporter()`

创建 LangSmith 导出器

### `duration_ms()`

获取持续时间(毫秒)

### `to_dict()`

转换为字典

### `export_span()`

导出跨度

### `export_spans()`

批量导出跨度

### `export_span()`

导出到 OpenTelemetry 兼容的后端

### `export_span()`

导出到 LangSmith

### `export_span()`

输出到控制台

### `add_exporter()`

添加导出器

### `export_span()`

导出到所有导出器

### `add_exporter()`

添加导出器

### `start_span()`

开始跨度

### `end_span()`

结束跨度

### `trace()`

追踪上下文管理器

### `export_all()`

导出所有跨度
