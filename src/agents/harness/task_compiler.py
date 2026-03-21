"""
Task Compiler - Task → Harness Graph

将 Task 转换为 Harness Graph 的编译器。
用于将自然语言任务转换为可执行的 Harness 步骤图。
"""


from src.agents.harness.graph import HarnessGraph


class TaskCompiler:
    """Task → Harness Graph 编译器

    将 Task 对象编译为 Harness Graph 格式，
    支持多步骤任务的图结构构建。
    """

    def __init__(self):
        self._graph_template = {
            "nodes": [],
            "edges": [],
            "metadata": {},
        }

    def compile(self, task, **kwargs) -> HarnessGraph:
        """将 Task 编译为 HarnessGraph

        Args:
            task: Task 对象
            **kwargs: 额外编译参数

        Returns:
            HarnessGraph 实例
        """
        graph = self._graph_template.copy()
        graph["metadata"] = {
            "task_id": task.id if hasattr(task, "id") else None,
            "description": task.description if hasattr(task, "description") else str(task),
            "compiled_at": kwargs.get("timestamp"),
        }

        # 单任务：直接作为根节点
        if hasattr(task, "description"):
            graph["nodes"].append(
                {
                    "id": "root",
                    "type": "task",
                    "label": task.description[:100],
                }
            )

        return HarnessGraph(graph, config=kwargs)

    def add_node(self, graph: dict, node_id: str, node_type: str, label: str = "") -> dict:
        """向 Graph 添加节点

        Args:
            graph: 目标 Graph
            node_id: 节点 ID
            node_type: 节点类型 (task, tool, condition, etc.)
            label: 节点标签

        Returns:
            更新后的 Graph
        """
        graph["nodes"].append(
            {
                "id": node_id,
                "type": node_type,
                "label": label,
            }
        )
        return graph

    def add_edge(self, graph: dict, from_id: str, to_id: str, edge_type: str = "next") -> dict:
        """向 Graph 添加边

        Args:
            graph: 目标 Graph
            from_id: 起始节点 ID
            to_id: 目标节点 ID
            edge_type: 边类型 (next, dependency, condition, etc.)

        Returns:
            更新后的 Graph
        """
        graph["edges"].append(
            {
                "from": from_id,
                "to": to_id,
                "type": edge_type,
            }
        )
        return graph
