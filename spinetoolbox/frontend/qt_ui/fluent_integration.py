"""Helper to initialize FluentPySide theme when available.
This file attempts multiple known initialization entrypoints so it is
robust against different versions of FluentPySide.
"""
from typing import Any


def init_fluent_for_app(app: Any | None = None, theme: str | None = "dark") -> bool:
    """Try to initialize FluentPySide for the given Qt application.

    Returns True if Fluent initialization was applied, False otherwise.
    """
    try:
        import FluentPySide  # type: ignore
    except Exception:
        return False

    try:
        # Preferred: FluentPySide.init(app)
        if hasattr(FluentPySide, "init"):
            # some init() accept the app, others take no args
            try:
                if app is not None:
                    FluentPySide.init(app)
                else:
                    FluentPySide.init()
            except TypeError:
                FluentPySide.init()
            return True

        # Alternative: FluentPySide.setup_theme or apply_theme
        if hasattr(FluentPySide, "setup_theme"):
            try:
                FluentPySide.setup_theme(theme or "dark")
                return True
            except Exception:
                pass

        if hasattr(FluentPySide, "apply_theme"):
            try:
                FluentPySide.apply_theme(theme or "dark")
                return True
            except Exception:
                pass

        # Last resort: expose module-level attribute that sets palette
        if hasattr(FluentPySide, "theme") and app is not None:
            try:
                # some versions expose a Theme class
                theme_obj = getattr(FluentPySide, "theme")
                if callable(theme_obj):
                    theme_obj(app, theme or "dark")
                    return True
            except Exception:
                pass

    except Exception:
        return False

    return False


def get_token_colors() -> dict:
    """Return a mapping of node-kind -> (border_color, background_color).

    Attempts to query FluentPySide for theme tokens; falls back to sensible defaults.
    """
    # sensible defaults matching previous palette
    defaults = {
        "stack": ("#8a6fd8", "#f7f4ff"),
        "database": ("#50bf8c", "#f2fff8"),
        "tool": ("#dca557", "#fffaf1"),
        "results": ("#f1a053", "#fff9f3"),
        "input": ("#58b3ed", "#f7fcff"),
    }

    try:
        import FluentPySide  # type: ignore

        # Try common attribute names for color tokens
        palette = {}
        # newer versions might expose a `tokens` or `palette` dict
        if hasattr(FluentPySide, "tokens"):
            palette = getattr(FluentPySide, "tokens")
        elif hasattr(FluentPySide, "palette"):
            palette = getattr(FluentPySide, "palette")

        # If palette is a callable or object, try to access attributes
        if not isinstance(palette, dict):
            try:
                # convert object with attributes to dict
                palette = {k: getattr(palette, k) for k in dir(palette) if not k.startswith("_")}
            except Exception:
                palette = {}

        # Attempt to map tokens to our kinds
        mapping = {}
        # helper to pick a token or fallback
        def pick(*names, fallback="#dddddd"):
            for n in names:
                if n in palette:
                    return str(palette[n])
            return fallback

        mapping["stack"] = (pick("brandAccent", "accent", "purple" , fallback=defaults["stack"][0]), pick("stackBg", "purpleLight", fallback=defaults["stack"][1]))
        mapping["database"] = (pick("success", "green", fallback=defaults["database"][0]), pick("successLight", "greenLight", fallback=defaults["database"][1]))
        mapping["tool"] = (pick("accent", "orange", fallback=defaults["tool"][0]), pick("accentLight", "orangeLight", fallback=defaults["tool"][1]))
        mapping["results"] = (pick("warning", "amber", fallback=defaults["results"][0]), pick("warningLight", "amberLight", fallback=defaults["results"][1]))
        mapping["input"] = (pick("info", "blue", fallback=defaults["input"][0]), pick("infoLight", "blueLight", fallback=defaults["input"][1]))

        # If mapping looks reasonable, return it, else defaults
        if mapping:
            return mapping

    except Exception:
        pass

    return defaults
