""" urzędnicy łęczyccy, sieradzcy i wieluńscy XIII-XV wiek """
import re
import xml.dom.minidom
from pathlib import Path

from urzednicy_leczyccy_xii_xv_literatura import literatura

# === wzór rekordu ===
#
# <person>
#   <name>nazwa (imię, imię i patronimik)</name>
#   <surname>nazwisko</surname>
#   <location>opcjonalnie, pisze się z</location>
#   <coat_of_arms>opcjonalnie, herb</coat_of_arms>
#   <lineage>opcjonalnie, ród</lineage>
#   <info>opcjonalnie, dodatkowe informacje</info>
#   <position>
#       <stated_in>Źródło</stated_in>
#       <id>identyfikator w źródle (numer w wykazie urzędników)</id>
#       <reference_id>odnośnik do id innej postaci gdzie jest wzmianka
#       na temat urzędu obecnej postacji</reference_id>
#       <office>nazwa urzędu</office>
#       <start_date>poczatek urzędowania</start_date>
#       <end_date>koniec urzędowania</end_date>
#       <date>jeżeli znana jest tylko jedna data</date>
#   </position>
#   <bibliography>opcjonalnie literatura:
#       <biblio>pozycja literatury</biblio>
#   </bibliography>
# </person>

xml_start = '''<?xml version="1.0" encoding="UTF-8"?>
<persons>
'''
xml_end = "</persons>"

skroty_geo = {
    "Brzez.":"brzeziński",
    "Ostrz.":"ostrzeszowski",
    "Inowł.":"inowłodzki",
    "Rozp.":"rozpierski",
    "Kaz.":"kazimierski",
    "Sier.":"sieradzki",
    "Krak.":"krakowski",
    "Spic.":"spicymierski",
    "Łęcz.":"łęczycki",
    "Wiel.":"wieluński",
    "Maz.":"mazowiecki",
    "Wlkp.":"wielkopolski",
    "brzez.":"brzeziński",
    "ostrz.":"ostrzeszowski",
    "inowł.":"inowłodzki",
    "rozp.":"rozpierski",
    "kaz.":"kazimierski",
    "sier.":"sieradzki",
    "krak.":"krakowski",
    "spic.":"spicymierski",
    "łęcz.":"łęczycki",
    "wiel.":"wieluński",
    "maz.":"mazowiecki",
    "wlkp.":"wielkopolski"
}

# skróty nazw urzędów i powiązanych terminów
skroty_urz = {
    "arcbp":"arcybiskup",
    "pkom.":"podkomorzy",
    "bp":"biskup",
    "płow.":"podłowczy",
    "chor.":"chorąży",
    "psęd.":"podsędek",
    "cz.":"cześnik",
    "pstol.":"podstoli",
    "kan.":"kanonik",
    "sęd.":"sędzia",
    "klan":"kasztelan",
    "skarb.":"skarbnik",
    "łow.":"łowczy",
    "sta":"starosta",
    "miecz.":"miecznik",
    "stol.":"stolnik",
    "pcz.":"podczaszy",
    "wda":"wojewoda"
}

skroty_inne = {
    "m.":"mniejszy",
    "w.":"większy",
    "gen.":"generalny",
    "król.":"królewski",
    " A ":"awans",
    " N ":"nominacja",
    " R ":"rezygnacja"
}

# lista urzędów i skrótów urzędów i innych słów  do wykrywania poczatku listy urzędów
urzedy = [
    "może podkomorzy", "pleban", "może podkanclerzy",
    "włodarz", "może klan", "wojski", "notariusz", "marszałek",
    "syn ", "pisarz", "podkoni", "pisarz", "komornik",
    "siostrzeniec", "magister", "kanclerz", "podkoni",
    "podskarbi", "brat", "kustosz", "wójt", "komornik",
    "lożniczy", "łożniczy", "tenutariusz", "burgrabia",
    "arcbp ","arcybiskup", "pkom.", "podkomorzy", "wnuk",
    "może tożsamy", "błędnie jako", "zapewne brat",
    "może kanclerz", "ochmistrz", "dziekan", "dziad",
    "może sęd.", "bratanek", "dworzanin", "konarski",
    "może miecz.", "może pkom.", "tutor",
    "bp", "biskup", "płow.", "podłowczy",
    "chor.", "chorąży", "psęd.", "podsędek",
    "cz.", "cześnik", "pstol.", "podstoli",
    "kan.", "kanonik", "sęd.", "sędzia",
    "klan ", "kasztelan", "skarb.", "skarbnik",
    "łow.", "łowczy", "sta ", "starosta",
    "miecz.", "miecznik", "stol.", "stolnik",
    "pcz.", "podczaszy", "wda ", "wojewoda"
]

