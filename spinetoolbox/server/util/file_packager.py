######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Engine is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Contains a helper class for packaging project folders into ZIP-files.
:authors: P. Pääkkönen (VTT), P. Savolainen (VTT)
:date:   03.09.2021
"""
import shutil
import os


class FilePackager:

    @staticmethod
    def package(src_folder, dst_folder, fname):
        """Converts a folder into a ZIP-file.

        NOTE: Do not use the src_folder as the dst_folder. If the zip-file is
        created to the same directory as root_dir, there will be a  corrupted
        project_package.zip file INSIDE the actual project_package.zip file, which
        makes unzipping the file fail.

        Args:
            src_folder (str): Folder to be included to the ZIP-file
            dst_folder (str): Destination folder for the ZIP-file
            fname (str): Name of the ZIP-file without extension (it's added by shutil.make_archive())
        """
        zip_path = os.path.join(dst_folder, fname)
        try:
            shutil.make_archive(zip_path, "zip", src_folder)
        except OSError:
            raise

    @staticmethod
    def remove_file(file_path):
        """Deletes the given file.

        Args:
            file_path (str): Absolute path to file to be deleted.
        """
        try:
            os.remove(file_path)
        except OSError:
            raise
