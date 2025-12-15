from pywinauto import Desktop
import time

# Получаем окно Edge
windows = Desktop(backend="uia").windows()
edge_windows = [w for w in windows if "Edge" in w.window_text()]

if not edge_windows:
    print("Окна Edge не найдены")
else:
    window = edge_windows[0]  # берем первое найденное окно
    print(f"Работаем с окном: '{window.window_text()}'")
    
    # Находим все поля для ввода
    input_fields = [fld for fld in window.descendants(control_type="Edit") if fld.is_visible()]
    
    if not input_fields:
        print("Поля ввода не найдены")
    else:
        # Например, берём пустое поле (обычно второе)
        target_field = input_fields[1]
        target_field.set_focus()
        time.sleep(0.2)
        target_field.type_keys("Привет, это тест!", with_spaces=True)
        print("Текст введён в поле")
        
        # Если нужно, можно нажать Enter
        target_field.type_keys("{ENTER}")
        print("Enter нажат")
