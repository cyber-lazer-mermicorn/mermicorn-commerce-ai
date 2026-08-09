"""
Mermicorn AI Core — Shared intelligence layer
==============================================
Provides LLM, vision, and automation capabilities across all verticals.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass(slots=True)
class AIResult:
    """Result from an AI operation."""
    success: bool
    data: dict[str, Any]
    confidence: float
    reasoning: str
    model: str
    latency_ms: float
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "model": self.model,
            "latency_ms": self.latency_ms,
            "timestamp": self.timestamp,
        }


class MermicornAI:
    """
    Core AI engine for the Mermicorn constellation.
    
    Provides:
    - LLM inference (text generation, analysis)
    - Vision analysis (image understanding)
    - Structured extraction (JSON from text)
    - Grading/valuation (item assessment)
    - Listing generation (marketplace content)
    """
    
    def __init__(self, api_key: str | None = None, model: str = "gpt-4o"):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.model = model
        self._cache: dict[str, AIResult] = {}
    
    def _call_llm(self, prompt: str, system: str = "", temperature: float = 0.3) -> dict[str, Any]:
        """Call OpenAI API. Returns raw response."""
        import urllib.request
        
        if not self.api_key:
            return self._mock_response(prompt)
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        payload = json.dumps({
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 2000,
        }).encode()
        
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )
        
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())
        except Exception as e:
            return self._mock_response(prompt, str(e))
    
    def _mock_response(self, prompt: str, error: str = "") -> dict[str, Any]:
        """Fallback when no API key or error occurs."""
        return {
            "choices": [{"message": {"content": json.dumps({
                "analysis": "Mock response — connect OPENAI_API_KEY for real AI",
                "prompt_received": prompt[:100],
                "error": error,
            })}}],
            "usage": {"total_tokens": 0},
        }
    
    def analyze(self, text: str, task: str = "general", system: str = "") -> AIResult:
        """General text analysis."""
        start = time.time()
        
        default_systems = {
            "grading": "You are an expert grader. Analyze the item and provide: grade (A-F), confidence (0-1), key factors, estimated value.",
            "listing": "You are a marketplace listing expert. Generate: title, headline, bullets (5), description, SEO keywords, suggested price.",
            "research": "You are a research analyst. Provide: summary, key findings, confidence level, sources needed, recommended actions.",
            "identification": "You are an identification expert. Identify the item and provide: name, category, features, estimated age, condition, rarity.",
            "valuation": "You are a valuation expert. Provide: estimated value range (low/mid/high), factors affecting value, market conditions, comparable sales.",
        }
        
        if not system:
            system = default_systems.get(task, "You are a helpful AI assistant. Provide structured JSON response.")
        
        response = self._call_llm(prompt=text, system=system)
        latency = (time.time() - start) * 1000
        
        try:
            content = response["choices"][0]["message"]["content"]
            # Try to parse as JSON
            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                data = {"text": content}
            
            tokens = response.get("usage", {}).get("total_tokens", 0)
            
            return AIResult(
                success=True,
                data=data,
                confidence=data.get("confidence", 0.8),
                reasoning=data.get("reasoning", data.get("analysis", "")),
                model=self.model,
                latency_ms=latency,
            )
        except (KeyError, IndexError) as e:
            return AIResult(
                success=False,
                data={"error": str(e)},
                confidence=0.0,
                reasoning=f"Failed to parse AI response",
                model=self.model,
                latency_ms=latency,
            )
    
    def grade_item(self, description: str, item_type: str = "general") -> AIResult:
        """Grade an item (coin, vehicle, clothing, etc.)."""
        prompt = f"""Grade this {item_type}:

{description}

Provide JSON with:
- grade: letter grade (A+ through F)
- score: numeric score (0-100)
- confidence: how confident you are (0-1)
- factors: list of key factors affecting grade
- estimated_value: price range (low, mid, high)
- reasoning: explanation of grade"""
        
        return self.analyze(prompt, task="grading")
    
    def identify_item(self, description: str, context: str = "") -> AIResult:
        """Identify an item from description or features."""
        prompt = f"""Identify this item:

Description: {description}
{f"Context: {context}" if context else ""}

Provide JSON with:
- name: item name
- category: category
- maker/brand: if known
- year/era: estimated
- features: key features
- rarity: common/uncommon/rare/very_rare/legendary
- confidence: 0-1"""
        
        return self.analyze(prompt, task="identification")
    
    def generate_listing(self, item_data: dict[str, Any], marketplace: str = "general") -> AIResult:
        """Generate a marketplace listing."""
        prompt = f"""Generate a marketplace listing for:

{json.dumps(item_data, indent=2)}

Marketplace: {marketplace}

Provide JSON with:
- title: optimized title (max 80 chars)
- headline: compelling headline
- bullets: 5 bullet points
- description: full description (150-300 words)
- seo_keywords: list of SEO keywords
- suggested_price: recommended price
- cta: call to action text"""
        
        return self.analyze(prompt, task="listing")
    
    def research_topic(self, topic: str, context: str = "") -> AIResult:
        """Research a topic and provide analysis."""
        prompt = f"""Research this topic:

Topic: {topic}
{f"Context: {context}" if context else ""}

Provide JSON with:
- summary: 2-3 sentence summary
- key_findings: list of key findings
- confidence: 0-1
- sources_needed: list of sources to verify
- recommended_actions: what to do next
- estimated_time: time needed for full research"""
        
        return self.analyze(prompt, task="research")
    
    def value_item(self, description: str, comparable_sales: list[dict] | None = None) -> AIResult:
        """Provide valuation for an item."""
        prompt = f"""Value this item:

{description}
{f"Comparable sales: {json.dumps(comparable_sales)}" if comparable_sales else ""}

Provide JSON with:
- low_value: conservative estimate
- mid_value: likely estimate
- high_value: optimistic estimate
- factors: list of factors affecting value
- market_conditions: current market state
- confidence: 0-1
- reasoning: explanation"""
        
        return self.analyze(prompt, task="valuation")
    
    def generate_auction_message(self, item_data: dict[str, Any], auction_type: str = "standard") -> AIResult:
        """Generate auction listing message."""
        prompt = f"""Generate an auction listing message for:

{json.dumps(item_data, indent=2)}

Auction type: {auction_type}

Provide JSON with:
- headline: attention-grabbing headline
- opening_bid: suggested opening bid
- description: compelling description
- highlights: 5 key highlights
- shipping: shipping info
- return_policy: return policy
- terms: key terms"""
        
        return self.analyze(prompt, task="listing")
    
    def get_stats(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "api_configured": bool(self.api_key),
            "cache_size": len(self._cache),
        }
