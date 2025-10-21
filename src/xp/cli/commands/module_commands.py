"""Module type operations CLI commands."""

import json
from typing import Any, Dict, Union

import click
from click import Context
from click_help_colors import HelpColorsGroup

from xp.cli.utils.decorators import list_command
from xp.cli.utils.error_handlers import CLIErrorHandler
from xp.cli.utils.formatters import ListFormatter, OutputFormatter
from xp.services.module_type_service import ModuleTypeNotFoundError, ModuleTypeService


@click.group(
    cls=HelpColorsGroup, help_headers_color="yellow", help_options_color="green"
)
def module() -> None:
    """Perform module type operations."""
    pass


@module.command("info")
@click.argument("identifier")
@click.pass_context
@list_command(ModuleTypeNotFoundError)
def module_info(ctx: Context, identifier: str) -> None:
    r"""Get information about a module type by code or name.

    Args:
        ctx: Click context object.
        identifier: Module code or name.

    Examples:
        \b
        xp module info 14
        xp module info XP2606
    """
    service: ModuleTypeService = (
        ctx.obj.get("container").get_container().resolve(ModuleTypeService)
    )
    OutputFormatter(True)

    try:
        # Try to parse as integer first, then as string
        module_id: Union[int, str]
        try:
            module_id = int(identifier)
        except ValueError:
            module_id = identifier

        module_type = service.get_module_type(module_id)
        click.echo(json.dumps(module_type.to_dict(), indent=2))

    except ModuleTypeNotFoundError as e:
        CLIErrorHandler.handle_not_found_error(e, "module type", identifier)


@module.command("list")
@click.option("--category", "-c", help="Filter by category")
@click.option(
    "--group-by-category", "-g", is_flag=True, help="Group modules by category"
)
@click.pass_context
@list_command(Exception)
def module_list(ctx: Context, category: str, group_by_category: bool) -> None:
    r"""List module types, optionally filtered by category.

    Args:
        ctx: Click context object.
        category: Filter by category.
        group_by_category: Group modules by category.

    Examples:
        \b
        xp module list
        xp module list --category "Interface Panels"
        xp module list --group-by-category
    """
    service: ModuleTypeService = (
        ctx.obj.get("container").get_container().resolve(ModuleTypeService)
    )
    ListFormatter(True)

    try:
        if category:
            modules = service.get_modules_by_category(category)
            if not modules:
                click.echo(json.dumps({"modules": [], "category": category}))
                return
        else:
            modules = service.list_all_modules()

        if group_by_category:
            categories = service.list_modules_by_category()
            output: Dict[str, Any] = {
                "modules_by_category": {
                    cat: [mod.to_dict() for mod in mods]
                    for cat, mods in categories.items()
                }
            }
        else:
            output = {
                "modules": [_module.to_dict() for _module in modules],
                "count": len(modules),
            }
        click.echo(json.dumps(output, indent=2))

    except Exception as e:
        CLIErrorHandler.handle_service_error(e, "module listing")


@module.command("search")
@click.argument("query")
@click.option(
    "--field",
    multiple=True,
    type=click.Choice(["name", "description"]),
    help="Fields to search in (default: both)",
)
@click.pass_context
@list_command(Exception)
def module_search(ctx: Context, query: str, field: tuple) -> None:
    r"""Search for module types by name or description.

    Args:
        ctx: Click context object.
        query: Search query.
        field: Fields to search in.

    Examples:
        \b
        xp module search "push button"
        xp module search --field name "XP"
    """
    service: ModuleTypeService = (
        ctx.obj.get("container").get_container().resolve(ModuleTypeService)
    )
    ListFormatter(True)

    try:
        search_fields = list(field) if field else ["name", "description"]
        matching_modules = service.search_modules(query, search_fields)

        output = {
            "query": query,
            "search_fields": search_fields,
            "matches": [_module.to_dict() for _module in matching_modules],
            "count": len(matching_modules),
        }
        click.echo(json.dumps(output, indent=2))

    except Exception as e:
        CLIErrorHandler.handle_service_error(e, "module search", {"query": query})


@module.command("categories")
@click.pass_context
@list_command(Exception)
def module_categories(ctx: Context) -> None:
    r"""List all available module categories.

    Args:
        ctx: Click context object.

    Examples:
        \b
        xp module categories
    """
    service: ModuleTypeService = (
        ctx.obj.get("container").get_container().resolve(ModuleTypeService)
    )
    OutputFormatter(True)

    try:
        categories = service.list_modules_by_category()

        output = {
            "categories": {
                category: len(modules) for category, modules in categories.items()
            }
        }
        click.echo(json.dumps(output, indent=2))

    except Exception as e:
        CLIErrorHandler.handle_service_error(e, "category listing")
