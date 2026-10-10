# Coding Pet

A small desktop coding companion built with Python and PyQt5. The pet can offer coding suggestions through Google Gemini, respond to voice input, and run selected desktop actions. Several iterations are included; `coding_pet_pro.py` is the main all-in-one version.

## Bob demo

<video controls width="720" src="claude%20.mp4">
  Your browser does not support embedded video. [Open the Bob demo](<claude .mp4>).
</video>

## Choose a version

- `coding_pet_pro.py` — recommended full desktop app, with tab switching, voice controls, app launching, and a driver troubleshooting workflow.
- `coding_pet_advanced.py` — earlier advanced assistant.
- `coding_pet_google.py` and `coding_pet_google_with_image.py` — Gemini-focused variants.
- `coding_pet_bob.py` — Bob, the monitoring and automation variant; see `SETUP_PRO.md` and `SKILLS.md` for its supporting features.

Use `coding_pet_bob.py` on Linux. The other variants retain their original platform-specific behavior.

The app can run on Windows or a Linux desktop. Bob roams in two dimensions across the available desktop. On Wayland, Qt cannot generally reposition top-level windows, so free roaming requires X11 or XWayland; Bob selects XWayland automatically when both Wayland and X11 display variables are available. Simulated keyboard or mouse actions may also be restricted under Wayland. The app can launch commands and applications, so only use commands you understand. Gemini suggestions require a Google API key; basic built-in actions do not.

## Requirements

- Python 3.10 or newer (Python 3.12 is used by the checked-in bytecode files).
- Windows is recommended for the full feature set. Some UI and Gemini features may work on other desktop platforms, but Windows-specific automation will not.
- Optional: a Google AI Studio API key for Gemini-powered suggestions.

## Install and run

From this directory, create and activate a virtual environment, then install dependencies:

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements_google.txt
python coding_pet_pro.py
```

For Gemini features, set `GOOGLE_API_KEY` before launching. PowerShell:

```powershell
$env:GOOGLE_API_KEY = "your-key"
python coding_pet_pro.py
```

macOS/Linux:

```bash
export GOOGLE_API_KEY="your-key"
python coding_pet_pro.py
```

If PyAudio installation fails on Windows, consult `SETUP_PRO.md` for alternatives. Microphone input is optional.

### Linux

On Linux, install PortAudio development files if PyAudio needs to build from source. Install a speech engine for spoken replies. On Arch Linux, a typical setup is:

```bash
sudo pacman -S --needed python python-pip python-virtualenv python-pyqt5 python-pyaudio portaudio espeak-ng xdotool wmctrl python-requests python-beautifulsoup4 python-psutil
python -m venv --system-site-packages .venv
source .venv/bin/activate
python -m pip install -r requirements_google.txt
python coding_pet_bob.py
```

On Debian or Ubuntu, install `python3-venv`, `portaudio19-dev`, and `espeak-ng` first. Other distributions need their equivalent Python, Qt/PyQt5, PortAudio, and optional speech-engine packages. If PyAudio fails in the virtual environment, install your distribution's PyAudio package or PortAudio development files, then retry.

The bottom microphone button sends recognized speech to Bob. Speech recognition uses Google's service and needs internet access. Spoken replies use `pyttsx3` where available, with Linux fallbacks to `espeak-ng`, `espeak`, or `spd-say`. Linux hardware checks are read-only; use your distribution's package manager for driver changes. X11 generally supports more keyboard and mouse automation than Wayland.

## Project layout

The top-level Python files are the app variants. `animation_engine.py` and `automation_engine.py` contain reusable animation and automation support. The setup guides cover Google/Gemini, image, advanced, and PRO configurations. `bob_config.json`, `bob_memory.json`, and `bob_vault.json` hold local app state/configuration; database files are runtime data and should not be committed.

`tests/` and `playwright.config.js` belong to a JavaScript Playwright starter currently present in the folder; they do not test the Python desktop app.

## Troubleshooting

- **Qt or display errors:** run from a desktop session with a working display; this is not a headless/server app.
- **Gemini errors:** check `GOOGLE_API_KEY`, network access, and the API key's enabled access.
- **Voice input errors:** check microphone permissions and PyAudio installation, or run without voice input.
- **Linux app launch fails:** install the app through your distribution and confirm its executable is on `PATH`.
- **Linux voice input fails:** install PortAudio and PyAudio, check microphone permissions, and verify internet access.
- **Keyboard automation fails on Wayland:** run an X11 session for broader simulated input support; Wayland intentionally restricts desktop input automation.

See `SETUP_PRO.md`, `SETUP_ADVANCED.md`, `SETUP_GOOGLE.md`, and `SETUP_WITH_IMAGE.md` for variant-specific details.
