"""Hand-checked structural annotations for the source text.

Line numbers are 1-based line numbers of the .txt file whose name starts with the
given prefix.  Everything not listed here is ordinary body text, a section heading
(an ALL-CAPS line) or part of the chapter head / reading list.
"""

# (first_line, last_line, kind[, extra])
#   sidebar   boxed aside; its first line is the title
#   subhead   run-on heading inside a sidebar
#   quote     block quotation
#   narrow    a narrow prose block (set as a block quotation)
#   verse     poetry / creed: source line breaks are kept.  extra = measure in em:
#             lines that were only wrapped at that measure are joined again
#   lines     a displayed list of short lines
#   display   centred display lines
#   list      numbered list ("1. ...")
#   caption   caption of an illustration that is not in the text source
#   figtitle  title of a chart, map or timeline that is not in the text source
#   table     a table (rebuilt by hand in TABLES)
BLOCKS = {
    '07_': [(6, 10, 'narrow'), (124, 138, 'sidebar')],
    '08_': [(23, 28, 'verse'), (63, 75, 'sidebar'), (97, 109, 'sidebar'), (395, 403, 'quote')],
    '10_': [(53, 60, 'sidebar'), (254, 262, 'quote'), (268, 275, 'quote'), (347, 352, 'quote')],
    '11_': [(202, 207, 'quote')],
    '12_': [(59, 101, 'sidebar'), (169, 174, 'verse'), (228, 250, 'sidebar'), (234, 234, 'subhead'),
            (235, 250, 'list'), (271, 287, 'sidebar'), (324, 348, 'sidebar'), (380, 393, 'verse'),
            (394, 394, 'figtitle'), (400, 426, 'sidebar'), (401, 401, 'subhead'), (465, 502, 'sidebar')],
    '13_': [(88, 92, 'quote'), (175, 180, 'quote'), (359, 359, 'figtitle'), (365, 374, 'sidebar')],
    '14_': [(103, 142, 'list')],
    '15_': [(190, 198, 'quote'), (199, 203, 'caption')],
    '17_': [(40, 46, 'quote'), (142, 150, 'sidebar'), (160, 167, 'verse'), (216, 227, 'quote'),
            (260, 266, 'quote'), (278, 283, 'quote')],
    '18_': [(6, 10, 'verse'), (25, 30, 'quote'), (47, 72, 'sidebar'), (159, 177, 'quote'),
            (186, 193, 'quote'), (263, 300, 'sidebar')],
    '19_': [(253, 259, 'quote')],
    '20_': [(8, 15, 'quote'), (155, 161, 'quote')],
    '21_': [(271, 275, 'quote')],
    '22_': [(236, 241, 'quote'), (314, 320, 'quote')],
    '23_': [(33, 52, 'sidebar'), (34, 52, 'list'), (315, 332, 'quote')],
    '26_': [(304, 318, 'quote')],
    '27_': [(123, 128, 'quote'), (139, 144, 'quote'), (247, 252, 'sidebar'), (284, 291, 'quote'),
            (341, 349, 'quote')],
    '28_': [(194, 198, 'quote'), (217, 221, 'verse'), (254, 262, 'quote'), (358, 358, 'figtitle'),
            (360, 360, 'figtitle')],
    '29_': [(56, 62, 'quote'), (151, 155, 'quote'), (297, 303, 'caption')],
    '31_': [(267, 267, 'figtitle')],
    '32_': [(144, 150, 'caption'), (152, 155, 'caption'), (242, 251, 'sidebar'), (275, 280, 'quote')],
    '34_': [(77, 82, 'quote'), (91, 105, 'verse'), (174, 245, 'sidebar'), (175, 175, 'subhead'),
            (189, 208, 'table'), (209, 209, 'subhead'), (225, 225, 'subhead'), (328, 333, 'caption'),
            (334, 334, 'figtitle')],
    '35_': [(175, 184, 'quote')],
    '38_': [(42, 54, 'sidebar'), (43, 54, 'list'), (167, 172, 'quote')],
    '40_': [(9, 12, 'quote'), (299, 299, 'figtitle')],
    '43_': [(9, 14, 'quote'), (49, 60, 'quote'), (102, 115, 'sidebar'), (156, 157, 'verse'),
            (310, 315, 'quote')],
    '44_': [(10, 20, 'verse', 22.75), (64, 77, 'sidebar'), (194, 199, 'quote'), (224, 245, 'sidebar'),
            (315, 324, 'quote')],
    '45_': [(68, 75, 'verse'), (174, 180, 'quote')],
    '46_': [(17, 18, 'display'), (20, 21, 'display')],
    '48_': [(142, 153, 'quote'), (213, 236, 'sidebar')],
    '49_': [(4, 7, 'verse'), (14, 17, 'verse'), (42, 49, 'sidebar'), (206, 214, 'quote')],
    '50_': [(172, 179, 'verse')],
    '51_': [(52, 56, 'quote'), (105, 111, 'quote'), (288, 291, 'caption')],
    '52_': [(49, 67, 'sidebar'), (257, 258, 'verse'), (263, 270, 'quote')],
    '53_': [(6, 13, 'quote'), (146, 151, 'quote'), (159, 165, 'quote'), (332, 335, 'verse'),
            (351, 359, 'quote')],
    '55_': [(389, 416, 'quote')],
    '56_': [(62, 71, 'sidebar'), (140, 159, 'table'), (243, 249, 'quote')],
    '57_': [(265, 271, 'lines'), (294, 298, 'quote')],
    '60_': [(107, 127, 'sidebar'), (355, 388, 'sidebar')],
    '61_': [(19, 24, 'quote'), (82, 95, 'sidebar'), (151, 175, 'table'), (218, 230, 'sidebar')],
}

