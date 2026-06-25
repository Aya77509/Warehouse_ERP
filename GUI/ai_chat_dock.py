import re
from PyQt6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QFrame, QComboBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from GUI.theme import (
    BG, SURFACE, SURFACE_3, BORDER, TEXT_BODY, TEXT_MUTED,
    PRIMARY, RADIUS_MD, FS_BODY, FS_SMALL,
    Icons, qicon, primary_button, input_style
)
from Kernel.ai_assistant import AIAssistantService

# Simple Markdown to HTML regex parser for QLabel rendering
def markdown_to_html(text: str) -> str:
    # 1. Escape HTML entities
    html = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    
    # 2. Bold: **text** -> <b>text</b>
    html = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", html)
    
    # 3. Italics: *text* -> <i>text</i>
    html = re.sub(r"\*(.*?)\*", r"<i>\1</i>", html)
    
    # 4. Monospace/Code: `code` -> <code style="...">code</code>
    html = re.sub(
        r"`([^`\n]+)`",
        r"<code style='background-color: rgba(0,0,0,0.06); color: #c7254e; font-family: Courier New, monospace; padding: 1px 3px; border-radius: 3px;'>\1</code>",
        html
    )
    
    # 5. Multiline Code Blocks: ```code``` -> <pre>code</pre>
    html = re.sub(
        r"```([\s\S]*?)```",
        r"<pre style='background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 4px; padding: 8px; font-family: Courier New, monospace; font-size: 12px;'>\1</pre>",
        html
    )
    
    # 6. Headers
    html = re.sub(r"^###\s+(.*?)$", r"<h4 style='margin: 4px 0; color: #0f172a;'>\1</h4>", html, flags=re.MULTILINE)
    html = re.sub(r"^##\s+(.*?)$", r"<h3 style='margin: 6px 0; color: #0f172a;'>\1</h3>", html, flags=re.MULTILINE)
    html = re.sub(r"^#\s+(.*?)$", r"<h2 style='margin: 8px 0; color: #0f172a;'>\1</h2>", html, flags=re.MULTILINE)
    
    # 7. List Items
    html = re.sub(r"^\s*[-*]\s+(.*?)$", r"• \1", html, flags=re.MULTILINE)
    
    # 8. Newlines to <br> (only outside pre tags to preserve formatting)
    parts = html.split("<pre")
    new_parts = [parts[0].replace("\n", "<br>")]
    for part in parts[1:]:
        subparts = part.split("</pre>")
        new_text = subparts[1].replace("\n", "<br>") if len(subparts) > 1 else ""
        new_parts.append("<pre" + subparts[0] + "</pre>" + new_text)
    
    html = "".join(new_parts)
    return html


class ChatBubble(QFrame):
    """Visual speech bubble representing a single message in the chat."""
    
    def __init__(self, text: str, is_user: bool = False, parent=None):
        super().__init__(parent)
        self.is_user = is_user
        self._init_ui(text)
        
    def _init_ui(self, text: str):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 3, 4, 3)
        layout.setSpacing(0)
        
        self.content_frame = QFrame()
        self.content_frame.setObjectName("ContentFrame")
        
        # Format the text
        formatted_html = markdown_to_html(text)
        
        self.label = QLabel(formatted_html)
        self.label.setWordWrap(True)
        self.label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        
        content_layout = QVBoxLayout(self.content_frame)
        content_layout.setContentsMargins(12, 9, 12, 9)
        content_layout.addWidget(self.label)
        
        # Alignments & Styles
        if self.is_user:
            bg_color = PRIMARY
            fg_color = "#ffffff"
            border_radius_qss = f"border-radius: {RADIUS_MD}px; border-bottom-right-radius: 2px;"
            self.label.setStyleSheet(f"color: {fg_color}; font-size: {FS_BODY}px; background: transparent;")
        else:
            bg_color = SURFACE_3
            fg_color = TEXT_BODY
            border_radius_qss = f"border-radius: {RADIUS_MD}px; border-bottom-left-radius: 2px; border: 1px solid {BORDER};"
            self.label.setStyleSheet(f"color: {fg_color}; font-size: {FS_BODY}px; background: transparent;")
            
        self.content_frame.setStyleSheet(f"""
            QFrame#ContentFrame {{
                background-color: {bg_color};
                {border_radius_qss}
            }}
        """)
        
        if self.is_user:
            layout.addStretch()
            layout.addWidget(self.content_frame)
        else:
            layout.addWidget(self.content_frame)
            layout.addStretch()