patterns_date = [
        r'\(\s?\d{4}\s+-\s+R\s\d{1,2}\s+[XVI]{1,4}\s+\d{4}\s?\)', # 1677 - R 18 IV 1712
        r'\(\s?\d{4}-\d{2},\s+\d{4}\)', # 1777-92, 1793
        r'\(\s?[XVI]+\s+w\.\s?\)',
        r'\(\s?zm\.\s+a\.\s+\d{4}\s?\)',
        r'\(\s?\d{4}\s?-\s?zm\.\s+a\.\s+\d{4}\s?\)', # 1670 - zm. a. 1699
        r'\(\s?\d{4}\s?-\s?zm\.\s+\d{4}\s?\)', # 1794 - zm. 1804)
        r'\(zm\.\s+a\.\s+\d{1,2}\s+[XVI]{1,4}\s+\d{4}\)',
        r'\(\s?zm\.\s+\d{4}\s?\)',
        r'\(\s?\d{4}-\d{2},\s+\d{4}\s?\)', # 1335-36, 1343
        r'\(\s?\d{4}-\d{2}\s+i\s+\d{4}\s+-\s+zm\.\s+a\.\s+\d{1,2}\s+[XVI]{1,4}\s+\d{4}\s?\)', # 1651-59 i 1661 - zm. a. 23 II 1665
        r'\(\s?\d{4}\s+-\s+zm\.\s+a\.\s+\d{1,2}\s+[XVI]{1,4}\s+\d{4}\s?\)',
        r'\(\s?a\.\s+\d{4}\s?\)',
        r'\(\s?a\.\s+\d{4}\?\s?\)',
        r'\(\s?\d{4}\s?(\?)?\)',
        r'\(\s?\d{4}\s?(\?)?\)',
        r'\(\s?(ok\.)?\s?\d{4}\s?-\s?\d{1,2}\s?\)',
        r'\(\s?ok\.\s+\d{4}\s?\?\)', # ok. 1488?
        r'\(\s?\d{4}\s?-\s?\d{4}\s?\)',
        r'\(\s?\d{4}\/\d{1,2}\s?\)',
        r'\(\s?\d{4}\s?-\s?lata\s+osiemdziesiąte\s+XIII\s+w\.\)',
        r'\(\s?\d{4}\s?-\s?lata\s+[a-ząśężźćńłó\s]+\s[XVI]+\s+w\.\s?\)',
        r'\(\s?[a-ząśężźćńłó\s]+\s[XVI]+\s+w\.\s?\)',
        r'\(\s?\d{4}\s?albo\s?\d{4}\s?\)',
        r'\(\s?\d{4}\s?-\s?\d{2}\/\d{2}\s?\)', # 1278- 80/81, 1275­-80/81
        r'\((przed|po)\s+\d{4}(\?)?\s?\)', #przed 1308?, po 1304?
        r'\(\d{4},\s+\d{4}\)', # (1485, 1487)

        r'1\d{3}\s?-\s?1\d{3}',
        r'1\d{3}\s?-\s?\d{2}',
        r'\s?a.\s+\d{4}',
        r'\s?ok\.\s+\d{4}',
        r'\s+do\s+\d{4}',
        r'\d{4}'
    ]

