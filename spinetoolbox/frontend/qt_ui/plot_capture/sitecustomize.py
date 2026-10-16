"""Makes ``matplotlib.pyplot.show()`` save figures, unmodified, to the Results folder instead of opening windows.

Python picks this module up automatically when its folder is on PYTHONPATH.
"""

import importlib.abc
import importlib.machinery
import importlib.util
import os
import sys
import time

_PLOTS_DIR_ENV_VAR = "SPINETOOLBOX_PLOTS_DIR"


def _chain_next_sitecustomize() -> None:
    """Runs the sitecustomize module that this one shadows, if any."""
    here = os.path.dirname(os.path.abspath(__file__))
    paths = [p for p in sys.path if os.path.abspath(p or ".") != here]
    spec = importlib.machinery.PathFinder.find_spec("sitecustomize", paths)
    if spec is not None and spec.loader is not None:
        spec.loader.exec_module(importlib.util.module_from_spec(spec))


def _save_figures_on_show(pyplot) -> None:
    def show(*args, **kwargs) -> None:
        plots_dir = os.environ.get(_PLOTS_DIR_ENV_VAR)
        if not plots_dir:
            return
        for number in pyplot.get_fignums():
            path = os.path.join(plots_dir, f"plot_{time.time_ns()}_{number}.png")
            # write under a temporary name so the Results page never reads a half-written image
            pyplot.figure(number).savefig(path + ".tmp", format="png")
            os.replace(path + ".tmp", path)
        pyplot.close("all")

    pyplot.show = show


class _PyplotLoader(importlib.abc.Loader):
    def __init__(self, wrapped: importlib.abc.Loader) -> None:
        self._wrapped = wrapped

    def create_module(self, spec):
        return self._wrapped.create_module(spec)

    def exec_module(self, module) -> None:
        self._wrapped.exec_module(module)
        _save_figures_on_show(module)


class _PyplotFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if fullname != "matplotlib.pyplot":
            return None
        sys.meta_path.remove(self)
        try:
            spec = importlib.util.find_spec(fullname)
        finally:
            sys.meta_path.insert(0, self)
        if spec is not None and spec.loader is not None:
            spec.loader = _PyplotLoader(spec.loader)
        return spec


if os.environ.get(_PLOTS_DIR_ENV_VAR):
    os.environ.setdefault("MPLBACKEND", "Agg")
    sys.meta_path.insert(0, _PyplotFinder())
_chain_next_sitecustomize()
