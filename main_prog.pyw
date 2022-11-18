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
import os
import tempfile

from fpdf import FPDF
import win32api
import win32print

# pylint: disable = no-name-in-module
# Third party imports
from PyQt5.QtWidgets import (QApplication, QWidget, QMenu, QMainWindow,
QAction, QGridLayout, QVBoxLayout, QHBoxLayout, QDesktopWidget, QPushButton,
QMessageBox, QFormLayout, QLineEdit,
QTreeWidgetItem, QTreeWidget, QSizePolicy, QLabel, QSpacerItem)
from PyQt5.QtGui import (QFont, QPainter, QBrush, QColor, QFontMetrics)
from PyQt5.QtCore import (Qt, QRect, QSize)

# Local application imports
# TODO: Implement log ?
# from logger import MAIN_LOGGER as l

RELEASE_DATE = "2022-11-16"


class StockPatternItem(QWidget):

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

            font_metrics = QFontMetrics(painter.font())
            item_length_text = str(self._item_width)
            x_pos = int(self._gui_width/2)
            y_pos = self._gui_height
            xoffset = font_metrics.boundingRect(item_length_text).width()/2
            yoffset = font_metrics.boundingRect(item_length_text).height()/2
            painter.drawText(int(x_pos-xoffset), int(y_pos-yoffset), item_length_text)

        painter.end()


