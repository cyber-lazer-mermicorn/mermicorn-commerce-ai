"""
Mermicorn Vision — Image Analysis Engine
=========================================
Real vision: see coins, vehicles, clothing, screenshots.
"""

from __future__ import annotations

import base64
import json
import os
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass(slots=True)
class VisionResult:
    """Result from image analysis."""
    success: bool
    description: str
    identified_items: list[dict[str, Any]]
    confidence: float
    details: dict[str, Any]
    model: str
    latency_ms: float
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "description": self.description,
            "identified_items": self.identified_items,
            "confidence": self.confidence,
            "details": self.details,
            "model": self.model,
            "latency_ms": self.latency_ms,
            "timestamp": self.timestamp,
        }


class MermicornVision:
    """
    Real vision engine using GPT-4o multimodal.
    
    Capabilities:
    - See and identify coins from photos
    - Assess vehicle condition from images
    - Analyze clothing designs
    - Read text from screenshots
    - Compare items visually
    """
    
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.model = "gpt-4o"
        self.analyses: list[VisionResult] = []
    
    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64."""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    
    def _call_vision(self, image_b64: str, prompt: str, system: str = "") -> dict[str, Any]:
        """Call OpenAI Vision API."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_b64}",
                        "detail": "high",
                    },
                },
            ],
        })
        
        payload = json.dumps({
            "model": self.model,
            "messages": messages,
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
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read())
        except Exception as e:
            return {"error": str(e)}
    
    def analyze_image(self, image_path: str, task: str = "identify") -> VisionResult:
        """Analyze an image."""
        start = time.time()
        
        if not self.api_key:
            return VisionResult(
                success=False,
                description="No API key configured",
                identified_items=[],
                confidence=0.0,
                details={"error": "Set OPENAI_API_KEY"},
                model=self.model,
                latency_ms=0,
            )
        
        image_b64 = self._encode_image(image_path)
        
        prompts = {
            "identify": "Identify everything in this image. Provide JSON with: items (list of identified items with name, category, features, confidence), description (overall description), setting (where this was taken/used).",
            "grade": "Grade the item in this image. Provide JSON with: item_name, grade (A-F or numeric), condition (excellent/good/fair/poor), key_factors (list), defects (list), estimated_value (low/mid/high), confidence.",
            "compare": "Compare these two items visually. Provide JSON with: similarities, differences, quality_comparison, recommendation, confidence.",
            "read_text": "Read all text visible in this image. Provide JSON with: text (all text found), structured_data (parsed data if any), language, confidence.",
            "design": "Analyze this design/image aesthetically. Provide JSON with: style, colors (hex codes), mood, target_audience, suggestions, confidence.",
        }
        
        system = "You are an expert visual analyst. Always respond with valid JSON."
        prompt = prompts.get(task, prompts["identify"])
        
        response = self._call_vision(image_b64, prompt, system)
        latency = (time.time() - start) * 1000
        
        try:
            content = response["choices"][0]["message"]["content"]
            # Parse JSON from response
            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code block
                if "```json" in content:
                    json_str = content.split("```json")[1].split("```")[0]
                    data = json.loads(json_str)
                elif "```" in content:
                    json_str = content.split("```")[1].split("```")[0]
                    data = json.loads(json_str)
                else:
                    data = {"raw_text": content}
            
            return VisionResult(
                success=True,
                description=data.get("description", str(data)[:200]),
                identified_items=data.get("items", []),
                confidence=data.get("confidence", 0.8),
                details=data,
                model=self.model,
                latency_ms=latency,
            )
        except (KeyError, IndexError) as e:
            return VisionResult(
                success=False,
                description=f"Parse error: {e}",
                identified_items=[],
                confidence=0.0,
                details={"error": str(e), "raw": response},
                model=self.model,
                latency_ms=latency,
            )
    
    def see_coin(self, image_path: str) -> VisionResult:
        """Identify and grade a coin from photo."""
        return self.analyze_image(image_path, task="grade")
    
    def see_vehicle(self, image_path: str) -> VisionResult:
        """Identify and assess a vehicle from photo."""
        return self.analyze_image(image_path, task="identify")
    
    def see_clothing(self, image_path: str) -> VisionResult:
        """Analyze clothing design from photo."""
        return self.analyze_image(image_path, task="design")
    
    def read_screenshot(self, image_path: str) -> VisionResult:
        """Read text/data from screenshot."""
        return self.analyze_image(image_path, task="read_text")
    
    def compare_images(self, image1_path: str, image2_path: str) -> VisionResult:
        """Compare two images."""
        # For comparison, we'd need to send both images
        # This is a simplified version
        result1 = self.analyze_image(image1_path, task="identify")
        result2 = self.analyze_image(image2_path, task="identify")
        
        return VisionResult(
            success=result1.success and result2.success,
            description=f"Comparison: {result1.description} vs {result2.description}",
            identified_items=result1.identified_items + result2.identified_items,
            confidence=min(result1.confidence, result2.confidence),
            details={"image1": result1.details, "image2": result2.details},
            model=self.model,
            latency_ms=result1.latency_ms + result2.latency_ms,
        )
    
    def get_stats(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "api_configured": bool(self.api_key),
            "analyses_performed": len(self.analyses),
        }


# Standalone usage
if __name__ == "__main__":
    vision = MermicornVision()
    print("👁️ Mermicorn Vision")
    print(f"   Model: {vision.model}")
    print(f"   API: {'✅' if vision.api_key else '❌ Set OPENAI_API_KEY'}")
    print()
    print("Usage:")
    print('  vision.see_coin("coin.jpg")')
    print('  vision.see_vehicle("car.jpg")')
    print('  vision.see_clothing("design.jpg")')
    print('  vision.read_screenshot("screenshot.png")')
    print('  vision.compare_images("before.jpg", "after.jpg")')
