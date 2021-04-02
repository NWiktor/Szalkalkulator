# -*- coding: utf-8 -*-#
#!/usr/bin/python3

""" GUI (frontend) a Szálkalkulátor alkalmazáshoz.

Ez a program adott szálanyagok vágási sorrendjének meghatározására szolgál.


---- Libs ----
* Tkinter

---- Help ----

---- Info ----
Wetzl Viktor - 2021.04.01 - Minden jog fenntartva a birtoklásra, felhasználásra,
sokszorosításra, szerkesztésre, értékesítésre nézve, valamint az ipari
tulajdonjog hatálya alá eső felhasználások esetén is.
"""

import uuid
import sys
from tkinter import ttk
import tkinter as tk

release_date = "2021-04-21"
celhossz = 6000 # Elérendő szálhossz (mm)
fureszlap_vast = 2 # Fűrészlap vastagsága (mm)
szalak = []  # 2D tömb, benne a szálhosszakkal
szalanyag_nev = "" ## Szálanyag elnevezése (pl.: 20x20x3 acél zártszv.)


class Stock_pattern(tk.Canvas):
    global celhossz

    def __init__(self, master, max_length = celhossz, elements=[], **kwargs):
        self.field_height = 250
        self.cutting_width = 2
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
            42, act_length+item_length-self.cutting_width,
            fill="LightSteelBlue3", width=0)

            # Item text
            if k >= self.text_limit:
                self.create_text(20, act_length+(item_length)/2,
                font="Times 8", text="{0}".format(k))

            # Cutting width
            self.create_rectangle(0, act_length+item_length-self.cutting_width,
            42, act_length+item_length, fill="gray15", width=0)
            act_length += item_length


