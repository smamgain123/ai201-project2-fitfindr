"""
agent.py

The FitFindr planning loop. Orchestrates the three tools in response to a
natural language user query, passing state between them via a session dict.

Complete tools.py and test each tool in isolation before implementing this file.

Usage (once implemented):
    from agent import run_agent
    from utils.data_loader import get_example_wardrobe
a
    result = run_agent(
        query="vintage graphic tee under $30, size M",
        wardrobe=get_example_wardrobe(),
    )
    print(result["fit_card"])
    print(result["error"])   # None on success
"""

from tools import search_listings, suggest_outfit, create_fit_card


# ── session state ─────────────────────────────────────────────────────────────

def _new_session(query: str, wardrobe: dict) -> dict:
    """
    Initialize and return a fresh session dict for one user interaction.

    The session dict is the single source of truth for everything that happens
    during a run — it stores the original query, parsed parameters, tool results,
    and any error that caused early termination.

    You may add fields to this dict as needed for your implementation.
    """
    return {
        "query": query,              # original user query
        "parsed": {},                # extracted description / size / max_price
        "search_results": [],        # list of matching listing dicts
        "selected_item": None,       # top result, passed into suggest_outfit
        "wardrobe": wardrobe,        # user's wardrobe dict
        "outfit_suggestion": None,   # string returned by suggest_outfit
        "fit_card": None,            # string returned by create_fit_card
        "error": None,               # set if the interaction ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def _parse_query(query: str) -> dict:
    """
    Simple parser for description, size, and max_price.
    Example: "vintage graphic tee under $30 size M"
    """
    import re

    parsed = {
        "description": query,
        "size": None,
        "max_price": None,
    }

    # Find price like $30 or under 30
    price_match = re.search(r"\$?(\d+(?:\.\d+)?)", query)
    if price_match:
        parsed["max_price"] = float(price_match.group(1))

    # Find size like size M
    size_match = re.search(r"size\s+([A-Za-z0-9/]+)", query, re.IGNORECASE)
    if size_match:
        parsed["size"] = size_match.group(1)

    # Clean description by removing price and size phrases
    description = query
    description = re.sub(r"under\s+\$?\d+(?:\.\d+)?", "", description, flags=re.IGNORECASE)
    description = re.sub(r"\$?\d+(?:\.\d+)?", "", description)
    description = re.sub(r"size\s+[A-Za-z0-9/]+", "", description, flags=re.IGNORECASE)
    description = description.replace("looking for", "")
    description = description.replace("I'm", "")
    description = description.replace("i'm", "")
    description = description.strip(" ,.")

    parsed["description"] = description

    return parsed


def run_agent(query: str, wardrobe: dict) -> dict:
    session = _new_session(query, wardrobe)

    # Step 1: Parse query
    parsed = _parse_query(query)
    session["parsed"] = parsed

    description = parsed["description"]
    size = parsed["size"]
    max_price = parsed["max_price"]

    # Step 2: Search listings
    results = search_listings(description, size=size, max_price=max_price)
    session["search_results"] = results

    # Step 3: Error path if no listings found
    if not results:
        session["error"] = (
            "No listings found. Try using a broader description, removing the size filter, "
            "or increasing your max price."
        )
        return session

    # Step 4: Save selected item in session state
    session["selected_item"] = results[0]

    # Step 5: Suggest outfit using selected item and wardrobe
    outfit = suggest_outfit(session["selected_item"], wardrobe)
    session["outfit_suggestion"] = outfit

    # Step 6: Create fit card using outfit and selected item
    fit_card = create_fit_card(outfit, session["selected_item"])
    session["fit_card"] = fit_card

    # Step 7: Return final session
    return session

# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")
