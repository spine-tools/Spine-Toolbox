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

"""Contains functions for automatically generating scenarios from a set of alternatives."""
from itertools import compress, permutations


def all_combinations(alternatives):
    """Creates all possible combinations of alternatives.

    Args:
        alternatives (Iterable of Any): alternatives

    Returns:
        list of list: lists containing alternatives for each scenario
    """
    count = len(alternatives)
    proto_selection = count * [False]
    scenarios = []
    for i in range(count):
        proto_selection[i] = True
        if i != count - 1:
            selections = set(permutations(proto_selection, count))
        else:
            selections = (proto_selection,)
        for selection in selections:
            scenarios.append(list(compress(alternatives, selection)))
    return scenarios


def unique_alternatives(alternatives):
    """Creates all possible single-alternative scenarios.

    Args:
        alternatives (Iterable of Any): alternatives

    Returns:
        list of list: tuples containing alternatives for each scenario
    """
    return [[alternative] for alternative in alternatives]
