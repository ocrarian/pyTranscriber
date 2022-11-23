"""
   (C) 2019 Raryel C. Souza
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from PySide6 import QtCore
from pathlib import Path
from pytranscriber.util.srtparser import SRTParser
from pytranscriber.util.util import MyUtil
from pytranscriber.control.ctr_autosub import Ctr_Autosub
import os


class Thread_Exec_Autosub(QtCore.QThread):
    locking_gui = QtCore.Signal()
    reseting_gui_after_success = QtCore.Signal()
    reseting_gui_after_cancel = QtCore.Signal()
    updateing_progress = QtCore.Signal(str, int)
    updating_file_progress = QtCore.Signal(str)
    sending_message = QtCore.Signal(str)

    def __init__(self, objParamAutosub):
        self.objParamAutosub = objParamAutosub
        self.running = True
        QtCore.QThread.__init__(self)

    def __updateProgressFileYofN(self, currentIndex, countFiles):
        self.updating_file_progress.emit(
            "File " + str(currentIndex + 1) + " of " + str(countFiles)
        )

    def listenerProgress(self, string, percent):
        self.updateing_progress.emit(string, percent)

    def __generatePathOutputFile(self, sourceFile):
        # extract the filename without extension from the path
        base = os.path.basename(sourceFile)
        # [0] is filename, [1] is file extension
        fileName = os.path.splitext(base)[0]

        # the output file has same name as input file, located on output Folder
        # with extension .srt
        pathOutputFolder = Path(self.objParamAutosub.outputFolder)
        outputFileSRT = pathOutputFolder / (fileName + ".srt")
        outputFileTXT = pathOutputFolder / (fileName + ".txt")
        return [outputFileSRT, outputFileTXT]

    def __runAutosubForMedia(self, index, langCode):
        sourceFile = self.objParamAutosub.listFiles[index]
        outputFiles = self.__generatePathOutputFile(sourceFile)
        outputFileSRT = outputFiles[0]
        outputFileTXT = outputFiles[1]

        # run autosub
        fOutput = Ctr_Autosub.generate_subtitles(
            source_path=sourceFile,
            output=outputFileSRT,
            src_language=langCode,
            listener_progress=self.listenerProgress,
        )
        # if nothing was returned
        if not fOutput:
            self.sending_message.emit(
                "error",
                "Error! Unable to generate subtitles for file " + sourceFile + ".",
            )
        elif fOutput != -1:
            # if the operation was not canceled

            # updated the progress message
            self.listenerProgress("Finished", 100)

            # parses the .srt subtitle file and export text to .txt file
            SRTParser.extractTextFromSRT(str(outputFileSRT))

            if self.objParamAutosub.boolOpenOutputFilesAuto:
                # open both SRT and TXT output files
                MyUtil.open_file(outputFileTXT)
                MyUtil.open_file(outputFileSRT)

    def __loopSelectedFiles(self):
        self.locking_gui.emit()

        langCode = self.objParamAutosub.langCode

        # if output directory does not exist, creates it
        pathOutputFolder = Path(self.objParamAutosub.outputFolder)

        if not os.path.exists(pathOutputFolder):
            os.mkdir(pathOutputFolder)
        # if there the output file is not a directory
        if not os.path.isdir(pathOutputFolder):
            # force the user to select a different output directory
            self.sending_message.emit(
                "error", "Error! Invalid output folder. Please choose another one."
            )
        else:
            # go ahead with autosub process
            nFiles = len(self.objParamAutosub.listFiles)
            for i in range(nFiles):
                # does not continue the loop if user clicked cancel button
                if not Ctr_Autosub.is_operation_canceled():
                    self.__updateProgressFileYofN(i, nFiles)
                    self.__runAutosubForMedia(i, langCode)

            # if operation is canceled does not clear the file list
            if Ctr_Autosub.is_operation_canceled():
                self.reseting_gui_after_cancel.emit()
            else:
                self.reseting_gui_after_success.emit()

    def run(self):
        Ctr_Autosub.init()
        self.__loopSelectedFiles()
        self.running = False

    def cancel(self):
        Ctr_Autosub.cancel_operation()
