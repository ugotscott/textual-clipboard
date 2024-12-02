from __future__ import annotations
from dataclasses import dataclass
from textual.app import App, ComposeResult
from textual.widgets import TextArea, Header, Footer, Label
from textual.binding import Binding
from textual.message import Message

"""Demo TextArea with clipboard (cut/copy/paste) feature"""


@dataclass
class State:
    """State storage for the app"""

    clipboard = ""


class TextClipboard(TextArea):
    """Adds these features to TextArea:

    Cut ctrl-x

    Copy ctrl-c

    Paste ctrl-v

    Send message when clipboard text is updated
    """

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
        """Update clipboard and delete the selected text"""
        State.clipboard = self.selected_text
        print(f"action_cut_selection: State.clipboard updated to {State.clipboard}")
        self.post_message(self.ClipboardUpdate(State.clipboard))
        self.action_delete_left()

    def action_paste_text(self) -> None:
        """Insert clipboard text"""
        if State.clipboard:
            self.insert(State.clipboard)

    def action_copy_selection(self) -> None:
        """Update clipboard with the selected text"""
        State.clipboard = self.selected_text
        print(f"action_copy_selection: State.clipboard updated to {State.clipboard}")
        self.post_message(self.ClipboardUpdate(State.clipboard))


class ClipboardWatcher(TextClipboard):
    """Provides widget to display clipboard content"""

    def clipboard_update(self, clipboard_text) -> None:
        """Replace text area with new content"""
        print(f"Clipboard content changed {clipboard_text}")
        self.clear()
        self.insert(clipboard_text)


class MyApp(App):
    """Demo textarea with clipboard"""

    CSS_PATH = "text_clipboard.tcss"
    BINDINGS = [Binding("ctrl+c", "quit", "Quit", show=True, priority=False)]

    def compose(self) -> ComposeResult:
        """Top level widgets"""
        yield Header()
        yield Footer()
        yield Label("Editor:")
        yield TextClipboard()
        yield Label("Clipboard:")
        yield ClipboardWatcher()

    def on_text_clipboard_clipboard_update(
        self, message: TextClipboard.ClipboardUpdate
    ) -> None:
        """Update clipboard watcher with updated clipboard content"""
        print(f"Clipboard content changed to {message.clipboard_text}")
        self.query_one(ClipboardWatcher).clipboard_update(message.clipboard_text)


def main():
    app = MyApp()
    app.run()


if __name__ == "__main__":
    main()
