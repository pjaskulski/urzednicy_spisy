""" spis urzędników województwa sandomierskiego XVI-XVIII wieku """
import re
from pathlib import Path
import xml.dom.minidom
from urzednicy_sandomierscy_literatura import literatura


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
    "chęc.":"chęciński",
    "rad.":"radomski",
    "czech.":"Czechowski",
    "sand.":"sandomierski",
    "krak.":"krakowski",
    "sąd.":"sądecki",
    "lit.":"litewski",
    "sier.":"sieradzki",
    "lub.":"lubelski",
    "stęż.":"stężycki",
    "małog.":"małogojski",
    "wiśl.":"wiślicki",
    "nkorcz.":"nowokorczyński",
    "wojn.":"wojnicki",
    "opocz.":"opoczyński",
    "zaw.":"zawichojski",
    "pilz.":"pilzneński",
    "żarn.":"żarnowski",
    "poł.":"połaniecki"
}

# skróty nazw urzędów i powiązanych terminów
skroty_urz = {
    "burg.":"burgrabia",
    "chor.":"chorąży",
    "gen.":"generał",
    "klan":"kasztelan",
    "kom.":"komornik",
    "kpt.":"kapitan",
    "łow.":"łowczy",
    "miecz.":"miecznik",
    "mjr":"major",
    "reg.":"regent",
    "pcz.":"podczaszy",
    "sekr.":"sekretarz",
    "pis.":"pisarz",
    "sęd.":"sędzia",
    "pkom.":"podkomorzy",
    "skar.":"skarbnik",
    "płk":"pułkownik",
    "sta":"starosta",
    "psęd.":"podsędek",
    "stol.":"stolnik",
    "psta":"podstarości",
    "wda":"wojewoda",
    "pstol.":"podstoli",
    "wger.":"wicesgerent",
    "pwda":"podwojewodzi",
    "wrząd.":"wielkorządca"
}

skroty_inne = {
    "N ": "Nominacja",
    "R ": "Rezygnacja",
    "par.": "parafia"
}


class Person:
    """ klasa Person """
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
        self.stated_in = 'Urzędnicy województwa sandomierskiego XVI-XVIII wieku, w: Urzędnicy dawnej Rzeczypospolitej XII - XVIII wieku, t. IV, z. 3, 1993'
        self.id = ''
        self.reference_id = ''
        self.start_date = ''
        self.end_date = ''
        self.date = ''


def shortcuts(text: str) -> str:
    """ rozwijanie skrótów """
    text_tab = text.split(' ')
    for i, value in enumerate(text_tab):
        if text_tab[i].lower() in skroty_urz:
            text_tab[i] = skroty_urz[text_tab[i].lower()]

        elif text_tab[i].lower().replace(')', '') in skroty_urz:
            text_tab[i] = skroty_urz[text_tab[i].lower()] + ')'

        elif text_tab[i].lower().replace('(', '') in skroty_urz:
            text_tab[i] = '(' + skroty_urz[text_tab[i].lower()]

        elif text_tab[i].lower() in skroty_geo:
            text_tab[i] = skroty_geo[text_tab[i].lower()]

        elif text_tab[i].lower().replace(')', '') in skroty_geo:
            text_tab[i] = skroty_geo[text_tab[i].lower().replace(')', '')] + ')'

        elif text_tab[i].lower().replace('(', '') in skroty_geo:
            text_tab[i] = '(' + skroty_geo[text_tab[i].lower().replace('(', '')]

        elif text_tab[i].lower().replace('?', '') in skroty_geo:
            text_tab[i] = skroty_geo[text_tab[i].lower().replace('?', '')] + '?'

        elif text_tab[i].lower() in skroty_inne:
            text_tab[i] = skroty_inne[text_tab[i].lower()]

    return ' '.join(text_tab)


