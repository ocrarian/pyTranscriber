"""Main window for GUI."""
# TODO: Config and enable internationalization.
from gettext import gettext as _
from pathlib import Path
from typing import Optional

from PySide6 import QtCore
from PySide6 import QtWidgets

from pytranscriber.control.thread_cancel_autosub import Thread_Cancel_Autosub
from pytranscriber.control.thread_exec_autosub import Thread_Exec_Autosub
from pytranscriber.model.param_autosub import Param_Autosub
from pytranscriber.util.util import MyUtil

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

        self.__b_select_output = QtWidgets.QPushButton(_("Output Directory"))
        self.__b_select_output.setFixedSize(150, 35)
        output_directory_layout.addWidget(self.__b_select_output)
        self.__b_select_output.clicked.connect(
            self.__listener_selecting_output_directory
        )

        self.__output_directory = QtWidgets.QLineEdit()
        self.__output_directory.setReadOnly(True)
        self.__output_directory.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        # TODO: Implement a click action.
        self.__output_directory.setToolTip(_("Click to open directory"))
        output_directory_layout.addWidget(self.__output_directory)
        # Default output directory.
        self.__output_directory.setText(str(Path.home()))

        self.__chbx_auto_open_output = QtWidgets.QCheckBox(_("Auto open"))
        self.__chbx_auto_open_output.setToolTip(_("Open output files automatically"))
        self.__chbx_auto_open_output.setChecked(True)
        output_directory_layout.addWidget(self.__chbx_auto_open_output)

        # A spacer
        main_layout.addItem(QtWidgets.QSpacerItem(0, 15))

        # Where you can select audio language.
        audio_lang_layout = QtWidgets.QHBoxLayout()
        audio_lang_layout.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addLayout(audio_lang_layout)

        audio_lang_layout.addWidget(QtWidgets.QLabel(_("Audio Language")))

        self.__cobx_audio_lang = QtWidgets.QComboBox()
        self.__cobx_audio_lang.addItems(data.languages)
        self.__cobx_audio_lang.setMaximumWidth(
            self.__cobx_audio_lang.minimumSizeHint().width()
        )
        audio_lang_layout.addWidget(self.__cobx_audio_lang)

        # TODO: Add combobox for selecting a generator.

        # A spacer
        main_layout.addItem(QtWidgets.QSpacerItem(0, 20))

        # A button to run the generator
        self.__b_run_generator = QtWidgets.QPushButton(
            _("Transcribe Audio / Generate Subtitles")
        )
        self.__b_run_generator.setFixedHeight(35)
        self.__b_run_generator.setDisabled(True)
        main_layout.addWidget(self.__b_run_generator, alignment=QtCore.Qt.AlignCenter)
        self.__b_run_generator.clicked.connect(self.__listener_running_generator)

        self.__b_cancel_generator = QtWidgets.QPushButton(_("Cancel Operation"))
        self.__b_cancel_generator.setFixedHeight(35)
        self.__b_cancel_generator.hide()
        main_layout.addWidget(
            self.__b_cancel_generator, alignment=QtCore.Qt.AlignCenter
        )
        self.__b_cancel_generator.clicked.connect(self.__listener_cancel_generator)

        # A spacer
        main_layout.addItem(QtWidgets.QSpacerItem(0, 20))

        # A progress bar
        self.__progress_bar = QtWidgets.QProgressBar()
        self.__progress_bar.setValue(0)
        main_layout.addWidget(self.__progress_bar)

        progress_bar_description_layout = QtWidgets.QHBoxLayout()
        progress_bar_description_layout.setAlignment(QtCore.Qt.AlignLeft)
        main_layout.addLayout(progress_bar_description_layout)

        self.__current_file_progress_lable = QtWidgets.QLabel()
        progress_bar_description_layout.addWidget(self.__current_file_progress_lable)
        self.__current_operation_progress_lable = QtWidgets.QLabel()
        progress_bar_description_layout.addWidget(
            self.__current_operation_progress_lable
        )

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
        """Get selected files then delete them and disable buttons if list is empty."""
        for item in self.__selected_files_list.selectedItems():
            self.__selected_files_list.takeItem(self.__selected_files_list.row(item))

        if self.__selected_files_list.count() == 0:
            # If no items left disables those buttons
            self.__b_remove_files.setEnabled(False)
            self.__b_run_generator.setEnabled(False)

    def __listener_selecting_output_directory(self) -> None:
        """Get an output directory from the user and display it."""
        selected_directory = QtWidgets.QFileDialog.getExistingDirectory(
            self, caption="Select output directory", dir=self.__output_directory.text()
        )

        if selected_directory:
            self.__output_directory.setText(selected_directory)

    # TODO:
    # def __listener_opening_output_directory(self) -> None:
    #         MyUtil.open_file(pathOutputFolder)

    def __listener_reseting_gui_after_success(self):
        """Clear list and enable buttons after success."""
        self.__selected_files_list.clear()

        self.__listener_reseting_gui_after_cancel()

    def __listener_reseting_gui_after_cancel(self):
        """Reset progress bar and enable buttons after canceling the operation."""
        self.__reset_progressbar()

        self.__b_select_files.setEnabled(True)
        self.__b_select_output.setEnabled(True)
        self.__cobx_audio_lang.setEnabled(True)
        self.__chbx_auto_open_output.setEnabled(True)
        self.__b_run_generator.setEnabled(True)
        self.__b_remove_files.setEnabled(True)

    def __listener_locking_buttons_during_operation(self):
        """Disable buttons when there is a running operation."""
        self.__b_run_generator.setEnabled(False)
        self.__b_remove_files.setEnabled(False)
        self.__b_select_files.setEnabled(False)
        self.__b_select_output.setEnabled(False)
        self.__cobx_audio_lang.setEnabled(False)
        self.__chbx_auto_open_output.setEnabled(False)

        QtCore.QCoreApplication.processEvents()

    def __listener_updateing_progress(self, string: str, percentage: int):
        """When there is a progress update display it in the GUI."""
        self.__current_operation_progress_lable.setText(string)
        self.__progress_bar.setValue(percentage)
        QtCore.QCoreApplication.processEvents()

    def __listener_updating_file_progress(self, string: str):
        """Update the GUI to display which file it currently being processed."""
        self.__current_file_progress_lable.setText(string)
        QtCore.QCoreApplication.processEvents()

    def __set_progress_indefinite(self):
        """Make the progress bar indefinite by making no minimum or maximum value."""
        self.__progress_bar.setMinimum(0)
        self.__progress_bar.setMaximum(0)

    def __reset_progressbar(self):
        """Reset the progress bar to its default status."""
        self.__progress_bar.setMinimum(0)
        self.__progress_bar.setMaximum(100)
        self.__listener_updateing_progress("", 0)

    def __show_message(
        self, message_type: str, text: str, title: Optional[str] = None
    ) -> int:
        if message_type == "info":
            message = QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Information, title, text
            )
        elif message_type == "error":
            message = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Critical, title, text)
        else:
            raise TypeError(f'No message type called "{message_type}" is available.')

        return message.exec()

    def __toggle_generate_cancel_button(self):
        if self.__b_run_generator.isHidden():
            self.__b_run_generator.setHidden(False)
            self.__b_cancel_generator.setHidden(True)
        else:
            self.__b_run_generator.setHidden(True)
            self.__b_cancel_generator.setHidden(False)

    def __listener_running_generator(self):
        # TODO: Check for the selected service.
        if not MyUtil.able_to_access_service():
            self.__show_message(
                "error",
                _(
                    "Error! Cannot reach Google Speech Servers.\n\n"
                    + "1) Make sure you are connected to the internet.\n"
                    + "2) If you are connected to a network that blocks "
                    + "access to Google servers: please install and enable a "
                    + "desktop-wide VPN app like ProtonVPN or Windscribe "
                    + "then try again."
                ),
            )
            return None

        # Execute the main job in a separate thread to avoid gui being locked.
        self.thread_exec = Thread_Exec_Autosub(
            Param_Autosub(
                tuple(
                    self.__selected_files_list.item(i).text()
                    for i in range(self.__selected_files_list.count())
                ),
                self.__output_directory.text(),
                # Extract language code from text displayed in the combobox.
                self.__cobx_audio_lang.currentText().split(" ")[0],
                self.__chbx_auto_open_output.isChecked(),
            )
        )

        # Connect signals from thread to GUI actions.
        self.thread_exec.locking_gui.connect(
            self.__listener_locking_buttons_during_operation
        )
        self.thread_exec.reseting_gui_after_success.connect(
            self.__listener_reseting_gui_after_success
        )
        self.thread_exec.reseting_gui_after_cancel.connect(
            self.__listener_reseting_gui_after_cancel
        )
        self.thread_exec.updateing_progress.connect(self.__listener_updateing_progress)
        self.thread_exec.updating_file_progress.connect(
            self.__listener_updating_file_progress
        )
        self.thread_exec.sending_message.connect(self.__show_message)
        self.thread_exec.start()

        # Show cancel button insted of generate button.
        self.__toggle_generate_cancel_button()

    def __listener_cancel_generator(self):
        # Show generate button insted of cancel button.
        self.__toggle_generate_cancel_button()

        self.thread_cancel = Thread_Cancel_Autosub(self.thread_exec)

        # Only if worker thread is running.
        if self.thread_exec and self.thread_exec.isRunning():
            self.__listener_updateing_progress(_("Cancelling..."), 0)
            self.__listener_updating_file_progress("")
            self.__set_progress_indefinite()

            # Connect termination signal to reset the GUI.
            self.thread_cancel.terminated.connect(
                self.__listener_reseting_gui_after_cancel
            )

            # Run the cancel operation in new thread to avoid freezing the GUI.
            self.thread_cancel.start()
            self.thread_exec = None


def main() -> int:
    """Start the GUI."""
    app = QtWidgets.QApplication([])
    window = MainWindow()
    window.show()
    return app.exec()
