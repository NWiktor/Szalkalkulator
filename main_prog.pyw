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
from PyQt5.QtGui import (QStandardItemModel, QPainter, QBrush, QColor, QFontMetrics)
from PyQt5.QtCore import (Qt, QRect, QSize)

# Local application imports
# TODO: Implement log ?
# from logger import MAIN_LOGGER as l

RELEASE_DATE = "2022-11-16"


class Stock_pattern_item(QWidget):

    def __init__(self, width1: int = 0, color: str = 'black', *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.color = color
        self._item_width = width1

        # Gui params
        self._gui_width = None
        self._gui_height = 30

        # Sizepolicy
        self.setSizePolicy(QSizePolicy.MinimumExpanding,
        QSizePolicy.MinimumExpanding)


    def sizeHint(self):
        if self._item_width == 0:
            self._gui_width = 1
        else:
            self._gui_width = (self._item_width / self.parent()._pixel_ratio)-1
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
            item_length_text = "{}".format(self._item_width)
            x = int(self._gui_width/2)
            y = self._gui_height
            xoffset = font_metrics.boundingRect(item_length_text).width()/2;
            yoffset = font_metrics.boundingRect(item_length_text).height()/2;
            painter.drawText(int(x-xoffset), int(y-yoffset), item_length_text);

        painter.end()


class Stock_pattern_widget(QWidget):

    def __init__(self, elements: list, number: int = 1, waste: int = None, max_length: int = 6000, *args, **kwargs):
        super(Stock_pattern_widget, self).__init__(*args, **kwargs)

        # Constructor
        self.elements = elements
        self.max_length = max_length
        self.number = f"x{number}"

        if waste is None:
            self.waste = max_length-sum(elements)
        else:
            self.waste = waste

        # GUI variables
        self._height = 1
        self._width = 1
        self._show_text_limit = 250 # minimum length in mm, where the text shows
        self._max_gui_width = 600 # width of the stock bar in pixels
        self._pixel_ratio = int(self.max_length / (self._max_gui_width ))

        # Create stock items
        layout = QHBoxLayout()
        for i, value in enumerate(self.elements):
            layout.addWidget(Stock_pattern_item(self.elements[i], 'limegreen'), alignment=Qt.AlignCenter)
            layout.addWidget(Stock_pattern_item(), alignment=Qt.AlignCenter)

        layout.addWidget(Stock_pattern_item(self.waste, 'red'), alignment=Qt.AlignCenter)
        verticalSpacer = QSpacerItem(10, 10, QSizePolicy.Minimum, QSizePolicy.Expanding)
        layout.addItem(verticalSpacer)
        layout.addWidget(QLabel(self.number))

        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch()
        self.setLayout(layout)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(parent=None)

        self.setWindowTitle("Stock cutting calculator - ")

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
        # TODO: Add separator here
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
        # button_box.addStretch()
        add_button = QPushButton("Hozzáad")
        add_button.clicked.connect(self.add_item)
        print_button = QPushButton("Print")
        print_button.clicked.connect(self.create_pdf)
        button_box.addWidget(add_button)
        button_box.addWidget(print_button)
        button_box.addStretch()
        data_field.addLayout(button_box)
        data_field.addStretch()
        layout.addLayout(data_field,0,0)

        # List
        self.stock_table = QTreeWidget(self)
        self.stock_table.resize(700,200)
        self.stock_table.setColumnCount(4)
        self.stock_table.setHeaderLabels(["Poz.", "Hossz", "Mennyiség", "Címke"])
        self.stock_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.stock_table.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.stock_table,0,1)

        # Add pattern table
        self.pattern_table = QVBoxLayout()
        layout.addLayout(self.pattern_table,1,0,2,0)
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


    # TODO: This function is needed later!
    def update_stock_pattern(self):
        """ Regenerate tables and calculates cutting patterns
        dynamcially when focusing out of entry field.
        """

        self.stock_length = int(self.szalhossz_input.text())
        self.cutting_width = int(self.fureszlap_input.text())
        self.calculate()

        # print(self.results)

        for i in reversed(range(self.pattern_table.count())):
                widget = self.pattern_table.takeAt(i).widget()
                if widget is not None:
                    widget.setParent(None)

        for k in self.results.keys():
            self.pattern_table.addWidget(Stock_pattern_widget(self.results[k]["pattern"],
            waste=self.results[k]["waste"], number=self.results[k]["nbr"]))

        self.pattern_table.update()


    def add_item(self):
        """ Add item to stock list """

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


    # TODO: Make this context menu element
    def delete_item(self):
        """ Delete item from list """

        # column = self.stock_table.currentColumn()
        item_uuid = self.stock_table.currentItem().text(0)
        print("Right-clicked item is: " + item_uuid)

        # Delete item from widget
        root = self.stock_table.invisibleRootItem()
        for item in self.stock_table.selectedItems():
            (item.parent() or root).removeChild(item)

        # Delete item from memory
        for s in item_uuid: # Kiválasztott elemeken végigiterálok
            if s in self.stocks:
                del self.stocks[s]

        self.update_stock_pattern()


    def oversized_item(self):
        """ Delete oversized items """

        del_list = []

        for k in self.stocks.keys():
            akt_hossz = self.stocks[k]["len"]
            if int(akt_hossz) > self.stock_length:
                print("Szálhosszat meghaladó elem törölve: {0}".format(akt_hossz))
                del_list.append(k)

        for d in del_list:
            del self.stocks[d]


    def calculate(self):
        """ Calculate cutting patterns """

        szalak = []
        teljes_hossz = 0
        hulladek_hossz = 0
        hulladek_szazalek = 0
        eredmeny = [] # eredmény gyűjtő tömb
        hulladek = [] #hulladek gyüjtő tömb
        self.results = {} # Eredmény tömb törlése

        self.oversized_item() # Hosszú elemek törlése

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

        # Képernyő frissítése
        self.update()


    def check_for_multiple_patterns(self):
        """ Merge cutting patterns """

        last_nbr = 0
        last_pattern = None
        last_uuid = None
        del_uuid = []

        for k in self.results.keys():
            # Ha az első vizsgálat, feltöltöm az adatokat
            if last_pattern == None:
                last_pattern = self.results[k]["pattern"]
                last_nbr = int(self.results[k]["nbr"])
                last_uuid = k

            # Ha már van adat a last_patternben
            else:
                a = last_pattern
                b = self.results[k]["pattern"]

                # Ha az aktuális pattern egyezik az előzővel
                if a == b:
                    # Aktuális pattern nbr emelése
                    self.results[k]["nbr"] = last_nbr + 1

                    # Előző item hozzáadása a törlési tömbhöz
                    del_uuid.append(last_uuid)

                # Végül frissítem a last_adatokat
                last_pattern = self.results[k]["pattern"]
                last_nbr = int(self.results[k]["nbr"])
                last_uuid = k

        for d in del_uuid:
            print("Item törlése: {0}".format(d))
            del self.results[d]


    def create_pdf(self):
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
