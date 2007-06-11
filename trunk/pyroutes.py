#! /usr/bin/env python
#
# This program reads a Tab Seperated Field text file with route directions to
# make a route description for use in route-holders.
# The data in the text file must be formatted as follows:
# distance since last direction<tab>total distance<tab>route-direction<tab>Remarks
# Field 3 or 4 starting with '#' will be shown emphasized.
# Field 2 starting with '@' will be shown in bold.
# Field 1 starting with '<' wil start an alternative line numbering, in Roman Numerals.
# Field 1 starting with '>' ends the alternative line numbering.
# The program writes the data as a LaTeX longtable, which can be compiled to a
# dvi/pdf/ps file.
# Example of a text file for a route (in Dutch):
#
# 0	0	Via A4, A10-south, A10-east to Amsterdam	
# 46.5		RT at exit S114 Zeeburg	
# 1.2		T-FRK LT	S114, Zuiderzeeweg
# 1.1		2nd TFL RT to Noord (white sign)	
# 1.3	50	ROT RT and immediately FRK LT to Durgerdam	Liergouw
# 2.0		T-FRK LT to Ransdorp	Dorpsweg Ransdorp
# 	@RANSDORP		
# 		# comment in field 3	# or field 4 will be printed empasized
#
# The [tab] charcters must be 'real' tabs, not "soft-tabs" with spaces.
# The last, thirth [tab] can be left out, in that case the program
# notices this and adds the replacing struture by it self. If too little
# fields in a row are read, the program also notices this, but in that
# case the offending row is not used.
# In case of too many fields in a row, only the first four are used.
'''
Usage:
FormatRoutes [-s N.N] [-h] [-t "title"] [-z NN] [TSV file]
Options: -h          this help
         -s N.N      relative height of table rows, between 0.7 and 3.0
         -t "title"  Optional title for the route
         -d          Draft version; table rows for distances filled with dots,
                     -s becomes 2.0 when -d is used.
         -z NN       Edition nummer for a "Zeepaardjesrit" -version; the file
                     "ZPR-Voorpagina.tex" will be loaded and used to make the
                     frontpage with.
The file that is written has the name of the input-file, with the suffix
(e.g. 'txt') replaced by 'tex'.
Also the title is taken from the name of the input-file, unless the user
supplies a seperate title with -t "sometitle".
'''
import os
import sys
import csv
import re

# Print usage message and exit
def usage(*args):
    sys.stdout = sys.stderr
    for msg in args: print msg
    print __doc__
    sys.exit(1)

# decToRoman from ASPN
coding = zip(
    [1000,900,500,400,100,90,50,40,10,9,5,4,1],
    ["M","CM","D","CD","C","XC","L","XL","X","IX","V","IV","I"]
)

def decToRoman(num):
    if num <= 0 or num >= 4000 or int(num) != num:
        raise ValueError('Input should be an integer between 1 and 3999')
    result = []
    for d, r in coding:
        while num >= d:
            result.append(r)
            num -= d
    return ''.join(result)

def UserInput():
    '''
    UserInput asks for the filename of the Tab Seperated Route File to parse.
    Arguments: none
    Returns: name of input file in RouteFile and name of formatted output file to be written in FmtRouteFile
    '''
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

    try:
        RouteFile = raw_input("The name of the TSV route file please: ")
        f = open(RouteFile, 'r')
    except IOError, msg:
        usage("Cannot read %s.\n %s" % (repr(RouteFile), str(msg)))
    f.close()
    UserTitle = str(raw_input("A title for the route please (<Enter> for usage of the input filename): "))
    if UserTitle:
        Title = UserTitle
    else:
        Title = RouteFile.rpartition('.')[0] #rpartition('.')[0] returns the stuff before the last .
    FmtRouteFile = RouteFile.rpartition('.')[0] + '.tex'
    return RouteFile, FmtRouteFile, Title

# Get Frontpage matter for a "Zeepaardjesrit" or default.
def MakeFrontMatter(ZPRedition):
    '''
    MakeFrontMatter: makes a list containing default or extended frontpage
    Argumenten: ZPRedition; greater than 0 for usage of extended "Zeepaardjes-rit" fontpage
                            The extended page is read from file "ZPR-Voorpagina.tex".
                            this file has to be present in the directory the program
                            is run in.
                            ZPRedition is also put in the LaTeX frontpage
    returns: FrontMatter; list of LaTeX commands and text to make frontpage
    '''
    if ZPRedition:
        NewCommand = '\\vspace{0.25cm}\n\\newcommand{\\ZPReditie}{' + ZPRedition + '}\n'
        try:
            f = open("ZPR-Voorpagina.tex")
            FrontMatter = NewCommand + ''.join(f.readlines())
            f.close()
        except IOError, msg:
            usage("Cannot read %s.\n %s" % (repr(f), str(msg)))
    else:
        FrontMatter = [
        '\\hspace*{0.5cm}\\underline{Used acronyms:}\\\\\n',
        '\\textbf{\\begin{tabular}{ll}\n',
        'CRS: & Crossing\\\\\n',
        'LT: & Left\\\\\n',
        'PNS: & Placename Sign\\\\\n',
        'RT: & Right\\\\\n',
        'dir: & direction\\\\\n',
        'ROT: & Round-about\\\\\n',
        'FRK: & Road fork\\\\\n',
        'TFL: & Traffic Light\\\\\n',
        'YaC: & Yield at Crossing\\\\\n',
        'YaR: & Yield at Road\\\\\n',
        '\\underline{NOORDWIJK}: & Placename Sign\\\\\n',
        '\\end{tabular}}\n']
    return FrontMatter

