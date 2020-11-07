#!/usr/bin/python

__author__     = "Michael Lienhardt"
__copyright__  = "Copyright 2019-2020, Michael Lienhardt"
__license__    = "GPL3"
__version__    = "1"
__maintainer__ = "Michael Lienhardt"
__email__      = "michael.lienhardt@onera.fr"
__status__     = "Prototype"


# Graph loading and generation
import random
import sys
import argparse
import sys

# Parsing
import pydot
import lrparsing

# Solving
import z3

#
# CONSTRAINT SYNTAX AND TRANSLATION IN Z3
#

KW_AND = 'and'
KW_NOT = 'not'
KW_XOR = 'xor'
KW_OR  = 'or'
KW_IMPLIES = '=>'
KW_IFF = '<=>'
KW_TRUE = 'True'
KW_FALSE = 'False'

class T(lrparsing.TokenRegistry):
  AND     = lrparsing.Keyword(KW_AND)
  NOT     = lrparsing.Keyword(KW_NOT)
  XOR     = lrparsing.Keyword(KW_XOR)
  OR      = lrparsing.Keyword(KW_OR)
  IMPLIES = lrparsing.Token(KW_IMPLIES)
  IFF     = lrparsing.Token(KW_IFF)
  TRUE    = lrparsing.Keyword(KW_TRUE)
  FALSE   = lrparsing.Keyword(KW_FALSE)
  # special symbols
  LPAREN     = lrparsing.Token('(')
  RPAREN     = lrparsing.Token(')')

class C(lrparsing.Grammar):
  c_base = lrparsing.Token(re=r'[0-9a-zA-Z_]+') | (T.LPAREN + lrparsing.Ref('c_iff') + T.RPAREN)
  c_not = T.NOT*(0,1) + c_base
  c_and = c_not + (T.AND + c_not)*()
  c_xor = c_and + (T.XOR + c_and)*()
  c_or = c_xor + (T.OR + c_xor)*()
  c_implies = c_or | (c_or + T.IMPLIES + c_or)
  c_iff = c_implies | (c_implies + T.IFF + c_implies)
  START = c_iff

lrparsing.compile_grammar(C)

class c_translator(object):
  __slots__ = '_features'
  def __init__(self):
    self._features = {}

  def c_translate_base(self, parse_tree):
    #print("        c_base: {}".format(parse_tree))
    if(parse_tree[1][1] == '('): return self.c_translate_iff(parse_tree[2])
    elif(parse_tree[1][1] == KW_TRUE): return True
    elif(parse_tree[1][1] == KW_FALSE): return False
    else:
      name = parse_tree[1][1]
      res = self._features.get(name)
      if(res is None):
        res = z3.Bool(name)
        self._features[name] = res
      return res
  def c_translate_not(self, parse_tree):
    if(parse_tree[1][1] != KW_NOT): res = self.c_translate_base(parse_tree[1])
    else: res = z3.Not(self.c_translate_base(parse_tree[2]))
    #print("     c_not: {}".format(spc_debug(res)))
    return res
  def c_translate_and(self, parse_tree):
    subs = tuple(self.c_translate_not(el) for el in parse_tree if((len(el) > 0) and (el[0].name == "c_not")))
    #print("    c_and: {}".format([spc_debug(el) for el in subs]))
    if(len(subs) == 1): return subs[0]
    else: return z3.And(*subs)
  def c_translate_xor(self, parse_tree):
    subs = tuple(self.c_translate_and(el) for el in parse_tree if((len(el) > 0) and (el[0].name == "c_and")))
    #print("   c_xor: {}".format([spc_debug(el) for el in subs]))
    if(len(subs) == 1): return subs[0]
    else: return z3.Xor(*subs)
  def c_translate_or(self, parse_tree):
    subs = tuple(self.c_translate_xor(el) for el in parse_tree if((len(el) > 0) and (el[0].name == "c_xor")))
    #print("  c_or: {}".format([spc_debug(el) for el in subs]))
    if(len(subs) == 1): return subs[0]
    else: return z3.Or(*subs)
  def c_translate_implies(self, parse_tree):
    subs = tuple(self.c_translate_or(el) for el in parse_tree if((len(el) > 0) and (el[0].name == "c_or")))
    #print(" c_implies: {}".format([spc_debug(el) for el in subs]))
    if(len(subs) == 1): return subs[0]
    else: return z3.Implies(subs[0], subs[1])
  def c_translate_iff(self, parse_tree):
    subs = tuple(self.c_translate_implies(el) for el in parse_tree if((len(el) > 0) and (el[0].name == "c_implies")))
    #print("c_iff: {}".format([spc_debug(el) for el in subs]))
    if(len(subs) == 1): return subs[0]
    else: return subs[0] == subs[1]

  def c_translate(self, s): return self.c_translate_iff(C.parse(s)[1])