class App():
    def __init__(self, master):
        self.master = master
        self.master.geometry("600x550+100+100") #Ablak mérete +xpos(v) +ypos(f)
        self.master.maxsize(600, 550) # Az ablak max. mérete
        self.master.resizable(width=False, height=False)

        self.stock_length = 6000 # mm
        self.cutting_width = 3 # mm

        self.stocks = {}
        self.stocks = {"A" : {"nbr": 2, "len": 2345, "label": "proba"},
        "B" : {"nbr": 34, "len": 245633, "label": "proba2"}}

        self.results = []
        self.results = [[1450, 1450, 1450, 1450], [500, 500], [1000, 1000], [200, 400, 800]]

        self.init_window() # Inicializáló fv. meghívása


    # Init_window létrehozása (konstruktor)
    def init_window(self):
        global release_date

        self.master.title("Szálkalkulátor by W.V.") # Ablak cím beállítása

        # Widgets at master:
        self.leftframe = tk.Frame(self.master, width=300, height = 300)
        self.leftframe.grid(row=0, column=0, sticky="NWES")
        self.leftframe.config(bg="blue")
        self.leftframe.grid_columnconfigure(0, weight=1, minsize=150)
        self.leftframe.grid_columnconfigure(1, weight=1, minsize=150)

        self.rightframe = tk.Frame(self.master, width=300, height = 300)
        self.rightframe.grid(row=0, column=1, sticky="NWES")
        self.rightframe.config(bg="red")
        self.rightframe.grid_columnconfigure(0, weight=1, minsize=275)
        self.rightframe.grid_columnconfigure(1, weight=1, minsize=25)

        self.separator = ttk.Separator(self.master, orient=tk.HORIZONTAL)
        self.separator.grid(row = 1, columnspan = 2, sticky = 'WE',
        pady=5, padx=5)

        self.downframe = tk.Frame(self.master, width=600, height = 200)
        self.downframe.grid(row = 2, column = 0, columnspan=2, sticky="NWS")
        # self.downframe.config(bg="black")
        self.downframe.grid_rowconfigure(0, weight=1, minsize=200)

        # self.hori_scroll = ttk.Scrollbar(self.master, orient=tk.HORIZONTAL)
        # self.hori_scroll.grid(row = 3, columnspan = 2, sticky= 'WE',
        # padx = 5, pady=(2.5, 5))

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
        self.textbox1.bind("<Button-1>", self.clear_field)
        self.textbox1.bind("<FocusOut>", self.update_field)
        self.textbox1.grid(row=n, column=1, sticky = 'WE',
        padx = 2.5, pady=(5, 2.5))

        n += 1
        self.label2 = ttk.Label(self.leftframe, text="Fűrészlap vastagság")
        self.label2.grid(row=n, column=0, sticky = 'W',
        padx = (5, 2.5), pady=(5, 2.5))

        self.textbox2 = ttk.Entry(self.leftframe)
        self.textbox2.insert(0, "{0}".format(self.cutting_width))
        self.textbox2.bind("<Button-1>", self.clear_field)
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
        self.help_button = ttk.Button(self.leftframe, text="Segítség",
        command=self.help)
        self.help_button.grid(row=n, column=0, sticky = 'WE',
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


    def update(self):

        #Tree 1
        self.tree = ttk.Treeview(self.rightframe, height = 10,
        yscrollcommand = self.vert_scroll.set, selectmode="browse")
        self.vert_scroll.config(command=self.tree.yview)

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
            values=(self.stocks[p]["nbr"], self.stocks[p]["len"], self.stocks[p]["label"]))
            self.tree.item(p, open=True)
            i += 1

        self.tree.grid(row=0, column = 0, sticky='WE',
        padx = 2.5, pady = (5, 2.5))

        # Display patterns
        c = 0
        for m in self.results:
            self.downframe.grid_columnconfigure(c, weight=1, minsize=40)
            self.stock_pattern = Stock_pattern(master=self.downframe, elements=m)
            self.stock_pattern.grid(row=0, column=c, sticky='NSW', padx=(5, 0))

            multiply = 2
            self.infolabel1 = ttk.Label(self.downframe,
            text="x{0}".format(multiply), anchor="center")
            self.infolabel1.grid(row=1, column=c, sticky='NS', padx=(5, 0))
            c += 1


    def clear_field(self, event=None):
        print("clear_field")
        # self.textbox1.delete(0, tk.END)
        pass


    def update_field(self, event=None):
        print("focus_out")
        self.stock_length = int(self.textbox1.get())
        self.cutting_width = int(self.textbox2.get())

        print(self.stock_length)
        print(self.cutting_width)

        self.update()
        self.calculate()


    def add_item(self):
        print("Add item")

        uuid_str = str(uuid.uuid4())
        label = str(self.textbox3.get())
        nbr = int(self.textbox4.get())
        len = int(self.textbox5.get())

        if len > self.stock_length:
            print("Szál túl hosszú!")
            pass

        else:
            self.stocks.update({uuid_str : {"nbr": nbr, "len": len, "label" : label}})

        self.update()
        self.calculate()


    def delete_item(self):
        print("Delete item")

        ids = []
        sections = []
        sel = self.tree.selection() # Kiválasztott 'item'-ek listája

        for s in sel: # Kiválasztott elemeken végigiterálok
            # print(s)
            if s in self.stocks:
                del self.stocks[s]

        self.update()
        self.calculate()


    del oversized_item(self):
        print("Túl hosszú elem törlése")
        pass


    def calculate(self):
        print("Calculate")
        self.update()


    def help(self):
        help_info()


    def close_window(self):
        self.master.destroy()
        print("EXIT")



# Obsolete funcs to be refactored
def help_info():
    print("\n-- INFO --")
    print("A szálanyagok alaphosszúsága: {0} mm".format(celhossz))
    print("A fűrészlap vastagság: {0} mm".format(fureszlap_vast))
    print("Add meg a szálhosszat és a mennyiséget vesszővel elválasztva (pl.: 1300,4)")
    print("Az adatbevitel befejezéséhez és az összegzéshez írj be egy 'x' karaktert.")
    print("A szálhossz alapértékének módosításához írj be egy 'm' karaktert.")
    print("A fűrészlap vastagság módosításához írj be egy 'f' karaktert.")
    print("A help ismételt előhívásához nyomd meg az 'i' karaktert.")
    print("A kilépéshez nyomd meg az 'e' karaktert.")


