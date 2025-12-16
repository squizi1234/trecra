import json, time, random, string, pyperclip, re, requests
from pywinauto import Desktop
from pynput.keyboard import Controller, Key

RECORD_FILE = "recordinggff.json"
API = "https://api.mail.tm"
keyboard = Controller()
if True:
	def extract_code_from_message(message_text):
		# Пример извлечения кода из текста сообщения
		# Здесь вы можете настроить логику в зависимости от формата ваших писем
		try:
			if "код OpenAI" in message_text:
				message_text = message_text.replace("Ваш код OpenAI","")
				message_text = message_text.replace(" ","")

				return str(message_text)
			return None
		except Exception as e:
			print(e)
			return None
# ---------------- MailTM ----------------
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
                    full_text = subject + " " + text
                    match = re.search(r'\b([A-Z0-9]{6})\b', full_text.upper())
                    if match:
                        code = extract_code_from_message(subject)
                        print(f"✅ Код найден: {code}")
                        return code
            except Exception as e:
                print(f"⚠️ Ошибка при проверке почты: {e}")
            time.sleep(5)
        raise TimeoutError("Код не пришёл за отведенное время")

# ---------------- Helpers ----------------
def paste_text(val):
    pyperclip.copy(val)
    time.sleep(0.1)
    keyboard.press(Key.ctrl)
    keyboard.press('v')
    keyboard.release('v')
    keyboard.release(Key.ctrl)
    time.sleep(0.1)

def generate_birthdate():
    import datetime
    current_year = datetime.datetime.now().year
    age = random.randint(18, 65)
    birth_year = current_year - age
    birth_month = random.randint(1, 12)
    birth_day = random.randint(1, 28)
    return {"month": birth_month, "day": birth_day, "year": birth_year}

def wait_for_element(elements, timeout=10):
    start = time.time()
    while time.time() - start < timeout:
        for el in elements:
            try:
                if el.is_visible() and el.is_enabled():
                    return el
            except:
                pass
        time.sleep(0.2)
    return None

# ---------------- Autoplay ----------------
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
        time.sleep(2)
        success = False
        start = time.time()
        while time.time() - start < 60:  # ждём до 15 секунд
            windows = Desktop(backend="uia").windows()
            edge_windows = [w for w in windows if "InPrivate" in w.window_text()]
            if not edge_windows: 
                time.sleep(0.5)
                continue
            edge_window = edge_windows[0]

            if event["type"]=="click_button":
                buttons = [btn for btn in edge_window.descendants(control_type="Button")]
                btn = next((b for b in buttons if (b.window_text() == event["text"])), None)
                if btn and btn.is_visible() and btn.is_enabled():
                    btn.invoke()
                    print(f"✓ Кнопка '{event['text']}' нажата")
                    success = True

            elif event["type"]=="edit_field":
                inputs = [fld for fld in edge_window.descendants(control_type="Edit")]
                fld = next((f for f in inputs if f.window_text() == event["text"] or (event["text"].startswith("Edit") and f.window_text() == "")), None)
                if fld and fld.is_visible() and fld.is_enabled():
                    fld.set_focus()
                    if event["value_type"]=="user":
                        paste_text(event["value"])
                        print(f"✓ Текст вставлен: {event['value']}")
                    elif event["value_type"]=="email":
                        paste_text(mail.email)
                        print(f"✓ Email вставлен: {mail.email}")
                    elif event["value_type"]=="code":
                        try:
                            code = mail.wait_for_code()
                            paste_text(code)
                            print(f"✅ Код получен и вставлен: {code}")
                        except TimeoutError:
                            print("⚠️ Код не пришёл")
                    elif event["value_type"]=="birthdate":
                        val = str(bd.get(event.get("part","day"), "01"))
                        paste_text(val)
                        print(f"✓ {event.get('part','day').capitalize()} вставлен: {val}")
                    success = True

            elif event["type"]=="spinbutton":
                elems = [e for e in edge_window.descendants() if "spin" in str(e.element_info.control_type).lower() or "editable" in str(e.element_info.control_type).lower()]
                spin = next((s for s in elems if (s.element_info.name or "") == event["name"]), None)
                if spin and spin.is_visible() and spin.is_enabled():
                    val = str(bd.get(event.get("part","day"), "01"))
                    try:
                        spin.set_edit_text(val)
                    except:
                        spin.set_focus()
                        try:
                            spin.set_text(val)
                        except:
                            spin.type_keys(val)
                    print(f"✓ Spin '{event['name']}' {event.get('part','day')} вставлен: {val}")
                    success = True

            elif event["type"]=="click_link":
                links = [lnk for lnk in edge_window.descendants(control_type="Hyperlink")]
                lnk = next((l for l in links if l.window_text() == event["text"]), None)
                if lnk and lnk.is_visible() and lnk.is_enabled():
                    lnk.invoke()
                    print(f"✓ Ссылка '{event['text']}' нажата")
                    success = True

            if success:
                break
            time.sleep(0.3)
        if not success:
            print(f"⚠️ Элемент '{event.get('text', event.get('name',''))}' не найден или не доступен")
    
    print("🏁 Воспроизведение завершено")

# ---------------- MAIN ----------------
mode = input("Выберите режим: (r) запись, (p) воспроизведение: ").strip().lower()
if mode=="p":
    autoplay()
else:
    print("❌ Используйте 'p' для воспроизведения записи")
