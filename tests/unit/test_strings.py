from edit_python_pe.strings import _, set_language


class TestStrings:
    def test_strings_set_language(self):
        set_language("es")
        assert isinstance(_("Hello"), str)
        set_language("en")
