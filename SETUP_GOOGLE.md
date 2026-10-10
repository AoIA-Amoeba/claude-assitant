# 🐾 Coding Pet with Google Gemini API

Setup guide for using Google's Gemini API instead of Claude.

## Quick Differences

| Feature | Claude | Google Gemini |
|---------|--------|---------------|
| **API Key** | Anthropic Console | Google AI Studio |
| **Cost** | Pay per use | Free tier available |
| **Speed** | Fast | Very fast |
| **File** | `coding_pet.py` | `coding_pet_google.py` |

## Step 1: Get Google Gemini API Key

### Option A: Free API Key (Recommended)

1. Go to [Google AI Studio](https://ai.google.dev/)
2. Click **"Get API Key"** button
3. Select **"Create API key in new Google Cloud project"**
4. Copy your API key

### Option B: Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Generative AI API
4. Create an API key
5. Copy your API key

## Step 2: Install Dependencies

```bash
pip install -r requirements_google.txt
```

Or install manually:
```bash
pip install PyQt5==5.15.9
pip install google-generativeai==0.3.0
```

For Windows (optional, for window detection):
```bash
pip install pywin32
```

## Step 3: Set Environment Variable

### macOS/Linux:

```bash
export GOOGLE_API_KEY="AIza..."
python coding_pet_google.py
```

Or permanently (add to ~/.bashrc or ~/.zshrc):
```bash
echo 'export GOOGLE_API_KEY="AIza..."' >> ~/.bashrc
source ~/.bashrc
```

### Windows (PowerShell):

```powershell
$env:GOOGLE_API_KEY="AIza..."
python coding_pet_google.py
```

### Windows (Command Prompt):

```cmd
set GOOGLE_API_KEY=AIza...
python coding_pet_google.py
```

### Windows (Permanent - Environment Variables GUI):

1. Press `Win + X`, select "System"
2. Click "Advanced system settings"
3. Click "Environment Variables"
4. Click "New" (under User variables)
5. Variable name: `GOOGLE_API_KEY`
6. Variable value: `AIza...`
7. Click OK and restart your terminal

## Step 4: Run the Pet!

```bash
python coding_pet_google.py
```

## API Limits & Pricing

### Free Tier (Google AI Studio)
- **Requests per minute:** 60
- **Cost:** Free
- **Model:** Gemini 1.5 Flash or Pro

### Paid Tier (Google Cloud)
- **Requests per minute:** Unlimited (with quota)
- **Cost:** ~$0.075 per 1M input tokens, $0.30 per 1M output tokens
- **Model:** Same models available

For coding suggestions, free tier should be plenty!

## Comparing APIs

### Google Gemini (This Version)
✅ Free tier with generous limits
✅ Very fast responses
✅ Great for code analysis
✅ Easy setup with Google AI Studio
⚠️ Slightly less polished than Claude for some tasks

### Claude (Original Version)
✅ Excellent code understanding
✅ Thoughtful suggestions
✅ Longer context window
⚠️ Requires paid account (after free credits)

## Troubleshooting

### "Set GOOGLE_API_KEY environment variable"
1. Verify you copied the full key from Google AI Studio
2. Check that it starts with `AIza`
3. Make sure you set it correctly for your OS
4. Test with: `echo $GOOGLE_API_KEY` (or `echo %GOOGLE_API_KEY%` on Windows)
5. Restart your terminal after setting the variable

### "401 Unauthorized"
- Your API key might be invalid or expired
- Generate a new one at [Google AI Studio](https://ai.google.dev/)
- Some APIs might not be enabled in your Google Cloud project

### "Quota exceeded"
- You hit the rate limit (60 requests/minute on free tier)
- Wait a minute and try again
- Consider upgrading to paid tier for more requests

### Pet suggestions are slow
- First request might be slower (~5 seconds)
- Subsequent requests should be fast (<2 seconds)
- Check internet connection

### Window detection not working
See README.md for platform-specific setup

## Customization

Same as the Claude version! Modify `coding_pet_google.py`:

### Change suggestion frequency:
```python
SUGGESTION_INTERVAL = 120000  # Check every 2 minutes instead
```

### Add more coding keywords:
```python
CODING_KEYWORDS = ["code", "editor", "terminal", "git", "python", 
                   "javascript", "vscode", "pycharm", "sublime", 
                   "rust", "golang", "java"]  # Add more!
```

### Change suggestion prompt:
Find this section and modify:
```python
prompt = f"""You are a helpful coding assistant pet..."""
```

## File Comparison

```
coding_pet.py          ← Uses Claude API
coding_pet_google.py   ← Uses Google Gemini API (THIS ONE)
requirements.txt       ← For Claude version
requirements_google.txt ← For Google version
```

## Switching Between APIs

You can have both versions! Just run the one you want:

```bash
python coding_pet.py           # Claude version
python coding_pet_google.py    # Google version
```

## Future Improvements

- 🔄 Switch between APIs dynamically
- 📊 Compare suggestion quality
- 💾 Cross-save suggestion logs
- 🌐 Use Gemini's multimodal (image) capabilities

## Support

Need help?
- Google AI Studio: https://ai.google.dev/
- Python SDK: https://github.com/google/generative-ai-python
- Common Issues: Check README.md

Enjoy your coding companion powered by Google Gemini! 🐾
