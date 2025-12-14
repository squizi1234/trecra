from pynput.mouse import Controller as MouseController, Button
from pynput.keyboard import Controller as KeyboardController, Key
import pyperclip
import json
import time
import re
import requests
import random
import string

# ================== MAIL.TM ==================
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
API = "https://api.mail.tm"

def rand_string(n=10):
	return ''.join(random.choices(string.ascii_lowercase + string.digits, k=n))

class MailTM:
	def __init__(self):
		self.email = None
		self.password = None
		self.token = None
		self.headers = {}

	def create_account(self):
		domains = requests.get(f"{API}/domains").json()["hydra:member"]
		domain = domains[0]["domain"]

		self.email = f"{rand_string()}@{domain}"
		self.password = rand_string(12)

		r = requests.post(
			f"{API}/accounts",
			json={"address": self.email, "password": self.password}
		)
		if r.status_code != 201:
			raise Exception("Ошибка создания почты")

		r = requests.post(
			f"{API}/token",
			json={"address": self.email, "password": self.password}
		)
		if r.status_code != 200:
			raise Exception("Ошибка токена")

		self.token = r.json()["token"]
		self.headers = {"Authorization": f"Bearer {self.token}"}

	def wait_for_code(self, timeout=300):
		seen = set()
		start = time.time()

		while time.time() - start < timeout:
			r = requests.get(f"{API}/messages", headers=self.headers)
			messages = r.json()["hydra:member"]

			for msg in messages:
				if msg["id"] in seen:
					continue
				seen.add(msg["id"])

				full = requests.get(
					f"{API}/messages/{msg['id']}",
					headers=self.headers
				).json()
				subject = full.get("subject", "(Без темы)")
				text = (full.get("text") or "") + " " + (full.get("subject") or "")
				match = re.search(r"\b[A-Z0-9]{6}\b", text.upper())
				#if match:
				return extract_code_from_message(subject)

			time.sleep(5)

		raise TimeoutError("Код не пришёл")

# ================== AUTOPLAYER ==================

mouse = MouseController()
keyboard = KeyboardController()

def is_code_or_email(text, expected_type):
	text = text.strip()
	if expected_type == "email":
		return re.match(r"[^@ \t\r\n]+@[^@ \t\r\n]+\.[^@ \t\r\n]+", text)
	elif expected_type == "code":
		return len(text) == 6 and text.isalnum()
	return False

def wait_or_use_clipboard(expected_type, timeout=300):
	start = time.time()
	initial = pyperclip.paste().strip()

	if is_code_or_email(initial, expected_type):
		return initial

	while time.time() - start < timeout:
		cur = pyperclip.paste().strip()
		if cur != initial and is_code_or_email(cur, expected_type):
			return cur
		time.sleep(0.5)

	raise TimeoutError("Буфер не дождался")

def paste_clipboard():
	keyboard.press(Key.ctrl)
	keyboard.press('v')
	keyboard.release('v')
	keyboard.release(Key.ctrl)

# ================== LOAD EVENTS ==================

with open("recording.json", "r", encoding="utf-8") as f:
	events = json.load(f)

print("Старт через 5 секунд...")
time.sleep(5)

# ================== MAIN LOOP ==================

while True:
	print("🔁 Новый цикл → создаём почту")

	mail = MailTM()
	mail.create_account()

	print("📧 Почта:", mail.email)
	pyperclip.copy(mail.email)

	start_time = events[0]["time"]
	print("▶️ Воспроизведение началось")

	for event in events:
		delay = event["time"] - start_time
		time.sleep(delay)
		start_time = event["time"]

		if event["type"] == "click":
			mouse.position = (event["x"], event["y"])
			mouse.click(Button.left if "left" in event["button"] else Button.right)

		elif event["type"] == "key_combo":
			combo = event["combo"].split('+')
			pressed = []

			for k in combo:
				k = k.strip()
				if k.startswith("Key."):
					key_obj = getattr(Key, k[4:])
				else:
					key_obj = k

				keyboard.press(key_obj)
				pressed.append(key_obj)

			for k in reversed(pressed):
				keyboard.release(k)

		elif event["type"] == "wait_clipboard":
			expected = event["data_type"]

			if expected == "email":
				paste_clipboard()

			elif expected == "code":
				print("📬 Ждём письмо с кодом...")
				code = mail.wait_for_code()
				print("🔢 Код:", code)
				pyperclip.copy(code)
				paste_clipboard()

	print("🏁 Цикл завершён\n")
