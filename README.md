# FTS4VMC

Prototype for FTS4VMC user interface.

## Depency
Python 3.

To prevent damaging user's libraries it is suggested to install the required packages under a virtual environment.

```bash
$ pip install -r requirements.txt
```

## Structure

+ *fts.py*: this file contains the definitions of functions used to upload files and execute analysis also includes bindings between functions and URLs.  

+ *analyser.py*: this file implements the ambiguities analyser.  

+ *templates*: under this folder are contained the html files used.  

+ *static*: under this folder are contained static resources such as javascript and CSS files.  


## Usage

**WARNING**: Currently it is used the flask web server to deploy the application and it should be used only on localhost.

It is suggested to create a virtual environment using:
```bash
$ python3 -m venv venv
```

To activate the environment:
```bash
$ . venv/bin/activate
```

Launch app on Flask web server:
```bash
$ export FLASK_APP=fts.py
$ export FLASK_ENV=development
$ flask run
 * Running on http://127.0.0.1:5000/
```
<<<<<<< HEAD

## Building docker image

From root of the repository execute the following command:

```bash
$ docker build -t fts4vmc -f docker/Dockerfile .
```

## Running the docker container

For manually built image:

```bash
$ docker run -p <host port>:5000 fts4vmc
```
For running image hosted on docker hub:

```bash
$ docker run -p <host port>:5000 gior26/fts4vmc
```
=======
## Testing
In order to run the unit tests, refer to tests/README.md.

## Translator
A first working version of the translator is available (src/translator.py). At the moment it is not included
in any other module. To run:
```bash
$ python3 src/translator.py <path_to_file>
```
