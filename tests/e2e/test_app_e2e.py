import tempfile
from unittest.mock import MagicMock, patch

import pytest

from edit_python_pe.app import MemberApp
from edit_python_pe.screens.auth import AuthScreen
from edit_python_pe.screens.dashboard import DashboardScreen
from edit_python_pe.screens.language import LanguageScreen
from edit_python_pe.screens.member_form import MemberFormScreen
from edit_python_pe.screens.save_loading import SaveLoadingScreen


class TestAppE2E:
    @pytest.mark.asyncio
    @patch("edit_python_pe.screens.loading.get_repo")
    @patch("edit_python_pe.screens.loading.fork_repo")
    @patch("edit_python_pe.github_client._commit_and_push")
    @patch("keyring.get_password", return_value=None)
    @patch("keyring.set_password")
    async def test_full_app_flow(
        self,
        mock_set_password,
        mock_get_password,
        mock_commit_and_push,
        mock_fork_repo,
        mock_get_repo_loading,
    ):
        mock_repo = MagicMock()
        mock_forked = MagicMock()
        mock_get_repo_loading.return_value = ("fake-token", mock_repo)
        mock_fork_repo.return_value = (tempfile.gettempdir(), mock_forked)
        mock_commit_and_push.return_value = (
            "Commit message",
            MagicMock(),
            MagicMock(),
            MagicMock(),
        )

        # Create a mock PR
        mock_pr = MagicMock()
        mock_pr.html_url = "https://github.com/fake/pr"
        mock_repo.get_pulls.return_value = []
        mock_repo.create_pull.return_value = mock_pr

        app = MemberApp()
        async with app.run_test(size=(120, 100)) as pilot:
            # 1. Language Screen
            assert isinstance(app.screen, LanguageScreen)
            await pilot.click("#lang-continue")
            await pilot.pause()

            # 2. Auth Screen
            assert isinstance(app.screen, AuthScreen)
            await pilot.click("#github-token")
            await pilot.press("f", "a", "k", "e")
            await pilot.pause()
            await pilot.click("#login-btn")

            # 3. Loading Screen
            # The background thread sets app repos; advance_screen fires after a
            # 1.5 s timer. Give it up to 5 s total to reach DashboardScreen in CI.
            for _ in range(50):
                await pilot.pause(0.1)
                if isinstance(app.screen, DashboardScreen):
                    break

            assert isinstance(app.screen, DashboardScreen)

            # Verify repos were populated by LoadingScreen before proceeding
            assert app.original_repo is not None
            assert app.forked_repo is not None

            # 4. Dashboard -> Add Member
            await pilot.click("#dash-add")
            await pilot.pause()
            assert isinstance(app.screen, MemberFormScreen)

            # 5.1 Validation test
            await pilot.click("#member-form-add-alias")
            await pilot.click("#member-form-add-social")

            # Fill with invalid URLs
            app.screen.homepage_input.value = "not_a_url"

            # Since social entries are dynamically added, get the last one
            if app.screen.social_entries:
                app.screen.social_entries[-1].url_input.value = "not_a_social_url"

            await pilot.click("#member-form-save")
            await pilot.pause()

            # Validation should prevent navigating away
            assert isinstance(
                app.screen,
                __import__(
                    "edit_python_pe.screens.member_form"
                ).screens.member_form.MemberFormScreen,
            )

            # 5. Member Form Screen
            app.screen.name_input.value = "John Doe"
            app.screen.email_input.value = "john@example.com"
            app.screen.city_input.value = "Lima"
            app.screen.homepage_input.value = "https://example.com"
            if app.screen.social_entries:
                app.screen.social_entries[
                    -1
                ].url_input.value = "https://github.com/john"

            await pilot.click("#member-form-save")

            # 6. Save Loading Screen — give up to 5 s for the background work
            for _ in range(50):
                await pilot.pause(0.1)
                if (
                    isinstance(app.screen, SaveLoadingScreen)
                    and app.screen.query("#loading-actions")
                    and app.screen.query("#loading-actions").first().display
                ):
                    break

            assert isinstance(app.screen, SaveLoadingScreen)
            assert "was saved successfully" in str(
                app.screen.query_one("#result-msg").render()
            )

            # 7. Back to Dashboard
            app.pop_screen()
            await pilot.pause()

            for _ in range(10):
                await pilot.pause(0.1)
                if isinstance(app.screen, MemberFormScreen):
                    break

            # Now we are back at MemberFormScreen
            assert isinstance(app.screen, MemberFormScreen)

            # Click discard to go back to Dashboard
            app.pop_screen()
            await pilot.pause()
            for _ in range(10):
                await pilot.pause(0.1)
                if isinstance(app.screen, DashboardScreen):
                    break
            assert isinstance(app.screen, DashboardScreen)