# Take route file in.
def ReadTSVRoute(RouteFile):
    '''
    Uses csv module to read fileds from Tab Seperate value route file
    Arguments: RouteFile name of input file
    Returns:   RouteList list of raw route text
    '''
    TSVRouteRead = csv.reader(open(RouteFile, "rb"), delimiter='\t', quoting=csv.QUOTE_NONE)
    RouteList = []
    InvalidLines = 0
    for row in TSVRouteRead:
        if len(row) < 3:
            print "Row will not be used.\nNumber of fields in this row is %d (minimal 3), edit please." % len(row)
            print `row`
            InvalidLines += 1
        elif len(row) == 3:
            print "The number of fields in this row is 3, the row will be appended."
            print "Old:\t%s" % `row`
            row.append('')
            print "New:\t%s" % `row`
            RouteList.append(row)
        elif len(row) > 4:
            print "The number of fields in this row is %d, edit please\n (first 4 fields of the row are used)." % len(row)
            print `row`
            RouteList.append(row)
        else:
            RouteList.append(row)
    return RouteList, InvalidLines

# Add LaTeX longtable formats and divide in blocks of 5
def FormatRoute(RouteList, FrontMatter, Title, Stretch, Draft):
    '''
    FormatRoute gets the raw TSV date and formats this in to LaTeX.
    Arguments: RouteList   list with route text fields
               FrontMatter LaTeX frontpage stuff.
               Title       Title to write on top of the route
               Stretch     Relative distance between rows
               Draft       boolean to make spaces under distance columns fill with dots.
    Returns:   NewRouteList list with LaTeX formatted text
    '''
    NewRouteList = []
    RowNum = 0
    AltRowNum = 1 # ASCII 'a'
    UseAltRowNum = False
    # Community namesign matches all names starting with '@'
    PlaatsNaam = re.compile(r'^@(.*)$')
    # Comment matches a string that starts with a hash
    Comment =   re.compile(r'^#(.*)$')
    AltRouteStart = re.compile(r'^<(.*)$')
    AltRouteEnd = re.compile(r'^>(.*)$')
    EmptyRow = '& & & \\\\\n'
    ArrayStretch = '\\renewcommand{\\arraystretch}{' + Stretch + '}\n'
    TitleRow = '\\begin{center}\\framebox[10cm]{\\begin{LARGE}\\textbf{' + Title + '}\\end{LARGE}}\\end{center}\n'

    PreAmble = [
    '\\documentclass[dvips,a4paper,12pt]{article}\n',
    '\\usepackage{longtable}\n',
    '\\usepackage[T1]{fontenc}\n',
    '\\usepackage[latin1]{inputenc}\n',
    '\\usepackage[]{times}\n',
    '\\usepackage{fancyhdr}\n',
    '\\usepackage{lastpage}\n',
    '\\usepackage[margin=1cm,centering]{geometry}\n',
    '\\pagestyle{fancy}\n',
    '\\renewcommand{\\headrulewidth}{0pt}\n',
    '\\setlength{\\textheight}{27cm}\n',
    '\\fancyfoot[L]{MCN ' + Title + '}\n',
    '\\fancyfoot[C]{\\thepage / \\pageref{LastPage}}\n',
    '\\fancyfoot[R]{\\*Datum\\*}\n',
    '\\def\\BackgroundEPS#1#2#3#4{%\n',
    '\\special{ps: @beginspecial @setspecial initmatrix\n',
    '0.1 setgray #2 #3 translate #4 dup scale}\n',
    '\\special{ps: plotfile #1}\n',
    '\\special{ps: @endspecial}\n',
    '}\n',
    '\\BackgroundEPS{MCNLogo-grey.eps}{60}{60}{1.5}\n',
    '\\begin{document}\n',
    TitleRow]

    BeginTable = [
    ArrayStretch,
    '\\begin{longtable}{p{0.5cm}p{1.2cm}p{1.0cm}p{9cm}p{6cm}}\n',
    '& diff (km) & total (km) & \\newline Direction & \\newline Streetname/Remark\\\ \hline \endhead\n']

    PostAmble = [
    '\\hfill\n',
    '\\end{longtable}\n',
    '\\end{document}\n']

    for Row in PreAmble:
        NewRouteList.append(Row)
    for Row in FrontMatter:
        NewRouteList.append(Row)
    for Row in BeginTable:
        NewRouteList.append(Row)
    for Row in RouteList:
        RowNum += 1
        if AltRouteStart.match(Row[1]):
            KeepRowNum = RowNum
            RowNum = AltRowNum
            Row[1] = Row[1][1:]
            UseAltRowNum = True
        elif AltRouteEnd.match(Row[1]):
            RowNum = KeepRowNum
            Row[1] = Row[1][1:]
            UseAltRowNum = False
        if UseAltRowNum:
            RowNumStr = '\\textit{' + decToRoman(RowNum) +'}'
        else:
            RowNumStr = '\\textit{' +`RowNum` +'}'
        DepDF = DF = '\\dotfill & '
        if PlaatsNaam.match(Row[1]):
            Row[1] = '\\underline{\\textbf{' + Row[1][1:] + '}}'
            RowNumStr = '' # No linenumbers together with community name-signs
            DepDF = '& '
            RowNum -=1
        if Comment.match(Row[2]):
            Row[2] = '\\underline{\\emph{' + Row[2][1:] + '}}' #[1:] to remove the hash.
            DepDF = '& '
            RowNumStr = '' # No linenumbers together with comments in 2nd field
            RowNum -=1
        if Comment.match(Row[3]):
            Row[3] = '\\underline{\\emph{' + Row[3][1:] + '}}'
        if Draft == 1:
            DraftDF = DF
        else:
            DraftDF = '& '
        NewRow =  RowNumStr + ' & ' + Row[0] + DraftDF + Row[1] + DraftDF + Row[2] + DepDF + Row[3] + '\\\\\n'
        NewRouteList.append(NewRow)
        if RowNum % 5 == 0: # Make nice 5 row parts
            NewRouteList.append(EmptyRow)
    for Row in PostAmble:
        NewRouteList.append(Row)
    return NewRouteList