def mod_fureszlap(): # Fűrészlap módosítása
    global fureszlap_vast

    try: #Input konvertálása integerré
        fureszlap_vast = int(key_input("\nA fűrészlap új vastagsága: "))

    except:
        print("Hibás adatbevitel! A fűrészlap vastagsága nem változott: {0} mm".format(fureszlap_vast))
        return

    print("A fűrészlap vastagság sikeresen megváltoztatva!")


def key_input(string):
    ki = input(string)

    if ki == "e":
        raise Escape()
    elif ki == "i":
        help_info()
    elif ki == "m":
        mod_celhossz()
    elif ki == "f":
        mod_fureszlap()
    elif ki == "x":
        tulhossz_torles() # Biztonság kedvéért
        if szalak == []:
            print("Nem adtál hozzá vágandó szálat!")
        else:
            kalk()
            inputs()
    else:
        return ki


def inputs():
    global szalanyag_nev
    input_list = []

    while True: # Száltípus elnevezése
        try:
            szalanyag_nev = key_input("\nAdd meg a vágandó szál nevét: ")
            if szalanyag_nev == None:
                continue

            break

        except ValueError:
            print("Nem megfelelő elnevezés!")

    print("Szálanyag: {0}".format(szalanyag_nev))

    while True: # Vágandó szálak hozzáadása
        try:
            data = key_input("\nAdd meg a vágandó szál hosszát és a mennyiségét: ")
            if data == None:
                continue
            else:
                input_list = data.split(",")

            hossz = int(input_list[0])

            try:
                menny = int(input_list[1])

            except IndexError:
                menny = 1
                print("Hiányos adatbevitel! A mennyiség beállítva: 1 db!")

            except ValueError:
                print("Mennyiségi érték hiba! Kérlek számértéket adj meg!")

            add_szal(hossz, menny)

        except ValueError:
            print("Szálhossz érték hiba! Kérlek számértéket adj meg!")


def tulhossz_torles(): ## Célhossznál nagyobb elemek utúlagos törlése - ha a hosszú elem korábban lett a listához adva
    if szalak == []: return
    torolt_hossz = []

    szalak.sort(reverse=True) # Szalak forditott sorrendbe állitasa
    while szalak != []:
        if szalak[0] > celhossz: # Ha az első elem hosszabb mint a célhossz
            torolt_hossz.append(szalak[0]) # A törlendő elemet hozzáadjuk a listához
            szalak.pop(0) # Az első elemet kivesszük a listából
        else:
            break

    if torolt_hossz != []:
        print("A célhossznál hosszabb elemek {0} törölve a listából!".format(torolt_hossz))


def mod_celhossz(): # Célhossz módosítása
    global celhossz

    try: #Input konvertálása integerré
        celhossz = int(key_input("\nA szálhossz új alapértéke: "))

    except:
        print("Hibás adatbevitel! A szálhossz értéke nem változott: {0} mm".format(celhossz))
        return

    print("A szálhossz alapérték sikeresen megváltoztatva!")
    tulhossz_torles()


def add_szal(szalhossz, menny): # szálanyag hozzáadása a tömbhöz
    if szalhossz > celhossz:
        print("Hibás adatbevitel: túl nagy szálhossz!")

    else:
        for i in range (0, menny): szalak.append(szalhossz)
        print("{0} db, {1} mm szálanyag hozzáadva a listához!".format(menny, szalhossz))


