import time
from pathlib import Path

from dotenv import load_dotenv
from pydantic import ValidationError
from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import (
    Center,
    Horizontal,
    Middle,
    Vertical,
    VerticalScroll,
)
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    Markdown,
    Select,
    Static,
)

from app.ui.directory_picker import DirectoryPicker
from app.ui.styles import APP_CSS
from app.utils.chat import (
    MAX_TOKENS,
    Conversation,
    fetch_context,
    generate_title,
    stream_answer,
)
from app.utils.indexing import has_files, index_directory
from app.utils.persistence import (
    ConversationRecord,
    conversation_title,
    list_conversations,
    load_conversation,
    rename_conversation,
    save_conversation,
)
from src.var import (
    INDEX_DIR,
    LANG,
    RAW_DIR,
    SYSTEM,
)

load_dotenv()


class HistoryButton(Button):
    """History panel button bound to a conversation file."""

    def __init__(self, path: Path) -> None:
        """Label the button with the conversation title."""
        super().__init__(conversation_title(path))
        self.path = path


class RagApp(App[None]):
    """Main RAG application window."""

    TITLE = "RAG"
    BINDINGS = [Binding("ctrl+q", "quit", "Quit", show=True, priority=True)]
    CSS = APP_CSS

    def __init__(self) -> None:
        """Start the app with no indexed directory."""
        super().__init__()
        self.indexed_path: Path | None = None
        self.conversation = Conversation()
        self.chat_started = False
        self.lang = LANG

    def compose(self) -> ComposeResult:
        """Build the window widgets."""
        yield Header()
        with Vertical(id="home"):
            with Horizontal():
                yield VerticalScroll(id="history-panel")
                with Vertical(id="home-main"):
                    with Middle():
                        with Center():
                            yield Input(
                                placeholder="Ask your question...", id="prompt"
                            )
                        with Center():
                            with Horizontal(id="home-buttons"):
                                yield Button(
                                    "Choose a folder",
                                    variant="primary",
                                    id="pick-folder",
                                )
                                yield Select(
                                    [(c, c) for c in sorted({"fr", "en", LANG})],
                                    value=LANG,
                                    allow_blank=False,
                                    id="lang",
                                )
                        with Center():
                            yield Label(
                                f"No files in {RAW_DIR}", id="status"
                            )
        yield VerticalScroll(id="chat-log")
        with Vertical(id="bottom-bar"):
            with Horizontal(id="chat-bar"):
                yield Button(
                    "Change folder", variant="primary", id="chat-folder"
                )
                yield Button("Back to home", id="chat-home")
            yield Input(placeholder="Ask your question...", id="chat-input")
        yield Footer()

    def on_mount(self) -> None:
        """Hide the chat and index the default directory on startup."""
        self.show_chat(False)
        self.index_default()

    def index_default(self) -> None:
        """Index RAW_DIR on startup if it contains files."""
        path = Path(RAW_DIR)
        if not has_files(path):
            self.query_one("#status", Label).update(
                f"No files in {RAW_DIR}"
            )
            return
        self.query_one("#status", Label).update(f"Indexing {path}...")
        self.index_folder(path, self.lang)

    def show_chat(self, visible: bool) -> None:
        """Toggle between the chat screen and the home screen."""
        for widget_id in ("#chat-log", "#bottom-bar"):
            self.query_one(widget_id).display = visible
        self.query_one("#home").display = not visible
        if not visible:
            self.refresh_history_panel()

    def refresh_history_panel(self) -> None:
        """Rebuild the list of saved conversations."""
        panel = self.query_one("#history-panel", VerticalScroll)
        panel.remove_children()
        files = list_conversations()
        if not files:
            panel.mount(Static("No conversations", classes="history-empty"))
            return
        for path in files:
            panel.mount(HistoryButton(path))

    def start_chat(self) -> None:
        """Switch from the home screen to the chat view."""
        self.chat_started = True
        self.show_chat(True)
        self.query_one("#chat-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Send the question to the LLM, switching to chat view if needed."""
        query = event.value.strip()
        event.input.clear()
        if not query:
            return
        if not self.chat_started:
            self.start_chat()
            self.name_chat(query)
        self.send_query(query, self.lang)

    def send_query(self, query: str, lang: str) -> None:
        """Display the question, then call the LLM."""
        chat_log = self.query_one("#chat-log", VerticalScroll)
        chat_log.mount(Static(query, classes="user-message"))
        answer = Markdown(
            "*Searching sources...*", classes="answer-message"
        )
        chat_log.mount(answer)
        chat_log.scroll_end(animate=False)
        self.query_one("#chat-input", Input).disabled = True
        self.ask_llm(query, lang, answer)

    @work(thread=True, exclusive=True)
    def ask_llm(self, query: str, lang: str, answer: Markdown) -> None:
        """Retrieve sources, then stream the LLM answer."""
        try:
            context = fetch_context(query, lang)
        except Exception as error:
            self.call_from_thread(
                self.stream_update,
                answer,
                f"*No index available ({error.__class__.__name__}), "
                "answering without sources.*\n\n",
            )
            context = ""

        user = self.conversation.build_prompt(query, context)

        try:
            full_response = ""
            for delta in stream_answer(user, SYSTEM, MAX_TOKENS):
                time.sleep(0.01)
                full_response += delta
                self.call_from_thread(
                    self.stream_update, answer, full_response
                )
        except Exception as error:
            self.call_from_thread(self.answer_failed, answer, error)
        else:
            self.call_from_thread(self.answer_done, query, full_response)

    @work(thread=True, group="title")
    def name_chat(self, query: str) -> None:
        """Generate the conversation title without blocking the answer."""
        try:
            title = generate_title(query)
        except Exception:  # keep the default timestamped name
            return
        if title:
            self.call_from_thread(self.title_ready, title)

    def title_ready(self, title: str) -> None:
        """Rename the conversation once the title is generated."""
        try:
            rename_conversation(self.conversation.record, title)
        except OSError as error:
            self.notify(
                f"Could not rename: {error}",
                title="History",
                severity="warning",
            )
            return
        self.sub_title = title

    def stream_update(self, answer: Markdown, text: str) -> None:
        """Update the answer bubble while streaming."""
        if not answer.is_mounted:  # bubble removed by a reset
            return
        answer.update(text)
        self.query_one("#chat-log", VerticalScroll).scroll_end(animate=False)

    def answer_done(self, query: str, response: str) -> None:
        """Record and save the exchange, then re-enable input."""
        self.conversation.add(query, response)
        try:
            save_conversation(self.conversation.record)
        except OSError as error:
            self.notify(
                f"Could not save: {error}",
                title="History",
                severity="warning",
            )
        chat_input = self.query_one("#chat-input", Input)
        chat_input.disabled = False
        chat_input.focus()

    def answer_failed(self, answer: Markdown, error: Exception) -> None:
        """Display the error returned by the LLM."""
        if not answer.is_mounted:
            return
        answer.update(f"**Error**: {error.__class__.__name__}: {error}")
        chat_input = self.query_one("#chat-input", Input)
        chat_input.disabled = False
        chat_input.focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Open the folder picker, go home, or open a saved conversation."""
        if event.button.id in ("pick-folder", "chat-folder"):
            self.push_screen(
                DirectoryPicker(self.indexed_path), self.folder_chosen
            )
        elif event.button.id == "chat-home":
            self.go_home()
        elif isinstance(event.button, HistoryButton):
            self.open_history(event.button.path)

    def on_select_changed(self, event: Select.Changed) -> None:
        """Switch the stopword language and re-index with it."""
        if event.value == self.lang:
            return
        self.lang = str(event.value)
        path = self.indexed_path or Path(RAW_DIR)
        if not has_files(path):
            return
        self.query_one("#status", Label).update(f"Indexing {path}...")
        self.index_folder(path, self.lang)

    def open_history(self, path: Path) -> None:
        """Load the conversation from the file chosen in the panel."""
        try:
            record = load_conversation(path)
        except (OSError, ValidationError) as error:
            self.notify(
                f"Unreadable file ({path.name}): {error}",
                title="History",
                severity="error",
            )
            return
        self.show_conversation(record)

    def show_conversation(self, record: ConversationRecord) -> None:
        """Display a saved conversation in the chat."""
        self.conversation.restore(record)
        self.sub_title = record.name
        self.start_chat()
        chat_log = self.query_one("#chat-log", VerticalScroll)
        chat_log.remove_children()
        for exchange in record.exchanges:
            chat_log.mount(Static(exchange.query, classes="user-message"))
            chat_log.mount(
                Markdown(exchange.response, classes="answer-message")
            )
        chat_log.scroll_end(animate=False)
        self.notify(
            f"Conversation from {record.created_at} reloaded "
            f"({len(record.exchanges)} exchanges)",
            title="History",
            severity="information",
        )

    def go_home(self) -> None:
        """Return to the home screen, keeping the current index."""
        self.query_one("#chat-log", VerticalScroll).remove_children()
        self.query_one("#chat-input", Input).clear()
        self.conversation.reset()
        self.sub_title = ""
        self.chat_started = False
        self.show_chat(False)
        self.query_one("#prompt", Input).focus()

    def folder_chosen(self, path: Path | None) -> None:
        """Start indexing the chosen directory."""
        if path is None:
            return
        self.notify(
            f"Folder selected: {path}",
            title="Success",
            severity="information",
        )
        self.query_one("#status", Label).update(f"Indexing {path}...")
        self.index_folder(path, self.lang)

    @work(thread=True, exclusive=True)
    def index_folder(self, path: Path, lang: str) -> None:
        """Build the directory BM25 index in a worker thread."""
        try:
            count = index_directory(path, lang)
        except Exception as error:
            self.call_from_thread(self.indexing_failed, error)
        else:
            self.call_from_thread(self.indexing_done, path, count)

    def indexing_done(self, path: Path, count: int) -> None:
        """Display the result of a finished indexing run."""
        if count == 0:
            self.query_one("#status", Label).update("No indexable files")
            self.notify(
                f"No indexable files under {path}",
                title="Indexing",
                severity="warning",
            )
            return
        self.indexed_path = path
        self.query_one("#status", Label).update(
            f'Indexed "{path}" - {count} chunks'
        )
        self.notify(
            f"Indexing succeeded: {count} chunks written to {INDEX_DIR}",
            title="Success",
            severity="information",
        )

    def indexing_failed(self, error: Exception) -> None:
        """Display the error raised during indexing."""
        self.query_one("#status", Label).update("Indexing failed")
        self.notify(
            f"{error.__class__.__name__}: {error}",
            title="Error",
            severity="error",
        )
