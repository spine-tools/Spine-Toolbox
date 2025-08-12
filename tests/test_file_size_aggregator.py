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
from spinetoolbox.file_size_aggregator import AggregatorProcess, aggregate_file_sizes
from spinetoolbox.helpers import signal_waiter
from tests.mock_helpers import q_object


class TestAggregatorProcess:
    def test_aggregates_file_sizes(self, application, tmp_path):
        with open(tmp_path / "file", "wb") as file1:
            file1.write(b"xxxxx")
        with q_object(AggregatorProcess(None)) as aggregator:
            with signal_waiter(aggregator.aggregated, timeout=1.0) as waiter:
                aggregator.start_aggregating([tmp_path])
                waiter.wait()
                assert waiter.args == (5,)
            aggregator.tear_down()


class TestAggregateFileSizes:
    def test_empty_directory_aggregates_to_zero_bytes(self, tmp_path):
        assert aggregate_file_sizes(tmp_path) == 0

    def test_returns_file_size_if_path_is_file(self, tmp_path):
        with open(tmp_path / "file1", "wb") as file1:
            file1.write(b"xxx")
        assert aggregate_file_sizes(tmp_path) == 3

    def test_file_sizes_are_summed(self, tmp_path):
        with open(tmp_path / "file1", "wb") as file1:
            file1.write(b"xxx")
        with open(tmp_path / "file2", "wb") as file2:
            file2.write(b"xxxx")
        assert aggregate_file_sizes(tmp_path) == 7

    def test_aggregates_subdirectories(self, tmp_path):
        subdir = tmp_path / "sub"
        subdir.mkdir()
        with open(subdir / "file", "wb") as file1:
            file1.write(b"xxx")
        assert aggregate_file_sizes(tmp_path) == 3
