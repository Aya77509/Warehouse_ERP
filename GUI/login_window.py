from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont

from Kernel.auth_service import AuthService
from Kernel.entities import User
from GUI.theme import (
    BG, SURFACE, BORDER, TEXT, TEXT_MUTED, PRIMARY,
    FS_SMALL, FS_MICRO, RADIUS_XL,
    Icons, qicon, primary_button, input_style, card_frame,
)




class LoginWindow(QWidget):
    def __init__(self, auth_service: AuthService, on_success_callback):
        super().__init__()
        self.auth_service = auth_service
        self.on_success_callback = on_success_callback
        self.setWindowTitle("Warehouse  — Sign In")
        self.setStyleSheet(f"background-color: {BG};")
        self._build_ui()
        self.showMaximized()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        card = card_frame(padding=40)
        card.setFixedWidth(440)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setSpacing(14)

        # Brand
        logo = QLabel()
        #logo.setPixmap(qicon(Icons.BRAND).pixmap(QSize(52, 52)))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("background: transparent;")

        title = QLabel("Warehouse ERP")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Helvetica", 22, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {TEXT}; background: transparent;")

        subtitle = QLabel("Sign in to your workspace")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(f"color: {TEXT_MUTED}; font-size: {FS_SMALL}px; background: transparent;")

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setStyleSheet(input_style())

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet(input_style())
        self.password_input.returnPressed.connect(self._handle_login)

        login_btn = primary_button("Sign in", Icons.LOGIN, variant="primary")
        login_btn.setMinimumHeight(42)
        login_btn.clicked.connect(self._handle_login)

        hint = QLabel("Demo accounts: admin / admin123 ")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet(f"color: {TEXT_MUTED}; font-size: {FS_MICRO}px; background: transparent;")

        card_layout.addWidget(logo)
        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addSpacing(12)
        card_layout.addWidget(self.username_input)
        card_layout.addWidget(self.password_input)
        card_layout.addSpacing(4)
        card_layout.addWidget(login_btn)
        card_layout.addWidget(hint)

        outer.addStretch()
        row = QHBoxLayout(); row.addStretch(); row.addWidget(card); row.addStretch()
        outer.addLayout(row)
        outer.addStretch()

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
