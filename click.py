from __future__ import annotations

import time

import win32api
import win32con

MOVE_DELAY_SECONDS = 0.02
BUTTON_HOLD_SECONDS = 0.01

def click(x: int, y: int) -> None:
    win32api.SetCursorPos((int(x), int(y)))
    time.sleep(MOVE_DELAY_SECONDS)

    win32api.mouse_event(
        win32con.MOUSEEVENTF_LEFTDOWN,
        0,
        0,
        0,
        0,
    )
    try:
        time.sleep(BUTTON_HOLD_SECONDS)
    finally:
        win32api.mouse_event(
            win32con.MOUSEEVENTF_LEFTUP,
            0,
            0,
            0,
            0,
        )
