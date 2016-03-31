echo "Deployment script started"

USER=vagrant # it may be hardcoded in some places

echo "Installing dependencies:"

export DEBIAN_FRONTEND=noninteractive

# https://github.com/mitchellh/vagrant/issues/6051
bash <<EOB
add-apt-repository -y ppa:fkrull/deadsnakes
apt-get update -y
apt-get install -y python3.5 python3.5-dev python-pip python-virtualenv postgresql libpq-dev
EOB

su vagrant -c '/vagrant/setup_virtualenv.sh' -
