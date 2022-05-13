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
    def package(src_folder, dst_folder, zip_file_name):
        """Converts a folder into a ZIP-file

        Args:
            src_folder (string): Folder to be included to the ZIP-file
            dst_folder (string): Destination folder of the ZIP-file to be created
            zip_file_name (string): Name of the ZIP-file without extension (it's added by shutil.make_archive())
        """
        if not dst_folder or not zip_file_name or not src_folder:
            raise ValueError("source folder, destination folder or file name were invalid")
        # check if the source folder exists
        if not os.path.isdir(src_folder):
            raise ValueError(f"provided src_folder {src_folder} doesn't exist")
        # Use parent dir of project directory as destination directory
        # If zip-file is created to the same directory as root_dir,
        # there's a corrupted project_package.zip inside the actual project_package.zip file, which
        # makes unzipping the file fail.
        # TODO: Find a better dst dir and handle what happens if file already exists. Or use a temp dir
        dst_folder = os.path.join(dst_folder, os.pardir)
        zip_path = os.path.join(dst_folder, zip_file_name)
        shutil.make_archive(zip_path, "zip", src_folder)
        if os.path.isfile(zip_path + ".zip"):  # Extension is added by make_archive
            print(f"FilePackager.package() ZIP-file created: {zip_path + '.zip'}")
        else:
            print(f"FilePackager.package() Error in creating ZIP-file. src_folder:{src_folder}, dest_file:{zip_path}")

    @staticmethod
    def deleteFile(file):
        """Deletes the file at the provided location (includes the folder).

        Args:
            file: File to be deleted. 
        """
        # check input
        if not file:
            raise ValueError('invalid input to FilePackager.deleteFile()')
        if not os.path.exists(file):
            raise ValueError("provided file %s doesn't exist" % file)
        os.remove(file)
        print("FilePackager.deleteFile(): Removed file: %s" % file)
