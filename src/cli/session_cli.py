"""
Session CLI - 会话管理命令

提供命令行接口管理持久Agent会话
"""

import asyncio

import click

from src.agents.session import SessionManager


@click.group(name="session")
def session_group():
    """持久Agent会话管理"""
    pass


@session_group.command(name="create")
@click.argument("agent_name")
@click.option("--name", "session_name", help="会话名称")
@click.option("--context", "context_json", help="初始上下文 (JSON)")
def create_session(agent_name: str, session_name: str = None, context_json: str = None):
    """创建持久会话"""
    import json

    session_mgr = SessionManager()
    context = {}
    if context_json:
        context = json.loads(context_json)

    session = session_mgr.create_persistent_session(
        agent_name=agent_name,
        description=session_name or "",
        initial_context=context,
    )

    click.echo(f"Created session: {session.session_id}")
    click.echo(f"Agent: {session.agent_name}")
    click.echo(f"Status: {session.status}")


@session_group.command(name="list")
def list_sessions():
    """列出所有持久会话"""
    session_mgr = SessionManager()
    sessions = session_mgr.get_persistent_sessions()

    if not sessions:
        click.echo("No persistent sessions")
        return

    click.echo(f"{'Session ID':<40} {'Agent':<20} {'Status':<10}")
    click.echo("-" * 70)
    for s in sessions:
        click.echo(f"{s.session_id:<40} {s.agent_name or '-':<20} {s.status:<10}")


@session_group.command(name="send")
@click.argument("session_id")
@click.argument("message")
def send_message(session_id: str, message: str):
    """发送消息到会话"""
    session_mgr = SessionManager()

    session = session_mgr.get_persistent_session(session_id)
    if not session:
        click.echo(f"Error: Session {session_id} not found")
        return

    # 添加消息
    session_mgr.add_message(session_id, "user", message)

    # TODO: 执行Agent
    response = f"Echo: {message}"

    # 添加响应
    session_mgr.add_message(session_id, "assistant", response)

    click.echo(f"Response: {response}")


@session_group.command(name="history")
@click.argument("session_id")
def get_history(session_id: str):
    """获取会话历史"""
    session_mgr = SessionManager()
    messages = session_mgr.get_messages(session_id)

    if not messages:
        click.echo("No messages")
        return

    for msg in messages:
        click.echo(f"[{msg.role}] {msg.content}")


@session_group.command(name="suspend")
@click.argument("session_id")
def suspend_session(session_id: str):
    """暂停会话"""
    session_mgr = SessionManager()
    success = session_mgr.suspend_session(session_id)

    if success:
        click.echo(f"Session {session_id} suspended")
    else:
        click.echo(f"Error: Failed to suspend session {session_id}")


@session_group.command(name="resume")
@click.argument("session_id")
def resume_session(session_id: str):
    """恢复会话"""
    session_mgr = SessionManager()
    success = session_mgr.resume_session(session_id)

    if success:
        click.echo(f"Session {session_id} resumed")
    else:
        click.echo(f"Error: Failed to resume session {session_id}")


@session_group.command(name="terminate")
@click.argument("session_id")
def terminate_session(session_id: str):
    """终止会话"""
    session_mgr = SessionManager()
    success = session_mgr.terminate_session(session_id)

    if success:
        click.echo(f"Session {session_id} terminated")
    else:
        click.echo(f"Error: Failed to terminate session {session_id}")


if __name__ == "__main__":
    session_group()
