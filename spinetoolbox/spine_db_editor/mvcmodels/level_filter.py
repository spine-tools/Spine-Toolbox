######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# Copyright Spine Toolbox contributors
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""A mixin adding per-level regex filtering to tree models."""

from collections.abc import Callable
from PySide6.QtCore import QTimer, Slot
from .utils import make_search_matcher

LEVEL_FILTER_INTERVAL = 200
"""Debounce (ms) of the cheap visibility recompute: filters the already-loaded rows while typing."""
FORCE_FETCH_DELAY = 450
"""Debounce (ms) of the expensive force-fetch: it only fires once the user pauses typing."""
FORCE_FETCH_CONTINUE_INTERVAL = 0
"""Interval (ms) used to continue the force-fetch cascade as freshly fetched children land."""
FORCE_FETCH_MAX_ITERATIONS = 100000
"""Hard upper bound on force-fetch cascade steps; a safety net against a runaway reschedule loop."""


class LevelFilterMixin:
    """Adds per-level regex filter state and a debounced apply to a tree model.

    Each entry in ``LEVEL_ITEM_TYPES`` names a tree level (ordered top to bottom). A subclass must set
    that tuple, provide :meth:`filter_text` (the real text to match a node against) and implement
    :meth:`_apply_level_filters` (the model-specific, batched refresh). Setting or clearing a filter
    schedules two things: a cheap :meth:`_apply_level_filters` on a short single-shot timer so live typing
    filters the already-loaded rows responsively, and - when a *lower* level (below the top one) is
    filtered - an expensive :meth:`_run_force_fetch` on a longer single-shot timer that only fires once the
    user pauses. The force-fetch drives the lazy child fetch under matching parents so collapsed/unfetched
    parents are filtered accurately without the user having to expand them first.
    """

    LEVEL_ITEM_TYPES: tuple[str, ...] = ()
    """Item types that carry a filter cell, ordered top to bottom. Set by the subclass."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._level_patterns: dict[str, str] = {}
        self._level_matchers: dict[str, Callable[[str], bool]] = {}
        self._level_filter_timer = QTimer(self)
        self._level_filter_timer.setSingleShot(True)
        self._level_filter_timer.setInterval(LEVEL_FILTER_INTERVAL)
        self._level_filter_timer.timeout.connect(self._apply_level_filters)
        self._force_fetch_timer = QTimer(self)
        self._force_fetch_timer.setSingleShot(True)
        self._force_fetch_timer.timeout.connect(self._run_force_fetch)
        self._applying_level_filters = False
        self._force_fetching = False
        self._filter_generation = 0
        self._force_fetch_frontier: list | None = None
        self._force_fetch_iterations = 0

    @property
    def filter_generation(self) -> int:
        """A monotonically increasing counter bumped whenever the filtered visibility may have changed.

        Tree items cache their filtered child list keyed on this value: a cache is reused while the counter
        is unchanged and recomputed lazily once it moves. It is bumped both when the level filters are
        (re)applied and on a structural child insert/remove under an active filter.
        """
        return self._filter_generation

    def _bump_filter_generation(self) -> None:
        """Invalidates every item's cached filtered child list by advancing the generation counter."""
        self._filter_generation += 1

    @Slot(str, str)
    def set_level_filter(self, item_type: str, pattern: str) -> None:
        """Sets or clears the regex filter for a tree level and schedules a refresh.

        Args:
            item_type: the level's item type
            pattern: raw regex/substring pattern; an empty string clears the level's filter
        """
        pattern = pattern or ""
        if self._level_patterns.get(item_type, "") == pattern:
            return
        if pattern == "":
            self._level_patterns.pop(item_type, None)
            self._level_matchers.pop(item_type, None)
        else:
            self._level_patterns[item_type] = pattern
            self._level_matchers[item_type] = make_search_matcher(pattern)
        self._reschedule_level_filters()

    def clear_level_filters(self) -> None:
        """Clears all level filters and schedules a refresh."""
        if not self._level_patterns and not self._level_matchers:
            return
        self._level_patterns.clear()
        self._level_matchers.clear()
        self._reschedule_level_filters()

    def _reschedule_level_filters(self) -> None:
        """Restarts both debounces so the latest keystroke wins.

        Any in-flight force-fetch cascade from an earlier keystroke is cancelled (``_force_fetching`` is
        reset) so it cannot fight the new input; the cheap recompute runs soon, the force-fetch only after
        the user pauses.
        """
        self._force_fetching = False
        self._force_fetch_frontier = None
        self._force_fetch_iterations = 0
        self._level_filter_timer.start()
        self._force_fetch_timer.start(FORCE_FETCH_DELAY)

    def _schedule_level_filter_refresh(self) -> None:
        """Reschedules the cheap recompute after a child insert/remove and continues any force-fetch.

        Called from the item insert/remove hooks. The cheap recompute always runs so freshly loaded rows
        are filtered; while a force-fetch cascade is active it is also continued promptly so the next level
        down gets fetched as soon as the current batch lands.
        """
        self._level_filter_timer.start()
        if self._force_fetching:
            self._force_fetch_timer.start(FORCE_FETCH_CONTINUE_INTERVAL)

    def has_level_filters(self) -> bool:
        """Returns whether any level filter is active."""
        return bool(self._level_matchers)

    def level_filter_active(self, item_type: str) -> bool:
        """Returns whether the given level has an active filter.

        Args:
            item_type: the level's item type
        """
        return item_type in self._level_matchers

    def lower_level_filter_active(self) -> bool:
        """Returns whether any filter below the top level is active.

        A lower-level filter is what makes collapsed/unfetched parents relevant: matching leaves may hide
        under parents the user never expanded, so the tree must force-fetch and auto-expand to reveal them.
        """
        return any(self.level_filter_active(t) for t in self.LEVEL_ITEM_TYPES[1:])

    def _deepest_filtered_type(self) -> str | None:
        """Returns the item type of the deepest level that currently has an active filter, or None."""
        deepest_type = None
        for item_type in self.LEVEL_ITEM_TYPES:
            if self.level_filter_active(item_type):
                deepest_type = item_type
        return deepest_type

    def collect_visible_matches(self) -> list:
        """Returns every currently visible real item on the deepest filtered level.

        A single walk over the visible tree, used by the view once the filter has settled to decide whether
        to reveal the matches or collapse (and, when revealing, which branches to expand) - so it does not
        have to walk the tree again separately. The phantom add-row is ignored. With no lower level filtered
        the list is empty.
        """
        deepest_type = self._deepest_filtered_type()
        if deepest_type is None:
            return []
        root = self._level_filter_root()
        if root is None:
            return []
        matches = []
        stack = [root]
        while stack:
            item = stack.pop()
            for child in item.visible_children:
                is_empty_row = getattr(child, "is_empty_row", None)
                if is_empty_row is not None and is_empty_row():
                    continue
                if child.item_type == deepest_type:
                    matches.append(child)
                else:
                    stack.append(child)
        return matches

    def has_visible_match(self) -> bool:
        """Returns whether any real item on the deepest filtered level is currently visible.

        Used by the view to decide, once the filter has settled, whether to expand the tree onto the
        matches or collapse it because nothing matched. With no filter active this is trivially True. The
        phantom add-row is ignored, so an otherwise empty tree does not count as a match.
        """
        if self._deepest_filtered_type() is None:
            return True
        return bool(self.collect_visible_matches())

    def _level_index(self, item) -> int:
        """Returns the item's index within ``LEVEL_ITEM_TYPES``, or -1 for items above the top level.

        Args:
            item: a tree item
        """
        try:
            return self.LEVEL_ITEM_TYPES.index(item.item_type)
        except ValueError:
            return -1

    @Slot()
    def _run_force_fetch(self) -> None:
        """Drives the lazy child fetch so a lower-level filter is accurate across collapsed parents.

        Does nothing unless a lower-level filter is active. Otherwise it walks the tree and fetches every
        item that (a) is not hidden by an upper-level filter and (b) still has children to fetch down to the
        deepest filtered level. Fetching is async and batched, so as children land the insert hook continues
        the cascade (see :meth:`_schedule_level_filter_refresh`) until nothing is left to fetch.
        """
        if self._applying_level_filters:
            self._force_fetch_timer.start(FORCE_FETCH_CONTINUE_INTERVAL)
            return
        if not self.lower_level_filter_active():
            self._force_fetching = False
            return
        self._force_fetching = self._force_fetch_lower_levels()
        if self._force_fetching:
            # Keep driving the cascade until nothing is left to fetch. A fetch that lands no new rows still
            # needs one more pass to flip ``can_fetch_more`` off, and deeper levels only become fetchable
            # once their parents' children have arrived; the batched fetch keeps the UI responsive meanwhile.
            self._force_fetch_timer.start(FORCE_FETCH_CONTINUE_INTERVAL)

    def _force_fetch_lower_levels(self) -> bool:
        """Advances the force-fetch cascade by one step over a frontier of still-fetchable items.

        Instead of re-walking the whole subtree from the root on every 0 ms reschedule (which re-tested
        already-settled branches, making the cascade O(cascade steps x tree size)), this keeps a frontier
        worklist: only items that may still need fetching are examined, and a fetched item's children are
        enqueued once they have arrived. The scoping is unchanged - a child is only visited when it is under
        a parent that passes its own filter, down to the deepest active level - so the cascade fetches
        exactly the same set of branches as before, just without the repeated rescans.

        Returns:
            whether any fetch was issued (i.e. the cascade has not settled yet)
        """
        root = self._level_filter_root()
        if root is None:
            return False
        self._force_fetch_iterations += 1
        if self._force_fetch_iterations > FORCE_FETCH_MAX_ITERATIONS:
            return False
        deepest = max(i for i, t in enumerate(self.LEVEL_ITEM_TYPES) if self.level_filter_active(t))
        if self._force_fetch_frontier is None:
            self._force_fetch_frontier = [root]
        issued = False
        next_frontier = []
        for item in self._force_fetch_frontier:
            is_empty_row = getattr(item, "is_empty_row", None)
            if is_empty_row is not None and is_empty_row():
                continue
            if item is not root and not self.item_passes_own_filter(item):
                continue
            if self._level_index(item) >= deepest:
                continue
            if item.can_fetch_more():
                item.fetch_more()
                issued = True
                # Its children have not landed yet (fetching is async); revisit it next step so the arriving
                # rows get enqueued and its ``can_fetch_more`` flips off exactly once.
                next_frontier.append(item)
            else:
                # Fully fetched: descend so the next level down can be fetched in turn.
                next_frontier.extend(item.children)
        self._force_fetch_frontier = next_frontier
        # The cascade has not settled while a fetch was issued (children still incoming) or the frontier
        # still holds items to descend into. Returning True here keeps ``_run_force_fetch`` rescheduling.
        return issued or bool(next_frontier)

    def _level_filter_root(self):
        """Returns the item whose subtree the force-fetch should walk.

        Implemented by the subclass (the invisible root for the standard trees, the visible root item for
        the entity tree).
        """
        raise NotImplementedError()

    def item_passes_own_filter(self, item) -> bool:
        """Returns whether an item matches the filter of its own level.

        Items on a level with no active filter always pass.

        Args:
            item: a tree item
        """
        matcher = self._level_matchers.get(item.item_type)
        if matcher is None:
            return True
        return matcher(self.filter_text(item))

    def filter_text(self, item) -> str:
        """Returns the real text of a tree item to match its level filter against.

        Args:
            item: a tree item
        """
        raise NotImplementedError()

    def _apply_level_filters(self) -> None:
        """Refreshes the model so the current level filters take effect.

        Implemented by the subclass. It should be guarded with ``self._applying_level_filters`` to
        prevent re-entrancy and emit a single layout change around the refresh.
        """
        raise NotImplementedError()
