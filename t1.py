import win32gui
import win32con
import time

# Функция для перечисления всех видимых окон
def enum_windows():
    windows = []

    def callback(hwnd, extra):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title:
                windows.append((hwnd, title))
        return True

    win32gui.EnumWindows(callback, None)
    return windows

# Находим все окна Edge
all_windows = enum_windows()
edge_windows = [(hwnd, title) for hwnd, title in all_windows if 'Edge' in title]

if not edge_windows:
    print("Окна Microsoft Edge не найдены!")
else:
    # Берём первое окно
    hwnd, title = edge_windows[0]
    print(f"Используем окно: HWND={hwnd}, Title='{title}'")

    # Координаты внутри окна, куда хотим кликнуть
    x, y = 0, 0
    lparam = (y << 16) | x

    # Отправляем клик левой кнопкой мыши
    win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lparam)
    time.sleep(0.05)
    win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, None, lparam)

    print(f"Клик отправлен в окно Edge по координатам ({x}, {y})!")
