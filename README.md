# FTS4VMC

Prototype for FTS4VMC user interface.

## Depency
Python 3.

To prevent damaging user's libraries it is suggested to install the required packages under a virtual environment.

```bash
$ pip install z3-solver pydot lrparsing Flask
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
