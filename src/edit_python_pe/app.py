from textual.app import App

from .screens.language import LanguageScreen


class MemberApp(App):
    CSS_PATH = "styles.tcss"

    def __init__(self) -> None:
        super().__init__()
        self.original_repo = None
        self.forked_repo = None
        self.token = ""
        self.repo_path = ""

    def on_mount(self) -> None:
        self.push_screen(LanguageScreen())
