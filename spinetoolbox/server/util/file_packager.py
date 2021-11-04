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
:authors: P. Pääkkönen (VTT)
:date:   03.09.2021
"""
import shutil
import os


class FilePackager:
    """Converts a folder into a ZIP-file

    Args:
        sourceFolder(string): the folder to be included to the ZIP-file
        destinationFolder(string):destination folder of the ZIP-file to be created
        zipFileName(string): name of the ZIP-file to be created
    """

    @staticmethod
    def package(sourceFolder, destinationFolder, zipFileName):
        if not destinationFolder or not zipFileName or not sourceFolder:
            raise ValueError("source folder,destination folder or file name were invalid")
        # check if the source folder exists
        if not os.path.isdir(sourceFolder):
            raise ValueError("provided sourceFolder %s doesn't exist." % sourceFolder)
        zipPath = os.path.join(destinationFolder, zipFileName)
        # print('FilePackager.package() source folder: %s, dest-folder+file name: %s' % (sourceFolder, destinationFolder + zipFileName,))
        print('FilePackager.package() source folder: %s, dest-folder+file name: %s' % (sourceFolder, zipPath))
        # shutil.make_archive(destinationFolder + zipFileName, 'zip', sourceFolder)
        shutil.make_archive(zipPath, 'zip', sourceFolder)

    @staticmethod
    def deleteFile(file):
        """Deletes the file at the provided location (includes the folder).

        Args:
            file: File to be deleted. 
        """
        # check input
        if not file:
            raise ValueError('invalid input to FileExtractor.deleteFile()')
        if not os.path.exists(file):
            raise ValueError("provided file %s doesn't exist" % file)
        os.remove(file)
        print("FileExtractor.deleteFile(): Removed file: %s" % file)
