# FitFindr — planning.md

## Tools

### Tool 1: search_listings

**What it does:**
Searches the mock secondhand listings dataset for items that match the user's description, optional size, and optional max price. It returns matching listings sorted by relevance.

**Input parameters:**
- `description` (str): Keywords describing what the user wants, such as "vintage graphic tee".
- `size` (str | None): Optional size filter, such as "M" or "XXS". If None, the tool does not filter by size.
- `max_price` (float | None): Optional maximum price. If None, the tool does not filter by price.

**What it returns:**
A list of listing dictionaries. Each dictionary may include fields such as `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

**What happens if it fails or returns nothing:**
It returns an empty list instead of crashing. The agent then stops early and tells the user to broaden the description, remove the size filter, or increase the max price.

---

### Tool 2: suggest_outfit

**What it does:**
Takes the selected secondhand item and the user's wardrobe, then generates a complete outfit suggestion. It uses the LLM to explain how to style the item.

**Input parameters:**
- `new_item` (dict): The selected listing dictionary from `search_listings`.
- `wardrobe` (dict): The user's wardrobe dictionary, including an `items` list.

**What it returns:**
A non-empty outfit suggestion string. The suggestion explains what to pair with the new item and why the pieces work together.

**What happens if it fails or returns nothing:**
If the wardrobe is empty, the tool still returns general styling advice using common wardrobe staples. If `new_item` is missing, it returns a helpful message instead of crashing.

---

### Tool 3: create_fit_card

**What it does:**
Creates a short, shareable Instagram/TikTok-style outfit caption using the selected item and outfit suggestion.

**Input parameters:**
- `outfit` (str): The outfit suggestion returned by `suggest_outfit`.
- `new_item` (dict): The selected listing dictionary.

**What it returns:**
A 2–4 sentence caption string that mentions the item, price, platform, and outfit vibe.

**What happens if it fails or returns nothing:**
If the outfit string is empty or missing, the tool returns a descriptive error message instead of raising an exception.

---

### Additional Tools

No additional tools were implemented. I focused on the three required tools.

---

## Planning Loop

The agent starts with a natural language user query. It parses the query to extract a description, optional size, and optional max price.

The first tool called is `search_listings(description, size, max_price)`. If search returns an empty list, the agent saves an error message in `session["error"]` and returns early. In this case, it does not call `suggest_outfit` or `create_fit_card`.

If search returns results, the agent selects the first result as the top listing and stores it as `session["selected_item"]`. Then it calls `suggest_outfit(selected_item, wardrobe)` and stores the returned outfit string in `session["outfit_suggestion"]`.

Finally, the agent calls `create_fit_card(outfit_suggestion, selected_item)` and stores the caption in `session["fit_card"]`. The loop is done when the session has either an error or all three successful outputs.

---

## State Management

The agent stores information in a session dictionary for one full interaction.

The session tracks:
- `query`: the original user query
- `parsed`: extracted description, size, and max price
- `search_results`: listings returned by `search_listings`
- `selected_item`: the first matching listing
- `wardrobe`: the user's wardrobe
- `outfit_suggestion`: the result from `suggest_outfit`
- `fit_card`: the result from `create_fit_card`
- `error`: an error message if the agent stops early

State lets one tool's output become the next tool's input. For example, `selected_item` comes from `search_listings` and is then passed into `suggest_outfit`. The outfit suggestion is then passed into `create_fit_card`.

---

## Error Handling

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | Return an empty list. The agent sets `session["error"]` to: "No listings found. Try using a broader description, removing the size filter, or increasing your max price." Then it stops early. |
| suggest_outfit | Wardrobe is empty | Return general styling advice using common staples instead of crashing. |
| create_fit_card | Outfit input is missing or incomplete | Return: "Could not create a fit card because no outfit suggestion was provided." |

---

## Architecture

```text
User Query
   |
   v
Planning Loop
   |
   v
Parse query into:
description, size, max_price
   |
   v
search_listings(description, size, max_price)
   |
   |-- if results == [] ----------------------------|
   |                                                |
   v                                                v
session["search_results"]                     session["error"]
   |                                                |
   v                                                v
session["selected_item"] = results[0]          Return session early
   |
   v
suggest_outfit(selected_item, wardrobe)
   |
   v
session["outfit_suggestion"]
   |
   v
create_fit_card(outfit_suggestion, selected_item)
   |
   v
session["fit_card"]
   |
   v
Return completed session


AI Tool Plan

Milestone 3 — Individual tool implementations:

I used ChatGPT to help implement each required tool one at a time. For each tool, I provided the tool name, required function signature, inputs, outputs, and failure mode from this planning document. I expected the AI tool to produce Python code that matched the existing starter function stubs in tools.py.

For search_listings, I verified that the code used load_listings(), filtered by price and size, scored keyword matches, and returned an empty list when no listings matched. I tested it with a normal query and an impossible query.

For suggest_outfit, I verified that it handled an empty wardrobe and returned a useful string. I tested it with get_example_wardrobe() and get_empty_wardrobe().

For create_fit_card, I verified that it guarded against an empty outfit string and used a higher LLM temperature so captions could vary.

Milestone 4 — Planning loop and state management:

I used ChatGPT to help implement the planning loop in agent.py. I gave it my planning loop steps and architecture diagram. I expected it to create logic that parses the query, calls search_listings, branches on empty results, stores state in the session dictionary, then calls the remaining tools only when valid data exists.

I verified the output by running python agent.py. The happy path returned a listing, outfit suggestion, and fit card. The no-results path returned an error message and did not create an outfit or fit card.

A Complete Interaction (Step by Step)

Example user query:
"I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

Step 1:
The agent receives the query and parses it. It extracts:

description: "vintage graphic tee"
size: None
max_price: 30.0

Step 2:
The agent calls:

search_listings("vintage graphic tee", size=None, max_price=30.0)

The tool searches the listings dataset and returns matching items. In my test, it found the "Y2K Baby Tee — Butterfly Print" listing.

Step 3:
The agent stores the first result in:

session["selected_item"]

This selected item is then passed into the next tool.

Step 4:
The agent calls:

suggest_outfit(selected_item, wardrobe)

The tool returns an outfit suggestion using the selected tee with items from the example wardrobe, such as baggy jeans and chunky sneakers.

Step 5:
The agent stores the outfit suggestion in:

session["outfit_suggestion"]

Then it calls:

create_fit_card(outfit_suggestion, selected_item)

Step 6:
The fit card tool returns a short caption-style description for the outfit. The agent stores this in:

session["fit_card"]

Final output to user:
The user sees three panels:

The top listing found, including title, price, platform, size, condition, brand, and description.
An outfit suggestion explaining how to style the item.
A social-media-style fit card caption.

If no listing is found, the user sees an error message in the first panel and the outfit and fit card panels stay empty.