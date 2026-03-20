"""
LLM Command - LLM Provider 管理命令

提供 openyoung llm 命令
"""

import click

from src.package_manager.manager import PackageManager


@click.group(name="llm")
def llm_group():
    """LLM Provider management"""
    pass


@llm_group.command(name="list")
@click.option("--enabled", "-e", is_flag=True, help="Show only enabled providers")
def llm_list(enabled: bool):
    """List available LLM providers"""
    manager = PackageManager()
    providers = manager.list_providers(enabled_only=enabled)

    if not providers:
        click.echo("No LLM providers configured")
        return

    default_provider = manager.get_default_provider()

    click.echo("Available LLM providers:")
    for p in providers:
        marker = " (default)" if default_provider and p.name == default_provider.name else ""
        click.echo(f"  • {p.name} ({p.provider_type}){marker}")
        click.echo(f"    Models: {', '.join(p.models[:3])}{'...' if len(p.models) > 3 else ''}")


@llm_group.command(name="add")
@click.argument("provider_name")
@click.option("--api-key", "-k", required=True, help="API key for the provider")
@click.option("--base-url", "-b", help="Base URL (optional)")
@click.option("--models", "-m", help="Comma-separated list of models")
@click.option("--default", "-d", is_flag=True, help="Set as default provider")
def llm_add(
    provider_name: str,
    api_key: str,
    base_url: str | None,
    models: str | None,
    default: bool,
):
    """Add an LLM provider"""
    manager = PackageManager()
    provider_manager = manager.provider_manager

    # Get provider info
    provider_info = provider_manager.get_provider_info(provider_name)
    if not provider_info:
        click.echo(f"Error: Unknown provider '{provider_name}'")
        click.echo(f"Available: {', '.join(provider_manager.available_providers)}")
        return

    # Validate API key
    if not provider_manager.validate_provider_config(provider_name, api_key):
        click.echo(f"Error: Invalid API key format for '{provider_name}'")
        return

    # Get base_url
    actual_base_url = base_url or provider_manager.get_base_url(provider_name)
    if not actual_base_url:
        click.echo(f"Error: Could not determine base URL for '{provider_name}'")
        return

    # Parse models
    model_list = None
    if models:
        model_list = [m.strip() for m in models.split(",")]

    # Add provider
    success = manager.add_provider(
        name=provider_name,
        provider_type=provider_name,
        base_url=actual_base_url,
        api_key=api_key,
        models=model_list,
    )

    if success:
        if default:
            manager.set_default_provider(provider_name)
            click.echo(f"Added and set '{provider_name}' as default provider")
        else:
            click.echo(f"Added provider: {provider_name}")
    else:
        click.echo(f"Error: Failed to add provider '{provider_name}'")


@llm_group.command(name="remove")
@click.argument("provider_name")
def llm_remove(provider_name: str):
    """Remove an LLM provider"""
    manager = PackageManager()
    success = manager.remove_provider(provider_name)

    if success:
        click.echo(f"Removed provider: {provider_name}")
    else:
        click.echo(f"Error: Provider '{provider_name}' not found")


@llm_group.command(name="use")
@click.argument("provider_name")
def llm_use(provider_name: str):
    """Set default LLM provider"""
    manager = PackageManager()

    # Verify provider exists
    provider = manager.get_provider(provider_name)
    if not provider:
        click.echo(f"Error: Provider '{provider_name}' not found")
        return

    manager.set_default_provider(provider_name)
    click.echo(f"Default provider set to: {provider_name}")


@llm_group.command(name="info")
@click.argument("provider_name", required=False)
def llm_info(provider_name: str | None):
    """Show provider details"""
    manager = PackageManager()

    if provider_name:
        # Show specified provider
        provider = manager.get_provider(provider_name)
        if not provider:
            click.echo(f"Error: Provider '{provider_name}' not found")
            return

        click.echo(f"Provider: {provider.name}")
        click.echo(f"Type: {provider.provider_type}")
        click.echo(f"Base URL: {provider.base_url}")
        click.echo(f"API Key: {'*' * 8}{provider.api_key[-4:] if provider.api_key else 'N/A'}")
        click.echo(f"Enabled: {provider.enabled}")
        click.echo(f"Models: {', '.join(provider.models)}")
    else:
        # Show default provider
        default = manager.get_default_provider()
        if not default:
            click.echo("No default provider set")
            return

        click.echo(f"Default provider: {default.name}")
        click.echo(f"Type: {default.provider_type}")
        click.echo(f"Base URL: {default.base_url}")
        click.echo(
            f"Models: {', '.join(default.models[:3])}{'...' if len(default.models) > 3 else ''}"
        )