#
# CORE IMPLEMENTATION OF FTS
#

z3_id = 0
def fresh_var():
  global z3_id
  res = z3_id
  z3_id = z3_id + 1
  return z3.Bool(str(res))


class State(object):
  """Simple implementation of a state class"""
  __slots__ = '_id', '_in', '_out', '_z3_var', '_is_hidden_deadlock'
  def __init__(self, id):
    self._id = id
    self._in = set()
    self._out = set()
    self._z3_var = fresh_var()
    self._is_hidden_deadlock = None
  def __str__(self): return str(self._id)


class Transition(object):
  """Generic edge class specification"""
  __slots__ = '_in', '_out', '_label', '_constraint', '_z3_var', '_is_dead', '_is_false_optional'
  def __init__(self, _in, _out, label, constraint):
    self._in = _in
    self._out = _out
    self._label = label
    self._constraint = constraint
    self._z3_var = fresh_var()
    self._is_dead = None
    self._is_false_optional = None
  def __str__(self): return f"({str(self._in)}, {str(self._out)}, {self._label})"


class FTS(c_translator):
  __slots__ = '_name', '_fm', '_states', '_transitions', '_initial', '_set_hidden_deadlock', '_set_dead', '_set_false_optional'

  def __init__(self, name, fm):
    super().__init__()
    self._name = name
    self._fm = self.c_translate(fm[1:-1] if(fm is not None) else KW_TRUE)                # the feature model of the FTS
    self._states = {}
    self._transitions = []
    self._initial = None         # the initial state of the FTS
    self._set_hidden_deadlock = None # the list of hidden deadlocks in the FTS
    self._set_dead = None # the list of dead transitions in the FTS
    self._set_false_optional = None

  def state(self, id):
    """this method adds the state $id to the FTS"""
    res = self._states.get(id)
    if(res is None):
      res = State(id)
      self._states[id] = res
    return res

  def transition(self, _in, _out, label, constraint):
    """this method adds the transition between the states $_in and $_out, with the label $label and the constraint $constraint to the FTS"""
    _in = self.state(_in)
    _out = self.state(_out)
    transition = Transition(_in, _out, label, self.c_translate(constraint))
    _in._out.add(transition)
    _out._in.add(transition)
    self._transitions.append(transition)

  # this method sets the initial state of the FTS
  def initial_state(self, id): 
    self._initial = self.state(id)
    return self._initial

  def report(self):
    print(f"{self._name}: {'not live' if self._set_hidden_deadlock else 'live'}")
    print(f"  HIDDEN DEADLOCKS = {tuple(str(n) for n in self._set_hidden_deadlock)}")
    if(self._set_false_optional is None):
      print("  FALSE OPTIONAL   = NOT ANALYSED")
    else: print(f"  FALSE OPTIONAL   = {tuple(str(e) for e in self._set_false_optional)}")
    if(self._set_dead is None):
      print("  DEAD TRANSITIONS = NOT ANALYSED")
    else: print(f"  DEAD TRANSITIONS = {tuple(str(e) for e in self._set_dead)}")


#
# FTS LOADING AND TRANSLATION
#

def load_dot(f):
  g = pydot.graph_from_dot_data(f.read())[0]
  
  if(g.get_type() != "digraph"):
    print("ERROR: the input graph is not a digraph (it is a {} instead)".format(g.get_type()))
    return

  g_attributes = g.get_attributes()
  fm = g_attributes.get('FM')
  name = g_attributes.get('name')
  name = name[1:-1] if(name is not None) else file_name

  res = FTS(name, fm)
  for node in g.get_nodes():
    node_name = node.get_name()
    if(node_name not in ('node', 'FeatureModel')):
      res.state(node_name)
      if(node.get_attributes().get('initial', False)): res.initial_state(node_name)

  for edge in g.get_edges():
    entry = edge.get_source()
    exit = edge.get_destination()
    label, constraint = edge.get_attributes().get('label', "|True")[1:-1].split('|')
    #print(action, formula)
    res.transition(entry, exit, label, constraint)

  return res


