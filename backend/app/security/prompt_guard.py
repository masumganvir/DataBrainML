"""
DataWise AI — Prompt Injection Guard & Input Sanitizer

Protects the Agentic LLM from:
  1. System prompt extraction & override attempts
  2. Jailbreak keywords ("DAN", "ignore previous instructions", "you are now a...")
  3. Role-play bypasses and delimiters injection
  4. Command injection patterns
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class PromptSecurityAssessment:
    is_safe: bool
    risk_score: float  # 0.0 (clean) to 1.0 (malicious)
    flagged_patterns: List[str]
    sanitized_prompt: str
    warning_message: str = ""


# Common injection and jailbreak regex patterns
SUSPICIOUS_PATTERNS = [
    (r"(?i)\bignore\s+(all\s+)?(your\s+)?(previous|prior|above)\s+(instructions|prompts|rules)", "Instruction override"),
    (r"(?i)\bdisregard\s+(all\s+)?(your\s+)?(previous|prior|above)\s+(instructions|prompts|rules)", "Instruction disregard"),
    (r"(?i)\byou\s+are\s+now\s+(an?\s+)?.*?(unrestricted|jailbroken|evil|dan|developer\s+mode)", "Persona override / Jailbreak"),
    (r"(?i)\b(repeat|print|reveal|show|output|leak)\s+(your\s+)?(system\s+prompt|initial\s+instructions|hidden\s+instructions|api\s*key)", "System prompt leak attempt"),
    (r"(?i)\bwhat\s+(is|are)\s+your\s+(system\s+prompt|hidden\s+instructions)", "System prompt probe"),
    (r"(?i)<script\b[^>]*>(.*?)</script>", "XSS Injection"),
    (r"(?i)\b(exec|eval|__import__|os\.system|subprocess\.Popen)\b", "Dangerous python code in prompt"),
    (r"(?i)\[system\s*#", "Special delimiter spoofing"),
    (r"(?i)```python\s*import\s+(os|sys|subprocess|shutil|socket|requests)\b", "Suspicious code block"),
]


class PromptGuard:
    """Evaluates and sanitizes prompts before forwarding them to the LLM agent."""

    def __init__(self, sensitivity: float = 0.5):
        self.sensitivity = sensitivity
        self._compiled_patterns = [
            (re.compile(pat), label) for pat, label in SUSPICIOUS_PATTERNS
        ]

    def evaluate(self, user_text: str) -> PromptSecurityAssessment:
        if not user_text or not user_text.strip():
            return PromptSecurityAssessment(
                is_safe=True,
                risk_score=0.0,
                flagged_patterns=[],
                sanitized_prompt="",
                warning_message="",
            )

        flagged: List[str] = []
        score = 0.0

        for regex, label in self._compiled_patterns:
            if regex.search(user_text):
                flagged.append(label)
                score += 0.35

        score = min(score, 1.0)
        is_safe = len(flagged) == 0 and (score < self.sensitivity)

        sanitized = self._sanitize(user_text)

        warning = ""
        if not is_safe:
            warning = f"Potentially adversarial prompt pattern detected: {', '.join(flagged)}."

        return PromptSecurityAssessment(
            is_safe=is_safe,
            risk_score=round(score, 2),
            flagged_patterns=flagged,
            sanitized_prompt=sanitized,
            warning_message=warning,
        )

    def _sanitize(self, text: str) -> str:
        # Strip null bytes and control characters
        clean = "".join(ch for ch in text if ch == "\n" or ch == "\t" or (32 <= ord(ch) <= 126) or ord(ch) > 127)
        # Neutralize common markdown system token injections
        clean = re.sub(r"(?i)<\|im_start\|>", "", clean)
        clean = re.sub(r"(?i)<\|im_end\|>", "", clean)
        clean = re.sub(r"(?i)<\|endoftext\|>", "", clean)
        return clean.strip()


# Global instance
prompt_guard = PromptGuard()
