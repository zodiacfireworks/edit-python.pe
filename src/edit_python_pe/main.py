import glob
import os

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.events import Event
from textual.screen import Screen
from textual.types import NoSelection
from textual.widgets import (
    Button,
    Input,
    ListItem,
    ListView,
    LoadingIndicator,
    OptionList,
    Select,
    Static,
    TextArea,
)

from .constants import (
    BITBUCKET_OPTION,
    FACEBOOK_OPTION,
    GITHUB_OPTION,
    GITLAB_OPTION,
    INSTAGRAM_OPTION,
    LINKEDIN_OPTION,
    X_OPTION,
    YOUTUBE_OPTION,
)
from .strings import _, set_language
from .utils import (
    build_md_content,
    create_pr,
    fork_repo,
    get_repo,
    load_file_into_form,
)


class LabeledInput(Vertical):
    def __init__(
        self, label: str, placeholder: str = "", value: str = "", **kwargs
    ):
        super().__init__(**kwargs)
        self.label = label
        self.placeholder = placeholder
        self._value = value

    def compose(self) -> ComposeResult:
        yield Static(self.label, classes="label")
        yield Input(
            id="input", placeholder=self.placeholder, value=self._value
        )

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, v: str):
        self._value = v
        self.query_one(selector="#input").value = v  # type: ignore


class SocialEntry(Horizontal):
    def __init__(self, index: int, value: str) -> None:
        super().__init__()
        self.index = index
        self.select = Select(
            options=[
                GITHUB_OPTION,
                GITLAB_OPTION,
                BITBUCKET_OPTION,
                LINKEDIN_OPTION,
                FACEBOOK_OPTION,
                INSTAGRAM_OPTION,
                X_OPTION,
                YOUTUBE_OPTION,
            ],
            prompt=_("Social Network"),
            value=value,
        )
        self.url_input = Input(placeholder=_("Social network URL"))
        self.delete_btn = Button(_("Delete"), id=f"delete_social_{index}")

    def compose(self) -> ComposeResult:
        yield self.select
        yield self.url_input
        yield self.delete_btn


class AliasEntry(Horizontal):
    def __init__(self, index: int) -> None:
        super().__init__()
        self.index = index
        self.alias_input = Input(placeholder=_("Alias"))
        self.delete_btn = Button(_("Delete"), id=f"delete_alias_{index}")

    def compose(self) -> ComposeResult:
        yield self.alias_input
        yield self.delete_btn


