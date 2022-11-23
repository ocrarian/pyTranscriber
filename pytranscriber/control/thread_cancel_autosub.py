from PySide6 import QtCore


class Thread_Cancel_Autosub(QtCore.QThread):
    terminated = QtCore.Signal()

    def __init__(self, pObjWT):
        self.objWT = pObjWT
        QtCore.QThread.__init__(self)

    def run(self):
        self.objWT.cancel()
        self.terminated.emit()
