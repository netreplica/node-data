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

Clond and initialize venv
```Shell
git clone <node-data-url>

source ~/venv/host-data-poc39/bin/activate
pip3 install -r node-data/requirements.txt
```

Manual CLI run:

```Shell
cd node-data
python3 node_data.py <topology>
```

Run as a Flask app:

```Shell
cd node-data
FLASK_APP=node_data flask run --host=0.0.0.0
```
