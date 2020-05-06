######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Contains utility Data Store's utility functions.

:authors: A. Soininen (VTT)
:date:   6.5.2020
"""
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
import spinedb_api


def convert_to_sqlalchemy_url(urllib_url, item_name, logger, log_errors):
    """Returns a sqlalchemy url from the url or None if not valid."""
    if not urllib_url:
        if log_errors:
            logger.msg_error.emit(f"No URL specified for <b>{item_name}</b>. Please specify one and try again")
        return None
    try:
        url = {key: value for key, value in urllib_url.items() if value}
        dialect = url.pop("dialect")
        if not dialect:
            if log_errors:
                logger.msg_error.emit(
                    f"Unable to generate URL from <b>{item_name}</b> selections: invalid dialect {dialect}. "
                    "<br>Please select a new dialect and try again."
                )
            return None
        if dialect == 'sqlite':
            sa_url = URL('sqlite', **url)  # pylint: disable=unexpected-keyword-arg
        else:
            db_api = spinedb_api.SUPPORTED_DIALECTS[dialect]
            drivername = f"{dialect}+{db_api}"
            sa_url = URL(drivername, **url)  # pylint: disable=unexpected-keyword-arg
    except Exception as e:  # pylint: disable=broad-except
        # This is in case one of the keys has invalid format
        if log_errors:
            logger.msg_error.emit(
                f"Unable to generate URL from <b>{item_name}</b> selections: {e} "
                "<br>Please make new selections and try again."
            )
        return None
    if not sa_url.database:
        if log_errors:
            logger.msg_error.emit(
                f"Unable to generate URL from <b>{item_name}</b> selections: database missing. "
                "<br>Please select a database and try again."
            )
        return None
    # Final check
    try:
        engine = create_engine(sa_url)
        with engine.connect():
            pass
    except Exception as e:  # pylint: disable=broad-except
        if log_errors:
            logger.msg_error.emit(
                f"Unable to generate URL from <b>{item_name}</b> selections: {e} "
                "<br>Please make new selections and try again."
            )
        return None
    return sa_url
