#!/usr/bin/env python

from pathlib import Path
import time


current_year = time.gmtime().tm_year
root_dir = Path(__file__).parent.parent
project_source_dir = Path(root_dir, "spinetoolbox")
test_source_dir = Path(root_dir, "tests")

expected = f"# Copyright (C) 2017-{current_year} Spine project consortium"


def update_copyrights(path, suffix, recursive=True):
    for path in path.iterdir():
        if path.suffix == suffix:
            with open(path) as python_file:
                lines = python_file.readlines()
                for i, line in enumerate(lines[1:4]):
                    if line.startswith("# Copyright (C) "):
                        lines[i + 1] = lines[i + 1][:21] + str(current_year) + lines[i + 1][25:]
                        break
            if not lines[i + 1].startswith(expected):
                print(f"Confusing or no copyright: {path}")
            else:
                with open(path, "w") as python_file:
                    python_file.writelines(lines)
        elif recursive and path.is_dir():
            update_copyrights(path, suffix)


update_copyrights(root_dir, ".py", recursive=False)
update_copyrights(project_source_dir, ".py")
update_copyrights(project_source_dir, ".ui")
update_copyrights(test_source_dir, ".py")
