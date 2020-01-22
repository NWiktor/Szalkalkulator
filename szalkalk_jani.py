# -*- coding: utf-8 -*-#
import sys

celhossz = 6000 # Elérendő szálhossz (mm)
fureszlap_vast = 2 # Fűrészlap vastagsága (mm)
szalak = []  # 2D tömb, benne a szálhosszakkal
szalanyag_nev = "" ## Szálanyag elnevezése (pl.: 20x20x3 acél zártszv.)


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
print("\nHello Jani!")
help_info() ## Alap parancsok kiírása

try: # Amíg ki nem lépek Escape exceptionnel, addig ismétli
    # a kalkulációt/kiértékelést az inputs fv.-en belüli loop miatt
    inputs()

except Escape as e:
    print(e.value)

except KeyboardInterrupt:
    print("\nKilépés a programból!")

credits()
input("Kilépéshez nyomj 'Enter'-t!")
sys.exit()
