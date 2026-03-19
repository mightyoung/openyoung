"""
Output Formatters - 输出格式化

提供 CLI 输出格式化工具
"""

from typing import Any


def format_table(headers: list[str], rows: list[list[Any]]) -> str:
    """Format data as a table"""
    if not rows:
        return "No data"

    # Calculate column widths
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    # Format header
    header_line = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    separator = "-+-".join("-" * w for w in col_widths)

    # Format rows
    data_lines = []
    for row in rows:
        line = " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row))
        data_lines.append(line)

    return f"{header_line}\n{separator}\n" + "\n".join(data_lines)


def format_badge(name: str, style: str = "default") -> str:
    """Format a badge string"""
    if style == "compact":
        return f"[{name}]"
    return f"*{name}*"


def format_stats(stats: dict[str, Any]) -> str:
    """Format statistics output"""
    lines = ["=== Statistics ==="]
    for key, value in stats.items():
        if isinstance(value, float):
            lines.append(f"  {key}: {value:.2f}")
        else:
            lines.append(f"  {key}: {value}")
    return "\n".join(lines)


def format_agent_info(name: str, config: Any) -> str:
    """Format agent information"""
    lines = [
        f"Agent: {name}",
        f"  Mode: {config.mode}",
        f"  Model: {config.model}",
        f"  Temperature: {config.temperature}",
    ]
    if hasattr(config, "tools") and config.tools:
        lines.append(f"  Tools: {len(config.tools)}")
    if hasattr(config, "skills") and config.skills:
        lines.append(f"  Skills: {len(config.skills)}")
    return "\n".join(lines)
