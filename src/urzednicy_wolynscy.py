""" spis urzędników wołyńskich XIV-XVIII w. """
import re
from pathlib import Path
import xml.dom.minidom
from urzednicy_wolynscy_literatura import literatura


# === wzór rekordu ===
#
# <person>
#   <name>nazwa (imię, imię i patronimik)</name>
#   <surname>nazwisko</surname>
#   <location>opcjonalnie, pisze się z</location>
#   <coat_of_arms>opcjonalnie, herb</coat_of_arms>
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
    "beł." : "bełski",
    "bracł." : "bracławski",
    "czern." : "czernihowski",
    "dub." : "dubieniecki",
    "kam." : "kamieniecki",
    "kij." : "kijowski",
    "kow." : "kowelski",
    "krak." : "krakowski",
    "krzem." : "krzemieniecki",
    "lit." : "litewski",
    "łuc." : "łucki",
    "now." : "nowogrodzki siewierski",
    "owr." : "owrucki",
    "pol." : "poleski",
    "sand." : "sandomierski",
    "włodz." : "włodzimierski",
    "woł." : "wołyński",
    "żyt." : "żytomierski"
}

# skróty nazw urzędów i powiązanych terminów
skroty_urz = {
    "chor.":"chorąży",
    "cz.":"cześnik",
    "horod.":"horodniczy",
    "klana":"kasztelana",
    "klan":"kasztelan",
    "klucz.":"klucznik",
    "łow.":"łowczy",
    "marsz.":"marszałek",
    "miecz.":"miecznik",
    "most.":"mostowniczy",
    "nam.":"namiestnik",
    "pcz.":"podczaszy",
    "pis.":"pisarz",
    "pkom.":"podkomorzy",
    "psęd.":"podsędek",
    "pskarb.":"podskarbi",
    "psta":"podstarości",
    "pstol.":"podstoli",
    "sęd.":"sędzia",
    "skarb.":"skarbnik",
    "sta":"starosta",
    "stol.":"stolnik",
    "wda":"wojewoda",
    "wdy":"wojewody"
}

skroty_inne = {
    "NN":"NN (nieznanego imienia)",
    "gr." : "grodzki",
    "gran." : "graniczny",
    "kor." : "koronny",
    "król." : "królewski",
    "mn." : "mniejszy",
    "rzk." : "rzekomy",
    "wzm." : "wzmiankowany",
    "N ": "Nominacja",
    "R ": "Rezygnacja",
    "d.": "deło",
    "hosp.": "hospodarski",
    "ndw." : "nadworny",
    "wlk." : "wielki"
}

urzedy = [
    "chor.", "chorąży", "cz.", "cześnik", "horod.", "horodniczy",
    "klan", "kasztelan", "klucz.", "klucznik", "łow.", "łowczy",
    "marsz.", "marszałek", "miecz.", "miecznik", "nam.", "namiestnik",
    "pcz.", "podczaszy", "pis.", "pisarz", "pkom.", "podkomorzy",
    "psęd.", "podsędek", "pskarb.", "podskarbi", "psta", "podstarości",
    "pstol.", "podstoli", "sęd.", "sędzia", "skarb.", "skarbnik",
    "sta", "starosta", "stol.", "stolnik", "wda", "wojewoda",
    "most.", "mostowniczy", "ciwun", "regent", "wojski", "poborca",
    "starościc", "thesaurarius", "kasztelanic", "podwojewodzi"
]

class Person:
    def __init__(self:str, name='') -> None:
        self.surname = name
        self.name = ''
        self.location = ''
        self.coat_of_arms = ''
        self.info = ''
        self.position = []
        self.biblio = []

    def get_xml(self) -> str:
        """ zwraca dane osoby w formacie xml """
        output = "<person>"
        if self.surname:
            output += f"<surname>{self.surname}</surname>\n"
        if self.name:
            if self.name == 'NN':
                self.name = 'NN (nieznanego imienia)'
            output += f"<name>{self.name}</name>\n"
        if self.location:
            output += f"<location>{self.location}</location>\n"
        if self.coat_of_arms:
            output += f"<coat_of_arms>{self.coat_of_arms}</coat_of_arms>\n"
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
                    output += f"<id>{posit.id}</id>"
                if posit.reference_id:
                    output += f"<reference_id>{posit.reference_id}</reference_id>"
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
        self.stated_in = 'Urzędnicy wołyńscy XIV-XVIII wieku, w: Urzędnicy dawnej Rzeczypospolitej XII - XVIII wieku, t.III, z. 5, 2007'
        self.id = ''
        self.reference_id = ''
        self.start_date = ''
        self.end_date = ''
        self.date = ''


