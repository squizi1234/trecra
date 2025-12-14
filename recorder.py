from pynput import mouse, keyboard
import json
import time

events = []
pressed_keys = set()
mouse_listener = None

def on_click(x, y, button, pressed):
    if pressed:  # Записываем только нажатие, а не отпускание
        events.append({
            "type": "click",
            "time": time.time(),
            "x": x,
            "y": y,
            "button": str(button)
        })

def on_press(key):
    global mouse_listener, pressed_keys

    pressed_keys.add(key)

    combo = []
    for k in pressed_keys:
        try:
            combo.append(k.char)
        except AttributeError:
            combo.append(str(k))
    combo_str = "+".join(sorted(combo))

    if key == keyboard.KeyCode.from_char('5'):
        print("🕓 Вставка кода из буфера")
        events.append({
            "type": "wait_clipboard",
            "time": time.time(),
            "data_type": "code"
        })
        return

    elif key == keyboard.KeyCode.from_char('6'):
        print("📧 Вставка почты из буфера")
        events.append({
            "type": "wait_clipboard",
            "time": time.time(),
            "data_type": "email"
        })
        return

    print(f"🔴 Комбинация: {combo_str}")
    events.append({
        "type": "key_combo",
        "time": time.time(),
        "combo": combo_str
    })

    if key == keyboard.Key.esc:
        print("⏹ Остановка записи...")
        mouse_listener.stop()
        return False

def on_release(key):
    if key in pressed_keys:
        pressed_keys.remove(key)

def record():
    global mouse_listener
    input("Нажмите Enter для начала записи...")
    print("🎥 Запись началась. Нажмите 9 для вставки кода, 0 для вставки почты, ESC для остановки.")
    with mouse.Listener(on_click=on_click) as ml:  # БЕЗ on_move
        mouse_listener = ml
        with keyboard.Listener(on_press=on_press, on_release=on_release) as kl:
            kl.join()

    with open("recording.json", "w", encoding="utf-8") as f:
        json.dump(events, f, indent=2, ensure_ascii=False)
    print("✅ Запись сохранена в recording.json")

record()
