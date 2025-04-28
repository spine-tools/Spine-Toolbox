"""Contains functions for CHANGELOG diffs."""
import os
import difflib
from .config import CHANGELOG_PATH
import re


'''
def save_changelog_to_settings(settings):
    if os.path.isfile(CHANGELOG_PATH):
        with open(CHANGELOG_PATH, "r") as fp:
            cl = fp.readlines()
            settings.setValue("changeLog", cl)
'''


def pick_latest_release(settings):
    if os.path.isfile(CHANGELOG_PATH):
        with open(CHANGELOG_PATH, "r") as fp:
            current_changelog = fp.read()

        # Use regex to find all headers (e.g., ## [Version])
        headers = re.findall(r'^## \[.*?\]', current_changelog, re.MULTILINE)

        if headers:
            # Assume the first header is the latest release (e.g., Unreleased or latest version)
            latest_release_header = headers[0]

            # Find the position of the latest release
            latest_release_start = current_changelog.find(latest_release_header)
            next_header_start = None

            # Find the next header to delimit the section
            for header in headers[1:]:
                pos = current_changelog.find(header, latest_release_start + len(latest_release_header))
                if pos != -1:
                    next_header_start = pos
                    break

            # Extract the content of the latest release section
            if next_header_start:
                latest_release_content = current_changelog[latest_release_start:next_header_start].strip()
            else:
                # No further header; take till the end of the file
                latest_release_content = current_changelog[latest_release_start:].strip()

            # Split the content into lines for further processing
            diff = [line.strip() for line in latest_release_content.splitlines() if line.strip()]

            return diff
        else:
            print("No headers found in the changelog.")
            return []
    else:
        print(f"Changelog not found at {CHANGELOG_PATH}")
        return []