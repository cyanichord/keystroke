# Keystroke Script

A cross-platform keystroke flow runner with global hotkeys, capture tools, and a lightweight flow editor.

## Features

- Global hotkeys for run/stop/capture (customizable).
- Flow editor with JSON validation and syntax highlighting.
- Auto capture that records key hold durations and spacing.
- Optional looping until the stop hotkey is pressed.
- Log view and key reference table.

## Requirements

- Python 3.10+
- Windows/macOS/Linux

## Install

```bash
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

## Usage

1. Configure hotkeys in the left panel (Start/Stop/Capture/Auto Capture).
2. Use Capture Key to add a single step, or Auto Capture to build a flow.
3. Edit the JSON flow directly in the Flow Editor tab if needed.
4. Press the start hotkey to run, and the stop hotkey to stop.

## Flow Format

```json
{
	"spacing": 0.05,
	"steps": [
		{"key": "a", "duration": 0.12, "spacing": 0.3},
		{"key": "b", "duration": 0.08}
	]
}
```

- `spacing`: Global delay (seconds) between steps.
- `steps[].duration`: How long to hold the key.
- `steps[].spacing` (optional): Delay after this step, overrides global spacing.

## Hotkeys

Default hotkeys (can be changed in the UI):

- Run: `,`
- Stop: `.`
- Capture: `[`
- Auto capture: `]`
