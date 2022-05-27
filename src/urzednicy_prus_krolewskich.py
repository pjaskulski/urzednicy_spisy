""" spis urzędników prus królewskich XV-XVIII w. """
import re
from pathlib import Path
import xml.dom.minidom
from urzednicy_prus_krolewskich_literatura import literatura


# === wzór rekordu ===
#
# <person>
#   <name>nazwa (imię, imię i patronimik, imię i nazwisko)</name>
#   <location>opcjonalnie, pisze się z</location>
#   <coat_of_arms>opcjonalnie, herb</coat_of_arms>
#   <info>opcjonalnie, dodatkowe informacje</info>
#   <bibliography>opcjonalnie literatura:
#       <biblio>pozycja literatury</biblio>
#   </bibliography>
#   <position>
#       <stated_in>Źródło</stated_in>
#       <id>identyfikator w źródle (numer w wykazie urzędników)</id>
#       <office>nazwa urzędu</office>
#       <start_date>poczatek urzędowania</start_date>
#       <end_date>koniec urzędowania</end_date>
#       <date>jeżeli znana jest tylko jedna data</date>
#   </position>
# </person>

xml_start = '''<?xml version="1.0" encoding="UTF-8"?>
<persons>
'''
xml_end = "</persons>"

skroty_geo = {
    "cheł.": "chełmiński",
    "pom.": "pomorski",
    "człuch.": "człuchowski",
    "prus.": "pruski",
    "elb.": "elbląski",
    "puc.": "pucki",
    "gd.": "gdański",
    "św.": "świecki",
    "malb.": "malborski",
    "tcz.": "tczewski",
    "michał.": "michałowski",
    "tor.": "toruński",
    "mirach.": "mirachowski",
    "tuch.": "tucholski",
    "Cheł.": "chełmiński",
    "Pom.": "pomorski",
    "Człuch.": "człuchowski",
    "Prus.": "pruski",
    "Elb.": "elbląski",
    "Puc.": "pucki",
    "Gd.": "gdański",
    "Św.": "świecki",
    "Malb.": "malborski",
    "Mlb.": "malborski",
    "Tcz.": "tczewski",
    "Michał.": "michałowski",
    "Tor.": "toruński",
    "Mirach.": "mirachowski",
    "Tuch.": "tucholski"
}

# skróty nazw urzędów i powiązanych terminów
skroty_urz = {
    "bgr.": "burgrabia",
    "chor.": "chorąży",
    "cz.": "cześnik",
    "gub.":"gubernator",
    "klan": "kasztelan",
    "ław.": "ławnik",
    "miecz.": "miecznik",
    "pcz.": "podczaszy",
    "pis.": "pisarz",
    "p.s. skarb.": "pisarz skarbowy",
    "pkom.": "podkomorzy",
    "psk.": "podskarbi",
    "reg.": "regent",
    "sęd.": "sędzia",
    "sta": "starosta",
    "stol.": "stolnik",
    "wda": "wojewoda",
    "wreg.": "wiceregent",
    "wwda": "wicewojewoda",
    "mieszcz.":"mieszczanin",
    "nadw.":"nadworny",
    "gr.":"grodzki",
    "łow.": "łowczy"
}

urzedy = ['burgrabia', 'kanclerz', 'kustosz', 'landwójt', 'prefekt', 'komornik', 
    'wojski', 'łoźniczy', 'gubernator', 'kasztelan', 'ławnik', 'miecznik', 'podczaszy',
    'pisarz', 'pisarz skarbowy', 'podkomorzy', 'podskarbi', 'regent', 'sędzia', 'stolnik',
    'wójt', 'celnik', 'giermek', 'włodarz', 'łożniczy', 'namiestnik', 'klucznik',
    'podkanclerzy', 'starosta', 'wiceregent', 'wicewojewoda',
    'chor.', 'pstol.', 'cz.', 'sęd.', 'klan', 'skarb.', 'łow.', 'pis.', 'p.s. skarb.', 
    'ław.', 'sta', 'pcz.', 'stol.', 'pkom.', 'wda', 'wreg.', 'wwda', 'sta', 'reg.', 
    'psk.', 'miecz.', 'gub.', 'bgr.'
    ]

class Person:
    def __init__(self:str, name='') -> None:
        self.name = name
        self.forname = ''
        self.location = ''
        self.coat_of_arms = ''
        self.info = ''
        self.position = []
        self.biblio = []

    def get_xml(self) -> str:
        """ zwraca dane osoby w formacie xml """
        output = "<person>"
        if self.name:
            output += f"<name>{self.name}</name>\n"
        if self.forname:
            output += f"<forname>{self.forname}</forname>\n"
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
        self.stated_in = 'Urzędnicy Prus Królewskich XV-XVIII wieku, w: Urzędnicy dawnej Rzeczypospolitej XII - XVIII wieku, t.V, z. 2, 1990'
        self.id = ''
        self.start_date = ''
        self.end_date = ''
        self.date = ''


def shortcuts(text: str) -> str:
    """ rozwijanie skrótów """
    text_tab = text.split(' ')
    for i in range(0, len(text_tab)):
        if text_tab[i] in skroty_urz:
            text_tab[i] = skroty_urz[text_tab[i]]
        elif text_tab[i] in skroty_geo:
            text_tab[i] = skroty_geo[text_tab[i]]
        
    return ' '.join(text_tab)


