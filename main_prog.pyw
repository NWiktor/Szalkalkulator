# -*- coding: utf-8 -*-#
#!/usr/bin/python3
"""  GUI for the Szálkalkulátor app.

This app is used for determining cutting patterns for stock materials.

Libs
----
* Tkinter
* win32api
* win32print

Help
----
* https://www.w3.org/TR/SVG11/types.html#ColorKeywords

Info
----
Wetzl Viktor - 2021.04.01 - All rights reserved
"""
# TODO: Add proper licence type

import uuid
import sys

from fpdf import FPDF
import tempfile
import win32api
import win32print

from tkinter import ttk
import tkinter as tk

# pylint: disable = no-name-in-module
# Third party imports
from PyQt5.QtWidgets import (QApplication, QWidget, QMenu, QMainWindow,
QAction, QDockWidget, QListWidget, QGridLayout, QVBoxLayout, QHBoxLayout,
QTreeView, QDesktopWidget, QPushButton, QMessageBox, QFormLayout, QLineEdit,
QTreeWidgetItem, QTreeWidget, QSizePolicy, QLabel, QSpacerItem)
from PyQt5.QtGui import (QStandardItemModel, QFont, QPainter, QBrush, QColor, QFontMetrics)
from PyQt5.QtCore import (Qt, QRect, QSize)

# Local application imports
# TODO: Implement log ?
# from logger import MAIN_LOGGER as l

RELEASE_DATE = "2022-11-16"


