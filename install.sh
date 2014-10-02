# Install the requirements
sudo apt-get install -y matchbox
sudo apt-get install -y iceweasel
sudo apt-get install -y x11-xserver-utils
sudo apt-get install -y ttf-mscorefonts-installer
sudo apt-get install -y xwit
sudo apt-get install -y libnss3

cp root/etc/rc.local /etc/rc.local && chmod +x /etc/rc.local
cp root/boot/xinitrc /home/pi/.xinitrc && chown pi:pi /home/pi/.xinitrc
cp -r root/boot/.mozilla /boot/