###############################################################################
# SAT ANALYSIS
###############################################################################


def one_exit(n):
  out = n._out
  if(len(out) > 1):
    return tuple(z3.Implies(e1._z3_var, z3.Not(z3.Or(*tuple(e2._z3_var for e2 in out if e2 is not e1)))) for e1 in out)
  else: return ()

def no_exit(n):
  return tuple(z3.Not(e._z3_var) for e in n._out)

def z3_translator(fts):
    # z3_states = the constraint when each node is accessible, or within a loop
    z3_states = (fts._initial._z3_var,) #(fts._initial._z3_var == True,)
    z3_states = z3_states + tuple(z3.Implies(n._z3_var, z3.Or(*tuple(z3.And(e._z3_var, e._constraint, e._in._z3_var) for e in n._in))) for n in fts._states.values() if n != fts._initial)
    # forbid loops
    no_loop_partial = []
    for n in fts._states.values(): no_loop_partial.extend(one_exit(n))
    return (fts._fm, *z3_states, *no_loop_partial)


def z3_analyse_full(fts):
  print("setting up solver ...", flush=True)
  solver = z3.Solver()
  constraint_list = z3_translator(fts)
  solver.add(*constraint_list)
  print(" ... done", flush=True)

  for i,n in enumerate(fts._states.values()):
    print(f"managing node {str(i)}: {str(n)} ...")
    if(n._out):
      constraint_annex = (n._z3_var, *no_exit(n)) + tuple(z3.Not(e._constraint) for e in n._out)
      n._is_hidden_deadlock = (solver.check(*constraint_annex,) == z3.sat)
    else: n._is_hidden_deadlock = False

  for i,t in enumerate(fts._transitions):
    print(f"managing transition {str(i)}: {str(t)} ...")
    t_in_useful = (t._in._z3_var, *no_exit(t._in))
    #n._is_hidden_deadlock = (solver.check(*constraint_annex, *tuple(z3.Not(e._constraint) for e in n._out)) == z3.sat)
    if(t._constraint is True):
      t._is_dead = not (solver.check(*t_in_useful) == z3.sat)
      t._is_false_optional = False
    elif(t._constraint is False):
      t._is_dead = True
      t._is_false_optional = False
    else:
      t._is_dead = not (solver.check(*t_in_useful, t._constraint) == z3.sat)
      if(t._is_dead): t._is_false_optional = False
      else: t._is_false_optional = not (solver.check(*t_in_useful, z3.Not(t._constraint)) == z3.sat)

  # Collect all information
  fts._set_hidden_deadlock = tuple( n for n in fts._states.values() if n._is_hidden_deadlock )
  fts._set_false_optional = tuple( e for e in fts._transitions if e._is_false_optional )
  fts._set_dead = tuple( e for e in fts._transitions if e._is_dead )


def z3_analyse_hdead(fts):
  print("setting up solver ...", flush=True)
  solver = z3.Solver()
  constraint_list = z3_translator(fts)
  solver.add(*constraint_list)
  print(" ... done", flush=True)

  for i,n in enumerate(fts._states.values()):
    print(f"managing node {str(i)}: {str(n)} ...")
    if(n._out):
      constraint_annex = (n._z3_var, *no_exit(n)) + tuple(z3.Not(e._constraint) for e in n._out)
      n._is_hidden_deadlock = (solver.check(*constraint_annex,) == z3.sat)
    else: n._is_hidden_deadlock = False

  # Collect all information
  fts._set_hidden_deadlock = tuple( n for n in fts._states.values() if n._is_hidden_deadlock )


def z3_analyse_quick(fts):
  print("setting up solver ...", flush=True)
  solver = z3.Solver()
  constraint_list = z3_translator(fts)
  solver.add(*constraint_list)
  print(" ... done", flush=True)

  for i,n in enumerate(fts._states.values()):
    print(f"managing node {str(i)}: {str(n)} ...")
    if(n._out):
      constraint_exit = tuple(z3.Not(e._constraint) for e in n._out)
      if(solver.check(*constraint_exit) != z3.sat):
        n._is_hidden_deadlock = False
      else:
        constraint_annex = (n._z3_var, *no_exit(n)) + constraint_exit
        n._is_hidden_deadlock = (solver.check(*constraint_annex) == z3.sat)
    else: n._is_hidden_deadlock = False

  # Collect all information
  fts._set_hidden_deadlock = tuple( n for n in fts._states.values() if n._is_hidden_deadlock )



