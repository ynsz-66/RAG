from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DirectoryTree, Label

from app.ui.styles import PICKER_CSS


class DirectoryPicker(ModalScreen[Path | None]):
    """Modal screen for choosing a local directory."""

    BINDINGS = [("escape", "dismiss", "Cancel")]
    CSS = PICKER_CSS

    def __init__(self, root: Path | None = None) -> None:
        """Start the picker at the given root directory."""
        super().__init__()
        self.root = root or Path.home()
        self.selected = self.root

    def compose(self) -> ComposeResult:
        """Build the directory tree and buttons."""
        with Vertical(id="picker-box"):
            yield Label(str(self.selected), id="picker-path")
            yield DirectoryTree(self.root, id="picker-tree")
            with Horizontal(id="picker-buttons"):
                yield Button("Select", variant="success", id="picker-ok")
                yield Button("Cancel", variant="default", id="picker-cancel")

    def on_directory_tree_directory_selected(
        self, event: DirectoryTree.DirectorySelected
    ) -> None:
        """Remember the directory highlighted in the tree."""
        self.selected = event.path
        self.query_one("#picker-path", Label).update(str(event.path))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Confirm or cancel the selection."""
        self.dismiss(self.selected if event.button.id == "picker-ok" else None)