patterns_birth_death = [r'zm\.\s+a\.\s+\d{4}',
                         r'zm\.\s+a\.\s+[XVI]{1,4}\s+\d{4}',
                         r'zm\.\s+\d{4}',
                         r'zm\.\s+po\s+\d{4}',
                         r'zm\.\s+przed\s+\d{4}',
                         r'zm\.\s+ok\.\s+\d{4}',
                         r'zm.\s+[XVI]{1,4}\s+\d{1,4}',
                         r'zm.\s+po\s+[XVI]{1,4}\s+\d{1,4}',
                         r'zm\.\s+\d{1,2}\s+[XVI]{1,4}\s+\d{4}',
                         r'poch\.\s+\d{1,2}\s+[XVI]{1,4}\s+\d{4}',
                         r'zm\.\s+\d{1,2}\/\d{1,2}\s+[XVI]{1,4}\s+\d{4}', #  zm. 18/19 X 1580
                         r'zm\.\s+po\s+\d{1,2}\s+[XVI]{1,4}\s+\d{4}',
                         r'zm\.\s+przed\s+\d{1,2}\s+[XVI]{1,4}\s+\d{4}',
                         r'zm\.\s+a\.\s+\d{1,2}\s+[XVI]{1,4}\s+\d{4}',
                         r'zm\.\s+\?\s+a\.\s+\d{1,2}\s+[XVI]{1,4}\s+\d{4}',
                         r'zm\.\s+\d{4}\s+-\s+a\.\s+\d{1,2}\s+[XVI]{1,4}',
                         r'zm\.\s+\d{1,2}-\d{1,2}\s+[XVI]{1,4}\s+\d{4}',
                         r'R\s+ok\.\s+\d{1,2}\s+[XVI]{1,4}\s+\d{4}', # R ok. 1 VIII 1789
                         r'poch\.\s+w', # poch. w Kniehyninie
                         r'urodzony\s+\d{1,2}\s+[XVI]{1,4}\s+\d{4}',  # urodzony 2 IX 1693
                    ]

class Person:
    def __init__(self:str, name='') -> None:
        self.surname = name
        self.name = ''
        self.location = ''
        self.coat_of_arms = ''
        self.lineage = ''
        self.info = ''
        self.position = []
        self.biblio = []
        self.text = ''

    def get_xml(self) -> str:
        """ zwraca dane osoby w formacie xml """
        output = "<person>"
        if self.surname:
            output += f"<surname>{self.surname}</surname>\n"
        if self.name:
            output += f"<name>{self.name}</name>\n"
        if self.location:
            output += f"<location>{self.location}</location>\n"
        if self.coat_of_arms:
            output += f"<coat_of_arms>{self.coat_of_arms}</coat_of_arms>\n"
        if self.lineage:
            output += f"<lineage>{self.lineage}</lineage>\n"
        if self.info:
            output += f"<info>{self.info}</info>\n"
        if self.position:
            output += "<positions>\n"
            for posit in self.position:
                output += "<position>\n"
                if posit.office:
                    output += f"<office>{posit.office}</office>\n"
                if posit.stated_in:
                    output += f"<stated_in>{posit.stated_in}</stated_in>\n"
                if posit.id:
                    output += f"<id>{posit.id}</id>\n"
                if posit.reference_id:
                    output += f"<reference_id>{posit.reference_id}</reference_id>\n"
                if posit.start_date:
                    output += f"<start_date>{posit.start_date}</start_date>\n"
                if posit.end_date:
                    output += f"<end_date>{posit.end_date}</end_date>\n"
                if posit.date:
                    output += f"<date>{posit.date}</date>\n"
                output += '</position>\n'
            output += "</positions>\n"
        if self.biblio:
            output += "<bibliography>\n"
            for bibl in self.biblio:
                output += f"<biblio>{bibl}</biblio>\n"
            output += "</bibliography>\n"
        output += "</person>\n"
        return output

class Position:
    def __init__(self, office:str='') -> None:
        self.office = office
        self.stated_in = 'Urzędnicy łęczyccy, sieradzcy i wieluńscy XIII-XV wieku w: Urzędnicy dawnej Rzeczypospolitej XII - XVIII wieku, t. II, z. 1, 1985'
        self.id = ''
        self.reference_id = ''
        self.start_date = ''
        self.end_date = ''
        self.date = ''


