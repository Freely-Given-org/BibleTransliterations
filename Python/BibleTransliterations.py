#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# BibleTransliterations.py
#
# Module handling BibleTransliterations
#
# Copyright (C) 2022 Robert Hunt
# Author: Robert Hunt <Freely.Given.org+BOS@gmail.com>
# License: See gpl-3.0.txt
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Module handling BibleTransliterations.


"""
from gettext import gettext as _
from pathlib import Path
import logging
from csv import  DictReader
import unicodedata

import BibleOrgSysGlobals
from BibleOrgSysGlobals import fnPrint, vPrint, dPrint



LAST_MODIFIED_DATE = '2022-08-31' # by RJH
SHORT_PROGRAM_NAME = "BibleTransliterations"
PROGRAM_NAME = "Bible Transliterations handler"
PROGRAM_VERSION = '0.07'
programNameVersion = f'{SHORT_PROGRAM_NAME} v{PROGRAM_VERSION}'

debuggingThisModule = False



hebrew_tsv_rows = greek_tsv_rows = None
def load_transliteration_table(which) -> bool:
    """
    """
    global hebrew_tsv_rows, greek_tsv_rows
    project_folderpath = Path(__file__).parent.parent # Find tables relative to this module
    with open( project_folderpath.joinpath(f'sourceTables/{which}.tsv'), 'rt', encoding='utf-8' ) as tsv_table:
        tsv_lines = tsv_table.readlines()

    # Remove BOM
    if tsv_lines[0].startswith("\ufeff"):
        vPrint('Quiet', debuggingThisModule, f"  Removing Byte Order Marker (BOM) from start of {which} TSV file…")
        tsv_lines[0] = tsv_lines[0][1:]

    # Get the headers before we start
    original_column_headers = [ header for header in tsv_lines[0].strip().split('\t') ]
    dPrint('Verbose', debuggingThisModule, f"  Original transliteration column headers: ({len(original_column_headers)}): {original_column_headers}")

    # Read, check the number of columns, and summarise row contents all in one go
    dict_reader = DictReader(tsv_lines, delimiter='\t')
    tsv_rows = []
    # tsv_column_counts = defaultdict(lambda: defaultdict(int))
    source_list, source_set = [], set()
    source_language_code = 'hbo' if which=='Hebrew' else 'x-grc-koine'
    for n, row in enumerate(dict_reader):
        if len(row) != len(original_column_headers):
            logging.critical(f"Line {n} has {len(row)} column(s) instead of {len(original_column_headers)}: {row} from '{tsv_lines[n+1]}'")
        if row['en'] is None: row['en'] = ''
        tsv_rows.append(row)
        assert row[source_language_code]
        source_list.append(row[source_language_code])
        source_set.add(row[source_language_code])

    if len(source_set) < len(source_list):
        logging.critical(f"Have a duplicate entry in the {which} set!")
        for source in source_set:
            if source_list.count(source) > 1:
                logging.critical(f"  Have {source_list.count(source)} of '{source}'")
        halt

    # Must sort so the longest sequences go first
    if which=='Hebrew':
        destination = hebrew_tsv_rows = sorted(tsv_rows, key=lambda k:-len(k[source_language_code]))
    else: destination = greek_tsv_rows = sorted(tsv_rows, key=lambda k:-len(k[source_language_code]))
    vPrint('Quiet', debuggingThisModule, f"  Loaded {len(destination):,} '{which}' transliteration data rows.")
    return True
# end of load_transliteration_table()

def transliterate_Hebrew(input:str, toTitleFlag=False) -> str:
    """
    Hebrew doesn't have capital letters,
        so if the calling function knows it's a name or at the beginning of a sentence,
        we may need to capitalise it.

    TODO: This is only a temporary function that sort of works
        but it really needs to be completely rewritten.
        See https://en.wikipedia.org/wiki/Romanization_of_Hebrew.
    """
    fnPrint( debuggingThisModule, f"transliterate_Hebrew({input}, {toTitleFlag})")
    result = input

    # Transliterate Hebrew letters to English
    for tsv_row in hebrew_tsv_rows:
        # print( f"  {tsv_row=}")
        result = result.replace( tsv_row['hbo'], tsv_row['en'] )

    # Find the index of the first Hebrew character in the INPUT string (will be the same for the output string)
    for first_Hebrew_index,char in enumerate(input):
        if 'HEBREW' in unicodedata.name(char):
            break
    else:
        logging.warning( f"transliterate_Hebrew failed to find any Hebrew in '{input}'")
        return result

    # Correct dagesh in first letter giving double letters
    if result[first_Hebrew_index] == result[first_Hebrew_index+1]:
        result = f'{result[:first_Hebrew_index]}{result[first_Hebrew_index+1:]}' # Remove the first of the duplicate letters

    if not toTitleFlag:
        return result
    if result[first_Hebrew_index] == 'ʦ':
        return result.replace( 'ʦ', 'Ts', 1 ) # This digraph doesn't have an UPPERCASE form
    # print(f"Title-casing '{result}' '{result[first_Hebrew_index:first_Hebrew_index+2]}' to '{result[:first_Hebrew_index+2].title()}'")
    return f'{result[:first_Hebrew_index]}{result[first_Hebrew_index:first_Hebrew_index+2].title()}{result[first_Hebrew_index+2:]}' # Title case, but don't want something like Rəḩavə'Ām
# end of transliterate_Hebrew function

def transliterate_Greek(input:str) -> str:
    """
    """
    result = input
    for tsv_row in greek_tsv_rows:
        # print( f"  {tsv_row=}")
        result = result.replace( tsv_row['x-grc-koine'], tsv_row['en'] )
    return result
# end of transliterate_Greek function


Genesis_1 = '''Chapter 1
1 בְּרֵאשִׁ֖ית בָּרָ֣א אֱלֹהִ֑ים אֵ֥ת הַשָּׁמַ֖יִם וְאֵ֥ת הָאָֽרֶץ׃
2 וְהָאָ֗רֶץ הָיְתָ֥ה תֹ֨הוּ֙ וָבֹ֔הוּ וְחֹ֖שֶׁךְ עַל־פְּנֵ֣י תְה֑וֹם וְר֣וּחַ אֱלֹהִ֔ים מְרַחֶ֖פֶת עַל־פְּנֵ֥י הַמָּֽיִם׃
3 וַיֹּ֥אמֶר אֱלֹהִ֖ים יְהִ֣י א֑וֹר וַֽיְהִי־אֽוֹר׃
4 וַיַּ֧רְא אֱלֹהִ֛ים אֶת־הָא֖וֹר כִּי־ט֑וֹב וַיַּבְדֵּ֣ל אֱלֹהִ֔ים בֵּ֥ין הָא֖וֹר וּבֵ֥ין הַחֹֽשֶׁךְ׃
5 וַיִּקְרָ֨א אֱלֹהִ֤ים ׀ לָאוֹר֙ י֔וֹם וְלַחֹ֖שֶׁךְ קָ֣רָא לָ֑יְלָה וַֽיְהִי־עֶ֥רֶב וַֽיְהִי־בֹ֖קֶר י֥וֹם אֶחָֽד׃ פ
6 וַיֹּ֣אמֶר אֱלֹהִ֔ים יְהִ֥י רָקִ֖יעַ בְּת֣וֹךְ הַמָּ֑יִם וִיהִ֣י מַבְדִּ֔יל בֵּ֥ין מַ֖יִם לָמָֽיִם׃
7 וַיַּ֣עַשׂ אֱלֹהִים֮ אֶת־הָרָקִיעַ֒ וַיַּבְדֵּ֗ל בֵּ֤ין הַמַּ֨יִם֙ אֲשֶׁר֙ מִתַּ֣חַת לָרָקִ֔יעַ וּבֵ֣ין הַמַּ֔יִם אֲשֶׁ֖ר מֵעַ֣ל לָרָקִ֑יעַ וַֽיְהִי־כֵֽן׃
8 וַיִּקְרָ֧א אֱלֹהִ֛ים לָֽרָקִ֖יעַ שָׁמָ֑יִם וַֽיְהִי־עֶ֥רֶב וַֽיְהִי־בֹ֖קֶר י֥וֹם שֵׁנִֽי׃ פ
9 וַיֹּ֣אמֶר אֱלֹהִ֗ים יִקָּו֨וּ הַמַּ֜יִם מִתַּ֤חַת הַשָּׁמַ֨יִם֙ אֶל־מָק֣וֹם אֶחָ֔ד וְתֵרָאֶ֖ה הַיַּבָּשָׁ֑ה וַֽיְהִי־כֵֽן׃
10 וַיִּקְרָ֨א אֱלֹהִ֤ים ׀ לַיַּבָּשָׁה֙ אֶ֔רֶץ וּלְמִקְוֵ֥ה הַמַּ֖יִם קָרָ֣א יַמִּ֑ים וַיַּ֥רְא אֱלֹהִ֖ים כִּי־טֽוֹב׃
11 וַיֹּ֣אמֶר אֱלֹהִ֗ים תַּֽדְשֵׁ֤א הָאָ֨רֶץ֙ דֶּ֔שֶׁא עֵ֚שֶׂב מַזְרִ֣יעַ זֶ֔רַע עֵ֣ץ פְּרִ֞י עֹ֤שֶׂה פְּרִי֙ לְמִינ֔וֹ אֲשֶׁ֥ר זַרְעוֹ־ב֖וֹ עַל־הָאָ֑רֶץ וַֽיְהִי־כֵֽן׃
12 וַתּוֹצֵ֨א הָאָ֜רֶץ דֶּ֠שֶׁא עֵ֣שֶׂב מַזְרִ֤יעַ זֶ֨רַע֙ לְמִינֵ֔הוּ וְעֵ֧ץ עֹֽשֶׂה־פְּרִ֛י   אֲשֶׁ֥ר זַרְעוֹ־ב֖וֹ לְמִינֵ֑הוּ וַיַּ֥רְא אֱלֹהִ֖ים כִּי־טֽוֹב׃
13 וַֽיְהִי־עֶ֥רֶב וַֽיְהִי־בֹ֖קֶר י֥וֹם שְׁלִישִֽׁי׃ פ
14 וַיֹּ֣אמֶר אֱלֹהִ֗ים יְהִ֤י מְאֹרֹת֙ בִּרְקִ֣יעַ הַשָּׁמַ֔יִם לְהַבְדִּ֕יל בֵּ֥ין הַיּ֖וֹם וּבֵ֣ין הַלָּ֑יְלָה וְהָי֤וּ לְאֹתֹת֙ וּלְמ֣וֹעֲדִ֔ים וּלְיָמִ֖ים וְשָׁנִֽים׃
15 וְהָי֤וּ לִמְאוֹרֹת֙ בִּרְקִ֣יעַ הַשָּׁמַ֔יִם לְהָאִ֖יר עַל־הָאָ֑רֶץ וַֽיְהִי־כֵֽן׃
16 וַיַּ֣עַשׂ אֱלֹהִ֔ים אֶת־שְׁנֵ֥י הַמְּאֹרֹ֖ת הַגְּדֹלִ֑ים אֶת־הַמָּא֤וֹר הַגָּדֹל֙ לְמֶמְשֶׁ֣לֶת הַיּ֔וֹם וְאֶת־הַמָּא֤וֹר הַקָּטֹן֙ לְמֶמְשֶׁ֣לֶת הַלַּ֔יְלָה וְאֵ֖ת הַכּוֹכָבִֽים׃
17 וַיִּתֵּ֥ן אֹתָ֛ם אֱלֹהִ֖ים בִּרְקִ֣יעַ הַשָּׁמָ֑יִם לְהָאִ֖יר עַל־הָאָֽרֶץ׃
18 וְלִמְשֹׁל֙ בַּיּ֣וֹם וּבַלַּ֔יְלָה וּֽלֲהַבְדִּ֔יל בֵּ֥ין הָא֖וֹר וּבֵ֣ין הַחֹ֑שֶׁךְ וַיַּ֥רְא אֱלֹהִ֖ים כִּי־טֽוֹב׃
19 וַֽיְהִי־עֶ֥רֶב וַֽיְהִי־בֹ֖קֶר י֥וֹם רְבִיעִֽי׃ פ
20 וַיֹּ֣אמֶר אֱלֹהִ֔ים יִשְׁרְצ֣וּ הַמַּ֔יִם שֶׁ֖רֶץ נֶ֣פֶשׁ חַיָּ֑ה וְעוֹף֙ יְעוֹפֵ֣ף עַל־הָאָ֔רֶץ עַל־פְּנֵ֖י רְקִ֥יעַ הַשָּׁמָֽיִם׃
21 וַיִּבְרָ֣א אֱלֹהִ֔ים אֶת־הַתַּנִּינִ֖ם הַגְּדֹלִ֑ים וְאֵ֣ת כָּל־נֶ֣פֶשׁ הַֽחַיָּ֣ה ׀ הָֽרֹמֶ֡שֶׂת אֲשֶׁר֩ שָׁרְצ֨וּ הַמַּ֜יִם לְמִֽינֵהֶ֗ם וְאֵ֨ת כָּל־ע֤וֹף כָּנָף֙ לְמִינֵ֔הוּ וַיַּ֥רְא אֱלֹהִ֖ים כִּי־טֽוֹב׃
22 וַיְבָ֧רֶךְ אֹתָ֛ם אֱלֹהִ֖ים לֵאמֹ֑ר פְּר֣וּ וּרְב֗וּ וּמִלְא֤וּ אֶת־הַמַּ֨יִם֙ בַּיַּמִּ֔ים וְהָע֖וֹף יִ֥רֶב בָּאָֽרֶץ׃
23 וַֽיְהִי־עֶ֥רֶב וַֽיְהִי־בֹ֖קֶר י֥וֹם חֲמִישִֽׁי׃ פ
24 וַיֹּ֣אמֶר אֱלֹהִ֗ים תּוֹצֵ֨א הָאָ֜רֶץ נֶ֤פֶשׁ חַיָּה֙ לְמִינָ֔הּ בְּהֵמָ֥ה וָרֶ֛מֶשׂ וְחַֽיְתוֹ־אֶ֖רֶץ לְמִינָ֑הּ וַֽיְהִי־כֵֽן׃
25 וַיַּ֣עַשׂ אֱלֹהִים֩ אֶת־חַיַּ֨ת הָאָ֜רֶץ לְמִינָ֗הּ וְאֶת־הַבְּהֵמָה֙ לְמִינָ֔הּ וְאֵ֛ת כָּל־רֶ֥מֶשׂ הָֽאֲדָמָ֖ה לְמִינֵ֑הוּ וַיַּ֥רְא אֱלֹהִ֖ים כִּי־טֽוֹב׃
26 וַיֹּ֣אמֶר אֱלֹהִ֔ים נַֽעֲשֶׂ֥ה אָדָ֛ם בְּצַלְמֵ֖נוּ כִּדְמוּתֵ֑נוּ וְיִרְדּוּ֩ בִדְגַ֨ת הַיָּ֜ם וּבְע֣וֹף הַשָּׁמַ֗יִם וּבַבְּהֵמָה֙ וּבְכָל־הָאָ֔רֶץ וּבְכָל־הָרֶ֖מֶשׂ הָֽרֹמֵ֥שׂ עַל־הָאָֽרֶץ׃
27 וַיִּבְרָ֨א אֱלֹהִ֤ים ׀ אֶת־הָֽאָדָם֙ בְּצַלְמ֔וֹ בְּצֶ֥לֶם אֱלֹהִ֖ים בָּרָ֣א אֹת֑וֹ זָכָ֥ר וּנְקֵבָ֖ה בָּרָ֥א אֹתָֽם׃
28 וַיְבָ֣רֶךְ אֹתָם֮ אֱלֹהִים֒ וַיֹּ֨אמֶר לָהֶ֜ם אֱלֹהִ֗ים פְּר֥וּ וּרְב֛וּ וּמִלְא֥וּ אֶת־הָאָ֖רֶץ וְכִבְשֻׁ֑הָ וּרְד֞וּ בִּדְגַ֤ת הַיָּם֙ וּבְע֣וֹף הַשָּׁמַ֔יִם וּבְכָל־חַיָּ֖ה הָֽרֹמֶ֥שֶׂת עַל־הָאָֽרֶץ׃
29 וַיֹּ֣אמֶר אֱלֹהִ֗ים הִנֵּה֩ נָתַ֨תִּי לָכֶ֜ם אֶת־כָּל־עֵ֣שֶׂב ׀ זֹרֵ֣עַ זֶ֗רַע אֲשֶׁר֙ עַל־פְּנֵ֣י כָל־הָאָ֔רֶץ וְאֶת־כָּל־הָעֵ֛ץ אֲשֶׁר־בּ֥וֹ פְרִי־עֵ֖ץ זֹרֵ֣עַ זָ֑רַע לָכֶ֥ם יִֽהְיֶ֖ה לְאָכְלָֽה׃
30 וּֽלְכָל־חַיַּ֣ת הָ֠אָרֶץ וּלְכָל־ע֨וֹף הַשָּׁמַ֜יִם וּלְכֹ֣ל ׀ רוֹמֵ֣שׂ עַל־הָאָ֗רֶץ אֲשֶׁר־בּוֹ֙ נֶ֣פֶשׁ חַיָּ֔ה אֶת־כָּל־יֶ֥רֶק עֵ֖שֶׂב לְאָכְלָ֑ה וַֽיְהִי־כֵֽן׃
31 וַיַּ֤רְא אֱלֹהִים֙ אֶת־כָּל־אֲשֶׁ֣ר עָשָׂ֔ה וְהִנֵּה־ט֖וֹב מְאֹ֑ד וַֽיְהִי־עֶ֥רֶב וַֽיְהִי־בֹ֖קֶר י֥וֹם הַשִּׁשִּֽׁי׃ פ
'''

Matthew_1 = '''\\v 1 ¶Βίβλος γενέσεως Ἰησοῦ Χριστοῦ, υἱοῦ Δαυὶδ, υἱοῦ Ἀβραάμ:
\\v 2 ¶Ἀβραὰμ ἐγέννησεν τὸν Ἰσαάκ, Ἰσαὰκ δὲ ἐγέννησεν τὸν Ἰακώβ, Ἰακὼβ δὲ ἐγέννησεν τὸν Ἰούδαν καὶ τοὺς ἀδελφοὺς αὐτοῦ,
\\v 3 Ἰούδας δὲ ἐγέννησεν τὸν Φαρὲς καὶ τὸν Ζάρα ἐκ τῆς Θαμάρ, Φαρὲς δὲ ἐγέννησεν τὸν Ἑσρώμ, Ἑσρὼμ δὲ ἐγέννησεν τὸν Ἀράμ,
\\v 4 Ἀρὰμ δὲ ἐγέννησεν τὸν Ἀμιναδάβ, Ἀμιναδὰβ δὲ ἐγέννησεν τὸν Ναασσών, Ναασσὼν δὲ ἐγέννησεν τὸν Σαλμών,
\\v 5 Σαλμὼν δὲ ἐγέννησεν τὸν Βόες ἐκ τῆς Ῥαχάβ, Βόες δὲ ἐγέννησεν τὸν Ἰωβὴδ ἐκ τῆς Ῥούθ, Ἰωβὴδ δὲ ἐγέννησεν τὸν Ἰεσσαί,
\\v 6 Ἰεσσαὶ δὲ ἐγέννησεν τὸν Δαυὶδ τὸν βασιλέα. ¶Δαυὶδ δὲ ἐγέννησεν τὸν Σολομῶνα ἐκ τῆς τοῦ Οὐρίου,
\\v 7 Σολομὼν δὲ ἐγέννησεν τὸν Ῥοβοάμ, Ῥοβοὰμ δὲ ἐγέννησεν τὸν Ἀβιά, Ἀβιὰ δὲ ἐγέννησεν τὸν Ἀσάφ,
\\v 8 Ἀσὰφ δὲ ἐγέννησεν τὸν Ἰωσαφάτ, Ἰωσαφὰτ δὲ ἐγέννησεν τὸν Ἰωράμ, Ἰωρὰμ δὲ ἐγέννησεν τὸν Ὀζίαν,
\\v 9 Ὀζίας δὲ ἐγέννησεν τὸν Ἰωαθάμ, Ἰωαθὰμ δὲ ἐγέννησεν τὸν Ἀχάζ, Ἀχὰζ δὲ ἐγέννησεν τὸν Ἑζεκίαν,
\\v 10 Ἑζεκίας δὲ ἐγέννησεν τὸν Μανασσῆ, Μανασσῆ δὲ ἐγέννησεν τὸν Ἀμώς, Ἀμὼς δὲ ἐγέννησεν τὸν Ἰωσίαν,
\\v 11 Ἰωσίας δὲ ἐγέννησεν τὸν Ἰεχονίαν καὶ τοὺς ἀδελφοὺς αὐτοῦ ἐπὶ τῆς μετοικεσίας Βαβυλῶνος.
\\v 12 ¶Μετὰ δὲ τὴν μετοικεσίαν Βαβυλῶνος, Ἰεχονίας ἐγέννησεν τὸν Σαλαθιήλ, Σαλαθιὴλ δὲ ἐγέννησεν τὸν Ζοροβαβέλ,
\\v 13 Ζοροβαβὲλ δὲ ἐγέννησεν τὸν Ἀβιούδ, Ἀβιοὺδ δὲ ἐγέννησεν τὸν Ἐλιακείμ, Ἐλιακεὶμ δὲ ἐγέννησεν τὸν Ἀζώρ,
\\v 14 Ἀζὼρ δὲ ἐγέννησεν τὸν Σαδώκ, Σαδὼκ δὲ ἐγέννησεν τὸν Ἀχείμ, Ἀχεὶμ δὲ ἐγέννησεν τὸν Ἐλιούδ,
\\v 15 Ἐλιοὺδ δὲ ἐγέννησεν τὸν Ἐλεάζαρ, Ἐλεάζαρ δὲ ἐγέννησεν τὸν Ματθάν, Ματθὰν δὲ ἐγέννησεν τὸν Ἰακώβ,
\\v 16 Ἰακὼβ δὲ ἐγέννησεν τὸν Ἰωσὴφ τὸν ἄνδρα Μαρίας, ἐξ ἧς ἐγεννήθη Ἰησοῦς, ὁ λεγόμενος Χριστός.
\\v 17 ¶Πᾶσαι οὖν αἱ γενεαὶ ἀπὸ Ἀβραὰμ ἕως Δαυὶδ γενεαὶ δεκατέσσαρες, καὶ ἀπὸ Δαυὶδ ἕως τῆς μετοικεσίας Βαβυλῶνος γενεαὶ δεκατέσσαρες, καὶ ἀπὸ τῆς μετοικεσίας Βαβυλῶνος ἕως τοῦ Χριστοῦ γενεαὶ δεκατέσσαρες.
\\v 18 ¶Τοῦ δὲ Ἰησοῦ Χριστοῦ ἡ γένεσις οὕτως ἦν: μνηστευθείσης τῆς μητρὸς αὐτοῦ Μαρίας τῷ Ἰωσήφ, πρὶν ἢ συνελθεῖν αὐτοὺς, εὑρέθη ἐν γαστρὶ ἔχουσα ἐκ Πνεύματος Ἁγίου.
\\v 19 Ἰωσὴφ δὲ ὁ ἀνὴρ αὐτῆς, δίκαιος ὢν καὶ μὴ θέλων αὐτὴν δειγματίσαι, ἐβουλήθη λάθρᾳ ἀπολῦσαι αὐτήν.
\\v 20 Ταῦτα δὲ αὐτοῦ ἐνθυμηθέντος, ἰδοὺ, ἄγγελος Κυρίου κατʼ ὄναρ ἐφάνη αὐτῷ λέγων, “Ἰωσὴφ, υἱὸς Δαυίδ, μὴ φοβηθῇς παραλαβεῖν Μαριὰμ τὴν γυναῖκά σου, τὸ γὰρ ἐν αὐτῇ γεννηθὲν ἐκ Πνεύματός ἐστιν Ἁγίου.
\\v 21 Τέξεται δὲ υἱὸν, καὶ καλέσεις τὸ ὄνομα αὐτοῦ Ἰησοῦν, αὐτὸς γὰρ σώσει τὸν λαὸν αὐτοῦ ἀπὸ τῶν ἁμαρτιῶν αὐτῶν.”
\\v 22 Τοῦτο δὲ ὅλον γέγονεν, ἵνα πληρωθῇ τὸ ῥηθὲν ὑπὸ Κυρίου διὰ τοῦ προφήτου λέγοντος,
\\v 23 “Ἰδοὺ, ἡ παρθένος ἐν γαστρὶ ἕξει καὶ τέξεται υἱόν, καὶ καλέσουσιν τὸ ὄνομα αὐτοῦ Ἐμμανουήλ”, ὅ ἐστιν μεθερμηνευόμενον, “Μεθʼ ἡμῶν ὁ Θεός”.
\\v 24 Ἐγερθεὶς δὲ ὁ Ἰωσὴφ ἀπὸ τοῦ ὕπνου, ἐποίησεν ὡς προσέταξεν αὐτῷ ὁ ἄγγελος Κυρίου, καὶ παρέλαβεν τὴν γυναῖκα αὐτοῦ,
\\v 25 καὶ οὐκ ἐγίνωσκεν αὐτὴν ἕως οὗ ἔτεκεν υἱόν· καὶ ἐκάλεσεν τὸ ὄνομα αὐτοῦ, Ἰησοῦν.
'''

def check_line(line:str):
    """
    """
    # import unicodedata
    for c,char in enumerate(line, start=1):
        if char in ' ʼ,.?!:;-–/\\1234567890“”‘’()¶…©':
            continue
        char_name = unicodedata.name(char)
        if 'GREEK' in char_name or 'HEBREW' in char_name:
            return c, char, char_name
    return True
# end of BibleTransliterations.check_line

def check_text(text:str):
    """
    """
    for l,line in enumerate(text.split('\n'), start=1):
        vPrint( 'Info', debuggingThisModule, line )
        result = check_line( line )
        if result is not True:
            c, char, char_name = result
            logging.critical( f"Found line {l:,} char {c:,}: '{char}' {char_name}\n  in '{line}'" )
            return False
    return True
# end of BibleTransliterations.check_text


def briefDemo() -> None:
    """
    Main program to handle command line parameters and then run what they want.
    """
    BibleOrgSysGlobals.introduceProgram( __name__, programNameVersion, LAST_MODIFIED_DATE )

    vPrint( 'Normal', debuggingThisModule, "\nTesting Genesis 1 in Hebrew…" )
    load_transliteration_table('Hebrew')
    result = transliterate_Hebrew( Genesis_1 )
    vPrint( 'Verbose', debuggingThisModule, result )
    if not check_text(result): have_bad_transliteration

    vPrint( 'Normal', debuggingThisModule, "\nTesting Matthew 1 in Greek…" )
    load_transliteration_table('Greek')
    result = transliterate_Greek( Matthew_1 )
    vPrint( 'Verbose', debuggingThisModule, result )
    if not check_text(result): have_bad_transliteration
# end of BibleTransliterations.briefDemo

def fullDemo() -> None:
    """
    Full demo to check class is working
    """
    BibleOrgSysGlobals.introduceProgram( __name__, programNameVersion, LAST_MODIFIED_DATE )

    source_folderpath = Path( '../../Forked/bibletags-usfm/usfm/uhb/' )
    vPrint( 'Normal', debuggingThisModule, f"\nTesting {source_folderpath} in Hebrew…" )
    load_transliteration_table('Hebrew')
    for entry in source_folderpath.iterdir():
        vPrint( 'Quiet', debuggingThisModule, f"  Loading {entry.name}…" )

        with open( entry, 'rt', encoding='utf-8' ) as source_file:
            source_text = source_file.read()

        result = transliterate_Hebrew( source_text )
        vPrint( 'Verbose', debuggingThisModule, result )

        if not check_text(result):
            logging.critical( f"Failed in {entry.name}!" )
            bad_transliteration

    source_folderpath = Path( '../../CNTR-GNT/derivedFormats/USFM/PlainText/' )
    vPrint( 'Normal', debuggingThisModule, f"\nTesting {source_folderpath} in Greek…" )
    load_transliteration_table('Greek')
    for entry in source_folderpath.iterdir():
        vPrint( 'Quiet', debuggingThisModule, f"  Loading {entry.name}…" )

        with open( entry, 'rt', encoding='utf-8' ) as source_file:
            source_text = source_file.read()

        result = transliterate_Greek( source_text )
        vPrint( 'Verbose', debuggingThisModule, result )

        if not check_text(result):
            logging.critical( f"Failed in {entry.name}!" )
            bad_transliteration
# end of BibleTransliterations.fullDemo

if __name__ == '__main__':
    from multiprocessing import freeze_support
    freeze_support() # Multiprocessing support for frozen Windows executables

    # Configure basic Bible Organisational System (BOS) set-up
    parser = BibleOrgSysGlobals.setup( SHORT_PROGRAM_NAME, PROGRAM_VERSION, LAST_MODIFIED_DATE )
    BibleOrgSysGlobals.addStandardOptionsAndProcess( parser )

    fullDemo()

    BibleOrgSysGlobals.closedown( PROGRAM_NAME, PROGRAM_VERSION )
# end of BibleTransliterations.py
