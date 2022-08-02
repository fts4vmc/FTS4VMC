# FTS4VMC User Guide #
[VMC]: https://fmt.isti.cnr.it/vmc
[UI-START]: ./manual_images/ui_start.png
[UI-SELECT]: ./manual_images/ui_select.png
[CONSOLE-TAB]: ./manual_images/console_tab.png
[SOURCE-TAB]: ./manual_images/source_tab.png
[GRAPH-TAB]: ./manual_images/graph_tab.png
[SUMMARY-TAB]: ./manual_images/summary_tab.png

FTS4VMC is a tool to analyze featured transition system, detect and remove ambiguities,
display transformed modal transition systems and verify properties expressed in a logic accepted by the Variability Model Checker [VMC][VMC].

The tool takes as input a dot file containing a FTS, here's an example of compatible dot file:

~~~~
digraph COFFEE_MACHINE { # the FTS is encoded as a directed graph
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
  1 -> 3 [ label = "no_sugar | W" ];
  2 -> 6 [ label = "coffee | C" ];
  2 -> 5 [ label = "tea | T" ];
  2 -> 4 [ label = "cappuccino | P" ];
  3 -> 9 [ label = "cappuccino | P" ];
  3 -> 8 [ label = "tea | T" ];
  3 -> 7 [ label = "coffee | C" ];
  6 -> 7 [ label = "pour_sugar | W" ];
  5 -> 8 [ label = "pour_sugar | W" ];
  4 -> 9 [ label = "pour_sugar | W" ];
  9 -> 11 [ label = "pour_milk | P" ];
  9 -> 10 [ label = "pour_coffee | P" ];
  8 -> 12 [ label = "pour_tea | T" ];
  7 -> 12 [ label = "pour_coffee | C" ];
  11 -> 12 [ label = "pour_coffee | P" ];
  10 -> 12 [ label = "pour_milk | P" ];
  12 -> 13 [ label = "ring | R" ];
  12 -> 13 [ label = "skip | not R" ];
  13 -> 0 [ label = "take_cup | M" ];
}
~~~~

## User interface ##

UI for FTS4VMC was inspired by [VMC][VMC] for easier integration between the tools.

Here's a screenshot:

![User Interface Start Menu][UI-START]

The first thing to do to start the process is selecting a dot file containing a FTS definition following the format showed in the previous example, this can be done by clicking on **Select FTS Model**.   
Once the file is selected it can be uploaded to the server by clicking on **Upload model**.

![User Interface Selected File][UI-SELECT]

When the upload is completed the server will inspect the provided file checking if the file is in dot format and does contain a FTS definition when both of these condition are true the file is ready for starting the analysis process otherwise the user is informed that the given file is not compatible with the tool.

### Tabs ###

There are four tabs used to show different aspects about the loaded FTS:
+ Console
+ Source
+ Graph
+ Summary
+ Counterexample graph


#### Console ####

The console tab is used to show the progress and the result for commands sent to the server, by pressing the **Download displayed result** the user can save the console output locally for further analysis.

![Console tab][CONSOLE-TAB]

#### Source ####

The source tab is used to show the source dot file for the currently displayed graph.  

![Source tab][SOURCE-TAB]

This is useful if the user want to save the FTS without ambiguities or the FTS with highlighted ambiguities or the equivalent MTS which can be done by clicking **Download displayed result** while the source tab is visible.

#### Graph ####

The graph tab is used to show the rendered graph using as source the same file displayed inside the source tab.

![Graph tab][GRAPH-TAB]

To prevent heavy load on server FTS with more than 300 transitions won't be rendered, these graphs can be rendered locally by downloading the content inside the source tab.   
Images are rendered in SVG format and they can also be downloaded by clicking **Download displayed result**.

#### Summary ####

The summary tab is used to present in a nicer way the console output after a successful analysis.  

![Summary tab][SUMMARY-TAB]

The displayed information are:
* Number of states
* Number of transitions
* Ambiguities found
  * Dead transitions
    1. Source state
    2. Destination state
    3. Action
    4. Feature expression
  * False optional transitions
    1. Source state
    2. Destination state
    3. Action
    4. Feature expression
  * Hidden deadlocks
  	* State name

This summary can also be downloaded by pressing **Download displayed result** in HTML format.

#### Counterexample graph ####

This tab is used to render the counterexample, obtained with the **Show explanation** button, as a graph(See VMC section below)

### Analysis ###

#### Full ambiguities analysis ####

The full ambiguities analysis will search inside the provided FTS for three types of ambiguities:  
+ Dead transition
+ False optional transition
+ Hidden deadlocks

This analysis may require quite a lot of time for bigger models so it's possible to abort it prematurely by clicking **Stop processing**.
The output of this process is an updated version of the uploaded FTS with:  
+ dead transitions highlighted in **blue**
+ false optional transitions highlighted in **green**
+ hidden deadlock highlighted in **red**

By completing a full analysis the buttons for removal of ambiguities will be enabled.

#### Liveness analysis ####

If the user is only interested in knowing if the FTS is live, meaning that it doesn't contain hidden deadlock, this analysis can get the answer way more quickly than a full ambiguities analysis by skipping the detection of dead transitions and false optional transitions.  
While faster than a full analysis it is also possible to stop a running liveness analysis clicking on **Stop processing**.

### Ambiguities removal ###

For ambiguities removal there are three possible options.  
Every command of this section will updated the code inside the source tab and the image present in the graph tab.

#### Remove false optional transitions #####

This command will remove false optional transition by replacing the transition's feature expression with True converting it into a must transition.  
This operation won't add or delete transition in the FTS.

#### Remove dead transitions and hidden deadlocks ####

This command alters the graph by deleting unreachable transitions if present, then it solves hidden deadlocks by adding an explicit deadlock state called DEAD and creating special transitions to this newly created state starting from every state marked as hidden deadlock with feature expression equivalent to the disjunction of every feature expression starting from a hidden deadlock state negated.  

#### Remove all ambiguities #####

This command combines the two types of ambiguities removal inside a single command.

### Modal transition system ###

FTS can quickly be converted into MTS by replacing transition with feature expression True into MTS's must transition and every other transition into an admissible one.  
By clicking on **View modal transition system** the user can quickly pass to an MTS view updating both the source code tab and the image inside the graph tab.

### <a name="vmc-section"></a> VMC ###

Once an analysis is fully completed and the FTS is found to be live it is possible to verify properties expressed in the logic accepted by the Variability Model Checker [VMC][VMC].  
Properties can be written inside the textarea under the **Verify properties** button.  
After checking if a property is either True or False you can ask a counterexample the see why the formula is False by clicking on the **Show explanation button**.
