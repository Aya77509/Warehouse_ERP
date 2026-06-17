from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from Kernel.auth_service import AuthService
from Kernel.entities import User


class LoginWindow(QWidget):
    """Login screen for user authentication."""

    def __init__(self, auth_service: AuthService, on_success_callback):
        super().__init__()
        self.auth_service = auth_service
        self.on_success_callback = on_success_callback
        self.setWindowTitle("Warehouse ERP - Login")
        self.setStyleSheet("background-color: #1e2530;")
        self._build_ui()
        self.showMaximized()

    def _build_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #2a3142;
                border-radius: 12px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setSpacing(18)

        title = QLabel("Warehouse ERP")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #ffffff;")

        subtitle = QLabel("Sign in to continue")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #9aa5b1; font-size: 13px;")

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setStyleSheet(self._input_style())

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet(self._input_style())
        self.password_input.returnPressed.connect(self._handle_login)

        login_btn = QPushButton("Login")
        login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        login_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border-radius: 6px;
                padding: 10px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)
        login_btn.clicked.connect(self._handle_login)

        hint = QLabel("Default: admin / admin123  |  user / user123")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("color: #6b7280; font-size: 11px;")

        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addSpacing(10)
        card_layout.addWidget(self.username_input)
        card_layout.addWidget(self.password_input)
        card_layout.addSpacing(6)
        card_layout.addWidget(login_btn)
        card_layout.addWidget(hint)

        card.setFixedWidth(420)

        outer_layout.addStretch()
        center_row = QHBoxLayout()
        center_row.addStretch()
        center_row.addWidget(card)
        center_row.addStretch()
        outer_layout.addLayout(center_row)
        outer_layout.addStretch()

    @staticmethod
    def _input_style() -> str:
        return """
            QLineEdit {
                background-color: #1e2530;
                color: #ffffff;
                border: 1px solid #3a4256;
                border-radius: 6px;
                padding: 10px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #3b82f6;
            }
        """

    def _handle_login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        try:
            user: User = self.auth_service.login(username, password)
            self.on_success_callback(user)
        except ValueError as e:
            QMessageBox.warning(self, "Login Failed", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Unexpected error: {e}")