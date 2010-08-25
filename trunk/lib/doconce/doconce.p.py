#!/usr/bin/env python
'''

# #include "docstrings/docstring.dst.txt"

'''
__author__ = 'Hans Petter Langtangen <hpl@simula.no>'
__version__ = 0.7

import re, os, sys, shutil, commands, pprint

if len(sys.argv) >= 4 and sys.argv[3] == 'debug':
    debug_flag = True
    del sys.argv[3]
else:
    debug_flag = False
if debug_flag:
    _log_filename = '_doconce_debugging.log'
    _log = open(_log_filename,'w')
    _log.write("""
This is a log file for the doconce2format script.
Debugging is turned on by a 3rd command-line argument 'debug'
to doconce2format. Without that command-line argument,
this file is not produced.

""")
    

from common import *
import html, latex, rst, sphinx, st, epytext, plaintext, wiki
for module in html, latex, rst, sphinx, st, epytext, plaintext, wiki:
    #print 'calling define function in', module.__name__
    module.define(FILENAME_EXTENSION,
                  BLANKLINE,
                  INLINE_TAGS_SUBST,
                  CODE,
                  LIST,
                  ARGLIST,
                  TABLE,
                  FIGURE_EXT,
                  CROSS_REFS,
                  INTRO,
                  OUTRO)

def supported_format_names():
    return 'HTML', 'LaTeX', 'rst', 'sphinx', 'st', 'epytext', 'plain', 'wiki'

#----------------------------------------------------------------------------
# Translators: (no, do not include! use import! - as shown above)
# include "common.py"
# include "html.py"
# include "rst.py"
# include "st.py"
# include "plaintext.py"
# include "latex.py"
#----------------------------------------------------------------------------

def debug(out):
    if debug_flag:
        #print out
        global _log
        _log = open('_doconce_debugging.log','a')
        _log.write(out + '\n')
        _log.close()

def insert_code_from_file(filestr, format):
    lines = filestr.splitlines()
    inside_verbatim = False
    for i in range(len(lines)):
        line = lines[i]
        debug('Read ' + line)
        line = line.lstrip()

        # detect if we are inside verbatim blocks:
        if line.startswith('!bc'):
            inside_verbatim = True
        if line.startswith('!ec'):
            inside_verbatim = False
        if inside_verbatim:
            continue
            
        if line.startswith('@@@CODE'):
            debug('Found verbatim copy (line %d): %s' % (i+1, line))
            try:
                filename = line.split()[1]
            except IndexError:
                raise SyntaxError, \
                      'Syntax error: missing filename in line\n  %s' % line
            try:
                f = open(filename, 'r')
            except IOError, e:
                print 'Could not open the file %s used in @@@CODE instruction' % filename
                print e
                sys.exit(1)
            index = line.find('fromto:')
            if index == -1:
                # no from/to regex, read the whole file:
                complete_file = True
                code = f.read()
                debug('copy the file "%s" into a verbatim block\n' % filename)
               
            else:
                complete_file = False
                patterns = line[index+7:]
                try:
                    from_, to_ = patterns.split('@')
                except:
                    raise SyntaxError, \
                    'Syntax error: missing @ in regex in line\n  %s' % line
                cfrom = re.compile(from_)
                cto = re.compile(to_)
                codelines = []
                copy = False
                for codeline in f:
                    m = cfrom.search(codeline)
                    if m:
                        copy = True
                    m = cto.search(codeline)
                    if m:
                        copy = False
                        # now the to line is not included
                    if copy:
                        debug('copy from "%s" the line\n%s' % \
                              (filename, codeline))
                        codelines.append(codeline)
                code = ''.join(codelines)

            if format == 'LaTeX':
                # insert a cod or pro directive for ptex2tex:
                if complete_file:
                    code = "!bc pro\n%s\n!ec" % code
                else:
                    code = "!bc cod\n%s\n!ec" % code
            else:
                code = "!bc\n%s\n!ec" % code
            lines[i] = code
    
    filestr = '\n'.join(lines)
    return filestr


                
