"""
Mermicorn AI — Multi-Provider Intelligence
===========================================
Free tier AI: Gemini, Groq, Mistral, DeepSeek, HuggingFace, Ollama
"""

from __future__ import annotations

import json
import os
import time
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(slots=True)
class AIResult:
    """Result from AI call."""
    success: bool
    data: dict[str, Any]
    reasoning: str
    confidence: float
    model: str
    provider: str
    latency_ms: float
    cached: bool = False
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success, "data": self.data,
            "reasoning": self.reasoning, "confidence": self.confidence,
            "model": self.model, "provider": self.provider,
            "latency_ms": self.latency_ms, "cached": self.cached,
        }


# ════════════════════════════════════════════════════════════════
# PROVIDERS
# ════════════════════════════════════════════════════════════════

class Provider:
    """Base AI provider."""
    name: str = "base"
    models: list[str] = []
    free_tier: str = ""
    
    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self.calls = 0
    
    def generate(self, prompt: str, model: str = "", **kwargs) -> dict[str, Any]:
        raise NotImplementedError
    
    def is_available(self) -> bool:
        return bool(self.api_key)


class GeminiProvider(Provider):
    """Google Gemini — FREE: 15 RPM, 1M tokens/day"""
    name = "gemini"
    models = ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"]
    free_tier = "15 RPM, 1M tokens/day"
    
    def generate(self, prompt: str, model: str = "gemini-2.0-flash", **kwargs) -> dict[str, Any]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
        
        payload = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": kwargs.get("temperature", 0.7),
                "maxOutputTokens": kwargs.get("max_tokens", 2048),
            },
        }).encode()
        
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read())
                text = result["candidates"][0]["content"]["parts"][0]["text"]
                self.calls += 1
                return {"text": text, "model": model}
        except Exception as e:
            return {"error": str(e)}


class GroqProvider(Provider):
    """Groq — FREE: 30 RPM, fast inference"""
    name = "groq"
    models = ["llama-3.3-70b-versatile", "mixtral-8x7b-32768", "gemma2-9b-it"]
    free_tier = "30 RPM, instant speed"
    
    def generate(self, prompt: str, model: str = "llama-3.3-70b-versatile", **kwargs) -> dict[str, Any]:
        url = "https://api.groq.com/openai/v1/chat/completions"
        
        payload = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2048),
        }).encode()
        
        req = urllib.request.Request(url, data=payload, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "MermicornAI/1.0",
        })
        
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read())
                text = result["choices"][0]["message"]["content"]
                self.calls += 1
                return {"text": text, "model": model}
        except Exception as e:
            return {"error": str(e)}


class MistralProvider(Provider):
    """Mistral AI — FREE: 1 RPM, 30K tokens/month"""
    name = "mistral"
    models = ["mistral-small-latest", "mistral-medium-latest", "open-mixtral-8x22b"]
    free_tier = "1 RPM, 30K tokens/month"
    
    def generate(self, prompt: str, model: str = "mistral-small-latest", **kwargs) -> dict[str, Any]:
        url = "https://api.mistral.ai/v1/chat/completions"
        
        payload = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2048),
        }).encode()
        
        req = urllib.request.Request(url, data=payload, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "MermicornAI/1.0",
        })
        
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read())
                text = result["choices"][0]["message"]["content"]
                self.calls += 1
                return {"text": text, "model": model}
        except Exception as e:
            return {"error": str(e)}


class DeepSeekProvider(Provider):
    """DeepSeek — FREE: 500K tokens/day"""
    name = "deepseek"
    models = ["deepseek-chat", "deepseek-reasoner"]
    free_tier = "500K tokens/day"
    
    def generate(self, prompt: str, model: str = "deepseek-chat", **kwargs) -> dict[str, Any]:
        url = "https://api.deepseek.com/v1/chat/completions"
        
        payload = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2048),
        }).encode()
        
        req = urllib.request.Request(url, data=payload, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "MermicornAI/1.0",
        })
        
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read())
                text = result["choices"][0]["message"]["content"]
                self.calls += 1
                return {"text": text, "model": model}
        except Exception as e:
            return {"error": str(e)}


class HuggingFaceProvider(Provider):
    """HuggingFace — FREE: 1000 req/day"""
    name = "huggingface"
    models = ["meta-llama/Llama-3.3-70B-Instruct", "Qwen/Qwen2.5-72B-Instruct"]
    free_tier = "1000 requests/day"
    
    def generate(self, prompt: str, model: str = "meta-llama/Llama-3.3-70B-Instruct", **kwargs) -> dict[str, Any]:
        url = f"https://api-inference.huggingface.co/models/{model}"
        
        payload = json.dumps({
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": kwargs.get("max_tokens", 2048),
                "temperature": kwargs.get("temperature", 0.7),
            },
        }).encode()
        
        req = urllib.request.Request(url, data=payload, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "MermicornAI/1.0",
        })
        
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read())
                text = result[0]["generated_text"] if isinstance(result, list) else str(result)
                self.calls += 1
                return {"text": text, "model": model}
        except Exception as e:
            return {"error": str(e)}


