# Coding Pet PRO - Setup

New file: `coding_pet_pro.py` - has EVERYTHING

## Features

### 🦘 Jumping Tab-to-Tab
- Pet does parabolic jump (up + horizontal leap) THEN switches browser tab via `Ctrl+Tab`
- Trigger: Click 🗂️ button, right-click → "Jump Next Tab", or say/type `"jump to next tab"` / `"jump to previous tab"`
- Implementation `coding_pet_pro.py:127` `jump_between_tabs()` - animates with `velocity_y` + `pet_x += 180`, then uses `pyautogui.hotkey('ctrl','tab')` + fallback `SendKeys` + auto-focuses Chrome/Edge via `win32gui`
- Wants to jump on its own? It still walks and you can say `"jump"` anytime

### 🖥️ Full PC Control
- `open youtube/github/google` → new tab
- `search X` → Google search
- `open notepad/calculator/chrome/vscode/device manager/task manager` → launches app
- `run <command>` via shell
- Voice + text both work via `AgentWorker`

### 🛠️ "Fix My Drivers" - Automatic
Trigger: click 🛠️ button or say/type `"fix my drivers"`

Workflow `DriverFixWorker` `coding_pet_pro.py:24`:
1. **Search Google** - opens `https://google.com/search?q=Windows 11 fix drivers...` + asks Gemini for 3-step summary
2. **Diagnose** - runs `driverquery /v`, `pnputil /enum-devices /problem 28`, `Get-PnpDevice | Where Status != OK` and streams to black log area
3. **Fix** - runs `pnputil /scan-devices`, `UsoClient StartScan` (Windows Update scan), checks `PSWindowsUpdate` for driver updates
4. **Open tools** - auto-opens `devmgmt.msc` + `ms-settings:windowsupdate` and shows recommendations (Optional updates → Driver updates, OEM assistants, `winget upgrade --all`)
- Progress shown live in `QTextEdit` log + voice feedback

## Install
```bash
pip install -r requirements_google.txt
# If pyaudio fails on Windows:
pip install pipwin
pipwin install pyaudio
# Or: conda install pyaudio
```

## Run (AS ADMIN for driver fix)
Right-click → Run as Administrator (needed for `pnputil`, `sfc`, etc.)

```bash
# PowerShell as Admin:
$env:GOOGLE_API_KEY="your_key"  # optional
python coding_pet_pro.py
```

## Usage Examples
- 🎤 Click 🎤 → Say `"fix my drivers"` → pet searches Google, diagnoses, fixes, opens Device Manager
- 🎤 Say `"jump to next tab"` → pet leaps visually and switches Chrome tab
- Type `"open youtube"` → new tab
- Click 🛠️ instantly runs driver fix

## Files
- `coding_pet_pro.py` ← USE THIS (all features)
- `coding_pet_advanced.py` ← previous version (no tab-jump/driver-fix)
- `requirements_google.txt` updated with `pyautogui`, `requests`, `beautifulsoup4`
