"""Main window for GUI."""
import os
from pathlib import Path

# TODO: Config and enable internationalization.
from gettext import gettext as _

from PySide6 import QtCore
from PySide6 import QtWidgets

# from pytranscriber.model.param_autosub import Param_Autosub
# from pytranscriber.util.util import MyUtil

# from pytranscriber.control.thread_exec_autosub import Thread_Exec_Autosub
# from pytranscriber.control.thread_cancel_autosub import Thread_Cancel_Autosub
from . import data


class MainWindow(QtWidgets.QMainWindow):
    """Main window."""

    def __init__(self) -> None:
        """Config window and initialize base components."""
        super().__init__()

        self.resize(900, 450)
        self.setWindowTitle(_("Name"))

        main_panel = MainPanel()

        self.setCentralWidget(main_panel)


class MainPanel(QtWidgets.QWidget):
    """Central widget for the main window."""

    def __init__(self) -> None:
        """Initialize base components."""
        super().__init__()

        main_layout = QtWidgets.QVBoxLayout(self)

        # Where you can select files, remove files and view them is a list.
        upper_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(upper_layout)

        # Where the select and remove buttons are located.
        files_controls_layout = QtWidgets.QVBoxLayout()
        files_controls_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        upper_layout.addLayout(files_controls_layout)

        # The Select File(s) button.
        self.__b_select_files = QtWidgets.QPushButton(_("&Select File(s)"))
        self.__b_select_files.setFixedSize(150, 35)
        files_controls_layout.addWidget(self.__b_select_files)
        self.__b_select_files.clicked.connect(self.__listener_selecting_files)

        # The Remove File(s) button.
        self.__b_remove_files = QtWidgets.QPushButton(_("&Remove File(s)"))
        self.__b_remove_files.setFixedSize(150, 35)
        self.__b_remove_files.setDisabled(True)
        files_controls_layout.addWidget(self.__b_remove_files)
        self.__b_remove_files.clicked.connect(self.__listener_removing_files)

        # Where the files list and it's description are located.
        files_list_layout = QtWidgets.QVBoxLayout()
        upper_layout.addLayout(files_list_layout)

        # The files list description.
        files_list_layout.addWidget(
            QtWidgets.QLabel(
                _("List of files to generate transcribe audio / generate subtitles")
            )
        )

        # The files list.
        self.__selected_files_list = QtWidgets.QListWidget()
        self.__selected_files_list.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection
        )
        files_list_layout.addWidget(self.__selected_files_list)

        # A spacer
        main_layout.addItem(QtWidgets.QSpacerItem(0, 10))

        # Where you can select an output directory
        output_directory_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(output_directory_layout)

        b_select_output = QtWidgets.QPushButton(_("Output Directory"))
        b_select_output.setFixedSize(150, 35)
        output_directory_layout.addWidget(b_select_output)
        b_select_output.clicked.connect(self.__listener_selecting_output_directory)

        self.__output_directory = QtWidgets.QLineEdit()
        self.__output_directory.setReadOnly(True)
        self.__output_directory.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        # TODO: Implement a click action.
        self.__output_directory.setToolTip(_("Click to open directory"))
        output_directory_layout.addWidget(self.__output_directory)
        # Default output directory.
        self.__output_directory.setText(str(Path.home()))

        auto_open_output = QtWidgets.QCheckBox(_("Auto open"))
        auto_open_output.setToolTip(_("Open output files automatically"))
        auto_open_output.setChecked(True)
        output_directory_layout.addWidget(auto_open_output)

        # A spacer
        main_layout.addItem(QtWidgets.QSpacerItem(0, 15))

        # Where you can select audio language.
        # TODO: Implement per file audio language.
        audio_lang_layout = QtWidgets.QHBoxLayout()
        audio_lang_layout.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addLayout(audio_lang_layout)

        audio_lang_layout.addWidget(QtWidgets.QLabel(_("Audio Language")))

        self.__audio_lang = QtWidgets.QComboBox()
        self.__audio_lang.addItems(data.languages)
        self.__audio_lang.setMaximumWidth(self.__audio_lang.minimumSizeHint().width())
        audio_lang_layout.addWidget(self.__audio_lang)

        # A spacer
        main_layout.addItem(QtWidgets.QSpacerItem(0, 20))

        # A button to run the generator
        self.__b_run_generator = QtWidgets.QPushButton(
            _("Transcribe Audio / Generate Subtitles")
        )
        self.__b_run_generator.setFixedHeight(35)
        self.__b_run_generator.setDisabled(True)
        main_layout.addWidget(self.__b_run_generator, alignment=QtCore.Qt.AlignCenter)

        # A spacer
        main_layout.addItem(QtWidgets.QSpacerItem(0, 20))

        # A progress bar
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)

        self.progress_bar_description = QtWidgets.QLabel()
        main_layout.addWidget(self.progress_bar_description)

    def __listener_selecting_files(self) -> None:
        """Get files, check if they was selected before then add them to the list."""
        files, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self,
            caption="Select media",
            filter="All Media Files (*.mp3 *.mp4 *.wav *.m4a *.wma)",
        )

        if files:
            current_files_list = tuple(
                self.__selected_files_list.item(i).text()
                for i in range(self.__selected_files_list.count())
            )

            for file in files:
                if file not in current_files_list:
                    self.__selected_files_list.addItem(file)

            # Enable those buttons only if list of files is not empty.
            # No problem if selected files were duplicates, since the list is not empty.
            self.__b_run_generator.setEnabled(True)
            self.__b_remove_files.setEnabled(True)

    def __listener_removing_files(self) -> None:
        for item in self.__selected_files_list.selectedItems():
            self.__selected_files_list.takeItem(self.__selected_files_list.row(item))

        if self.__selected_files_list.count() == 0:
            # If no items left disables those buttons
            self.__b_remove_files.setEnabled(False)
            self.__b_run_generator.setEnabled(False)

    def __listener_selecting_output_directory(self) -> None:
        selected_directory = QtWidgets.QFileDialog.getExistingDirectory(
            self, caption="Select output directory", dir=self.__output_directory.text()
        )

        if selected_directory:
            self.__output_directory.setText(selected_directory)

    # TODO
    # def __listener_opening_output_directory(self) -> None:
    #         MyUtil.open_file(pathOutputFolder)


def main() -> int:
    """Start the GUI."""
    app = QtWidgets.QApplication([])
    window = MainWindow()
    window.show()
    return app.exec()
