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
QTreeWidgetItem, QTreeWidget)
from PyQt5.QtGui import QStandardItemModel
from PyQt5.QtCore import Qt

# Local application imports
# TODO: Implement log ?
# from logger import MAIN_LOGGER as l

RELEASE_DATE = "2021-04-21"


# TODO: Refactor
class Stock_pattern(tk.Canvas):

    def __init__(self, master, max_length = 6000, elements=[], **kwargs):
        self.field_height = 250
        self.cutting_pixel_width = 2
        self.text_limit = 400
        self.pixel_ratio = float(max_length/self.field_height)

        tk.Canvas.__init__(self, master, bg="chartreuse2", width=40,
        height=self.field_height, **kwargs)

        # Calculate relative point of rectangle
        act_length = 0

        for k in elements:
            item_length = int(k/self.pixel_ratio)

            # Item
            self.create_rectangle(0, act_length,
            42, act_length+item_length-self.cutting_pixel_width,
            fill="LightSteelBlue3", width=0)

            # Item text
            if k >= self.text_limit:
                self.create_text(20, act_length+(item_length)/2,
                font="Times 8", text="{0}".format(k))

            # Cutting width
            self.create_rectangle(0, act_length+item_length-self.cutting_pixel_width,
            42, act_length+item_length, fill="gray15", width=0)
            act_length += item_length


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
        # "B": {"nbr": 1, "pattern": [500, 500, 1450, 950]},
        # "C": {"nbr": 2, "pattern": [780, 657, 345, 880]},
        # "D": {"nbr": 6, "pattern": [1045, 650, 890]}}

        self.print_data = []
        self._create_menubar()
        self._create_central_widget()
        self._create_status_bar()


    def _create_menubar(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu('File')


    def _create_central_widget(self):

        layout_widget = QWidget()
        layout = QGridLayout()
        data_field = QVBoxLayout()
        input_field = QFormLayout()

        # Datafields
        self.szalhossz_input = QLineEdit()
        self.szalhossz_input.setPlaceholderText(str(self.stock_length))
        self.szalhossz_input.setFixedWidth(50)
        input_field.addRow("Szálhossz (mm)", self.szalhossz_input)
        self.fureszlap_input = QLineEdit()
        self.fureszlap_input.setPlaceholderText(str(self.cutting_width))
        self.fureszlap_input.setFixedWidth(50)
        input_field.addRow("Fűrészlap vast. (mm)", self.fureszlap_input)

        self.darab_hossza = QLineEdit()
        self.darab_hossza.setPlaceholderText("Pl.: 500")
        self.darab_hossza.setFixedWidth(50)
        input_field.addRow("Darab hossza (mm)", self.darab_hossza)
        self.darab_nbr = QLineEdit()
        self.darab_nbr.setPlaceholderText("Pl.: 2")
        self.darab_nbr.setFixedWidth(50)
        input_field.addRow("Darab mennyiség (mm)", self.darab_nbr)
        self.darab_label = QLineEdit()
        self.darab_label.setPlaceholderText("Pl.: Part 01")
        self.darab_label.setFixedWidth(50)
        input_field.addRow("Darab hossza (mm)", self.darab_label)
        data_field.addLayout(input_field)

        button_box = QHBoxLayout()
        # button_box.addStretch()
        add_button = QPushButton("Hozzáad")
        add_button.clicked.connect(self.add_item)
        del_button = QPushButton("Töröl")
        del_button.clicked.connect(self.delete_item)
        print_button = QPushButton("Print")
        print_button.clicked.connect(self.print_results)
        button_box.addWidget(add_button)
        button_box.addWidget(del_button)
        button_box.addWidget(print_button)
        data_field.addLayout(button_box)
        layout.addLayout(data_field,0,0)

        # List
        l1 = QTreeWidgetItem(["1", "B", "C", "D"])
        stock_table = QTreeWidget(self)
        # stock_table.resize(500,200)
        stock_table.setColumnCount(4)
        stock_table.setHeaderLabels(["Poz.", "Hossz", "Mennyiség", "Címke"])
        stock_table.addTopLevelItem(l1)
        
        layout.addWidget(stock_table,0,1)

        # Add stocks
        pattern_table = QHBoxLayout()
        layout.addLayout(pattern_table,1,0)
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



    def onFrameConfigure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))


    def update(self):
        #Tree 1
        self.tree = ttk.Treeview(self.rightframe, height = 11,
        yscrollcommand = self.vert_scroll.set, selectmode="browse")
        self.vert_scroll.configure(command=self.tree.yview)

        self.tree["columns"]=("1", "2", "3")
        self.tree.column("#0", width=40, minwidth=40, stretch="False")
        self.tree.column("1", width=50, minwidth=50, stretch="False")
        self.tree.column("2", width=50, minwidth=50, stretch="False")
        self.tree.column("3", width=100, minwidth=100, stretch="False")

        self.tree.heading("#0",text="Poz.",anchor=tk.W)
        self.tree.heading("1", text="Menny.",anchor=tk.W)
        self.tree.heading("2", text="Hossz",anchor=tk.W)
        self.tree.heading("3", text="Címke",anchor=tk.W)

        # Level 1
        i = 1
        for p in self.stocks.keys():
            index = i*10
            self.tree.insert("", "end", iid = p, text=index,
            values=(self.stocks[p]["nbr"], self.stocks[p]["len"],
            self.stocks[p]["label"]))
            self.tree.item(p, open=True)
            i += 1

        self.tree.grid(row=0, column = 0, sticky='WE',
        padx = 2.5, pady = (5, 2.5))


        # Display patterns
        for widget in self.canvasframe.winfo_children():
            widget.destroy()

        c = 0
        for m in self.results.keys():
            self.canvasframe.grid_columnconfigure(c, weight=1, minsize=40)
            self.stock_pattern = Stock_pattern(master=self.canvasframe,
            elements=self.results[m]["pattern"], max_length=self.stock_length)
            self.stock_pattern.grid(row=0, column=c, sticky='NSW', padx=(5, 0))

            multiply = self.results[m]["nbr"]
            self.infolabel1 = ttk.Label(self.canvasframe,
            text="x{0}".format(multiply), anchor="center")
            self.infolabel1.grid(row=1, column=c, sticky='NS', padx=(5, 0))
            c += 1


    def update_field(self, event=None):
        """ Regenerate tables and calculates cutting patterns
        dynamcially when focusing out of entry field.
        """

        self.stock_length = int(self.textbox1.get())
        self.cutting_width = int(self.textbox2.get())

        self.update()
        self.calculate()


    def add_item(self):
        """ Add item to stock list """

        uuid_str = str(uuid.uuid4())
        label = str(self.textbox3.get()) # Címke, bármit elfogadunk

        # Mennyiség, ha nincs vagy ha üres, akkor default = 1
        if (self.textbox4.get() == None) or (self.textbox4.get() == ""):
            nbr = 1
        else:
            nbr = int(self.textbox4.get())

        # Ha nincs hossz, akkor értelmetlen
        if (self.textbox5.get() == None) or (self.textbox5.get() == ""):
            print("Hiányzó hossz!")
            return

        else:
            try:
                len = int(self.textbox5.get())

            except Exception as e:
                print("Váratlan hiba: {0}".format(e))
                return

        # Ha a hossz túl nagy
        if len > self.stock_length:
            print("Szál túl hosszú!")
            pass

        else:
            self.stocks.update({uuid_str : {"nbr": nbr, "len": len, "label" : label}})

        self.update()
        self.calculate()


    def delete_item(self):
        """ Delete item from list """

        ids = []
        sections = []
        sel = self.tree.selection() # Kiválasztott 'item'-ek listája

        for s in sel: # Kiválasztott elemeken végigiterálok
            if s in self.stocks:
                del self.stocks[s]

        self.update()
        self.calculate()


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
            self.results[uuid_str] = {"pattern": actual_stock, "nbr" : 1}
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


    def print_results(self):
        """ Print results by default printer. """
        # https://stackoverflow.com/questions/12723818/print-to-standard-printer-from-python
        # https://stackoverflow.com/questions/2878616/programmatically-print-a-pdf-file-specifying-printer

        # Generate image
        # import io
        # import subprocess
        # from PIL import Image
        #
        # ps = self.canvas.postscript(colormode='color')
        # img = Image.open(io.BytesIO(ps.encode('utf-8')))
        # img.save('/tmp/test.jpg')
        #
        # return

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


    def help(self):
        help_info()


    def close_window(self):
        self.master.destroy()


def credits():
    print("\nSzalkalkulátor V1.2")
    print("Wetzl Viktor - 2020-01-11 - (C) Minden jog fenntartva!")


### Fő program
if __name__ == '__main__':
    app = QApplication([])
    app.setStyle('Fusion')

    main = MainWindow()
    main.show()
    main.center()
    app.exec()
    l.info("Main window open")

    credits()
    sys.exit()
