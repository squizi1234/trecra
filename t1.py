import json, time, random, string, pyperclip, re, requests
from pywinauto import Desktop
from pynput.keyboard import Controller, Key

RECORD_FILE = "recordinggff.json"
API = "https://api.mail.tm"
keyboard = Controller()

# ================== MAIL.TM ==================
class MailTM:
    def __init__(self):
        self.email = None
        self.password = None
        self.token = None
        self.headers = {}
    
    def create_account(self):
        domains = requests.get(f"{API}/domains").json()["hydra:member"]
        domain = domains[0]["domain"]
        self.email = f"{''.join(random.choices(string.ascii_lowercase+string.digits, k=10))}@{domain}"
        self.password = ''.join(random.choices(string.ascii_letters+string.digits, k=12))
        r = requests.post(f"{API}/accounts", json={"address": self.email, "password": self.password})
        if r.status_code != 201: 
            raise Exception("Ошибка создания почты")
        r = requests.post(f"{API}/token", json={"address": self.email, "password": self.password})
        if r.status_code != 200: 
            raise Exception("Ошибка токена")
        self.token = r.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        print(f"✅ Почта создана: {self.email}")
    
    def wait_for_code(self, timeout=300):
        """Ждет письмо и извлекает из него 6-значный код"""
        seen = set()
        start = time.time()
        print(f"⏳ Ожидание письма с кодом (таймаут {timeout}сек)...")
        
        while time.time() - start < timeout:
            try:
                r = requests.get(f"{API}/messages", headers=self.headers)
                messages = r.json()["hydra:member"]
                
                for msg in messages:
                    if msg["id"] in seen: 
                        continue
                    seen.add(msg["id"])
                    
                    full = requests.get(f"{API}/messages/{msg['id']}", headers=self.headers).json()
                    subject = full.get("subject", "")
                    text = full.get("text", "")
                    html = full.get("html", [])
                    
                    full_text = subject + " " + text
                    if html:
                        for item in html:
                            full_text += " " + str(item)
                    
                    print(f"📬 Получено письмо: {subject[:50]}")
                    
                    match = re.search(r'\b([A-Z0-9]{6})\b', full_text.upper())
                    if match:
                        code = match.group(1)
                        print(f"✅ Код найден: {code}")
                        return code
                    else:
                        print(f"⚠️ Код не найден в письме, продолжаем ждать...")
                
            except Exception as e:
                print(f"⚠️ Ошибка при проверке почты: {e}")
            
            time.sleep(5)
        
        raise TimeoutError("Код не пришёл за отведенное время")

# ================== HELPERS ==================
def paste_text(val):
    pyperclip.copy(val)
    time.sleep(0.2)
    keyboard.press(Key.ctrl)
    keyboard.press('v')
    keyboard.release('v')
    keyboard.release(Key.ctrl)
    time.sleep(0.2)

def generate_birthdate():
    """Генерирует случайную дату рождения (18-65 лет)"""
    import datetime
    current_year = datetime.datetime.now().year
    age = random.randint(18, 65)
    birth_year = current_year - age
    birth_month = random.randint(1, 12)
    birth_day = random.randint(1, 28)
    return {"month": birth_month, "day": birth_day, "year": birth_year}