class Stock_pattern_item(QWidget):

    def __init__(self, stock_width, gui_width, color: str = 'black', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.color = color
        self._item_width = stock_width # Stock width in mm
        self._gui_width = gui_width # Item visible width in px
        self._gui_height = 30
        self.setSizePolicy(QSizePolicy.MinimumExpanding,
        QSizePolicy.MinimumExpanding)


    def sizeHint(self):
        return QSize(int(self._gui_width), self._gui_height)


    def paintEvent(self, e):
        painter = QPainter(self)
        brush = QBrush()
        brush.setColor(QColor(self.color))
        brush.setStyle(Qt.SolidPattern)
        rect = QRect(0, 0, painter.device().width(), painter.device().height())
        painter.fillRect(rect, brush)

        # Write length text inside item
        if self._item_width >= int(self.parent()._show_text_limit):
            pen = painter.pen()
            pen.setColor(QColor('black'))
            painter.setPen(pen)
            font = painter.font()
            font.setFamily('Times')
            font.setPointSize(10)
            painter.setFont(font)

            font_metrics = QFontMetrics(painter.font());
            item_length_text = str(self._item_width)
            x = int(self._gui_width/2)
            y = self._gui_height
            xoffset = font_metrics.boundingRect(item_length_text).width()/2;
            yoffset = font_metrics.boundingRect(item_length_text).height()/2;
            painter.drawText(int(x-xoffset), int(y-yoffset), item_length_text);

        painter.end()


class Stock_pattern_widget(QWidget):

    def __init__(self, stock_pieces: list, number: int = 1, waste: int = None,
        max_length: int = 6000, *args, **kwargs):
        super(Stock_pattern_widget, self).__init__(*args, **kwargs)

        # Constructor
        self.stock_pieces = stock_pieces
        self.max_length = max_length
        self.number = f"x{number}"

        if waste is None:
            self.waste = max_length-sum(elements)
        else:
            self.waste = waste

        # GUI variables
        self._show_text_limit = 250 # minimum length in mm, where the text shows
        self._max_gui_width = 600 # width of the stock bar in pixels
        self._pixel_ratio = int(self.max_length / (self._max_gui_width ))
        self.create_UI()


    def create_UI(self):
        """ Create stock items. """

        pixels_left = 600
        separator_width = 1
        layout = QHBoxLayout()

        # Add stock items:
        for i, stock_length in enumerate(self.stock_pieces):
            gui_width = (stock_length / self._pixel_ratio)
            pixels_left -= gui_width
            layout.addWidget(Stock_pattern_item(stock_length,
            gui_width-separator_width, 'limegreen'), alignment=Qt.AlignCenter)
            layout.addWidget(Stock_pattern_item(0, separator_width),
            alignment=Qt.AlignCenter)

        # Last item length is equal to the number of pixels left,
        # this strategy corrects cumulative rounding errors
        if pixels_left != 0:
            layout.addWidget(Stock_pattern_item(self.waste, pixels_left, 'red'),
            alignment=Qt.AlignCenter)

        layout.addItem(QSpacerItem(10, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))
        layout.addWidget(QLabel(self.number))

        # Finalize layout
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch()
        self.setLayout(layout)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(parent=None)

        self.setWindowTitle("Stock cutting calculator")
        # self.setMinimumSize(650, 350)
        # self.setSizePolicy(QSizePolicy.MinimumExpanding,
        # QSizePolicy.MinimumExpanding)

        self.stock_length = 6000 # mm
        self.cutting_width = 3 # mm
        self.stocks = {}
        # self.stocks = {"A" : {"nbr": 2, "len": 4345, "label": "proba"},
        # "B" : {"nbr": 34, "len": 245633, "label": "proba2"}}

        self.results = {}
        # self.results = {"A": {"nbr": 3, "pattern": [1450, 1450, 1450, 1450]},
        # "B": {"nbr": 1, "pattern": [500, 500, 1450, 950], "waste": 23231},
        # "C": {"nbr": 2, "pattern": [780, 657, 345, 880], "waste": 23231},
        # "D": {"nbr": 6, "pattern": [1045, 650, 890], "waste": 21321}}

        self.print_data = []
        self._create_menubar()
        self._create_central_widget()
        self._create_status_bar()


    def _create_menubar(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu('File')
        # Add actions
        clear_action = QAction("Clear results", self, triggered=self.clear_results)
        file_menu.addAction(clear_action)
        test_action = QAction("Test", self, triggered=self.test)
        file_menu.addAction(test_action)
        about_action = QAction("About", self, triggered=self.about)
        file_menu.addAction(about_action)


    def _create_central_widget(self):
        layout_widget = QWidget()
        layout = QGridLayout()
        data_field = QVBoxLayout()
        input_field = QFormLayout()

        # Datafields
        self.szalhossz_input = QLineEdit()
        self.szalhossz_input.setText(str(self.stock_length))
        self.szalhossz_input.setFixedWidth(50)
        input_field.addRow("Szálhossz (mm)", self.szalhossz_input)
        self.fureszlap_input = QLineEdit()
        self.fureszlap_input.setText(str(self.cutting_width))
        self.fureszlap_input.setFixedWidth(50)
        input_field.addRow("Fűrészlap vast. (mm)", self.fureszlap_input)

        # Separator boilerplate code:
        # layout.addItem(QSpacerItem(10, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.darab_hossz = QLineEdit()
        self.darab_hossz.setPlaceholderText("Pl.: 500")
        self.darab_hossz.setFixedWidth(50)
        input_field.addRow("Darab hossza (mm)", self.darab_hossz)
        self.darab_nbr = QLineEdit()
        self.darab_nbr.setPlaceholderText("Pl.: 2")
        self.darab_nbr.setFixedWidth(50)
        input_field.addRow("Darab mennyiség (db)", self.darab_nbr)
        self.darab_label = QLineEdit()
        self.darab_label.setPlaceholderText("Pl.: Part 01")
        self.darab_label.setFixedWidth(50)
        input_field.addRow("Címke", self.darab_label)
        data_field.addLayout(input_field)

        button_box = QHBoxLayout()
        add_button = QPushButton("Hozzáad")
        add_button.clicked.connect(self.add_item)
        print_button = QPushButton("PDF")
        print_button.clicked.connect(self.create_pdf_report)
        button_box.addWidget(add_button)
        button_box.addWidget(print_button)
        button_box.addStretch()
        data_field.addLayout(button_box)
        data_field.addStretch()
        layout.addLayout(data_field,0,0)

        # List
        stock_layout = QVBoxLayout()
        self.stock_table = QTreeWidget(self)
        self.stock_table.setColumnCount(4)
        self.stock_table.setHeaderLabels(["UUID", "Hossz", "Mennyiség", "Címke"])
        self.stock_table.setColumnHidden(0, True)
        self.stock_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.stock_table.customContextMenuRequested.connect(self._show_context_menu)
        stock_layout.addWidget(self.stock_table)
        stock_layout.addStretch()
        layout.addLayout(stock_layout,0,1)

        # Add pattern table
        pattern_layout = QVBoxLayout()
        pattern_header = QLabel("Számítási eredmények")
        pattern_header.setFont(QFont('Arial', 10, QFont.Bold))
        pattern_layout.addWidget(pattern_header, alignment=Qt.AlignCenter)
        self.pattern_table = QVBoxLayout()

        pattern_layout.addLayout(self.pattern_table)
        self.update_stock_pattern()

        self.pattern_summary = QLabel("Összegzés")
        self.pattern_summary.setFont(QFont('Arial', 10, QFont.Bold))
        pattern_layout.addWidget(self.pattern_summary, alignment=Qt.AlignCenter)
        layout.addLayout(pattern_layout,1,0,2,0)

        # Finialize layout
        layout_widget.setLayout(layout)
        self.setCentralWidget(layout_widget)


    def _create_status_bar(self):
        self.statusbar = self.statusBar()


    def center(self):
        """Position window to the center."""
        qt_rectangle = self.frameGeometry()
        centerpoint = QDesktopWidget().availableGeometry().center()
        qt_rectangle.moveCenter(centerpoint)
        self.move(qt_rectangle.topLeft())


    def _show_context_menu(self, position):
        display_action1 = QAction("Delete item")
        display_action1.triggered.connect(self.delete_item)
        menu = QMenu(self.stock_table)
        menu.addAction(display_action1)
        menu.exec_(self.stock_table.mapToGlobal(position))


    def update_stock_pattern(self):
        """ Regenerate tables and calculates cutting patterns
        dynamcially when focusing out of entry field.
        """

        self.stock_length = int(self.szalhossz_input.text())
        self.cutting_width = int(self.fureszlap_input.text())
        self.calculate_patterns()

        # Delete layout elements
        for i in reversed(range(self.pattern_table.count())):
                widget = self.pattern_table.takeAt(i).widget()
                if widget is not None:
                    widget.setParent(None)

        # Set placeholder before results
        if not self.results:
            results_placeholder = QLabel("Üres")
            font = QFont('Arial', 10)
            font.setItalic(True)
            results_placeholder.setFont(font)
            results_placeholder.setFixedWidth(622)
            self.pattern_table.addWidget(results_placeholder, alignment=Qt.AlignCenter)

        else:
            # Add new elements
            for k in self.results.keys():
                self.pattern_table.addWidget(Stock_pattern_widget(self.results[k]["pattern"],
                waste=self.results[k]["waste"], number=self.results[k]["nbr"]))

        self.pattern_table.update()


    def add_item(self):
        """ Add item to stock list. """

        uuid_str = str(uuid.uuid4())
        label = str(self.darab_label.text()) # Címke, bármit elfogadunk

        # Mennyiség, ha nincs vagy ha üres, akkor default = 1
        if (self.darab_nbr.text() is None) or (self.darab_nbr.text() == ""):
            nbr = 1
        else:
            nbr = int(self.darab_nbr.text())

        # Ha nincs hossz, akkor értelmetlen
        if (self.darab_hossz.text() is None) or (self.darab_hossz.text() == ""):
            self.statusbar.showMessage("Hiányzó hossz!", 3000)
            return

        else:
            try:
                len = int(self.darab_hossz.text())

            except Exception as e:
                self.statusbar.showMessage("Váratlan hiba: {0}".format(e), 3000)
                return

        # Ha a hossz túl nagy
        if len > self.stock_length:
            self.statusbar.showMessage("Szál túl hosszú!")

        else:
            self.stocks.update({uuid_str : {"nbr": nbr, "len": len, "label" : label}})
            self.stock_table.addTopLevelItem(QTreeWidgetItem([uuid_str, str(len), str(nbr), label]))

        self.update_stock_pattern()


    def delete_item(self):
        """ Delete item from list """

        item_uuid = self.stock_table.currentItem().text(0)
        # Delete item from widget
        root = self.stock_table.invisibleRootItem()
        for item in self.stock_table.selectedItems():
            (item.parent() or root).removeChild(item)

        # Delete item from memory
        if item_uuid in self.stocks.keys():
                del self.stocks[item_uuid]

        self.update_stock_pattern()


    def delete_oversized_items(self):
        """ Delete oversized items """

        del_list = []

        for item_uuid in self.stocks.keys():
            item_length = self.stocks[item_uuid]["len"]

            if int(item_length) > self.stock_length: # Oversized item deletion:
                del_list.append(item_uuid)

        for item_uuid in del_list:
            del self.stocks[item_uuid]


    def calculate_patterns(self):
        """ Calculate cutting patterns """

        szalak = []
        teljes_hossz = 0
        hulladek_hossz = 0
        hulladek_szazalek = 0
        eredmeny = [] # eredmény gyűjtő tömb
        hulladek = [] #hulladek gyüjtő tömb
        self.results = {} # Eredmény tömb törlése

        self.delete_oversized_items() # Hosszú elemek törlése

        # Elemek hozzáadása a tömbhöz
        for k in self.stocks.keys():
            length = int(self.stocks[k]["len"])
            nbr = int(self.stocks[k]["nbr"])
            stock_array = [length] * nbr
            szalak += stock_array

        szalak.sort(reverse=True) # csökkenő sorrendbe teszem a szálakat

        while szalak != []: # Amíg a szálak tömb nem nulla, fut a számítás
            pattern = {}
            actual_stock = []
            akt_szal = "|" # akutális szál összetétele / string formátumban
            akt_hossz = 0 # aktuális szál szálhossza
            maradek = self.stock_length ## aktuális szál maradéka
            torolni = []

            for i in range(0, len(szalak)): # Végigmegyek a szálak tömb minden elemén
                if szalak[i] <= maradek: # Ha az aktuális száldarab rövidebb v egyenlő, mint a maradék
                    akt_hossz += (szalak[i] + self.cutting_width)  # Aktuális szálhosszhoz hozzáadom az elemet
                    maradek -= (szalak[i] + self.cutting_width) # Maradékból kivonom az elemet
                    akt_szal += "| {0:>4} ".format(szalak[i]) # A szál összetételhez hozzáadom az elemet

                    actual_stock.append(szalak[i])
                    torolni.append(i) # torlendő elemek index listájához hozzáadni az aktuálisat

                else: # Ha az aktuális száldarab hosszabb, mint a maradék
                    if maradek < szalak[-1]: # Ha a maradék kisebb, mint az utolsó (legrövidebb elem), akkor kilépek
                        break # For ciklus megtörése, kilépés a while ciklusba

            # Ha kész az iteráció összesítem a szálat
            akt_szal += "|| --> {0} mm".format(akt_hossz)

            # Set pattern
            uuid_str = str(uuid.uuid4())
            self.results[uuid_str] = {"pattern": actual_stock, "waste": maradek, "nbr" : 1}
            eredmeny.append(akt_szal)

            if maradek > 0: # Ha a maradek hossz nagyobb mint nulla, akkor hulladek
                hulladek.append(maradek)
                hulladek_hossz += maradek

            torolni.sort(reverse=True) # torlendo indexek csökkenő sorrendbe állítása ( ez kell? )

            for k in range(0, len(torolni)): #felhasznált darabok törlése a tömbből
                szalak.pop(torolni[k])

        # Hulladék százalék kalkuláció
        teljes_hossz = len(eredmeny) * self.stock_length

        try: # Ha nem viszek be adatot, akkor nullával osztás következik.
            hulladek_szazalek = float(hulladek_hossz) / float(teljes_hossz) * 100

        except ZeroDivisionError:
            return

        # Check for same patterns
        self.check_for_multiple_patterns()

        #########

        # # TODO: Move to a separate function: prepare PDF data or similar
        # Ha készen vagyok, kiadom az eredményt
        self.print_data.clear()

        self.print_data.append("\n-- DARABOLÁSI TERV --")
        for p in range(0, len(eredmeny)):
            self.print_data.append("\n{0}".format(eredmeny[p])) # Eredmeny kiírása

        self.print_data.append("\n\n-- ÖSSZEGZÉS --")
        self.print_data.append("\nSzükséges szálmennyiség: "
        +"{0} db ({1} mm)".format(len(eredmeny), self.stock_length))
        self.print_data.append("\nHulladék mennyisége: "
        +"{0:.2f}% ({1} mm)".format(hulladek_szazalek, hulladek_hossz))
        self.print_data.append("\nHulladékok: " + str(hulladek)) # Hulladek darabok


    def check_for_multiple_patterns(self):
        """ Merge cutting patterns """

        last_nbr = 0
        last_pattern = None
        last_uuid = None
        del_uuid = []

        for k in self.results.keys():
            if last_pattern == None: # Ha az első vizsgálat, feltöltöm az adatokat
                last_pattern = self.results[k]["pattern"]
                last_nbr = int(self.results[k]["nbr"])
                last_uuid = k

            else: # Ha már van adat a last_patternben
                a = last_pattern
                b = self.results[k]["pattern"]

                if a == b: # Ha az aktuális pattern egyezik az előzővel
                    self.results[k]["nbr"] = last_nbr + 1 # Increment pattern nbr
                    del_uuid.append(last_uuid) # Előző item hozzáadása a törlési tömbhöz

                # Végül frissítem a last_adatokat
                last_pattern = self.results[k]["pattern"]
                last_nbr = int(self.results[k]["nbr"])
                last_uuid = k

        for d in del_uuid: # Item törlése
            del self.results[d]


    def clear_results(self):
        """  """
        self.stocks = {}
        self.results = {}
        self.stock_table.clear()
        self.update_stock_pattern()
        self.statusbar.showMessage("Eredmények törölve!", 3000)


    def create_pdf_report(self):
        """ Create PDF with the results. """
        # https://stackoverflow.com/questions/12723818/print-to-standard-printer-from-python
        # https://stackoverflow.com/questions/2878616/programmatically-print-a-pdf-file-specifying-printer
        # https://www.pythonguis.com/examples/python-pdf-report-generator/
        # https://towardsdatascience.com/creating-pdf-files-with-python-ad3ccadfae0f
        # https://towardsdatascience.com/creating-pdf-files-with-python-ad3ccadfae0f

        # Generate pdf
        # TODO: Add code

        # Try to open file immediately
        try:
            os.startfile(filename)

        except Exception:
            # If startfile not available, show dialog.
            QMessageBox.information(self, "Finished", "PDF has been generated!")


    def print_pdf(self):
        """ Print results by default printer. """
        filename = tempfile.mktemp (".txt")
        with open(filename, "w") as file:
            file.writelines(self.print_data)

        win32api.ShellExecute (
            0,
            "print",
            filename,
            #
            # If this is None, the default printer will
            # be used anyway.
            #
            '/d:"%s"' % win32print.GetDefaultPrinter (),
            ".",
            0
            )


    def test(self):
        """  """
        w = self.frameGeometry().width()
        h = self.frameGeometry().height()
        print(f"Window size: {w}x{h}")
        # self.clear_results()


    # TODO: Change lic info
    def about(self):
        """Prints program version data."""

        window_text = (f"Wetzl Viktor - {RELEASE_DATE}\n"
        + "(C) Minden jog fenntartva!")

        about_w = QMessageBox()
        about_w.setWindowTitle("About")
        about_w.setIcon(QMessageBox.Information)
        about_w.setText("Stock Calculator App")
        about_w.setInformativeText(window_text)
        about_w.exec_()


    def close_window(self):
        self.master.destroy()


### Fő program
if __name__ == '__main__':
    app = QApplication([])
    app.setStyle('Fusion')
    main = MainWindow()
    main.show()
    main.center()
    app.exec()
    # l.info("Main window open")
    sys.exit()

    # Test widget only
    # app = QApplication([])
    # app.setStyle('Fusion')
    # stock_widget = Stock_pattern_widget([250, 500, 700, 890])
    # stock_widget.show()
    # print(stock_widget.frameGeometry().width())
    # app.exec_()
