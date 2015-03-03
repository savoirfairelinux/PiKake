
Installation
============


::

    sudo apt-ge install  matchbox

Get a Dev env
=============

::

    sudo apt-get install git python3  python3-pyqt5 python3-pyqt5.qtwebkit python3-setuptools python3-pip
    git clone git@github.com:savoirfairelinux/PiKake.git
    virtualenv -p python3.4 --system-site-packages env
    source env/bin/activate
    python3 setup.py develop
