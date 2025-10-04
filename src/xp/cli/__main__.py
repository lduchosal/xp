"""Entry point for running xp.cli as a module."""

from xp.cli.main import cli
from xp.utils.dependencies import ServiceContainer

if __name__ == "__main__":
    service_container = ServiceContainer()
    cli(service_container=service_container)
