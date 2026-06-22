# FitFindr

FitFindr is a multi-tool AI agent that helps users find secondhand clothing, style the selected item with their wardrobe, and generate a shareable outfit caption.

The agent uses three required tools:
1. `search_listings`
2. `suggest_outfit`
3. `create_fit_card`

It also uses a planning loop and session state so information from one tool flows into the next tool.

---

## Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
````

Create a `.env` file in the project root:

```bash
GROQ_API_KEY=your_key_here
```

Run the app:

```bash
python app.py
```

Run tests:

```bash
PYTHONPATH=. pytest tests/
```

---

## Tool Inventory

### Tool 1: `search_listings(description, size=None, max_price=None)`

**Purpose:**
Searches the mock secondhand listings dataset for items matching the user's request.

**Inputs:**

* `description` (str): keywords describing what the user wants, such as `"vintage graphic tee"`
* `size` (str | None): optional size filter, such as `"M"` or `"XXS"`
* `max_price` (float | None): optional maximum price filter

**Output:**
Returns a list of matching listing dictionaries. Each listing can include:

* `id`
* `title`
* `description`
* `category`
* `style_tags`
* `size`
* `condition`
* `price`
* `colors`
* `brand`
* `platform`

If no listings match, it returns an empty list `[]`.

---

### Tool 2: `suggest_outfit(new_item, wardrobe)`

**Purpose:**
Suggests an outfit using the selected secondhand item and the user's wardrobe.

**Inputs:**

* `new_item` (dict): the selected listing from `search_listings`
* `wardrobe` (dict): the user's wardrobe dictionary

**Output:**
Returns a non-empty outfit suggestion string.

If the wardrobe is empty, the tool still returns general styling advice instead of crashing.

---

### Tool 3: `create_fit_card(outfit, new_item)`

**Purpose:**
Creates a short Instagram/TikTok-style outfit caption using the selected item and outfit suggestion.

**Inputs:**

* `outfit` (str): outfit suggestion returned by `suggest_outfit`
* `new_item` (dict): the selected listing

**Output:**
Returns a short shareable fit card caption string.

If the outfit input is empty, it returns a descriptive error message.

---

## Planning Loop

The agent does not call every tool blindly. It uses conditional logic.

1. The user enters a natural language query.
2. The agent parses the query into:

   * description
   * size
   * max price
3. The agent calls `search_listings(description, size, max_price)`.
4. If no listings are found, the agent stores an error message and stops early.
5. If listings are found, the agent stores the first result as `selected_item`.
6. The agent calls `suggest_outfit(selected_item, wardrobe)`.
7. The outfit suggestion is stored in the session.
8. The agent calls `create_fit_card(outfit_suggestion, selected_item)`.
9. The fit card is stored in the session.
10. The app displays the listing, outfit suggestion, and fit card.

The important branch is the no-results path. If `search_listings` returns `[]`, the agent does not call `suggest_outfit` or `create_fit_card`.

---

## State Management

The agent stores data in a session dictionary during each interaction.

The session includes:

* `query`: original user query
* `parsed`: extracted description, size, and max price
* `search_results`: list returned by `search_listings`
* `selected_item`: first listing result selected by the agent
* `wardrobe`: wardrobe passed into the agent
* `outfit_suggestion`: result from `suggest_outfit`
* `fit_card`: result from `create_fit_card`
* `error`: error message if the agent stops early

This allows the output of one tool to become the input of the next tool. For example, the selected item from `search_listings` is stored in `session["selected_item"]` and then passed into `suggest_outfit`.

---

## Interaction Walkthrough

**User query:**

```text
vintage graphic tee under $30
```

### Step 1 — Tool called

**Tool:**
`search_listings`

**Input:**

```python
search_listings("vintage graphic tee", size=None, max_price=30.0)
```

**Why this tool:**
The agent needs to find a secondhand item before it can suggest an outfit.

