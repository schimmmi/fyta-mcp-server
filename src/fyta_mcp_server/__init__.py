"""
FYTA MCP Server - Plant sensor data access via Model Context Protocol
"""
from .client import FytaClient
from .server import create_fyta_server

__version__ = "1.1.1"
__all__ = ["FytaClient", "create_fyta_server"]
