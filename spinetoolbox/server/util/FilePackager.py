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


    """
    Converts a folder into a ZIP-file
    Args:
        sourceFolder(string): the folder to be included to the ZIP-file
        destinationFolder(string):destination folder of the ZIP-file to be created
        zipFileName(string): name of the ZIP-file to be created
    """
    @staticmethod
    def package(sourceFolder,destinationFolder,zipFileName):

        if destinationFolder==None or zipFileName==None or sourceFolder==None:
            raise ValueError("source folder,destination folder or file name were invalid")

        if len(destinationFolder)==0 or len(zipFileName)==0 or len(sourceFolder)==0:
            raise ValueError("source folder,destination folder or file name were invalid")

        #check if the source folder exists
        if os.path.isdir(sourceFolder)==False:
            raise ValueError("provided sourceFolder doesn't exist.")

        print('FilePackager.package() source folder: %s, dest-folder+file name: %s'%(sourceFolder,destinationFolder+zipFileName,))
        shutil.make_archive(destinationFolder+zipFileName, 'zip', sourceFolder)        


    @staticmethod
    def deleteFile(file):
        """
        Deletes the file at the provided location (includes the folder).
        Args:
            file: File to be deleted. 
        """
         #check input
        if file==None:
            raise ValueError('invalid input to FileExtractor.deleteFile()')
        if len(file)==0:
            raise ValueError('invalid input to FileExtractor.deleteFile()')

        if os.path.exists(file)==False:
            raise ValueError('provided file %s doesn''t exist'%file)  

        os.remove(file) 
        print("FileExtractor.deleteFile(): Removed file: %s"%file)   
