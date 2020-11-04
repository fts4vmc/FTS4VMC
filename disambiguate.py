import os
import sys
import src.internals.analyser as analyser
from src.internals.disambiguator import Disambiguator

def main(source, target):
    with open(source, 'r') as fts_source:
        fts = analyser.load_dot(fts_source)
    fts_source.close()
    analyser.z3_analyse_full(fts)
    dis = Disambiguator.from_file(source)
    dis.remove_transitions(fts._set_dead)
    dis.set_true_list(fts._set_false_optional)
    dis.solve_hidden_deadlocks(fts._set_hidden_deadlock)
    with open(target, 'w') as out:
        out.write(dis.get_graph())

if len(sys.argv) < 2 or len(sys.argv) >= 2 and sys.argv[1] == None:
    print ("Usage: python3 disambiguate.py [source file] [output file]")
    print ("Usage: python3 disambiguate.py [source file]")
    print ("Output file will be saved in the same directory of source file,\n"+
            "using the same filename prepended with fixed- if no output path is given.")
    exit()

if len(sys.argv) >= 2 and os.path.exists(sys.argv[1]):
    source = sys.argv[1]
else:
    print ("Invalid path for source file")
    print ("Usage: python3 disambiguate.py [source file] [output file]")
    exit()

if len(sys.argv) == 2:
    path, base = os.path.split(source)
    target = os.path.join(path, 'fixed-'+base)
elif len(sys.argv) >= 2 and sys.argv[2] != None:
    target = sys.argv[2]

main(source, target)

print ("Output written on "+target)
