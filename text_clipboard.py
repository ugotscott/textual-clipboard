from __future__ import annotations
from dataclasses import dataclass
from textual.app import App, ComposeResult
from textual.widgets import TextArea, Header, Footer, Label
from textual.binding import Binding
from textual.message import Message


@dataclass
class State:
    clipboard = ""


class TextClipboard(TextArea):
    BINDINGS = [
        Binding("ctrl+c", "copy_selection", "Copy", show=False),
        Binding("ctrl+v", "paste_text", "Paste", show=False),
        Binding("ctrl+x", "cut_selection", "Cut", show=False),
    ]

    @dataclass
    class ClipboardUpdate(Message):
        """Posted when clipboard content has been updated.

        Handle this message using the `on` decorator - `@on(TextClipboard.ClipboardUpdate)`
        or a method named `on_text_clipboard_clipboard_update`.
        """

        def __init__(self, text: str) -> None:
            self.clipboard_text = text
            super().__init__()

    def action_cut_selection(self) -> None:
        State.clipboard = self.selected_text
        print(f"action_cut_selection: State.clipboard updated to {State.clipboard}")
        self.post_message(self.ClipboardUpdate(State.clipboard))
        self.action_delete_left()

    def action_paste_text(self) -> None:
        if State.clipboard:
            self.insert(State.clipboard)

    def action_copy_selection(self) -> None:
        State.clipboard = self.selected_text
        print(f"action_copy_selection: State.clipboard updated to {State.clipboard}")
        self.post_message(self.ClipboardUpdate(State.clipboard))


class ClipboardWatcher(TextClipboard):
    def clipboard_update(self, clipboard_text) -> None:
        print(f"Clipboard content changed {clipboard_text}")
        self.clear()
        self.insert(clipboard_text)


class MyApp(App):
    CSS_PATH = "text_clipboard.tcss"
    BINDINGS = [Binding("ctrl+c", "quit", "Quit", show=True, priority=False)]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield Label("Editor:")
        yield TextClipboard()
        yield Label("Clipboard:")
        yield ClipboardWatcher()

    def on_text_clipboard_clipboard_update(
        self, message: TextClipboard.ClipboardUpdate
    ) -> None:
        print(f"Clipboard content changed to {message.clipboard_text}")
        self.query_one(ClipboardWatcher).clipboard_update(message.clipboard_text)


if __name__ == "__main__":
    app = MyApp()
    app.run()
