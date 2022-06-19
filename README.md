python -V
pip -V
python get-pip.py
pip -V
pip install virtualenv


mkdir -p ~/venv
cd ~/venv
export PYENV=host-data-poc
virtualenv -p python3 $PYENV; cd $PYENV; export PYENV_DIR=`pwd`
source "$PYENV_DIR/bin/activate"

git clone <node-data-url>
pip3 install -r node-data/requirements.txt

