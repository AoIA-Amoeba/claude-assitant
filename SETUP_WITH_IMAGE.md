# 🐾 Coding Pet with Your Claude Code Image

Setup guide for the version using your custom Claude Code SVG image!

## Files You Need

Download all 3 files to the **same folder**:

1. ✅ `coding_pet_google_with_image.py` - Main app
2. ✅ `claude-code.svg` - Your pet image (I already included this!)
3. ✅ `requirements_google.txt` - Dependencies

**IMPORTANT:** These files MUST be in the same folder!

## Quick Setup

### Step 1: Install Dependencies

```powershell
pip install -r requirements_google.txt
```

### Step 2: Set Google API Key

```powershell
$env:GOOGLE_API_KEY="AQ.Ab8RN6LDX4WpQw959vvU7D1HKmEVFWvqHZ0OQz7WdFmjAo1kxw"
```

### Step 3: Run It!

```powershell
python coding_pet_google_with_image.py
```

## What's Different?

✨ **Uses your Claude Code SVG image** instead of simple shapes
- Happy state: Glowing orange border
- Thinking state: Animated thought bubbles
- Sad state: Darkened with red tint

## Troubleshooting

### "SVG file not found"

Make sure `claude-code.svg` is in the same folder as `coding_pet_google_with_image.py`

```
C:\Users\jadha\OneDrive\claude assitant\
├── coding_pet_google_with_image.py
├── claude-code.svg          ← This must be here!
└── requirements_google.txt
```

### Pet image doesn't show

1. Close the app
2. Check that all 3 files are in the same folder
3. Run again

### Still having issues?

Copy the exact file paths and verify:
```powershell
ls "C:\Users\jadha\OneDrive\claude assitant\"
```

You should see all 3 files listed.

## Customization

### Change pet size

In `coding_pet_google_with_image.py`, find:
```python
self.pet_label.setFixedSize(150, 150)
```

Change `150, 150` to a different size (e.g., `200, 200`)

### Change colors in different states

Look for these sections and modify RGB values:
```python
QColor(217, 119, 87, 100)  # Happy glow color
QColor(200, 200, 200, 150) # Thinking bubble color
QColor(255, 100, 100, 80)  # Sad darkening color
```

## Running the Pet

Once it's working, you should see:
1. A small Claude Code icon on your desktop
2. Every 60 seconds: checks if you're coding
3. If coding detected: shows "🤔 Thinking..." then a suggestion
4. Click the pet to dismiss or get a new suggestion
5. Right-click for menu

## Tips

- The pet stays on top of other windows
- Won't interfere with your work
- Suggestions logged automatically
- No data sent to anyone except Google (for suggestions)

## Still using Claude API?

You can have BOTH versions:
- `coding_pet_google_with_image.py` ← Google version with image
- `coding_pet.py` ← Original Claude version

Just run whichever you want!

---

Enjoy your custom coding pet! 🐾✨
