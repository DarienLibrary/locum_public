import re
from django.utils.html import strip_tags
from html.parser import HTMLParser


class UniqueDictlist(dict):
    def __setitem__(self, key, value, listed=True):
        if listed:
            try:
                self[key]
            except KeyError:
                super(UniqueDictlist, self).__setitem__(key, [])
            if value not in self[key]:
                self[key].append(value)
        else:
            super(UniqueDictlist, self).__setitem__(key, value)


def convert_to_mods(marc):
    mod = UniqueDictlist()
    for content, grouping in mods_mapping.items():
        for mapping in grouping:
            for field in mapping['fields']:
                for marc_field in marc.get(field, []):
                    mod_field = {}
                    for subfield, mod_subfield in mapping['subfields'].items():
                        if marc_field.get(subfield):
                            k, v = clean_subfield(mod_subfield, marc_field[subfield])
                            if v:
                                mod_field[k] = v
                    if mod_field:
                        mod[content] = mod_field
    mod = extract_additinal_fields(mod)
    return mod

def extract_additinal_fields(mod):
    mod.__setitem__('provider', None, listed=False)
    mod.__setitem__('provider_id', None, listed=False)
    for field in mod.get('urls', []):
        if field.get('display') == 'excerpt':
            if field.get('url'):
                excerpt = {
                    'url': field['url'],
                    'format': field['url'].split('.')[-1]
                }
                mod['excerpts'] = excerpt
        if field.get('url'):
            url = field.get('url')
            provider_indicators = {
                'hoopla':
                    r'https://www\.hoopladigital\.com/title/(\d+)$',
                'bibliotheca':
                    r'^http://.*/library/darienlibrary-document_id-([\w]+)$',
                'overdrive':
                    r'^(\w{8}-\w{4}-\w{4}-\w{4}-\w{12})$',
            }
            for provider, exp in provider_indicators.items():
                m = re.search(exp, url)
                if m:
                    mod.__setitem__('provider', provider, listed=False)
                    if provider in ['bibliotheca', 'overdrive', 'hoopla']:
                        mod.__setitem__('provider_id', m.group(1), listed=False)
                    break
    return mod

def clean_subfield(k, v):
    parser = HTMLParser()
    punctuation = r'!"#$%&\'*+,-./:;<=>?@\^_`|~*$ \s'

    if k != 'url':
        m = re.match(r'^[{0}]*([^{0}].*[^{0}])[{0}]*$'.format(punctuation), v)
        if m:
            v = m.group(1)
        if k == 'note' or k == 'abstract':
            v = parser.unescape(strip_tags(v))
        else:
            v = v.lower()
        if k == 'code':
            if v in role_codes.keys():
                v = role_codes[v]
                k = 'role'
            else:
                v = None
        if k == 'name':
            names = [re.sub(r'[^\w\-\'\ ]', '', name)
                     for name in re.split('[,/]', v)]
            if not len(names):
                first = None
                last = None
            elif len(names) == 1:
                first = None
                last = names[0]
            elif len(names) > 1:
                first = names[1]
                last = names[0]
            v = {
                'first': first,
                'last': last
            }
        if k == 'isbn':
            res = re.match(r'\S*', v).group()
            isbn = re.sub(r'[^X0-9]', '', res)
            if len(isbn) == 10 and isbn10_check_digit(isbn[:-1]) == isbn[-1]:
                isbn = isbn_convert_10_to_13(isbn)
            if len(isbn) == 13 and isbn13_check_digit(isbn[:-1]) == isbn[-1]:
                v = isbn
            else:
                v = None
    return k, v


def consolidate_content(mods, content):
    consolodation = []
    for mod in mods:
        if mod.get(content):
            for field in mod[content]:
                if field not in consolodation:
                    consolodation.append(field)
            del mod[content]
    return consolodation


def get_longest_exemplar(mods, content, attribute):
    mods.sort(key=lambda bib_record: bib_record['precedence'])
    for mod in mods:
        if mod.get(content):
            return max(mod[content], key=lambda field: len(field[attribute]))


