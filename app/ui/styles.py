PICKER_CSS = """
DirectoryPicker {
    align: center middle;
}
#picker-box {
    width: 70%;
    height: 80%;
    border: round $accent;
    background: $surface;
    padding: 1;
}
#picker-buttons {
    height: auto;
    align: center middle;
}
#picker-buttons Button {
    margin: 1 2;
}
"""

APP_CSS = """
#history-panel {
    dock: left;
    width: 36;
    border-right: solid $accent;
    padding: 1;
}
#history-panel Button {
    width: 100%;
    margin-bottom: 1;
}
.history-empty {
    color: $text-muted;
}
#home-main {
    width: 1fr;
}
#prompt {
    width: 60%;
}
#home-buttons {
    height: auto;
    width: auto;
    align: center middle;
}
#home-buttons Button {
    margin: 1 1 0 1;
}
#lang {
    width: 12;
    margin: 1 1 0 1;
}
#status {
    margin-top: 1;
    color: $text-muted;
}
#chat-log {
    height: 1fr;
    padding: 1 2;
}
#bottom-bar {
    dock: bottom;
    height: auto;
}
#chat-bar {
    height: auto;
    align: right middle;
    margin: 0 2;
}
#chat-bar Button {
    margin: 0 0 0 2;
    min-width: 20;
}
#chat-input {
    margin: 1 2 1 2;
}
.user-message {
    background: $primary 20%;
    border-left: thick $primary;
    padding: 0 1;
    margin: 1 0 0 0;
}
.answer-message {
    margin: 0 0 1 0;
}
"""
