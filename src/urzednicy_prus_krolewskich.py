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
#   <biblio>opcjonalnie literatura</biblio>
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
    "wwda": "wicewojewoda"
}

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
    "tuch.": "tucholski"
}

urzedy = ['kanclerz', 'kustosz', 'landwójt', 'prefekt', 'komornik', 'wojski', 'łoźniczy',
    'wójt', 'celnik', 'giermek', 'włodarz', 'łożniczy', 'namiestnik', 'klucznik',
    'podkanclerzy',
    'chor.', 'pstol.', 'cz.', 'sęd.', 'klan', 'skarb.', 'łow.',
    'sta', 'pcz.', 'stol.', 'pkom.', 'wda'
    ]

class Person:
    def __init__(self:str, name='') -> None:
        self.name = name
        self.location = ''
        self.coat_of_arms = ''
        self.info = ''
        self.position = []
        self.biblio = ''

    def get_xml(self) -> str:
        """ zwraca dane osoby w formacie xml """
        output = "<person>"
        if self.name:
            output += f"<name>{self.name}</name>\n"
        if self.location:
            output += f"<location>{self.location}</location>\n"
        if self.coat_of_arms:
            output += f"<coat_of_arms>{self.coat_of_arms}</coat_of_arms>\n"
        if self.info:
            output += f"<info>{self.info}</info>\n"
        if self.biblio:
            output += f"<biblio>{self.biblio}</biblio>\n"
        if self.position:
            for posit in self.position:
                output += f"<position>\n"
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
        output += "</person>\n"
        return output

class Position:
    def __init__(self, office:str='') -> None:
        self.office = office
        self.stated_in = 'Urzędnicy Pomorza Wschodniego do 1309 roku, w: Urzędnicy dawnej Rzeczypospolitej XII - XVIII wieku, t.V, z. 1, 1989'
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


def pos_urzad(text: str) -> int:
    """ pozycja nazwy urzedu """
    pos = -1
    # bez szukania w nawiasach
    tmp_text = re.sub(r'\([^)]*\)', '', text)
    tmp_text = double_space(tmp_text)
    text_tab = tmp_text.split(' ')
    find_urz = ''
    for word in text_tab:
        if word in urzedy:
            find_urz = word
            break

    if find_urz:
        start = 0
        while pos == -1:
            pos = text.find(find_urz, start)
            if ')' in text:
                start = text.find('(')
                stop = text.find(')')
                if pos > start and pos < stop:
                    pos = -1
                    start = stop
    
    return pos


