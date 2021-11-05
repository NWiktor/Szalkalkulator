# -*- coding: utf-8 -*-#
#!/usr/bin/python3

""" GUI (frontend) a Szálkalkulátor alkalmazáshoz.

Ez a program adott szálanyagok vágási sorrendjének meghatározására szolgál.


---- Libs ----
* Tkinter
* win32api
* win32print

---- Help ----
* https://stackoverflow.com/questions/3085696/adding-a-scrollbar-to-a-group-of-widgets-in-tkinter/3092341#3092341

---- Info ----
Wetzl Viktor - 2021.04.01 - Minden jog fenntartva a birtoklásra, felhasználásra,
sokszorosításra, szerkesztésre, értékesítésre nézve, valamint az ipari
tulajdonjog hatálya alá eső felhasználások esetén is.
"""

import uuid
import sys

import tempfile
import win32api
import win32print

from tkinter import ttk
import tkinter as tk

release_date = "2021-04-21"


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


class App():
    def __init__(self, master):
        self.master = master
        self.master.geometry("600x565+100+100") #Ablak mérete +xpos(v) +ypos(f)
        self.master.maxsize(600, 565) # Az ablak max. mérete
        self.master.resizable(width=False, height=False)

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

        self.init_window() # Inicializáló fv. meghívása


    # Init_window létrehozása (konstruktor)
    def init_window(self):
        global release_date

        self.master.title("Szálkalkulátor by W.V.") # Ablak cím beállítása

        # Widgets at master:
        self.leftframe = tk.Frame(self.master, width=300, height = 300)
        self.leftframe.grid(row=0, column=0, sticky="NWES")
        # self.leftframe.config(bg="blue")
        self.leftframe.grid_columnconfigure(0, weight=1, minsize=150)
        self.leftframe.grid_columnconfigure(1, weight=1, minsize=150)

        self.rightframe = tk.Frame(self.master, width=300, height = 300)
        self.rightframe.grid(row=0, column=1, sticky="NWES")
        # self.rightframe.config(bg="red")
        self.rightframe.grid_columnconfigure(0, weight=1, minsize=275)
        self.rightframe.grid_columnconfigure(1, weight=1, minsize=25)

        self.separator = ttk.Separator(self.master, orient=tk.HORIZONTAL)
        self.separator.grid(row = 1, columnspan = 2, sticky = 'WE',
        pady=5, padx=5)

        self.downframe = tk.Frame(self.master, width=600, height=200)
        self.downframe.grid(row = 2, column = 0, columnspan=2, sticky="NWSE")
        # self.downframe.config(bg="black")
        self.downframe.grid_rowconfigure(0, weight=1, minsize=200)
        self.downframe.grid_rowconfigure(1, weight=1, minsize=16)
        self.downframe.grid_columnconfigure(0, weight=1, minsize=570)

        self.canvas = tk.Canvas(self.downframe, borderwidth=0)
        self.canvas.grid(row = 0, column = 0, sticky = "NWSE")
        self.canvasframe = tk.Frame(self.canvas)
        self.hori_scroll = ttk.Scrollbar(self.downframe, orient=tk.HORIZONTAL,
        command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=self.hori_scroll.set)
        self.hori_scroll.grid(row = 1, column = 0, sticky= 'WE',
        padx = 5, pady=(5,0))

        self.canvas.create_window((0,0), window=self.canvasframe, anchor="nw",
        tags="self.frame")
        self.canvasframe.bind("<Configure>", self.onFrameConfigure)

        style = ttk.Style()
        # style.theme_use('xpnative')
        style.theme_use('vista')

        # Widgets at leftframe:
        n = 0 # Row (line) number
        self.label1 = ttk.Label(self.leftframe, text="Szálhossz")
        self.label1.grid(row=n, column=0, sticky = 'W',
        padx = (5, 2.5), pady=(5, 2.5))

        self.textbox1 = ttk.Entry(self.leftframe)
        self.textbox1.insert(0, "{0}".format(self.stock_length))
        # self.textbox1.bind("<Button-1>", self.clear_field)
        self.textbox1.bind("<FocusOut>", self.update_field)
        self.textbox1.grid(row=n, column=1, sticky = 'WE',
        padx = 2.5, pady=(5, 2.5))

        n += 1
        self.label2 = ttk.Label(self.leftframe, text="Fűrészlap vastagság")
        self.label2.grid(row=n, column=0, sticky = 'W',
        padx = (5, 2.5), pady=(5, 2.5))

        self.textbox2 = ttk.Entry(self.leftframe)
        self.textbox2.insert(0, "{0}".format(self.cutting_width))
        # self.textbox2.bind("<Button-1>", self.clear_field)
        self.textbox2.bind("<FocusOut>", self.update_field)
        self.textbox2.grid(row=n, column=1, sticky = 'WE',
        padx = 2.5, pady=(5, 2.5))

        n += 1
        self.separator = ttk.Separator(self.leftframe, orient=tk.HORIZONTAL)
        self.separator.grid(row=n, column=0, columnspan=2, sticky='WE',
        pady=5, padx=(5, 2.5))

        n += 1
        self.label3 = ttk.Label(self.leftframe, text="Címke")
        self.label3.grid(row=n, column=0, sticky = 'W',
        padx = (5, 2.5), pady=(5, 2.5))

        self.textbox3 = ttk.Entry(self.leftframe)
        self.textbox3.insert(0, "")
        self.textbox3.grid(row=n, column=1, sticky = 'WE',
        padx = 2.5, pady=(5, 2.5))

        n += 1
        self.label4 = ttk.Label(self.leftframe, text="Mennyiség")
        self.label4.grid(row=n, column=0, sticky = 'W',
        padx = (5, 2.5), pady=(5, 2.5))

        self.textbox4 = ttk.Entry(self.leftframe)
        self.textbox4.insert(0, "")
        self.textbox4.grid(row=n, column=1, sticky = 'WE',
        padx = 2.5, pady=(5, 2.5))

        n += 1
        self.label5 = ttk.Label(self.leftframe, text="Hossz")
        self.label5.grid(row=n, column=0, sticky = 'W',
        padx = (5, 2.5), pady=(5, 2.5))

        self.textbox5 = ttk.Entry(self.leftframe)
        self.textbox5.insert(0, "")
        self.textbox5.grid(row=n, column=1, sticky = 'WE',
        padx = 2.5, pady=(5, 2.5))

        n += 1
        self.add_button = ttk.Button(self.leftframe, text="Hozzáad",
        command=self.add_item)
        self.add_button.grid(row=n, column=0, sticky = 'WE',
        padx = (5, 2.5), pady=2.5)

        self.delete_button = ttk.Button(self.leftframe, text="Törlés",
        command=self.delete_item)
        self.delete_button.grid(row=n, column=1, sticky = 'WE',
        padx = 2.5, pady=2.5)

        n += 1
        self.separator = ttk.Separator(self.leftframe, orient=tk.HORIZONTAL)
        self.separator.grid(row=n, column=0, columnspan=2, sticky='WE',
        pady=5, padx=(5, 2.5))

        n += 1
        self.print_button = ttk.Button(self.leftframe, text="Print",
        command=self.print_results)
        self.print_button.grid(row=n, column=0, sticky = 'WE',
        padx = (5, 2.5), pady=2.5)

        self.close_button = ttk.Button(self.leftframe, text="Kijelentkezés",
        command=self.close_window)
        self.close_button.grid(row=n, column=1, sticky = 'WE',
        padx = 2.5, pady=2.5)

        n += 1
        self.about = ttk.Label(self.leftframe,
        text="by Wetzl Viktor - {0}".format(release_date), anchor="center")
        # self.about.bind("<Button-1>", redirect_to_webpage)
        self.about.grid(row=n, column=0, columnspan=2, sticky = 'WE',
        pady=5, padx=(5, 2.5))

        # Widgets at rightframe:
        self.vert_scroll = ttk.Scrollbar(self.rightframe, orient="vertical")
        self.vert_scroll.grid(row = 0, column = 1, sticky='N'+'S',
        padx = (2.5, 5), pady=(5, 2.5))

        # Dynamic update of contents:
        self.update() # Betölti a treeview-et


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


    # def clear_field(self, event=None):
    #     print("clear_field")
    #     # self.textbox1.delete(0, tk.END)
    #     pass


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
        import io
        import subprocess
        from PIL import Image

        ps = self.canvas.postscript(colormode='color')
        img = Image.open(io.BytesIO(ps.encode('utf-8')))
        img.save('/tmp/test.jpg')

        return

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
    root = tk.Tk()
    app = App(root)
    root.mainloop()

    credits()
    sys.exit()