# ================== INTERACTIVE RECORD ==================
def interactive_record():
    windows = Desktop(backend="uia").windows()
    edge_windows = [w for w in windows if "InPrivate" in w.window_text()]
    if not edge_windows:
        print("❌ Окно Edge не найдено")
        exit()
    edge_window = edge_windows[0]

    try:
        with open(RECORD_FILE, "r", encoding="utf-8") as f:
            recording = json.load(f)
    except FileNotFoundError:
        recording = []

    mail = MailTM()
    mail.create_account()
    print(f"\n📧 Временная почта для записи: {mail.email}")
    print("Используйте эту почту при регистрации в браузере\n")

    # Генерируем дату рождения ОДИН РАЗ для всей записи
    bd = generate_birthdate()
    print(f"🎂 Дата рождения для записи: {bd['day']:02d}.{bd['month']:02d}.{bd['year']}\n")

    print("Начинаем интерактивную запись действий (q - выход, r - обновить список)")

    while True:
        buttons = [btn for btn in edge_window.descendants(control_type="Button") if btn.is_visible()]
        inputs = [fld for fld in edge_window.descendants(control_type="Edit") if fld.is_visible()]
        links = [lnk for lnk in edge_window.descendants(control_type="Hyperlink") if lnk.is_visible()]
        
        # Ищем spinbutton элементы (для даты рождения)
        spinbuttons = []
        for elem in edge_window.descendants():
            try:
                if elem.is_visible():
                    name = (elem.element_info.name or "").lower()
                    ctrl_type = str(elem.element_info.control_type).lower()
                    # Ищем элементы со словами day, month, year или spinbutton
                    if any(kw in name for kw in ["день", "месяц", "год", "day", "month", "year"]) or "spin" in ctrl_type:
                        spinbuttons.append(elem)
            except:
                pass

        print("\n--- Кнопки ---")
        for i, btn in enumerate(buttons):
            print(f"{i}: {btn.window_text()}")
        print("\n--- Spinbuttons (дата рождения) ---")
        for i, spin in enumerate(spinbuttons):
            try:
                name = spin.element_info.name or f"Spin {i+1}"
            except:
                name = f"Spin {i+1}"
            print(f"{i}: {name}")
        print("\n--- Поля ---")
        for i, fld in enumerate(inputs):
            print(f"{i}: {fld.window_text() or 'Edit '+str(i+1)}")
        print("\n--- Ссылки ---")
        for i, lnk in enumerate(links):
            print(f"{i}: {lnk.window_text() or 'Link '+str(i+1)}")

        choice = input("\nЧто делать? (b=кнопка, s=spinbutton, e=поле, l=ссылка, r=обновить список, q=готово): ").strip().lower()
        if choice=="q": 
            break
        elif choice=="r": 
            continue
        elif choice=="b":
            idx = int(input("Введите индекс кнопки: "))
            if 0<=idx<len(buttons):
                btn = buttons[idx]
                try:
                    btn.invoke()
                    print(f"✓ Кнопка '{btn.window_text()}' нажата!")
                    recording.append({"type":"click_button","text":btn.window_text()})
                except Exception as e:
                    print(f"❌ Ошибка: {e}")
        
        elif choice=="s":
            idx = int(input("Введите индекс spinbutton: "))
            if 0<=idx<len(spinbuttons):
                spin = spinbuttons[idx]
                try:
                    spin_name = spin.element_info.name or f"Spin {idx+1}"
                except:
                    spin_name = f"Spin {idx+1}"
                
                # Определяем что это за поле
                name_lower = "None"
                
                if "день" in name_lower or "day" in name_lower:
                    val = str(bd["day"])
                    part = "day"
                elif "месяц" in name_lower or "month" in name_lower:
                    val = str(bd["month"])
                    part = "month"
                elif "год" in name_lower or "year" in name_lower:
                    val = str(bd["year"])
                    part = "year"
                else:
                    part = input("Что это? (d)день, (m)месяц, (y)год: ").strip().lower()
                    if part=="d":
                        val = str(bd["day"])
                        part = "day"
                    elif part=="m":
                        val = str(bd["month"])
                        part = "month"
                    else:
                        val = str(bd["year"])
                        part = "year"
                
                print(f"DEBUG: Поле '{spin_name}' -> часть '{part}' -> значение '{val}'")
                
                try:
                    # Пробуем set_edit_text (для некоторых элементов)
                    spin.set_edit_text(val)
                except:
                    try:
                        # Если не работает, пробуем через фокус и type_keys
                        spin.set_focus()
                        time.sleep(0.3)
                        # Отправляем текст целиком
                        spin.set_text(val)
                    except:
                        # Последняя попытка - через invoke
                        spin.set_focus()
                        time.sleep(0.3)
                        spin.type_keys(val)
                
                recording.append({"type":"spinbutton","name":spin_name,"value_type":"birthdate","part":part})
                print(f"✓ {part.capitalize()} вставлен: {val}")
        
        elif choice=="e":
            idx = int(input("Введите индекс поля: "))
            if 0<=idx<len(inputs):
                fld = inputs[idx]
                field_name = fld.window_text() or f"Edit {idx+1}"
                text_type = input("Вставить: (u)текст, (e)email, (c)код, (b)дата? [u/e/c/b]: ").strip().lower()
                
                if text_type=="u":
                    val = input("Введите текст: ")
                    fld.set_focus()
                    paste_text(val)
                    recording.append({"type":"edit_field","text":field_name,"value_type":"user","value":val})
                    print(f"✓ Текст вставлен: {val}")
                
                elif text_type=="e":
                    fld.set_focus()
                    paste_text(mail.email)
                    recording.append({"type":"edit_field","text":field_name,"value_type":"email"})
                    print(f"✓ Email вставлен: {mail.email}")
                
                elif text_type=="c":
                    print(f"\n📧 Ожидание кода на почту: {mail.email}")
                    try:
                        code = mail.wait_for_code()
                        fld.set_focus()
                        paste_text(code)
                        recording.append({"type":"edit_field","text":field_name,"value_type":"code"})
                        print(f"✅ Код получен и вставлен: {code}")
                    except TimeoutError:
                        print("❌ Код не пришёл в течение таймаута")
                
                elif text_type=="b":
                    bd = generate_birthdate()
                    part = input("Что вставить? (d)день, (m)месяц, (y)год: ").strip().lower()
                    if part=="d":
                        val = str(bd["day"])
                        fld.set_focus()
                        paste_text(val)
                        recording.append({"type":"edit_field","text":field_name,"value_type":"birthdate","part":"day"})
                        print(f"✓ День вставлен: {val}")
                    elif part=="m":
                        val = str(bd["month"])
                        fld.set_focus()
                        paste_text(val)
                        recording.append({"type":"edit_field","text":field_name,"value_type":"birthdate","part":"month"})
                        print(f"✓ Месяц вставлен: {val}")
                    elif part=="y":
                        val = str(bd["year"])
                        print(val)
                        fld.set_focus()
                        paste_text(val)
                        recording.append({"type":"edit_field","text":field_name,"value_type":"birthdate","part":"year"})
                        print(f"✓ Год вставлен: {val}")
        
        elif choice=="l":
            idx = int(input("Введите индекс ссылки: "))
            if 0<=idx<len(links):
                lnk = links[idx]
                try:
                    lnk.invoke()
                    print(f"✓ Ссылка '{lnk.window_text()}' нажата!")
                    recording.append({"type":"click_link","text":lnk.window_text()})
                except Exception as e:
                    print(f"❌ Ошибка: {e}")
    
    with open(RECORD_FILE, "w", encoding="utf-8") as f:
        json.dump(recording, f, ensure_ascii=False, indent=4)
    print(f"\n✅ Запись сохранена в {RECORD_FILE}")

