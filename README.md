[tutorial]: <https://www.youtube.com/watch?v=nck8vyk3JuA> "FTS4VMC setup and usage tutorial"
[SPLC2021]: <https://www.youtube.com/watch?v=OEuZ8BC-43U> "Static Analysis and Family based Model Checking with VMC"
[models]: ./fts_models

# FTS4VMC #

FTS4VMC is a tool to verify properties using family-based model checking taking as input featured transition system (FTS).  
It also provides detection and removal of ambiguities inside the FTS, written mostly in Python it uses Flask as web framework.  

## Models

Inside the [fts_models][models]
folder there are some examples of FTS written in dot compatible with FTS4VMC.

## Tutorials

+ FTS4VMC Quickstart [Video][tutorial]
+ Complete tutorial from SPLC 2021 [Video][SPLC2021]

# Install

## Dependencies ##

These software are required:

+ Graphviz open source graph visualization software. [Link](https://graphviz.org/download/ "Graphviz")
+ Python 3. [Link](https://www.python.org/downloads/ "Python 3")

On some OS the **python** and **pip** commands refer to Python 2, to make sure you're using Python 3 try the following commands:
```bash
$ python -V
 Python 3.9.2
$ pip -V
 pip 20.3.4 from /usr/lib/python3/dist-packages/pip (python 3.9)
```
If the previous commands refer to Python 2 you may need to upgrade your Python installation or check if the commands **python3** and **pip3** are available.

Source code can be obtained by either downloading the repository as ZIP file or using the following command:
```bash
$ git clone https://github.com/fts4vmc/FTS4VMC.git
```

### Graphviz

A path to the dot binaries must be present in the environment variable PATH for graph rendering.  

On Windows be sure to click on **Add Graphviz to system PATH** during the installation process.

On Mac installing Graphviz using brew adds the program to the PATH automatically.

On Linux if installed with a package manager it should be already available in
the PATH variable.

#### Add Graphviz to the PATH manually

If you'already installed Graphviz, but it is not available inside the PATH
variable, you have to locate where the executable is installed and then
add the program using the following command.

For Linux and Mac:
```bash
# With Graphviz's dot in /home/user/Downloads/Graphviz/bin/
$ export PATH=$PATH:/home/user/Downloads/Graphviz/bin
```
For Windows:
```bash
# With Graphviz's dot in C:\Program Files\Graphviz\bin\
$ set PATH=%PATH%;C:\Program Files\Graphviz\bin\
```
### Virtual environment and Python's dependencies ###

**WARNING: This project requires specific version of packages installed through pip
for reproducibility purpose, it is highly reccomended to use a Python's virtual
environment to prevent downgrade of system-wide libraries.**

To install the required packages under a virtual environment use the following
commands:
```bash
$ pip install virtualenv

# If administrator rights are required
$ sudo pip install virtualenv

# Create virtual environment in venv directory
$ python -m venv venv
```

To activate the environment:
```bash
#On Linux and Mac
$ . venv/bin/activate
#On Windows
$ venv\Scripts\activate.bat
```

Necessary python modules can be installed with the following command:
```bash
$ pip install -r requirements.txt
```

To deactivate:
```bash
#On Linux and Mac
$ deactivate
#On Windows
$ venv\Scripts\deactivate.bat
```

More details about Python's virtual environment can be found [here](https://docs.python.org/3/library/venv.html "venv").

## Structure ##

The source code is organized with the following structure:

+ *fts.py*: this file contains the definitions of functions used to upload files and execute analysis also includes bindings between functions and URLs.
+ *config.py*: this file contains the definitions of variables used in FTS4VMC
  to configure the server.
+ *sessions.py*: this file contains functions used to manage the users' session data.
+ *file_manager.py*: this file contains functions used to handle uploaded file and delete old ones.

+ *internals*: this folder contains the core files used for alter FTSs and execute family-based model checking.
	* *analyser.py*: this module implements the ambiguities analyser.
	* *disambiguator.py* this class implements the ambiguities removal.
	* *graph.py* this class implements the FTS and MTS graph rendering.
	* *translator.py*: this class implements the translation from a FTS to MTS.
	* *vmc_controller.py*: this class handles properties verification with VMC.
	* *process_manager.py*: this class handles multiprocessing required for real-time output during the analysis process.

+ *templates*: under this folder are contained the HTML templates used by Jinja to render the web pages.

+ *static*: under this folder are contained static resources.
	* *js*: contains JavaScript code used to handle asynchronous requests.
	* *css*: contains CSS style sheet files.


## Usage ##

### Flask ###

#### Tested on Windows 10, macOS Big Sur and Debian Bullseye ####

**WARNING**: Currently it is used the flask web server to deploy the application and it should be used only on localhost.


Launch app on Flask web server on Linux and Mac:
```bash
$ export FLASK_APP=src/fts.py
$ export FLASK_ENV=development
$ flask run
 * Running on http://127.0.0.1:5000/
```

On Windows:
```bash
$ set FLASK_APP=src\fts.py
$ set FLASK_ENV=development
$ flask run
 * Running on http://127.0.0.1:5000/
```

You can now use FTS4VMC by visiting http://localhost:5000 with a web
browser.

### Docker ###

#### Compatible with every OS capable of running Docker #####

An alternative deployment method is building the Docker image or using the
compiled one from Docker hub, this option works for all operative systems
supported by Docker and it is easier to set up.  

For Windows and Mac is required [Docker Desktop](https://www.docker.com/products/docker-desktop),
for Linux it can be installed through the packet manager of your distribution or by building
manually the program.

#### Building the docker image ####

From root of the repository execute the following command:

```bash
$ docker build -t fts4vmc -f docker/Dockerfile .
```

#### Running the docker container ####

For manually built image:

```bash
$ docker run -p <host port>:5000 fts4vmc
```

For running the image hosted on docker hub:

```bash
$ docker run -p <host port>:5000 gior26/fts4vmc
```

You can now use FTS4VMC by visiting http://localhost: \<host port\> with a web
browser.

### Command-line interface ###

FTS4VMC's disambiguator and translator modules can also be used from the command
line.

#### Disambiguation ####

After installing the required dependencies you can obtain a FTS with all the
ambiguities removed given a source FTS using the following command from the
root of the repository:

```bash
# Using vendingnew.dot as an example
$ python3 disambiguator.py fts_models/vendingnew/vendingnew.dot vendingnew-fixed.dot
```

#### Translation ####

The translator output files compatible with the Variability Model Checker
in txt format, using the output from the previous command we can perform the
translation using the following command from the root of the repository:

```bash
$ python3 translator.py vendingnew-fixed.dot vendingnew-vmc.txt
```

#### Verification of properties ####

Verification of properties is done using VMC, from the root of the repository
use the following commands:

```bash
# With property.txt containing: [pay] AF {take}
$ ./vmc65-linux vendingnew-vmc.txt property.txt

# To obtain the counterexample
$ ./vmc65-linux vendingnew-vmc.txt property.txt +z
```

## Manual

More details on how to use the deployed tool can be found
[here](https://github.com/fts4vmc/FTS4VMC/blob/master/MANUAL.md "User manual").

## Testing ##

From the root directory of FTS4VMC use the following command to launch all tests.

```bash
$ pip install pytest
$ python -m pytest
```

## Server-side configuration ##

Editing the src/config.py we can edit some server-side options, currently the
following options are available:

* Path to the folder used for storing uploaded files
  * UPLOAD_FOLDER
* Path to the folder used for storing temporary files
  * TMP_FOLDER
* Path to the VMC binaries
  * VMC_LINUX
  * VMC_MAC
  * VMC_WINDOWS
* Maximum uploaded file size
  * MAX_CONTENT_LENGTH = 2 * 1024 * 1024
  * MAX_CONTENT_UNIT = 'MB'
* Maximum number of edges for rendering graph using dot
  * RENDER_GRAPH_EDGE_LIMIT = 300
* Define the direction used to render dot graphs, accepted value are: TB, BT, LR, RL
  * RENDER_GRAPH_DIRECTION = 'TB'
