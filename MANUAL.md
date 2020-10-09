# FTS4VMC User Guide #

FTS4VMC is a tool to analyse feature transition system, detect and remove ambiguities,
display equivalent modal transition system and verify properties expressed in process algebra
compatible with the variability model checker [VMC](http://fmtlab.isti.cnr.it/vmc/V6.4/vmc.html).

The tool takes as input a dot file containing a FTS, here's an example:

~~~~
digraph COFFEE\_MACHINE { # the FTS is encoded as a directed graph
  # the following three lines are only used for display
  FeatureModel [shape=plaintext, style=filled, color=yellow, label="FM = M and W and C and (E xor D) and (P => R) and (not (P and D))"];
  FM="M and W and C and (E xor D) and (P => R) and (not (P and D))";    # the feature model of the FTS
  name="COFFEE MACHINE"; # the name of the FTS
  0 [initial=True] # states that the initial state of the FTS is "0"
  # all the transitions of the FTS; the label of a transition is 
  # structured in two parts, separated with the "|" symbols:
  #  - the first part is the action of the transition
  #  - the second part is the feature expression of the transition
  0 -> 1 [ label = "insertBev(Euro) | E" ];
  0 -> 1 [ label = "insertBev(Dollar) | D" ];
  1 -> 0 [ label = "cancelBev | X" ];  
  1 -> 2 [ label = "sugar | W" ];
  1 -> 3 [ label = "no\_sugar | W" ];
  2 -> 6 [ label = "coffee | C" ];
  2 -> 5 [ label = "tea | T" ];
  2 -> 4 [ label = "cappuccino | P" ];
  3 -> 9 [ label = "cappuccino | P" ];
  3 -> 8 [ label = "tea | T" ];
  3 -> 7 [ label = "coffee | C" ];
  6 -> 7 [ label = "pour\_sugar | W" ];
  5 -> 8 [ label = "pour\_sugar | W" ];
  4 -> 9 [ label = "pour\_sugar | W" ];
  9 -> 11 [ label = "pour\_milk | P" ];
  9 -> 10 [ label = "pour\_coffee | P" ];
  8 -> 12 [ label = "pour\_tea | T" ];
  7 -> 12 [ label = "pour\_coffee | C" ];
  11 -> 12 [ label = "pour\_coffee | P" ];
  10 -> 12 [ label = "pour\_milk | P" ];
  12 -> 13 [ label = "ring | R" ];
  12 -> 13 [ label = "skip | not R" ];
  13 -> 0 [ label = "take\_cup | M" ];
}
~~~~
