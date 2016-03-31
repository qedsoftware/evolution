set -e

if [ ! -e ~/venv/ ]; then
	virtualenv -p /usr/bin/python3.5 ~/venv && echo ". ~/venv/bin/activate" >> ~/.bashrc
fi
. ~/venv/bin/activate
pip install --upgrade -e /vagrant/
pip install --upgrade python-prctl

cd /vagrant/
./manage.py migrate