class AiQueryWorker(QThread):
    """Asynchronous worker thread to prevent the GUI from freezing during LLM calls."""
    response_received = pyqtSignal(str)
    
    def __init__(self, ai_service: AIAssistantService, user_msg: str, history: list[dict], model: str):
        super().__init__()
        self.ai_service = ai_service
        self.user_msg = user_msg
        self.history = history
        self.model = model
        
    def run(self):
        # Update the model in the service before querying
        self.ai_service.model = self.model
        try:
            res = self.ai_service.query(self.user_msg, self.history)
            self.response_received.emit(res)
        except Exception as e:
            self.response_received.emit(f"⚠️ Error: {str(e)}")


class AiChatDock(QDockWidget):
    """Dock widget showing the AI Assistant chat interface."""
    
    def __init__(self, product_service, inventory_service, supplier_service, report_service, parent=None):
        super().__init__("🤖 AI Assistant", parent)
        self.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable | 
            QDockWidget.DockWidgetFeature.DockWidgetClosable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        
        self.product_service = product_service
        self.inventory_service = inventory_service
        self.supplier_service = supplier_service
        self.report_service = report_service
        self.category_service = getattr(parent, "category_service", None)
        
        # Initialize AI Service
        self.ai_service = AIAssistantService(
            product_service=self.product_service,
            inventory_service=self.inventory_service,
            supplier_service=self.supplier_service,
            category_service=self.category_service,
            model="llama3.2"
        )
        
        self.chat_history = []  # List of {"role": "user/assistant", "content": "..."}
        self.worker = None
        
        self._init_ui()
        
    def _init_ui(self):
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet(f"background-color: {BG};")
        self.setWidget(self.content_widget)
        
        main_layout = QVBoxLayout(self.content_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 1. Header Toolbar
        header_frame = QFrame()
        header_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {SURFACE};
                border-bottom: 1px solid {BORDER};
            }}
        """)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(12, 8, 12, 8)
        header_layout.setSpacing(8)
        
        # Model Selector
        self.model_combo = QComboBox()
        self.model_combo.addItems(["llama3.2", "llama3.2:1b", "qwen2.5:1.5b", "qwen2.5:0.5b"])
        self.model_combo.setStyleSheet(input_style())
        self.model_combo.setToolTip("Select the local LLM running in Ollama")
        
        # Clear Chat button
        clear_btn = QPushButton()
        clear_btn.setIcon(qicon(Icons.DELETE))
        clear_btn.setIconSize(QSize(16, 16))
        clear_btn.setToolTip("Clear conversation history")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; border: 1px solid {BORDER}; border-radius: {RADIUS_MD}px; padding: 6px;
            }}
            QPushButton:hover {{
                background: {SURFACE_3};
            }}
        """)
        clear_btn.clicked.connect(self.clear_history)
        
        header_layout.addWidget(QLabel("<b>Model:</b>"), 0, Qt.AlignmentFlag.AlignVCenter)
        header_layout.addWidget(self.model_combo, 1, Qt.AlignmentFlag.AlignVCenter)
        header_layout.addWidget(clear_btn, 0, Qt.AlignmentFlag.AlignVCenter)
        
        main_layout.addWidget(header_frame)
        
        # 2. Chat Message Display Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet(f"QScrollArea {{ border: none; background-color: {BG}; }}")
        
        self.chat_container = QWidget()
        self.chat_container.setStyleSheet(f"background-color: {BG};")
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(12, 12, 12, 12)
        self.chat_layout.setSpacing(10)
        self.chat_layout.addStretch(1)  # Keeps messages pushed to the top
        
        self.scroll_area.setWidget(self.chat_container)
        main_layout.addWidget(self.scroll_area, 1)
        
        # 3. Typing/Loading Indicator
        self.loading_label = QLabel("🤖 AI is thinking...")
        self.loading_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: {FS_SMALL}px; padding: 4px 16px;")
        self.loading_label.setVisible(False)
        main_layout.addWidget(self.loading_label)
        
        # 4. Input Bar
        input_frame = QFrame()
        input_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {SURFACE};
                border-top: 1px solid {BORDER};
            }}
        """)
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(12, 10, 12, 10)
        input_layout.setSpacing(8)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask a question about stock or inventory...")
        self.input_field.setStyleSheet(input_style())
        self.input_field.returnPressed.connect(self.send_message)
        
        send_btn = primary_button("Send", variant="primary")
        send_btn.clicked.connect(self.send_message)
        
        input_layout.addWidget(self.input_field, 1)
        input_layout.addWidget(send_btn)
        
        main_layout.addWidget(input_frame)
        
        # Add welcome message
        self.add_message(
            "Hello! I am your Warehouse AI Assistant. I can answer questions about your inventory, such as:\n"
            "- *\"How much stock do we have for [product]?\"*\n"
            "- *\"Which products are low in stock?\"*\n"
            "- *\"Who supplies [product]?\"*\n"
            "- *\"What products expire soon?\"*\n"
            "- *\"What are the recent movements?\"*",
            is_user=False
        )

    def add_message(self, text: str, is_user: bool):
        """Creates and appends a ChatBubble to the chat interface."""
        bubble = ChatBubble(text, is_user=is_user)
        # Insert the bubble right before the stretch spacer
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)
        
        # Scroll to bottom
        self.scroll_to_bottom()

    def scroll_to_bottom(self):
        """Scrolls the chat display to the very bottom."""
        # Defer to allow the layout to compute new sizes
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )
        # Using a timer call or repeating can guarantee it scrolls to the absolute end
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(50, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))

    def send_message(self):
        """Handles sending the user message and initiating the AI response worker."""
        # Don't send if already thinking
        if self.worker and self.worker.isRunning():
            return
            
        text = self.input_field.text().strip()
        if not text:
            return
            
        # Add user message to UI
        self.add_message(text, is_user=True)
        self.input_field.clear()
        
        # Show loading indicator
        self.loading_label.setVisible(True)
        self.scroll_to_bottom()
        
        # Create and start the worker thread
        selected_model = self.model_combo.currentText()
        # Convert chat history to Ollama format: [{"role": "user/assistant", "content": "..."}]
        # Let's limit the history to the last 10 messages to keep the prompt clean and fast
        ollama_history = self.chat_history[-10:]
        
        self.worker = AiQueryWorker(self.ai_service, text, ollama_history, selected_model)
        self.worker.response_received.connect(lambda res: self.handle_ai_response(text, res))
        self.worker.start()

    def handle_ai_response(self, user_msg: str, response: str):
        """Handles the response received from the worker thread."""
        self.loading_label.setVisible(False)
        self.add_message(response, is_user=False)
        
        # Save to history
        self.chat_history.append({"role": "user", "content": user_msg})
        self.chat_history.append({"role": "assistant", "content": response})

    def clear_history(self):
        """Clears all conversation items from the UI and history tracker."""
        self.chat_history.clear()
        
        # Remove widgets except the last stretch spacer
        while self.chat_layout.count() > 1:
            item = self.chat_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
                
        # Re-add welcome message
        self.add_message(
            "Hello! I am your Warehouse AI Assistant. I can answer questions about your inventory, such as:\n"
            "- *\"How much stock do we have for [product]?\"*\n"
            "- *\"Which products are low in stock?\"*\n"
            "- *\"Who supplies [product]?\"*\n"
            "- *\"What products expire soon?\"*\n"
            "- *\"What are the recent movements?\"*",
            is_user=False
        )
