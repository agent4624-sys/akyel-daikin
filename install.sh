#!/bin/bash

echo "Kurulum başlıyor..."

sudo apt update
sudo apt install -y python3-pip ffmpeg

pip3 install numpy pillow opencv-python pyserial --break-system-packages

# mediamtx indir
cd /home/pi
wget https://github.com/bluenviron/mediamtx/releases/latest/download/mediamtx_linux_arm64.tar.gz
tar -xzf mediamtx_linux_arm64.tar.gz

# servis dosyaları
sudo cp akyel-daikin.service /etc/systemd/system/
sudo cp mediamtx.service /etc/systemd/system/

sudo systemctl daemon-reload
sudo systemctl enable akyel-daikin
sudo systemctl enable mediamtx

echo "Kurulum tamam!"