# ================== AUTOPLAY ==================
def autoplay():
    try:
        with open(RECORD_FILE, "r", encoding="utf-8") as f:
            events = json.load(f)
    except FileNotFoundError:
        print(f"❌ {RECORD_FILE} не найден!")
        return

    print("🚀 Старт через 5 секунд...")
    time.sleep(5)
    
    mail = MailTM()
    mail.create_account()
    bd = generate_birthdate()
    print(f"🎂 Дата рождения: {bd['day']:02d}.{bd['month']:02d}.{bd['year']}")
    
    for event in events:
        time.sleep(0.1)
        windows = Desktop(backend="uia").windows()
        edge_windows = [w for w in windows if "InPrivate" in w.window_text()]
        if not edge_windows: 
            continue
        edge_window = edge_windows[0]

        if event["type"]=="click_button":
            # Ищем кнопку по тексту
            target_text = event["text"]
            buttons = [btn for btn in edge_window.descendants(control_type="Button") if btn.is_visible()]
            for btn in buttons:
                if btn.window_text() == target_text:
                    btn.invoke()
                    print(f"✓ Кнопка '{target_text}' нажата")
                    break
        
        elif event["type"]=="edit_field":
            # Ищем поле по тексту
            target_text = event["text"]
            inputs = [fld for fld in edge_window.descendants(control_type="Edit") if fld.is_visible()]
            
            for fld in inputs:
                field_name = fld.window_text() or ""
                if field_name == target_text or (target_text.startswith("Edit") and field_name == ""):
                    fld.set_focus()
                    
                    if event["value_type"]=="user":
                        paste_text(event["value"])
                        print(f"✓ Текст вставлен: {event['value']}")
                    
                    elif event["value_type"]=="email":
                        paste_text(mail.email)
                        print(f"✓ Email вставлен: {mail.email}")
                    
                    elif event["value_type"]=="code":
                        try:
                            code = mail.wait_for_code(timeout=300)
                            paste_text(code)
                            print(f"✅ Код получен и вставлен: {code}")
                        except TimeoutError:
                            print("❌ Код не пришёл, пропускаем")
                    
                    elif event["value_type"]=="birthdate":
                        part = event.get("part", "day")
                        val = str(bd[part])
                        paste_text(val)
                        print(f"✓ {part.capitalize()} вставлен: {val}")
                    break
        
        elif event["type"]=="spinbutton":
            # Ищем spinbutton по имени
            target_name = event["name"]
            part = event.get("part", "day")
            val = str(bd[part])
            
            print(f"DEBUG: Ищем spinbutton '{target_name}' для части '{part}' со значением '{val}'")
            
            for elem in edge_window.descendants():
                try:
                    if elem.is_visible():
                        name = elem.element_info.name or ""
                        if name == target_name:
                            try:
                                elem.set_edit_text(val)
                            except:
                                try:
                                    elem.set_focus()
                                    time.sleep(0.3)
                                    elem.set_text(val)
                                except:
                                    elem.set_focus()
                                    time.sleep(0.3)
                                    elem.type_keys(val)
                            
                            print(f"✓ {part.capitalize()} вставлен: {val}")
                            break
                except:
                    pass
        
        elif event["type"]=="click_link":
            # Ищем ссылку по тексту
            target_text = event["text"]
            links = [lnk for lnk in edge_window.descendants(control_type="Hyperlink") if lnk.is_visible()]
            for lnk in links:
                if lnk.window_text() == target_text:
                    lnk.invoke()
                    print(f"✓ Ссылка '{target_text}' нажата")
                    break
    
    print("🏁 Воспроизведение завершено")

# ================== MAIN ==================
mode = input("Выберите режим: (r) запись, (p) воспроизведение: ").strip().lower()
if mode=="r":
    interactive_record()
elif mode=="p":
    autoplay()
else:
    print("❌ Неверный режим. Используйте 'r' или 'p'")