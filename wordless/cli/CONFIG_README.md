# Wordless Config Command Guide

The `wordless config` command manages application settings stored in `~/.wordless/config.json`.

## Overview

```bash
wordless config <action> [key] [value]
```

**Supported Actions:**
- `set` — Save a configuration value
- `get` — Retrieve a specific value
- `list` — Display all settings
- `reset` — Restore one key to default
- `reset-all` — Restore all settings to defaults

---

## Configuration Keys

### API & Embedding

| Key | Type | Default | Purpose |
|-----|------|---------|---------|
| `api_key` | string | `` | OpenAI or OpenRouter API key |
| `embedding_provider` | string | `openai` | Embedding service: `openai` or `openrouter` |
| `gateway_url` | string | `http://localhost:6768` | Legacy gateway URL (deprecated) |

### Search

| Key | Type | Default | Purpose |
|-----|------|---------|---------|
| `top_k` | int | `5` | Number of search results to return |
| `default_hops` | int | `3` | Call graph traversal depth |

### Server

| Key | Type | Default | Purpose |
|-----|------|---------|---------|
| `mcp_host` | string | `localhost` | MCP server hostname |
| `mcp_port` | int | `6767` | MCP server port |

### Repositories

| Key | Type | Default | Purpose |
|-----|------|---------|---------|
| `indexed_repos` | list | `[]` | Auto-populated list of indexed repos |

---

## Command Examples

### Setting Values

**Set OpenAI API key:**
```bash
wordless config set api_key sk-proj-YOUR_OPENAI_KEY
```

**Switch to OpenRouter:**
```bash
wordless config set embedding_provider openrouter
wordless config set api_key YOUR_OPENROUTER_KEY
```

**Increase search results:**
```bash
wordless config set top_k 10
```

**Change MCP server port:**
```bash
wordless config set mcp_port 8000
```

**Reduce call graph depth:**
```bash
wordless config set default_hops 2
```

---

### Getting Values

**Check current embedding provider:**
```bash
$ wordless config get embedding_provider
embedding_provider = openai
```

**View API key (if set):**
```bash
$ wordless config get api_key
api_key = sk-proj-...
```

**Check search result limit:**
```bash
$ wordless config get top_k
top_k = 5
```

---

### Listing All Settings

**Display all configuration:**
```bash
$ wordless config list
📋 Wordless Configuration:
────────────────────────────────────────────────────────
✓ api_key                = sk-proj-YOUR_KEY
✓ default_hops           = 3
✎ embedding_provider     = openrouter
✓ gateway_url            = http://localhost:6768
✓ indexed_repos          = [{"name": "wordless", "path": "/Users/you/wordless"}]
✓ mcp_host               = localhost
✓ mcp_port               = 6767
✓ top_k                  = 5
────────────────────────────────────────────────────────
```

**Legend:**
- `✓` = Default value
- `✎` = Custom value (changed from default)

---

### Resetting Values

**Reset API key to default (empty):**
```bash
wordless config reset api_key
✅ Reset api_key to 
```

**Reset search limit back to 5:**
```bash
wordless config reset top_k
✅ Reset top_k to 5
```

**Reset embedding provider to OpenAI:**
```bash
wordless config reset embedding_provider
✅ Reset embedding_provider to openai
```

---

### Reset All Settings

**Restore everything to defaults:**
```bash
$ wordless config reset-all
Reset ALL configuration to defaults? [y/N]: y
✅ All configuration reset to defaults
```

⚠️ **Warning:** This action requires confirmation and cannot be undone easily.

---

## Configuration File Location

All settings are saved in:
```
~/.wordless/config.json
```

### View Raw Config

```bash
cat ~/.wordless/config.json
```

### Manual Editing

You can edit directly, but using CLI commands is recommended:
```json
{
  "api_key": "sk-proj-YOUR_KEY",
  "embedding_provider": "openai",
  "top_k": 5,
  "default_hops": 3,
  "mcp_host": "localhost",
  "mcp_port": 6767,
  "indexed_repos": [
    {"name": "wordless", "path": "/Users/you/wordless"}
  ]
}
```

---

## Type Conversions

The config command automatically converts types for numeric keys:

| Key | Conversion |
|-----|------------|
| `top_k` | string → integer |
| `default_hops` | string → integer |
| `mcp_port` | string → integer |

**Example:**
```bash
wordless config set top_k 10    # Automatically stored as integer 10
wordless config set mcp_port 7000  # Automatically stored as integer 7000
```

---

## Common Workflows

### Setup OpenAI Embeddings

```bash
# 1. Get API key from https://platform.openai.com/account/api-keys
# 2. Save it
wordless config set api_key sk-proj-YOUR_KEY

# 3. Verify
wordless config get api_key
```

### Switch to OpenRouter

```bash
# 1. Get API key from https://openrouter.ai/keys
wordless config set api_key YOUR_OPENROUTER_KEY

# 2. Switch provider
wordless config set embedding_provider openrouter

# 3. Verify
wordless config list
```

### Use Local Ollama (Free)

```bash
# Remove API key to fall back to Ollama
wordless config reset api_key
wordless config reset embedding_provider

# Now searches use local Ollama automatically
wordless debug "find parser functions"
```

### Tune Search Results

```bash
# Get more results
wordless config set top_k 15

# Deeper call graph analysis
wordless config set default_hops 5

# Verify changes
wordless config list
```

---

## Error Handling

### Unknown Key
```bash
$ wordless config get nonexistent_key
❌ Unknown config key: nonexistent_key
```

### Missing Required Arguments
```bash
$ wordless config set api_key
❌ Usage: wordless config set <key> <value>
```

### Invalid Action
```bash
$ wordless config modify api_key
❌ Unknown action: modify
Valid actions: set, get, list, reset, reset-all
```

---

## Security Notes

⚠️ **Plain Text Storage**

API keys are stored in plain text in `~/.wordless/config.json`. For better security:

1. **Restrict file permissions:**
   ```bash
   chmod 600 ~/.wordless/config.json
   ```

2. **Don't commit to version control:**
   ```bash
   # Add to .gitignore
   ~/.wordless/config.json
   ```

3. **Use restricted API keys:**
   - OpenAI: Create keys with minimal scope
   - OpenRouter: Use per-project keys

---

## Implementation Details

**File:** `wordless/cli/app.py` (`config` command function)  
**Config Manager:** `wordless/config_manager.py`  
**Defaults:** `wordless/config_manager.py` (DEFAULTS dict)  
**Runtime Config:** `wordless/config.py` (loads via config_manager)

### How It Works

1. User runs `wordless config set key value`
2. CLI validates the key exists in DEFAULTS
3. Type conversion applied for numeric keys
4. Value written to `~/.wordless/config.json`
5. Subsequent runs load from JSON file

---

## Related Commands

- `wordless config get <key>` — Check a setting
- `wordless config list` — View all settings before/after changes
- `wordless doctor` — System diagnostics (includes config validation)
- `wordless repos` — List indexed repositories (uses config)
- `wordless serve` — Start MCP server (uses `mcp_host`, `mcp_port`)
- `wordless debug` — Test search (uses `api_key`, `embedding_provider`)