def shortcuts(text: str) -> str:
    """ rozwijanie skrótów """
    text_tab = text.split(' ')
    for i, value in enumerate(text_tab):
        if text_tab[i].lower() in skroty_geo:
            text_tab[i] = skroty_geo[text_tab[i].lower()]

        elif text_tab[i].lower().replace(')', '') in skroty_geo:
            text_tab[i] = skroty_geo[text_tab[i].lower().replace(')', '')] + ')'

        elif text_tab[i].lower().replace('(', '') in skroty_geo:
            text_tab[i] = '(' + skroty_geo[text_tab[i].lower().replace('(', '')]

        elif text_tab[i].lower().replace('?', '') in skroty_geo:
            text_tab[i] = skroty_geo[text_tab[i].lower().replace('?', '')] + '?'

        elif text_tab[i].lower() in skroty_urz:
            text_tab[i] = skroty_urz[text_tab[i].lower()]

        elif text_tab[i].lower().replace(')', '') in skroty_urz:
            text_tab[i] = skroty_urz[text_tab[i].lower()] + ')'

        elif text_tab[i].lower().replace('(', '') in skroty_urz:
            text_tab[i] = '(' + skroty_urz[text_tab[i].lower()]

        elif text_tab[i].lower() in skroty_inne:
            text_tab[i] = skroty_inne[text_tab[i].lower()]

    return ' '.join(text_tab)


# from: https://stackoverflow.com/questions/26808913/split-string-at-commas-except-when-in-bracket-environment/26809037
def csplit(s:str):
    """ funkcja dzieli przekazany tekst na wiersze według przecinka pomijając
        przecinki w nawiasach, zwraca listę
    """
    parts = []
    bracket_level = 0
    current = []
    # trick to remove special-case of trailing chars
    for c in (s + ","):
        if c == "," and bracket_level == 0:
            parts.append("".join(current))
            current = []
        else:
            if c == "(":
                bracket_level += 1
            elif c == ")":
                bracket_level -= 1
            current.append(c)
    return parts


def double_space(value:str) -> str:
    """ usuwa podwójne spacje z przekazanego tekstu """
    return ' '.join(value.strip().split())


