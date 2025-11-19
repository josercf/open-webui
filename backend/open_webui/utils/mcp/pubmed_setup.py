"""
Setup script to register PubMed MCP server with Open WebUI
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def get_pubmed_mcp_config() -> dict:
    """Get the PubMed MCP server configuration"""
    return {
        "url": "http://pubmed-mcp:8000/sse",
        "path": "/sse",
        "type": "mcp",
        "auth_type": "none",
        "key": None,
        "config": {},
        "info": {
            "id": "pubmed-mcp",
            "name": "PubMed MCP Server",
            "description": "Medical literature search and comprehensive analysis using PubMed",
            "version": "1.0.0"
        }
    }

async def setup_pubmed_mcp(app_state):
    """
    Automatically setup PubMed MCP if not already configured
    """
    try:
        # Get current tool server connections
        current_connections = app_state.config.get("TOOL_SERVER_CONNECTIONS", [])
        
        # Check if PubMed MCP is already configured
        pubmed_exists = any(
            conn.get("info", {}).get("id") == "pubmed-mcp" 
            for conn in current_connections
        )
        
        if not pubmed_exists:
            logger.info("Setting up PubMed MCP server...")
            pubmed_config = get_pubmed_mcp_config()
            
            # Add PubMed MCP to connections
            current_connections.append(pubmed_config)
            app_state.config["TOOL_SERVER_CONNECTIONS"] = current_connections
            
            logger.info("PubMed MCP server successfully registered")
            return True
        else:
            logger.info("PubMed MCP server already configured")
            return False
            
    except Exception as e:
        logger.error(f"Failed to setup PubMed MCP: {e}")
        return False
