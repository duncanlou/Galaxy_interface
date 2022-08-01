import sys
import ast

from PyQt5 import uic
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtSql import QSqlQuery, QSqlDatabase
from PyQt5.QtWidgets import *
from astropy.io import fits
from matplotlib.backends.backend_qtagg import (
    FigureCanvasQTAgg)
from matplotlib.figure import Figure

IMAGE_PATH_BEAMS = "data/beams"
IMAGE_PATH_SYNTHESIS = "data/synthesis"
IMAGE_PATH_SDSS = "data/SDSS"


class MplCanvas(FigureCanvasQTAgg):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""

    def __init__(self, parent, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, constrained_layout=True)
        self.axes = self.fig.add_subplot(111)
        super(MplCanvas, self).__init__(self.fig)

    def plot_beams(self, file_path):
        with fits.open(file_path) as hdu:
            freq = hdu[1].data['freq']
            TABL = hdu[1].data['TABL']

        self.axes.plot(freq, TABL)
        print(type(self.fig.canvas))
        self.fig.canvas.draw()


    def plot_synthesis(self, file_path):
        with fits.open(file_path) as hdu:
            freq = hdu[1].data['freq']
            FLUXBL = hdu[1].data['FLUXBL']
        self.axes.plot(freq, FLUXBL)
        self.fig.canvas.draw()

    def plot_SDSS(self, data):
        pass


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi("mainwindow.ui", self)
        self.setWindowTitle("Galaxy Inspector")
        self.moveWindowToScreenCenter()
        self.dbQuery = QSqlQuery(QSqlDatabase.database())
        self.current_galaxy = self.next_db_entry()
        self.init_widgets()
        self.plot_images(self.current_galaxy)

    def moveWindowToScreenCenter(self):
        qtRectangle = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())

    def init_widgets(self):
        self.initPlotWidget()
        self.setRadioButtons()
        self.setBeamGroupBoxVisibility()

        self.btn_next = self.findChild(QPushButton, "btn_next")
        self.btn_next.clicked.connect(self.go_to_next_galaxy)

    @pyqtSlot()
    def go_to_next_galaxy(self):
        button = QMessageBox.question(self, "Save Results", "Do you want to save your selection?")
        if button == QMessageBox.Yes:
            self.save_results()
            self.del_current_galaxy_from_database()
            self.current_galaxy = self.next_db_entry()
            self.setBeamGroupBoxVisibility()
            self.plot_images(self.current_galaxy)

        else:
            print("No!")

        # # 设置下一个Galaxy页面的radio button的初始状态
        # self.setRadioButtons()

    def save_results(self):
        beam1, beam2, beam3, beam4, synthesis = self.getUserResults()
        print("用户选择结果：", beam1, beam2, beam3, beam4, synthesis)
        # save user selection to database
        user_inspection_query = QSqlQuery()
        user_inspection_query.prepare("""
            INSERT INTO results (
                galaxy_name,
                beam1_rfi_flag,
                beam1_ripple_flag,
                beam2_rfi_flag,
                beam2_ripple_flag,
                beam3_rfi_flag,
                beam3_ripple_flag,
                beam4_rfi_flag,
                beam4_ripple_flag,
                synthesis_signal_flag,
                synthesis_baseline_flag
                )
            VALUES (:galaxy_name,:beam1_rfi_flag,:beam1_ripple_flag,:beam2_rfi_flag,:beam2_ripple_flag,:beam3_rfi_flag,:beam3_ripple_flag,:beam4_rfi_flag,:beam4_ripple_flag,:synthesis_signal_flag,:synthesis_baseline_flag)
            """)
        user_inspection_query.bindValue(":galaxy_name", self.current_galaxy["galaxy_name"])
        user_inspection_query.bindValue(":beam1_rfi_flag", beam1[0])
        user_inspection_query.bindValue(":beam1_ripple_flag", beam1[1])
        user_inspection_query.bindValue(":beam2_rfi_flag", beam2[0])
        user_inspection_query.bindValue(":beam2_ripple_flag", beam2[1])
        user_inspection_query.bindValue(":beam3_rfi_flag", beam3[0])
        user_inspection_query.bindValue(":beam3_ripple_flag", beam3[1])
        user_inspection_query.bindValue(":beam4_rfi_flag", beam4[0])
        user_inspection_query.bindValue(":beam4_ripple_flag", beam4[1])
        user_inspection_query.bindValue(":synthesis_signal_flag", synthesis[0])
        user_inspection_query.bindValue(":synthesis_baseline_flag", synthesis[1])
        return user_inspection_query.exec()

    def del_current_galaxy_from_database(self):
        del_query = QSqlQuery()
        del_query.prepare(f"""
        DELETE FROM galaxies WHERE galaxy_name = ?
        """)
        galaxy_name = self.current_galaxy["galaxy_name"]
        # print(galaxy_name)
        del_query.addBindValue(galaxy_name)
        del_query.exec()
        print("number of rows affected: ", del_query.numRowsAffected())

    def getUserResults(self):
        # 收集beams和synthesis附属的radio button的状态
        beam1_rfi_flag = 0
        beam1_ripple_flag = 0
        beam2_rfi_flag = 0
        beam2_ripple_flag = 0
        beam3_rfi_flag = 0
        beam3_ripple_flag = 0
        beam4_rfi_flag = 0
        beam4_ripple_flag = 0
        synthesis_signal_flag = 0
        baseline_flag = 0

        # beams
        if self.gb_beam1.isVisible():
            if self.rb_beam1_rfi_1.isChecked():
                beam1_rfi_flag = 1
            if self.rb_beam1_rfi_2.isChecked():
                beam1_rfi_flag = 2
            if self.rb_beam1_rfi_3.isChecked():
                beam1_rfi_flag = 3
            if self.rb_beam1_ripple_1.isChecked():
                beam1_ripple_flag = 1
            if self.rb_beam1_ripple_2.isChecked():
                beam1_ripple_flag = 2
        if self.gb_beam2.isVisible():
            if self.rb_beam2_rfi_1.isChecked():
                beam2_rfi_flag = 1
            if self.rb_beam2_rfi_2.isChecked():
                beam2_rfi_flag = 2
            if self.rb_beam2_rfi_3.isChecked():
                beam2_rfi_flag = 3
            if self.rb_beam2_ripple_1.isChecked():
                beam2_ripple_flag = 1
            if self.rb_beam2_ripple_2.isChecked():
                beam2_ripple_flag = 2
        if self.gb_beam3.isVisible():
            if self.rb_beam3_rfi_1.isChecked():
                beam3_rfi_flag = 1
            if self.rb_beam3_rfi_2.isChecked():
                beam3_rfi_flag = 2
            if self.rb_beam3_rfi_3.isChecked():
                beam3_rfi_flag = 3
            if self.rb_beam3_ripple_1.isChecked():
                beam3_ripple_flag = 1
            if self.rb_beam3_ripple_2.isChecked():
                beam3_ripple_flag = 2
        if self.gb_beam4.isVisible():
            if self.rb_beam4_rfi_1.isChecked():
                beam4_rfi_flag = 1
            if self.rb_beam4_rfi_2.isChecked():
                beam4_rfi_flag = 2
            if self.rb_beam4_rfi_3.isChecked():
                beam4_rfi_flag = 3
            if self.rb_beam4_ripple_1.isChecked():
                beam4_ripple_flag = 1
            if self.rb_beam4_ripple_2.isChecked():
                beam4_ripple_flag = 2
        # synthesis
        if self.rb_synthesis_signal_1.isChecked():
            synthesis_signal_flag = 1
        if self.rb_synthesis_signal_2.isChecked():
            synthesis_signal_flag = 2
        if self.rb_synthesis_signal_3.isChecked():
            synthesis_signal_flag = 3
        if self.rb_synthesis_baseline_1.isChecked():
            baseline_flag = 1
        if self.rb_synthesis_baseline_2.isChecked():
            baseline_flag = 2

        return (beam1_rfi_flag, beam1_ripple_flag), (beam2_rfi_flag, beam2_ripple_flag), \
               (beam3_rfi_flag, beam3_ripple_flag), (beam4_rfi_flag, beam4_ripple_flag), \
               (synthesis_signal_flag, baseline_flag)

    def setCanvas(self, container):
        canvas = MplCanvas(self)
        layout = QGridLayout(container)
        layout.addWidget(canvas)
        return canvas

    def next_db_entry(self):
        if self.dbQuery.exec("SELECT galaxy_name, beam_file_path, synthesis_file_path, sdss_file_path FROM galaxies"):
            if self.dbQuery.next():
                name, beams, synthesis, sdss = range(4)
                name = self.dbQuery.value(name)
                beams = self.dbQuery.value(beams)
                synthesis = self.dbQuery.value(synthesis)
                sdss = self.dbQuery.value(sdss)
                self.current_galaxy = {
                    "galaxy_name": name,
                    "beams": beams,
                    "synthesis": synthesis,
                    "sdss": sdss
                }
        else:
            print(__file__, "db error", self.dbQuery.lastError().text())
            sys.exit(-1)
        print("Current Galaxy: ")
        print("-" * 10)
        print(self.current_galaxy)
        return self.current_galaxy

    def plot_images(self, data=None):
        if data is None:
            print("No data about current galaxy!")
            sys.exit(-1)
        # plot beams
        beams = ast.literal_eval(data["beams"])
        for i, beam in enumerate(beams):
            self.beam_canvases[i].plot_beams(beam)

        # plot synthesis
        synthesis = data['synthesis']
        self.canvas_synthesis.plot_synthesis(synthesis)

    def initPlotWidget(self):
        widget_beam1 = self.findChild(QWidget, "widget_beam1")
        widget_beam2 = self.findChild(QWidget, "widget_beam2")
        widget_beam3 = self.findChild(QWidget, "widget_beam3")
        widget_beam4 = self.findChild(QWidget, "widget_beam4")
        widget_synthesis = self.findChild(QWidget, "widget_synthesis")
        widget_sdss = self.findChild(QWidget, "widget_SDSS")
        self.canvas_beam1 = self.setCanvas(widget_beam1)
        self.canvas_beam2 = self.setCanvas(widget_beam2)
        self.canvas_beam3 = self.setCanvas(widget_beam3)
        self.canvas_beam4 = self.setCanvas(widget_beam4)
        self.beam_canvases = [self.canvas_beam1, self.canvas_beam2, self.canvas_beam3, self.canvas_beam4]
        self.canvas_synthesis = self.setCanvas(widget_synthesis)
        self.canvas_SDSS = self.setCanvas(widget_sdss)

    def setBeamGroupBoxVisibility(self):
        beam_number = len(ast.literal_eval(self.current_galaxy["beams"]))
        if beam_number == 1:
            self.gb_beam1.setVisible(True)
            self.gb_beam2.setVisible(False)
            self.gb_beam3.setVisible(False)
            self.gb_beam4.setVisible(False)
        elif beam_number == 2:
            self.gb_beam1.setVisible(True)
            self.gb_beam2.setVisible(True)
            self.gb_beam3.setVisible(False)
            self.gb_beam4.setVisible(False)
        elif beam_number == 3:
            self.gb_beam1.setVisible(True)
            self.gb_beam2.setVisible(True)
            self.gb_beam3.setVisible(True)
            self.gb_beam4.setVisible(False)
        else:
            self.gb_beam1.setVisible(True)
            self.gb_beam2.setVisible(True)
            self.gb_beam3.setVisible(True)
            self.gb_beam4.setVisible(True)

    def setRadioButtons(self):
        # radio groups in beam1
        self.gb_beam1 = self.findChild(QGroupBox, "gb_beam1")
        self.rb_beam1_rfi_1 = self.findChild(QRadioButton, "rb_beam1_rfi_1")
        self.rb_beam1_rfi_2 = self.findChild(QRadioButton, "rb_beam1_rfi_2")
        self.rb_beam1_rfi_3 = self.findChild(QRadioButton, "rb_beam1_rfi_3")
        self.bg_beam1_rfi = QButtonGroup(self.gb_beam1)
        self.bg_beam1_rfi.addButton(self.rb_beam1_rfi_1)
        self.bg_beam1_rfi.addButton(self.rb_beam1_rfi_2)
        self.bg_beam1_rfi.addButton(self.rb_beam1_rfi_3)
        self.rb_beam1_rfi_1.setChecked(True)

        self.rb_beam1_ripple_1 = self.findChild(QRadioButton, "rb_beam1_ripple_1")
        self.rb_beam1_ripple_2 = self.findChild(QRadioButton, "rb_beam1_ripple_2")
        self.bg_beam1_ripple = QButtonGroup(self.gb_beam1)
        self.bg_beam1_ripple.addButton(self.rb_beam1_ripple_1)
        self.bg_beam1_ripple.addButton(self.rb_beam1_ripple_2)
        self.rb_beam1_ripple_1.setChecked(True)

        # radio groups in beam2
        self.gb_beam2 = self.findChild(QGroupBox, "gb_beam2")
        self.rb_beam2_rfi_1 = self.findChild(QRadioButton, "rb_beam2_rfi_1")
        self.rb_beam2_rfi_2 = self.findChild(QRadioButton, "rb_beam2_rfi_2")
        self.rb_beam2_rfi_3 = self.findChild(QRadioButton, "rb_beam2_rfi_3")
        self.bg_beam2_rfi = QButtonGroup(self.gb_beam2)
        self.bg_beam2_rfi.addButton(self.rb_beam2_rfi_1)
        self.bg_beam2_rfi.addButton(self.rb_beam2_rfi_2)
        self.bg_beam2_rfi.addButton(self.rb_beam2_rfi_3)
        self.rb_beam2_rfi_1.setChecked(True)

        self.rb_beam2_ripple_1 = self.findChild(QRadioButton, "rb_beam2_ripple_1")
        self.rb_beam2_ripple_2 = self.findChild(QRadioButton, "rb_beam2_ripple_2")
        self.bg_beam2_ripple = QButtonGroup(self.gb_beam2)
        self.bg_beam2_ripple.addButton(self.rb_beam2_ripple_1)
        self.bg_beam2_ripple.addButton(self.rb_beam2_ripple_2)
        self.rb_beam2_ripple_1.setChecked(True)

        # radio groups in beam3
        self.gb_beam3 = self.findChild(QGroupBox, "gb_beam3")
        self.rb_beam3_rfi_1 = self.findChild(QRadioButton, "rb_beam3_rfi_1")
        self.rb_beam3_rfi_2 = self.findChild(QRadioButton, "rb_beam3_rfi_2")
        self.rb_beam3_rfi_3 = self.findChild(QRadioButton, "rb_beam3_rfi_3")
        self.bg_beam3_rfi = QButtonGroup(self.gb_beam3)
        self.bg_beam3_rfi.addButton(self.rb_beam3_rfi_1)
        self.bg_beam3_rfi.addButton(self.rb_beam3_rfi_2)
        self.bg_beam3_rfi.addButton(self.rb_beam3_rfi_3)
        self.rb_beam3_rfi_1.setChecked(True)

        self.rb_beam3_ripple_1 = self.findChild(QRadioButton, "rb_beam3_ripple_1")
        self.rb_beam3_ripple_2 = self.findChild(QRadioButton, "rb_beam3_ripple_2")
        self.bg_beam3_ripple = QButtonGroup(self.gb_beam3)
        self.bg_beam3_ripple.addButton(self.rb_beam3_ripple_1)
        self.bg_beam3_ripple.addButton(self.rb_beam3_ripple_2)
        self.rb_beam3_ripple_1.setChecked(True)

        # radio groups in beam4
        self.gb_beam4 = self.findChild(QGroupBox, "gb_beam4")
        self.rb_beam4_rfi_1 = self.findChild(QRadioButton, "rb_beam4_rfi_1")
        self.rb_beam4_rfi_2 = self.findChild(QRadioButton, "rb_beam4_rfi_2")
        self.rb_beam4_rfi_3 = self.findChild(QRadioButton, "rb_beam4_rfi_3")
        self.bg_beam4_rfi = QButtonGroup(self.gb_beam4)
        self.bg_beam4_rfi.addButton(self.rb_beam4_rfi_1)
        self.bg_beam4_rfi.addButton(self.rb_beam4_rfi_2)
        self.bg_beam4_rfi.addButton(self.rb_beam4_rfi_3)
        self.rb_beam4_rfi_1.setChecked(True)

        self.rb_beam4_ripple_1 = self.findChild(QRadioButton, "rb_beam4_ripple_1")
        self.rb_beam4_ripple_2 = self.findChild(QRadioButton, "rb_beam4_ripple_2")
        self.bg_beam4_ripple = QButtonGroup(self.gb_beam4)
        self.bg_beam4_ripple.addButton(self.rb_beam4_ripple_1)
        self.bg_beam4_ripple.addButton(self.rb_beam4_ripple_2)
        self.rb_beam4_ripple_1.setChecked(True)

        # radio groups in synthesis
        widget_synthesis_container = self.findChild(QWidget, "widget_container_synthesis")
        self.rb_synthesis_signal_1 = self.findChild(QRadioButton, "rb_synthesis_signal_1")
        self.rb_synthesis_signal_2 = self.findChild(QRadioButton, "rb_synthesis_signal_2")
        self.rb_synthesis_signal_3 = self.findChild(QRadioButton, "rb_synthesis_signal_3")
        self.bg_synthesis_signal = QButtonGroup(widget_synthesis_container)
        self.bg_synthesis_signal.addButton(self.rb_synthesis_signal_1)
        self.bg_synthesis_signal.addButton(self.rb_synthesis_signal_2)
        self.bg_synthesis_signal.addButton(self.rb_synthesis_signal_3)
        self.rb_synthesis_signal_1.setChecked(True)

        self.rb_synthesis_baseline_1 = self.findChild(QRadioButton, "rb_synthesis_baseline_1")
        self.rb_synthesis_baseline_2 = self.findChild(QRadioButton, "rb_synthesis_baseline_2")
        self.bg_synthesis_baseline = QButtonGroup(widget_synthesis_container)
        self.bg_synthesis_baseline.addButton(self.rb_synthesis_baseline_1)
        self.bg_synthesis_baseline.addButton(self.rb_synthesis_baseline_2)
        self.rb_synthesis_baseline_1.setChecked(True)