class OllamaProvider(Provider):
    """Ollama — FREE: unlimited, runs locally"""
    name = "ollama"
    models = ["llama3.3", "mistral", "gemma2", "qwen2.5", "deepseek-r1"]
    free_tier = "Unlimited (local)"
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url or os.environ.get("OLLAMA_URL", "http://localhost:11434")
        self.api_key = "local"
    
    def is_available(self) -> bool:
        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags")
            urllib.request.urlopen(req, timeout=5)
            return True
        except Exception:
            return False
    
    def generate(self, prompt: str, model: str = "llama3.3", **kwargs) -> dict[str, Any]:
        url = f"{self.base_url}/api/generate"
        
        payload = json.dumps({
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", 0.7),
                "num_predict": kwargs.get("max_tokens", 2048),
            },
        }).encode()
        
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                result = json.loads(resp.read())
                self.calls += 1
                return {"text": result.get("response", ""), "model": model}
        except Exception as e:
            return {"error": str(e)}


# ════════════════════════════════════════════════════════════════
# MULTI-PROVIDER AI
# ════════════════════════════════════════════════════════════════

class MermicornAI:
    """
    Multi-provider AI with automatic fallback.
    
    Tries providers in order:
    1. Ollama (local, unlimited)
    2. Groq (fast, free)
    3. Gemini (generous free)
    4. DeepSeek (large free tier)
    5. Mistral (free)
    6. HuggingFace (free)
    7. OpenAI (paid fallback)
    """
    
    def __init__(self):
        self.providers: list[Provider] = []
        self.cache: dict[str, dict] = {}
        self._init_providers()
    
    def _init_providers(self):
        """Initialize available providers."""
        # Order by free tier generosity
        ollama = OllamaProvider()
        if ollama.is_available():
            self.providers.append(ollama)
        
        if os.environ.get("GROQ_API_KEY"):
            self.providers.append(GroqProvider(os.environ["GROQ_API_KEY"]))
        
        if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
            key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
            self.providers.append(GeminiProvider(key))
        
        if os.environ.get("DEEPSEEK_API_KEY"):
            self.providers.append(DeepSeekProvider(os.environ["DEEPSEEK_API_KEY"]))
        
        if os.environ.get("MISTRAL_API_KEY"):
            self.providers.append(MistralProvider(os.environ["MISTRAL_API_KEY"]))
        
        if os.environ.get("HF_API_KEY") or os.environ.get("HUGGINGFACE_API_KEY"):
            key = os.environ.get("HF_API_KEY") or os.environ.get("HUGGINGFACE_API_KEY")
            self.providers.append(HuggingFaceProvider(key))
        
        if os.environ.get("OPENAI_API_KEY"):
            self.providers.append(OpenAIProvider(os.environ["OPENAI_API_KEY"]))
    
    def generate(self, prompt: str, **kwargs) -> AIResult:
        """Generate with automatic fallback."""
        # Check cache
        cache_key = f"{prompt[:100]}:{json.dumps(kwargs, sort_keys=True)}"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            return AIResult(**cached, cached=True)
        
        # Try providers
        last_error = ""
        for provider in self.providers:
            try:
                start = time.time()
                result = provider.generate(prompt, **kwargs)
                latency = (time.time() - start) * 1000
                
                if "error" in result:
                    last_error = result["error"]
                    continue
                
                # Parse JSON from response
                text = result.get("text", "")
                data = self._parse_json(text)
                
                ai_result = AIResult(
                    success=True,
                    data=data,
                    reasoning=text[:200],
                    confidence=0.85,
                    model=result.get("model", "unknown"),
                    provider=provider.name,
                    latency_ms=latency,
                )
                
                # Cache
                self.cache[cache_key] = ai_result.to_dict()
                return ai_result
            except Exception as e:
                last_error = str(e)
                continue
        
        return AIResult(
            success=False,
            data={},
            reasoning=f"All providers failed: {last_error}",
            confidence=0.0,
            model="none",
            provider="none",
            latency_ms=0,
        )
    
    def _parse_json(self, text: str) -> dict[str, Any]:
        """Parse JSON from AI response."""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            if "```json" in text:
                try:
                    json_str = text.split("```json")[1].split("```")[0]
                    return json.loads(json_str)
                except Exception:
                    pass
            elif "```" in text:
                try:
                    json_str = text.split("```")[1].split("```")[0]
                    return json.loads(json_str)
                except Exception:
                    pass
            return {"raw_text": text}
    
    def get_stats(self) -> dict[str, Any]:
        return {
            "providers": [
                {"name": p.name, "available": p.is_available(), "calls": p.calls,
                 "free_tier": p.free_tier, "models": p.models[:3]}
                for p in self.providers
            ],
            "cache_size": len(self.cache),
            "total_calls": sum(p.calls for p in self.providers),
        }


class OpenAIProvider(Provider):
    """OpenAI — paid fallback."""
    name = "openai"
    models = ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"]
    free_tier = "None (paid)"
    
    def __init__(self, api_key: str = ""):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.calls = 0
    
    def generate(self, prompt: str, model: str = "gpt-4o", **kwargs) -> dict[str, Any]:
        url = "https://api.openai.com/v1/chat/completions"
        
        payload = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2048),
        }).encode()
        
        req = urllib.request.Request(url, data=payload, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "MermicornAI/1.0",
        })
        
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read())
                text = result["choices"][0]["message"]["content"]
                self.calls += 1
                return {"text": text, "model": model}
        except Exception as e:
            return {"error": str(e)}
