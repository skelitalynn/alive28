import base64
import random
import urllib.parse
import urllib.request
import json
from typing import Optional


def _build_prompt(day_index: int, task_title: str, user_text: str, reflection_note: str) -> str:
    return (
        "Create a beautiful, abstract digital art piece for a personal growth NFT collection.\n"
        f"Theme: \"Day {day_index} of 28 - {task_title}\"\n"
        f"User mood keywords: {user_text[:200]}\n"
        f"Reflection note: {reflection_note[:120]}\n"
        "Style: modern digital art, clean composition, vibrant yet harmonious colors.\n"
        "No text, no words, no letters in the image."
    )


def _pollinations_image(prompt: str) -> Optional[str]:
    encoded = urllib.parse.quote(prompt)
    seed = random.randint(1, 1_000_000)
    url = f"https://pollinations.ai/p/{encoded}?width=1024&height=1024&seed={seed}&model=flux"
    req = urllib.request.Request(url, headers={"User-Agent": "alive28-mvp"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        content_type = resp.headers.get("Content-Type") or ""
        if not content_type.startswith("image"):
            return None
        data = resp.read()
        b64 = base64.b64encode(data).decode("ascii")
        return f"data:{content_type};base64,{b64}"


def _gemini_image(prompt: str, api_key: str) -> Optional[str]:
    if not api_key:
        return None
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        "gemini-2.5-flash-image:generateContent?key="
        + api_key
    )
    body = json.dumps(
        {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]},
        }
    ).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    parts = payload.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    for part in parts:
        inline = part.get("inlineData") or {}
        data = inline.get("data")
        if data:
            mime = inline.get("mimeType") or "image/png"
            return f"data:{mime};base64,{data}"
    return None


def _fallback_svg(day_index: int) -> str:
    if day_index <= 7:
        colors = ("#fce7f3", "#f9a8d4", "#ec4899", "#f472b6")
    elif day_index <= 14:
        colors = ("#fed7aa", "#fb923c", "#ea580c", "#fdba74")
    elif day_index <= 21:
        colors = ("#a5f3fc", "#22d3ee", "#0891b2", "#67e8f9")
    else:
        colors = ("#fef3c7", "#fcd34d", "#d97706", "#fbbf24")
    primary, secondary, accent, highlight = colors
    svg = f"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:{primary};stop-opacity:1" />
      <stop offset="100%" style="stop-color:{secondary};stop-opacity:1" />
    </linearGradient>
    <radialGradient id="glow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" style="stop-color:{accent};stop-opacity:0.8" />
      <stop offset="100%" style="stop-color:{accent};stop-opacity:0" />
    </radialGradient>
  </defs>
  <rect width="400" height="400" fill="url(#bg)"/>
  <circle cx="200" cy="200" r="120" fill="url(#glow)" opacity="0.6"/>
  <circle cx="140" cy="140" r="60" fill="{accent}" opacity="0.25"/>
  <circle cx="280" cy="250" r="80" fill="{highlight}" opacity="0.25"/>
  <text x="200" y="210" font-family="Arial, sans-serif" font-size="72" font-weight="bold"
        fill="white" text-anchor="middle" opacity="0.9">{day_index}</text>
  <text x="200" y="260" font-family="Arial, sans-serif" font-size="14"
        fill="white" text-anchor="middle" opacity="0.7">DAY OF 28</text>
</svg>
""".strip()
    b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"


def generate_nft_image(
    day_index: int,
    task_title: str,
    user_text: str,
    reflection_note: str,
    reflection_next: str,
    gemini_api_key: str = "",
) -> str:
    prompt = _build_prompt(day_index, task_title, user_text, reflection_note)
    try:
        image = _pollinations_image(prompt)
        if image:
            return image
    except Exception:
        pass
    try:
        image = _gemini_image(prompt, gemini_api_key)
        if image:
            return image
    except Exception:
        pass
    return _fallback_svg(day_index)