def WriteFormattedRoute(NewRouteList,FmtRouteFile):
    '''
    WriteFormattedRoute writes the data back to disk.
    Arguments: NewRouteList list with the LaTeX formatted route
               FmtRouteFile file-name to write data to.
    Returns:   none
    '''
    try:
        f = open(FmtRouteFile, 'w')
        for Row in NewRouteList:
            f.write(Row)
        f.close()
    except IOError, msg:
        usage("Cannot write to %s.\n %s" % (repr(FmtRouteFile), str(msg)))

# Main program: parse command line and start processing
def main():
    '''
    main() handles the arguments to the script and calls the the other functions with
    arguments from the command line if they are supplied, or calls the UserInput function first
    if no argument are supplied.
    Arguments: none
    Returns: none
    '''
    import getopt
    try:
        opts, args = getopt.getopt(sys.argv[1:], 's:t:z:dh')
    except getopt.error, msg:
        usage(msg)
    Stretch = '1.0'
    OptTitle = ''
    Draft = 0
    ZPRedition = ''
    for o, a in opts:
        if o == '-h': usage()
        if o == '-s':
            Stretch = a
        if o == '-t':
            OptTitle = a
        if o == '-d':
            Draft = 1
            Stretch = '2.0'
        if o == '-z':
            ZPRedition = a
    try:
        if float(Stretch) < 0.7 or float(Stretch) > 3.0:
            print "Relative distance -s %s not valid. -s will be 1.0" % Stretch
            Stretch = '1.0'
    except ValueError, msg:
        usage(msg)
    if args:
        RouteFile = args[0]
        if OptTitle:
            Title = OptTitle
        else:
            Title = RouteFile.rpartition('.')[0]
        FmtRouteFile = RouteFile.rpartition('.')[0] + '.tex'
    else:
        RouteFile, FmtRouteFile, Title = UserInput()
    if ZPRedition:
        print "This is a 'Zeepaardjes' version"
        Title = ZPRedition + 'e ' + Title
    RouteList, InvalidLines = ReadTSVRoute(RouteFile)
    print "The route file is read from %s (%d lines, %d invalid)\n" % (RouteFile,len(RouteList),InvalidLines)
    print "The title will be: \'%s\'\n" % Title
    print "The distance between the rows will be %sx larger" % Stretch
    FrontMatter = MakeFrontMatter(ZPRedition)
    NewRouteList = FormatRoute(RouteList, FrontMatter, Title, Stretch, Draft)
    print; print "The LaTeX route file will be written in %s\n" % FmtRouteFile
    WriteFormattedRoute(NewRouteList,FmtRouteFile)
    print "Done.."
    print "Edit the LaTeX file if neccessary to remove empty lines etc., and compile"
    print "the generated file with:  build-mcnroute.sh %s.\n" % FmtRouteFile
    return

if __name__ == '__main__':
    main()
