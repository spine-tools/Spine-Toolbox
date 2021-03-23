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

"""
Conda environment widget.

:author: P. Savolainen (VTT)
:date:   19.3.2021
"""
from PySide2.QtWidgets import QWidget
from PySide2.QtCore import Slot, Qt
from spinetoolbox.config import MAINWINDOW_SS
from spinetoolbox.cksm import CondaKernelSpecManager
# import environment_kernels
# from environment_kernels.envs_conda import get_conda_env_data


class CondaEnv(QWidget):
    """Class for a Conda environment editor."""

    def __init__(self, parent):
        """

        Args:
            parent (QWidget): Parent widget (Settings widget)
        """
        from ..ui import conda_env_window  # pylint: disable=import-outside-toplevel

        super().__init__(parent=parent)  # Inherits stylesheet from SettingsWindow
        self.setWindowFlags(Qt.Window)
        self._parent = parent  # QSettingsWidget
        self.ui = conda_env_window.Ui_Form()
        self.ui.setupUi(self)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.connect_signals()
        self.ksm = CondaKernelSpecManager()
        # self.ksm.conda_env_dirs.append("~/.julia/conda/3/envs/")

    def connect_signals(self):
        """Connect signals."""
        self.ui.buttonBox.accepted.connect(self.close)
        self.ui.buttonBox.rejected.connect(self.close)
        self.ui.toolButton_refresh.clicked.connect(self.refresh)

    @Slot(bool)
    def refresh(self, _checked=False):
        kernel_specs = self.ksm.find_kernel_specs()
        print("All specs\n")
        for k, v in kernel_specs.items():
            print(f"{k}: {v}")

        print("\nAll envs\n")
        all_envs = self.ksm._all_envs()
        for k, v in all_envs.items():
            print(f"{k}: {v}")

        print("\nAll specs\n")
        all_specs = self.ksm._all_specs()
        for k, v in all_specs.items():
            print(f"{k}: {v}")

        # kernel_specs_for_envs = self.ksm.find_kernel_specs_for_envs()
        # all_kernel_specs_for_envs = self.ksm.get_all_kernel_specs_for_envs()
        # print("All kernel specs\n")
        # for k, v in all_kernel_specs_for_envs.items():
        #     print(f"{k}: {v.to_dict()}")
        #     print(f"\nenv:{v.env}\n")
        # conda_data = get_conda_env_data(self.ksm)
        # for a, b in conda_data.items():
        #     print(f"{a}: {b}")

    def keyPressEvent(self, e):
        """Close settings form when escape key is pressed.

        Args:
            e (QKeyEvent): Received key press event.
        """
        if e.key() == Qt.Key_Escape:
            self.close()

    def closeEvent(self, e):
        if e:
            e.accept()