# ALL-CAPS lines that are not section headings.
NOT_HEADING = {('46_', 17), ('46_', 18)}

# Paragraph breaks that the line widths cannot show (the last line of the paragraph
# happens to be full): "a new paragraph starts after this source line".  Decided by reading.
BREAK_AFTER = {
    ('07_', 35),
    ('08_', 338), ('08_', 387), ('08_', 408),
    ('10_', 202), ('10_', 243),
    ('11_', 52), ('11_', 125), ('11_', 289),
    ('12_', 38), ('12_', 190), ('12_', 195), ('12_', 257), ('12_', 307), ('12_', 311),
    ('13_', 147),
    ('14_', 204),
    ('15_', 145), ('15_', 153),
    ('17_', 242),
    ('18_', 224), ('18_', 252),
    ('19_', 18),
    ('20_', 35),
    ('22_', 117),
    ('23_', 168),
    ('24_', 70), ('24_', 144), ('24_', 215),
    ('26_', 47), ('26_', 73),
    ('27_', 258), ('27_', 353),
    ('28_', 25),
    ('29_', 124),
    ('30_', 11), ('30_', 318),
    ('31_', 108), ('31_', 277),
    ('34_', 126),
    ('35_', 94), ('35_', 155),
    ('36_', 19), ('36_', 142),
    ('37_', 149),
    ('38_', 74),
    ('39_', 7), ('39_', 48), ('39_', 124), ('39_', 186),
    ('40_', 15), ('40_', 81), ('40_', 191), ('40_', 203), ('40_', 259),
    ('41_', 92), ('41_', 113), ('41_', 229), ('41_', 234),
    ('43_', 262),
    ('44_', 184), ('44_', 291), ('44_', 372),
    ('45_', 134), ('45_', 217),
    ('48_', 78), ('48_', 166), ('48_', 348), ('48_', 375),
    ('49_', 150), ('49_', 306),
    ('50_', 10), ('50_', 216), ('50_', 277), ('50_', 313),
    ('51_', 42), ('51_', 98),
    ('52_', 244),
    ('55_', 163), ('55_', 259),
    ('57_', 305),
    ('60_', 26), ('60_', 210), ('60_', 293),
    ('61_', 239),
    ('62_', 39),
    ('40_', 337),                              # reading list: "Watkins. Owen C." starts an entry
    ('64_', 95), ('64_', 228),                 # notes: a new note after a full line
}

# Places where a paragraph (or entry) must NOT be broken although the line model allows it.
JOIN_AFTER = {
    ('26_', 41),      # an italic book title makes this first line look short
    ('32_', 313), ('38_', 346),     # reading lists: continuation lines that look like a new entry
    ('35_', 317),                   # reading list: an entry whose second line is not indented
    ('64_', 184),                   # notes: an early line break inside one note
}

# The Epilogue has two signed halves; its structure is fixed by hand (line numbers of 63_).
BLOCKS['63_'] = [(63, 72, 'verse'), (77, 81, 'verse')]
EPILOGUE = {
    'byline1': 2, 'epigraph': (3, 10), 'epigraph_by': 11, 'epigraph_work': (12, 13),
    'body1': (14, 81), 'byline2': 82, 'body2': (83, 232),
}

# Hand-built tables.  Cells are given exactly as the words appear in the source lines.
TABLES = {
    ('34_', 189): {
        'title': 'Summary of Righteousness',
        'cols': 2,
        'header': ['Augustine’s view of righteousness (Catholic model)',
                   'Luther’s view of righteousness (Protestant model)'],
        'rows': [
            ['Faithful followers are made righteous in the spiritual pilgrimage',
             'Believers are declared righteous and only then can progress to become more holy experientially'],
            ['Righteousness is acquired in a process', 'Righteousness is received in an event'],
            ['Righteousness is imparted', 'Righteousness is imputed'],
            ['Righteousness is an inner state, infused or implanted', 'Righteousness is external to the believer'],
            ['Justification and Sanctification are a seamless unity',
             'Justification and Sanctification are vigorously distinguished[1]'],
        ],
    },
    ('56_', 140): {
        'title': 'Three Crucial Ages of Dispensationalism',
        'cols': 4,
        'header': ['', '. . . Jewish age', 'Church age', '1,000 year rule'],
        'rows': [
            ['People', 'Israel', 'Church', 'Israel/ World'],
            ['Predominant Race', 'Hebrews', 'Gentiles', 'Hebrews/ World'],
            ['Jesus’ role', 'Jesus comes to be king over Israel.',
             'After rejection, Jesus turns to Gentiles and mercifully dies to pay for sin.',
             'Jesus returns to rule for 1,000 years.'],
        ],
    },
    ('61_', 151): {
        'title': None,
        'cols': 3,
        'header': ['Regions as Designated by David Barrett',
                   'Number of Charismatic/Pentecostal Christians in Millions in 1900',
                   'Number of Charismatic/Pentecostal Christians in Millions in 2000'],
        'rows': [
            ['Africa', '.9', '126'], ['Asia', '0', '135'], ['Europe', '0', '37.6'],
            ['Latin America', '0', '141.4'], ['North America', '0', '79.6'], ['Oceania', '0', '4.3'],
        ],
    },
}
