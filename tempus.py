import sys
import requests
import random
import string
import signal
import os
import threading
import time
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QListWidget, QListWidgetItem,
    QVBoxLayout, QHBoxLayout, QSystemTrayIcon, QStyle
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPainter, QColor, QIcon
import ctypes

API = "https://api.mail.tm"
ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

def generate_random_string(length=10):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


class MailTmClient:
    def __init__(self):
        self.email = None
        self.password = None
        self.token = None
        self.headers = {}

    def create_account(self):
        domains = requests.get(f"{API}/domains").json()["hydra:member"]
        domain = domains[0]["domain"]
        username = generate_random_string()
        email = f"{username}@{domain}"
        password = generate_random_string(12)

        account_payload = {"address": email, "password": password}
        account_resp = requests.post(f"{API}/accounts", json=account_payload)
        if account_resp.status_code != 201:
            raise Exception(f"Ошибка создания аккаунта: {account_resp.text}")

        token_resp = requests.post(f"{API}/token", json=account_payload)
        if token_resp.status_code != 200:
            raise Exception(f"Ошибка получения токена: {token_resp.text}")

        self.email = email
        self.password = password
        self.token = token_resp.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def get_messages(self):
        resp = requests.get(f"{API}/messages", headers=self.headers)
        if resp.status_code != 200:
            raise Exception(f"Ошибка получения сообщений: {resp.text}")
        return resp.json()["hydra:member"]

    def get_message(self, msg_id):
        resp = requests.get(f"{API}/messages/{msg_id}", headers=self.headers)
        if resp.status_code != 200:
            raise Exception(f"Ошибка получения письма: {resp.text}")
        return resp.json()


class MailFetcherThread(QThread):
    new_messages_signal = pyqtSignal(list)
    error_signal = pyqtSignal(str)

    def __init__(self, mail_client):
        super().__init__()
        self.mail_client = mail_client
        self.running = True
        self.seen_ids = set()

    def run(self):
        while self.running:
            try:
                messages = self.mail_client.get_messages()
                new_msgs = []
                for msg in messages:
                    if msg["id"] not in self.seen_ids:
                        self.seen_ids.add(msg["id"])
                        detail = self.mail_client.get_message(msg["id"])
                        new_msgs.append(detail)
                if new_msgs:
                    self.new_messages_signal.emit(new_msgs)
            except Exception as e:
                self.error_signal.emit(str(e))
            self.msleep(10000)  # 10 секунд

    def stop(self):
        self.running = False
        self.wait()


class BottomRightWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.Tool |
            Qt.WindowStaysOnBottomHint |
            Qt.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        self.setFixedSize(400, 430)

        # Получаем размеры экрана через ctypes
        user32 = ctypes.windll.user32
        screen_width = user32.GetSystemMetrics(0)
        screen_height = user32.GetSystemMetrics(1)
        offset_x, offset_y = 50, 50
        self.move(screen_width - self.width() - offset_x, screen_height - self.height() - offset_y)

        # UI элементы
        self.email_label = QLabel("Почта: (нет)", self)
        self.email_label.setStyleSheet("color: white;")
        self.email_label.setFont(QFont("Arial", 12, QFont.Bold))

        self.copy_button = QPushButton("Копировать почту", self)
        self.new_mail_button = QPushButton("Новая почта", self)

        self.mail_list = QListWidget(self)
        self.mail_list.setStyleSheet("""
            background-color: #222222;
            color: white;
            border: 1px solid #555555;
            border-radius: 8px;
        """)

        self.status_label = QLabel("", self)
        self.status_label.setStyleSheet("color: #ffaa00; font-weight: bold;")
        self.status_label.setAlignment(Qt.AlignCenter)

        top_layout = QHBoxLayout()
        top_layout.addWidget(self.email_label)
        top_layout.addWidget(self.copy_button)
        top_layout.addWidget(self.new_mail_button)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.mail_list)
        main_layout.addWidget(self.status_label)
        self.setLayout(main_layout)

        self.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 220);
                border-radius: 12px;
            }
        """)

        btn_style = """
            QPushButton {
                background-color: #444444;
                color: white;
                border: 1px solid #888888;
                border-radius: 8px;
                padding: 8px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #666666;
            }
            QPushButton:pressed {
                background-color: #222222;
            }
        """
        self.copy_button.setStyleSheet(btn_style)
        self.new_mail_button.setStyleSheet(btn_style)

        # Разрешаем кнопкам принимать мышь
        self.copy_button.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.new_mail_button.setAttribute(Qt.WA_TransparentForMouseEvents, False)

        # Таймер для очистки статуса — создаём ДО create_new_email
        self.status_clear_timer = QTimer()
        self.status_clear_timer.setSingleShot(True)
        self.status_clear_timer.timeout.connect(self.clear_status)

        self.app = QtWidgets.QApplication.instance()
        if self.app is None:
            self.app = QtWidgets.QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        # Трей иконка с базовой иконкой
        self.tray = QSystemTrayIcon(self)
        self.tray.setToolTip("Разминка")
        self.tray.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))

        def on_activated(reason):
            if reason == QtWidgets.QSystemTrayIcon.Trigger:
                self.app.quit()
                os.kill(os.getpid(), signal.SIGTERM)

        self.tray.activated.connect(on_activated)

        self.menu = QtWidgets.QMenu()
        self.exit_action = self.menu.addAction("Выход")
        self.exit_action.triggered.connect(self.app.quit)
        self.tray.setContextMenu(self.menu)
        self.tray.show()

        self.mail_client = MailTmClient()

        self.copy_button.clicked.connect(self.copy_email)
        self.new_mail_button.clicked.connect(self.create_new_email)

        self.create_new_email()

    def copy_email(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.mail_client.email or "")
        self.show_status(f"Почта скопирована: {self.mail_client.email}")

    def create_new_email(self):
        self.mail_list.clear()
        self.email_label.setText("Почта: ...")
        try:
            self.mail_client.create_account()
            self.email_label.setText(f"Почта: {self.mail_client.email}")

            if hasattr(self, "fetcher_thread"):
                self.fetcher_thread.stop()
            self.fetcher_thread = MailFetcherThread(self.mail_client)
            self.fetcher_thread.new_messages_signal.connect(self.add_messages)
            self.fetcher_thread.error_signal.connect(self.show_error)
            self.fetcher_thread.start()

            self.show_status("Создана новая почта")

            # Автоматически копируем почту
            self.copy_email()

        except Exception as e:
            self.show_error(str(e))
            self.email_label.setText("Почта: (ошибка)")

    def add_messages(self, messages):
        for msg in messages:
            subject = msg.get("subject", "(Без темы)")
            text = msg.get("text") or "(Нет текста)"
            item_text = f"Тема: {subject}\nТекст: {text}"
            print(item_text)
            item = QListWidgetItem(item_text)
            self.mail_list.addItem(item)

            # Показать уведомление Windows
            self.tray.showMessage(
                f"Новое письмо: {subject}",
                text[:200],
                QSystemTrayIcon.Information,
                5000
            )

            # Автоматически копируем код из письма, если он есть
            code = self.extract_code_from_message(subject)
            print(code)
            if code:
                clipboard = QApplication.clipboard()
                clipboard.setText(code)
                self.show_status(f"Код скопирован: {code}")

        self.show_status(f"Получено {len(messages)} новых писем")

    def extract_code_from_message(self, message_text):
        # Пример извлечения кода из текста сообщения
        # Здесь вы можете настроить логику в зависимости от формата ваших писем
        try:
            if "код OpenAI" in message_text:
                message_text = message_text.replace("Ваш код OpenAI","")
                message_text = message_text.replace(" ","")
                self.tray.showMessage(
                    f"""{message_text}""",
                    "Код найден",
                    QSystemTrayIcon.Information,
                    5000
                )
                return str(message_text)
            return None
        except Exception as e:
            print(e)
            return None

    def show_error(self, error_text):
        self.show_status(f"Ошибка: {error_text}", error=True)

    def show_status(self, message, error=False):
        color = "#ff5555" if error else "#ffaa00"
        self.status_label.setStyleSheet(f"color: {color}; font-weight: bold;")
        self.status_label.setText(message)
        self.status_clear_timer.start(5000)  # Очистить через 5 секунд

    def clear_status(self):
        self.status_label.setText("")

    def closeEvent(self, event):
        if hasattr(self, "fetcher_thread"):
            self.fetcher_thread.stop()
        event.accept()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(0, 0, 0, 220))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 12, 12)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BottomRightWidget()
    window.show()
    sys.exit(app.exec_())