def get_person(person_text: str, p_location:str='', p_herb:str='', p_rod:str='') -> Person:
    """ przetwarza podany tekst na obiekt klasy Person """
    result = None
    person_text = person_text.strip()
    if person_text == '':
        return result

    urzednik = Person()
    urzednik.text = person_text

    # jeżeli na końcu wpisu jest literatura w nawiasie
    if person_text.endswith(")"):
        pos = person_text.rfind("(")
        urzednik.biblio = person_text[pos:].replace("(", "").replace(")", "")
        t_biblio = urzednik.biblio.split(";")
        list_biblio = []
        if t_biblio:
            for t_bibl in t_biblio:
                t_bibl = t_bibl.strip()
                for skrot, rozwiniecie in literatura.items():
                    if skrot in t_bibl:
                        t_bibl = t_bibl.replace(skrot, rozwiniecie)
                        break
                list_biblio.append(t_bibl)

        urzednik.biblio = list_biblio
        person_text = person_text[:pos]

    # jeżeli w rekordzie są nawiasy klamrowe to od razu do informacji dodatkowych
    if '{' in person_text:
        pattern_dodatkowe = r'\{[a-zA-ZąśężźćńłóĄŚĘŻŹĆŃŁÓ\.,\s2340]+\}'
        match = re.search(pattern_dodatkowe, person_text)
        if match:
            urzednik.info = match.group().replace('{','').replace('}','').strip()
            person_text = person_text.replace(match.group(),'').strip()

    # location na początku
    pattern_location = r'^[A-ZĄŚĘŻŹĆŃŁÓ]{1}[a-ząśężźćńłó]+([\(A-Za-ząśężźćńłóĄŚĘŻŹĆŃŁÓ\s\.\)]+)?,\s+z\s+'
    match = re.search(pattern=pattern_location, string=person_text)
    if match:
        urzednik.location = match.group().strip()
        person_text = person_text.replace(match.group(), '')
    # jeżeli nie znaleziono location ale przekazano z rekordu nadrzędnego
    if not urzednik.location and p_location:
        urzednik.location = p_location

    # podział na część z inf o osobie i część z inf o urzędach osoby
    best_pos = 999999
    for u_item in urzedy:
        pos = person_text.find(u_item)
        if pos != -1 and pos < best_pos:
            best_pos = pos

    if best_pos != 999999:
        position_text = person_text[best_pos:].strip()
        person_text = person_text[:best_pos].strip()
    else:
        print(f'ERROR: nie znaleziono listy urzędów, [{person_text}] ')
        exit()

    # jeżeli jest herb
    pattern_herb = r'(\s{1}|^)h\.\s+([\wąśężźćńłó\s]+\(\?\)|[\wąśężźćńłó\s]+\??|\?)'
    match = re.search(pattern_herb, person_text)
    if match:
        urzednik.coat_of_arms = match.group().replace('h.', '').strip()
        if urzednik.coat_of_arms == 'własnego':
            urzednik.coat_of_arms = 'h. własnego'
        elif urzednik.coat_of_arms == 'nieznanego':
            urzednik.coat_of_arms = 'h. nieznanego'
        elif urzednik.coat_of_arms == '?':
            urzednik.coat_of_arms = 'h. ?'

        person_text = person_text.replace(match.group(), '')

    # jeżeli nie znaleziono herbu ale jest przekazany z rekordu narzędnego
    if not urzednik.coat_of_arms and p_herb:
        urzednik.coat_of_arms = p_herb

    # jeżeli jest podany ród
    pattern_rod = r'[A-ZŚŻŹĆŁ]{1}[\wąśężźćńłó]+:'
    match = re.search(pattern_rod, person_text)
    if match:
        urzednik.lineage = match.group().replace(':', '').strip()
        person_text = person_text.replace(urzednik.lineage, '') # zostaje dwukropek!
        # za informacją o rodzie jest zwykle imię osoby
        person_imie = r':\s{1,}([A-ZĄŚĘŻŹĆŃŁÓ]{1}[a-ząśężźćńłó]+\s+)*'
        match = re.search(person_imie, person_text)
        if match:
            urzednik.name = match.group().replace(':','').strip()
            person_text = person_text.replace(match.group(), '')

        # po tych operacjach czyszczenie ewentualnych wielokrotnych spacji
        person_text = double_space(person_text)

    # jeżeli nie znaleziono rodu ale był przekazany z rekordu nadrzędnego
    if not urzednik.lineage and p_rod:
        urzednik.lineage = p_rod

    # jeżeli kolejne dodatkowe informacje w nawiasach zwykłych
    pattern_dodatkowe = r'\([a-zA-ZąśężźćńłóĄŚĘŻŹĆŃŁÓ\.,\s]+\)'
    match = re.search(pattern_dodatkowe, person_text)
    if match:
        dodatkowe = match.group().replace('(','').replace(')','').strip()
        if urzednik.info:
            urzednik.info += ', ' + dodatkowe
        else:
            urzednik.info = dodatkowe
        person_text = person_text.replace(match.group(),'').strip()

    person_text = person_text.strip()
    if person_text == ',':
        person_text = ''
    if person_text != '':
        if not urzednik.name:
            urzednik.name = person_text
            if urzednik.name.startswith('-'):
                urzednik.name = urzednik.name[1:].strip()
        else:
            urzednik.name += ', ' + person_text

    # przetwarzanie listy urzędów i informacji dodatkowych podanych wśród urzędów
    #tmp_positions = position_text.split(",")
    tmp_positions = csplit(position_text)
    for position in tmp_positions:
        position = position.strip()
        if position == '': # pomijanie pustych zapisów
            continue

        # test czy to nie jest tylko inf. o roku narodzin lub śmierci urzędnika, albo
        is_info = False

        for pattern in patterns_birth_death:
            match = re.match(pattern, position)
            if match:
                is_info = True
                if urzednik.info:
                    urzednik.info += ', ' + position
                else:
                    urzednik.info = position
                break
        # jeżeli to nie był urząd to bez dalszego przetwarzania, skrypt przechodzi
        # do kolejnego potencjalnego urzędu z listy
        if is_info:
            continue

        # test czy to nie jest tylko informacja o pokrewieństwie
        is_relation = False
        relations = ['syn', 'ojciec', 'wnuk', 'brat', 'dziad', 'bratanek', 'siostrzeniec']
        for r_item in relations:
            if r_item in position:
                if urzednik.info:
                    urzednik.info += ', ' + position
                else:
                    urzednik.info = position
                is_relation = True
                break
        # jeżeli to nie był urząd to bez dalszego przetwarzania, skrypt przechodzi
        # do kolejnego potencjalnego urzędu z listy
        if is_relation:
            continue

        urzad = Position()

        # lata urzędowania - wyszukiwanie dat
        year = ''
        for y in patterns_date:
            match = re.search(y, position)
            if match:
                year_n = match.group()
                year = year_n.replace("(","").replace(")","")
                break
        # przetwarzanie jeżeli znaleziono lata urzędowania
        if year:
            if "-" in year and ',' not in year:
                tmp_year = year.split("-")
                urzad.start_date = tmp_year[0].strip()
                urzad.end_date = tmp_year[1].strip()
                if len(urzad.end_date) == 2:
                    urzad.end_date = urzad.start_date[:2] + urzad.end_date
                elif len(urzad.end_date) == 3 and urzad.end_date.endswith('?'):
                    urzad.end_date = urzad.start_date[:2] + urzad.end_date
                elif '/' in urzad.end_date and len(urzad.end_date) == 5:
                    urzad.end_date = urzad.start_date[:2] + urzad.end_date
            else:
                urzad.date = year

        pos_year = -1
        if year:
            pos_year = position.find(year_n)
            urzad.office = position[:pos_year].strip()

            # identyfikator z wykazu
            pattern_id = r'\)\s+[A-Z]{1}\s+\d{1,4}(\s+zob.\s+też\s+nr\s+\d{1,4})?'
            match = re.search(pattern_id, position)
            if match:
                urzad.id = match.group().replace(')','').strip()
        else:
            urzad.office = position.strip()

        # jeżeli brak id z wykazu to informacja o urzędzie nie pochodzi z tego tomu
        if not urzad.id:
            urzad.stated_in = ''

        # rozwinięcie skrótów i zapis urzędu do listy urzędów
        if urzad.office:
            urzad.office = shortcuts(urzad.office).strip()
            urzednik.position.append(urzad)

    # zapis danych w obiekcie urzednik
    urzednik.info = urzednik.info.strip()
    urzednik.info = shortcuts(urzednik.info)
    if urzednik.name.endswith(','):
        urzednik.name = urzednik.name[:-1].strip()
    return urzednik

