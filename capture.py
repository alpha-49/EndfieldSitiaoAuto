from __future__ import annotations

import ctypes
import time
from datetime import datetime
from pathlib import Path

import psutil
import win32api
import win32con
import win32gui
import win32process
from PIL import Image, ImageGrab

PROJECT_DIR = Path(__file__).resolve().parent
IMAGE_DIR = PROJECT_DIR / "img"
PROCESS_NAME = "Endfield.exe"

MARKER_SIZE = (96, 128)
MARKER_LEFT_TOPS = (
    (458, 396),
    (826, 396),
    (1194, 396),
    (1562, 396),
    (1930, 396),
)


def _window_pid(hwnd: int) -> int:
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    return pid


def _window_area(hwnd: int) -> int:
    try:
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    except win32gui.error:
        return 0
    return max(0, right - left) * max(0, bottom - top)


def _find_endfield_window() -> int:
    endfield_pids = {
        process.info["pid"]
        for process in psutil.process_iter(["pid", "name"])
        if (process.info["name"] or "").casefold() == PROCESS_NAME.casefold()
    }
    if not endfield_pids:
        raise RuntimeError("Endfield.exe is not running.")

    process_windows: list[tuple[bool, bool, int, int]] = []
    title_windows: list[tuple[bool, bool, int, int]] = []

    def collect_window(hwnd: int, _: object) -> bool:
        title = win32gui.GetWindowText(hwnd)
        visible = bool(win32gui.IsWindowVisible(hwnd))
        area = _window_area(hwnd)
        pid = _window_pid(hwnd)

        if pid in endfield_pids:
            process_windows.append((visible, bool(title), area, hwnd))
        elif "endfield" in title.casefold():
            title_windows.append((visible, bool(title), area, hwnd))
        return True
    win32gui.EnumWindows(collect_window, None)
    candidates = process_windows or title_windows
    if not candidates:
        raise RuntimeError(
            "Endfield.exe is running, but its application window was not found."
        )

    return max(candidates)[3]


def _set_foreground(hwnd: int) -> None:
    if win32gui.IsIconic(hwnd):
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    else:
        win32gui.ShowWindow(hwnd, win32con.SW_SHOW)

    current_thread = win32api.GetCurrentThreadId()
    target_thread, _ = win32process.GetWindowThreadProcessId(hwnd)
    foreground = win32gui.GetForegroundWindow()
    foreground_thread = (
        win32process.GetWindowThreadProcessId(foreground)[0] if foreground else 0
    )

    attached_threads: list[int] = []
    for thread_id in {target_thread, foreground_thread}:
        if thread_id and thread_id != current_thread:
            try:
                win32process.AttachThreadInput(current_thread, thread_id, True)
                attached_threads.append(thread_id)
            except win32gui.error:
                pass

    try:
        win32gui.BringWindowToTop(hwnd)
        win32gui.SetForegroundWindow(hwnd)
        try:
            win32gui.SetActiveWindow(hwnd)
            win32gui.SetFocus(hwnd)
        except win32gui.error:
            pass
    finally:
        for thread_id in reversed(attached_threads):
            try:
                win32process.AttachThreadInput(current_thread, thread_id, False)
            except win32gui.error:
                pass


def _enable_dpi_awareness() -> None:
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except (AttributeError, OSError):
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            pass


def _crop_markers(screenshot: Image.Image) -> list[Image.Image]:
    width, height = MARKER_SIZE
    markers: list[Image.Image] = []
    for left, top in MARKER_LEFT_TOPS:
        right = left + width
        bottom = top + height
        if right > screenshot.width or bottom > screenshot.height:
            raise RuntimeError(
                f"Screenshot size {screenshot.size} is too small for the "
                "configured marker crop positions."
            )
        markers.append(screenshot.crop((left, top, right, bottom)))
    return markers


def capture(save: bool = False) -> list[Image.Image]:
    _enable_dpi_awareness()
    hwnd = _find_endfield_window()
    _set_foreground(hwnd)
    time.sleep(0.2)
    screenshot = ImageGrab.grab(all_screens=True)
    markers = _crop_markers(screenshot)
    if save:
        IMAGE_DIR.mkdir(parents=True, exist_ok=True)
        prefix = datetime.now().strftime("endfield_%Y%m%d_%H%M%S_%f")
        for index, marker in enumerate(markers, start=1):
            marker.save(IMAGE_DIR / f"{prefix}_{index}.png", format="PNG")
    return markers
