# Advanced Coding Pet - Setup

## New Features Added

### 1. 🦘 Jumping
- Physics-based jump (gravity + velocity)
- Click `🦘` button, say "jump", or click pet
- Walks left/right and bounces at screen edges, shadow when in air
- Drag to reposition anywhere (ground auto-updates)

### 2. 🌐 Opening Tabs & Doing Work
Type or say:
- `open youtube` -> opens https://youtube.com
- `open github` / `open google` -> opens tab
- `search python tutorials` -> opens Google search
- `open notepad` / `open calculator` / `open chrome` / `open vscode` -> opens app
- Any other request -> Gemini parses intent and executes, or replies conversationally
- Right-click menu has quick open for Google/YouTube/GitHub

### 3. 🎤 Talk To It (Voice)
- Click `🎤` button -> turns red 🔴 = listening
- Say: "jump", "open youtube", "search for cats", "open notepad"
- Pet shows what it heard, does the action, and SPEAKS back (TTS via pyttsx3 + Windows SAPI)
- Also works by typing in the input bar + Enter / Go button

## Install

```bash
pip install -r requirements_google.txt
# If on Windows and pyaudio fails:
pip install pipwin
pipwin install pyaudio
# Or use conda:
conda install pyaudio
```

## Run

```bash
# Set API key (optional but needed for AI suggestions/parsing)
set GOOGLE_API_KEY=your_key_here   # Windows CMD
# $env:GOOGLE_API_KEY="your_key"  # PowerShell

python coding_pet_advanced.py
```

Without API key, rule-based parsing still works for jump/open/search and voice still works.

## Files
- `coding_pet_advanced.py` - NEW main file (use this)
- `coding_pet_google.py` - old simple pet
- `coding_pet_google_with_image.py` - old with SVG walk
- `claude-code.svg` - pet image