class StockPatternWidget(QWidget):

    def __init__(self, stock_pieces: list, number: int = 1, waste: int = None,
        max_length: int = 6000, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Constructor
        self.stock_pieces = stock_pieces
        self.max_length = max_length
        self.number = f"x{number}"

        if waste is None:
            self.waste = max_length - sum(stock_pieces)
        else:
            self.waste = waste

        # GUI variables
        self._show_text_limit = 250 # minimum length in mm, where the text shows
        self._max_gui_width = 600 # width of the stock bar in pixels
        self._pixel_ratio = int(self.max_length / (self._max_gui_width ))
        self.create_ui()


    def create_ui(self):
        """ Create stock items. """

        pixels_left = 600
        separator_width = 1
        layout = QHBoxLayout()

        # Add stock items:
        for i, stock_length in enumerate(self.stock_pieces):
            gui_width = (stock_length / self._pixel_ratio)
            pixels_left -= gui_width
            layout.addWidget(StockPatternItem(stock_length,
            gui_width-separator_width, 'limegreen'), alignment=Qt.AlignCenter)
            layout.addWidget(StockPatternItem(0, separator_width),
            alignment=Qt.AlignCenter)

        # Last item length is equal to the number of pixels left,
        # this strategy corrects cumulative rounding errors
        if pixels_left != 0:
            layout.addWidget(StockPatternItem(self.waste, pixels_left, 'red'),
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
        self.stock_length = 6000 # mm
        self.cutting_width = 3 # mm
        self.stock_item_dict = {}
        # self.stock_item_dict = {"A" : {"nbr": 2, "len": 4345, "label": "proba"},
        # "B" : {"nbr": 34, "len": 245633, "label": "proba2"}}

        self.patterns = {}
        # self.patterns = {"A": {"nbr": 3, "pattern": [1450, 1450, 1450, 1450]},
        # "B": {"nbr": 1, "pattern": [500, 500, 1450, 950], "waste": 23231},
        # "C": {"nbr": 2, "pattern": [780, 657, 345, 880], "waste": 23231},
        # "D": {"nbr": 6, "pattern": [1045, 650, 890], "waste": 21321}}

        self.total_stocks = "" # Formatted string of total nbr of stocks
        self.total_waste = "" # Formatted string of total waste perc. and length

        self.print_data = []
        self._create_menubar()
        self._create_central_widget()
        self._create_status_bar()


    def _create_menubar(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu('Fájl')
        # Add actions
        clear_action = QAction("Memória törlése", self, triggered=self.clear_results)
        file_menu.addAction(clear_action)
        # test_action = QAction("Test", self, triggered=self.test)
        # file_menu.addAction(test_action)
        about_action = QAction("About", self, triggered=self.about)
        file_menu.addAction(about_action)


    def _create_central_widget(self):
        layout_widget = QWidget()
        layout = QGridLayout()
        data_field = QVBoxLayout()
        data_field_h = QHBoxLayout()
        input_field = QFormLayout()

        # Datafields
        self.szalhossz_input = QLineEdit()
        self.szalhossz_input.setText(str(self.stock_length))
        self.szalhossz_input.setFixedWidth(50)
        self.szalhossz_input.textChanged.connect(self.clear_results)
        szalhossz_label = QLabel("Szálhossz (mm)")
        szalhossz_label.setFixedWidth(150)
        input_field.addRow(szalhossz_label, self.szalhossz_input)
        self.fureszlap_input = QLineEdit()
        self.fureszlap_input.setText(str(self.cutting_width))
        self.fureszlap_input.setFixedWidth(50)
        self.fureszlap_input.textChanged.connect(self.clear_results)
        input_field.addRow("Fűrészlap vast. (mm)", self.fureszlap_input)

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
        button_box.addStretch()
        add_button = QPushButton("Hozzáad")
        add_button.clicked.connect(self.add_item_wrapper)
        add_button.setShortcut("Return")
        print_button = QPushButton("PDF")
        print_button.clicked.connect(self.create_pdf_report)
        button_box.addWidget(add_button)
        button_box.addWidget(print_button)
        data_field.addLayout(button_box)
        data_field.addStretch()

        data_field_h.addLayout(data_field)
        data_field_h.addStretch()
        layout.addLayout(data_field_h,0,0)

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
        self.pattern_summary = QLabel("")
        self.pattern_summary.setFont(QFont('Arial', 10, QFont.Bold))
        self.update_stock_pattern() # Update after adding all elements to layout
        pattern_layout.addWidget(self.pattern_summary, alignment=Qt.AlignCenter)
        layout.addLayout(pattern_layout,1,0,2,0)

        # Finialize layout
        layout_widget.setLayout(layout)
        self.setCentralWidget(layout_widget)
        self.darab_hossz.setFocus()


    def _create_status_bar(self):
        self.statusbar = self.statusBar()


    def center(self):
        """Position window to the center."""
        qt_rectangle = self.frameGeometry()
        centerpoint = QDesktopWidget().availableGeometry().center()
        qt_rectangle.moveCenter(centerpoint)
        self.move(qt_rectangle.topLeft())


    def _show_context_menu(self, position):
        display_action1 = QAction("Elem törlése")
        display_action1.triggered.connect(self.delete_item)
        menu = QMenu(self.stock_table)
        menu.addAction(display_action1)
        menu.exec_(self.stock_table.mapToGlobal(position))


    def add_item_wrapper(self):
        """ Wrapper """
        self.darab_hossz.setFocus()
        self.add_item()
        self.darab_hossz.setText("")


    def update_stock_pattern(self):
        """ Regenerate tables and calculates cutting patterns
        dynamcially.
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
        if not self.patterns:
            results_placeholder = QLabel("Nincs szál")
            font = QFont('Arial', 10)
            font.setItalic(True)
            results_placeholder.setFont(font)
            results_placeholder.setFixedWidth(622)
            self.pattern_table.addWidget(results_placeholder, alignment=Qt.AlignCenter)
            # Set summary line
            self.pattern_summary.setText(f"Összesen: - / Veszteség: -")

        else:
            # Add new elements
            for k in self.patterns.keys():
                self.pattern_table.addWidget(StockPatternWidget(
                self.patterns[k]["pattern"],
                waste=self.patterns[k]["waste"],
                number=self.patterns[k]["nbr"],
                max_length=self.stock_length))

            # Set summary line
            self.pattern_summary.setText(
            f"Összesen: {self.total_stocks} / Veszteség: {self.total_waste}")

        self.pattern_table.update()


    def add_item(self):
        """ Add item to stock list. """

        uuid_str = str(uuid.uuid4())
        label = str(self.darab_label.text()) # Címke, bármit elfogadunk

        # Ha nincs hossz, akkor értelmetlen és visszalépek
        if (self.darab_hossz.text() is None) or (self.darab_hossz.text() == ""):
            self.statusbar.showMessage("Hiányzó hossz!", 3000)
            return

        # TODO: Add check for zero!
        # Mennyiség, ha nincs vagy ha üres, akkor default = 1
        if (self.darab_nbr.text() is None) or (self.darab_nbr.text() == ""):
            self.statusbar.showMessage("Hiányzó darabszám, alapértelmezetten: 1!", 3000)
            nbr = 1

        # Megpróbálom konvertálni és menteni, ha sikertelen raise error
        try:
            nbr = int(self.darab_nbr.text())
            len = int(self.darab_hossz.text())
            # Ha a beírt hossz túl nagy
            if len > self.stock_length:
                self.statusbar.showMessage("Szál túl hosszú!")
                return

            # Ha mindennek vége, akkor elmentem
            self.stock_item_dict.update({uuid_str : {"nbr": nbr, "len": len, "label" : label}})
            self.stock_table.addTopLevelItem(QTreeWidgetItem([uuid_str, str(len), str(nbr), label]))

        except Exception as e:
            self.statusbar.showMessage("Váratlan hiba: {0}".format(e), 3000)
            return

        finally:
            self.update_stock_pattern()


    def delete_item(self):
        """ Delete item from list """

        item_uuid = self.stock_table.currentItem().text(0)
        # Delete item from widget
        root = self.stock_table.invisibleRootItem()
        for item in self.stock_table.selectedItems():
            (item.parent() or root).removeChild(item)

        # Delete item from memory
        if item_uuid in self.stock_item_dict.keys():
            del self.stock_item_dict[item_uuid]

        self.update_stock_pattern()


    def delete_oversized_items(self):
        """ Delete oversized items """

        del_list = []

        for item_uuid in self.stock_item_dict.keys():
            item_length = self.stock_item_dict[item_uuid]["len"]

            if int(item_length) > self.stock_length: # Oversized item deletion:
                del_list.append(item_uuid)

        for item_uuid in del_list:
            del self.stock_item_dict[item_uuid]


    def calculate_patterns(self):
        """ Calculate cutting patterns """

        szalak = []
        teljes_hossz = 0
        hulladek_hossz = 0
        hulladek_szazalek = 0
        eredmeny = [] # eredmény gyűjtő tömb
        hulladek = [] #hulladek gyüjtő tömb
        self.patterns = {} # Eredmény tömb törlése
        self.delete_oversized_items() # Hosszú elemek törlése

        # Elemek hozzáadása a tömbhöz
        for i, stock_item in self.stock_item_dict.items():
            szalak += [int(stock_item["len"])] * int(stock_item["nbr"])

        szalak.sort(reverse=True) # csökkenő sorrendbe teszem a szálakat

        while szalak != []: # Amíg a szálak tömb nem nulla, fut a számítás
            actual_stock = []
            akt_szal = "|" # akutális szál összetétele / string formátumban
            akt_hossz = 0 # aktuális szál szálhossza
            maradek = self.stock_length ## aktuális szál maradéka
            torolni = []

            # Végigmegyek a szálak tömb minden elemén
            for i, stock_item in enumerate(szalak):
                if stock_item <= maradek: # Ha az aktuális száldarab rövidebb v egyenlő, mint a maradék
                    akt_hossz += (stock_item + self.cutting_width)  # Aktuális szálhosszhoz hozzáadom az elemet
                    maradek -= (stock_item + self.cutting_width) # Maradékból kivonom az elemet
                    akt_szal += f"| {stock_item:>4} " # A szál összetételhez hozzáadom az elemet
                    actual_stock.append(stock_item)
                    torolni.append(i) # torlendő elemek index listájához hozzáadni az aktuálisat

                else: # Ha az aktuális száldarab hosszabb, mint a maradék
                    if maradek < szalak[-1]: # Ha a maradék kisebb, mint az utolsó (legrövidebb elem), akkor kilépek
                        break # For ciklus megtörése, kilépés a while ciklusba

            # Ha kész az iteráció összesítem a szálat
            akt_szal += f"|| --> {akt_hossz} mm"

            # Set pattern
            uuid_str = str(uuid.uuid4())
            self.patterns[uuid_str] = {"pattern": actual_stock, "waste": maradek, "nbr" : 1}
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

        # Using new class variables
        self.total_stocks = f"{len(eredmeny)} db ({self.stock_length} mm)"
        self.total_waste = f"{hulladek_szazalek:.2f}% ({hulladek_hossz} mm)"

        #########

        # # TODO: Move to a separate function: prepare PDF data or similar
        # Ha készen vagyok, kiadom az eredményt
        self.print_data.clear()
        self.print_data.append("\n-- DARABOLÁSI TERV --")

        # TODO: Move this to Stock item pattern (?)
        for pat in range(0, len(eredmeny)):
            self.print_data.append("\n{0}".format(eredmeny[pat])) # Eredmeny kiírása

        self.print_data.append("\n\n-- ÖSSZEGZÉS --")
        self.print_data.append("\nSzükséges szálmennyiség: " + self.total_stocks)
        self.print_data.append("\nHulladék mennyisége:" + self.total_waste)
        self.print_data.append("\nHulladékok: " + str(hulladek)) # Hulladek darabok


    def check_for_multiple_patterns(self):
        """ Merge cutting patterns. """

        last_nbr = 0
        last_pattern = None
        last_uuid = None
        del_uuid = []

        for k, pattern in self.patterns.items():
            if last_pattern is not None: # Ha már van adat a last_patternben
                # Ha az aktuális pattern egyezik az előzővel
                if last_pattern == (pattern["pattern"]):
                    pattern["nbr"] = last_nbr + 1 # Increment pattern nbr
                    del_uuid.append(last_uuid) # Előző item hozzáadása a törlési tömbhöz

            # Ha az első vizsgálat, és/vagy kész a check feltöltöm az adatokat
            last_pattern = pattern["pattern"]
            last_nbr = int(pattern["nbr"])
            last_uuid = k

        for _uuid in del_uuid: # Item törlése
            del self.patterns[_uuid]


    def clear_results(self):
        """  """
        self.stock_item_dict = {}
        self.patterns = {}
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
    sys.exit()


    # def test(self):
    #     """  """
    #     w = self.frameGeometry().width()
    #     h = self.frameGeometry().height()
    #     print(f"Window size: {w}x{h}")
