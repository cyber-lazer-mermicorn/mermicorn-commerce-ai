#!/usr/bin/env python3
"""
Mermicorn AI Setup — One-Click Free Tier Setup
===============================================
Run this to get all free AI keys configured.

Usage:
    python3 setup_ai.py              # Interactive setup
    python3 setup_ai.py --test       # Test current keys
    python3 setup_ai.py --status     # Show provider status
"""

import os
import sys
import json
import urllib.request
from pathlib import Path


# ════════════════════════════════════════════════════════════════
# PROVIDER SETUP INSTRUCTIONS
# ════════════════════════════════════════════════════════════════

PROVIDERS = {
    "groq": {
        "name": "Groq",
        "url": "https://console.groq.com/keys",
        "env_key": "GROQ_API_KEY",
        "prefix": "gsk_",
        "free_tier": "30 RPM, instant speed",
        "signup_steps": [
            "1. Go to https://console.groq.com",
            "2. Click 'Sign In' (use Google/GitHub)",
            "3. Go to 'API Keys' in left sidebar",
            "4. Click 'Create API Key'",
            "5. Copy the key (starts with gsk_)",
        ],
        "test_url": "https://api.groq.com/openai/v1/chat/completions",
        "test_model": "llama-3.3-70b-versatile",
    },
    "gemini": {
        "name": "Google Gemini",
        "url": "https://aistudio.google.com/apikey",
        "env_key": "GEMINI_API_KEY",
        "prefix": "AI",
        "free_tier": "15 RPM, 1M tokens/day",
        "signup_steps": [
            "1. Go to https://aistudio.google.com/apikey",
            "2. Sign in with Google account",
            "3. Click 'Create API Key'",
            "4. Copy the key",
        ],
        "test_url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
        "test_model": "gemini-2.0-flash",
    },
    "deepseek": {
        "name": "DeepSeek",
        "url": "https://platform.deepseek.com/api_keys",
        "env_key": "DEEPSEEK_API_KEY",
        "prefix": "sk-",
        "free_tier": "500K tokens/day",
        "signup_steps": [
            "1. Go to https://platform.deepseek.com",
            "2. Sign up (email or Google)",
            "3. Go to 'API Keys'",
            "4. Click 'Create new key'",
            "5. Copy the key",
        ],
        "test_url": "https://api.deepseek.com/v1/chat/completions",
        "test_model": "deepseek-chat",
    },
    "mistral": {
        "name": "Mistral AI",
        "url": "https://console.mistral.ai/api-keys",
        "env_key": "MISTRAL_API_KEY",
        "prefix": "",
        "free_tier": "1 RPM, 30K tokens/month",
        "signup_steps": [
            "1. Go to https://console.mistral.ai",
            "2. Sign up (email or Google)",
            "3. Go to 'API Keys'",
            "4. Click 'Create new key'",
            "5. Copy the key",
        ],
        "test_url": "https://api.mistral.ai/v1/chat/completions",
        "test_model": "mistral-small-latest",
    },
    "huggingface": {
        "name": "HuggingFace",
        "url": "https://huggingface.co/settings/tokens",
        "env_key": "HF_API_KEY",
        "prefix": "hf_",
        "free_tier": "1000 requests/day",
        "signup_steps": [
            "1. Go to https://huggingface.co",
            "2. Sign up (email or Google)",
            "3. Go to Settings > Access Tokens",
            "4. Click 'New token'",
            "5. Copy the token (starts with hf_)",
        ],
        "test_url": "https://api-inference.huggingface.co/models/meta-llama/Llama-3.3-70B-Instruct",
        "test_model": "meta-llama/Llama-3.3-70B-Instruct",
    },
}


# ════════════════════════════════════════════════════════════════
# FUNCTIONS
# ════════════════════════════════════════════════════════════════

def load_env(env_path: str = ".env") -> dict[str, str]:
    """Load existing .env file."""
    env = {}
    path = Path(env_path)
    if path.exists():
        for line in path.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                key, _, value = line.partition("=")
                env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def save_env(env: dict[str, str], env_path: str = ".env"):
    """Save to .env file."""
    lines = []
    for key, value in env.items():
        lines.append(f'{key}="{value}"')
    
    with open(env_path, "w") as f:
        f.write("\n".join(lines) + "\n")


