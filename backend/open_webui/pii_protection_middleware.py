"""
PII Protection Middleware for Open WebUI
Intercepts chat messages and sanitizes sensitive patient data
"""

import logging
from typing import Callable, Any
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import json

from open_webui.middleware_pii import PIIFilter

logger = logging.getLogger(__name__)


class PIIProtectionMiddleware(BaseHTTPMiddleware):
    """
    Middleware that intercepts chat completion requests and sanitizes PII
    """

    def __init__(self, app):
        super().__init__(app)
        self.pii_filter = PIIFilter(strict_mode=False)

    async def dispatch(self, request: Request, call_next: Callable) -> Any:
        """
        Process request and sanitize PII in chat messages
        """
        # Only intercept chat completion requests
        pii_detected = False
        pii_types = []
        if request.url.path.endswith(("/v1/chat/completions", "/api/chat/completions")):
            if request.method == "POST":
                try:
                    # Get request body
                    body = await request.body()

                    if body:
                        try:
                            data = json.loads(body)
                        except json.JSONDecodeError:
                            # If not JSON, pass through
                            return await call_next(request)

                        # Extract user messages
                        messages = data.get("messages", [])
                        user_message_idx = None

                        # Find the last user message
                        for idx in range(len(messages) - 1, -1, -1):
                            if messages[idx].get("role") == "user":
                                user_message_idx = idx
                                user_message = messages[idx].get("content", "")
                                break

                        if user_message_idx is not None and user_message:
                            logger.info(f"[PII] Checking message: {user_message[:100]}...")

                            # Detect and sanitize PII
                            detection_result = self.pii_filter.detect_pii(user_message)

                            if not detection_result.is_safe:
                                # Sanitize the message
                                sanitized_message = self.pii_filter.sanitize_query(user_message)

                                # Detected PII types
                                detected_types = list(detection_result.found_pii.keys())
                                detected_type_names = [pii.value for pii in detected_types]

                                logger.warning(
                                    f"[PII] Detected sensitive data: {detected_type_names}"
                                )
                                logger.info(
                                    f"[PII] ORIGINAL → {user_message}"
                                )
                                logger.info(
                                    f"[PII] SANITIZED → {sanitized_message}"
                                )

                                # Replace the message with sanitized version
                                messages[user_message_idx]["content"] = sanitized_message
                                data["messages"] = messages

                                # Update request body
                                body = json.dumps(data).encode()
                                request._body = body

                                # Mark detection for response signaling
                                pii_detected = True
                                pii_types = detected_type_names

                            else:
                                logger.info("[PII] Message passed validation")

                except Exception as e:
                    logger.error(f"[PII] Middleware error: {e}", exc_info=True)
                    # On error, pass through

        # Pass request to next middleware/route
        response = await call_next(request)

        # Signal PII detection to clients via headers (non-breaking, extensible)
        try:
            if pii_detected:
                response.headers["X-PII-Detected"] = "true"
                if pii_types:
                    response.headers["X-PII-Types"] = ",".join(pii_types)
        except Exception:
            # never fail the request on header set
            pass

        return response
