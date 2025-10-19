"""HomeKit management CLI commands."""

import click
from click_help_colors import HelpColorsGroup

from xp.cli.utils.decorators import service_command


@click.group(
    cls=HelpColorsGroup, help_headers_color="yellow", help_options_color="green"
)
def homekit() -> None:
    """Manage the HomeKit server for XP Protocol operations."""
    pass


@homekit.group(
    cls=HelpColorsGroup, help_headers_color="yellow", help_options_color="green"
)
def config() -> None:
    """Manage HomeKit configuration."""
    pass


@config.command()
@click.option(
    "--conson-config",
    default="conson.yml",
    help="Path to conson.yml configuration file",
)
@click.option(
    "--homekit-config",
    default="homekit.yml",
    help="Path to homekit.yml configuration file",
)
@service_command()
def validate(conson_config: str, homekit_config: str) -> None:
    """Validate homekit.yml and conson.yml coherence.

    Args:
        conson_config: Path to conson.yml configuration file.
        homekit_config: Path to homekit.yml configuration file.
    """
    from xp.services.homekit.homekit_config_validator import ConfigValidationService

    try:
        validator = ConfigValidationService(conson_config, homekit_config)
        results = validator.validate_all()

        if results["is_valid"]:
            click.echo(click.style("✓ Configuration validation passed", fg="green"))
        else:
            click.echo(
                click.style(
                    f"✗ Configuration validation failed with {results['total_errors']} errors",
                    fg="red",
                )
            )

            if results["conson_errors"]:
                click.echo(
                    click.style("\nConson Configuration Errors:", fg="red", bold=True)
                )
                for error in results["conson_errors"]:
                    click.echo(f"  - {error}")

            if results["homekit_errors"]:
                click.echo(
                    click.style("\nHomeKit Configuration Errors:", fg="red", bold=True)
                )
                for error in results["homekit_errors"]:
                    click.echo(f"  - {error}")

            if results["cross_reference_errors"]:
                click.echo(
                    click.style("\nCross-Reference Errors:", fg="red", bold=True)
                )
                for error in results["cross_reference_errors"]:
                    click.echo(f"  - {error}")

            exit(1)

    except Exception as e:
        click.echo(click.style(f"✗ Validation failed: {e}", fg="red"))
        exit(1)


@config.command("show")
@click.option(
    "--conson-config",
    default="conson.yml",
    help="Path to conson.yml configuration file",
)
@click.option(
    "--homekit-config",
    default="homekit.yml",
    help="Path to homekit.yml configuration file",
)
@service_command()
def show_config(conson_config: str, homekit_config: str) -> None:
    """Display parsed configuration summary.

    Args:
        conson_config: Path to conson.yml configuration file.
        homekit_config: Path to homekit.yml configuration file.
    """
    from xp.services.homekit.homekit_config_validator import ConfigValidationService

    try:
        validator = ConfigValidationService(conson_config, homekit_config)
        summary = validator.print_config_summary()

        click.echo(click.style("Configuration Summary:", fg="blue", bold=True))
        click.echo(summary)

    except Exception as e:
        click.echo(click.style(f"✗ Failed to load configuration: {e}", fg="red"))
        exit(1)
