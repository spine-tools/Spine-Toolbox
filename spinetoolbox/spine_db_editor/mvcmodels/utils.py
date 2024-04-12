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

"""General helper functions and classes for DB editor's models."""
import csv
from io import StringIO


def two_column_as_csv(indexes):
    """Writes data in given indexes into a CSV table.

    Expects the source table to have two columns.

    Args:
        indexes (Sequence of QModelIndex): model indexes

    Returns:
        str: data as CSV table
    """
    first_column = indexes[0].column()
    single_column = all(i.column() == first_column for i in indexes[1:])
    with StringIO(newline="") as out:
        writer = csv.writer(out, delimiter="\t", quotechar="'")
        rows = {}
        for index in indexes:
            if single_column:
                rows[index.row()] = [index.data()]
            else:
                rows.setdefault(index.row(), ["", ""])[index.column()] = index.data()
        for row in sorted(rows):
            content = rows[row]
            writer.writerow(content)
        return out.getvalue()