def parse_keyword(keyword, format):
    """
    Parse a keyword for a description list when the keyword may
    represent information about an argument to a function or a
    variable in a program::

      - argument x: x coordinate (float).
      - keyword argument tolerance: error tolerance (float).
      - return: corresponding y coordinate (float).
    """
    keyword = keyword.strip()
    if keyword[-1] == ':':      # strip off trailing colon
        keyword = keyword[:-1]

    typical_words = ('argument', 'keyword argument', 'return', 'variable')
    parse = False
    for w in typical_words:
        if w in keyword:    # part of function argument++ explanation?
            parse = True
            break
    if not parse:
        # no need to parse for variable type and name
        if format == 'epytext':
            # epytext does not have description lists, add a "bullet" -
            keyword = '- ' + keyword
        return keyword

    # parse:
    if 'return' in keyword:
        type = 'return'
        varname = None
        type = ARGLIST[format][type]  # formatting of keyword type
        return type
    else:
        words = keyword.split()
        varname = words[-1]
        type = ' '.join(words[:-1])
        if type == 'argument':
            type = 'parameter'
        elif type == 'keyword argument':
            type = 'keyword'
        elif type == 'instance variable':
            type = 'instance variable'
        elif type == 'class variable':
            type = 'class variable'
        elif type == 'module variable':
            type = 'module variable'
        else:
            return keyword # probably not a list of variable explanations
        # construct "type varname" string, where varname is typeset in
        # inline verbatim:
        pattern = r'(?P<begin>^)(?P<subst>%s)(?P<end>$)' % varname
        #varname = re.sub(pattern, INLINE_TAGS_SUBST[format]['verbatim'], varname)
        keyword = ARGLIST[format][type] + ' ' + varname
        return keyword


def typeset_tables(filestr, format):
    """
    Translate tables with pipes and dashes to a list of
    row-column values. Horizontal rules become a row
    ['horizontal rule'] in the list.
    The list is easily translated to various output formats 
    by other modules.
    """
    from StringIO import StringIO
    result = StringIO()
    table = []
    inside_table = False
    for line in filestr.splitlines():
        # horisontal table rule?
        lin = line.lstrip()
        if lin.startswith('|--') and lin.endswith('-|'):
            table.append(['horizontal rule'])
            continue  # continue with next line
        if lin.startswith('|') and not lin.startswith('|--'):  
            # row in table:
            if not inside_table:
                inside_table = True
            columns = line.strip().split('|')
            # remove empty columns and extra white space:
            #columns = [c.strip() for c in columns if c]
            columns = [c.strip() for c in columns if c.strip()]
            table.append(columns)
        else:
            if inside_table:
                # not a table line anymore, but we were just inside a table
                # so the table is ended
                inside_table = False
                result.write(TABLE[format](table))   # typeset table
            else:
                result.write(line + '\n')
    return result.getvalue()
            