**Output:**
The tool returns matching listings. In my test, the top result was:

```text
Y2K Baby Tee — Butterfly Print
Price: $18
Platform: depop
Size: S/M
Condition: excellent
```

---

### Step 2 — Tool called

**Tool:**
`suggest_outfit`

**Input:**

```python
suggest_outfit(selected_item, wardrobe)
```

**Why this tool:**
After the agent finds a listing, it needs to help the user style it with their wardrobe.

**Output:**
The tool returns an outfit suggestion. Example:

```text
Pair the Y2K Baby Tee with baggy straight-leg jeans and chunky white sneakers. The fitted crop top balances the high-waisted baggy jeans, while the sneakers add a streetwear touch that matches the Y2K vibe.
```

---

### Step 3 — Tool called

**Tool:**
`create_fit_card`

**Input:**

```python
create_fit_card(outfit_suggestion, selected_item)
```

**Why this tool:**
The final step is to turn the outfit into a shareable caption.

**Output:**
The tool returns a fit card caption. Example:

```text
Just scored the cutest Y2K Baby Tee for $18 on Depop and I'm obsessed! The butterfly graphic is giving nostalgic Y2K vibes. Pairing it with baggy jeans and chunky sneakers for an easy thrifted streetwear look.
```

---

## Final Output to User

The user sees three panels in the Gradio app:

1. **Top listing found**
   Shows the title, price, platform, size, condition, brand, and description.

2. **Outfit idea**
   Shows the generated outfit suggestion.

3. **Your fit card**
   Shows the generated caption.

---

## Error Handling and Fail Points

| Tool              | Failure mode                          | Agent response                                                                     |
| ----------------- | ------------------------------------- | ---------------------------------------------------------------------------------- |
| `search_listings` | No results match the query            | Returns `[]`. The agent sets an error message and stops early.                     |
| `suggest_outfit`  | Wardrobe is empty                     | Returns general styling advice using common wardrobe staples instead of crashing.  |
| `create_fit_card` | Outfit input is missing or incomplete | Returns `"Could not create a fit card because no outfit suggestion was provided."` |

Example no-results query:

```text
designer ballgown size XXS under $5
```

Agent response:

```text
No listings found. Try using a broader description, removing the size filter, or increasing your max price.
```

The outfit and fit card panels stay empty because the agent stops early.

---

## Tests

I added tests in `tests/test_tools.py`.

The tests cover:

* successful listing search
* empty search results
* price filtering
* empty wardrobe behavior
* empty outfit behavior

I ran:

```bash
PYTHONPATH=. pytest tests/
```

Result:

```text
5 passed
```

---

## Spec Reflection

**One way planning.md helped during implementation:**

The planning document helped me define each tool before writing code. It made it clear what each function should accept, what it should return, and how it should handle failure cases. This made implementation easier because I could build and test one tool at a time instead of trying to code the whole agent at once.

**One divergence from your spec, and why:**

The planning loop stayed simpler than a fully flexible AI agent. Instead of asking the LLM to decide every next step, I used a clear conditional loop in Python. This made the project easier to test and ensured that the no-results branch stopped early instead of calling later tools with missing data.

---

## AI Usage

I used ChatGPT to help implement the three required tools after writing the tool specifications. I gave ChatGPT the function signatures, expected inputs and outputs, and failure modes from my planning document. I reviewed the generated code to make sure it matched the starter stubs and tested each tool individually before connecting them.

I also used ChatGPT to help implement the planning loop in `agent.py`. I provided the planning loop steps and architecture diagram from `planning.md`. I verified the result by running both a happy path query and a no-results query.

---

## Demo Notes

The demo video shows:

1. A complete successful interaction using all three tools.
2. State passing from search result to outfit suggestion to fit card.
3. A no-results failure case where the agent stops early and shows a helpful error.

````

Then run:

```bash
git add README.md
git commit -m "Complete README"
git push
````