mods_mapping = {
    # 'authors': [{
    #     'fields': [100],
    #     'subfields': {
    #         'a': 'name',
    #         'e': 'role',
    #         '4': 'code',
    #     }
    # }],
    'names': [{
        'fields': [100, 110, 111, 700, 710, 711],
        'subfields': {
            'a': 'name',
            'e': 'role',
            '4': 'code',
        }
    }],
    'isbns': [{
        'fields': [20],
        'subfields': {
            'a': 'isbn',
        }
    }],
    'subjects': [{
        'fields': [600, 610, 611, 630, 648, 650, 651],
        'subfields': {
            'a': 'subject',
            'x': 'topic',
        }
    }],
    'genres': [{
        'fields': [600, 610, 611, 630, 648, 650, 651],
        'subfields': {
            'v': 'genre',
        }
    },
        {
        'fields': [655],
        'subfields': {
            'a': 'genre',
        }
    }],
    # 'titles': [{
    #     'fields': [210, 242, 245, 246],
    #     'subfields': {
    #         'a': 'title',
    #         'b': 'subtitle',
    #         'n': 'part_number',
    #         'p': 'part',
    #     }
    # }],
    'physical_description': [{
        'fields': [300],
        'subfields': {
            'a': 'extent',
            'b': 'other',
            'c': 'dimensions',
        }
    }],
    'notes': [{
        'fields': range(500, 520),
        'subfields': {
            'a': 'note',
        },
    },
        {
        'fields': range(521, 585),
        'subfields': {
            'a': 'note',
        }
    }],
    'abstracts': [{
        'fields': [520],
        'subfields': {
            'a': 'abstract',
        }
    }],
    'origin': [{
        'fields': [260, 262],
        'subfields': {
            'a': 'place',
            'b': 'publisher',
            'c': 'date_issued',
        }
    }],
    'edition': [{
        'fields': [250],
        'subfields': {
            'a': 'edition',
        }
    }],
    'urls': [{
        'fields': [856],
        'subfields': {
            'u': 'url',
            '3': 'display',
        },
    },
        {
        'fields': [37],
        'subfields': {
            'a': 'url',
        }
    }],
}

