"""Read the actual NVDA Speech Viewer for one explicitly owned NVDA process.

This reads the viewer's native RichEdit control. It neither inspects arbitrary
windows nor synthesizes speech from the ResearchOS DOM or accessibility tree.
"""
from __future__ import annotations

import argparse
import ctypes
import json

import win32con
import win32gui
import win32process


def _speech_text(hwnd: int) -> str:
    length = min(win32gui.SendMessage(hwnd, win32con.WM_GETTEXTLENGTH, 0, 0), 65535)
    buffer = ctypes.create_unicode_buffer(length + 1)
    result = ctypes.c_size_t()
    send = ctypes.windll.user32.SendMessageTimeoutW
    send.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_size_t,
                     ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint,
                     ctypes.POINTER(ctypes.c_size_t)]
    send.restype = ctypes.c_void_p
    if not send(hwnd, win32con.WM_GETTEXT, len(buffer), ctypes.cast(buffer, ctypes.c_void_p),
                win32con.SMTO_ABORTIFHUNG, 2000, ctypes.byref(result)):
        raise RuntimeError('NVDA Speech Viewer RichEdit did not respond')
    return buffer.value


def inspect(pid: int) -> dict:
    if pid <= 0:
        raise ValueError('an exact NVDA process ID is required')
    viewers = []

    def on_window(hwnd: int, _arg: object) -> None:
        if win32process.GetWindowThreadProcessId(hwnd)[1] != pid or not win32gui.IsWindowVisible(hwnd):
            return
        title = win32gui.GetWindowText(hwnd)
        if 'NVDA' not in title:
            return
        children = []
        win32gui.EnumChildWindows(hwnd, lambda child, _unused: children.append(child), None)
        editors = [child for child in children if win32gui.GetClassName(child).upper().startswith('RICHEDIT')]
        if len(editors) == 1:
            viewers.append({'window_handle': hwnd, 'title': title,
                            'editor_handle': editors[0], 'speech': _speech_text(editors[0])})

    win32gui.EnumWindows(on_window, None)
    if len(viewers) != 1:
        raise RuntimeError(f'expected one visible NVDA Speech Viewer for PID {pid}; found {len(viewers)}')
    return {'source': 'NVDA Speech Viewer native RichEdit', 'nvda_pid': pid, **viewers[0]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--pid', type=int, required=True)
    args = parser.parse_args()
    print(json.dumps(inspect(args.pid), ensure_ascii=False))


if __name__ == '__main__':
    main()
