# FTS4VMC #

FTS4VMC is a tool to verify properties using family-based model checking taking as input featured transition system (FTS).  
It also provides detection and removal of ambiguities inside the FTS, written mostly in Python it uses Flask as web framework.  
More details on how to use the tool can be found [here](https://github.com/fts4vmc/FTS4VMC/blob/master/MANUAL.md "User manual").

## Dependencies ##

These software are required:

+ Graphviz open source graph visualization software. [Link](https://graphviz.org/download/ "Graphviz")
+ Python 3. [Link](https://www.python.org/downloads/ "Python 3")

A path to the dot binaries must be present in the environment variable PATH for graph rendering.  

For Windows:
```
# With Graphviz's dot in C:\\Users\WIN10\Downloads\Graphviz\bin\
$ set PATH = %PATH%;C:\\Users\WIN10\Downloads\Graphviz\bin\
```

For Linux and Mac:
```bash
# With Graphviz's dot in /home/user/Downloads/Graphviz/bin/
$ export $PATH = $PATH:/home/user/Downloads/Graphviz/bin
```

Necessary python modules can be installed with the following command:
```bash
$ pip3 install -r requirements.txt
```

If you don't want to install these module system-wide read the next section for creating and activating a virtual environment then execute the previous command.

### Virtual environment ###

To prevent damaging user's libraries it is suggested to install the required packages under a virtual environment using:
```bash
$ python3 -m venv venv
```

To activate the environment:
```bash
#On Linux and Mac
$ . venv/bin/activate
#On Windows
$ venv\Scripts\activate.bat
```

More details about Python's virtual environment can be found [here](https://docs.python.org/3/library/venv.html "venv").

## Structure ##

The source code is organized with the following structure:

+ *fts.py*: this file contains the definitions of functions used to upload files and execute analysis also includes bindings between functions and URLs.
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

**WARNING**: Currently it is used the flask web server to deploy the application and it should be used only on localhost.

Launch app on Flask web server:
```bash
# For Linux and Mac
$ export FLASK_APP=src/fts.py
$ export FLASK_ENV=development

# For Windows
$ set FLASK_APP=src/fts.py
$ set FLASK_ENV=development

$ flask run
 * Running on http://127.0.0.1:5000/
```

## Building docker image ##

An alternative deployment method is building the Docker image or using the compiled one from Docker hub.  

For Windows and Mac is required [Docker Desktop](https://www.docker.com/products/docker-desktop) for Linux it can be installed through the packet manager of your distribution or by building manually the program.

From root of the repository execute the following command:

```bash
# For Linux
$ docker build -t fts4vmc -f docker/Dockerfile .
```

## Running the docker container ##

For manually built image:

```bash
# For Linux
$ docker run -p <host port>:5000 fts4vmc
```
For running image hosted on docker hub:

```bash
# For Linux
$ docker run -p <host port>:5000 gior26/fts4vmc
```
## Testing ##

From the root directory of FTS4VMC use the following command to launch all tests.

```bash
$ pip3 install pytest
$ pytest 
```