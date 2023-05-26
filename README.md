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
cd ~/netreplica/code/host-data-poc
pip3 install -r node-data/requirements.txt
mkdir -p instance

cat > instance/node-data.cfg << EOF
ROOT='./clab'
SECRETS='instance/secrets.json'
EOF

touch instance/secrets.json
chmod 600 instance/secrets.json
cat > instance/secrets.json << EOF
{
  "linux":    {"username": "root", "password": "root"},
  "ceos":     {"username": "admin", "password": "admin"},
  "crpd":     {"username": "root", "password": "clab123"}
}
EOF
```

Development addons

```Shell
cd ~/venv
python3.9 -m venv host-data-poc39-dev
source ~/venv/host-data-poc39-dev/bin/activate
cd ~/netreplica/code/host-data-poc/node-data
pip3 install -r requirements.txt -r requirements_dev.txt
```

Manual CLI run. Note: if no `<topology>` parameter is provided, `node-data` will use `<root>/default` folder to locate `ansible-inventory.yml` file.

```Shell
source ~/venv/host-data-poc39/bin/activate
cd ~/netreplica/code/host-data-poc/node-data
python3 main.py -r <root> -t <topology>
```

Run as a Flask app:

```Shell
source ~/venv/host-data-poc39/bin/activate
cd ~/netreplica/code/host-data-poc/node-data
flask --app=nodedata run --host=0.0.0.0
```

Build for Prod server:

```Shell
cd ~/netreplica/code/host-data-poc/node-data
pip3 install -r requirements.txt -r requirements_prod.txt
pip install -e .
```

Run as prod

```Shell
cd ~/venv
export PYENV=host-data-prod
python3.9 -m venv $PYENV
source "$PYENV/bin/activate"
cd ~/netreplica/code/host-data-poc/node-data
pip3 install -r requirements.txt -r requirements_prod.txt
uwsgi --socket 127.0.0.1:5000 --protocol=http -w wsgi:app --master -p 4
```

Run as a Jupyter notebook:
```Shell
source ~/venv/host-data-jup39/bin/activate
cd ~/netreplica/code/host-data-poc/node-data
pip3 install -r requirements.txt -r requirements_jupyter.txt
jupyter notebook --ip=0.0.0.0
```
