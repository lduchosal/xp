"""Module type operations CLI commands."""

import click
import json

from ...services.module_type_service import ModuleTypeService, ModuleTypeNotFoundError
from ..utils.decorators import json_output_option, list_command
from ..utils.formatters import OutputFormatter, ListFormatter
from ..utils.error_handlers import CLIErrorHandler


@click.group()
def module():
    """Module type operations"""
    pass


@module.command("info")
@click.argument("identifier")
@list_command(ModuleTypeNotFoundError)
def module_info(identifier: str, json_output: bool):
    """
    Get information about a module type by code or name.

    Example: xp module info 14
    Example: xp module info XP2606
    """
    service = ModuleTypeService()
    formatter = OutputFormatter(json_output)

    try:
        # Try to parse as integer first, then as string
        try:
            module_id = int(identifier)
        except ValueError:
            module_id = identifier

        module_type = service.get_module_type(module_id)

        if json_output:
            click.echo(json.dumps(module_type.to_dict(), indent=2))
        else:
            click.echo(service.get_module_info_summary(module_id))

    except ModuleTypeNotFoundError as e:
        CLIErrorHandler.handle_not_found_error(
            e, json_output, "module type", identifier
        )


@module.command("list")
@click.option("--category", "-c", help="Filter by category")
@click.option(
    "--group-by-category", "-g", is_flag=True, help="Group modules by category"
)
@list_command(Exception)
def module_list(category: str, json_output: bool, group_by_category: bool):
    """
    List module types, optionally filtered by category.

    Example: xp module list
    Example: xp module list --category "Interface Panels"
    Example: xp module list --group-by-category
    """
    service = ModuleTypeService()
    formatter = ListFormatter(json_output)

    try:
        if category:
            modules = service.get_modules_by_category(category)
            if not modules:
                if json_output:
                    click.echo(json.dumps({"modules": [], "category": category}))
                else:
                    click.echo(f"No modules found in category '{category}'")
                return
        else:
            modules = service.list_all_modules()

        if json_output:
            if group_by_category:
                categories = service.list_modules_by_category()
                output = {
                    "modules_by_category": {
                        cat: [mod.to_dict() for mod in mods]
                        for cat, mods in categories.items()
                    }
                }
            else:
                output = {
                    "modules": [module.to_dict() for module in modules],
                    "count": len(modules),
                }
            click.echo(json.dumps(output, indent=2))
        else:
            if group_by_category:
                click.echo(service.get_all_modules_summary(group_by_category=True))
            else:
                click.echo(service.get_all_modules_summary(group_by_category=False))

    except Exception as e:
        CLIErrorHandler.handle_service_error(e, json_output, "module listing")


@module.command("search")
@click.argument("query")
@click.option(
    "--field",
    multiple=True,
    type=click.Choice(["name", "description"]),
    help="Fields to search in (default: both)",
)
@list_command(Exception)
def module_search(query: str, json_output: bool, field: tuple):
    """
    Search for module types by name or description.

    Example: xp module search "push button"
    Example: xp module search --field name "XP"
    """
    service = ModuleTypeService()
    formatter = ListFormatter(json_output)

    try:
        search_fields = list(field) if field else ["name", "description"]
        matching_modules = service.search_modules(query, search_fields)

        if json_output:
            output = {
                "query": query,
                "search_fields": search_fields,
                "matches": [module.to_dict() for module in matching_modules],
                "count": len(matching_modules),
            }
            click.echo(json.dumps(output, indent=2))
        else:
            click.echo(formatter.format_search_results(matching_modules, query))

    except Exception as e:
        CLIErrorHandler.handle_service_error(
            e, json_output, "module search", {"query": query}
        )


@module.command("categories")
@list_command(Exception)
def module_categories(json_output: bool):
    """
    List all available module categories.

    Example: xp module categories
    """
    service = ModuleTypeService()
    formatter = OutputFormatter(json_output)

    try:
        categories = service.list_modules_by_category()

        if json_output:
            output = {
                "categories": {
                    category: len(modules) for category, modules in categories.items()
                }
            }
            click.echo(json.dumps(output, indent=2))
        else:
            click.echo("Available categories:")
            click.echo("-" * 30)
            for category, modules in categories.items():
                click.echo(f"{category}: {len(modules)} modules")

    except Exception as e:
        CLIErrorHandler.handle_service_error(e, json_output, "category listing")
