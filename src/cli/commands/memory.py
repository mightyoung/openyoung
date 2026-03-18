"""
Memory Command - 记忆和向量搜索命令

提供 openyoung memory 命令
"""

import click

from src.core.memory.impl.vector_store import VectorStore


@click.group(name="memory")
def memory_group():
    """Memory and vector search commands"""
    pass


@memory_group.command(name="list")
@click.option("--namespace", "-n", default=None, help="Filter by namespace")
@click.option("--limit", "-l", default=20, help="Maximum results")
def memory_list(namespace: str = None, limit: int = 20):
    """List all memory entries"""
    store = VectorStore()

    if namespace:
        results = store.list(namespace=namespace, limit=limit)
    else:
        # List all namespaces
        stats = store.get_stats()
        namespaces = stats.get("namespace_list", [])
        if not namespaces:
            click.echo("No namespaces found")
            return

        click.echo("=== Namespaces ===")
        for ns in namespaces:
            click.echo(f"  - {ns}")

        # Also show first few entries from each namespace
        click.echo("\n=== Recent Entries ===")
        for ns in namespaces[:3]:
            results = store.list(namespace=ns, limit=3)
            if results:
                click.echo(f"\n[{ns}]:")
                for r in results:
                    content = r.get("content", "")[:100]
                    click.echo(f"  - {content}...")


@memory_group.command(name="search")
@click.argument("query")
@click.option("--namespace", "-n", default="default", help="Namespace to search in")
@click.option("--limit", "-l", default=5, help="Maximum results")
@click.option("--threshold", "-t", default=0.0, help="Similarity threshold")
def memory_search(query: str, namespace: str, limit: int, threshold: float):
    """Search memory using semantic vector search"""
    store = VectorStore()
    results = store.search(query, namespace=namespace, limit=limit, threshold=threshold)

    if not results:
        click.echo("No results found")
        return

    click.echo(f"Found {len(results)} results:\n")
    for i, r in enumerate(results, 1):
        similarity = r.get("similarity", 0)
        content = r.get("content", "")[:200]
        click.echo(f"{i}. [similarity: {similarity:.3f}] {content}...")


@memory_group.command(name="stats")
def memory_stats():
    """Show memory statistics"""
    store = VectorStore()
    stats = store.get_stats()

    click.echo("=== Vector Store Stats ===")
    click.echo(f"Status: {stats.get('status')}")
    click.echo(f"Namespaces: {stats.get('namespaces', 0)}")
    if stats.get("namespace_list"):
        click.echo(f"Namespace list: {', '.join(stats['namespace_list'])}")
