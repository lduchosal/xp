"""Cache operations CLI commands for HomeKit cache service."""

import click
import json
from click_help_colors import HelpColorsGroup

from ...services.homekit_cache_service import HomeKitCacheService
from ..utils.decorators import list_command
from ..utils.formatters import OutputFormatter
from ..utils.error_handlers import CLIErrorHandler


@click.group(
    cls=HelpColorsGroup, help_headers_color="yellow", help_options_color="green"
)
def cache() -> None:
    """
    Cache operations for HomeKit device states
    """
    pass


@cache.command("get")
@click.argument("key")
@click.argument("tag")
@list_command(Exception)
def cache_get(key: str, tag: str) -> None:
    """
    Get cached data for a device key with specified tag.

    Examples:

    \b
        xp cache get 2113010000 output_state
        xp cache get E14L00I02M module_info
    """
    OutputFormatter(True)

    try:
        service = HomeKitCacheService()
        response = service.get(key, tag)

        if response.error:
            output = {
                "key": key,
                "tag": tag,
                "hit": response.hit,
                "data": response.data,
                "error": response.error,
                "timestamp": response.timestamp.isoformat(),
            }
        else:
            output = {
                "key": key,
                "tag": tag,
                "hit": response.hit,
                "data": response.data,
                "timestamp": response.timestamp.isoformat(),
            }

        click.echo(json.dumps(output, indent=2))

    except Exception as e:
        CLIErrorHandler.handle_service_error(e, "cache get", {"key": key, "tag": tag})


@cache.command("set")
@click.argument("key")
@click.argument("tag")
@click.argument("data")
@list_command(Exception)
def cache_set(key: str, tag: str, data: str) -> None:
    """
    Set cache entry for a device key with specified tag and data.

    Examples:

    \b
        xp cache set 2113010000 output_state "ON"
        xp cache set E14L00I02M module_info "Push Button Module"
    """
    OutputFormatter(True)

    try:
        service = HomeKitCacheService()
        service.set(key, tag, data)

        output = {
            "success": True,
            "key": key,
            "tag": tag,
            "data": data,
            "message": f"Cache entry set for key: {key}",
        }

        click.echo(json.dumps(output, indent=2))

    except Exception as e:
        CLIErrorHandler.handle_service_error(
            e, "cache set", {"key": key, "tag": tag, "data": data}
        )


@cache.command("clear")
@click.argument("key_or_tag_or_all", required=False)
@list_command(Exception)
def cache_clear(key_or_tag_or_all: str) -> None:
    """
    Clear cache entries by key, tag, or clear entire cache.

    Examples:

    \b
        xp cache clear 2113010000      # Clear specific key
        xp cache clear output_state    # Clear all entries with tag
        xp cache clear --all           # Clear entire cache
    """
    OutputFormatter(True)

    try:
        service = HomeKitCacheService()

        if "all" in key_or_tag_or_all:
            service.clear()
            message = "Entire cache cleared"
            cleared_item = "all"
        elif key_or_tag_or_all:
            service.clear(key_or_tag_or_all)
            message = f"Cache cleared for: {key_or_tag_or_all}"
            cleared_item = key_or_tag_or_all
        else:
            click.echo("Error: Must specify key_or_tag_or_all")
            return

        output = {"success": True, "cleared": cleared_item, "message": message}

        click.echo(json.dumps(output, indent=2))

    except Exception as e:
        CLIErrorHandler.handle_service_error(
            e, "cache clear", {"key_or_tag_or_all": key_or_tag_or_all, "all": all}
        )


@cache.command("items")
@list_command(Exception)
def cache_items() -> None:
    """
    List all cached items with their data.

    Examples:

    \b
        xp cache items
    """
    OutputFormatter(True)

    try:
        service = HomeKitCacheService()
        items = service.items()
        stats = service.get_cache_stats()

        # Format output as specified in the feature doc
        output_lines = ["Cached items :"]
        for key, data in items.items():
            output_lines.append(f"- {key} : {data}")

        if not items:
            output_lines.append("(no cached items)")

        # Also include statistics
        output = {
            "cached_items": items,
            "statistics": stats,
            "formatted_output": "\n".join(output_lines),
        }

        click.echo(json.dumps(output, indent=2))

    except Exception as e:
        CLIErrorHandler.handle_service_error(e, "cache items")


@cache.command("stats")
@list_command(Exception)
def cache_stats() -> None:
    """
    Show cache statistics and information.

    Examples:

    \b
        xp cache stats
    """
    OutputFormatter(True)

    try:
        service = HomeKitCacheService()
        stats = service.get_cache_stats()

        output = {"cache_statistics": stats, "cache_file": str(service.cache_file)}

        click.echo(json.dumps(output, indent=2))

    except Exception as e:
        CLIErrorHandler.handle_service_error(e, "cache stats")
