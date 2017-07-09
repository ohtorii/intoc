# -*- coding: utf-8 -*-

import os
import re
import sys

def file2list(filepath):
    ret = []
    with open(filepath, 'r') as f:
        ret = [line.rstrip('\n') for line in f.readlines()]
    return ret

def list2file(filepath, ls):
    with open(filepath, 'w') as f:
        f.writelines(['%s\n' % line for line in ls] )

def terminalencoding2utf8(bytestr):
    return bytestr.decode(sys.stdin.encoding).encode('utf8')

def parse_arguments():
    import argparse

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument('-i', '--input', default=None, required=True,
        help='A input filename.')

    parser.add_argument('--indent-depth', default=2, type=int,
        help='The number of spaces per a nest in TOC.')
    parser.add_argument('--parse-depth', default=-1, type=int,
        help='The depth of the TOC list nesting. If minus then no limit depth.')

    parser.add_argument('--edit', default=False, action='store_true',
        help='If given then insert TOC to the file from "--input".')
    parser.add_argument('--edit-target', default='<!-- TOC',
        help='A insertion destination label when --edit given. NOT CASE-SENSITIVE.')

    parser.add_argument('--edit-debug', default=False, action='store_true',
        help=argparse.SUPPRESS)
    parser.add_argument('--debug', default=False, action='store_true',
        help=argparse.SUPPRESS)

    args = parser.parse_args()
    return args

def line2sectioninfo(line):
    sectionlevel = 0
    body = ''

    # # level1
    # ## level2
    # ### level3
    # ###... level...
    #
    # ## level2
    #   ^^^^^^^
    #   body
    while True:
        cnt = sectionlevel+1
        comparer = '#'*cnt
        if line[0:cnt]==comparer:
            sectionlevel += 1
            body = line[sectionlevel:]
            continue
        break

    return sectionlevel, body

def sectionname2anchor(sectionname, duplicator):
    ret = sectionname

    ret = ret.lower()
    ret = ret.replace(' ', '-')

    # remove ascii marks excxept hypen and underscore.
    remove_targets = '[!"#$%&\'\\(\\)\\*\\+,\\./:;<=>?@\\[\\\\\\]\\^`\\{\\|\\}~]'
    ret = re.sub(remove_targets, '', ret)

    # remove Japanese marks
    remove_targets = u'[、。，．・：；？！゛゜´｀¨＾￣＿ヽヾゝゞ〃仝々〆〇ー―‐／＼～∥｜…‥‘’“”（）〔〕［］｛｝〈〉《》「」『』【】＋－±×÷＝≠＜＞≦≧∞∴♂♀°′″℃￥＄￠￡％＃＆＊＠§☆★○●◎◇◆□■△▲▽▼※〒→←↑↓〓∈∋⊆⊇⊂⊃∪∩∧∨￢⇒⇔∀∃∠⊥⌒∂∇≡≒≪≫√∽∝∵∫∬Å‰♯♭♪ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩαβγδεζηθικλμνξοπρστυφχψωАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюя─│┌┐┘└├┬┤┴┼━┃┏┓┛┗┣┳┫┻╋┠┯┨┷┿┝┰┥┸╂｡｢｣､･ｦｧｨｩｪｫｬｭｮｯｰｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝﾞﾟ①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ㍉㌔㌢㍍㌘㌧㌃㌶㍑㍗㌍㌦㌣㌫㍊㌻㎜㎝㎞㎎㎏㏄㎡　㍻〝〟№㏍℡㊤㊥㊦㊧㊨㈱㈲㈹㍾㍽㍼≒≡∫∮∑√⊥∠∟⊿∵∩∪]'#deleter = u'[#]'
    uret = re.sub(remove_targets, u'', ret.decode('utf-8'))

    # In GFM, do numbering if there is a duplicated anchor name.
    #
    # Ex.
    #   # section1
    #   # section1
    #   # section1
    #       VVV
    #   href="#section1"
    #   href="#section1-1"
    #   href="#section1-2"
    ret = uret.encode('utf8')
    dup_count = duplicator.add(ret)
    if dup_count>0:
        ret = ret + '-{0}'.format(dup_count)

    return ret

def is_edit_target_line(line, edit_target):
    return line.strip().lower().find(edit_target.lower())!=-1

def get_toc_range(lines, edit_target):
    """ @return (p_start, p_end) If no toc exists then p_end returns None. """
    p_start = None
    p_end = None
    for i,line in enumerate(lines):
        if p_start==None:
            if is_edit_target_line(line, edit_target):
                p_start = i+1
            continue

        if line.lstrip()[0:1]=='-':
            p_end = i
            continue
        else:
            if p_end!=None:
                p_end += 1
        break

    return p_start, p_end

class Duplicator:
    def __init__(self):
        self._d = {}

    def add(self, k):
        try:
            self._d[k]
        except KeyError:
            self._d[k] = 1
            return 0

        ret = self._d[k]
        self._d[k] += 1
        return ret

class SectionLine:
    def __init__(self, level, body):
        self._lv = level
        self._body = body
        self._duplicator = Duplicator()

    def set_indent_depth(self, num):
        self._indent_depth = num

    @property
    def tocline(self):
        normed_body = self._body.strip()

        indent = ' '*((self._lv-1)*self._indent_depth)
        mark   = '-'
        text   = normed_body
        anchor = sectionname2anchor(normed_body, self._duplicator)

        ret = '{0}{1} [{2}](#{3})'.format(
            indent,
            mark,
            text,
            anchor
        )

        return ret

    def __str__(self):
        return 'LV{0} [{1}]'.format(self._lv, self._body)

if __name__ == "__main__":
    MYDIR = os.path.abspath(os.path.dirname(__file__))

    args = parse_arguments()
    infile = os.path.join(MYDIR, args.input)
    indent_depth = args.indent_depth
    parse_depth = args.parse_depth
    use_edit = args.edit
    edit_target = args.edit_target

    lines = file2list(infile)
    toclines = []
    edit_target_pos = None
    is_in_hilight_area = False
    for i,line in enumerate(lines):
        if len(line)==0:
            continue

        if line[:3]=='```':
            if is_in_hilight_area==False:
                is_in_hilight_area = True
                continue
            is_in_hilight_area = False
            continue
        if is_in_hilight_area==True:
            continue

        if use_edit and edit_target_pos==None and is_edit_target_line(line, edit_target):
            edit_target_pos = i
            if args.debug:
                print 'edit target pos: {0}'.format(edit_target_pos)
            continue

        sectionlevel, body = line2sectioninfo(line)
        if sectionlevel==0:
            continue

        if parse_depth>=0 and sectionlevel>=parse_depth+1:
            continue
        sl = SectionLine(sectionlevel, body)
        sl.set_indent_depth(indent_depth)
        toclines.append(sl.tocline)

    if edit_target_pos==None:
        for i,line in enumerate(toclines):
            print line
        exit(0)
    if args.edit_debug:
        print 'Edit Target    : {0}'.format(edit_target)
        print 'Edit Target Pos: {0}'.format(edit_target_pos)

    outlines = lines[:edit_target_pos+1]
    outlines.extend(toclines)

    # If old TOC exists, must skip it.
    # Then, old one is not merged.
    startpos, endpos = get_toc_range(lines, edit_target)
    skippos = 0
    if startpos and endpos:
        if args.debug:
            print 'start, end:({0}, {1})'.format(startpos, endpos)
        skippos = endpos - startpos

    outlines.extend(lines[edit_target_pos+1+skippos:])
    writee_filename = infile
    if args.edit_debug:
        writee_filename += '.debug'
    list2file(writee_filename, outlines)