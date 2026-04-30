# AKYEL Daikin RTSP & Web Monitor

Daikin Altherma ısı pompası verilerini:

- 📺 RTSP stream (NVR kayıt)
- 🌐 Web arayüz (tüm parametreler Türkçe)

olarak yayınlayan Raspberry Pi projesi.

---

## 🚀 Özellikler

- 34 parametre web arayüzünde
- 24 parametre RTSP overlay
- Türkçe veri gösterimi
- MediaMTX RTSP server
- Otomatik başlatma (systemd)
- Düşük sistem kullanımı

---

## 📡 RTSP


---

## 🌐 Web


---

## 🔧 Kurulum

```bash
git clone https://github.com/KULLANICI_ADI/akyel-daikin.git
cd akyel-daikin
bash install.sh

X10A pin 2 → RX
X10A pin 3 → TX
X10A pin 5 → GND