def typeset_lists(filestr, format, debug_info=[]):
    """
    Go through filestr and parse all lists and typeset them correctly.
    This function must be called after all (verbatim) code and tex blocks
    have been removed from the file.
    This function also treats comment lines and blank lines.
    """
    debug('*** List typesetting phase + comments and blank lines ***')
    from StringIO import StringIO
    result = StringIO()
    lastindent = 0
    lists = []
    inside_description_environment = False
    lines = filestr.splitlines()
    lastline = lines[0]
    # for debugging only:
    _code_block_no = 0; _tex_block_no = 0    

    for line in lines:
        
        debug('\n------------------------\nsource line=[%s]' % line)
        # do a syntax check:
        for tag in INLINE_TAGS_BUGS:
            bug = INLINE_TAGS_BUGS[tag]
            if bug:
                m = re.search(bug[0], line)
                if m:
                    print '>>> Syntax ERROR? "%s"\n    %s!' % \
                          (m.group(0), bug[1])
                
        if not line or line.isspace():  # blank line?
            result.write(BLANKLINE[format])
            debug('  > This is a blank line')
            lastline = line
            continue

        if line.startswith('#'):

            # first do some debug output:
            if line.startswith('#!!CODE') and len(debug_info) >= 1:
                result.write(line + '\n')
                debug('  > Here is a code block:\n%s\n--------' % \
                      debug_info[0][_code_block_no])
                _code_block_no += 1
            elif line.startswith('#!!TEX') and len(debug_info) >= 2:
                result.write(line + '\n')
                debug('  > Here is a latex block:\n%s\n--------' % \
                      debug_info[1][_tex_block_no])
                _tex_block_no += 1
                
            else:
                debug('  > This is just a comment line')
                # the comment can be propagated to some formats
                # (rst, LaTeX, HTML):
                line = line[1:]  # strip off initial #
                if 'comment' in INLINE_TAGS_SUBST[format]:
                    comment_action = INLINE_TAGS_SUBST[format]['comment']
                    if isinstance(comment_action, str):
                        new_comment = comment_action % line.strip()
                    elif callable(comment_action):
                        new_comment = comment_action(line.strip())
                    result.write(new_comment + '\n')

            lastline = line
            continue
            
        # structure of a line:
        linescan = re.compile(
            r"(?P<indent> *(?P<listtype>[*o-] )? *)" +
            r"(?P<keyword>[^:]+?:)?(?P<text>.*)\s?")

        m = linescan.match(line)
        indent = len(m.group('indent'))
        listtype = m.group('listtype')
        if listtype:
            listtype = listtype.strip()
            listtype = LIST_SYMBOL[listtype]
        keyword = m.group('keyword')
        text = m.group('text')
        debug('  > indent=%d (previous indent=%d)' % (indent, lastindent))

        # new (sub)section makes end of any indent (we could demand
        # (sub)sections to start in column 1, but we have later relaxed
        # such a requirement; it is easier to just test for ___ and
        # set indent=0 here):
        if line.lstrip().startswith('___'):
            indent = 0


        if indent > lastindent and listtype:
            debug('  > This is a new list of type "%s"' % listtype)
            # begin a new list or sublist:
            lists.append({'listtype': listtype, 'indent': indent})
            result.write(LIST[format][listtype]['begin'])
            lastindent = indent
            if listtype == 'enumerate':
                enumerate_counter = 0

        if indent < lastindent:
            # end a list or sublist, nest back all list
            # environments on the lists stack:
            while lists and lists[-1]['indent'] > indent:
                 debug('  > This is the end of a %s list' % \
                       lists[-1]['listtype'])
                 result.write(LIST[format][lists[-1]['listtype']]['end'])
                 del lists[-1]
            lastindent = indent

        if indent == lastindent:
            debug('  > This line belongs to the previous block since it has '\
                  'the same indent (%d blanks)' % indent)

        if listtype:
            # need blank line between items and last line was not blank?
            if not (lastline.isspace() or not lastline):
                result.write(LIST[format]['separator'])

            # first write the list item identifier:
            itemformat = LIST[format][listtype]['item']
            item = itemformat
            if listtype == 'enumerate':
                debug('  > This is an item in an enumerate list')
                enumerate_counter += 1
                if '%d' in itemformat:
                    item = itemformat % enumerate_counter
                # indent here counts with '3. ':
                result.write(' '*(indent - 2 - enumerate_counter//10 - 1))  
                result.write(item + ' ')
            elif listtype == 'description':
                if '%s' in itemformat:
                    if keyword:
                        keyword = parse_keyword(keyword, format) + ':'
                        item = itemformat % keyword + ' '
                        debug('  > This is an item in a description list '\
                              'with keyword "%s"' % keyword)
                        keyword = '' # to avoid adding keyword up in
                        # below (ugly hack, but easy linescan parsing...)
                result.write(' '*(indent-2))  # indent here counts with '* '
                result.write(item)
                if not (text.isspace() or not text):
                    result.write('\n' + ' '*(indent-1))
            else:
                debug('  > This is an item in a bullet list')
                result.write(' '*(indent-2))  # indent here counts with '* '
                result.write(item + ' ')

        else:
            debug('  > This line is not part of a list environment...')
            # should check emph, verbatim, etc., syntax check and common errors
            result.write(' '*indent)      # ordinary line

        # this is not a list line and therefore we must
        # add keyword + text because these two items make up the
        # line if a : present
        if keyword:
            text = keyword + text
        debug('text=[%s]' % text)
        result.write(text + '\n')
        lastindent = indent
        lastline = line

    # end lists if any are left:
    while lists:
        debug('  > This is the end of a %s list' % lists[-1]['listtype'])
        result.write(LIST[format][lists[-1]['listtype']]['end'])
        del lists[-1]
    
    return result.getvalue()


def handle_figures(filestr, format):
    if not format in FIGURE_EXT:
        # no special handling of figures:
        return filestr
    
    pattern = INLINE_TAGS['figure']
    c = re.compile(pattern, re.MULTILINE)

    # first check if the figure files are of right type:
    files = [filename for filename, options, caption in c.findall(filestr)]
    if type(FIGURE_EXT[format]) is str:
        extensions = [FIGURE_EXT[format]]
    else:
        extensions = FIGURE_EXT[format]  # is list
    for f in files:
        basepath, ext = os.path.splitext(f)
        if not ext in extensions:
            print 'Figure', f, 'must have extension(s)', extensions
            # use convert from ImageMagick:
            for e in extensions:
                newfile = basepath + e
                if not os.path.isfile(newfile):
                    # ext might be empty, in that case we cannot convert
                    # anything:
                    if ext:
                        failure = os.system('convert %s %s' % (f, newfile))
                        if not failure:
                            print '....ok, converted %s to %s' % (f, newfile)
                            filestr = filestr.replace(f, newfile)
                            break  # jump out of inner e loop
                else:  # right file exists:
                    print '....ok, ', newfile, 'exists'
                    filestr = filestr.replace(f, newfile)
                    break
                

    # replace FIGURE... by format specific syntax:
    try:
        replacement = INLINE_TAGS_SUBST[format]['figure']
        filestr = c.sub(replacement, filestr)
    except KeyError:
        pass
    return filestr
    

def cross_referencing(filestr, format):
    # 0. syntax check (outside !bt/!et environments there should only
    # be ref and label *without* the latex-ish backslash
    label_matches = re.findall(r'\\label\{', filestr)
    if label_matches:
        print r'Syntax error: found \label{...} (should be no backslash!)'
    ref_matches = re.findall(r'\\ref\{', filestr)
    if ref_matches:
        print r'Syntax error: found \ref{...} (should be no backslash!)'
        
    # 1. find all section/chapter titles and corresponding labels
    section_pattern = r'(_+|=+)([A-Za-z !.,;0-9]+)(_+|=+)\s*label\{(.+?)\}'
    section_pattern = r'(_{3,7}|={3,7})(.+?)(_{3,7}|={3,7})\s*label\{(.+?)\}'
    m = re.findall(section_pattern, filestr)
    #import pprint
    #pprint.pprint(m)
    section_label2title = {}
    for dummy1, title, dummy2, label in m:
        section_label2title[label] = title.strip()
    #pprint.pprint(section_label2title)

    # 2. perform format-specific editing of ref{...} and label{...}
    filestr = CROSS_REFS[format](section_label2title, format, filestr)
    return filestr

        
def inline_tag_subst(filestr, format):
    debug('\n*** Inline tags substitution phase ***')
    ordered_tags = (
        'title', 'author', 'date', #'figure',
        # important to do section, subsection, etc. BEFORE paragraph and bold:
        'section', 'subsection', 'subsubsection',
        'emphasize', 'math2', 'math', 'bold', 'verbatim',
        'citation',
        'paragraph',  # after bold and emphasize
        'plainURL', 'linkURL', 
        )
    for tag in ordered_tags:
        debug('Working with tag "%s"' % tag)
        tag_pattern = INLINE_TAGS[tag]
        c = re.compile(tag_pattern, re.MULTILINE)
        try:
            replacement = INLINE_TAGS_SUBST[format][tag]
        except KeyError:
            continue  # just ignore missing tags in current format
        if replacement is None:
            continue  # no substitution
        
        if isinstance(replacement, basestring):
            # first some info for debug output:
            findlist = c.findall(filestr)
            occurences = len(findlist)
            findlist = pprint.pformat(findlist)
            if occurences > 0:
                debug('Found %d occurences of "%s":\n%s' % (occurences, tag, findlist))
                debug('%s is to be replaced using %s' % (tag, replacement))
            
            filestr = c.sub(replacement, filestr)
        elif callable(replacement):
            # treat line by line because replacement string depends
            # on the match object for each occurence
            # (this is mainly for headlines in rst format)
            lines = filestr.splitlines()
            occurences = 0
            for i in range(len(lines)):
                m = re.search(tag_pattern, lines[i])
                if m:
                    replacement_str = replacement(m)
                    lines[i] = re.sub(tag_pattern, replacement_str, lines[i])
                    occurences += 1
            filestr = '\n'.join(lines)

        else:
            raise ValueError, 'replacement is of type %s' % type(replacement)
        if occurences > 0:
            debug('\n**** The file after %d "%s" substitutions ***\n%s\n%s\n\n' % \
                  (occurences, tag, filestr, ':'*80))
    return filestr
        

    
def doconce2format(in_filename, format, out_filename):
    """
    Perform the transformation of a doconce file, stored in in_filename,
    to a given format (HTML, LaTeX, etc.), written to out_filename.
    This is the "main" function in the module.
    """
    print '\n2nd step: run doconce2format on preprocessed file', in_filename
    f = open(in_filename, 'r')
    #import codecs; f = codecs.open(in_filename, 'r', 'utf-8')
    filestr = f.read()
    f.close()

    # hack to fix a bug with !ec at the end of files, which is not
    # correctly substituted by '' in rst, sphinx, st, epytext, plain
    # (the fix is to add "enough" blank lines)
    if format in ('rst', 'sphinx', 'st', 'epytext', 'plain'):
        filestr = filestr.rstrip()
        if filestr.endswith('!ec'):
            filestr += '\n'*10

    # 0. step: check if ^#?TITLE: is present, and if so, header and footer
    # are to be included (later below):
    if re.search(r'^#?TITLE:', filestr, re.MULTILINE):
        has_title = True
    else:
        has_title = False
        
    # 1. step: insert verbatim code from other (source code) files:
    # (if the format is LaTeX, we could let ptex2tex do this, but
    # the CODE start@stop specifications may contain uderscores and
    # asterix, which will be replaced later and hence destroyed)
    #if format != 'LaTeX':
    filestr = insert_code_from_file(filestr, format)
    debug('%s\n**** The file after inserting @@@CODE:\n\n%s\n\n' % \
          ('*'*80, filestr))

    # 2. step: remove all verbatim and math blocks
    
    filestr, code_blocks, tex_blocks = remove_code_and_tex(filestr)
    # for HTML we should make replacements of < ... > in code_blocks,
    # and handle latin-1 characters
    if format == 'HTML':  # fix
        from urllib import quote
        for i in range(len(code_blocks)):
            code_blocks[i] = re.sub(r'(<)([^>]*?)(>)',
                                    '&lt;\g<2>&gt;', code_blocks[i])
        # this transformation is easier done with encoding="utf-8"
        # in the first line in the HTML file:
        filestr = html.latin2html(filestr)
        
    debug('%s\n**** The file after removal of code/tex blocks:\n\n%s\n\n' % \
          ('*'*80, filestr))

    # 3. step: deal with cross referencing (must occur before other format subst)
    filestr = cross_referencing(filestr, format)
    
    debug('%s\n**** The file after handling ref and label cross referencing\n\n%s\n\n' % ('*'*80, filestr))


    # 4. step: deal with lists
    filestr = typeset_lists(filestr, format,
                            debug_info=[code_blocks, tex_blocks])
    debug('%s\n**** The file after typesetting of list:\n\n%s\n\n' % \
          ('*'*80, filestr))

    # 5. step: deal with tables
    filestr = typeset_tables(filestr, format)
    debug('%s\n**** The file after typesetting of tables:\n\n%s\n\n' % \
          ('*'*80, filestr))

    # 6. step: deal with figures
    filestr = handle_figures(filestr, format)

    # 7. step: do substitutions:
    filestr = inline_tag_subst(filestr, format)

    debug('%s\n**** The file after all inline substitutions:\n\n%s\n\n' % ('*'*80, filestr))

    # 8. step: substitute latex-style newcommands in filestr and tex_blocks
    # (not in code_blocks)
    from expand_newcommands import expand_newcommands
    if format != 'LaTeX':
        newcommand_files = ['newcommands_replace.tex']
        if format == 'sphinx':  # replace all newcommands in sphinx
            newcommand_files.extend(['newcommands.tex', 'newcommands_keep.tex'])
        print 'expanding newcommands in', ', '.join(newcommand_files)
        filestr = expand_newcommands(newcommand_files, filestr)
        for i in range(len(tex_blocks)):
            tex_blocks[i] = expand_newcommands(newcommand_files, tex_blocks[i])

    # 9. step: insert verbatim and math code blocks again:
    filestr = insert_code_and_tex(filestr, code_blocks, tex_blocks, format)
    filestr += '\n'
    
    # substitute code and tex environments:
    filestr = CODE[format](filestr, format)
    debug('%s\n**** The file after inserting tex/code blocks:\n\n%s\n\n' % \
          ('*'*80, filestr))

    if has_title:
        if format in INTRO:
            filestr = INTRO[format] + filestr
        if format in OUTRO:
            filestr = filestr + OUTRO[format]
        
    f = open(out_filename, 'w')
    f.write(filestr)
    f.close()


def preprocess(filename, format, preprocess_options=''):
    """
    Run the preprocess script on filename and return the name
    of the resulting file. In the call, all sys.argv[3:] arguments
    are given as preprocess_options. In addition, -DFORMAT=format is
    always defined.
    """
    resultfile = '__tmp.do.txt'
    print '1st step: run preprocessor on', filename
    cmd = 'preprocess -DFORMAT=%s %s %s > %s' % \
          (format, preprocess_options, filename, resultfile)
    print '>>>>', cmd
    failure, outtext = commands.getstatusoutput(cmd)
    if failure:
        print 'Could not run preprocess:\n%s' % cmd
        sys.exit(1)
    return resultfile

def main():
    try:
        format = sys.argv[1]
        filename = sys.argv[2]
    except IndexError:
        print 'Usage: %s format filename [preprocess options]\n' \
              % sys.argv[0]
        print 'formats:', supported_format_names()
        print '-DFORMAT=format is always defined when running preprocess'
        print 'Other -Dvar preprocess options can be added'
        sys.exit(1)

    names = supported_format_names()
    if format not in names:
        print '%s is not among the supported formats:\n%s' % (format, names)
        sys.exit(1)
        
    debug('\n\n>>>>>>>>>>>>>>>>> %s >>>>>>>>>>>>>>>>>\n\n' % format)
    if filename[-7:] != '.do.txt':
        print 'Wrong extension of %s, must be ".do.txt"' % filename
        sys.exit(1)
    basename = filename[:-7]
    out_filename = basename + FILENAME_EXTENSION[format]
    print '\n----- doconce2format %s %s' % (format, filename)
    filename_preprocessed = preprocess(filename, format,
                                       ' '.join(sys.argv[3:]))
    doconce2format(filename_preprocessed, format, out_filename)
    os.remove(filename_preprocessed)  # clean up
    print '----- successful run: %s filtered to %s\n' % \
          (filename, out_filename)
    
if __name__ == '__main__':
    main()
