import os.path
import sys
import pandas as pd
import time
from PyQt6 import QtWidgets, uic, QtCore, QtGui
from wdog import CifWatcher
from gui import Ui_MainWindow
from cif_manager import CifManager
from threading import Thread, Event
from parameters import Settings
from message_viewer import LogMessageViewer
from plotter import Plotter
from crysalis_manager import CrysalisManager
print("test")

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi("gui2.2.ui", self)

        self.logbook = pd.DataFrame()  # logbook data
        self.cif_manager = CifManager()  # Cif manager
        self.settings = Settings()  # Settings
        self.text_browser = LogMessageViewer(self.centralwidget)  # Log Viewer
        self.cif_watcher = CifWatcher(self.text_browser)  # Cif watcher
        self.plt = Plotter()  # Plotly plotter
        self.cm = CrysalisManager(self.text_browser)  # Autoindexer
        self.autoindex_update_calibrations_list()  # Autoindex calibrations

        # Bind buttons
        self.btn_open.clicked.connect(self.select_folder)
        self.btn_scan.clicked.connect(self.start_scan_thread)
        self.btn_save.clicked.connect(self.save_to_file)
        self.btn_live.clicked.connect(self.start_live_thread)
        self.btn_clear.clicked.connect(self.clear_df)
        self.btn_gen_eosfit.clicked.connect(self.generate_eosfit_file)
        self.btn_dist_plot.clicked.connect(lambda: self.plot(sheet="Bonds"))
        self.btn_angle_plot.clicked.connect(lambda: self.plot(sheet="Angles"))
        self.btn_torsion_plot.clicked.connect(lambda: self.plot(sheet="Torsions"))
        self.btn_ai.clicked.connect(self.autoindex)
        self.btn_ai_calibration_save.clicked.connect(self.autoindex_save_calibration)
        self.btn_ai_calibration.clicked.connect(self.autoindex_calibrate)

        # Threading
        self.scan_thread = Thread()
        self.live_thread = Thread()
        self.calibration_thread = Thread()
        self.autoindex_thread = Thread()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.check_thread)
        self.timer.start(500)

    def autoindex(self):
        # Update calibration
        with open(os.path.join("calibrations", self.combox_ai_calibrations.currentText()), "r") as clb_file:
            for line in clb_file.readlines():
                name, x, y = line.split()
                self.cm.calibration[name] = (int(x), int(y))
        # Update speed parameters
        self.cm.action_delay = self.spn_ai_action_delay.value()
        self.cm.dt = self.spn_ai_timeout.value()
        self.cm.um_i = self.chbox_umi.isChecked()
        self.autoindex_thread = Thread(target=self.cm.multi_indexing)
        self.autoindex_thread.start()

    def autoindex_update_calibrations_list(self):
        self.combox_ai_calibrations.clear()
        calibrations = []
        for root, dirs, files in os.walk("calibrations"):
            for file in files:
                if file.endswith(".clb"):
                    calibrations.append(file)
                    self.combox_ai_calibrations.addItem(file)

    def autoindex_calibrate(self):
        self.calibration_thread = Thread(target=self.cm.manual_screen_calibration)
        self.calibration_thread.start()

    def autoindex_save_calibration(self):
        name = self.entr_ai_calib_name.text()
        # Check if the name exists
        if not name:
            self.text_browser.append_log_message("You didn't specify #calibration name", err=True)
            return
        # Check that calibration was done
        elif not all(list(self.cm.calibration.values())):
            self.text_browser.append_log_message("You have to preform calibration procedure at first", err=True)
            return
        # Save calibration
        else:
            with open(os.path.join("calibrations", name + ".clb"), mode="w") as clb_file:
                for key, value in self.cm.calibration.items():
                    clb_file.write(str(key) + " " + str(value[0]) + " " + str(value[1]) + "\n")
            self.text_browser.append_log_message("Calibration was saved", service=True)
            self.autoindex_update_calibrations_list()

    def plot(self, sheet):
        # Connection and check of Excel file
        xl_file = QtWidgets.QFileDialog.getOpenFileName(self, "Chose Excel file")[0]
        if not xl_file:
            self.text_browser.append_log_message("Plotting module → no excel file was chosen", err=True)
            return None
        elif not xl_file.endswith(".xlsx"):
            self.text_browser.append_log_message("Plotting module→the input file should have .xlsx extension", err=True)
            return None

        # Check of plotting options
        path_to_save = ""
        if self.chb_save_indibidual.isChecked():
            path_to_save = QtWidgets.QFileDialog.getExistingDirectory(caption="Chose folder to store individual images")
            if not path_to_save:
                self.text_browser.append_log_message("Plotting module → You didn't specify the folder to store "
                                                     "individual images while using 'save each plot' option", err=True)
                return None

        msg = self.plt.multiple_plot(xl_file, sheet,
                                     frame=self.chb_frame.isChecked(),
                                     grid=self.chb_grid.isChecked(),
                                     bcg=self.chb_bcg.isChecked(),
                                     path=path_to_save)
        if msg.startswith("The figures"):
            self.text_browser.append_log_message(msg, service=True)
        else:
            self.text_browser.append_log_message(msg, err=True)

    def select_folder(self):
        self.settings.path = QtWidgets.QFileDialog.getExistingDirectory()
        self.entr_folder.clear()
        self.entr_folder.insert(self.settings.path)
        self.update_settings()

    def update_settings(self):
        self.settings.exceptions = self.settings.decompose_command(self.entr_excp.text())
        self.settings.requests = self.settings.decompose_command(self.entr_reqst.text())
        self.settings.chemistry = self.settings.decompose_command(self.entr_chem.text())
        self.settings.skip_crys = self.chbox_crys_skip.isChecked()
        self.settings.hyper = self.chbox_hyperlinking.isChecked()
        self.settings.light = self.chbox_highlighting.isChecked()
        self.settings.filter = self.cmbox_htype.currentText()
        self.settings.filter_limit = self.h_value.value()
        self.settings.columns_to_display = self.user_defined_table()
        # self.update_ud_values()

    def update_ud_values(self):
        # Bonds
        self.cif_manager.ud_bonds = self.settings.decompose_ud_parameters(self.bonds_entry.toPlainText())
        if not self.cif_manager.ud_bonds:
            pass
        elif not all(len(bond) == 2 for bond in self.cif_manager.ud_bonds):
            self.text_browser.append_log_message("Bond format error", err=True)
            self.cif_manager.ud_bonds = []

        # Angles
        self.cif_manager.ud_angles = self.settings.decompose_ud_parameters(self.angles_entry.toPlainText())
        if not self.cif_manager.ud_angles:
            pass
        elif not all(len(angle) == 3 for angle in self.cif_manager.ud_angles):
            self.text_browser.append_log_message("Angles format error", err=True)
            self.cif_manager.ud_angles = []

        # Torsions
        self.cif_manager.ud_torsions = self.settings.decompose_ud_parameters(self.torsions_entry.toPlainText())
        if not self.cif_manager.ud_torsions:
            pass
        elif not all(len(torsion) == 4 for torsion in self.cif_manager.ud_torsions):
            self.text_browser.append_log_message("Torsion angles format error", err=True)
            self.cif_manager.ud_torsions = []

        self.cif_manager.default_ud_df()

    def scan_folder(self):
        self.update_ud_values()
        self.settings.split_errors = self.chb_errors.isChecked()
        self.logbook = self.cif_manager.create_static_logbook(self.settings, echo=self.text_browser)

    def save_to_file(self):
        self.update_settings()
        columns_to_drop = list(set(self.logbook.columns.values) - set(self.settings.columns_to_display))
        logbook_to_display = self.logbook.drop(columns_to_drop, axis=1)
        print(logbook_to_display.columns)
        if self.logbook.empty:
            self.text_browser.append_log_message("The data frame is empty → Run the scan first", err=True)
            return None
        try:
            path_to_save = QtWidgets.QFileDialog.getSaveFileName(self, "Save File")
            xl_file = self.cif_manager.save_static_logbook(logbook_to_display,
                                                           os.path.splitext(path_to_save[0])[0],
                                                           split_errors=self.settings.split_errors)
        except:
            self.text_browser.append_log_message("Excel connection failed → excel is probably open."
                                                 " Close it and try again", err=True)
            return None

        from exceler import format_table
        format_thread = Thread(target=format_table, daemon=True, args=[xl_file, self.settings])
        format_thread.start()

    def start_scan_thread(self):
        self.update_settings()
        if self.settings.path == "":
            self.text_browser.append_log_message("Scan error → You didn't choose any folder to scan", err=True)
            return None
        # self.scan_thread = Thread(target=self.scan_folder, daemon=True)
        self.scan_thread = Thread(target=self.scan_folder)
        self.scan_thread.start()

    def start_live_thread(self):
        self.update_settings()
        if self.settings.path == "":
            self.text_browser.append_log_message("Live mode → You didn't specify folder to scan", err=True)
            return None
        self.stop_event = Event()
        self.live_thread.is_alive()
        if self.live_thread.is_alive():
            self.cif_watcher.q.put("STOP")
            self.cif_watcher.wdog_stop_event.set()
            self.stop_event.set()
        else:
            # Create default style Excel file
            path_to_save = QtWidgets.QFileDialog.getSaveFileName(self, "Save File")
            if os.path.isfile(path_to_save[0]):  # Check if the file already exists
                self.cif_watcher.xl = path_to_save[0]
            elif not os.path.isfile(path_to_save[0]) and path_to_save[0] != "":  # Create if not existed
                # Filter not checked columns
                columns_to_drop = list(set(self.cif_manager.default_df.columns.values) -
                                       set(self.settings.columns_to_display))
                default_cif_logbook = self.cif_manager.default_df.drop(columns_to_drop, axis=1)

                # Create file with default logbook
                abs_path = self.cif_manager.save_static_logbook(default_cif_logbook,
                                                                os.path.splitext(path_to_save[0])[0])
                self.cif_watcher.xl = abs_path
            else:  # File dialog was closed
                return None
            self.live_thread = Thread(target=self.start_live)
            self.live_thread.start()

    def start_live(self):
        self.text_browser.append_log_message("... Start watching ...", service=True)
        self.update_settings()
        self.cif_watcher.initiate(self.settings)
        while not self.stop_event.is_set():
            time.sleep(1)
        self.text_browser.append_log_message("... Stop watching ...", service=True)

    def check_thread(self):
        # Scan thread is active
        if self.scan_thread.is_alive():
            self.btn_scan.setEnabled(False)
        else:
            self.btn_scan.setEnabled(True)
        # Live thread is active
        if self.live_thread.is_alive():
            self.btn_scan.setEnabled(False)
            self.btn_open.setEnabled(False)
            self.btn_save.setEnabled(False)
            self.btn_live.setStyleSheet("background-color : lightgreen")
        else:
            self.btn_live.setStyleSheet("background-color : lightgrey")
            self.btn_scan.setEnabled(True)
            self.btn_open.setEnabled(True)
            self.btn_save.setEnabled(True)

        # Auto indexer calibration thread
        if self.calibration_thread.is_alive():
            self.btn_ai_calibration.setEnabled(False)
            self.btn_ai_calibration_save.setEnabled(False)
            self.btn_ai.setEnabled(False)
        else:
            self.btn_ai_calibration.setEnabled(True)
            self.btn_ai_calibration_save.setEnabled(True)
            self.btn_ai.setEnabled(True)

        # Auto indexer main thread
        if self.autoindex_thread.is_alive():
            self.btn_ai_calibration.setEnabled(False)
            self.btn_ai_calibration_save.setEnabled(False)
            self.btn_ai.setEnabled(False)
        else:
            self.btn_ai_calibration.setEnabled(True)
            self.btn_ai_calibration_save.setEnabled(True)
            self.btn_ai.setEnabled(True)

    def user_defined_table(self):
        columns_to_display = ["Filename"]
        if self.chb_formula.isChecked():
            columns_to_display.extend(["Formula"])
        if self.chb_cs.isChecked():
            columns_to_display.extend(["CS"])
        if self.chb_sg.isChecked():
            columns_to_display.extend(["SG"])
        if self.chb_rint.isChecked():
            columns_to_display.extend(["Rint"])
        if self.chb_r1.isChecked():
            columns_to_display.extend(["R1"])
        if self.chb_wr2.isChecked():
            columns_to_display.extend(["wR2"])
        if self.chb_abc.isChecked():
            columns_to_display.extend(["a(\u212B)", "b(\u212B)", "c(\u212B)"])
        if self.chb_angles.isChecked():
            columns_to_display.extend(["\u03B1(\u00b0)", "\u03B2(\u00b0)", "\u03B3(\u00b0)"])
        if self.chb_volume.isChecked():
            columns_to_display.extend(["V(" + u"\u212B^3)"])
        if self.chb_z.isChecked():
            columns_to_display.extend(["Z"])
        if self.chb_refl_all.isChecked():
            columns_to_display.extend(["N_all."])
        if self.chb_refl_obs.isChecked():
            columns_to_display.extend(["N_obs"])
        if self.chb_program.isChecked():
            columns_to_display.extend(["Program"])
        if self.chb_absorp.isChecked():
            columns_to_display.extend(["Abs.cor."])
        if self.chb_um.isChecked():
            columns_to_display.extend(["UM"])
        if self.chb_errors.isChecked():
            columns_to_display.extend(["\u0394a(\u212B)", "\u0394b(\u212B)", "\u0394c(\u212B)",
                                       "\u0394\u03B1(\u00b0)", "\u0394\u03B2(\u00b0)", "\u0394\u03B3(\u00b0)",
                                       "\u0394V" + "(\u212B^3)"])
        return columns_to_display

    def clear_df(self):
        self.text_browser.append_log_message("The data frame was cleared", service=True)
        self.logbook = self.logbook[0:0]
        self.cif_manager.ud_bonds = []
        self.cif_manager.ud_angles = []
        self.cif_manager.ud_torsions = []
        self.cif_manager.angles_df = pd.DataFrame()
        self.cif_manager.bonds_df = pd.DataFrame()
        self.cif_manager.torsions_df = pd.DataFrame()

    def generate_eosfit_file(self):
        from exceler import generate_eosfit_input
        # Chose excel file
        xl_file = QtWidgets.QFileDialog.getOpenFileName(self, "Chose Excel file")[0]
        if not xl_file:
            self.text_browser.append_log_message("No Excel file chosen", err=True)
            return None
        # Check extension of .xlsx file
        if not xl_file.endswith(".xlsx"):
            self.text_browser.append_log_message("Excel file should have .xlsx extension", err=True)
            return None
        # Choose .dat file
        output = QtWidgets.QFileDialog.getSaveFileName(self, "Create new .dat file for EOSfit")[0]
        if not output:
            self.text_browser.append_log_message("You didn't chose any file", err=True)
            return None
        # Check extension of .dat file
        if not output.endswith(".dat"):
            self.text_browser.append_log_message("EoSfit input file should have .dat extension", err=True)
            return None
        # Create input file
        msg = generate_eosfit_input(xl_file, output)
        if msg.startswith("The EoSFit input"):
            self.text_browser.append_log_message(msg, service=True)
        else:
            self.text_browser.append_log_message(msg, service=True)


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