def get_person(person_text: str) -> Person:
    """ przetwarza podany tekst na obiekt klasy Person """
    result = None
    person_text = person_text.strip()
    if person_text == '':
        return result

    # wzorce na daty
    patterns = [
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

    # literatura?
    if person_text.endswith(")"):
        pos = person_text.rfind("(")
        urzednik.biblio = person_text[pos:].replace("(", "").replace(")", "")
        t_biblio = urzednik.biblio.split(",")
        if t_biblio:
            if t_biblio[0] in literatura:
                t_biblio[0] = literatura[t_biblio[0]]
            urzednik.biblio = ', '.join(t_biblio)
            urzednik.biblio = double_space(urzednik.biblio)

        person_text = person_text[:pos]

    # if 'Arnold (syn Arnolda wdy Św.)' in person_text:
    #     print()

    if ',' in person_text:
        #print(person_text)
        tmp_parts = csplit(person_text)
        parts = []
        prepare_part = ''
        for part in tmp_parts:
            is_urzad = False
            tmp = re.sub(r'\([^)]*\)', '', part)
            for word in urzedy:
                if word in tmp:
                    is_urzad = True
                    break
            if is_urzad:
                if prepare_part:
                    part = double_space(prepare_part + ', ' + part)
                parts.append(part)
                prepare_part = ''
            else:
                if prepare_part:
                    prepare_part += ', ' + part
                else:
                    prepare_part = part
    else:
        parts = [item]

    # czasami dwie funkcje wymienione jako "cześnik 1290 i klucznik 1291"
    # ale nie należy rozdzielać "wójt i celnik pomorski (1299)"  bo mają wspólną datę
    new_parts = [parts[0]]
    for i in range(1, len(parts)):
        year_count = len(re.findall('\d{4}', parts[i]))
        if ' i ' in parts[i] and year_count > 1:
            t_parts = parts[i].split(' i ')
            for t_part in t_parts:
                new_parts.append(t_part)
        else:
            new_parts.append(parts[i])

    parts = new_parts

    name = info = name_urzad = urzad_id = ''
    
    for i in range(0, len(parts)):    
        if i == 0:           
            year = urzad_id = ''
            for y in patterns:
                match = re.search(y, parts[0])
                if match:
                    year_n = match.group()
                    year = year_n.replace("(","").replace(")","")
                    pattern = r'\)\s+\d{1,3}'
                    match1 = re.search(pattern, parts[0])
                    if match1:
                        urzad_id = match1.group().replace(")","").strip()
                    break

            if year:
                pos = parts[i].find(year_n)
                tmp_part = parts[0][:pos].strip()
            else:
                tmp_part = parts[0].strip()
            
            #tmp_part = re.sub(r'\([^)]*\)', '', tmp_part)
            pos = pos_urzad(tmp_part)
            if pos != -1:
                name_part = tmp_part[:pos].strip()
                if name_part.endswith(','):
                    name_part = name_part[:-1]
                name_urzad = tmp_part[pos:].strip()
                
                if '(' in name_part:
                    match = re.search(r'\([^)]*\)', name_part)
                    if match:
                        match_txt = match.group()
                        urzednik.info += match_txt
                        name_part = name_part.replace(match_txt, '').strip()

                if ',' in name_part:
                    tmp = name_part.split(",")
                    name_part = tmp[0].strip()
                    urzednik.info += ", ".join(tmp[1:])

                if ' z ' in name_part:
                    tmp_name = name_part.split(" z ")
                    urzednik.name = tmp_name[0].strip()
                    urzednik.location = "z " + tmp_name[1].strip()
                else:
                    urzednik.name = name_part

            else:
                print(f'ERROR: brak urzędu: {tmp_part}')
                exit()

            urzad = Position()
            urzad.id = urzad_id
            
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
            
            urzad.office = name_urzad

            if urzad.office:
                urzad.office = shortcuts(urzad.office)
                urzednik.position.append(urzad) 
        
        # dalsze części z urzędami         
        else:
            name_urzad = year = urzad_id = ''
            tmp = []
            if '(' in parts[i]:
                tmp = re.split('\(|\)', parts[i])
            else:
                for y in patterns:
                    match = re.search(y, parts[i])
                    if match:
                        # mamy urząd i rok
                        part1 = match.group()
                        part2 = parts[i].replace(part1, '').strip()
                        tmp = [part2, part1, '']
                        break
                if not tmp:
                        # mamy tylko urząd?
                        tmp = [parts[i], '', '']
            
            if len(tmp) == 3:
                name_urzad = tmp[0].strip()
                year = tmp[1].strip()
                urzad_id = tmp[2].strip()    
                
                urzad = Position()
            
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
                
                urzad.office = name_urzad
                urzad.id = urzad_id
                # jeżeli nie ma id to nie jest urząd opisany w tym tomie urzędników
                if not urzad.id:
                    urzad.stated_in = ''

                if urzad.office:
                    urzad.office = shortcuts(urzad.office)
                    urzednik.position.append(urzad)
            else:
                print(f"ERROR: {parts[i]}")
                exit()

    urzednik.info = urzednik.info.strip()
    urzednik.info = urzednik.info.replace('(','').replace(')','')
    urzednik.info = shortcuts(urzednik.info)
    return urzednik


if __name__ == '__main__':
    input_path = Path('.').parent / 'data/urzednicy_pomorza_wschodniego_do_1309_roku.txt'
    output_path = Path('.').parent / 'output/urzednicy_pomorza_wschodniego_do_1309_roku.xml'

    with open(input_path, 'r', encoding='utf-8') as f:
        data = f.readlines()

    lista = []
    for item in data:
        if item.strip() != '':
            osoba = get_person(item)
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