role_codes = {
    'abr': 'abridger',
    'acp': 'art copyist',
    'act': 'actor',
    'adi': 'art director',
    'adp': 'adapter',
    'aft': 'author of afterword, colophon, etc.',
    'anl': 'analyst',
    'anm': 'animator',
    'ann': 'annotator',
    'ant': 'bibliographic antecedent',
    'ape': 'appellee',
    'apl': 'appellant',
    'app': 'applicant',
    'aqt': 'author in quotations or text abstracts',
    'arc': 'architect',
    'ard': 'artistic director',
    'arr': 'arranger',
    'art': 'artist',
    'asg': 'assignee',
    'asn': 'associated name',
    'ato': 'autographer',
    'att': 'attributed name',
    'auc': 'auctioneer',
    'aud': 'author of dialog',
    'aui': 'author of introduction, etc.',
    'aus': 'screenwriter',
    'aut': 'author',
    'bdd': 'binding designer',
    'bjd': 'bookjacket designer',
    'bkd': 'book designer',
    'bkp': 'book producer',
    'blw': 'blurb writer',
    'bnd': 'binder',
    'bpd': 'bookplate designer',
    'brd': 'broadcaster',
    'brl': 'braille embosser',
    'bsl': 'bookseller',
    'cas': 'caster',
    'ccp': 'conceptor',
    'chr': 'choreographer',
    'clb': 'collaborator',
    'cli': 'client',
    'cll': 'calligrapher',
    'clr': 'colorist',
    'clt': 'collotyper',
    'cmm': 'commentator',
    'cmp': 'composer',
    'cmt': 'compositor',
    'cnd': 'conductor',
    'cng': 'cinematographer',
    'cns': 'censor',
    'coe': 'contestant-appellee',
    'col': 'collector',
    'com': 'compiler',
    'con': 'conservator',
    'cor': 'collection registrar',
    'cos': 'contestant',
    'cot': 'contestant-appellant',
    'cou': 'court governed',
    'cov': 'cover designer',
    'cpc': 'copyright claimant',
    'cpe': 'complainant-appellee',
    'cph': 'copyright holder',
    'cpl': 'complainant',
    'cpt': 'complainant-appellant',
    'cre': 'creator',
    'crp': 'correspondent',
    'crr': 'corrector',
    'crt': 'court reporter',
    'csl': 'consultant',
    'csp': 'consultant to a project',
    'cst': 'costume designer',
    'ctb': 'contributor',
    'cte': 'contestee-appellee',
    'ctg': 'cartographer',
    'ctr': 'contractor',
    'cts': 'contestee',
    'ctt': 'contestee-appellant',
    'cur': 'curator',
    'cwt': 'commentator for written text',
    'dbp': 'distribution place',
    'dfd': 'defendant',
    'dfe': 'defendant-appellee',
    'dft': 'defendant-appellant',
    'dgg': 'degree granting institution',
    'dgs': 'degree supervisor',
    'dis': 'dissertant',
    'dln': 'delineator',
    'dnc': 'dancer',
    'dnr': 'donor',
    'dpc': 'depicted',
    'dpt': 'depositor',
    'drm': 'draftsman',
    'drt': 'director',
    'dsr': 'designer',
    'dst': 'distributor',
    'dtc': 'data contributor',
    'dte': 'dedicatee',
    'dtm': 'data manager',
    'dto': 'dedicator',
    'dub': 'dubious author',
    'edc': 'editor of compilation',
    'edm': 'editor of moving image work',
    'edt': 'editor',
    'egr': 'engraver',
    'elg': 'electrician',
    'elt': 'electrotyper',
    'eng': 'engineer',
    'enj': 'enacting jurisdiction',
    'etr': 'etcher',
    'evp': 'event place',
    'exp': 'expert',
    'fac': 'facsimilist',
    'fds': 'film distributor',
    'fld': 'field director',
    'flm': 'film editor',
    'fmd': 'film director',
    'fmk': 'filmmaker',
    'fmo': 'former owner',
    'fmp': 'film producer',
    'fnd': 'funder',
    'fpy': 'first party',
    'frg': 'forger',
    'gis': 'geographic information specialist',
    'grt': '   graphic technician',
    'his': 'host institution',
    'hnr': 'honoree',
    'hst': 'host',
    'ill': 'illustrator',
    'ilu': 'illuminator',
    'ins': 'inscriber',
    'inv': 'inventor',
    'isb': 'issuing body',
    'itr': 'instrumentalist',
    'ive': 'interviewee',
    'ivr': 'interviewer',
    'jud': 'judge',
    'jug': 'jurisdiction governed',
    'lbr': 'laboratory',
    'lbt': 'librettist',
    'ldr': 'laboratory director',
    'led': 'lead',
    'lee': 'libelee-appellee',
    'lel': 'libelee',
    'len': 'lender',
    'let': 'libelee-appellant',
    'lgd': 'lighting designer',
    'lie': 'libelant-appellee',
    'lil': 'libelant',
    'lit': 'libelant-appellant',
    'lsa': 'landscape architect',
    'lse': 'licensee',
    'lso': 'licensor',
    'ltg': 'lithographer',
    'lyr': 'lyricist',
    'mcp': 'music copyist',
    'mdc': 'metadata contact',
    'med': 'medium',
    'mfp': 'manufacture place',
    'mfr': 'manufacturer',
    'mod': 'moderator',
    'mon': 'monitor',
    'mrb': 'marbler',
    'mrk': 'markup editor',
    'msd': 'musical director',
    'mte': 'metal-engraver',
    'mtk': 'minute taker',
    'mus': 'musician',
    'nrt': 'narrator',
    'opn': 'opponent',
    'org': 'originator',
    'orm': 'organizer',
    'osp': 'onscreen presenter',
    'oth': 'other',
    'own': 'owner',
    'pan': 'panelist',
    'pat': 'patron',
    'pbd': 'publishing director',
    'pbl': 'publisher',
    'pdr': 'project director',
    'pfr': 'proofreader',
    'pht': 'photographer',
    'plt': 'platemaker',
    'pma': 'permitting agency',
    'pmn': 'production manager',
    'pop': 'printer of plates',
    'ppm': 'papermaker',
    'ppt': 'puppeteer',
    'pra': 'praeses',
    'prc': 'process contact',
    'prd': 'production personnel',
    'pre': 'presenter',
    'prf': 'performer',
    'prg': 'programmer',
    'prm': 'printmaker',
    'prn': 'production company',
    'pro': 'producer',
    'prp': 'production place',
    'prs': 'production designer',
    'prt': 'printer',
    'prv': 'provider',
    'pta': 'patent applicant',
    'pte': 'plaintiff-appellee',
    'ptf': 'plaintiff',
    'pth': 'patent holder',
    'ptt': 'plaintiff-appellant',
    'pup': 'publication place',
    'rbr': 'rubricator',
    'rcd': 'recordist',
    'rce': 'recording engineer',
    'rcp': 'addressee',
    'rdd': 'radio director',
    'red': 'redaktor',
    'ren': 'renderer',
    'res': 'researcher',
    'rev': 'reviewer',
    'rpc': 'radio producer',
    'rps': 'repository',
    'rpt': 'reporter',
    'rpy': 'responsible party',
    'rse': 'respondent-appellee',
    'rsg': 'restager',
    'rsp': 'respondent',
    'rsr': 'restorationist',
    'rst': 'respondent-appellant',
    'rth': 'research team head',
    'rtm': 'research team member',
    'sad': 'scientific advisor',
    'sce': 'scenarist',
    'scl': 'sculptor',
    'scr': 'scribe',
    'sds': 'sound designer',
    'sec': 'secretary',
    'sgd': 'stage director',
    'sgn': 'signer',
    'sht': 'supporting host',
    'sll': 'seller',
    'sng': 'singer',
    'spk': 'speaker',
    'spn': 'sponsor',
    'spy': 'second party',
    'srv': 'surveyor',
    'std': 'set designer',
    'stg': 'setting',
    'stl': 'storyteller',
    'stm': 'stage manager',
    'stn': 'standards body',
    'str': 'stereotyper',
    'tcd': 'technical director',
    'tch': 'teacher',
    'ths': 'thesis advisor',
    'tld': 'television director',
    'tlp': 'television producer',
    'trc': 'transcriber',
    'trl': 'translator',
    'tyd': 'type designer',
    'tyg': 'typographer',
    'uvp': 'university place',
    'vac': 'voice actor',
    'vdg': 'videographer',
    'voc': 'vocalist',
    'wac': 'writer of added commentary',
    'wal': 'writer of added lyrics',
    'wam': 'writer of accompanying material',
    'wat': 'writer of added text',
    'wdc': 'woodcutter',
    'wde': 'wood engraver',
    'win': 'writer of introduction',
    'wit': 'witness',
    'wpr': 'writer of preface',
    'wst': 'writer of supplementary textual content'
}

def isbn10_check_digit(isbn):
    assert len(isbn) == 9
    sum = 0
    for i in range(len(isbn)):
        c = int(isbn[i])
        w = i + 1
        sum += w * c
    r = sum % 11
    if r == 10:
        return 'X'
    else:
        return str(r)


def isbn13_check_digit(isbn):
    assert len(isbn) == 12
    sum = 0
    for i in range(len(isbn)):
        c = int(isbn[i])
        if i % 2:
            w = 3
        else:
            w = 1
        sum += w * c
    r = 10 - (sum % 10)
    if r == 10:
        return '0'
    else:
        return str(r)


def isbn_convert_10_to_13(isbn):
    assert len(isbn) == 10
    prefix = '978' + isbn[:-1]
    check = isbn13_check_digit(prefix)
    return prefix + check