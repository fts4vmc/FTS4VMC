import os
import sys
from src.internals.translator import Translator

def main(source, target):
    t = Translator()
    t.load_model(source)
    t.translate()
    with open(target, 'w') as out:
        out.write(t.get_output())

if len(sys.argv) < 2 or len(sys.argv) >= 2 and sys.argv[1] == None:
    print ("Usage: python3 translate.py [source file] [output file]")
    print ("Usage: python3 translate.py [source file]")
    print ("Output file will be saved in the same directory of source file,\n"+
            "using the same filename prepended with vmc- if no output path is given.")
    exit()

if len(sys.argv) >= 2 and os.path.exists(sys.argv[1]):
    source = sys.argv[1]
else:
    print ("Invalid path for source file")
    print ("Usage: python3 translate.py [source file] [output file]")
    exit()

if len(sys.argv) == 2:
    path, base = os.path.split(source)
    target = os.path.join(path, 'vmc-'+base+'.txt')
elif len(sys.argv) >= 2 and sys.argv[2] != None:
    target = sys.argv[2]

main(source, target)

print ("Output written on "+target)
