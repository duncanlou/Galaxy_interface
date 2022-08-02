import os
import sys
from collections import defaultdict

from astropy.table import Table

from PyQt5.QtWidgets import QApplication
from PyQt5.QtSql import QSqlDatabase, QSqlQuery
from PyQt5.QtWidgets import QMessageBox

from MainWindow import MainWindow

IMAGE_PATH_BEAMS = "data/beams"
IMAGE_PATH_SYNTHESIS = "data/synthesis"
IMAGE_PATH_SDSS = "data/SDSS"


def sqlite_db_already_exists():
    db_name = "galaxy.sqlite"
    from os.path import isfile, getsize
    if not isfile(db_name):
        return False
    if getsize(db_name) < 100:  # SQLite database file header is 100 bytes
        return False
    with open(db_name, 'rb') as fd:
        header = fd.read(100)
        return header[:16] == b'SQLite format 3\000'


def readData():
    beam_dict = defaultdict(list)
    beam_files = os.listdir(IMAGE_PATH_BEAMS)
    for beam in beam_files:
        if beam == '.DS_Store':  # ignore the auto generated file on Mac
            continue
        galaxy_name = beam.split("_")[0]
        beam_path = os.path.join(IMAGE_PATH_BEAMS, beam)
        beam_dict[galaxy_name].append(beam_path)

    synthesis_dict = {}
    synthesis_files = os.listdir(IMAGE_PATH_SYNTHESIS)
    for file_name in synthesis_files:
        if file_name == '.DS_Store':  # ignore the auto generated file on Mac
            continue
        galaxy_name = file_name.removesuffix(".fits")
        file_path = os.path.join(IMAGE_PATH_SYNTHESIS, file_name)
        synthesis_dict[galaxy_name] = file_path

    rows = []
    for key in beam_dict.keys():
        beams = list(beam_dict[key])
        s = synthesis_dict[key]
        rows.append((key, beams, s, ""))

    t = Table(rows=rows, names=['galaxy', 'beams', 'synthesis', 'sdss'])
    return t


def createConnection():
    con = QSqlDatabase.addDatabase("QSQLITE")
    con.setDatabaseName("galaxy.sqlite")
    if not con.open():
        QMessageBox.critical(None,
                             "Citizen Scientist Project Error!",
                             f"Database Error: {con.lastError().databaseText()}")
        return False
    return True


def init_database():
    createTableQuery = QSqlQuery()
    createTableQuery.exec(
        """
        CREATE TABLE galaxies (
            id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
            galaxy_name TEXT NOT NULL,
            beam_file_path TEXT NOT NULL ,
            synthesis_file_path TEXT NOT NULL,
            sdss_file_path TEXT NOT NULL 
        )
        """
    )
    userSelectionQuery = QSqlQuery()
    userSelectionQuery.exec(
        """
        CREATE TABLE results (
        id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
        galaxy_name TEXT NOT NULL,
        beam1_rfi_flag INTEGER DEFAULT 0 NOT NULL ,
        beam1_ripple_flag INTEGER DEFAULT 0 NOT NULL ,
        beam2_rfi_flag INTEGER DEFAULT 0 NOT NULL,
        beam2_ripple_flag INTEGER DEFAULT 0 NOT NULL,
        beam3_rfi_flag INTEGER DEFAULT 0 NOT NULL,
        beam3_ripple_flag INTEGER DEFAULT 0 NOT NULL,
        beam4_rfi_flag INTEGER DEFAULT 0 NOT NULL,
        beam4_ripple_flag INTEGER DEFAULT 0 NOT NULL,
        synthesis_signal_flag INTEGER DEFAULT 0 NOT NULL,
        synthesis_baseline_flag INTEGER DEFAULT 0 NOT NULL
        )
        """
    )

    insertDataQuery = QSqlQuery()
    insertDataQuery.prepare(
        """
        INSERT INTO galaxies (
            galaxy_name,
            beam_file_path,
            synthesis_file_path,
            sdss_file_path
        )
        VALUES (:galaxy_name,:beam_file_path,:synthesis_file_path,:sdss_file_path)
        """
    )

    dataTable = readData()
    for row in dataTable:
        insertDataQuery.bindValue(":galaxy_name", str(row['galaxy']))
        insertDataQuery.bindValue(":beam_file_path", str(row['beams']))
        insertDataQuery.bindValue(":synthesis_file_path", str(row['synthesis']))
        insertDataQuery.bindValue(":sdss_file_path", str(row['sdss']))
        insertDataQuery.exec()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    if not createConnection():
        print("Unable to connect to the database")
        sys.exit(-1)

    if not sqlite_db_already_exists():
        print("Create a new database")
        init_database()

    main_window = MainWindow()
    main_window.show()

    sys.exit(app.exec())