class LanguageScreen(Screen):
    def compose(self) -> ComposeResult:
        with Vertical(id="lang-container"):
            yield Static(
                _("Welcome aboard to Python Perú"),
                id="welcome-header",
                classes="header",
            )
            yield Static(_("Select your language"), id="lang-label")
            yield OptionList(
                "English",
                "Español",
                "Français",
                "Italiano",
                "Português",
                "Runa Simi",
                id="lang-select",
            )
            with Horizontal(id="lang-actions"):
                yield Button(_("Quit"), id="lang-quit", variant="error")
                yield Button(
                    _("Continue"), id="lang-continue", variant="primary"
                )
            yield Static(
                _("Proudly built with 🤍 in Perú"),
                id="footer-msg",
                classes="footer",
            )

    def on_option_list_option_highlighted(
        self, event: OptionList.OptionHighlighted
    ) -> None:
        lang_map = {
            0: "en",
            1: "es",
            2: "fr",
            3: "it",
            4: "pt",
            5: "qu",
        }
        lang_code = (
            lang_map.get(event.option_index, "en")
            if event.option_index is not None
            else "en"
        )

        set_language(lang_code)

        # Update labels dynamically
        self.query_one("#welcome-header", Static).update(
            _("Welcome aboard to Python Perú")
        )
        self.query_one("#lang-label", Static).update(_("Select your language"))
        self.query_one("#lang-continue", Button).label = _("Continue")
        self.query_one("#lang-quit", Button).label = _("Quit")
        self.query_one("#footer-msg", Static).update(
            _("Proudly built with 🤍 in Perú")
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "lang-quit":
            self.app.exit()
        elif event.button.id == "lang-continue":
            # If the user clicks continue without highlighting an option,
            # make sure we set default
            opt_list = self.query_one("#lang-select", OptionList)
            selected_idx = opt_list.highlighted
            lang_map = {0: "en", 1: "es", 2: "fr", 3: "it", 4: "pt", 5: "qu"}
            lang_code = (
                lang_map.get(selected_idx, "en")
                if selected_idx is not None
                else "en"
            )
            set_language(lang_code)
            self.app.push_screen(AuthScreen())


class AuthScreen(Screen):
    def compose(self) -> ComposeResult:
        with Vertical(id="auth-container"):
            yield Static(_("Please enter your GitHub personal access token: "))
            yield Input(password=True, id="github-token")
            yield Button(_("Login"), id="login-btn")
            yield LoadingIndicator(id="loading")

    def on_mount(self) -> None:
        self.query_one("#loading").display = False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "login-btn":
            token = self.query_one("#github-token", Input).value.strip()
            if not token:
                return

            self.query_one("#loading").display = True
            self.query_one("#login-btn").disabled = True
            self.query_one("#github-token").disabled = True

            self.run_worker(self.authenticate_and_clone(token), exclusive=True)

    async def authenticate_and_clone(self, token: str) -> None:
        try:
            # We call the blocking IO inside the worker
            _, original_repo = get_repo(token)
            repo_path, forked_repo = fork_repo(token, original_repo)

            from typing import cast

            app = cast("MemberApp", self.app)
            # Pass data to the app instance
            app.original_repo = original_repo
            app.forked_repo = forked_repo
            app.repo_path = repo_path
            app.token = token

            self.app.call_from_thread(self.app.push_screen, MainScreen())
        except Exception as e:
            error_message = str(e)

            def show_error():
                self.query_one("#loading").display = False
                self.query_one("#login-btn").disabled = False
                self.query_one("#github-token").disabled = False
                self.notify(error_message, severity="error")

            self.app.call_from_thread(show_error)


class MainScreen(Screen):
    def compose(self) -> ComposeResult:
        with Vertical(id="list-container"):
            yield Static(_("Files in 'blog/members':"))
            yield ListView(id="list-view")
            yield Button(_("Add"), id="add_list")
            yield Button(_("Quit"), id="quit_list")

        with Vertical(id="form-container"):
            yield Static(_("Member Form"), classes="header")
            yield LabeledInput(
                _("Name:"), placeholder=_("Name"), id="name-input"
            )
            yield LabeledInput(
                _("Email:"), placeholder=_("Email"), id="email-input"
            )

            yield Static(_("Social Networks"), classes="subheader")
            yield Vertical(id="social-container")
            yield Button(_("Add Social Network"), id="add_social")

            yield Static(_("Aliases"), classes="subheader")
            yield Vertical(id="alias-container")
            yield Button(_("Add Alias"), id="add_alias")

            yield LabeledInput(
                _("City:"), placeholder=_("City"), id="city-input"
            )
            yield LabeledInput(
                _("Homepage:"), placeholder=_("Homepage"), id="homepage-input"
            )

            yield Static(
                _("Who are you and what do you do?"), classes="subheader"
            )
            yield TextArea(id="who-area")

            yield Static(
                _("How do you program in Python?"), classes="subheader"
            )
            yield TextArea(id="python-area")

            yield Static(
                _("Do you have any contributions to the Python community?"),
                classes="subheader",
            )
            yield TextArea(id="contributions-area")

            yield Static(
                _("Are you available for mentoring, consulting, talks?"),
                classes="subheader",
            )
            yield TextArea(id="availability-area")

            with Horizontal(id="form-button-bar"):
                yield Button(_("Save"), id="save")
                yield Button(_("Back"), id="back")
                yield Button(_("Quit"), id="quit")

    def on_mount(self) -> None:
        self.social_entries: list[SocialEntry] = []
        self.alias_entries: list[AliasEntry] = []
        self.social_index = 0
        self.alias_index = 0
        self.current_file = None

        from typing import cast

        app = cast("MemberApp", self.app)
        # Load files into ListView
        list_view = self.query_one("#list-view", ListView)
        md_files = glob.glob(
            os.path.join(app.repo_path, "blog", "members", "*.md")
        )
        for f in md_files:
            basename = os.path.basename(f)
            list_view.append(ListItem(Static(basename)))

        self.query_one("#form-container").display = False

        # Connect proxy inputs to MemberApp style to not break tests
        self.name_input = self.query_one("#name-input", LabeledInput)
        self.email_input = self.query_one("#email-input", LabeledInput)
        self.city_input = self.query_one("#city-input", LabeledInput)
        self.homepage_input = self.query_one("#homepage-input", LabeledInput)
        self.who_area = self.query_one("#who-area", TextArea)
        self.python_area = self.query_one("#python-area", TextArea)
        self.contributions_area = self.query_one(
            "#contributions-area", TextArea
        )
        self.availability_area = self.query_one("#availability-area", TextArea)
        self.social_container = self.query_one("#social-container", Vertical)
        self.alias_container = self.query_one("#alias-container", Vertical)

    def show_list(self) -> None:
        self.query_one("#list-container").display = True
        self.query_one("#form-container").display = False

    def show_form(self) -> None:
        self.query_one("#list-container").display = False
        self.query_one("#form-container").display = True

    def clear_form(self) -> None:
        self.name_input.value = ""
        self.email_input.value = ""
        self.city_input.value = ""
        self.homepage_input.value = ""
        self.who_area.text = ""
        self.python_area.text = ""
        self.contributions_area.text = ""
        self.availability_area.text = ""

        for soc in self.social_entries:
            soc.remove()
        self.social_entries.clear()
        self.social_index = 0
        self.social_container.remove_children()

        for ali in self.alias_entries:
            ali.remove()
        self.alias_entries.clear()
        self.alias_index = 0
        self.alias_container.remove_children()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item_text_widget = event.item.children[0]
        filename = item_text_widget.content  # type: ignore
        self.current_file = filename

        self.clear_form()
        load_file_into_form(self, filename)
        self.show_form()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "quit_list":
            self.app.exit(message=_("See you next time!"))
        elif bid == "add_social":
            self.add_social_entry()
        elif bid == "add_alias":
            self.add_alias_entry()
        elif bid == "add_list":
            self.clear_form()
            self.current_file = None
            self.show_form()
        elif bid == "save":
            self.save_member()
        elif bid == "back":
            self.clear_form()
            self.show_list()
        elif bid == "quit":
            self.app.exit(message=_("See you next time!"))
        elif bid and bid.startswith("delete_social_"):
            index = int(bid.replace("delete_social_", ""))
            self.remove_social_entry(index)
        elif bid and bid.startswith("delete_alias_"):
            index = int(bid.replace("delete_alias_", ""))
            self.remove_alias_entry(index)

    def add_social_entry(
        self,
        value: str | NoSelection = Select.BLANK,  # type: ignore
    ) -> None:
        new_entry = SocialEntry(self.social_index, value)  # type: ignore
        self.social_index += 1
        self.social_entries.append(new_entry)
        self.social_container.mount(new_entry)

    def remove_social_entry(self, index: int) -> None:
        found = None
        for e in self.social_entries:
            if e.index == index:
                found = e
                break
        if found:
            self.social_entries.remove(found)
            found.remove()

    def add_alias_entry(self) -> None:
        row = AliasEntry(self.alias_index)
        self.alias_index += 1
        self.alias_entries.append(row)
        self.alias_container.mount(row)

    def remove_alias_entry(self, index: int) -> None:
        found = None
        for a in self.alias_entries:
            if a.index == index:
                found = a
                break
        if found:
            self.alias_entries.remove(found)
            found.remove()

    def save_member(self) -> None:
        name = self.name_input.value.strip()
        email = self.email_input.value.strip()
        city = self.city_input.value.strip()
        homepage = self.homepage_input.value.strip()
        who = self.who_area.text.strip()
        python_ = self.python_area.text.strip()
        contributions = self.contributions_area.text.strip()
        availability = self.availability_area.text.strip()

        aliases = []
        for row in self.alias_entries:
            alias_val = row.alias_input.value.strip()
            if alias_val:
                aliases.append(alias_val)

        socials = []
        for se in self.social_entries:
            plat = se.select.value
            urlval = se.url_input.value.strip()
            if plat and urlval:
                socials.append((str(plat), urlval))

        md_content = build_md_content(
            name,
            email,
            aliases,
            socials,
            city,
            homepage,
            who,
            python_,
            contributions,
            availability,
        )

        from typing import cast

        app = cast("MemberApp", self.app)

        assert app.original_repo is not None
        assert app.forked_repo is not None

        message = create_pr(
            md_content,
            self.current_file,
            app.repo_path,
            app.original_repo,
            app.forked_repo,
            app.token,
            aliases,
            name,
            email,
        )
        self.app.exit(message=message)

    async def on_event(self, event: Event) -> None:
        if isinstance(event, ListView.Selected):
            self.on_list_view_selected(event)
        await super().on_event(event)


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


def main() -> None:
    app = MemberApp()
    app.run()


if __name__ == "__main__":
    main()
