"""
tools.py
"""

import os
import re

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings 

load_dotenv()


def _get_groq_client():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set. Add it to a .env file.")
    return Groq(api_key=api_key)


def _call_groq(prompt: str, temperature: float = 0.7) -> str:
    client = _get_groq_client()

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )

    return response.choices[0].message.content.strip()


def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    listings = load_listings()
    results = []

    keywords = re.findall(r"\w+", description.lower())

    for item in listings:
        if max_price is not None and float(item.get("price", 0)) > float(max_price):
            continue

        if size:
            item_size = str(item.get("size", "")).lower()
            user_size = size.lower()
            if user_size not in item_size:
                continue

        searchable_text = " ".join(
            [
                str(item.get("title", "")),
                str(item.get("description", "")),
                str(item.get("category", "")),
                " ".join(item.get("style_tags", [])),
                str(item.get("brand", "")),
                " ".join(item.get("colors", [])),
            ]
        ).lower()

        score = 0
        for word in keywords:
            if word in searchable_text:
                score += 1

        if score > 0:
            results.append((score, item))

    results.sort(key=lambda pair: pair[0], reverse=True)

    return [item for score, item in results]


def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    if not new_item:
        return "I need a selected item before I can suggest an outfit."

    wardrobe_items = wardrobe.get("items", []) if wardrobe else []

    if not wardrobe_items:
        prompt = f"""
You are FitFindr, a helpful fashion styling assistant.

The user is considering this secondhand item:
{new_item}

The user's wardrobe is empty or unavailable.

Suggest one complete outfit using general wardrobe staples someone may own.
Keep it practical, stylish, and easy to understand.
"""
    else:
        prompt = f"""
You are FitFindr, a helpful fashion styling assistant.

The user is considering this secondhand item:
{new_item}

The user's wardrobe:
{wardrobe_items}

Suggest 1 complete outfit using the new item and pieces from the wardrobe.
Mention why the pieces work together.
Keep it concise and stylish.
"""

    return _call_groq(prompt, temperature=0.7)


def create_fit_card(outfit: str, new_item: dict) -> str:
    if not outfit or not outfit.strip():
        return "Could not create a fit card because no outfit suggestion was provided."

    prompt = f"""
You are FitFindr.

Create a short, casual, Instagram-style outfit caption.

New thrifted item:
{new_item}

Outfit suggestion:
{outfit}

Rules:
- 2 to 4 sentences
- Mention the item name, price, and platform naturally
- Sound like a real person, not a product description
- Make it cute and shareable
"""

    return _call_groq(prompt, temperature=0.9)