# from: https://stackoverflow.com/questions/26808913/split-string-at-commas-except-when-in-bracket-environment/26809037
def csplit(s:str):
    """ funkcja dzieli przekazany tekst na wiersze według średnika pomijając
        średniki w nawiasach, zwraca listę
    """
    parts = []
    bracket_level = 0
    current = []
    # trick to remove special-case of trailing chars
    for c in (s + ";"):
        if c == ";" and bracket_level == 0:
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

    # wzorce na daty
    patterns = [
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

        r'1\d{3}\s?-\s?1\d{3}',
        r'1\d{3}\s?-\s?\d{2}',
        r'\s?a.\s+\d{4}',
        r'\s?ok\.\s+\d{4}',
        r'\s+do\s+\d{4}',
        r'\d{4}'
    ]

    urzednik = Person()
    urzednik.text = person_text

    person_texts = csplit(person_text)
    person_text = person_texts[0].strip()
    position_text = person_texts[1].strip()

    # literatura?
    if position_text.endswith(")"):
        pos = position_text.rfind("(")
        urzednik.biblio = position_text[pos:].replace("(", "").replace(")", "")
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
        position_text = position_text[:pos]

    # dodatkowa literatura w danych urzędnika
    if person_text.endswith(")"):
        pos = person_text.rfind("(")
        urzednik_biblio = person_text[pos:].replace("(", "").replace(")", "")
        # czy to na pewno literatura
        if urzednik_biblio[0].isupper() and (',' in urzednik_biblio or 's.' in urzednik_biblio or 'nr ' in urzednik_biblio):
            t_biblio = urzednik_biblio.split(";")
            list_biblio = []
            if t_biblio:
                for t_bibl in t_biblio:
                    t_bibl = t_bibl.strip()
                    for skrot, rozwiniecie in literatura.items():
                        if skrot in t_bibl:
                            t_bibl = t_bibl.replace(skrot, rozwiniecie)
                            break
                    list_biblio.append(t_bibl)

            urzednik.biblio += list_biblio
            person_text = person_text[:pos]

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

    if not urzednik.coat_of_arms and p_herb:
        urzednik.coat_of_arms = p_herb

    # urzednik - dane
    # if 'i z Borku' in person_text:
    #     print()

    # jeżeli podpostać
    if person_text.startswith('- '):
        person_text = person_text[2:].strip()
        tmp_location = ''
        pattern_info = r'\([a-zA-ZĄŚĘŻŹĆŃŁÓąśężźćńłó\s\.\?,]+\)'
        matches = [x.group() for x in re.finditer(pattern_info, person_text)]
        for match in matches:
            tmp_info = match.strip().replace('(', '').replace(')', '')
            if (tmp_info.startswith('z ') or tmp_info.startswith('i z ')
                or tmp_info.startswith('i ze ') or ' z ' in tmp_info):
                tmp_location += ' ' + tmp_info
                tmp_location = double_space(tmp_location.strip())
            else:
                if urzednik.info:
                    urzednik.info += ',' + tmp_info
                else:
                    urzednik.info = tmp_info
            person_text = person_text.replace(match, '').replace(' , ', ', ')
            person_text = double_space(person_text)

        urzednik.name = person_text.strip()
        if tmp_location:
            if 'i ' in tmp_location:
                if p_location:
                    urzednik.name += ' ' + p_location + ' ' + tmp_location
                    urzednik.location = p_location + ' ' + tmp_location
                else:
                    urzednik.name += ' ' + tmp_location
                    urzednik.location = tmp_location
            else:
                urzednik.name += ' ' + tmp_location
                urzednik.location = tmp_location

    # pełna postać
    else:
        tmp_location = ''
        pattern_info = r'\([a-zA-Ząśężźćńłó\s\.\?,]+\)'
        matches = [x.group() for x in re.finditer(pattern_info, person_text)]
        for match in matches:
            tmp_info = match.strip().replace('(', '').replace(')', '')
            if tmp_info.startswith('z ') or tmp_info.startswith('i z ') or ' z ' in tmp_info:
                tmp_location += ' ' + tmp_info
                tmp_location = double_space(tmp_location.strip())
            else:
                if urzednik.info:
                    urzednik.info += ',' + tmp_info
                else:
                    urzednik.info = tmp_info
            person_text = person_text.replace(match, '').replace(' , ', ', ')
            person_text = double_space(person_text)

        pattern_rod = r'[A-ZŚŻŹĆŁ]{1}[\wąśężźćńłó]+:'
        match = re.search(pattern_rod, person_text)
        if match:
            urzednik.lineage = match.group().replace(':', '').strip()
            pos = person_text.find(match.group()) + len(match.group())
            person_text = double_space(person_text.replace(match.group(), ''))

        pattern_imie_location = r'^[A-ZŚŻŹĆŁ]{1}[\wąśężźćńłó]+,\s+z\s+[\wąśężźćńłó]+'
        match = re.search(pattern_imie_location, person_text)
        if match:
            urzednik_name = match.group().replace(',', '').strip()
            tmp_name = urzednik_name.split(' ')
            urzednik.name = f'{tmp_name[2]} {tmp_name[1]} {tmp_name[0]}'
            if tmp_name[1] == 'z':
                urzednik.location = f'{tmp_name[1]} {tmp_name[0]}'
                if tmp_location:
                    urzednik.location += ' ' + tmp_location
        else:
            urzednik.name = person_text.strip()

    if not urzednik.lineage and p_rod:
        urzednik.lineage = p_rod

    # czy to na pewno przechodzi z nadrzędnej postaci do podrzędnej?
    if not urzednik.location and p_location:
        urzednik.location = p_location
        urzednik.name += ' ' + p_location

    # if 'GWP' in position_text:
    #     print()

    # urzędy
    tmp_positions = position_text.split(",")
    for position in tmp_positions:
        position = position.strip()
        if position == '': # pomijanie pustych
            continue

        # test czy to nie jest tylko inf. o roku narodzin lub śmierci urzędnika, albo
        is_info = False
        patterns_info = [r'zm\.\s+a\.\s+\d{4}',
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

        urzad = Position()

        # lata urzędowania - wyszukiwanie
        year = ''
        for y in patterns:
            match = re.search(y, position)
            if match:
                year_n = match.group()
                year = year_n.replace("(","").replace(")","")
                break
        # jeżeli znaleziono lata urzędowania
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
            pattern_id = r'\)\s+\d{1,4}(\s+zob.\s+też\s+nr\s+\d{1,4})?'
            match = re.search(pattern_id, position)
            if match:
                urzad.id = match.group().replace(')','').strip()
        else:
            urzad.office = position.strip()

        # jeżeli brak id z wykazu to informacja o urzędzie nie pochodzi z tego tomu
        if not urzad.id:
            urzad.stated_in = ''

        if urzad.office:
            urzad.office = shortcuts(urzad.office).strip()
            urzednik.position.append(urzad)

    urzednik.info = urzednik.info.strip()
    urzednik.info = shortcuts(urzednik.info)
    if urzednik.name.endswith(','):
        urzednik.name = urzednik.name[:-1]
    return urzednik


if __name__ == '__main__':
    input_path = Path('.').parent / 'data/urzednicy_wojewodztwa_sandomierskiego_XVI_XVIII_wieku.txt'
    output_path = Path('.').parent / 'output/urzednicy_wojewodztwa_sandomierskiego_XVI_XVIII_wieku.xml'

    with open(input_path, 'r', encoding='utf-8') as f:
        data = f.readlines()

    # usunięcie niewidocznych znaków po ocr
    data = [re.sub(r'[\u00AD]', '', line) for line in data]

    lista = []
    person_location = person_herb = person_rod = ''

    for item in data:
        item = item.strip()
        if item != '':
            if item[0] == '-':
                osoba = get_person(item, person_location, person_herb, person_rod)
            else:
                osoba = get_person(item)
                person_location = osoba.location
                pos = -1
                if ' i z ' in person_location:
                    pos = person_location.find(' i z ')
                elif ' i ze ' in person_location:
                    pos =  person_location.find(' i ze ')
                if pos > -1:
                    person_location = person_location[:pos].strip()

                person_herb = osoba.coat_of_arms
                person_rod = osoba.lineage

            if osoba:
                lista.append(osoba)

    with open(output_path, 'w', encoding='utf-8') as f:
        xml_text = xml_start + '\n'
        for person in lista:
            rekord = person.get_xml()
            print(person.text)
            print()
            print(rekord)
            print()
            xml_text += rekord + '\n'
        xml_text += xml_end + '\n'
        t_xml = xml.dom.minidom.parseString(xml_text)
        xml_pretty_str = t_xml.toprettyxml()
        tmp = xml_pretty_str.split("\n")
        for line in tmp:
            if line.strip() != "":
                line = line.replace("\t", "    ")
                f.write(line+'\n')
