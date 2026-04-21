# Wordless Setup Command Guide

The `wordless setup` command is an interactive wizard that guides you through configuring your embedding provider in just a few steps.

## Overview

```bash
wordless setup
```

This command will:
1. Present embedding provider options (OpenAI, OpenRouter, Ollama)
2. Ask for your API key (if needed)
3. Validate the API key automatically
4. Let you choose your preferred embedding model
5. Save all settings automatically

---

## Interactive Setup Wizard

### Step 1: Choose Provider

```
🔧 Wordless Setup Wizard
────────────────────────────────────────────────────────

📌 Step 1: Choose Embedding Provider
1. OpenAI (Recommended - Best quality)
2. OpenRouter (Alternative - Multi-provider)
3. Local Ollama (Free - No API key needed)
Select option:
```

**Options:**

| Option | Provider | Best For | Cost |
|--------|----------|----------|------|
| 1 | OpenAI | Production, best quality | Paid |
| 2 | OpenRouter | Multi-provider access | Paid |
| 3 | Ollama | Local development | Free |

### Step 2: Enter API Key

```
📌 Step 2: API Key
Get your free API key at: https://platform.openai.com/account/api-keys
Enter your API key:
```

**The wizard will:**
- ✅ Validate your API key by making a test request
- 🔴 Show errors if the key is invalid
- 🟡 Warn about rate limiting
- ✅ Save it securely in `~/.wordless/config.json`

### Step 3: Select Model

```
📌 Step 3: Select Embedding Model
1. text-embedding-3-small
2. text-embedding-3-large
Select model:
```

**OpenAI Models:**
- `text-embedding-3-small` (default) — 1536 dimensions, fast, cheap
- `text-embedding-3-large` — 3072 dimensions, more accurate

**OpenRouter Models:**
- `openai/text-embedding-3-small` (default)
- `openai/text-embedding-3-large`
- Other models available through OpenRouter

### Step 4: Confirmation

```
════════════════════════════════════════════════════════
✨ Setup Complete!
════════════════════════════════════════════════════════
Provider: openai
API Key: sk-proj-***
Model: text-embedding-3-small

💡 You can now use Wordless to search your code!
   Try: wordless debug 'find parser functions'
════════════════════════════════════════════════════════
```

---

## Setup Examples

### Example 1: OpenAI Setup

```bash
$ wordless setup

🔧 Wordless Setup Wizard
────────────────────────────────────────────────────────
📌 Step 1: Choose Embedding Provider
1. OpenAI (Recommended - Best quality)
2. OpenRouter (Alternative - Multi-provider)
3. Local Ollama (Free - No API key needed)
Select option: 1

📌 Step 2: API Key
Get your free API key at: https://platform.openai.com/account/api-keys
Enter your API key: sk-proj-abc123...

⏳ Validating API key...
✅ API key validated!

📌 Step 3: Select Embedding Model
1. text-embedding-3-small
2. text-embedding-3-large
Select model: 1

⏳ Saving configuration...
✅ Configuration saved!

════════════════════════════════════════════════════════
✨ Setup Complete!
════════════════════════════════════════════════════════
Provider: openai
API Key: sk-proj-***
Model: text-embedding-3-small

💡 You can now use Wordless to search your code!
   Try: wordless debug 'find parser functions'
════════════════════════════════════════════════════════
```

### Example 2: OpenRouter Setup

```bash
$ wordless setup

📌 Step 1: Choose Embedding Provider
Select option: 2

📌 Step 2: API Key
Get your free API key at: https://openrouter.ai/keys
Enter your API key: your-openrouter-key...

⏳ Validating API key...
✅ API key validated!

📌 Step 3: Select Embedding Model
1. openai/text-embedding-3-small
2. openai/text-embedding-3-large
Select model: 1

✨ Setup Complete!
Provider: openrouter
API Key: your-***
Model: openai/text-embedding-3-small
```

### Example 3: Local Ollama (Free)

```bash
$ wordless setup

📌 Step 1: Choose Embedding Provider
Select option: 3

✅ Ollama configured!
   Make sure to install: ollama pull qwen3-embedding:0.6b

✨ Setup Complete!
```

---

## Error Handling

### Invalid API Key

```
⏳ Validating API key...
❌ API key validation failed. Please check your key and try again.
   Get a new key at: https://platform.openai.com/account/api-keys
```

