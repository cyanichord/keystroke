"""
key_reference.py
Reference tables for keyboard keys.
"""

KEYBOARD_KEYS: list[dict] = [
    {"category": "Modifiers",  "key": "ctrl",        "description": "Control key"},
    {"category": "Modifiers",  "key": "shift",       "description": "Shift key"},
    {"category": "Modifiers",  "key": "alt",         "description": "Alt / Option key"},
    {"category": "Modifiers",  "key": "cmd",         "description": "Command (macOS) / Win key"},
    {"category": "Combos",     "key": "ctrl+c",      "description": "Copy"},
    {"category": "Combos",     "key": "ctrl+v",      "description": "Paste"},
    {"category": "Combos",     "key": "ctrl+z",      "description": "Undo"},
    {"category": "Combos",     "key": "ctrl+1",      "description": "Ctrl + number 1"},
    {"category": "Combos",     "key": "ctrl+shift+t","description": "Ctrl + Shift + T"},
    {"category": "Navigation", "key": "up",          "description": "Arrow Up"},
    {"category": "Navigation", "key": "down",        "description": "Arrow Down"},
    {"category": "Navigation", "key": "left",        "description": "Arrow Left"},
    {"category": "Navigation", "key": "right",       "description": "Arrow Right"},
    {"category": "Navigation", "key": "home",        "description": "Home"},
    {"category": "Navigation", "key": "end",         "description": "End"},
    {"category": "Navigation", "key": "page_up",     "description": "Page Up"},
    {"category": "Navigation", "key": "page_down",   "description": "Page Down"},
    {"category": "Function",   "key": "f1",          "description": "F1"},
    {"category": "Function",   "key": "f5",          "description": "F5 (Refresh)"},
    {"category": "Function",   "key": "f12",         "description": "F12"},
    {"category": "Special",    "key": "tab",         "description": "Tab"},
    {"category": "Special",    "key": "esc",         "description": "Escape"},
    {"category": "Special",    "key": "backspace",   "description": "Backspace"},
    {"category": "Special",    "key": "delete",      "description": "Delete"},
    {"category": "Printable",  "key": "a-z",         "description": "Single letter keys"},
    {"category": "Printable",  "key": "0-9",         "description": "Number keys"},
]