# from: https://stackoverflow.com/questions/26808913/split-string-at-commas-except-when-in-bracket-environment/26809037
def csplit(s):
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
        r'\d{4}'
    ]

    urzednik = Person()

    if 'Burgerssdorff von' in person_text:
        print()

    # literatura?
    if person_text.endswith(")"):
        pos = person_text.rfind("(")
        urzednik.biblio = person_text[pos:].replace("(", "").replace(")", "")
        t_biblio = urzednik.biblio.split(",")
        list_biblio = []
        if t_biblio:
            for t_bibl in t_biblio:
                t_bibl = t_bibl.strip()
                if t_bibl in literatura:
                    list_biblio.append(literatura[t_bibl])
                elif 'PSB' in t_bibl:
                    list_biblio.append(t_bibl.replace('PSB', 'Polski Słownik Biograficzny'))
                elif t_bibl.startswith('s. '):
                    list_biblio[-1] = list_biblio[-1] + ', ' + t_bibl
                else:
                    list_biblio.append(t_bibl)

            urzednik.biblio = list_biblio

        person_text = person_text[:pos]

    # nazwisko
    if p_name:
        urzednik.name = p_name
    else:
        #pattern_nazwisko = r'^[\w]+'
        pattern_nazwisko = r'^[\w]+(\s+von\s{1})?'
        match = re.search(pattern_nazwisko, person_text)
        if match:
            urzednik.name = match.group().strip()
        person_text = re.sub(pattern_nazwisko, '', person_text).strip()

    # herb
    if p_herb:
        urzednik.coat_of_arms = p_herb
    else:
        #pattern_herb = r'h\.\s+[\w\s]+'
        pattern_herb = r'h\.\s+([\w\s]+\(\?\)|[\w\s]+)'
        match = re.search(pattern_herb, person_text)
        if match:
            urzednik.coat_of_arms = match.group().replace('h.', '').strip()
            if urzednik.coat_of_arms == 'własnego':
                urzednik.coat_of_arms = 'h. własnego'
            elif urzednik.coat_of_arms == 'nieznanego':
                urzednik.coat_of_arms = 'h. nieznanego'

    pos_herb = -1
    if urzednik.coat_of_arms:
        pos_herb = person_text.find(urzednik.coat_of_arms)
        if pos_herb > -1:
            pos_herb += len(urzednik.coat_of_arms)

    # imie
    if not p_name:
        # imie, jeżeli dwukropek to imie po dwukropku a potem już urząd lub urzędy
        # usunąć spacje,:, h.
        pattern_imie = r':\s+([A-Z]{1}[\w]+\s{1})*'
        match = re.search(pattern_imie, person_text)
        if match: # jeżeli imię/imiona po herbie
            p_imie = match.group().replace(':','').strip()
            urzednik.forname = p_imie
        else: # jeżeli imię przed herbem
            pattern_imie = r'\s?[\w]+\s+h\.'
            pattern_imie = r'\s?([A-Z{1}[a-ząśężźćńłó]+\s{1})*h\.'
            match = re.search(pattern_imie, person_text)
            if match:
                p_imie = match.group().replace('h.', '').strip()
                urzednik.forname = p_imie
            else: # jeżeli imię imiona po nazwisku a przed dodatkowymi informacjami w nawiasie
                pattern_imie = r'([A-ZŚŁŻ]{1}[\w]+\s{1})*'
                if '(' in person_text:
                    stop = person_text.find('(')
                    tmp_text = person_text[:stop]
                else:
                    tmp_text = person_text
                match = re.search(pattern_imie, tmp_text)
                if match:
                    p_imie = match.group().strip()
                    if urzednik.name in p_imie:
                        p_imie = p_imie.replace(urzednik.name, '').strip()
                    urzednik.forname = p_imie
    else: # dla podpunktów
        #pattern_imie_pod = r'•\s+[A-ZŚŁŻ]{1}[\w]+'
        pattern_imie_pod = r'•\s+([A-ZŚŁŻ]{1}[\w]+\s{1})*'
        match = re.search(pattern_imie_pod, person_text)
        if match:
            urzednik.forname = match.group().replace('•','').strip()

    pos_forname = -1
    if urzednik.forname:
        pos_forname = person_text.find(urzednik.forname)
        if pos_forname > -1:
            pos_forname += len(urzednik.forname)

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
        if position.strip() == '': # pomijanie pustych
            continue

        urzad = Position()

        # lata
        year = ''
        for y in patterns:
            match = re.search(y, position)
            if match:
                year_n = match.group()
                year = year_n.replace("(","").replace(")","")
                break

        if year:
            if "-" in year:
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
    input_path = Path('.').parent / 'data/urzednicy_prus_krolewskich_XV-XVIII_wieku.txt'
    output_path = Path('.').parent / 'output/urzednicy_prus_krolewskich_XV-XVIII_wieku.xml'

    with open(input_path, 'r', encoding='utf-8') as f:
        data = f.readlines()

    # usunięcie niewidocznych znaków po ocr
    data = [re.sub(r'[\u00AD]', '', line) for line in data]

    lista = []
    person_name = person_herb = ''

    for item in data:
        item = item.strip()
        if item != '':
            if item[0] == '•':
                osoba = get_person(item, person_name, person_herb)
            else:
                osoba = get_person(item)
                person_name = osoba.name
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
