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

import BibleOrgSysGlobals
from BibleOrgSysGlobals import fnPrint, vPrint, dPrint



LAST_MODIFIED_DATE = '2022-08-19' # by RJH
SHORT_PROGRAM_NAME = "BibleTransliterations"
PROGRAM_NAME = "Bible Transliterations handler"
PROGRAM_VERSION = '0.02'
programNameVersion = f'{SHORT_PROGRAM_NAME} v{PROGRAM_VERSION}'

debuggingThisModule = False



tsv_rows = None
def load_Greek_table(which='Greek') -> bool:
    """
    """
    global tsv_rows
    with open( f'../sourceTables/{which}.tsv', 'rt', encoding='utf-8' ) as greek_table:
        tsv_lines = greek_table.readlines()

    # Remove BOM
    if tsv_lines[0].startswith("\ufeff"):
        vPrint('Quiet', debuggingThisModule, f"  Removing Byte Order Marker (BOM) from start of {which} TSV file…")
        tsv_lines[0] = tsv_lines[0][1:]

    # Get the headers before we start
    original_column_headers = [ header for header in tsv_lines[0].strip().split('\t') ]
    dPrint('Normal', debuggingThisModule, f"  Original column headers: ({len(original_column_headers)}): {original_column_headers}")

    # Read, check the number of columns, and summarise row contents all in one go
    dict_reader = DictReader(tsv_lines, delimiter='\t')
    tsv_rows = []
    # tsv_column_counts = defaultdict(lambda: defaultdict(int))
    source_list, source_set = [], set()
    for n, row in enumerate(dict_reader):
        if len(row) != len(original_column_headers):
            logging.critical(f"Line {n} has {len(row)} column(s) instead of {len(original_column_headers)}: {row} from '{tsv_lines[n+1]}'")
        tsv_rows.append(row)
        assert row['x-grc-koine']
        source_list.append(row['x-grc-koine'])
        source_set.add(row['x-grc-koine'])

    if len(source_set) < len(source_list):
        logging.critical(f"Have a duplicate entry in the set!")
        for source in source_set:
            if source_list.count(source) > 1:
                logging.critical(f"  Have {source_list.count(source)} of '{source}'")
        halt

    # Must sort so the longest sequences go first
    tsv_rows = sorted(tsv_rows, key=lambda k:-len(k['x-grc-koine']))
    vPrint('Quiet', debuggingThisModule, f"  Loaded {len(tsv_rows):,} '{which}' data rows.")
    return True
# end of load_Greek_table()


def transliterate_Greek(input:str) -> str:
    """
    """
    result = input
    for tsv_row in tsv_rows:
        # print( f"  {tsv_row=}")
        result = result.replace( tsv_row['x-grc-koine'], tsv_row['en'] )
    return result
# end of transliterate_Greek function


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

def briefDemo() -> None:
    """
    Main program to handle command line parameters and then run what they want.
    """
    BibleOrgSysGlobals.introduceProgram( __name__, programNameVersion, LAST_MODIFIED_DATE )

    vPrint( 'Normal', debuggingThisModule, "\nTesting Matthew 1 in Greek…" )
    load_Greek_table()
    result = transliterate_Greek( Matthew_1 )
    vPrint( 'Normal', debuggingThisModule, result )
# end of BibleOrganisationalSystem.briefDemo

def fullDemo() -> None:
    """
    Full demo to check class is working
    """
    import unicodedata
    BibleOrgSysGlobals.introduceProgram( __name__, programNameVersion, LAST_MODIFIED_DATE )

    source_folderpath = Path( '../../CNTR-GNT/derivedFormats/USFM/PlainText/' )
    vPrint( 'Normal', debuggingThisModule, f"\nTesting {source_folderpath} in Greek…" )
    load_Greek_table()

    for entry in source_folderpath.iterdir():
        vPrint( 'Quiet', debuggingThisModule, f"  Loading {entry.name}…" )

        with open( entry, 'rt', encoding='utf-8' ) as source_file:
            source_text = source_file.read()

        result = transliterate_Greek( source_text )

        for n,line in enumerate(result.split('\n'), start=1):
            vPrint( 'Info', debuggingThisModule, line )
            for char in line:
                if char in ' ʼ,.?!:;-–/\\1234567890“”‘’()¶…©':
                    continue
                if char in 'χΧ': # We use these in the transliteration
                    continue
                char_name = unicodedata.name(char)
                if 'LATIN' not in char_name:
                    vPrint( 'Quiet', debuggingThisModule, f"From {entry.name} line {n:,}: '{line}'" )
                    logging.critical( f"Found '{char}' {char_name} {unicodedata.category(char)} " )
                    halt
        vPrint( 'Verbose', debuggingThisModule, result )
# end of BibleOrganisationalSystem.fullDemo

if __name__ == '__main__':
    from multiprocessing import freeze_support
    freeze_support() # Multiprocessing support for frozen Windows executables

    # Configure basic Bible Organisational System (BOS) set-up
    parser = BibleOrgSysGlobals.setup( SHORT_PROGRAM_NAME, PROGRAM_VERSION, LAST_MODIFIED_DATE )
    BibleOrgSysGlobals.addStandardOptionsAndProcess( parser )

    fullDemo()

    BibleOrgSysGlobals.closedown( PROGRAM_NAME, PROGRAM_VERSION )
# end of BibleTransliterations.py
