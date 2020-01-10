# -*- coding: utf-8 -*-#
import sys

celhossz = 6000 # Elérendő szálhossz (mm)
szalak = []  # 2D tömb, benne a szálhosszakkal
szalanyag_nev = "" ## Szálanyag elnevezése (pl.: 20x20x3 acél zártszv.)


def help_info():
    print("\n-- INFO --")
    print("Add meg a szálhosszat és a mennyiséget vesszővel elválasztva (pl.: 1300,4)")
    print("Az adatbevitel befejezéséhez és az összegzéshez írj be egy 'x' karaktert.")
    print("A szálhossz alapértékének módosításához írj be egy 'm' karaktert.")
    print("A help ismételt előhívásához nyomd meg az 'i' karaktert.")
    print("A kilépéshez nyomd meg az 'e' karaktert.")


def inputs():
    global szalanyag_nev
    input_list = []
    szalanyag_nev = input("\nAdd meg a vágandó szál nevét: ")

    if szalanyag_nev == "e": ## Ha a beírt billentyű 'e', akkor kilép.
        raise Escape()

    else:
        print("Szálanyag: {0}".format(szalanyag_nev))

    while True:
        try:
            input_list = input("\nAdd meg a vágandó szál hosszát és a mennyiségét: ").split(",")

            if input_list[0] == "x":
                print("Adatbevitel vége!")
                break

            elif input_list[0] == "e":
                raise Escape()

            elif input_list[0] == "m":
                mod_celhossz()

            elif input_list[0] == "i":
                help_info()

            else:
                hossz = int(input_list[0])

                try:
                    menny = int(input_list[1])

                except IndexError:
                    menny = 1
                    print("Hiányos adatbevitel! A mennyiség alapértéke: 1!")

                add_szal(hossz, menny)

        except ValueError:
            print(" Érték hiba! Kérlek számértéket adj meg!")


def mod_celhossz(): # Célhossz módosítása
    global celhossz
    celh = 0
    torolni_hosszu = []
    torolt_hossz = []

    try: #Input konvertálása integerré
        celh = int(input("\nA szálhossz új alapértéke: "))
        celhossz = celh

    except:
        print("Hibás adatbevitel! A szálhossz értéke nem változott: {0}".format(celhossz))
        return

    ## Célhossznál nagyobb elemek utúlagos törlése - ha a hosszú elem korábban lett a listához adva
    for s in range(0, len(szalak)):
        if szalak[s] > celhossz:
            torolni_hosszu.append(s) # A törlendő indexet hozzáadjuk a listához
            torolt_hossz.append(szalak[s]) # A törlendő elemet hozzáadjuk a listához
        else:
            continue

    torolni_hosszu.sort(reverse=True)
    for st in range(0, len(torolni_hosszu)): # a túl hosszú darabok törlése a tömbből
        szalak.pop(torolni_hosszu[st])

    print("Célhossznál hosszabb elemek ({0}) törölve a listából!".format(torolt_hossz))
    print("\nA szálhossz alapérték sikeresen megváltoztatva!")


def add_szal(szalhossz, menny): # szálanyag hozzáadása a tömbhöz
    if szalhossz > celhossz:
        print("Hibás adatbevitel: túl nagy szálhossz!")

    else:
        for i in range (0, menny):
            szalak.append(szalhossz)

        print("{0} db, {1} mm szálanyag hozzáadva a listához!".format(menny, szalhossz))


def kalk():
    szalak.sort(reverse=True) # csökkenő sorrendbe teszem a szálakat
    teljes_hossz = 0
    hulladek_hossz = 0
    hulladek_szazalek = 0
    eredmeny = [] # eredmény gyűjtő tömb
    hulladek = []

    while szalak != []: # Amíg a szálak tömb nem nulla, fut a számítás
        akt_szal = "|" # akutális szál összetétele / string
        akt_hossz = 0 # aktuális szál szálhossza
        maradek = celhossz ## aktuális szál maradéka
        torolni = []

        for i in range(0, len(szalak)): # Végigmegyek a szálak tömb minden elemén
            if szalak[i] <= maradek: # Ha az aktuális száldarab rövidebb, mint a maradék
                akt_hossz += szalak[i]  # Aktuális szálhosszhoz hozzáadom az elemet
                maradek -= szalak[i] # Maradékból kivonom az elemet
                akt_szal += "| {0:>4} ".format(szalak[i]) # A szál összetételhez hozzáadom az elemet
                torolni.append(i) # torlendp elemek indexéhez hozzáadni az aktuálisat

            else: # Ha az aktuális száldarab hosszabb, mint a maradék
                if maradek < szalak[len(szalak)-1]: # Ha a maradék kisebb, mint az utolsó (legrövidebb elem), akkor kilépek
                    break

                else:
                    continue

        # Ha kész az iteráció összesítem a szálat
        akt_szal += "|| --> {0} mm".format(akt_hossz)
        eredmeny.append(akt_szal)

        if maradek > 0: # Ha a maradek hossz nagyobb mint nulla, akkor hulladek
            hulladek.append(maradek)
            hulladek_hossz += maradek

        else:
            pass

        torolni.sort(reverse=True) # torlendo indexek megforditasa

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

    # Hulladek darabok
    print(hulladek)


def credits():
    print("\nSzalkalkulator V1.0.1")
    print("Wetzl Viktor - 2020-01-08 - (C) Minden jog fenntartva!")


class Escape(Exception):
    def __init__(self):
        self.value = "Kilépés a programból!"
    def __str__(self):
        return repr(self.value)


### Fő program
print("\nHello Jani!")
help_info() ## Alap parancsok kiírása

try:
    while True:
        inputs()
        kalk()

except Escape as e:
    print(e.value)

except KeyboardInterrupt:
    print("\nKilépés a programból!")

credits()
sys.exit()
