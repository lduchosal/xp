"""FastAPI application for XP Protocol API endpoints."""

import logging
import os
from pathlib import Path
from typing import Any

import yaml
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from xp.api.routers import conbus
from xp.utils.dependencies import ServiceContainer

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_api_config() -> dict[str, Any]:
    """Load API configuration from api.yml or environment variables."""
    config = {
        "title": "XP Protocol API",
        "description": "REST API for XP Protocol Conbus operations",
        "version": "0.2.0",
        "cors_origins": ["*"],
        "cors_methods": ["GET", "POST"],
        "cors_headers": ["*"],
    }

    # Try to load from api.yml
    try:
        if Path("api.yml").exists():
            with Path("api.yml").open("r") as file:
                file_config = yaml.safe_load(file)
                if file_config:
                    config.update(file_config.get("api", {}))
                    logger.info("Loaded API configuration from api.yml")
    except Exception as e:
        logger.warning(f"Could not load api.yml: {e}")

    # Override with environment variables
    config["title"] = os.getenv("API_TITLE", config["title"])
    config["description"] = os.getenv("API_DESCRIPTION", config["description"])
    config["version"] = os.getenv("API_VERSION", config["version"])

    # CORS configuration from environment
    cors_origins = os.getenv("CORS_ORIGINS")
    if cors_origins is not None:
        config["cors_origins"] = cors_origins.split(",")
    cors_methods = os.getenv("CORS_METHODS")
    if cors_methods is not None:
        config["cors_methods"] = cors_methods.split(",")
    cors_headers = os.getenv("CORS_HEADERS")
    if cors_headers is not None:
        config["cors_headers"] = cors_headers.split(",")

    return config


def create_app(container: ServiceContainer) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        container: Optional ServiceContainer instance. If not provided, a new one will be created.
    """
    config = load_api_config()

    fastapi = FastAPI(
        title=config["title"],
        description=config["description"],
        version=config["version"],
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Add CORS middleware
    fastapi.add_middleware(
        CORSMiddleware,
        allow_origins=config["cors_origins"],
        allow_credentials=True,
        allow_methods=config["cors_methods"],
        allow_headers=config["cors_headers"],
    )

    # Initialize service container
    fastapi.state.container = container

    # Include routers
    fastapi.include_router(conbus.router)

    # Health check endpoint
    @fastapi.get("/health")
    async def health_check() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "healthy", "service": "xp-api"}

    # Root endpoint
    @fastapi.get("/")
    async def root() -> dict[str, str]:
        """Root endpoint with API information."""
        return {
            "message": "XP Protocol API",
            "version": config["version"],
            "docs": "/docs",
            "health": "/health",
        }

    logger.info(f"FastAPI application created: {config['title']} v{config['version']}")
    return fastapi
