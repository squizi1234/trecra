import json, time, random, string, pyperclip, re, requests,os
from pywinauto import Desktop
from pynput.keyboard import Controller, Key
import tester
import tkinter as tk
import win32gui
import win32con
import win32api
import threading
import tkinter as tk
import win32gui
import win32con
import builtins
curtain = None
def show_keyboard_safe_curtain(alpha=180):
	root = tk.Tk()
	root.overrideredirect(True)
	root.configure(bg="black")

	root.attributes("-topmost", True)
	root.attributes("-alpha", alpha / 255)

	root.geometry("1x1+0+0")
	root.withdraw()

	# Верхний текст
	status_var = tk.StringVar(value="⏳ Ожидание...")
	label_top = tk.Label(
		root,
		textvariable=status_var,
		fg="white",
		bg="black",
		font=("Segoe UI", 20, "bold")
	)
	label_top.place(relx=0.5, rely=0.45, anchor="center")  # чуть выше центра

	# Нижний текст с символами запрета
	status_var_bottom = tk.StringVar(value="🚫🖱️  🚫⌨️")
	label_bottom = tk.Label(
		root,
		textvariable=status_var_bottom,
		fg="white",
		bg="black",
		font=("Segoe UI", 40, "bold")  # можно сделать крупнее
	)
	label_bottom.place(relx=0.5, rely=0.55, anchor="center")  # чуть ниже центра

	root.update_idletasks()

	hwnd_overlay = win32gui.GetParent(root.winfo_id())
	style = win32gui.GetWindowLong(hwnd_overlay, win32con.GWL_EXSTYLE)
	style |= win32con.WS_EX_NOACTIVATE
	win32gui.SetWindowLong(hwnd_overlay, win32con.GWL_EXSTYLE, style)

	# Сохраняем переменные для дальнейшего использования
	root.status_var = status_var
	root.status_var_bottom = status_var_bottom

	return root


def follow_window(curtain, get_hwnd_func, interval=300):
	def tick():
		hwnd = get_hwnd_func()

		# ❌ окна нет — скрываем занавес
		if not hwnd or not win32gui.IsWindow(hwnd):
			curtain.withdraw()
			curtain.after(interval, tick)
			return

		# если свернуто — скрываем
		if win32gui.IsIconic(hwnd):
			curtain.withdraw()
			curtain.after(interval, tick)
			return

		try:
			x1, y1, x2, y2 = win32gui.GetWindowRect(hwnd)

			# если окно слишком маленькое / странное
			if x2 - x1 < 50 or y2 - y1 < 50:
				curtain.withdraw()
			else:
				curtain.deiconify()
				curtain.geometry(f"{x2-x1}x{y2-y1}+{x1}+{y1}")

		except:
			curtain.withdraw()

		curtain.after(interval, tick)

	tick()
def find_edge_hwnd():
	try:
		windows = Desktop(backend="uia").windows()
		for w in windows:
			if "InPrivate" in w.window_text():
				return w.handle
	except:
		pass
	return None

def start_curtain_system():
	global curtain
	curtain = show_keyboard_safe_curtain()

	# запускаем слежение
	follow_window(curtain, find_edge_hwnd)

	curtain.mainloop()



RECORD_FILE = "recordinggff.json"
SAVE_FILE = "result.txt"
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
def save_clipboard_text():

	text = pyperclip.paste().strip()
	apitru = tester.testerapi(api=[text])
	if apitru:
		if not text:
			return

		with open(SAVE_FILE, "a", encoding="utf-8") as f:
			f.write(f"\n{text}")


		print("💾 сохранено:", text)
	else:
		print("❌ ключ не рабочий, не сохраняем")
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

def print(text, *args):
	global curtain,SAVE_FILE

	if args:
		text = text.format(*args)

	builtins.print(text)
	count = 0
	with open(SAVE_FILE, "r", encoding="utf-8") as f:
		for line in f:
			count += 1
	if curtain:
		try:
			curtain.after(0, lambda t=text: (
				curtain.status_var.set(f"{t}"),
				curtain.status_var_bottom.set(f"🚫🖱️ {count} 🚫⌨️")
			))

		except:
			pass


# ---------------- Autoplay ----------------
def autoplay():
	try:
		with open(RECORD_FILE, "r", encoding="utf-8") as f:
			events = json.load(f)
	except FileNotFoundError:
		print(f"❌ {RECORD_FILE} не найден!")
		return

	print("🚀 Старт через 5 секунд...")
	#time.sleep(1)
	
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
			edge_window = edge_windows[0]
			hwnd = edge_window.handle
			# Запускаем занавес в отдельном потоке



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
if mode == "p":
	# Запускаем overlay


	# Запускаем автоплей в другом потоке
	def start_autoplay_loop():
		while True:
			os.system("start msedge --inprivate")
			autoplay()
			save_clipboard_text()

#threading.Thread(target=start_autoplay_loop, daemon=True).start()


	#threading.Thread(target=loop_autoplay, daemon=True).start()

	curtain = show_keyboard_safe_curtain()
	follow_window(curtain, find_edge_hwnd)

	# Запускаем autoplay в отдельном потоке
	threading.Thread(target=start_autoplay_loop, daemon=True).start()

	# GUI главный поток
	curtain.mainloop()


else:
	print("❌ Используйте 'p' для воспроизведения записи")