def test_key(provider_name: str, key: str) -> bool:
    """Test if an API key works."""
    provider = PROVIDERS[provider_name]
    
    try:
        if provider_name == "groq":
            payload = json.dumps({
                "model": provider["test_model"],
                "messages": [{"role": "user", "content": "Say 'hello' in one word."}],
                "max_tokens": 10,
            }).encode()
            req = urllib.request.Request(provider["test_url"], data=payload, headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key}",
            })
        
        elif provider_name == "gemini":
            url = f"{provider['test_url']}?key={key}"
            payload = json.dumps({
                "contents": [{"parts": [{"text": "Say 'hello' in one word."}]}],
                "generationConfig": {"maxOutputTokens": 10},
            }).encode()
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        
        elif provider_name == "deepseek":
            payload = json.dumps({
                "model": provider["test_model"],
                "messages": [{"role": "user", "content": "Say 'hello' in one word."}],
                "max_tokens": 10,
            }).encode()
            req = urllib.request.Request(provider["test_url"], data=payload, headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key}",
            })
        
        elif provider_name == "mistral":
            payload = json.dumps({
                "model": provider["test_model"],
                "messages": [{"role": "user", "content": "Say 'hello' in one word."}],
                "max_tokens": 10,
            }).encode()
            req = urllib.request.Request(provider["test_url"], data=payload, headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key}",
            })
        
        elif provider_name == "huggingface":
            payload = json.dumps({
                "inputs": "Say 'hello' in one word.",
                "parameters": {"max_new_tokens": 10},
            }).encode()
            req = urllib.request.Request(provider["test_url"], data=payload, headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key}",
            })
        
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status == 200
    
    except Exception:
        return False


def show_status(env: dict[str, str]):
    """Show provider status."""
    print()
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║              MERMICORN AI PROVIDER STATUS                ║")
    print("╠═══════════════════════════════════════════════════════════╣")
    print()
    
    for name, provider in PROVIDERS.items():
        key = env.get(provider["env_key"], "")
        has_key = bool(key)
        
        print(f"  {'✅' if has_key else '❌'} {provider['name']:15} │ {provider['free_tier']}")
        
        if has_key:
            print(f"     Key: {key[:8]}...{key[-4:]}")
            # Test it
            sys.stdout.write("     Testing... ")
            sys.stdout.flush()
            if test_key(name, key):
                print("✅ Working!")
            else:
                print("❌ Failed")
        else:
            print(f"     Get key: {provider['url']}")
        print()
    
    active = sum(1 for n, p in PROVIDERS.items() if env.get(p["env_key"]))
    print(f"  ─────────────────────────────────────────────────────────")
    print(f"  Active: {active}/{len(PROVIDERS)} providers")
    
    if active == 0:
        print()
        print("  ⚡ QUICK START: Get Groq first (fastest free)")
        print(f"     → https://console.groq.com/keys")
    print()


def interactive_setup():
    """Interactive key setup."""
    print()
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║           MERMICORN AI — FREE TIER SETUP                ║")
    print("╠═══════════════════════════════════════════════════════════╣")
    print()
    print("  I'll walk you through getting free AI keys.")
    print("  Each one takes about 2 minutes.")
    print()
    
    env = load_env()
    
    for name, provider in PROVIDERS.items():
        existing = env.get(provider["env_key"], "")
        if existing:
            print(f"  ✅ {provider['name']}: Already configured ({existing[:8]}...)")
            continue
        
        print(f"  ─────────────────────────────────────────────────────────")
        print(f"  📋 {provider['name']} ({provider['free_tier']})")
        print()
        for step in provider["signup_steps"]:
            print(f"     {step}")
        print()
        
        key = input(f"  Paste your {provider['env_key']} (or press Enter to skip): ").strip()
        if key:
            env[provider["env_key"]] = key
            save_env(env)
            
            sys.stdout.write("  Testing... ")
            sys.stdout.flush()
            if test_key(name, key):
                print("✅ Working!")
            else:
                print("⚠️  Key saved but test failed — may need a moment to activate")
        else:
            print(f"  ⏭️  Skipped — get it later at {provider['url']}")
        print()
    
    print("  ════════════════════════════════════════════════════════════")
    show_status(env)


def install_ollama():
    """Install Ollama locally."""
    print()
    print("  📦 Installing Ollama...")
    print()
    print("  macOS:  brew install ollama")
    print("  Linux:  curl -fsSL https://ollama.com/install.sh | sh")
    print()
    print("  Then pull models:")
    print("    ollama pull llama3.3    # Best all-around")
    print("    ollama pull mistral    # Fast")
    print("    ollama pull gemma2     # Google quality")
    print()
    print("  Ollama runs locally = unlimited free AI")


# ════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    args = sys.argv[1:]
    
    if "--test" in args:
        env = load_env()
        show_status(env)
    elif "--status" in args:
        env = load_env()
        show_status(env)
    elif "--ollama" in args:
        install_ollama()
    elif "--setup" in args or len(args) == 0:
        interactive_setup()
    else:
        print("Usage: python3 setup_ai.py [--setup|--test|--status|--ollama]")
