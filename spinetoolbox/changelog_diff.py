"""Contains functions for CHANGELOG diffs."""
import os
import difflib
from .config import CHANGELOG_PATH


def save_changelog_to_settings(settings):
    if os.path.isfile(CHANGELOG_PATH):
        with open(CHANGELOG_PATH, "r") as fp:
            cl = fp.readlines()
            settings.setValue("changeLog", cl)

def get_changelog_diff(settings):
    if os.path.isfile(CHANGELOG_PATH):
        with open(CHANGELOG_PATH, "r") as fp:
            current_changelog = fp.readlines()
        old_changelog = settings.value("changelog", None)
        if not old_changelog:
            return None
        diff = [li for li in difflib.ndiff(old_changelog, current_changelog) if li[0] != ' ']
        return diff
    return None