def z3_analyse_alt(fts):
  print("setting up solver ...", flush=True)
  solver = z3.Solver()
  constraint_list = z3_translator(fts)
  solver.add(*constraint_list)
  print(" ... done", flush=True)

  #solver_optim = z3.Solver(ctx=z3.Context())
  #solver_optim.add(fts._fm)
  #print(tuple(f"node {str(n)} => {n._z3_var}" for n in fts._states.values()) + tuple(f"edge {str(e)} => {e._z3_var}" for e in fts._transitions))
  #print(constraint_list)
  #exit()
  #print(solver)
  for i,n in enumerate(fts._states.values()):
    print(f"managing node {str(i)}: {str(n)} ...")
    if(n._out):
      constraint_annex = (n._z3_var, *no_exit(n))
      n._is_hidden_deadlock = (solver.check(*tuple(z3.Not(e._constraint) for e in n._out)) == z3.sat)
      if(n._is_hidden_deadlock):
        n._is_hidden_deadlock = (solver.check(*constraint_annex, *tuple(z3.Not(e._constraint) for e in n._out)) == z3.sat)
      #n._is_hidden_deadlock = (solver.check(*constraint_annex, *tuple(z3.Not(e._constraint) for e in n._out)) == z3.sat)
      for e in n._out:
        if(e._constraint is True):
          e._is_dead = not (solver.check(*constraint_annex) == z3.sat)
          e._is_false_optional = False
        else:
          e._is_dead = not (solver.check(*constraint_annex, e._constraint) == z3.sat)
          if(e._is_dead): e._is_false_optional = False
          else: e._is_false_optional = not (solver.check(*constraint_annex, z3.Not(e._constraint)) == z3.sat)
      #solver.pop()
    else: n._is_hidden_deadlock = False
    print(f" ... done: hidden={n._is_hidden_deadlock}")
    for e in n._out:
      print(f"     edge {e}: false_opt={e._is_false_optional}, dead={e._is_dead}", flush=True)

  # Collect all information
  fts._set_hidden_deadlock = tuple( n for n in fts._states.values() if n._is_hidden_deadlock )
  fts._set_false_optional = tuple( e for e in fts._transitions if e._is_false_optional )
  fts._set_dead = tuple( e for e in fts._transitions if e._is_dead )






###############################################################################
# ADDITIONAL ANALYSIS FOR TESTING
###############################################################################

def check_always_accessible(graph, state_name):
  n_focus = graph._states[state_name]

  constraint_core = (n_focus._z3_var, *z3_translator(graph), *no_exit(n_focus)) # vincolo per un path verso s3
  to_hide = tuple(e._z3_var for e in graph._transitions) + tuple(n._z3_var for n in graph._states.values() if state_name != n_focus) # nascondo tutte le transizione e i stati diversi da s3
  solver = z3.Solver()
  solver.add(z3.Not( z3.Exists(to_hide, z3.And(*constraint_core)) )) # check se tautologia

  if(solver.check() == z3.sat):
    print(f"There exists a configuration in which {state_name} is not accessible:")
    model = solver.model()
    print(f"  {[ f'{f} => {model.eval(v)}' for f,v in graph._features.items()]}")
  else: print("OK")  # è una tautologia


def clean_path(graph, path, end):
  n = graph._initial
  res = []
  while(n != end):
    for e in n._out:
      if(e in path):
        res.append(e)
        n = e._out
        break
  return res

def compute_paths(graph, state_name):
  n_focus = graph._states[state_name]

  constraint_core = (n_focus._z3_var, *z3_translator(graph), *no_exit(n_focus))
  solver = z3.Solver()
  solver.add(constraint_core)
  while(solver.check() == z3.sat):
    model = solver.model()
    solution = {e for e in graph._transitions if z3.is_true(model.eval(e._z3_var))}
    solution = clean_path(graph, solution, n_focus)
    product = {f for f,v in graph._features.items() if z3.is_true(model.eval(v))} # this is just a possible product for this path, not all of them
    print(f"found path [product={product}]: { [str(e) for e in solution] }")
    solver.add(z3.Not(z3.And(*tuple(e._z3_var for e in solution)))) # next, search another path


