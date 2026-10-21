
from PySide6.QtCore import QThread, Signal, Qt, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizeGrip,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .brain import UltronBrain
from .config import settings
from .memory import ChatMemory
from .voice import VoiceEngine


class TaskThread(QThread):
    succeeded = Signal(str)
    failed = Signal(str)

    def __init__(self, fn):
        super().__init__()
        self.fn = fn

    def run(self):
        try:
            result = self.fn()
            self.succeeded.emit(str(result))
        except Exception as exc:
            self.failed.emit(str(exc))


class UltronWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("ULTRON | Personal AI")
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._drag_position = None
        self._expanded = False
        self._normal_geometry = None

        self.memory = ChatMemory(settings.db_path)
        self.voice = VoiceEngine(settings.vosk_model_path)

        self.busy = False
        self.task = None

        self._build_ui()
        self._position_floating_window()
        self._load_history()
        # Run after Qt has completed the initial layout pass; otherwise the
        # scroll area can report its old viewport size and preserve a blank gap.
        QTimer.singleShot(0, self._adjust_compact_height)

    # --------------------------------------------------
    # USER INTERFACE
    # --------------------------------------------------

    def _position_floating_window(self):
        """Place the translucent assistant in the upper-right corner."""
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            self.resize(540, 300)
            return
        area = screen.availableGeometry()
        # Start compact in the top-right, like the supplied reference.
        # A little wider than 1/3 on common screens so the header controls
        # have room and never overlap the ULTRON title.
        width = max(540, int(area.width() / 3))
        # Start compact; the window grows only as messages need room.
        height = 220
        width = min(width, area.width() - 28)
        height = min(height, area.height() - 60)
        self.setMinimumSize(520, 220)
        self.resize(width, height)
        margin = 8
        top_offset = 76  # approximately 2 cm lower on a typical display
        self.move(
            area.x() + area.width() - width - margin,
            min(area.y() + top_offset, area.y() + area.height() - height - margin),
        )


    def toggle_expand(self):
        """Expand the widget while keeping it anchored to the top-right."""
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            return
        area = screen.availableGeometry()
        margin = 8
        if not self._expanded:
            self._normal_geometry = self.geometry()
            width = min(max(760, int(area.width() * 0.48)), area.width() - 2 * margin)
            height = min(max(520, int(area.height() * 0.72)), area.height() - 2 * margin)
            self.resize(width, height)
            self.move(
                area.x() + area.width() - width - margin,
                min(area.y() + 76, area.y() + area.height() - height - margin),
            )
            self._expanded = True
        else:
            if self._normal_geometry is not None:
                self.setGeometry(self._normal_geometry)
            else:
                self._position_floating_window()
            self._expanded = False
            QTimer.singleShot(0, self._adjust_compact_height)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self._expanded and hasattr(self, "scroll"):
            QTimer.singleShot(0, self._adjust_compact_height)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_position is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_position = None
        super().mouseReleaseEvent(event)

    def _build_ui(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background: transparent;
                color: #f3f7ff;
                font-size: 13px;
            }
            QWidget#root {
                background: rgba(12, 28, 52, 28);
                border: none;
                border-radius: 0px;
            }
            QLabel#brand {
                color: #f5fbff;
                font-size: 23px;
                font-weight: 800;
                letter-spacing: 3px;
                background: transparent;
            }
            QLabel#sub, QLabel#status {
                color: rgba(230, 242, 255, 205);
                background: transparent;
                font-size: 10px;
            }
            QPushButton {
                background: rgba(90, 160, 220, 45);
                color: #f4f9ff;
                border: 1px solid rgba(180, 225, 255, 105);
                border-radius: 9px;
                padding: 6px 9px;
            }
            QPushButton:hover { background: rgba(90, 175, 245, 95); }
            QPushButton#send {
                background: rgba(0, 125, 255, 115);
                border: 1px solid rgba(170, 225, 255, 150);
                font-weight: bold;
            }
            QLineEdit, QComboBox {
                background: rgba(110, 165, 215, 40);
                color: #ffffff;
                border: 1px solid rgba(180, 225, 255, 120);
                border-radius: 12px;
                padding: 9px;
            }
            QLineEdit::placeholder { color: rgba(235, 245, 255, 175); }
            QComboBox QAbstractItemView {
                background: #142b48;
                color: white;
                selection-background-color: #1769aa;
            }
            QScrollArea, QScrollArea > QWidget, QScrollArea > QWidget > QWidget {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 6px;
                margin: 2px;
            }
            QScrollBar::handle:vertical {
                background: rgba(190, 225, 255, 105);
                border-radius: 3px;
                min-height: 22px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)

        root = QWidget()
        root.setObjectName("root")
        outer = QVBoxLayout(root)
        outer.setContentsMargins(14, 12, 14, 12)
        outer.setSpacing(8)

        header = QHBoxLayout()
        header.setSpacing(5)
        titles = QVBoxLayout()
        titles.setSpacing(1)
        brand = QLabel("ULTRON")
        brand.setObjectName("brand")
        subtitle = QLabel("YOUR PERSONAL AI ASSISTANT")
        subtitle.setObjectName("sub")
        titles.addWidget(brand)
        titles.addWidget(subtitle)
        title_widget = QWidget()
        title_widget.setStyleSheet("background: transparent;")
        title_widget.setLayout(titles)
        title_widget.setMinimumWidth(145)
        header.addWidget(title_widget, 1)

        self.provider = QComboBox()
        self.provider.addItems(["Local", "Cloud"])
        self.provider.setCurrentIndex(0 if settings.provider == "local" else 1)
        self.provider.setToolTip("Choose AI provider")
        self.provider.setFixedWidth(76)
        self.provider.setMinimumContentsLength(5)
        header.addWidget(self.provider)

        clear_btn = QPushButton("Clear")
        clear_btn.setFixedWidth(48)
        clear_btn.setToolTip("Clear conversation history")
        clear_btn.clicked.connect(self.clear_chat)
        header.addWidget(clear_btn)

        minimize_btn = QPushButton("—")
        minimize_btn.setFixedWidth(27)
        minimize_btn.setToolTip("Minimize ULTRON")
        minimize_btn.clicked.connect(self.showMinimized)
        header.addWidget(minimize_btn)

        expand_btn = QPushButton("□")
        expand_btn.setFixedWidth(27)
        expand_btn.setToolTip("Expand / restore ULTRON")
        expand_btn.clicked.connect(self.toggle_expand)
        header.addWidget(expand_btn)

        close_btn = QPushButton("×")
        close_btn.setFixedWidth(27)
        close_btn.setToolTip("Close ULTRON")
        close_btn.clicked.connect(self.close)
        header.addWidget(close_btn)
        outer.addLayout(header)

        self.status = QLabel("SYSTEM READY  •  DRAG WINDOW TO MOVE")
        self.status.setObjectName("status")
        self.status.setWordWrap(True)
        outer.addWidget(self.status)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.chat_body = QWidget()
        self.chat_body.setStyleSheet("background: transparent;")
        self.chat_layout = QVBoxLayout(self.chat_body)
        self.chat_layout.setContentsMargins(2, 2, 5, 2)
        self.chat_layout.setSpacing(5)
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.chat_body)
        # The chat area should use only the space needed by its messages in
        # compact mode. _adjust_compact_height() grows the window as needed.
        outer.addWidget(self.scroll, 0)
        self.scroll.setMinimumHeight(0)
        self.scroll.setMaximumHeight(0)
        self.scroll.setVisible(False)

        composer = QHBoxLayout()
        composer.setSpacing(6)
        self.input = QLineEdit()
        self.input.setPlaceholderText("Type a message…")
        self.input.returnPressed.connect(self.send_message)
        self.mic_btn = QPushButton("🎙")
        self.mic_btn.setFixedWidth(38)
        self.mic_btn.setToolTip("Listen")
        self.mic_btn.clicked.connect(self.listen)
        self.send_btn = QPushButton("➤")
        self.send_btn.setObjectName("send")
        self.send_btn.setFixedWidth(42)
        self.send_btn.setToolTip("Send message")
        self.send_btn.clicked.connect(self.send_message)
        composer.addWidget(self.input, 1)
        composer.addWidget(self.mic_btn)
        composer.addWidget(self.send_btn)
        outer.addLayout(composer)

        # QSizeGrip enables drag-resizing even though the window is frameless.
        grip_row = QHBoxLayout()
        grip_row.setContentsMargins(0, 0, 0, 0)
        grip_row.addStretch(1)
        self.size_grip = QSizeGrip(root)
        self.size_grip.setFixedSize(16, 16)
        self.size_grip.setStyleSheet("background: transparent;")
        grip_row.addWidget(self.size_grip, 0, Qt.AlignmentFlag.AlignRight)
        outer.addLayout(grip_row)

        self.setCentralWidget(root)

    # --------------------------------------------------
    # CHAT DISPLAY
    # --------------------------------------------------

    def _load_history(self):
        for item in self.memory.recent(30):
            who = (
                "You"
                if item["role"] == "user"
                else "ULTRON"
            )
            self._add_bubble(
                who,
                item["content"],
                item["role"],
            )

    def _add_bubble(self, who, content, role):
        # Escape user/model text before displaying rich text.
        safe_content = (
            str(content)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br>")
        )

        safe_who = (
            str(who)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

        label = QLabel(
            f"<b>{safe_who}</b><br>{safe_content}"
        )

        label.setWordWrap(True)
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )

        if role == "assistant":
            bubble_style = """
                background: rgba(20, 95, 155, 48);
                border: none;
                color: #f4faff;
            """
        elif role == "user":
            bubble_style = """
                background: rgba(90, 150, 205, 38);
                border: none;
                color: #ffffff;
            """
        else:
            bubble_style = """
                background: rgba(100, 100, 120, 42);
                border: none;
                color: #ffffff;
            """

        label.setStyleSheet(
            f"""
            QLabel {{
                {bubble_style}
                border-radius: 0px;
                padding: 9px;
                margin: 2px 0;
            }}
            """
        )

        self.chat_layout.addWidget(label)
        label.updateGeometry()
        self.chat_body.adjustSize()
        QTimer.singleShot(0, self._adjust_compact_height)

        self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()
        )

    def _adjust_compact_height(self):
        """Keep compact mode tightly fitted to messages; scroll only when needed."""
        if self._expanded or not hasattr(self, "scroll"):
            return

        screen = QGuiApplication.primaryScreen()
        if screen is None:
            return
        area = screen.availableGeometry()

        # Let Qt finish laying out wrapped labels before measuring them.
        self.chat_body.adjustSize()
        self.chat_layout.activate()
        count = self.chat_layout.count()
        if count:
            # Measure bubbles at the current chat width. This avoids relying on
            # the scroll area's stale viewport size, which caused the large gap.
            available_width = max(200, self.width() - 48)
            total_bubble_height = 0
            for i in range(count):
                item = self.chat_layout.itemAt(i)
                widget = item.widget() if item else None
                if widget is None:
                    continue
                # Force a real width before measuring wrapped rich text. QLabel
                # may not report heightForWidth reliably for rich-text bubbles,
                # so use the resulting size hint and ensure the actual widget
                # is at least that tall.
                widget.setFixedWidth(available_width)
                widget.adjustSize()
                hint = widget.sizeHint()
                bubble_height = max(widget.height(), hint.height())
                widget.setMinimumHeight(bubble_height)
                total_bubble_height += bubble_height
            margins = self.chat_layout.contentsMargins()
            content_height = (
                total_bubble_height + margins.top() + margins.bottom()
                + max(0, count - 1) * self.chat_layout.spacing() + 8
            )
        else:
            content_height = 0

        # Reserve enough room for header, status, composer, resize grip,
        # outer margins, and layout spacing. The old 158px estimate was too
        # small, so chat bubbles could extend behind the composer.
        fixed_height = 224
        min_height = 220
        max_height = min(int(area.height() * 0.68), area.height() - 24)
        desired_chat_height = min(content_height, max(0, max_height - fixed_height))
        target_height = max(min_height, fixed_height + desired_chat_height)

        # Make the compact window about 2 cm shorter from the bottom.
        # Keep the header and composer intact; the chat viewport becomes
        # shorter and scrolls when the full conversation no longer fits.
        bottom_trim_px = 76
        if count and target_height > min_height + bottom_trim_px:
            target_height -= bottom_trim_px
            desired_chat_height = max(0, target_height - fixed_height)

        self.scroll.setVisible(count > 0)
        if count:
            # Fixed viewport height prevents the layout from stretching into a gap.
            self.scroll.setMinimumHeight(desired_chat_height)
            self.scroll.setMaximumHeight(desired_chat_height)
            self.chat_body.setMinimumHeight(content_height)
            self.chat_body.setMaximumHeight(max(content_height, desired_chat_height))
        else:
            self.scroll.setMinimumHeight(0)
            self.scroll.setMaximumHeight(0)
            self.chat_body.setMinimumHeight(0)
            self.chat_body.setMaximumHeight(0)

        if abs(self.height() - target_height) > 2:
            right = area.x() + area.width() - self.width() - 8
            self.resize(self.width(), target_height)
            self.move(right, min(area.y() + 76, area.y() + area.height() - target_height - 8))

        self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()
        )

    def _set_busy(self, busy, status):
        self.busy = busy

        self.send_btn.setEnabled(not busy)
        self.mic_btn.setEnabled(not busy)
        self.input.setEnabled(not busy)

        self.status.setText(status)

    # --------------------------------------------------
    # PERSISTENT MEMORY COMMANDS
    # --------------------------------------------------

    def _handle_memory_command(self, text):
        """
        Handle explicit memory commands locally.
        Return True when the command was handled.
        """

        command = text.strip()
        lowered = command.lower()

        # Save a fact:
        # Remember this: My project code is PROJECT-5831
        prefix = "remember this:"

        if lowered.startswith(prefix):
            fact = command[len(prefix):].strip()

            if not fact:
                response = "Please provide a fact to remember."
            else:
                self.memory.remember(fact)
                response = (
                    "Saved to persistent memory:\n"
                    f"{fact}"
                )

            self._show_memory_response(command, response)
            return True

        # List saved facts
        if lowered in {
            "show my saved memories",
            "show saved memories",
            "list my memories",
        }:
            facts = self.memory.recall(limit=50)

            if facts:
                response = (
                    "Your saved memories:\n\n"
                    + "\n".join(
                        f"{index}. {fact}"
                        for index, fact in enumerate(
                            facts, start=1
                        )
                    )
                )
            else:
                response = "You have no saved facts yet."

            self._show_memory_response(command, response)
            return True

        # Search saved facts
        search_prefixes = (
            "what do you remember about ",
            "do you remember ",
            "recall ",
        )

        for prefix in search_prefixes:
            if lowered.startswith(prefix):
                query = command[len(prefix):].strip()

                if not query:
                    response = "Please specify what to search for."
                else:
                    facts = self.memory.recall(
                        query=query,
                        limit=20,
                    )

                    if facts:
                        response = (
                            "I found these saved facts:\n\n"
                            + "\n".join(
                                f"- {fact}" for fact in facts
                            )
                        )
                    else:
                        response = (
                            "No saved facts matched: "
                            f"{query}"
                        )

                self._show_memory_response(command, response)
                return True

        # Forget one exact saved fact
        prefix = "forget this:"

        if lowered.startswith(prefix):
            fact = command[len(prefix):].strip()

            if not fact:
                response = (
                    "Please provide the exact fact "
                    "you want me to forget."
                )
            elif self.memory.forget(fact):
                response = (
                    "Removed from persistent memory:\n"
                    f"{fact}"
                )
            else:
                response = (
                    "I couldn't find that exact saved fact."
                )

            self._show_memory_response(command, response)
            return True

        return False

    def _show_memory_response(self, user_text, response):
        """Save and display a local memory-command exchange."""

        self.memory.add("user", user_text)
        self._add_bubble("You", user_text, "user")

        self.memory.add("assistant", response)
        self._add_bubble("ULTRON", response, "assistant")

        self.status.setText("MEMORY ACTION COMPLETE")

    # --------------------------------------------------
    # NORMAL AI CHAT
    # --------------------------------------------------

    def send_message(self):
        if self.busy:
            return

        text = self.input.text().strip()

        if not text:
            return

        self.input.clear()

        # Handle memory commands before calling the AI.
        if self._handle_memory_command(text):
            return

        self.memory.add("user", text)
        self._add_bubble("You", text, "user")

        history = self.memory.recent(12)

        provider = (
            "local"
            if self.provider.currentIndex() == 0
            else "cloud"
        )

        self._set_busy(
            True,
            f"ULTRON THINKING  •  {provider.upper()}",
        )

        self.task = TaskThread(
            lambda: UltronBrain(
    provider,
    memory=self.memory,
).reply(history)
        )

        self.task.succeeded.connect(self._on_reply)
        self.task.failed.connect(self._on_error)
        self.task.finished.connect(self._task_finished)

        self.task.start()

    def _on_reply(self, answer):
        self.memory.add("assistant", answer)
        self._add_bubble("ULTRON", answer, "assistant")

        self.status.setText("RESPONSE READY")
        self._speak_async(answer)

    def _on_error(self, error):
        self._add_bubble("SYSTEM", error, "assistant")
        self.status.setText(
            "ACTION NEEDED  •  See message above"
        )

    def _task_finished(self):
        self._set_busy(False, self.status.text())

    # --------------------------------------------------
    # VOICE
    # --------------------------------------------------

    def _speak_async(self, text):
        # Keep speech processing off the UI thread.
        self.task = TaskThread(
            lambda: (
                self.voice.speak(text),
                "Speech complete",
            )[1]
        )

        self.task.failed.connect(
            lambda err: self.status.setText(
                f"Speech unavailable: {err}"
            )
        )

        self.task.start()

    def listen(self):
        if self.busy:
            return

        self._set_busy(
            True,
            "LISTENING  •  Speak after pressing Listen",
        )

        self.task = TaskThread(
            lambda: self.voice.listen_once()
        )

        self.task.succeeded.connect(self._on_heard)
        self.task.failed.connect(self._on_error)
        self.task.finished.connect(self._task_finished)

        self.task.start()

    def _on_heard(self, text):
        if text:
            self.input.setText(text)
            self.status.setText(
                "VOICE CAPTURED  •  Review and press Send"
            )
        else:
            self.status.setText(
                "No speech detected. Try again."
            )

    # --------------------------------------------------
    # CLEAR CHAT
    # --------------------------------------------------

    def clear_chat(self):
        answer = QMessageBox.question(
            self,
            "Clear chat",
            (
                "Delete saved conversation history?\n\n"
                "Your persistent saved memories will remain."
            ),
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        self.memory.clear()

        while self.chat_layout.count():
            item = self.chat_layout.takeAt(0)

            if item.widget():
                item.widget().deleteLater()

        self.status.setText(
            "CHAT HISTORY CLEARED  •  SAVED MEMORIES RETAINED"
        )
        self._adjust_compact_height()
