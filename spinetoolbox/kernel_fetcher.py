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

"""Contains a class for fetching kernel specs in a thread."""
import os
import json
from PySide6.QtCore import Signal, Slot, QThread
from PySide6.QtGui import QIcon
from jupyter_client.kernelspec import find_kernel_specs
from spine_engine.utils.helpers import resolve_conda_executable
from spine_engine.execution_managers.conda_kernel_spec_manager import CondaKernelSpecManager


class KernelFetcher(QThread):
    """Worker class for retrieving local kernels."""

    kernel_found = Signal(str, str, bool, QIcon, dict)
    stop_fetcher = Signal()

    def __init__(self, conda_path, fetch_mode=1):
        """

        Args:
            conda_path (str): Path to (mini)conda executable
            fetch_mode (int): 1: Fetch all kernels,
              2: Fetch regular and Conda Python kernels,
              3: Fetch only regular Python kernels,
              4: Fetch only regular Julia kernels,
              5: Fetch kernels that are neither Python nor Julia
        """
        super().__init__()
        self.conda_path = conda_path
        self.keep_going = True
        self.fetch_mode = fetch_mode
        self.stop_fetcher.connect(self.stop_thread)

    @Slot()
    def stop_thread(self):
        """Slot for handling a request to stop the thread."""
        self.keep_going = False

    def get_all_regular_kernels(self):
        """Finds all kernel specs as quickly as possible."""
        for kernel_name, resource_dir in find_kernel_specs().items():  # Find regular Kernels
            icon = self.get_icon(resource_dir)
            self.kernel_found.emit(kernel_name, resource_dir, False, icon, {})
            if not self.keep_going:
                return

    def get_all_conda_kernels(self):
        """Finds auto-generated Conda kernels."""
        conda_path = resolve_conda_executable(self.conda_path)
        if conda_path != "":
            cksm = CondaKernelSpecManager(conda_exe=conda_path)
            # Get Conda Kernel names and resource dirs
            for conda_kernel_name, spec_deats in cksm._all_specs().items():  # This is expensive
                rsc_dir = spec_deats.get("resource_dir", "Resource_dir not found")
                icon = self.get_icon(rsc_dir)
                self.kernel_found.emit(conda_kernel_name, rsc_dir, True, icon, {})
                if not self.keep_going:
                    return

    def run(self):
        """Finds kernel specs based on selected fetch mode. Sends found kernels one-by-one via signals."""
        if self.fetch_mode == 1:
            # Find all kernels as quickly as possible
            self.get_all_regular_kernels()
            self.get_all_conda_kernels()
            return
        # To find just a subset of kernels, we need to open kernel.json file and check the language
        for kernel_name, resource_dir in find_kernel_specs().items():
            d = self.get_kernel_deats(resource_dir)
            icon = self.get_icon(resource_dir)
            if d["language"].lower().strip() == "python":  # Regular Python kernel found
                if self.fetch_mode == 2 or self.fetch_mode == 3:
                    self.kernel_found.emit(kernel_name, resource_dir, False, icon, d)
            elif d["language"].lower().strip() == "julia":  # Regular Julia kernel found
                if self.fetch_mode == 4:
                    self.kernel_found.emit(kernel_name, resource_dir, False, icon, d)
            else:  # Some other kernel found
                if self.fetch_mode == 5:
                    self.kernel_found.emit(kernel_name, resource_dir, False, icon, d)
            if not self.keep_going:
                return
        if self.fetch_mode == 2:
            self.get_all_conda_kernels()

    @staticmethod
    def get_icon(p):
        """Retrieves the kernel's icon. First tries to find the .svg icon then .png's.

        Args:
            p (str): Path to Kernel's resource directory

        Returns:
            QIcon: Kernel's icon or a null icon if icon was not found.
        """
        icon_fnames = ["logo-svg.svg", "logo-64x64.png", "logo-32x32.png"]
        for icon_fname in icon_fnames:
            icon_fpath = os.path.join(p, icon_fname)
            if not os.path.isfile(icon_fpath):
                continue
            return QIcon(icon_fpath)
        return QIcon()

    @staticmethod
    def get_kernel_deats(kernel_path):
        """Reads kernel.json from given kernel's resource dir and returns the details in a dictionary.

        Args:
            kernel_path (str): Full path to kernel resource directory

        Returns:
            dict: language (str), path to executable (str), display name (str), project (str) (NA for Python kernels)
        """
        deats = {"language": "", "exe": "", "display_name": "", "project": ""}
        kernel_json = os.path.join(kernel_path, "kernel.json")
        if not os.path.exists(kernel_json):
            return deats
        if os.stat(kernel_json).st_size == 0:  # File is empty
            return deats
        with open(kernel_json, "r") as fh:
            try:
                kernel_dict = json.load(fh)
            except json.decoder.JSONDecodeError:
                return deats
            deats["language"] = kernel_dict.get("language", "")
            try:
                deats["exe"] = kernel_dict.get("argv", "")[0]
            except IndexError:
                pass
            deats["display_name"] = kernel_dict.get("display_name", "")
            try:
                # loop argv and find a string that starts with --project=
                for arg in kernel_dict["argv"]:
                    if arg.startswith("--project="):
                        deats["project"] = arg[10:]
            except (KeyError, IndexError):
                pass
            return deats