def kalk():
    szalak.sort(reverse=True) # csökkenő sorrendbe teszem a szálakat
    teljes_hossz = 0
    hulladek_hossz = 0
    hulladek_szazalek = 0
    eredmeny = [] # eredmény gyűjtő tömb
    hulladek = [] #hulladek gyüjtő tömb

    while szalak != []: # Amíg a szálak tömb nem nulla, fut a számítás
        akt_szal = "|" # akutális szál összetétele / string formátumban
        akt_hossz = 0 # aktuális szál szálhossza
        maradek = celhossz ## aktuális szál maradéka
        torolni = []

        for i in range(0, len(szalak)): # Végigmegyek a szálak tömb minden elemén
            if szalak[i] <= maradek: # Ha az aktuális száldarab rövidebb v egyenlő, mint a maradék
                akt_hossz += (szalak[i] + fureszlap_vast)  # Aktuális szálhosszhoz hozzáadom az elemet
                maradek -= (szalak[i] + fureszlap_vast) # Maradékból kivonom az elemet
                akt_szal += "| {0:>4} ".format(szalak[i]) # A szál összetételhez hozzáadom az elemet
                torolni.append(i) # torlendő elemek index listájához hozzáadni az aktuálisat

            else: # Ha az aktuális száldarab hosszabb, mint a maradék
                if maradek < szalak[-1]: # Ha a maradék kisebb, mint az utolsó (legrövidebb elem), akkor kilépek
                    break # For ciklus megtörése, kilépés a while ciklusba

        # Ha kész az iteráció összesítem a szálat
        akt_szal += "|| --> {0} mm".format(akt_hossz)
        eredmeny.append(akt_szal)

        if maradek > 0: # Ha a maradek hossz nagyobb mint nulla, akkor hulladek
            hulladek.append(maradek)
            hulladek_hossz += maradek

        torolni.sort(reverse=True) # torlendo indexek csökkenő sorrendbe állítása ( ez kell? )

        for k in range(0, len(torolni)): #felhasznált darabok törlése a tömbből
            szalak.pop(torolni[k])

    # Hulladék százalék kalkuláció
    teljes_hossz = len(eredmeny) * celhossz

    try: # Ha nem viszek be adatot, akkor nullával osztás következik.
        hulladek_szazalek = float(hulladek_hossz) / float(teljes_hossz) * 100

    except ZeroDivisionError:
        return

    # Ha készen vagyok, kiadom az eredményt
    print("\n" + "\n-- DARABOLÁSI TERV -- {0} --".format(szalanyag_nev))
    for p in range(0, len(eredmeny)):
        print(eredmeny[p]) # Eredmeny kiírása

    print("\n-- ÖSSZEGZÉS -- {0} --".format(szalanyag_nev))
    print("Szükséges szálmennyiség: {0} db ({1} mm)".format(len(eredmeny), celhossz))
    print("Hulladék mennyisége:     {0:.2f} % ({1} mm)".format(hulladek_szazalek, hulladek_hossz))
    print("Hulladékok: " + str(hulladek)) # Hulladek darabok


def credits():
    print("\nSzalkalkulátor V1.2")
    print("Wetzl Viktor - 2020-01-11 - (C) Minden jog fenntartva!")


class Escape(Exception):
    def __init__(self):
        self.value = "Kilépés a programból!"
    def __str__(self):
        return repr(self.value)





### Fő program
if __name__ == '__main__':
    root = tk.Tk()
    app = App(root)
    # root.wm_protocol('WM_DELETE_WINDOW', app.close_window) # 'X' gomb felülírása
    root.mainloop()

    sys.exit()




    # print("\nHello!")
    # help_info() ## Alap parancsok kiírása
    #
    # try: # Amíg ki nem lépek Escape exceptionnel, addig ismétli
    #     # a kalkulációt/kiértékelést az inputs fv.-en belüli loop miatt
    #     inputs()
    #
    # except Escape as e:
    #     print(e.value)
    #
    # except KeyboardInterrupt:
    #     print("\nKilépés a programból!")
    #
    # credits()
    # input("Kilépéshez nyomj 'Enter'-t!")
    # sys.exit()
