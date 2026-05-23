import pytest
from textual.app import App, ComposeResult

from edit_python_pe.components.layout import AppFooter, AppHeader


class ComponentTestApp(App):
    def compose(self) -> ComposeResult:
        yield AppHeader()
        yield AppFooter()


class TestLayout:
    @pytest.mark.asyncio
    async def test_layout_rendering(self):
        app = ComponentTestApp()
        async with app.run_test():
            header = app.query_one(AppHeader)
            footer = app.query_one(AppFooter)
            assert header is not None
            assert footer is not None
