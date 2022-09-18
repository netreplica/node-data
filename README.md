Prerequisites

```Shell
python3.9 -V
pip -V
python get-pip.py
pip -V
pip install virtualenv
```

Create venv environment

```Shell
mkdir -p ~/venv
cd ~/venv
export PYENV=host-data-poc39
python3.9 -m venv $PYENV; cd $PYENV; export PYENV_DIR=`pwd`
source "$PYENV_DIR/bin/activate"
```

Create venv environment for Jupyter

```Shell
mkdir -p ~/venv
cd ~/venv
export PYENV=host-data-jup39
python3.9 -m venv $PYENV; cd $PYENV; export PYENV_DIR=`pwd`
source "$PYENV_DIR/bin/activate"
```

Clone and initialize venv
```Shell
git clone <node-data-url>

source ~/venv/host-data-poc39/bin/activate
cd ~/netreplica/code/host-data-poc/node-data
pip3 install -r requirements.txt
```

Manual CLI run:

```Shell
python3 node_data.py <topology>
```

Run as a Flask app:

```Shell
source ~/venv/host-data-poc39/bin/activate
cd ~/netreplica/code/host-data-poc/node-data
FLASK_APP=node_data flask run --host=0.0.0.0
```



Run as a Jupyter notebook:
```Shell
source ~/venv/host-data-jup39/bin/activate
cd ~/netreplica/code/host-data-poc/node-data
pip3 install -r requirements.txt -r requirements_jupyter.txt
jupyter notebook --ip=0.0.0.0
```
