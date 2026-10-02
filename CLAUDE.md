# Working on Spine Toolbox

Conventions for changing or adding code in this repository. These reflect maintainer review
preferences; follow them so changes need less rework.

## Docstrings and comments
- Keep them lean. State what a function does, not how, and not what happens elsewhere in the code —
  descriptions of other code go out of sync when that code changes.
- Functions used only within Toolbox, especially short ones (a few lines), need only a one-line
  summary, or no docstring at all when the name and signature already say everything.
- Do not restate types, argument lists, or return values in prose when they are in the signature.
- Avoid jargon and filler. A comment must earn its place by explaining a non-obvious *why*.

## Type hints
- Put argument and return types in the function signature, never in the docstring. Do not add
  `Args:`/`Returns:` blocks solely to carry types; add them only for genuinely non-obvious meaning.
- Always annotate the return type (use `-> None` when nothing is returned).
- Use modern union syntax: `X | None`, not `Optional[X]`.
- Use `ClassVar[...]` for class-wide (non-instance) attributes.

## Simplicity — do not over-engineer
- Do not add functions, wrappers, or indirection that are not needed. Inline a one-line pass-through.
- Do not add defensive `None`/re-entrancy guards for conditions the call context already rules out
  (e.g. a slot invoked only from a single-threaded timer timeout cannot re-enter). Only guard what
  can actually happen.
- Merge state that is always read/written together. Two parallel dicts keyed the same way should be
  one dict of a small `@dataclass`.
- Prefer `if not x:` over `if x == "":`/`if len(x) == 0:`. Merge conditions that can be one `if`.
- Remove operations that have no effect.

## Naming and visibility
- A method or attribute used from outside its class is part of the public API: no leading underscore.
- Keep truly-internal helpers underscore-prefixed.

## Qt UI
- Do not build or mutate `self.ui` widgets/layouts by hand in Python (e.g. `insertWidget`). Declare
  widgets in the Qt Designer `.ui` file under `spinetoolbox/spine_db_editor/ui/` (promote custom
  widget classes there) and regenerate with `bin/build_ui.py`. Configure/connect them in code.
- Style widgets with Qt Style Sheets in code, not in Designer.

## Tests
- Write tests with `pytest` (test functions + fixtures), not `unittest.TestCase` subclasses.
- Do not add `if __name__ == "__main__": unittest.main()` — test modules are not runnable scripts.

## Style
- PEP 8 with 120-char lines; double-quoted strings. Run `black` and `isort` before committing.
- `.ui` files are compiled to `ui/*.py` by `bin/build_ui.py`; never hand-edit the generated `*.py`.

## Pull requests
- One concern per PR. Do not bundle orthogonal changes (refactors, unrelated fixes, behavior changes)
  with a feature — they make review harder and should be separate PRs.