#
# RANDOM ACYCLIC FTS GENERATION
#

def random_fts(nb_node, percent_edge):
  nb_rank = random.randint(0, nb_node - 1)
  nodes = { i: random.randint(0,nb_rank) for i in range(nb_node) }
  full_edges = { i: [j for j in range(nb_node) if nodes[i] < nodes[j]] for i in range(nb_node) }
  edges = { i: (random.choices(full_edges[i], k=((len(full_edges[i])*percent_edge)//100)) if(full_edges[i]) else []) for i in range(nb_node)}

  res = FTS("random", "True")
  for i, ns in edges.items():
    for j in ns:
      res.transition(f"S{i}", f"S{j}", "no_action", "True")
  res.initial_state("S0")
  return res



###############################################################################
# MAIN PROGRAM
###############################################################################


def set_default_subparser(parser, name):
  commands = { cmd for x in parser._subparsers._actions if(isinstance(x, argparse._SubParsersAction)) for cmd in x._name_parser_map.keys() }
  commands.update(('-h', '--help'))
  if(len(sys.argv) > 1):
    option = sys.argv[1]
    if(option in commands): return
  sys.argv.insert(1, name)

self_program_name = None
def main_manage_cmd_options():
  parser = argparse.ArgumentParser()
  subparsers = parser.add_subparsers()

  main_parser = subparsers.add_parser('main', add_help=False)
  main_parser.set_defaults(cmd='main')
  main_parser.add_argument('-g', '--generate', nargs=2, default=None)
  analysis_option = main_parser.add_mutually_exclusive_group()
  main_parser.add_argument('file', nargs='?', default=None)
  analysis_option.add_argument('--full', action="store_true")
  analysis_option.add_argument('--hdead', action="store_true")
  analysis_option.add_argument('--quick', action="store_true")
  analysis_option.add_argument('--alt', action="store_true")

  acc_parser = subparsers.add_parser('acc', add_help=False)
  acc_parser.set_defaults(cmd='acc')
  acc_parser.add_argument('state')
  acc_parser.add_argument('file', nargs='?', default=None)

  path_parser = subparsers.add_parser('path', add_help=False)
  path_parser.set_defaults(cmd='path')
  path_parser.add_argument('state')
  path_parser.add_argument('file', nargs='?', default=None)

  set_default_subparser(parser, 'main')
  #
  global self_program_name
  self_program_name = parser.prog

  args = parser.parse_args()

  if(args.cmd == "main"):
    if((args.generate is not None) and (args.file is not None)):
      print("ERROR: options -g and -f are incompatible")
      exit(-1)
    elif(args.generate is not None):
      fts = random_fts(int(args.generate[0]), int(args.generate[1]))
    elif(args.file is not None):
      fts = None
      with open(args.file, 'r') as f:
        fts = load_dot(f)
    else: fts = load_dot(sys.stdin)
    func_analyse = z3_analyse_full
    if args.hdead: func_analyse = z3_analyse_hdead
    elif args.quick: func_analyse = z3_analyse_quick
    elif args.alt: func_analyse = z3_analyse_alt
    func_display = lambda fts: fts.report()
    return func_analyse, func_display, fts
  elif(args.cmd == "acc"):
    if(args.file is not None):
      with open(args.file, 'r') as f:
        fts = load_dot(f)
    else: fts = load_dot(sys.stdin)
    state = args.state
    func_analyse = lambda fts: check_always_accessible(fts, state)
    func_display = None
    return func_analyse, func_display, fts
  elif(args.cmd == "path"):
    if(args.file is not None):
      with open(args.file, 'r') as f:
        fts = load_dot(f)
    else: fts = load_dot(sys.stdin)
    state = args.state
    func_analyse = lambda fts: compute_paths(fts, state)
    func_display = None
    return func_analyse, func_display, fts


#if(__name__ == "__main__"):
#  fts_implem, nb_node, pct_edge = main_manage_cmd_options_random()
#  fts = random_fts(fts_implem, nb_node, pct_edge)
#  print(fts.dot("random FTS"))


if(__name__ == "__main__"):
  func_analyse, func_display, fts = main_manage_cmd_options()
  #fts_debug(name, fts)
  func_analyse(fts)
  if(func_display): func_display(fts)



