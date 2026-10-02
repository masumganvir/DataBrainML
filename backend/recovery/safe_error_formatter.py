"""
Safe Error Formatter
Separates internal diagnostics from user-facing error presentations.
Constructs consistent, actionable error UX with zero credential or traceback leaks.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Union
from recovery.policies import ErrorCode, RecoveryDecisionState
from recovery.context_sanitizer import OutputSecurityGate


class SafeErrorFormatter:
    """Formats internal error objects into standardized user-facing external responses."""

    @classmethod
    def format_user_panel(
        cls,
        error_id: str,
        status: Union[str, RecoveryDecisionState],
        stage: str,
        what_happened: str,
        reason: str,
        recovery_attempted: str,
        recovery_result: str,
        recommended_action: str,
        reference_id: Optional[str] = None,
    ) -> str:
        """Constructs human-friendly, clean UI markdown panel."""
        ref = reference_id or error_id
        safe_what = OutputSecurityGate.sanitize_text(what_happened)
        safe_reason = OutputSecurityGate.sanitize_text(reason)
        safe_attempt = OutputSecurityGate.sanitize_text(recovery_attempted)
        safe_res = OutputSecurityGate.sanitize_text(recovery_result)
        safe_action = OutputSecurityGate.sanitize_text(recommended_action)

        lines = [
            f"Error ID: {error_id}",
            f"Status: {str(status)}",
            f"Stage: {stage}",
            "",
            "What happened:",
            safe_what,
            "",
            "Reason:",
            safe_reason,
            "",
            "Recovery attempted:",
            safe_attempt,
            "",
            "Result:",
            safe_res,
            "",
            "Recommended action:",
            safe_action,
            "",
            f"Reference: {ref}",
        ]
        return "\n".join(lines)

    @classmethod
    def format_api_response(
        cls,
        error_id: str,
        error_code: Union[str, ErrorCode],
        message: str,
        hint: str,
        retryable: bool = False,
        status: Optional[str] = None,
        reference_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Returns standard external API response contract."""
        code_str = error_code.value if isinstance(error_code, ErrorCode) else str(error_code)
        payload = {
            "success": False,
            "error": {
                "id": error_id,
                "code": code_str,
                "message": OutputSecurityGate.sanitize_text(message),
                "hint": OutputSecurityGate.sanitize_text(hint),
                "retryable": bool(retryable),
                "status": status or "Safe Stop",
                "reference_id": reference_id or error_id,
            },
        }
        return payload

    @classmethod
    def format_security_incident_response(cls, incident_id: str) -> Dict[str, Any]:
        """Returns uniform safe response for security-blocked actions."""
        return {
            "success": False,
            "error": {
                "id": incident_id,
                "code": ErrorCode.ERR_SECURITY_BLOCKED.value,
                "message": "Processing was stopped because the system detected a security-sensitive operation.",
                "hint": "No protected information was included in this response. Contact security administrators if this was unexpected.",
                "retryable": False,
                "status": RecoveryDecisionState.SECURITY_STOP.value,
            },
        }
