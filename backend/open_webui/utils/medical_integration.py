"""
Medical integration middleware for Open WebUI
Automatically applies medical prompts and tools for health-related queries
Supports bilingual prompts (Portuguese and English)
Automatically enables PubMed MCP for medical queries
"""
import logging
from typing import Optional, List, Dict, Any
from open_webui.utils.medical_prompts import (
    get_medical_system_prompt,
    detect_language,
    is_medical_query
)

logger = logging.getLogger(__name__)

# PubMed MCP Configuration
PUBMED_MCP_ID = "pubmed-mcp"
PUBMED_MCP_TOOL_ID = f"server:mcp:{PUBMED_MCP_ID}"

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
            "id": PUBMED_MCP_ID,
            "name": "PubMed MCP Server",
            "description": "Medical literature search and comprehensive analysis using PubMed",
            "version": "1.0.0"
        }
    }

def ensure_pubmed_mcp_registered(app_state) -> bool:
    """
    Ensure PubMed MCP is registered in TOOL_SERVER_CONNECTIONS

    Args:
        app_state: The application state object containing config

    Returns:
        True if MCP is now available, False if there was an error
    """
    try:
        # Get current tool server connections
        if not hasattr(app_state, 'config'):
            logger.warning("[Medical] app_state doesn't have config attribute")
            return False

        current_connections = app_state.config.get("TOOL_SERVER_CONNECTIONS", [])
        if not isinstance(current_connections, list):
            current_connections = []

        # Check if PubMed MCP is already configured
        pubmed_exists = any(
            conn.get("info", {}).get("id") == PUBMED_MCP_ID
            for conn in current_connections
        )

        if not pubmed_exists:
            logger.info("[Medical] 🔧 Registering PubMed MCP server for medical query...")
            pubmed_config = get_pubmed_mcp_config()

            # Add PubMed MCP to connections
            current_connections.append(pubmed_config)
            app_state.config["TOOL_SERVER_CONNECTIONS"] = current_connections

            logger.info(f"[Medical] ✅ PubMed MCP server successfully registered (ID: {PUBMED_MCP_ID})")
            return True
        else:
            logger.debug(f"[Medical] PubMed MCP server already registered")
            return True

    except Exception as e:
        logger.error(f"[Medical] ✗ Failed to register PubMed MCP: {e}", exc_info=True)
        return False

def auto_select_medical_tools(form_data: Dict[str, Any], app_state) -> Dict[str, Any]:
    """
    Automatically enable PubMed MCP tools for medical queries

    Args:
        form_data: The chat form data
        app_state: The application state object

    Returns:
        Modified form_data with PubMed MCP tool_id added
    """
    try:
        # Extract the user query
        messages = form_data.get("messages", [])
        query = None

        if messages:
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    query = msg.get("content", "")
                    if isinstance(query, list):
                        query = " ".join([
                            item.get("text", "")
                            for item in query
                            if isinstance(item, dict) and "text" in item
                        ])
                    break

        # Check if this is a medical query
        if query and is_medical_query(query):
            # Ensure MCP is registered
            if ensure_pubmed_mcp_registered(app_state):
                # Get current tool_ids
                tool_ids = form_data.get("tool_ids", [])
                if not isinstance(tool_ids, list):
                    tool_ids = []

                # Add PubMed MCP tool if not already present
                if PUBMED_MCP_TOOL_ID not in tool_ids:
                    tool_ids.append(PUBMED_MCP_TOOL_ID)
                    form_data["tool_ids"] = tool_ids
                    logger.info(f"[Medical] 🔧 Auto-enabled PubMed MCP tool for medical query")
                else:
                    logger.debug(f"[Medical] PubMed MCP tool already enabled")

    except Exception as e:
        logger.error(f"[Medical] ✗ Error auto-selecting medical tools: {e}", exc_info=True)

    return form_data

def enhance_medical_request(body: Dict[str, Any], query: Optional[str] = None) -> Dict[str, Any]:
    """
    Enhance a chat request with medical system prompt if it's a medical query
    Automatically detects query language and injects prompt in the same language

    Args:
        body: The chat completion request body
        query: The user's query text (optional, can extract from messages)

    Returns:
        Modified request body with medical enhancements
    """
    try:
        # Extract user message if not provided
        if not query:
            messages = body.get("messages", [])
            if messages:
                # Get the last user message
                for msg in reversed(messages):
                    if msg.get("role") == "user":
                        query = msg.get("content", "")
                        if isinstance(query, list):
                            query = " ".join([
                                item.get("text", "")
                                for item in query
                                if isinstance(item, dict) and "text" in item
                            ])
                        break

        # Check if query is medical
        if query and is_medical_query(query):
            messages = body.get("messages", [])
            logger.info(f"[Medical] ✓ Medical query detected: '{query[:80]}...'")
            logger.info(f"[Medical] Messages before enhancement: {len(messages)}")

            # Detect language of the query
            detected_language = detect_language(query)
            lang_display = "🇵🇹 Portuguese" if detected_language == "pt" else "🇬🇧 English"
            logger.info(f"[Medical] Language detected: {lang_display}")

            # Get or create messages list
            if "messages" not in body:
                body["messages"] = []

            messages = body["messages"]

            # Check if system message exists
            system_message_exists = any(msg.get("role") == "system" for msg in messages)

            if not system_message_exists:
                # Add medical system prompt in the detected language
                medical_prompt = get_medical_system_prompt(language=detected_language)
                system_message = {
                    "role": "system",
                    "content": medical_prompt
                }
                # Insert system message at the beginning
                messages.insert(0, system_message)
                body["messages"] = messages

                logger.info(f"[Medical] ✓ Medical system prompt ADDED ({lang_display}) - Messages after: {len(messages)}")
            else:
                # Log that system message already exists
                logger.info("[Medical] ⚠ System message already exists, skipping prompt injection")

        return body

    except Exception as e:
        logger.error(f"[Medical] ✗ Error enhancing medical request: {e}", exc_info=True)
        return body

def log_medical_response(query: Optional[str], response: str) -> None:
    """
    Log medical queries and responses for analysis
    
    Args:
        query: The user's query
        response: The model's response
    """
    try:
        if query and is_medical_query(query):
            logger.info(f"[Medical] Query: {query[:100]}...")
            logger.info(f"[Medical] Response: {response[:200]}...")
    except Exception as e:
        logger.error(f"[Medical] Error logging medical response: {e}")
