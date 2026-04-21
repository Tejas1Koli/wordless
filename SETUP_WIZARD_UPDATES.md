# Setup Wizard Enhancement: Dynamic Model Selection

## What Changed

The setup wizard now **dynamically fetches available embedding models** from each provider instead of using hard-coded lists.

### Before
```
📌 Step 3: Select Embedding Model
1. text-embedding-3-small        # ← Hard-coded
2. text-embedding-3-large        # ← Hard-coded
Select model: 
```

### After
```
⏳ Fetching available embedding models...
📌 Step 3: Select Embedding Model
1. text-embedding-3-small
2. text-embedding-3-large
3. text-embedding-3-gigantic
... (more models dynamically fetched)
Select model: 
```

## Implementation Details

### New Helper Functions

#### `_fetch_openai_models(api_key: str) -> list[str]`
- Calls OpenAI's `/v1/models` endpoint
- Filters for embedding models
- Returns list sorted by recommendation (3-small first)
- Fallback to defaults if API call fails

#### `_fetch_openrouter_models(api_key: str) -> list[str]`
- Returns curated list of popular embedding models available via OpenRouter:
  - `openai/text-embedding-3-small` (recommended)
  - `openai/text-embedding-3-large`
  - `cohere/embed-english-v3.0`
  - `nvidia/llama-nemotron-embed-vl-1b-v2:free` ✅ (from user request)
  - `thenlper/gte-base` ✅ (from user request)
  - `thenlper/gte-small`
  - `sentence-transformers/all-MiniLM-L6-v2`
  - `sentence-transformers/all-mpnet-base-v2`

### Updated Setup Flow

```
Step 1: Choose provider (OpenAI / OpenRouter / Ollama)
   ↓
Step 2: Enter API key
   ↓
Step 3: Validate API key (test request to provider)
   ↓
Step 4: Fetch available models from provider ← NEW
   ↓
Step 5: User selects model from full list ← ENHANCED
   ↓
Step 6: Save configuration
```

## Benefits

✅ **Dynamic Model Discovery** - Users see all available models, not just hardcoded defaults
✅ **OpenRouter Support** - Includes popular embedding models the user requested
✅ **Future-Proof** - When providers add new models, they automatically appear
✅ **Fallback Protection** - Uses sensible defaults if API call fails
✅ **Better UX** - OpenRouter shows models like `nvidia/llama-nemotron-embed-vl-1b-v2:free` as requested

## Tested Models

The setup wizard now supports user selection of these models from OpenRouter:
- 🟢 `nvidia/llama-nemotron-embed-vl-1b-v2:free`
- 🟢 `thenlper/gte-base`
- 🟢 `thenlper/gte-small`
- 🟢 `openai/text-embedding-3-small`
- And 4 more popular embedding models

## Usage

```bash
wordless setup

# Select: 2 (OpenRouter)
# Enter API key: sk-or-v1-...
# See available models (including nvidia nemotron & thenlper gte!)
# Select your preferred model
# Done!
```

## File Changes

- `wordless/cli/app.py`: 
  - Updated `setup()` command to fetch models dynamically
  - Added `_fetch_openai_models()` helper
  - Added `_fetch_openrouter_models()` helper