def shortcuts(text: str) -> str:
    """ rozwijanie skrótów """
    text_tab = text.split(' ')
    for i in range(0, len(text_tab)):
        if text_tab[i].lower() in skroty_urz:
            text_tab[i] = skroty_urz[text_tab[i].lower()]
        elif text_tab[i].lower() in skroty_geo:
            text_tab[i] = skroty_geo[text_tab[i].lower()]
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


def get_person(person_text: str, p_name:str = '', p_herb:str = '') -> Person:
    """ przetwarza podany tekst na obiekt klasy Person """
    result = None
    person_text = person_text.strip()
    if person_text == '':
        return result

    # wzorce na daty
    patterns = [
        r'\(\s?\d{4}-\d{2},\s+\d{4}\)', # 1777-92, 1793
        r'\(\s?[XVI]+\s+w\.\s?\)',
        r'\(\s?zm\.\s+a\.\s+\d{4}\s?\)',
        r'\(zm\.\s+a\.\s+\d{1,2}\s+[XVI]{1,4}\s+\d{4}\)',
        r'\(\s?zm\.\s+\d{4}\s?\)',
        r'\(\s?a\.\s+\d{4}\s?\)',
        r'\(\s?\d{4}\s?(\?)?\)',
        r'\(\s?\d{4}\s?(\?)?\)',
        r'\(\s?(ok\.)?\s?\d{4}\s?-\s?\d{1,2}\s?\)',
        r'\(\s?\d{4}\s?-\s?\d{4}\s?\)',
        r'\(\s?\d{4}\/\d{1,2}\s?\)',
        r'\(\s?\d{4}\s?-\s?lata\s+osiemdziesiąte\s+XIII\s+w\.\)',
        r'\(\s?\d{4}\s?-\s?lata\s+[a-ząśężźćńłó\s]+\s[XVI]+\s+w\.\s?\)',
        r'\(\s?[a-ząśężźćńłó\s]+\s[XVI]+\s+w\.\s?\)',
        r'\(\s?\d{4}\s?albo\s?\d{4}\s?\)',
        r'\(\s?\d{4}\s?-\s?\d{2}\/\d{2}\s?\)', # 1278- 80/81, 1275­-80/81
        r'\((przed|po)\s+\d{4}(\?)?\s?\)', #przed 1308?, po 1304?

        r'\d{4}\s?-\s?\d{4}',
        r'\d{4}\s?-\s?\d{2}',
        r'\s?a.\s+\d{4}',
        r'\d{4}'
    ]

    urzednik = Person()

    # if 'Bogusz Fedorowicz' in person_text:
    #     print()


    # literatura?
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

    # nazwisko
    if p_name:
        urzednik.surname = p_name
        if ' z ' in urzednik.surname:
            tmp_name = urzednik.surname.split(" z ")
            urzednik.location = "z " + tmp_name[1].strip()
    else:
        pattern_nazwisko = r'^[\wąśężźćńłó]+,\s+z\s+[\wąśężźćńłó]+'
        match = re.search(pattern_nazwisko, person_text)
        if match:
            toponimik = match.group()
            tmp_topo = toponimik.split(',')
            urzednik.location = 'z ' + tmp_topo[0]
            urzednik.name = tmp_topo[1].replace(" z ", "").strip()
        else:
            #pattern_nazwisko = r'^[\wąśężźćńłó-]+'
            pattern_nazwisko = r'^[A-ZĄŚĘŻŹĆŃŁÓ]{1}([\w]+\s+z\s+[A-ZĄŚĘŻŹĆŃŁÓ]{1}[\w]+|[\w\ąśężźćńłó-]+)'
            match = re.search(pattern_nazwisko, person_text)
            if match:
                urzednik.surname = match.group().strip()
                if ' z ' in urzednik.surname:
                    tmp_name = urzednik.surname.split(" z ")
                    #urzednik.surname = tmp_name[0].strip()
                    urzednik.location = "z " + tmp_name[1].strip()

        person_text = re.sub(pattern_nazwisko, '', person_text).strip()

        # weryfikacja czy drugie słowo tesktu też nie jest nazwiskiem
        match = re.search(pattern_nazwisko, person_text)
        if match:
            tmp_nazwisko = match.group().strip()
            if tmp_nazwisko.endswith('ski') or tmp_nazwisko.endswith('cki') or tmp_nazwisko.endswith('dzki'):
                urzednik.surname += ' ' + tmp_nazwisko
                person_text = re.sub(pattern_nazwisko, '', person_text).strip()

    # herb
    if p_herb:
        urzednik.coat_of_arms = p_herb
    else:
        pattern_herb = r'(\s{1}|^)h\.\s+([\wąśężźćńłó\s]+\(\?\)|[\wąśężźćńłó\s]+|\?)'
        match = re.search(pattern_herb, person_text)
        if match:
            urzednik.coat_of_arms = match.group().replace('h.', '').strip()
            if urzednik.coat_of_arms == 'własnego':
                urzednik.coat_of_arms = 'h. własnego'
            elif urzednik.coat_of_arms == 'nieznanego':
                urzednik.coat_of_arms = 'h. nieznanego'
            elif urzednik.coat_of_arms == '?':
                urzednik.coat_of_arms = 'h. ?'

    pos_herb = -1
    if not p_herb:
        if urzednik.coat_of_arms:
            pos_herb = person_text.find(urzednik.coat_of_arms)
            if pos_herb > -1:
                pos_herb += len(urzednik.coat_of_arms)

    # literatura do herbu
    if not p_herb:
        herb_biblio = ''
        if '):' in person_text:
            herb_biblio_start = 0
            pos = person_text.find('):')
            for i in range(pos, 1, -1):
                if person_text[i] == '(':
                    herb_biblio_start = i
                    break
            if herb_biblio_start:
                herb_biblio = person_text[herb_biblio_start:pos+1]
        else:
            tmp_person_herb = person_text[pos_herb:].strip()
            if tmp_person_herb.startswith('('):
                pos = tmp_person_herb.find(')')
                if pos > -1:
                    herb_biblio = tmp_person_herb[:pos+1]
        if herb_biblio:
            # usnięcie literatury do herbu
            person_text = person_text.replace(herb_biblio, '')
            herb_biblio = herb_biblio.replace('(', '').replace(')', '').strip()
            t_biblio = herb_biblio.split(";")
            for t_bibl in t_biblio:
                t_bibl = t_bibl.strip()
                for skrot, rozwiniecie in literatura.items():
                    if skrot in t_bibl:
                        t_bibl = t_bibl.replace(skrot, rozwiniecie)
                        break
                urzednik.biblio.append(t_bibl)

    # imie
    if not p_name:
        # imie, jeżeli dwukropek to imie po dwukropku a potem już urząd lub urzędy
        # usunąć spacje,:, h.
        pattern_imie = r':\s+([A-Z]{1}[\w]+\s{1})*'
        match = re.search(pattern_imie, person_text)
        if match: # jeżeli imię/imiona po herbie
            p_imie = match.group().replace(':','').strip()
            urzednik.name = p_imie
        else:
            # jeżeli imię przed herbem
            pattern_imie = r'\s?([A-ZŚŁŻ{1}[a-ząśężźćńłó\.]+\s{1})*h\.'
            match = re.search(pattern_imie, person_text)
            if match and match.group().strip() != 'h.':
                p_imie = match.group().replace('h.', '').strip()
                urzednik.name = p_imie
            else: # jeżeli imię imiona po nazwisku a przed dodatkowymi informacjami w nawiasie
                pattern_imie = r'([A-ZŚŁŻ]{1}[\w\.]+\s{1})*'
                if '(' in person_text:
                    stop = person_text.find('(')
                    tmp_text = person_text[:stop]
                else:
                    tmp_text = person_text
                match = re.search(pattern_imie, tmp_text)
                if match:
                    p_imie = match.group().strip()
                    if urzednik.surname in p_imie:
                        p_imie = p_imie.replace(urzednik.surname, '').strip()
                    urzednik.name = p_imie
    else: # dla podpunktów
        pattern_imie_pod = r'-\s+([A-ZŚŁŻ]{1}[\w\.]+\s{1})*'
        match = re.search(pattern_imie_pod, person_text)
        if match:
            urzednik.name = match.group().replace('-','').strip()

    # weryfikacja czy dodatkowe nazwisko nie trafiło do imion:
    # if ' ' in urzednik.name:
    #     t_names = urzednik.name.split(' ')
    #     urzednik.name = ''
    #     for t_name_item in t_names:
    #         if t_name_item.strip() == '':
    #             continue
    #         if t_name_item.endswith('ski') or t_name_item.endswith('cki'): # or t_name_item.endswith('dzki'):
    #             urzednik.surname += ' ' + t_name_item
    #         else:
    #             if urzednik.name:
    #                 urzednik.name += ' ' + t_name_item
    #             else:
    #                 urzednik.name = t_name_item

    pos_forname = -1
    if urzednik.name:
        pos_forname = person_text.find(urzednik.name)
        if pos_forname > -1:
            pos_forname += len(urzednik.name)

    # czy location ukrywa się w imionach?
    if ' z ' in urzednik.name:
        match = re.search(r'z\s+[\wąśężźć”łó]+', urzednik.name)
        if match:
            urzednik.location = match.group().strip()

    # ddatkowe informacje, np. location
    pos_info = -1
    pattern_info = r'\([a-zA-Ząśężźćńłó\s\.\?,]+\)'
    # tymczasowo usuwanie herbu
    if urzednik.coat_of_arms and urzednik.coat_of_arms in person_text:
        person_text_tmp = double_space(person_text.replace(urzednik.coat_of_arms, '').strip())
    else:
        person_text_tmp = person_text

    matches = [x.group() for x in re.finditer(pattern_info, person_text_tmp)]
    for match in matches:
        tmp_info = match.strip().replace('(', '').replace(')', '')

        # jeżeli to wiek, to nie jest to dodatkowa informacja tylko data spr. urzędu
        if tmp_info == 'XVIII w.' or tmp_info == 'XVII w.':
            matches.remove(match)
            continue

        if 'z ' in tmp_info or 'von' in tmp_info:
            urzednik.location = tmp_info
        else:
            if urzednik.info:
                urzednik.info += ',' + tmp_info
            else:
                urzednik.info = tmp_info
    if matches:
        pos_info = person_text.find(matches[-1]) + len(matches[-1])

    pos = max(pos_forname, pos_herb, pos_info)

    positions_text = person_text[pos:]
    if ',' in positions_text:
        tmp_positions = csplit(positions_text)
    else:
        tmp_positions = [positions_text]

    # urzędy
    prev_office = ''
    for position in tmp_positions:
        position = position.strip()
        if position == '': # pomijanie pustych
            continue

        urzad = Position()

        # test czy to nie jest tylko inf. o roku narodzin lub śmierci urzędnika, albo
        # dokładna data rezygnacji z ostatniego urzędu
        is_info = False
        patterns_info = [r'zm\.\s+a\.\s+\d{4}',
                         r'zm\.\s+\d{4}',
                         r'zm\.\s+po\s+\d{4}',
                         r'zm\.\s+przed\s+\d{4}',
                         r'zm\.\s+ok\.\s+\d{4}',
                         r'zm.\s+[XVI]{1,4}\s+\d{1,4}',
                         r'zm.\s+po\s+[XVI]{1,4}\s+\d{1,4}',
                         r'zm\.\s+\d{1,2}\s+[XVI]{1,4}\s+\d{4}',
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
        for pattern in patterns_info:
            match = re.match(pattern, position)
            if match:
                is_info = True
                if urzednik.info:
                    urzednik.info += ', ' + position
                else:
                    urzednik.info = position
                break
        # jeżeli to nie był urząd to bez dalszego przetwarzania
        if is_info:
            continue

        

        # lata
        year = ''
        for y in patterns:
            match = re.search(y, position)
            if match:
                year_n = match.group()
                year = year_n.replace("(","").replace(")","")
                break

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
            urzad.office = position[:pos_year]
        else:
            urzad.office = position.strip()

        # obsługa urzędów wymienianych po przecinku np. "sta malborski, gdański,
        # chełmski" gdzie tylko dla pierwszej pozycji jest nazwa urzędu
        t_office = urzad.office.split(' ')
        if len(t_office) > 1:
            prev_office = t_office[0]
        else:
            if urzad.office.endswith('i') or urzad.office.endswith('.'):
                urzad.office = prev_office + ' ' + urzad.office

        # identyfikator z wykazu
        pattern_id = r'\)\s+\d{1,4}([abcdef]{1})?'
        match = re.search(pattern_id, position)
        if match:
            urzad.id = match.group().replace(')','').strip()
        else:
            # jeżeli nie ma id, ale jest odnośnik do id innej postaci
            pattern_id = r'\)\szob\.\s+nr\s+\d{1,4}([abcdef]{1})?'
            match = re.search(pattern_id, position)
            if match:
                urzad.reference_id = match.group().replace(')','').strip()


        # jeżeli brak id z wykazu to informacja o urzędzie nie pochodzi z tego tomu
        if not urzad.id:
            urzad.stated_in = ''

        if urzad.office:
            urzad.office = shortcuts(urzad.office).strip()
            urzednik.position.append(urzad)

    urzednik.info = urzednik.info.strip()
    urzednik.info = shortcuts(urzednik.info)
    return urzednik


if __name__ == '__main__':
    input_path = Path('.').parent / 'data/urzednicy_wolynscy_XIV_XVIII_wiek.txt'
    output_path = Path('.').parent / 'output/urzednicy_wolynscy_XIV_XVIII_wiek.xml'

    with open(input_path, 'r', encoding='utf-8') as f:
        data = f.readlines()

    # usunięcie niewidocznych znaków po ocr
    data = [re.sub(r'[\u00AD]', '', line) for line in data]

    lista = []
    person_name = person_herb = ''

    for item in data:
        item = item.strip()
        if item != '':
            if item[0] == '-':
                osoba = get_person(item, person_name, person_herb)
            else:
                osoba = get_person(item)
                person_name = osoba.surname
                person_herb = osoba.coat_of_arms

            if osoba:
                lista.append(osoba)

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
