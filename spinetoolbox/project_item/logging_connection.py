######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

from spine_engine.project_item.connection import Connection, Jump
from ..log_mixin import LogMixin
from ..mvcmodels.resource_filter_model import ResourceFilterModel
from ..helpers import busy_effect, fix_lightness_color


class LoggingConnection(LogMixin, Connection):
    def __init__(self, *args, toolbox=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._toolbox = toolbox
        self._active = False
        self.resource_filter_model = ResourceFilterModel(self, toolbox.undo_stack, toolbox)
        self.link = None

    def item_type(self):
        return "connection"

    def refresh_resource_filter_model(self):
        """Makes resource filter mode fetch filter data from database."""
        self.resource_filter_model.build_tree()

    def activate(self):
        self._active = True

    def deactivate(self):
        self._active = False

    @busy_effect
    def set_connection_options(self, options):
        if options == self.options:
            return
        self.options = options
        self.link.update_icon()
        item = self._toolbox.project_item_model.get_item(self.source).project_item
        self._toolbox.project().notify_resource_changes_to_successors(item)
        if self is self._toolbox.active_link_item:
            self._toolbox.link_properties_widgets[LoggingConnection].load_connection_options()


class LoggingJump(LogMixin, Jump):
    def __init__(self, *args, toolbox=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._toolbox = toolbox
        self._active = False
        self.jump_link = None

    def item_type(self):
        return "jump"

    def activate(self):
        self._active = True

    def deactivate(self):
        self._active = False
