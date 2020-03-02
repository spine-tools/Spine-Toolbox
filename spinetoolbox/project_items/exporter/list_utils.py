######################################################################################################################
# Copyright (C) 2017-2019 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Contains list helper functions for list manipulation.

:author: A. Soininen (VTT)
:date:   12.12.2019
"""

from PySide2.QtCore import QModelIndex


def move_list_elements(originals, first, last, target):
    """
    Moves elements in a list.

    Args:
        originals (list): a list
        first (int): index of the first element to move
        last (int): index of the last element to move
        target (int): index where the elements `[first:last]` should be inserted

    Return:
        a new list with the elements moved
    """
    trashable = list(originals)
    elements_to_move = list(originals[first : last + 1])
    del trashable[first : last + 1]
    elements_that_come_before = trashable[:target]
    elements_that_come_after = trashable[target:]
    brave_new_list = elements_that_come_before + elements_to_move + elements_that_come_after
    return brave_new_list


def move_selected_elements_by(list_view, delta):
    """
    Moves selected items in a QListView by given delta.

    Args:
        list_view (QListView): a list view
        delta (int): positive values move the items up, negative down
    """
    selection_model = list_view.selectionModel()
    selected_rows = sorted(selection_model.selectedRows())
    if not selected_rows:
        return
    first_row = selected_rows[0].row()
    contiguous_selections = [[first_row, 1]]
    current_contiguous_chunk = contiguous_selections[0]
    for row in selected_rows[1:]:
        if row == current_contiguous_chunk[0] + 1:
            current_contiguous_chunk[1] += 1
        else:
            contiguous_selections.append((row, 1))
            current_contiguous_chunk = contiguous_selections[-1]
    model = list_view.model()
    for chunk in contiguous_selections:
        model.moveRows(QModelIndex(), chunk[0], chunk[1], QModelIndex(), chunk[0] + delta)
