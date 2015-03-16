#!/bin/bash


# Config command
#lb config --image-name PiKake --apt-recommends false --debian-installer normal -b hdd --hdd-label PiKake -a amd64 --mode debian -d jessie --cache true --cache-packages true --archive-areas "main contrib non-free

mkdir -p /tmp/pikake/chroot
rm -f chroot
ln -s /tmp/pikake/chroot
