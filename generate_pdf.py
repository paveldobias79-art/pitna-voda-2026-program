#!/usr/bin/env python3
"""
Generátor PDF programu konference Pitná voda 2026
Spusť: python3 generate_pdf.py
Výstup: program-pitna-voda-2026-vDDMMYYYY.pdf  +  automatické odeslání e-mailem
"""

import os
import smtplib
from datetime import datetime
from email.message import EmailMessage
from dotenv import load_dotenv
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ── Fonty s českou diakritikou ──────────────────────────────────────────────
FONT_DIR = "/usr/share/fonts/truetype/dejavu"
pdfmetrics.registerFont(TTFont("DejaVu",        f"{FONT_DIR}/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DejaVu-Bold",   f"{FONT_DIR}/DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("DejaVu-Italic", f"{FONT_DIR}/DejaVuSans-Oblique.ttf"))
pdfmetrics.registerFont(TTFont("DejaVu-BoldItalic", f"{FONT_DIR}/DejaVuSans-BoldOblique.ttf"))
pdfmetrics.registerFontFamily(
    "DejaVu",
    normal="DejaVu", bold="DejaVu-Bold",
    italic="DejaVu-Italic", boldItalic="DejaVu-BoldItalic"
)

# ── Barvy (odpovídají HTML) ─────────────────────────────────────────────────
NAVY      = colors.HexColor("#1A3660")
NAVY_MID  = colors.HexColor("#2B4E8C")
CYAN_LT   = colors.HexColor("#D0EEF8")
BLUE_LT   = colors.HexColor("#E2EAF7")
GREEN     = colors.HexColor("#C3EAAE")
PEACH     = colors.HexColor("#FAE4D6")
PINK      = colors.HexColor("#F4D0EC")
WHITE     = colors.white
MUTED     = colors.HexColor("#5A6A85")
CYAN      = colors.HexColor("#0BAAD4")

# ── Styly odstavců ──────────────────────────────────────────────────────────
def make_styles():
    base = dict(fontName="DejaVu", leading=10)
    return {
        "title":         ParagraphStyle("title",         fontSize=8, **base, textColor=colors.HexColor("#192035"), spaceAfter=1),
        "keynote_title": ParagraphStyle("keynote_title", fontSize=8, fontName="DejaVu-Bold", leading=10, textColor=colors.HexColor("#192035"), spaceAfter=1),
        "authors": ParagraphStyle("authors", fontSize=6.5, **base, textColor=MUTED),
        "section": ParagraphStyle("section", fontSize=7,  fontName="DejaVu-Bold", leading=9,
                                  textColor=NAVY, spaceAfter=0),
        "day":     ParagraphStyle("day",     fontSize=9,  fontName="DejaVu-Bold", leading=10,
                                  textColor=WHITE, spaceAfter=0),
        "time":    ParagraphStyle("time",    fontSize=7,  fontName="DejaVu", leading=9,
                                  textColor=NAVY, alignment=1),
        "util":    ParagraphStyle("util",    fontSize=7.5, fontName="DejaVu-Italic", leading=9,
                                  textColor=MUTED),
        "disc":    ParagraphStyle("disc",    fontSize=7.5, fontName="DejaVu-Italic", leading=9,
                                  textColor=colors.HexColor("#246B15")),
        "kdisc":   ParagraphStyle("kdisc",   fontSize=7.5, fontName="DejaVu-Italic", leading=9,
                                  textColor=NAVY),
        "lunch":   ParagraphStyle("lunch",   fontSize=7.5, fontName="DejaVu-Bold", leading=9,
                                  textColor=colors.HexColor("#922870")),
        "lunch_note": ParagraphStyle("lunch_note", fontSize=6.5, fontName="DejaVu-Italic", leading=8,
                                  textColor=colors.HexColor("#8e3070"), spaceBefore=2),
        "evening": ParagraphStyle("evening", fontSize=7.5, fontName="DejaVu-Bold", leading=9,
                                  textColor=NAVY),
        "header":  ParagraphStyle("header",  fontSize=14, fontName="DejaVu-Bold", leading=16,
                                  textColor=NAVY, spaceAfter=2),
        "subheader": ParagraphStyle("subheader", fontSize=9, fontName="DejaVu", leading=11,
                                    textColor=MUTED, spaceAfter=1),
        "firmy_title": ParagraphStyle("firmy_title", fontSize=8, fontName="DejaVu", leading=10,
                                      textColor=colors.HexColor("#192035"), spaceAfter=1),
        "firmy_authors": ParagraphStyle("firmy_authors", fontSize=6.5, fontName="DejaVu", leading=9,
                                        textColor=MUTED),
        "keynote_label": ParagraphStyle("keynote_label", fontSize=7, fontName="DejaVu-Italic", leading=9,
                                        textColor=NAVY_MID, spaceAfter=2),
        "firmy_label":   ParagraphStyle("firmy_label",   fontSize=7, fontName="DejaVu-Italic", leading=9,
                                        textColor=colors.HexColor("#C96830"), spaceAfter=2),
    }

S = make_styles()

# ── Šířky sloupců (landscape A4 = 297mm, margins 12mm each side) ───────────
PAGE_W = 210*mm - 24*mm  # ~186mm usable (portrait A4)
TIME_COL   = 35*mm
CONT_COL   = PAGE_W - TIME_COL

def row_day(text):
    return [Paragraph(text, S["day"]), ""], "day"

def row_section(text):
    return [Paragraph(text, S["section"]), ""], "section"

def row_util(time, text):
    return [Paragraph(time, S["time"]), Paragraph(text, S["util"])], "util"

def row_lunch(time):
    para = Paragraph(
        "Oběd"
        "<br/><font size='6.5' color='#8e3070'>"
        "Restaurace Illusion · 1. patro hotelu Palcát"
        "</font>",
        S["lunch"]
    )
    return [Paragraph(time, S["time"]), para], "lunch"

def row_disc(time, text):
    return [Paragraph(time, S["time"]), Paragraph(text, S["disc"])], "bdisc"

def row_kdisc(time):
    return [Paragraph(time, S["time"]), Paragraph("Diskuse k přednášce", S["kdisc"])], "kdisc"

def row_pres(time, title, authors=""):
    content = Paragraph(title, S["title"])
    if authors:
        content = [Paragraph(title, S["title"]), Paragraph(authors, S["authors"])]
    else:
        content = [Paragraph(title, S["title"])]
    from reportlab.platypus import KeepTogether as KT
    cell_content = content[0] if len(content) == 1 else content
    if isinstance(cell_content, list):
        from reportlab.platypus import Flowable
        cell_content = Paragraph(title + "<br/><font size='6.5' color='#5A6A85'>" + authors + "</font>", S["title"])
    return [Paragraph(time, S["time"]), cell_content], "pres"

def row_keynote(time, title, authors=""):
    label = Paragraph("Vyzvaná přednáška", S["keynote_label"])
    content_para = Paragraph(
        title + ("<br/><font size='6.5' color='#5A6A85'>" + authors + "</font>" if authors else ""),
        S["keynote_title"]
    )
    return [Paragraph(time, S["time"]), [label, content_para]], "keynote"

def row_firmy(time, title, authors=""):
    label = Paragraph("Firemní prezentace", S["firmy_label"])
    content_para = Paragraph(
        title + ("<br/><font size='6.5' color='#5A6A85'>" + authors + "</font>" if authors else ""),
        S["firmy_title"]
    )
    return [Paragraph(time, S["time"]), [label, content_para]], "firmy"

def row_green(time, text, authors=""):
    t = text + ("<br/><font size='6.5' color='#5A6A85'>" + authors + "</font>" if authors else "")
    return [Paragraph(time, S["time"]), Paragraph(t, S["disc"])], "green"

def row_evening(time):
    para = Paragraph(
        "Společenský večer s rautem a hudbou"
        "<br/><font size='6.5' color='#8e3070'>"
        "Střelnice – spolkový dům, Žižkova 249, Tábor"
        "</font>",
        S["evening"]
    )
    return [Paragraph(time, S["time"]), para], "util"

# ── Program dat ─────────────────────────────────────────────────────────────
# Vrací seznam dnů: každý den je list of (data_row, row_type)
def build_program():
    days = []   # každý prvek = list řádků jednoho dne
    rows = []   # aktuální den

    # ═══ PONDĚLÍ ════
    rows = []
    rows.append(row_day("PONDĚLÍ  1. 6. 2026  —  Neformální zahájení konference"))
    rows.append(row_util("15:00", "Registrace účastníků"))
    rows.append(row_keynote("17:00–17:45",
        "Adaptace vodárenství na měnící se svět",
        "Ing. Vilém Žák (SOVAK ČR)"))
    rows.append(row_util("17:45–18:15", "Diskuse k tématu přednášky"))
    days.append(rows)

    # ═══ ÚTERÝ ════
    rows = []
    rows.append(row_day("ÚTERÝ  2. 6. 2026  —  1. den konference"))
    rows.append(row_util("7:30", "Registrace účastníků"))
    rows.append(row_util("9:00–9:30", "Slavnostní zahájení konference"))
    rows.append(row_keynote("9:30–10:20",
        "Koagulace při úpravě vod — 50 let výzkumu pro praxi",
        "doc. Ing. Petr Dolejš, CSc. (W&amp;ET Team, České Budějovice)"))
    rows.append(row_kdisc("10:20–10:30"))
    rows.append(row_section("Strategický rámec  |  Resilience  |  Legislativa"))
    rows.append(row_pres("10:30–10:45",
        "Mělo smysl dělat rizikové analýzy vodovodů?",
        "Ing. Petra Pašková, Ph.D., Mgr. Jiří Paul (VAK Beroun, a.s.)"))
    rows.append(row_pres("10:45–11:00",
        "Největší ekologické ohrožení zdroje pitné vody v historii Znojemska",
        "Ing. Antonín Stuhl, Ing. Lenka Hahn, Ing. Tomáš Juhaňák (VAS, a.s.)"))
    rows.append(row_pres("11:00–11:15",
        "Preventivní posílení vodárenské infrastruktury — diagnostika odstavených zdrojů, ÚV Machnín",
        "Ing. David Janák, Ing. Lukáš Pařízek, MBA, Jaroslav Cebula DiS. (Severočeská servisní a.s. / SČVK, a.s.)"))
    rows.append(row_pres("11:15–11:30",
        "Význam ÚV Podolí ve výhledu do roku 2050 pro Prahu a metropolitní oblast",
        "Ing. Jindřich Šesták (PVS, a.s.)"))
    rows.append(row_pres("11:30–11:45",
        "Vodovod Soběnov — 20 let provozu s dezinfekcí vody pouze UV zářením",
        "Ing. Jiří Stara, Ing. Lenka Slancová, doc. Ing. Petr Dolejš, CSc. (ČEVAK a.s. / W&amp;ET Team, České Budějovice)"))
    rows.append(row_disc("11:45–12:00", "Diskuse k bloku"))
    rows.append(row_lunch("12:00–13:30"))
    rows.append(row_section("Aktivní uhlí v technologii úpravy vody"))
    rows.append(row_pres("13:30–13:45",
        "Aktivní uhlí a metody hodnocení jeho vlastností při úpravě pitné vody",
        "Ing. Mgr. Martina Švábová, Ph.D., doc. Ing. Marek Šváb, Ph.D., Prof. Ing. Václav Janda, CSc. (AV ČR / Dekonta / VŠCHT Praha)"))
    rows.append(row_pres("13:45–14:00",
        "Výsledky poloprovozních testů odstraňování mikropolutantů na reaktivovaném aktivním uhlí v podmínkách umělé infiltrace vodárny Káraný",
        "doc. Ing. Marek Šváb, Ph.D., Ing. Mgr. Martina Švábová, Ph.D., Prof. Ing. Václav Janda, CSc., Mgr. Marek Skalický (Dekonta / AV ČR / VŠCHT Praha)"))
    rows.append(row_pres("14:00–14:15",
        "Vliv dávkování práškového aktivního uhlí na účinnost odkyselovací filtrace",
        "Ing. Viktor Novotný (CHEVAK Cheb, a.s.)"))
    rows.append(row_pres("14:15–14:30",
        "Reaktivace granulovaného aktivního uhlí – změna paradigmatu v českém vodárenství?",
        "Ing. Adam Fendrych, Ing. Lukáš Havránek (VAK Pardubice, a.s.)"))
    rows.append(row_pres("14:30–14:45",
        "Poloprovozní testování granulovaného aktivního uhlí pro úpravnu vody Plzeň",
        "Ing. Lukáš Kačírek, Ing. Martina Klimtová, Ph.D., Ing. Pavel Dobiáš, Ph.D., doc. Ing. Petr Dolejš, CSc. (VODÁRNA PLZEŇ a.s. / W&amp;ET Team, České Budějovice)"))
    rows.append(row_disc("14:45–15:00", "Diskuse k bloku"))
    rows.append(row_firmy("15:00–15:10",
        "Technologie pro budoucnost pitné vody",
        "Ing. Ladislav Žilík — Endress+Hauser Czech"))
    rows.append(row_section("Technologie úpravy vody — nové poznatky a postupy"))
    rows.append(row_pres("15:10–15:25",
        "Hydrodynamika v průtočném modelovém flokulačním kanále s mechanickým mícháním",
        "doc. Ing. Radek Šulc, Ph.D., prof. Ing. Tomáš Jirout, Ph.D., Ing. Jiří Moravec, Ph.D., Ing. Filip Randák (ČVUT Praha)"))
    rows.append(row_pres("15:25–15:40",
        "Vliv míchání flokulačního kanálu na filtrační cyklus",
        "Ing. Eva Riederová, Ing. Linda Krunert, Ing. Petr Pěkný, Ing. Matěj Vrzáček (Želivská provozní, a.s.)"))
    rows.append(row_pres("15:40–15:55",
        "Využití umělé inteligence pro predikci výsledků koagulačního experimentu",
        "Ing. Michal Kuchař, Ing. Cyril Oswald, Ph.D., prof. Ing. Tomáš Vyhlídal, Ph.D. (ČVUT Praha)"))
    rows.append(row_pres("15:55–16:10",
        "Provozní zkušenosti včetně nových postupů na ÚV Mariánské Lázně",
        "Jiří Růžička, DiS. (CHEVAK Cheb, a.s.)"))
    rows.append(row_pres("16:10–16:25",
        "Postačuje prostá filtrace vody přes vápenec nebo dolomit ke spolehlivému navýšení koncentrací rozpuštěného vápníku a hořčíku v pitné vodě?",
        "prof. Ing. Václav Janda, CSc., doc. Ing. Marek Šváb, CSc., prof. Ing. Ondřej Šráček, M.Sc., Ph.D. (VŠCHT Praha / Dekonta / PF Univerzita Palackého v Olomouci)"))
    rows.append(row_pres("16:25–16:40",
        "Keramické membrány v úpravě pitné vody: zkušenosti ze zprovozňování a provozu ÚV Studená, Kašparov a Kelčice",
        "Ing. Kryštof Hnojna, Milan Drda (ENVI-PUR, s.r.o.)"))
    rows.append(row_disc("16:40–16:55", "Diskuse k bloku"))
    rows.append(row_firmy("16:55–17:05",
        "Monitorovacie systémy ECM s využitím sond Badger Meter pre úpravne pitnej vody",
        "ECM ECO Monitoring"))
    rows.append(row_section("Společenský večer"))
    rows.append(row_evening("19:30–24:00"))
    days.append(rows)

    # ═══ STŘEDA ════
    rows = []
    rows.append(row_day("STŘEDA  3. 6. 2026  —  2. den konference"))
    rows.append(row_keynote("8:30–9:10",
        "Hydrochemie úpravy vody: tradiční principy a nové výzvy",
        "doc. RNDr. Martin Pivokonský, Ph.D. (Hydrologický ústav AV ČR / Floc4U)"))
    rows.append(row_kdisc("9:10–9:20"))
    rows.append(row_section("Membránové technologie a nové postupy řízení procesů"))
    rows.append(row_pres("9:20–9:35",
        "Přímá nanofiltrace (dNF) a její technologický potenciál",
        "Ing. Tomáš Němec (ENVI-PUR, s.r.o.)"))
    rows.append(row_pres("9:35–9:50",
        "Posouzení účinnosti nanofiltrace při odstraňování organických látek a prekurzorů THM",
        "Ing. Robert Kvaček, prof. Ing. Václav Janda, CSc., Ing. Zuzana Sýkorová, Ph.D. (VŠCHT Praha / PVK, a.s.)"))
    rows.append(row_pres("9:50–10:05",
        "Koagulační testy pro návrh podmínek in-line koagulace na keramické membráně",
        "Ing. Martina Martinková, Bc. Eliška Kubová, Ing. Jindřich Procházka, Ph.D., doc. Ing. Petr Porcal, Ph.D., Ing. Lucie Pokorná, Ph.D. (VŠCHT Praha / Hydrobiologický ústav, Biologické centrum AV ČR)"))
    rows.append(row_pres("10:05–10:20",
        "Využití dat a algoritmů pro inteligentní řízení procesů úpravy vody",
        "Ing. Jindřich Procházka, Ph.D. (AquIQ / VŠCHT Praha)"))
    rows.append(row_pres("10:20–10:35",
        "Mechanismy zanášení membrán při opětovném využití vody",
        "Ing. Jan Vespalec, Mgr. Martina Repková, Ph.D., Ing. Silvestr Figalla, Ph.D., Ing. Jaroslav Lev, Ph.D., doc. Ing. Pavel Krystyník, Ph.D. (VUT FCH v Brně / ASIO TECH / UJEP Ústí n. L.)"))
    rows.append(row_pres("10:35–10:50",
        "Recyklace pracích vod na ÚV U Svaté Trojice – pilotní jednotka s SiC membránou",
        "Ing. Ladislava Hatáková, Ing. Martin Bouša (VHS Vrchlice–Maleč, a.s. / Water Carbon s.r.o.)"))
    rows.append(row_disc("10:50–11:05", "Diskuse k bloku"))
    rows.append(row_lunch("11:00–12:30"))
    rows.append(row_section("Hygiena a krizové řízení"))
    rows.append(row_green("12:30–12:45",
        "Když se natírá vodojem a je z toho vzbouření na vsi – pohled hygieniků na kontaminaci pitné vody v Holubicích",
        "Mgr. Hana Štollová, Mgr. Eva Kremeníková, Lenka Pokorná DiS., MUDr. František Kožíšek, CSc., Ing. Lenka Mayerová, Ph.D. (KHS Středočeský kraj / SZÚ Praha)"))
    rows.append(row_green("12:45–12:50",
        "Kontaminace vodovodu Holubice–Holubí Háj pohledem provozovatele",
        "Ing. Tomáš Hloušek, Ph.D. (Středočeské vodárny, a.s.)"))
    rows.append(row_green("12:50–13:30", "Ad-hoc diskuse"))
    rows.append(row_section("Mikrobiologie"))
    rows.append(row_pres("13:30–13:45",
        "Stanovení legionel … aneb každé vyšetření musí mít svůj účel",
        "RNDr. Dana Baudišová, Ph.D., MUDr. František Kožíšek, CSc. (SZÚ Praha)"))
    rows.append(row_pres("13:45–14:00",
        "Zkušenosti s monitoringem nukleových kyselin patogenních virů v povrchových vodách a v procesech úpravy vod",
        "Ing. Anna Košinová, Bc. Margita Řezáčová, Ing. Robert Kvaček, doc. RNDr. Jana Říhová Ambrožová, Ph.D., Dr. Ing. Pavla Šmejkalová, prof. Ing. Václav Janda, CSc., Ing. Kamila Zdeňková, Ph.D., Ing. Vojtěch Kouba, Ph.D. (VŠCHT Praha / PVK, a.s.)"))
    rows.append(row_pres("14:00–14:15",
        "Antimikrobiální rezistence na úpravnách vody a distribučních sítích pitné vody",
        "Ing. Vojtěch Kouba, Ph.D., Ing. Marco Antonio Lopez Marin, Ph.D., Ing. Abhijeet Udnoor, Ing. Robert Kvaček, James Manu MSc., Ing. Lucie Baumruková, Bc. Kateřina Hlaváčková, Ing. Stanislav Gajdoš, Ing. Zuzana Sýkorová, Ph.D., Dr. Ing. Pavla Šmejkalová, prof. Ing. Václav Janda, CSc., doc. RNDr. Jana Říhová Ambrožová, Ph.D. (VŠCHT Praha)"))
    rows.append(row_disc("14:15–14:30", "Diskuse k bloku"))
    rows.append(row_section("Mikropolutanty"))
    rows.append(row_pres("14:30–14:45",
        "Průmyslová aditiva – mikrokontaminanty povrchových vod",
        "RNDr. Marek Liška, Ph.D. (Povodí Vltavy s.p.)"))
    rows.append(row_pres("14:45–15:00",
        "Odkud se mohou dostávat PFAS do povrchových vod? Zkušenosti s pasivním vzorkováním od potenciálních zdrojů jejich vnosu po úpravny vod",
        "Kristina Mraz MSc, Bc. Antonín Hálek, Bc. Johana Kotková, Ing. Veronika Svobodová, Ph.D., Ing. Martin Srb, Ph.D., prof. Ing. Václav Janda, CSc., prof. Ing. Jana Pulkrabová, Ph.D., doc. Ing. Darina Dvořáková, Ph.D., Ing. Vojtěch Kouba, Ph.D. (VŠCHT Praha / PVK, a.s.)"))
    rows.append(row_pres("15:00–15:15",
        "Povinné stanovení PFAS v pitné vodě: První zkušenosti a data z praxe",
        "Ing. Jana Kováčová, Ph.D. (ALS Czech Republic, s.r.o.)"))
    rows.append(row_pres("15:15–15:30",
        "Zkušenosti SZÚ z místního šetření vodních zdrojů kontaminovaných PFAS",
        "MUDr. František Kožíšek, CSc., Ing. Lenka Mayerová, Ph.D., MUDr. Hana Jeligová, Ing. Filip Kotal, Ph.D., Ing. Markéta Havlová, Ph.D. (SZÚ Praha)"))
    rows.append(row_pres("15:30–15:45",
        "Inovativní postupy pro omezení kontaminace povrchových vod a zdrojů pitné vody pesticidy v zemědělské krajině",
        "Ing. Zuzana Bílková, Ph.D., Ing. Alice Vagenknechtová, Ph.D., Mgr. Daniela Tomešová, Ing. Jana Konečná, Ph.D., Mgr. Petr Karásek (ALS Czech Republic, s.r.o. / VÚMOP, v.v.i.)"))
    rows.append(row_pres("15:45–16:00",
        "Veřejné vodovody – příklady opatření ke snížení zdravotního rizika z uranu",
        "Ing. Jiří Stara, Ing. Jakub Škarda, Ing. Renáta Havlová, Ing. Kateřina Tebichová (ČEVAK, a.s.)"))
    rows.append(row_disc("16:00–16:15", "Diskuse k bloku"))
    rows.append(row_section("Diskusní blok — Mikropolutanty: legislativa, výskyt, eliminace"))
    rows.append(row_green("16:15–17:00",
        "Mikropolutanty — legislativa, výskyt, eliminace",
        "Mezioborový panel · Moderuje: Ing. Taťána Halešová · Waters"))
    rows.append(row_section("Společné jednání odborných skupin Komise pro úpravny vody (SOVAK) a Vodárenství (CzWA)"))
    rows.append(row_green("17:00–18:30",
        "Kdo po nás? — Diskusní panel SOVAK &amp; CzWA",
        "Společné jednání Komise pro úpravny vody (SOVAK ČR) a OS Vodárenství (CzWA)"))
    days.append(rows)

    # ═══ ČTVRTEK ════
    rows = []
    rows.append(row_day("ČTVRTEK  4. 6. 2026  —  3. (závěrečný) den konference"))
    rows.append(row_keynote("8:30–9:10",
        "Voda propojuje",
        "RNDr. Jindřich Duras, Ph.D. (Povodí Vltavy, s.p.)"))
    rows.append(row_kdisc("9:10–9:20"))
    rows.append(row_section("Zdroje pitné vody  |  Monitoring  |  Zásobování"))
    rows.append(row_pres("9:20–9:35",
        "Dlouhodobý monitoring vodárenského zdroje – řeky Úhlavy",
        "Ing. Martina Klimtová, Ph.D., Mgr. Milan Koželuh, Ing. Václav Tajč (VODÁRNA PLZEŇ a.s. / Povodí Vltavy, s.p.)"))
    rows.append(row_pres("9:35–9:50",
        "Monitoring kontaminace vody v povodí vodní nádrže Boskovice – zvýšené koncentrace mikropolutantů",
        "Mgr. Roman Horníček, Mgr. Lenka Váňová, RNDr. Zdenka Boháčková (VAS, a.s.)"))
    rows.append(row_pres("9:50–10:05",
        "Videobanka všech vodárenských nádrží v ČR — letecký pohled na vodárenství",
        "doc. Ing. Petr Dolejš, CSc. (W&amp;ET Team, České Budějovice)"))
    rows.append(row_disc("10:05–10:20", "Diskuse k bloku"))
    rows.append(row_section("Infrastruktura  |  Monitoring  |  Energetika  |  Digitalizace"))
    rows.append(row_pres("10:20–10:35",
        "Zkušenosti z přípravy a realizace oprav vodojemů (VDJ)",
        "Ing. Filip Harciník (Severočeské vodovody a kanalizace, a.s.)"))
    rows.append(row_pres("10:35–10:50",
        "Vývoj koncepce zásobování města Jihlavy pitnou vodou a role výstavby vodojemu Bukovno",
        "Ing. Marek Coufal, Ph.D., Ing. Rostislav Kasal, Ph.D. (Vodohospodářský rozvoj a výstavba, a.s.)"))
    rows.append(row_pres("10:50–11:05",
        "Vodní mikroturbíny pro vodárenství",
        "Dr. Ing. Petr Nowak, Ing. Eva Bílková Ph.D., Ing. Jiří Souček Ph.D. (ČVUT Praha)"))
    rows.append(row_disc("11:05–11:10", "Diskuse k bloku"))
    rows.append(row_firmy("11:10–11:20",
        "Nová generace sond volného chloru Pyxis ST",
        "Ing. Tomáš Chvátal — Katko s.r.o."))
    rows.append(row_firmy("11:20–11:30",
        "Elektrická infrastruktura ve vodárenství — audity a modernizační potenciál",
        "Ing. Adam Dolejší — Schneider Electric CZ, s.r.o."))
    rows.append(row_firmy("11:30–11:40",
        "Současné trendy v lokální filtraci pitné vody",
        "Ing. Dana Feferlová — Filbec"))
    rows.append(row_section("Závěr konference"))
    rows.append(row_green("11:40–12:00", "Závěrečná diskuse — shrnutí konference"))
    days.append(rows)

    return days

# ── Barvy dle typu řádku ────────────────────────────────────────────────────
ROW_BG = {
    "day":     NAVY,
    "section": BLUE_LT,
    "keynote": CYAN_LT,
    "pres":    WHITE,
    "firmy":   PEACH,
    "green":   GREEN,
    "bdisc":   GREEN,
    "kdisc":   WHITE,
    "util":    WHITE,
    "lunch":   PINK,
}

# ── Zápatí stránky ──────────────────────────────────────────────────────────
def draw_footer(canvas, doc):
    """Přidá copyright do zápatí každé stránky."""
    canvas.saveState()
    canvas.setFont("DejaVu", 7)
    canvas.setFillColor(colors.HexColor("#AAAAAA"))
    canvas.drawCentredString(
        doc.pagesize[0] / 2,
        7*mm,
        "© Pavel & Claude 2026"
    )
    canvas.restoreState()

# ── Sestavení PDF ───────────────────────────────────────────────────────────
def build_pdf(output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=12*mm, rightMargin=12*mm,
        topMargin=14*mm, bottomMargin=14*mm,
    )

    # Záhlaví stránky
    header_block = [
        Paragraph("Program konference  Pitná voda 2026", S["header"]),
        Paragraph(
            "1.–4. června 2026  ·  Hotel Palcát, Tábor  ·  "
            "Garanti: doc. Ing. Petr Dolejš, CSc.  |  Ing. Pavel Dobiáš, Ph.D.",
            S["subheader"]),
        Spacer(1, 4*mm),
    ]

    days = build_program()

    def build_day_table(rows):
        """Sestaví tabulku pro jeden den."""
        table_data = []
        style_cmds = [
            ("FONT",         (0,0), (-1,-1), "DejaVu",    7),
            ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
            ("TOPPADDING",   (0,0), (-1,-1), 3),
            ("BOTTOMPADDING",(0,0), (-1,-1), 3),
            ("LEFTPADDING",  (0,0), (-1,-1), 4),
            ("RIGHTPADDING", (0,0), (-1,-1), 4),
            ("LINEBELOW",    (0,0), (-1,-1), 0.3, colors.HexColor("#D8E2EF")),
        ]
        for i, (row_data, rtype) in enumerate(rows):
            table_data.append(row_data)
            bg = ROW_BG.get(rtype, WHITE)
            style_cmds.append(("BACKGROUND", (0,i), (-1,i), bg))
            if rtype in ("day", "section"):
                style_cmds.append(("SPAN", (0,i), (1,i)))
                if rtype == "day":
                    style_cmds.append(("FONT",          (0,i), (-1,i), "DejaVu-Bold", 8.5))
                    style_cmds.append(("TOPPADDING",    (0,i), (-1,i), 6))
                    style_cmds.append(("BOTTOMPADDING", (0,i), (-1,i), 6))
                else:
                    style_cmds.append(("FONT", (0,i), (-1,i), "DejaVu-Bold", 7))
        tbl = Table(
            table_data,
            colWidths=[TIME_COL, CONT_COL],
            splitByRow=1,
            repeatRows=0,
        )
        tbl.setStyle(TableStyle(style_cmds))
        return tbl

    story = header_block[:]
    for di, day_rows in enumerate(days):
        if di > 0:
            story.append(Spacer(1, 8*mm))   # mezera mezi dny
        story.append(build_day_table(day_rows))

    doc.build(story, onFirstPage=draw_footer, onLaterPages=draw_footer)
    print(f"PDF vygenerován: {output_path}")

def send_pdf_email(pdf_path: str) -> None:
    """Odešle PDF e-mailem. Přihlašovací údaje čte z .env souboru."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    load_dotenv(os.path.join(script_dir, ".env"))

    gmail_user   = os.getenv("GMAIL_USER", "").strip()
    app_password = os.getenv("GMAIL_APP_PASSWORD", "").strip()
    recipient    = os.getenv("RECIPIENT_EMAIL", "").strip()

    if not app_password:
        print("⚠️  E-mail nebyl odeslán — v souboru .env chybí GMAIL_APP_PASSWORD.")
        print("   Vygeneruj App heslo na: https://myaccount.google.com/apppasswords")
        return

    date_label = datetime.now().strftime("%-d. %-m. %Y")
    filename   = os.path.basename(pdf_path)

    msg = EmailMessage()
    msg["Subject"] = f"Aktualizovaný program konference Pitná voda 2026 ({date_label})"
    msg["From"]    = gmail_user
    msg["To"]      = recipient
    msg.set_content(
        f"Dobrý den,\n\n"
        f"v příloze zasílám aktualizovaný program konference Pitná voda 2026 "
        f"(verze {date_label}).\n\n"
        f"S pozdravem\nPavel Dobiáš\nENVI-PUR, s.r.o."
    )

    with open(pdf_path, "rb") as f:
        msg.add_attachment(
            f.read(),
            maintype="application",
            subtype="pdf",
            filename=filename,
        )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(gmail_user, app_password)
        smtp.send_message(msg)

    print(f"✉️  PDF odesláno na {recipient}")


if __name__ == "__main__":
    import shutil
    script_dir = os.path.dirname(os.path.abspath(__file__))
    date_stamp = datetime.now().strftime("%d%m%Y")

    # Datovaná verze → archiv/
    archiv_dir = os.path.join(script_dir, "archiv")
    os.makedirs(archiv_dir, exist_ok=True)
    dated_output = os.path.join(archiv_dir, f"program-pitna-voda-2026-v{date_stamp}.pdf")
    build_pdf(dated_output)

    # Pevná verze → www/ (pro publikaci na webu, název se nemění)
    www_dir = os.path.join(script_dir, "www")
    os.makedirs(www_dir, exist_ok=True)
    latest_output = os.path.join(www_dir, "program-pitna-voda-2026.pdf")
    shutil.copy2(dated_output, latest_output)
    print(f"Publikační kopie: {latest_output}")

    # send_pdf_email(dated_output)  # funkce zrušena
