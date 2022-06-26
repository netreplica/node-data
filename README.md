python3.9 -V
pip -V
python get-pip.py
pip -V
pip install virtualenv


mkdir -p ~/venv
cd ~/venv
export PYENV=host-data-poc39
python3.9 -m venv $PYENV; cd $PYENV; export PYENV_DIR=`pwd`
source "$PYENV_DIR/bin/activate"

git clone <node-data-url>


source ~/venv/host-data-poc39/bin/activate
pip3 install -r node-data/requirements.txt

python3 node-data/get_node_data.py
cd node-data
FLASK_APP=node_data flask run --host=0.0.0.0