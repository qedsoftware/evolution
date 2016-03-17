echo "Deployment script started"

USER=evolution # it may be hardcoded in some places

getent passwd $USER > /dev/null 2>&1
USER_EXISTS=$?

if [ $USER_EXISTS -eq 0 ]; then
  echo "The user already exists!"
else
  useradd -m $USER
fi

echo "Installing dependencies:"

export DEBIAN_FRONTEND=noninteractive

add-apt-repository -y ppa:fkrull/deadsnakes
apt-get update -y
apt-get install -y python3.5 python3.5-dev python-pip python3.5-venv

#virtualenv -p /usr/bin/python3.5 
