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

"""Unit tests for the KernelFetcher class."""
import unittest
from PySide6.QtWidgets import QApplication
from spinetoolbox.kernel_fetcher import KernelFetcher
from spinetoolbox.helpers import SignalWaiter


class TestKernelFetcher(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Runs once before any tests in this class."""
        if not QApplication.instance():
            QApplication()

    def test_fetch_all_kernels(self):
        waiter = SignalWaiter()
        kf = KernelFetcher(conda_path="")  # 1: All kernels
        kf.finished.connect(waiter.trigger)
        kf.start()
        waiter.wait()
        kf.finished.disconnect(waiter.trigger)

    def test_fetch_all_python_kernels(self):
        waiter = SignalWaiter()
        kf = KernelFetcher(conda_path="", fetch_mode=2)  # 2: Conda Python and regular Python kernels
        kf.finished.connect(waiter.trigger)
        kf.start()
        waiter.wait()
        kf.finished.disconnect(waiter.trigger)

    def test_fetch_julia_kernels(self):
        waiter = SignalWaiter()
        kf = KernelFetcher(conda_path="", fetch_mode=4)  # 4: Julia kernels
        kf.finished.connect(waiter.trigger)
        kf.start()
        waiter.wait()
        kf.finished.disconnect(waiter.trigger)

    def test_fetch_other_kernels(self):
        waiter = SignalWaiter()
        kf = KernelFetcher(conda_path="", fetch_mode=5)  # 5: Kernels that are neither Python nor Julia
        kf.finished.connect(waiter.trigger)
        kf.start()
        waiter.wait()
        kf.finished.disconnect(waiter.trigger)