**Solutions:**
1. Get a new API key from the provider's website
2. Check that you copied the key correctly
3. Make sure your account has credit/quota
4. Try `wordless setup` again

### Empty API Key

```
❌ API key cannot be empty. Setup cancelled.
```

**Solution:** You must provide a valid API key (unless using Ollama)

### Network Error

```
   🔴 Network error: [connection error details]
```

**Solutions:**
1. Check your internet connection
2. Verify the API endpoint is reachable
3. Try `wordless setup` again

### Rate Limited

```
   🟡 Rate limited - but key seems valid
```

**Meaning:** Your key works but you've hit rate limits. This is normal and the setup continues.

### Invalid Model Selection

```
❌ Invalid model selection. Setup cancelled.
```

**Solution:** Enter a number from the available options (1 or 2)

---

## After Setup

### Verify Your Configuration

```bash
# Check settings
wordless config list

# View your provider
wordless config get embedding_provider

# View your API key (masked)
wordless config get api_key
```

### Test Your Setup

```bash
# Try semantic search
wordless debug "find parser functions"

# Search in specific directory
wordless debug "async handlers" --repo-path ~/myproject

# Start the REPL
wordless repl
```

### Start the Server

```bash
# For AI agent integration
wordless serve
```

---

## Manual Configuration

If you prefer not to use the setup wizard, you can configure manually:

```bash
# Set provider
wordless config set embedding_provider openai

# Set API key
wordless config set api_key sk-proj-YOUR_KEY

# View all settings
wordless config list
```

See [CONFIG_README.md](CONFIG_README.md) for manual configuration details.

---

## Advanced: Changing Providers

If you need to switch providers after setup:

```bash
# Run setup again
wordless setup

# Or manually switch
wordless config set embedding_provider openrouter
wordless config set api_key YOUR_OPENROUTER_KEY
```

---

## File Locations

**Configuration saved to:**
```
~/.wordless/config.json
```

**View your full configuration:**
```bash
cat ~/.wordless/config.json
```

**Example config after setup:**
```json
{
  "api_key": "sk-proj-abc123...",
  "embedding_provider": "openai",
  "top_k": 5,
  "default_hops": 3,
  "mcp_host": "localhost",
  "mcp_port": 6767,
  "indexed_repos": []
}
```

---

## Security Notes

⚠️ **Plain Text Storage**

AP I keys are stored in plain text in `~/.wordless/config.json`. For better security:

1. **Restrict file permissions:**
   ```bash
   chmod 600 ~/.wordless/config.json
   ```

2. **Don't share your config file** — it contains your API key

3. **Use restricted API keys** — create keys with minimal scope in your provider dashboard

4. **Rotate keys regularly** — consider regenerating keys periodically

---

## Troubleshooting

### Setup says "API key validation failed"

**Check:**
1. Is your API key correct? (copy/paste carefully)
2. Is your account active and does it have credit?
3. Is your internet connection working?
4. Are you using the right API endpoint?

**Solution:**
- Get a fresh API key from your provider's dashboard
- Try `wordless setup` again

### Setup hangs or times out

**Possible causes:**
- Slow internet connection
- API service outage
- Firewall blocking the request

**Solution:**
- Check your internet connection
- Try again in a few moments
- Check the provider's status page

### I forgot my API key

**Solution:**
```bash
# Generate a new key from your provider:
# OpenAI: https://platform.openai.com/account/api-keys
# OpenRouter: https://openrouter.ai/keys

# Then run setup again to update it
wordless setup
```

---

## Comparison with Manual Config

| Method | Interactive | Validation | Saves Time | Recommended |
|--------|-------------|-----------|-----------|-----------|
| `wordless setup` | ✅ Yes | ✅ Yes | ✅ Fast | ✅ Yes |
| `wordless config set` | ❌ No | ❌ No | ❌ Slow | ❌ Advanced |
| Manual JSON edit | ❌ No | ❌ No | ❌ Very slow | ❌ Expert |

**Recommendation:** Use `wordless setup` for first-time setup. It's faster, validates your API key, and prevents misconfiguration.

---

## Implementation Details

**File:** `wordless/cli/app.py` (`setup` command and `_validate_api_key` function)

**What happens:**
1. User chooses provider (interactive prompt)
2. If not Ollama, user enters API key
3. Code validates key by making test embedding request
4. User chooses model
5. All settings saved to `~/.wordless/config.json`
6. Summary displayed with next steps
