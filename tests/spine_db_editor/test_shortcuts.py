import unittest
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtCore import QByteArray

app = QApplication.instance() or QApplication([])

class TestSpineDBEditorShortcuts(unittest.TestCase):
    def setUp(self):
        from spinetoolbox.spine_db_editor.widgets.spine_db_editor import SpineDBEditor
        self.mock_settings = MagicMock()

        with patch("spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.init_models"), \
                patch.object(SpineDBEditor, 'last_view', create=True, new=QByteArray()), \
                patch.object(SpineDBEditor, 'restoreState', return_value=True):
            self.spine_db_editor = SpineDBEditor(self.mock_settings)

    def tearDown(self):
        self.spine_db_editor.deleteLater()
        self.spine_db_editor = None

    def test_setup_focus_shortcuts(self):
        with patch('PySide6.QtGui.QShortcut') as MockShortcut:
            mock_shortcut = MagicMock()
            MockShortcut.return_value = mock_shortcut

            self.spine_db_editor.setup_focus_shortcuts()

            # Check if shortcut was created with correct key sequence
            MockShortcut.assert_any_call(QKeySequence("Alt+1"), self.spine_db_editor)