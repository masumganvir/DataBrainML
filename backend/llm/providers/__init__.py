"""
DataWise AI — LLM Providers Package
Primary: Gemini
Fallback 1: Groq
Fallback 2: Cloudflare Workers AI
"""

try:
    from llm.providers.gemini import GeminiProvider
    from llm.providers.groq import GroqProvider
    from llm.providers.cloudflare import CloudflareProvider
except ImportError:
    from backend.llm.providers.gemini import GeminiProvider
    from backend.llm.providers.groq import GroqProvider
    from backend.llm.providers.cloudflare import CloudflareProvider

__all__ = ["GeminiProvider", "GroqProvider", "CloudflareProvider"]
