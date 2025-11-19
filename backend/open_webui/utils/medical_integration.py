"""
Medical integration middleware for Open WebUI
Automatically applies medical prompts and tools for health-related queries
"""
import logging
from typing import Optional, List, Dict, Any
from open_webui.utils.medical_prompts import get_medical_system_prompt, is_medical_query

logger = logging.getLogger(__name__)

def enhance_medical_request(body: Dict[str, Any], query: Optional[str] = None) -> Dict[str, Any]:
    """
    Enhance a chat request with medical system prompt if it's a medical query

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

            # Get or create messages list
            if "messages" not in body:
                body["messages"] = []

            messages = body["messages"]

            # Check if system message exists
            system_message_exists = any(msg.get("role") == "system" for msg in messages)

            if not system_message_exists:
                # Add medical system prompt
                medical_prompt = get_medical_system_prompt()
                system_message = {
                    "role": "system",
                    "content": medical_prompt
                }
                # Insert system message at the beginning
                messages.insert(0, system_message)
                body["messages"] = messages

                logger.info(f"[Medical] ✓ Medical system prompt ADDED - Messages after: {len(messages)}")
            else:
                # Append medical instructions to existing system message
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
