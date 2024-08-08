#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# BibleTransliterations.py
#
# Module handling BibleTransliterations
#
# Copyright (C) 2022-2024 Robert Hunt
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

CHANGELOG:
    2023-03-23 Not sure why unicodedata.name(LF) fails, but catch it now
"""
from gettext import gettext as _
from pathlib import Path
import logging
from csv import  DictReader
import unicodedata

import BibleOrgSysGlobals
from BibleOrgSysGlobals import fnPrint, vPrint, dPrint



LAST_MODIFIED_DATE = '2024-08-07' # by RJH
SHORT_PROGRAM_NAME = "BibleTransliterations"
PROGRAM_NAME = "Bible Transliterations handler"
PROGRAM_VERSION = '0.29'
PROGRAM_NAME_VERSION = f'{SHORT_PROGRAM_NAME} v{PROGRAM_VERSION}'

DEBUGGING_THIS_MODULE = False



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
        vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Removing Byte Order Marker (BOM) from start of {which} TSV file…")
        tsv_lines[0] = tsv_lines[0][1:]

    # Get the headers before we start
    original_column_headers = [ header for header in tsv_lines[0].strip().split('\t') ]
    dPrint('Verbose', DEBUGGING_THIS_MODULE, f"  Original transliteration column headers: ({len(original_column_headers)}): {original_column_headers}")

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
    vPrint('Quiet', DEBUGGING_THIS_MODULE, f"  Loaded {len(destination):,} '{which}' transliteration data rows.")
    return True
# end of load_transliteration_table()


def transliterate_Hebrew(input:str, capitaliseHebrew=False) -> str:
    """
    Hebrew doesn't have capital letters,
        so if the calling function knows it's a name or at the beginning of a sentence,
        we may need to capitalise THE HEBREW PART of the input.
        (It's like this, so if the Hebrew is inside an html span or something,
            then only the first Hebrew word is capitalised, not 'Span'.)

    TODO: This is only a temporary function that sort of works
        but it really needs to be completely rewritten.
        See https://en.wikipedia.org/wiki/Romanization_of_Hebrew.
    """
    fnPrint( DEBUGGING_THIS_MODULE, f"transliterate_Hebrew({input}, {capitaliseHebrew})")

    # Find the index of the first Hebrew character in the INPUT string (will be the same for the output string)
    for first_Hebrew_index,char in enumerate(input):
        try:
            if 'HEBREW' in unicodedata.name(char):
                break
        except ValueError: continue
    else:
        logging.warning( f"transliterate_Hebrew failed to find any Hebrew in '{input}'")
        return input

    for past_Hebrew_index,char in enumerate(reversed(input)):
        try:
            if 'HEBREW' in unicodedata.name(char):
                break
        except ValueError: continue
    past_Hebrew_index = len(input) - past_Hebrew_index
    # print( f"({len(input)}) {input=} {first_Hebrew_index=} {past_Hebrew_index=}")

    # Now extract the Hebrew segment of the input
    hebrewInput = input[first_Hebrew_index:past_Hebrew_index]
    # print( f"({len(hebrewInput)}) {hebrewInput=} {first_Hebrew_index=} {past_Hebrew_index=}")

    # Transliterate Hebrew letters to English
    transliteratedHebrewInput = hebrewInput
    for tsv_row in hebrew_tsv_rows:
        transliteratedHebrewInput = transliteratedHebrewInput.replace( tsv_row['hbo'], tsv_row['en'] )

    # Fix YHWH to our desired 'yahweh'
    # TODO: What if it's in a compound like v... b... m... ?
    # transliteratedHebrewInput = transliteratedHebrewInput.replace( 'yəhvāh', 'yahweh' ) # vowels for adonai -- TODO: Could this be over-reaching, i.e., in the middle of some other word ???

    # Fix something like 'שִׁילֹה' which becomes 'Shiyloh' but shouldn't have that 'y'
    # TODO: Do we need something similar for 'v'?
    searchStartIndex = 0
    for _safetyCount in range( 2_000 ): # 1880 wasn't enough for one of the Hebrew word pages
        try: ixIY = transliteratedHebrewInput.index( 'iy', searchStartIndex )
        except ValueError: break
        try: nextChar = transliteratedHebrewInput[ixIY+2]
        except IndexError: break # it was at the end of the word/string
        if nextChar in 'bdfghklmnpqrsştţvz':
            transliteratedHebrewInput = f'{transliteratedHebrewInput[:ixIY+1]}{transliteratedHebrewInput[ixIY+2:]}' # Delete the y
        searchStartIndex = ixIY + 2
    else:
        logging.critical( f"Not enough {_safetyCount} IY {transliteratedHebrewInput.count( 'iy' )} loop iterations for ({len(hebrewInput)}) {hebrewInput[:200]=}… from {input[:800]=}…" )
        not_enough_loop_iterations_in_transliterateHebrew

    try: # Correct dagesh in first letter giving double letters
        if transliteratedHebrewInput[0] == transliteratedHebrewInput[1]:
            # assert transliteratedHebrewInput[0] in 'bdkt', f"Doubled initial letters {transliteratedHebrewInput=} from {hebrewInput=}"
            transliteratedHebrewInput = transliteratedHebrewInput[1:] # Remove the first of the duplicate letters
            # NOTE: This doesn't work for consecutive words
    except IndexError: pass # probably a very short Hebrew string

    # Now to handle everything properly, we have to post-process each transliterated Hebrew word
    # We get cleaned words, but do the substitutions on the actual transliterated string
    cleanedTransliteratedHebrew = transliteratedHebrewInput.replace( ',',' ' ).replace( '.',' ' ).replace( '-',' ' ) \
                                                           .replace( 'htm#Top">', ' ' ).replace( 'htm">', ' ' ).replace( '</a>', '' ) \
                                                           .replace( '\n',' ') \
                                                           .replace( '   ',' ' ).replace( '  ',' ' ) \
                                                           .rstrip()
    for cc, cleanedTransliteratedHebrewWord in enumerate( cleanedTransliteratedHebrew.split( ' ' ) ):
        assert cleanedTransliteratedHebrewWord, f"transliterate_Hebrew A{cc}: {cleanedTransliteratedHebrew=}"
        if cleanedTransliteratedHebrewWord.isdigit(): continue
        if len(cleanedTransliteratedHebrewWord) < 2: continue
        dPrint('Verbose', DEBUGGING_THIS_MODULE, f"  transliterate_Hebrew B{cc}: {cleanedTransliteratedHebrewWord=}")

        # Handle bad dagesh consonant doubling at the beginning of words
        if cleanedTransliteratedHebrewWord[0] == cleanedTransliteratedHebrewWord[1]:
            # assert cleanedTransliteratedHebrewWord[0] in 'bdkt', f"Doubled initial letters {transliteratedHebrewInput=} from {hebrewInput=}"
            dPrint('Info', DEBUGGING_THIS_MODULE, f"Replacing duplicated initial letters: {cleanedTransliteratedHebrewWord=}")
            if cc == 0: # it's the first word
                transliteratedHebrewInput = transliteratedHebrewInput.replace( cleanedTransliteratedHebrewWord, cleanedTransliteratedHebrewWord[1:], 1 ) # Remove the first of the duplicate letters but only ONCE
            else: # it's not the first word, so we can probably precede it with a space (assuming nothing got cleaned from the beginning of the word already) so we don't over-reach
                # Remove the first of the duplicate letters
                transliteratedHebrewInput = transliteratedHebrewInput.replace( f' {cleanedTransliteratedHebrewWord}', f' {cleanedTransliteratedHebrewWord[1:]}', 1 ) \
                                                                                .replace( f'>{cleanedTransliteratedHebrewWord}', f'>{cleanedTransliteratedHebrewWord[1:]}', 1 )
            cleanedTransliteratedHebrewWord = cleanedTransliteratedHebrewWord[1:] # in case it needs more fixes below
        # elif cleanedTransliteratedHebrewWord.startswith( 'shsh' ):
        #     dPrint('Info', DEBUGGING_THIS_MODULE, f"Replacing duplicated initial letters: {cleanedTransliteratedHebrewWord=}")
        #     if cc == 0: # it's the first word
        #         transliteratedHebrewInput = transliteratedHebrewInput.replace( cleanedTransliteratedHebrewWord, cleanedTransliteratedHebrewWord[2:], 1 ) # Remove the first of the duplicate sh but only ONCE
        #     else: # it's not the first word, so we can probably precede it with a space (assuming nothing got cleaned from the beginning of the word already) so we don't over-reach
        #          # Remove the first of the duplicate letters
        #         transliteratedHebrewInput = transliteratedHebrewInput.replace( f' {cleanedTransliteratedHebrewWord}', f' {cleanedTransliteratedHebrewWord[2:]}', 1 ) \
        #                                                                 .replace( f'>{cleanedTransliteratedHebrewWord}', f'>{cleanedTransliteratedHebrewWord[2:]}', 1 )
        #     cleanedTransliteratedHebrewWord = cleanedTransliteratedHebrewWord[2:] # in case it needs more fixes below

        # Handle final ḩa after we removed the line: חַ	HetPatah	aḩ	# Not ḩa, e.g., in 'נֹ֔חַ' (Noaḩ) IS THIS TOO WIDE, i.e., should only be at WORD END?
        if cleanedTransliteratedHebrewWord.endswith( 'ḩa' ): # Swap the final two letters
            dPrint('Info', DEBUGGING_THIS_MODULE, f"Fixing final two letters: {cleanedTransliteratedHebrewWord=}")
            transliteratedHebrewInput = transliteratedHebrewInput.replace( f'{cleanedTransliteratedHebrewWord}', f'{cleanedTransliteratedHebrewWord[:-2]}aḩ' ) \
                                        if transliteratedHebrewInput.endswith( cleanedTransliteratedHebrewWord ) \
                                    else transliteratedHebrewInput.replace( f'{cleanedTransliteratedHebrewWord} ', f'{cleanedTransliteratedHebrewWord[:-2]}aḩ ', 1 ) \
                                                                    .replace( f'{cleanedTransliteratedHebrewWord}<', f'{cleanedTransliteratedHebrewWord[:-2]}aḩ<', 1 )
    assert not transliteratedHebrewInput.startswith( 'bb' ) and ' bb' not in transliteratedHebrewInput and '>bb' not in transliteratedHebrewInput, f"{transliteratedHebrewInput=} from {hebrewInput=}"
    assert not transliteratedHebrewInput.startswith( 'dd' ) and ' dd' not in transliteratedHebrewInput and '>dd' not in transliteratedHebrewInput, f"{transliteratedHebrewInput=} from {hebrewInput=}"
    assert not transliteratedHebrewInput.startswith( 'kk' ) and ' kk' not in transliteratedHebrewInput and '>kk' not in transliteratedHebrewInput, f"{transliteratedHebrewInput=} from {hebrewInput=}"
    assert not transliteratedHebrewInput.startswith( 'tt' ) and ' tt' not in transliteratedHebrewInput and '>tt' not in transliteratedHebrewInput, f"{transliteratedHebrewInput=} from {hebrewInput=}"
    assert 'ḩa ' not in transliteratedHebrewInput and 'ḩa.' not in transliteratedHebrewInput and 'ḩa<' not in transliteratedHebrewInput, f"{transliteratedHebrewInput=} from {hebrewInput=}"

    # Handle schwa
    # We have to redo the loop because otherwise we get fooled by words that have already changed
    cleanedTransliteratedHebrew = transliteratedHebrewInput.replace( ',',' ' ).replace( '.',' ' ).replace( '\n',' ').replace( '   ',' ' ).replace( '  ',' ' ).rstrip()
    for cc, cleanedTransliteratedHebrewWord in enumerate( cleanedTransliteratedHebrew.split( ' ' ) ):
        assert cleanedTransliteratedHebrewWord, f"transliterate_Hebrew C{cc}: {cleanedTransliteratedHebrew=}"
        if cleanedTransliteratedHebrewWord.isdigit(): continue
        if len(cleanedTransliteratedHebrewWord) < 2: continue
        dPrint('Verbose', DEBUGGING_THIS_MODULE, f"  transliterate_Hebrew D{cc}: {cleanedTransliteratedHebrewWord=}")

        if 'ə' not in cleanedTransliteratedHebrewWord: continue
        searchStartIndex = 0
        for _safetyCount in range(6): # Maximum of five shwa's expected in a single word
            shwaIndex = cleanedTransliteratedHebrewWord.find('ə', searchStartIndex)
            if shwaIndex == -1: break # No more found
            if shwaIndex < 2: # Too near the start of the word to be of interest here
                searchStartIndex = shwaIndex + 1
                continue
            dPrint('Verbose', DEBUGGING_THIS_MODULE, f"  Found ə in '{cleanedTransliteratedHebrewWord}' at {shwaIndex=}")
            prevChar1, prevChar2, prevChar3 = cleanedTransliteratedHebrewWord[shwaIndex-1], cleanedTransliteratedHebrewWord[shwaIndex-2], cleanedTransliteratedHebrewWord[shwaIndex-3]
            try: nextChar1 = cleanedTransliteratedHebrewWord[shwaIndex+1]
            except IndexError: nextChar1 = ' ' # None doesn't work below
            try: nextChar2 = cleanedTransliteratedHebrewWord[shwaIndex+2]
            except IndexError: nextChar2 = None
            # dPrint('Verbose', DEBUGGING_THIS_MODULE, f"    Expected a consonant at {prevChar1=} preceded by {prevChar2=} from '{cleanedTransliteratedHebrewWord}' from '{input}'")
            numLettersToDelete = 1 # Usually just the shwa marking the end of a syllable
            if prevChar1 in 'ʼˊbdfghḩkⱪlmnpqrsşštţʦvⱱyz' and prevChar2 in 'aeiou': # short vowels, then this shwa should be a silent one
                dPrint('Info', DEBUGGING_THIS_MODULE, f"      RemovingA schwa preceded by short vowel '{prevChar2}' from '{cleanedTransliteratedHebrewWord}' from '{input}'")
                if nextChar1 in 'dgkmqrʦy' and nextChar2==nextChar1: # then the next consonant must have a dagesh
                    numLettersToDelete = 2 # But it doesn't need to be doubled at the beginning of the next syllable
                    dPrint('Verbose', DEBUGGING_THIS_MODULE, f"       Also removing doubled '{nextChar1}' after shwa from '{cleanedTransliteratedHebrewWord}'" )
                # elif cleanedTransliteratedHebrewWord[shwaIndex+1:].startswith( 'shsh' ):
                #     numLettersToDelete = 3 # But it doesn't need to be doubled at the beginning of the next syllable
                #     print( f"       Also removing doubled 'sh' after shwa from '{cleanedTransliteratedHebrewWord}'" )
                #     has_not_been_executed_yet
                newWord = f'{cleanedTransliteratedHebrewWord[:shwaIndex]}{cleanedTransliteratedHebrewWord[shwaIndex+numLettersToDelete:]}'
                dPrint('Verbose', DEBUGGING_THIS_MODULE, f"        Replacing '{cleanedTransliteratedHebrewWord}' with '{newWord}'")
                transliteratedHebrewInput = transliteratedHebrewInput.replace( cleanedTransliteratedHebrewWord, newWord ) # Will only work correctly ONCE FOR EACH WORD
                cleanedTransliteratedHebrewWord = newWord
                searchStartIndex = shwaIndex
            # elif prevChar1=='h' and prevChar2=='s' and prevChar3 in 'aeiou': # short vowels, then this shwa should be a silent one, e.g., after a 'sh'
            #     dPrint('Info', DEBUGGING_THIS_MODULE, f"      RemovingB schwa preceded by short vowel '{prevChar3}' from '{cleanedTransliteratedHebrewWord}' from '{input}'")
            #     assert prevChar2 in 's' and prevChar1 in 'h', f"{prevChar2=} and {prevChar1=}"
            #     if nextChar1 in 'dgkmqrʦy' and nextChar2==nextChar1: # then the next consonant must have a dagesh
            #         numLettersToDelete = 2 # But it doesn't need to be doubled at the beginning of the next syllable
            #         dPrint('Verbose', DEBUGGING_THIS_MODULE, f"       Also removing doubled '{nextChar1}' after shwa from '{cleanedTransliteratedHebrewWord}'" )
            #     elif cleanedTransliteratedHebrewWord[shwaIndex+1:].startswith( 'shsh' ):
            #         numLettersToDelete = 3 # But it doesn't need to be doubled at the beginning of the next syllable
            #         print( f"       Also removing doubled 'sh' after shwa from '{cleanedTransliteratedHebrewWord}'" )
            #         has_not_been_executed_yet
            #     newWord = f'{cleanedTransliteratedHebrewWord[:shwaIndex]}{cleanedTransliteratedHebrewWord[shwaIndex+numLettersToDelete:]}'
            #     dPrint('Verbose', DEBUGGING_THIS_MODULE, f"        Replacing '{cleanedTransliteratedHebrewWord}' with '{newWord}'")
            #     transliteratedHebrewInput = transliteratedHebrewInput.replace( cleanedTransliteratedHebrewWord, newWord ) # Will only work correctly ONCE FOR EACH WORD
            #     cleanedTransliteratedHebrewWord = newWord
            #     searchStartIndex = shwaIndex
            else:
                searchStartIndex = shwaIndex + 1
        else: not_enough_schwa_loops
        # TODO: To be continued....

    # Tidy up shin temporary single-consonant 'š' (for easier processing above) to English 'sh'
    transliteratedHebrewInput = transliteratedHebrewInput.replace( 'š', 'sh' )

    # Check that our function is working
    for thChar in transliteratedHebrewInput:
        if thChar!='\n' and 'HEBREW' in unicodedata.name(thChar):
            logging.critical(f"Have some Hebrew left-overs ({unicodedata.name(thChar)}) in '{transliteratedHebrewInput}' FROM '{input}'")
            stop_so_we_can_fix_the_Hebrew_table

    # if 1: # new code
    if not capitaliseHebrew:
        return f'{input[:first_Hebrew_index]}{transliteratedHebrewInput}{input[past_Hebrew_index:]}'

    # Ok, we have to title case it -- presumably the entire string, not each individual word
    if transliteratedHebrewInput[0] == 'ʦ': # This digraph doesn't have an UPPERCASE form in Unicode
        capitalisedHebrew = f'Ts{transliteratedHebrewInput[1:]}'
    elif transliteratedHebrewInput[0] == 'ₐ': # This subscript character doesn't have an UPPERCASE form in Unicode
        capitalisedHebrew = f'A{transliteratedHebrewInput[1:]}'
    elif transliteratedHebrewInput[0] == 'ₑ': # This subscript character doesn't have an UPPERCASE form in Unicode
        capitalisedHebrew = f'E{transliteratedHebrewInput[1:]}'
    elif transliteratedHebrewInput[0] == 'ⱱ': # This hooked character doesn't have an UPPERCASE form in Unicode
        capitalisedHebrew = f'V{transliteratedHebrewInput[1:]}'
    elif transliteratedHebrewInput[0] in 'ʼˊ':
        if transliteratedHebrewInput[1] == 'ʦ': # This digraph doesn't have an UPPERCASE form in Unicode
            capitalisedHebrew = f'{transliteratedHebrewInput[0]}Ts{transliteratedHebrewInput[2:]}'
        elif transliteratedHebrewInput[1] == 'ₐ': # This subscript character doesn't have an UPPERCASE form in Unicode
            capitalisedHebrew = f'{transliteratedHebrewInput[0]}A{transliteratedHebrewInput[2:]}'
        elif transliteratedHebrewInput[1] == 'ₑ': # This subscript character doesn't have an UPPERCASE form in Unicode
            capitalisedHebrew = f'{transliteratedHebrewInput[0]}E{transliteratedHebrewInput[2:]}'
        elif transliteratedHebrewInput[1] == 'ⱱ': # This hooked character doesn't have an UPPERCASE form in Unicode
            capitalisedHebrew = f'{transliteratedHebrewInput[0]}V{transliteratedHebrewInput[2:]}'
        else:
            capitalisedHebrew = f'{transliteratedHebrewInput[0]}{transliteratedHebrewInput[1].upper()}{transliteratedHebrewInput[2:]}' # Skip past either of the glottals and uppercase the next letter
    else: # The normal case
        capitalisedHebrew = f'{transliteratedHebrewInput[0].upper()}{transliteratedHebrewInput[1:]}'
    assert capitalisedHebrew != transliteratedHebrewInput, f'({len(hebrewInput)}) {hebrewInput=} ({len(transliteratedHebrewInput)}) {transliteratedHebrewInput=} ({len(capitalisedHebrew)}) {capitalisedHebrew=}'
    return f'{input[:first_Hebrew_index]}{capitalisedHebrew}{input[past_Hebrew_index:]}'
    # else: # old code
    #     assembled_result = f'{input[:first_Hebrew_index]}{transliteratedHebrewInput}{input[past_Hebrew_index:]}'
    #     if not capitaliseHebrew:
    #         return assembled_result

    #     # Ok, we have to title case it -- presumably the entire string
    #     if assembled_result[first_Hebrew_index] == 'ʦ':
    #         return assembled_result.replace( 'ʦ', 'Ts', 1 ) # This digraph doesn't have an UPPERCASE form

    #     # print(f"Title-casing '{result}' '{result[first_Hebrew_index:first_Hebrew_index+2]}' to '{result[:first_Hebrew_index+2].title()}'")
    #     return f'{assembled_result[:first_Hebrew_index]}{assembled_result[first_Hebrew_index:first_Hebrew_index+2].title()}{assembled_result[first_Hebrew_index+2:]}' # Title case, but don't want something like Rəḩavə'Ām
# end of transliterate_Hebrew function


def transliterate_Greek(input:str) -> str:
    """
    """
    result = input
    # Find the index of the first Greek character in the INPUT string (will be the same for the output string)
    for first_Greek_index,char in enumerate(input):
        # print( f"{first_Greek_index} ({ord(char)}) '{char}' from '{input}'")
        try:
            if 'GREEK' in unicodedata.name(char):
                break
        except ValueError: continue
    else:
        logging.warning( f"transliterate_Greek failed to find any Greek in '{input}'")
        return result

    for tsv_row in greek_tsv_rows:
        # print( f"  {tsv_row=} with {result=} from {input=}")
        result = result.replace( tsv_row['x-grc-koine'], tsv_row['en'] )

    # Transform aui to awi (esp. Dauid to Dawid)
    if 'aui' in result[first_Greek_index:]:
        result = f"{result[:first_Greek_index]}{result[first_Greek_index:].replace('aui','awi')}"

    for tgChar in result:
        if tgChar!='\n' and 'GREEK' in unicodedata.name(tgChar):
            logging.critical(f"Have some Greek left-overs ({unicodedata.name(tgChar)}) in '{result}' from '{input}'")
            stop_so_we_can_fix_the_Greek_table

    # Transform ie to ye at start
    for inChars,outChars in ( ('ie','ye'), ('Ie','Ye') ):
        if result[first_Greek_index:].startswith( inChars):
            result = f'{result[:first_Greek_index]}{outChars}{result[first_Greek_index+2:]}'
            break

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
2:4 אֵ֣לֶּה תוֹלְד֧וֹת הַשָּׁמַ֛יִם וְהָאָ֖רֶץ בְּהִבָּֽרְאָ֑ם בְּי֗וֹם עֲשׂ֛וֹת יְהוָ֥ה אֱלֹהִ֖ים אֶ֥רֶץ וְשָׁמָֽיִם׃
6:8 וְנֹ֕חַ מָ֥צָא חֵ֖ן בְּעֵינֵ֥י יְהוָֽה׃פ
'''
Expected_Gen_1_result_words = ['Chapter', '1',
                               '1', 'bərēʼshiyt', 'bārāʼ', 'ʼₑlohiym', 'ʼēt', 'hashshāmayim', 'vəʼēt', 'hāʼāreʦ.',
                               '2', 'vəhāʼāreʦ', 'hāyətāh', 'tohū', 'vāⱱohū', 'vəḩoshek', 'ˊal-pənēy', 'təhōm', 'vərūaḩ', 'ʼₑlohiym', 'məraḩefet', 'ˊal-pənēy', 'hammāyim.',
                               '3', 'vayyoʼmer', 'ʼₑlohiym', 'yəhiy', 'ʼōr', 'vayhī-ʼōr.',
                               '4', 'vayyarʼ', 'ʼₑlohiym', 'ʼet-hāʼōr', 'ⱪī-ţōⱱ', 'vayyaⱱddēl', 'ʼₑlohiym', 'bēyn', 'hāʼōr', 'ūⱱēyn', 'haḩoshek.',
                               '5', 'vayyiqrāʼ', 'ʼₑlohiym', 'lāʼōr', 'yōm', 'vəlaḩoshek', 'qārāʼ', 'lāyəlāh', 'vayhī-ˊereⱱ', 'vayhī-ⱱoqer', 'yōm', 'ʼeḩād.', 'f',

                               '6', 'vayyoʼmer', 'ʼₑlohiym', 'yəhiy', 'rāqiyˊa', 'bətōk', 'hammāyim', 'vīhiy', 'maⱱddiyl', 'bēyn', 'mayim', 'lāmāyim.',
                               '7', 'vayyaˊas', 'ʼₑlohīm', 'ʼet-hārāqīˊa', 'vayyaⱱddēl', 'bēyn', 'hammayim', 'ʼₐsher', 'mittaḩat', 'lārāqiyˊa', 'ūⱱēyn', 'hammayim', 'ʼₐsher', 'mēˊal', 'lārāqiyˊa', 'vayhī-kēn.',
                               '8', 'vayyiqrāʼ', 'ʼₑlohiym', 'lārāqiyˊa', 'shāmāyim', 'vayhī-ˊereⱱ', 'vayhī-ⱱoqer', 'yōm', 'shēniy.', 'f',

                               '9', 'vayyoʼmer', 'ʼₑlohiym', 'yiqqāvū', 'hammayim', 'mittaḩat', 'hashshāmayim', 'ʼel-māqōm', 'ʼeḩād', 'vətērāʼeh', 'hayyabāshāh', 'vayhī-kēn.',
                               '10', 'vayyiqrāʼ', 'ʼₑlohiym', 'layyabāshāh', 'ʼereʦ', 'ūləmiqvēh', 'hammayim', 'qārāʼ', 'yammiym', 'vayyarʼ', 'ʼₑlohiym', 'ⱪī-ţōⱱ.',
                               '11', 'vayyoʼmer', 'ʼₑlohiym', 'tadshēʼ', 'hāʼāreʦ', 'desheʼ', 'ˊēseⱱ', 'mazriyˊa', 'zeraˊ', 'ˊēʦ', 'pəriy', 'ˊoseh', 'pərī', 'ləmīnō', 'ʼₐsher', 'zarˊō-ⱱō', 'ˊal-hāʼāreʦ', 'vayhī-kēn.',
                               '12', 'vattōʦēʼ', 'hāʼāreʦ', 'desheʼ', 'ˊēseⱱ', 'mazriyˊa', 'zeraˊ', 'ləmīnēhū', 'vəˊēʦ', 'ˊoseh-pəriy', '', 'ʼₐsher', 'zarˊō-ⱱō', 'ləmīnēhū', 'vayyarʼ', 'ʼₑlohiym', 'ⱪī-ţōⱱ.',
                               '13', 'vayhī-ˊereⱱ', 'vayhī-ⱱoqer', 'yōm', 'shəlīshiy.', 'f',

                               '14', 'vayyoʼmer', 'ʼₑlohiym', 'yəhiy', 'məʼorot', 'birqiyˊa', 'hashshāmayim', 'ləhaⱱddiyl', 'bēyn', 'hayyōm', 'ūⱱēyn', 'hallāyəlāh', 'vəhāyū', 'ləʼotot', 'ūləmōˊₐdiym', 'ūləyāmiym', 'vəshāniym.',
                               '15', 'vəhāyū', 'limʼōrot', 'birqiyˊa', 'hashshāmayim', 'ləhāʼiyr', 'ˊal-hāʼāreʦ', 'vayhī-kēn.',
                               '16', 'vayyaˊas', 'ʼₑlohiym', 'ʼet-shənēy', 'hamməʼorot', 'haggədoliym', 'ʼet-hammāʼōr', 'haggādol', 'ləmemshelet', 'hayyōm',
                                        'vəʼet-hammāʼōr', 'haqqāţon', 'ləmemshelet', 'hallaylāh', 'vəʼēt', 'haⱪōkāⱱiym.',
                               '17', 'vayyittēn', 'ʼotām', 'ʼₑlohiym', 'birqiyˊa', 'hashshāmāyim', 'ləhāʼiyr', 'ˊal-hāʼāreʦ.',
                               '18', 'vəlimshol', 'bayyōm', 'ūⱱallaylāh', 'ūlₐhaⱱddiyl', 'bēyn', 'hāʼōr', 'ūⱱēyn', 'haḩoshek', 'vayyarʼ', 'ʼₑlohiym', 'ⱪī-ţōⱱ.',
                               '19', 'vayhī-ˊereⱱ', 'vayhī-ⱱoqer', 'yōm', 'rəⱱīˊiy.', 'f',

                               '20', 'vayyoʼmer', 'ʼₑlohiym', 'yishərəʦū', 'hammayim', 'shereʦ', 'nefesh', 'ḩayyāh', 'vəˊōf', 'yəˊōfēf', 'ˊal-hāʼāreʦ', 'ˊal-pənēy', 'rəqiyˊa', 'hashshāmāyim.',
                               '21', 'vayyiⱱrāʼ', 'ʼₑlohiym', 'ʼet-hattannīnim', 'haggədoliym',
                                        'vəʼēt', 'ⱪāl-nefesh', 'haḩayyāh', 'hāromeset', 'ʼₐsher', 'shārəʦū', 'hammayim', 'ləmiynēhem', 'vəʼēt', 'ⱪāl-ˊōf', 'ⱪānāf', 'ləmīnēhū', 'vayyarʼ', 'ʼₑlohiym', 'ⱪī-ţōⱱ.',
                               '22', 'vayⱱārek', 'ʼotām', 'ʼₑlohiym', 'lēʼmor', 'pərū', 'ūrəⱱū', 'ūmilʼū', 'ʼet-hammayim', 'bayyammiym', 'vəhāˊōf', 'yireⱱ', 'bāʼāreʦ.',
                               '23', 'vayhī-ˊereⱱ', 'vayhī-ⱱoqer', 'yōm', 'ḩₐmīshiy.', 'f',

                               '24', 'vayyoʼmer', 'ʼₑlohiym', 'tōʦēʼ', 'hāʼāreʦ', 'nefesh', 'ḩayyāh', 'ləmīnāh', 'bəhēmāh', 'vāremes', 'vəḩaytō-ʼereʦ', 'ləmīnāh', 'vayhī-kēn.',
                               '25', 'vayyaˊas', 'ʼₑlohīm', 'ʼet-ḩayyat', 'hāʼāreʦ', 'ləmīnāh', 'vəʼet-habhēmāh', 'ləmīnāh', 'vəʼēt', 'ⱪāl-remes', 'hāʼₐdāmāh', 'ləmīnēhū', 'vayyarʼ', 'ʼₑlohiym', 'ⱪī-ţōⱱ.',
                               '26', 'vayyoʼmer', 'ʼₑlohiym', 'naˊₐseh', 'ʼādām', 'bəʦalmēnū', 'ⱪidmūtēnū', 'vəyirddū', 'ⱱidgat', 'hayyām', 'ūⱱəˊōf', 'hashshāmayim', 'ūⱱabhēmāh', 'ūⱱəkāl-hāʼāreʦ', 'ūⱱəkāl-hāremes', 'hāromēs', 'ˊal-hāʼāreʦ.',
                               '27', 'vayyiⱱrāʼ', 'ʼₑlohiym', 'ʼet-hāʼādām', 'bəʦalmō', 'bəʦelem', 'ʼₑlohiym', 'bārāʼ', 'ʼotō', 'zākār', 'ūnəqēⱱāh', 'bārāʼ', 'ʼotām.',
                               '28', 'vayⱱārek', 'ʼotām', 'ʼₑlohīm', 'vayyoʼmer', 'lāhem', 'ʼₑlohiym', 'pərū', 'ūrəⱱū', 'ūmilʼū', 'ʼet-hāʼāreʦ',
                                        'vəkiⱱshuhā', 'ūrədū', 'bidgat', 'hayyām', 'ūⱱəˊōf', 'hashshāmayim', 'ūⱱəkāl-ḩayyāh', 'hāromeset', 'ˊal-hāʼāreʦ.',
                               '29', 'vayyoʼmer', 'ʼₑlohiym', 'hinnēh', 'nātattī', 'lākem', 'ʼet-ⱪāl-ˊēseⱱ', 'zorēˊa', 'zeraˊ', 'ʼₐsher', 'ˊal-pənēy', 'kāl-hāʼāreʦ',
                                        'vəʼet-ⱪāl-hāˊēʦ', 'ʼₐsher-bō', 'fərī-ˊēʦ', 'zorēˊa', 'zāraˊ', 'lākem', 'yihyeh', 'ləʼākəlāh.',
                               '30', 'ūləkāl-ḩayyat', 'hāʼāreʦ', 'ūləkāl-ˊōf', 'hashshāmayim', 'ūləkol', 'rōmēs', 'ˊal-hāʼāreʦ', 'ʼₐsher-bō', 'nefesh', 'ḩayyāh', 'ʼet-ⱪāl-yereq', 'ˊēseⱱ', 'ləʼākəlāh', 'vayhī-kēn.',
                               '31', 'vayyarʼ', 'ʼₑlohīm', 'ʼet-ⱪāl-ʼₐsher', 'ˊāsāh', 'vəhinnēh-ţōⱱ', 'məʼod', 'vayhī-ˊereⱱ', 'vayhī-ⱱoqer', 'yōm', 'hashshishshiy.', 'f',
                               '2:4', 'ʼēlleh', 'tōlədōt', 'hashshāmayim', 'vəhāʼāreʦ', 'bəhibārəʼām', 'bəyōm', 'ˊₐsōt', 'yahweh', 'ʼₑlohiym', 'ʼereʦ', 'vəshāmāyim.',
                               '6:8', 'vənoaḩ', 'māʦāʼ', 'ḩēn', 'bəˊēynēy', 'yahweh.◊']


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
    for c,char in enumerate(line, start=1):
        if char in ' ʼ,.?!:;-–/\\1234567890“”‘’()¶…©':
            continue
        try:
            char_name = unicodedata.name(char)
        except ValueError: continue
        if 'GREEK' in char_name or 'HEBREW' in char_name:
            return c, char, char_name
    return True
# end of BibleTransliterations.check_line

def check_text(text:str):
    """
    """
    for l,line in enumerate(text.split('\n'), start=1):
        vPrint( 'Info', DEBUGGING_THIS_MODULE, line )
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
    BibleOrgSysGlobals.introduceProgram( __name__, PROGRAM_NAME_VERSION, LAST_MODIFIED_DATE )

    vPrint( 'Normal', DEBUGGING_THIS_MODULE, "\nTesting Genesis 1 in Hebrew…" )
    load_transliteration_table('Hebrew')
    result = transliterate_Hebrew( Genesis_1 )
    vPrint( 'Verbose', DEBUGGING_THIS_MODULE, result )
    if not check_text(result): have_bad_transliteration
    resultWords = result.rstrip().replace( '\n', ' ' ).replace( '  ', ' ' ).split( ' ' )
    vPrint( 'Verbose', DEBUGGING_THIS_MODULE, f"({len(resultWords)}) {resultWords=}" )
    for n, (current_result_word, previous_result_word) in enumerate( zip( resultWords, Expected_Gen_1_result_words, strict=True ), start=1 ):
        if current_result_word != previous_result_word:
            logging.critical( f"Result word {n} differs: ({len(current_result_word)}) {current_result_word=} vs ({len(previous_result_word)}) {previous_result_word=}" )
            halt

    vPrint( 'Normal', DEBUGGING_THIS_MODULE, "\nTesting Matthew 1 in Greek…" )
    load_transliteration_table('Greek')
    result = transliterate_Greek( Matthew_1 )
    vPrint( 'Verbose', DEBUGGING_THIS_MODULE, result )
    if not check_text(result): have_bad_transliteration

    vPrint( 'Normal', DEBUGGING_THIS_MODULE, "\nTesting Hebrew schwa's…" )
    for hebWord in ('וְ⁠אֶל־מֹשֶׁ֨ה', 'אֶל־יְהוָ֗ה', 'וְ⁠אַהֲרֹן֙', 'וְ⁠שִׁבְעִ֖ים', 'מִ⁠זִּקְנֵ֣י', 'יִשְׂרָאֵ֑ל', 'וְ⁠הִשְׁתַּחֲוִיתֶ֖ם'):
        hebWord = hebWord.replace( '\u2060', '' ) # Remove word joiners
        assert 'ְ' in hebWord, f"{hebWord}"
        translit = transliterate_Hebrew( hebWord )
        print( f"{hebWord=} then {translit=}")
# end of BibleTransliterations.briefDemo

def fullDemo() -> None:
    """
    Full demo to check class is working
    """
    BibleOrgSysGlobals.introduceProgram( __name__, PROGRAM_NAME_VERSION, LAST_MODIFIED_DATE )

    source_folderpath = Path( '../../Forked/bibletags-usfm/usfm/uhb/' )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"\nTesting {source_folderpath} in Hebrew…" )
    load_transliteration_table('Hebrew')
    for entry in source_folderpath.iterdir():
        vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Loading {entry.name}…" )

        with open( entry, 'rt', encoding='utf-8' ) as source_file:
            source_text = source_file.read()

        result = transliterate_Hebrew( source_text )
        vPrint( 'Verbose', DEBUGGING_THIS_MODULE, result )

        if not check_text(result):
            logging.critical( f"Failed in {entry.name}!" )
            bad_transliteration

    source_folderpath = Path( '../../CNTR-GNT/derivedFormats/USFM/PlainText/' )
    vPrint( 'Normal', DEBUGGING_THIS_MODULE, f"\nTesting {source_folderpath} in Greek…" )
    load_transliteration_table('Greek')
    for entry in source_folderpath.iterdir():
        vPrint( 'Quiet', DEBUGGING_THIS_MODULE, f"  Loading {entry.name}…" )

        with open( entry, 'rt', encoding='utf-8' ) as source_file:
            source_text = source_file.read()

        result = transliterate_Greek( source_text )
        vPrint( 'Verbose', DEBUGGING_THIS_MODULE, result )

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

    briefDemo()

    BibleOrgSysGlobals.closedown( PROGRAM_NAME, PROGRAM_VERSION )
# end of BibleTransliterations.py