# -------------------------------- MAIN ----------------------------------------

if __name__ == '__main__':
    input_path = Path('.').parent / 'data/urzednicy_łęczyccy_sieradzcy_i_wieluńscy_XIII_XV_wieku.txt'
    output_path = Path('.').parent / 'output/urzednicy_leczyccy_sieradzcy_i_wielunscy_XIII_XV_wieku.xml'

    with open(input_path, 'r', encoding='utf-8') as f:
        data = f.readlines()

    # usunięcie ewentualnych niewidocznych znaków po ocr
    data = [re.sub(r'[\u00AD]', '', line) for line in data]

    lista = [] # lista znalezionych osób

    # wartości globalne przekazywane do rekordów podrzędnych
    person_location = person_herb = person_rod = ''

    for item in data:
        item = item.strip()
        if item != '':
            if item[0] == '-':
                osoba = get_person(item, person_location, person_herb, person_rod)
            else:
                osoba = get_person(item)
                person_location = osoba.location
                person_herb = osoba.coat_of_arms
                person_rod = osoba.lineage

            if osoba:
                lista.append(osoba)
                print(osoba.name, '@', osoba.location)

    with open(output_path, 'w', encoding='utf-8') as f:
        xml_text = xml_start + '\n'
        for person in lista:
            rekord = person.get_xml()
            xml_text += rekord + '\n'
        xml_text += xml_end + '\n'
        t_xml = xml.dom.minidom.parseString(xml_text)
        xml_pretty_str = t_xml.toprettyxml()
        tmp = xml_pretty_str.split("\n")
        for line in tmp:
            if line.strip() != "":
                line = line.replace("\t", "    ")
                f.write(line+'\n')
