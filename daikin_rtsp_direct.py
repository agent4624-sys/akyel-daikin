import cv2
import numpy as np
import subprocess
import time
import threading
import serial
import json
import html
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 640, 480
FPS = 5

RTSP_URL = "rtsp://127.0.0.1:8554/daikin"
SERIAL_PORT = "/dev/ttyAMA0"
WEB_PORT = 80

rtsp_data = {}
web_data = {}
last_update = 0
lock = threading.Lock()

RTSP_LEFT = [
    ("01", "DIŞ HAVA SICAKLIĞI"),
    ("02", "BOYLER TANK SICAKLIĞI"),
    ("03", "ÇIKIŞ SUYU SICAKLIĞI - YIS"),
    ("04", "ÇIKIŞ SUYU SICAKLIĞI - YIÖ"),
    ("05", "LİKİT HATTI SICAKLIĞI"),
    ("06", "GİRİŞ SUYU SICAKLIĞI"),
    ("07", "SU AKIŞ HIZI DEBİ"),
    ("08", "SU BASINCI BAR"),
    ("09", "BOYLER HEDEF SICAKLIĞI"),
    ("10", "SU ÇIKIŞ HEDEF SICAKLIĞI"),
    ("11", "FAN 1 HIZI"),
    ("12", "SU POMPASI SİNYALİ"),
]

RTSP_RIGHT = [
    ("13", "ÇEVİRİCİ VANA"),
    ("14", "BOYLER TAKVİYE ISITICI"),
    ("15", "YEDEK ISITICI KADEMESİ 1"),
    ("16", "YEDEK ISITICI KADEMESİ 2"),
    ("17", "DEFROST İŞLEMİ"),
    ("18", "TERMOSTAT DURUMU"),
    ("19", "DONMA KORUMASI"),
    ("21", "HIZLI BOYLER ISITMA"),
    ("22", "ÇALIŞMA MODU"),
    ("23", "HATA KODU"),
    ("24", "DETAYLI HATA KODU"),
    ("25", "HATA TİPİ"),
]

RTSP_SENSORS = [
    ("01", "DIŞ HAVA SICAKLIĞI", 0x20, 0, 2, 105, "°C"),
    ("02", "BOYLER TANK SICAKLIĞI", 0x61, 10, 2, 105, "°C"),
    ("03", "ÇIKIŞ SUYU SICAKLIĞI - YIS", 0x61, 4, 2, 105, "°C"),
    ("04", "ÇIKIŞ SUYU SICAKLIĞI - YIÖ", 0x61, 2, 2, 105, "°C"),
    ("05", "LİKİT HATTI SICAKLIĞI", 0x61, 6, 2, 105, "°C"),
    ("06", "GİRİŞ SUYU SICAKLIĞI", 0x61, 8, 2, 105, "°C"),
    ("07", "SU AKIŞ HIZI DEBİ", 0x62, 9, 2, 105, "l/min"),
    ("08", "SU BASINCI BAR", 0x62, 11, 1, 156, "bar"),
    ("09", "BOYLER HEDEF SICAKLIĞI", 0x60, 7, 2, 105, "°C"),
    ("10", "SU ÇIKIŞ HEDEF SICAKLIĞI", 0x60, 9, 2, 105, "°C"),
    ("11", "FAN 1 HIZI", 0x30, 0, 1, 211, "rpm"),
    ("12", "SU POMPASI SİNYALİ", 0x62, 12, 1, 152, ""),
    ("13", "ÇEVİRİCİ VANA", 0x60, 12, 1, 306, ""),
    ("14", "BOYLER TAKVİYE ISITICI", 0x60, 12, 1, 305, ""),
    ("15", "YEDEK ISITICI KADEMESİ 1", 0x60, 12, 1, 304, ""),
    ("16", "YEDEK ISITICI KADEMESİ 2", 0x60, 12, 1, 303, ""),
    ("17", "DEFROST İŞLEMİ", 0x10, 1, 1, 304, ""),
    ("18", "TERMOSTAT DURUMU", 0x60, 2, 1, 303, ""),
    ("19", "DONMA KORUMASI", 0x60, 2, 1, 302, ""),
    ("21", "HIZLI BOYLER ISITMA", 0x62, 2, 1, 304, ""),
    ("22", "ÇALIŞMA MODU", 0x60, 2, 1, 315, ""),
    ("23", "HATA KODU", 0x60, 3, 1, 204, ""),
    ("24", "DETAYLI HATA KODU", 0x60, 4, 1, 152, ""),
    ("25", "HATA TİPİ", 0x60, 5, 1, 203, ""),
]

WEB_SENSORS = [
    ("01", "DIŞ HAVA SICAKLIĞI", 0x20, 0, 2, 105, "°C"),
    ("02", "BOYLER TANK SICAKLIĞI", 0x61, 10, 2, 105, "°C"),
    ("03", "ÇIKIŞ SUYU SICAKLIĞI - YIS", 0x61, 4, 2, 105, "°C"),
    ("04", "ÇIKIŞ SUYU SICAKLIĞI - YIÖ", 0x61, 2, 2, 105, "°C"),
    ("05", "LİKİT HATTI SICAKLIĞI", 0x61, 6, 2, 105, "°C"),
    ("06", "GİRİŞ SUYU SICAKLIĞI", 0x61, 8, 2, 105, "°C"),
    ("07", "SU AKIŞ HIZI DEBİ", 0x62, 9, 2, 105, "l/min"),
    ("08", "SU BASINCI BAR", 0x62, 11, 1, 156, "bar"),
    ("09", "İÇ ORTAM SICAKLIĞI", 0x61, 12, 2, 105, "°C"),
    ("10", "BOYLER HEDEF SICAKLIĞI", 0x60, 7, 2, 105, "°C"),
    ("11", "SU ÇIKIŞ HEDEF SICAKLIĞI", 0x60, 9, 2, 105, "°C"),
    ("12", "FAN 1 HIZI", 0x30, 0, 1, 211, "rpm"),
    ("13", "SU POMPASI SİNYALİ", 0x62, 12, 1, 152, ""),
    ("14", "ÇEVİRİCİ VANA", 0x60, 12, 1, 306, ""),
    ("15", "BOYLER TAKVİYE ISITICI", 0x60, 12, 1, 305, ""),
    ("16", "YEDEK ISITICI KADEMESİ 1", 0x60, 12, 1, 304, ""),
    ("17", "YEDEK ISITICI KADEMESİ 2", 0x60, 12, 1, 303, ""),
    ("18", "DEFROST İŞLEMİ", 0x10, 1, 1, 304, ""),
    ("19", "TERMOSTAT DURUMU", 0x60, 2, 1, 303, ""),
    ("20", "DONMA KORUMASI", 0x60, 2, 1, 302, ""),
    ("21", "HIZLI BOYLER ISITMA", 0x62, 2, 1, 304, ""),
    ("22", "ÇALIŞMA MODU", 0x60, 2, 1, 315, ""),
    ("23", "HATA KODU", 0x60, 3, 1, 204, ""),
    ("24", "DETAYLI HATA KODU", 0x60, 4, 1, 152, ""),
    ("25", "HATA TİPİ", 0x60, 5, 1, 203, ""),
    ("26", "KOMPRESÖR BASMA BORUSU SICAKLIĞI", 0x20, 4, 2, 105, "°C"),
    ("27", "EŞANJÖR ORTA SICAKLIĞI", 0x20, 8, 2, 105, "°C"),
    ("28", "SOĞUTUCU BLOK SICAKLIĞI", 0x20, 12, 2, 105, "°C"),
    ("29", "İNVERTER PRİMER AKIM", 0x21, 0, 2, 105, "A"),
    ("30", "İNVERTER SEKONDER AKIM", 0x21, 2, 2, 105, "A"),
    ("31", "N FAZI VOLTAJ", 0x21, 4, 2, 101, "V"),
    ("32", "İNVERTER FREKANSI", 0x30, 0, 1, 152, "rps"),
    ("33", "FAN 2 KADEMESİ", 0x30, 1, 1, 211, "rpm"),
    ("34", "SESSİZ MOD", 0x60, 2, 1, 301, ""),
]

ALL_SENSORS = RTSP_SENSORS + WEB_SENSORS

ser = serial.Serial(
    SERIAL_PORT,
    baudrate=9600,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_EVEN,
    stopbits=serial.STOPBITS_ONE,
    timeout=1
)

def crc(buf):
    return (~sum(buf)) & 0xFF

def clean_frame(raw, reg):
    b = bytes(raw)
    for i in range(len(b) - 4):
        if b[i] == 0x40 and b[i + 1] == reg:
            length = b[i + 2]
            total = length + 2
            frame = b[i:i + total]
            if len(frame) == total and crc(frame[:-1]) == frame[-1]:
                return frame
    return None

def query(reg):
    try:
        ser.reset_input_buffer()
        cmd = [0x03, 0x40, reg]
        cmd.append(crc(cmd))
        ser.write(bytearray(cmd))
        time.sleep(0.16)
        raw = ser.read(100)
        return clean_frame(raw, reg)
    except Exception:
        return None

def uval(raw, order):
    return int.from_bytes(raw, byteorder=order, signed=False)

def sval(raw, order):
    return int.from_bytes(raw, byteorder=order, signed=True)

def fmt_num(x):
    if isinstance(x, float):
        return str(round(x, 2)).rstrip("0").rstrip(".")
    return str(x)

def convert(conv, raw):
    if not raw:
        return "--"

    if conv == 101:
        return fmt_num(sval(raw, "little"))
    if conv == 105:
        return fmt_num(sval(raw, "little") * 0.1)
    if conv == 151:
        return fmt_num(uval(raw, "little"))
    if conv == 152:
        return fmt_num(uval(raw, "big"))
    if conv == 156:
        return fmt_num(uval(raw, "big") * 0.1)
    if conv == 200:
        return "OFF" if raw[0] == 0 else "ON"
    if conv == 203:
        return {0: "NORMAL", 1: "HATA", 2: "UYARI", 3: "DİKKAT"}.get(raw[0], "-")
    if conv == 204:
        a = " ACEHFJLPU987654"
        b = "0123456789AHCJEF"
        return a[(raw[0] >> 4) & 15] + b[raw[0] & 15]
    if conv == 211:
        return fmt_num(raw[0] * 10)
    if conv in (300, 301, 302, 303, 304, 305, 306, 307):
        bit = 1 << (conv % 10)
        return "ON" if raw[0] & bit else "OFF"
    if conv == 315:
        mode = raw[0] >> 4
        return {
            0: "KAPALI",
            1: "A.ISITMA",
            2: "SOĞUTMA",
            3: "??",
            4: "BOYLER",
            5: "A.ISITMA+BOYLER",
            6: "SOĞUTMA+BOYLER",
        }.get(mode, "-")

    return raw.hex(" ")

def normalize(no, val):
    s = str(val).strip()
    low = s.lower()
    if no in ("08", "20") and s.replace(".", "", 1).isdigit():
        return s
    if no in ("13", "26"):
        if low == "off":
            return "A.ISITMA"
        if low == "on":
            return "BOYLER"
    return s.upper()

def value_color(label, value):
    v = value.upper().strip()
    if v == "ON":
        return (0, 255, 80)
    if v == "OFF":
        return (255, 45, 45)
    if v in ("NORMAL", "0", "0.0"):
        return (0, 255, 80)
    if "HATA" in label and v not in ("0", "--", "NORMAL"):
        return (255, 45, 45)
    return (0, 230, 255)

def read_loop():
    global last_update
    regs = sorted({s[2] for s in ALL_SENSORS})

    while True:
        frames = {}
        ok = False

        for reg in regs:
            f = query(reg)
            if f:
                frames[reg] = f
            time.sleep(0.03)

        new_rtsp = {}
        for no, label, reg, offset, size, conv, unit in RTSP_SENSORS:
            frame = frames.get(reg)
            if not frame:
                continue
            start = offset + 3
            raw = frame[start:start + size]
            if len(raw) != size:
                continue
            val = convert(conv, raw)
            new_rtsp[no] = {"label": label, "value": val, "unit": unit}
            ok = True

        new_web = {}
        for no, label, reg, offset, size, conv, unit in WEB_SENSORS:
            frame = frames.get(reg)
            if not frame:
                continue
            start = offset + 3
            raw = frame[start:start + size]
            if len(raw) != size:
                continue
            val = convert(conv, raw)
            new_web[no] = {"label": label, "value": val, "unit": unit}
            ok = True

        with lock:
            rtsp_data.clear()
            rtsp_data.update(new_rtsp)
            web_data.clear()
            web_data.update(new_web)
            if ok:
                last_update = time.time()

        time.sleep(5)

def start_ffmpeg():
    return subprocess.Popen([
        "ffmpeg",
        "-loglevel", "warning",
        "-y",
        "-f", "rawvideo",
        "-pix_fmt", "bgr24",
        "-s", f"{WIDTH}x{HEIGHT}",
        "-r", str(FPS),
        "-i", "-",
        "-vf", "format=yuv420p",
        "-c:v", "libx264",
        "-profile:v", "baseline",
        "-level", "3.0",
        "-preset", "veryfast",
        "-threads", "1",
        "-g", "10",
        "-keyint_min", "10",
        "-sc_threshold", "0",
        "-bf", "0",
        "-x264-params", "keyint=10:min-keyint=10:scenecut=0:repeat-headers=1:bframes=0:sliced-threads=0:slices=1",
        "-b:v", "1600k",
        "-maxrate", "1600k",
        "-bufsize", "3200k",
        "-an",
        "-f", "rtsp",
        "-rtsp_transport", "tcp",
        RTSP_URL
    ], stdin=subprocess.PIPE)

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        return

    def do_GET(self):
        with lock:
            snapshot = dict(web_data)
            online = time.time() - last_update < 45

        if self.path == "/json":
            body = json.dumps(snapshot, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)
            return

        rows = ""
        for no in sorted(snapshot.keys(), key=lambda x: int(x)):
            item = snapshot[no]
            val = normalize(no, item["value"])
            unit = item["unit"]
            shown = f"{val} {unit}".strip() if unit and unit not in val else val
            rows += f"<tr><td>{html.escape(no)}</td><td>{html.escape(item['label'])}</td><td>{html.escape(shown)}</td></tr>"

        status = "ONLINE" if online else "OFFLINE"
        color = "#00ff55" if online else "#ff3333"

        page = f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="5">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AKYEL DAİKİN İZLEME</title>
<style>
body{{background:#101010;color:white;font-family:Arial;margin:0;padding:16px}}
h1{{color:#ffd400;text-align:center}}
.status{{text-align:center;font-size:22px;color:{color};font-weight:bold;margin-bottom:12px}}
.info{{text-align:center;color:#aaa;margin-bottom:16px}}
table{{width:100%;border-collapse:collapse;font-size:17px}}
th{{background:#333;color:#00eaff;padding:10px}}
td{{border:1px solid #555;padding:9px}}
tr:nth-child(even){{background:#222}}
tr:nth-child(odd){{background:#181818}}
td:nth-child(1){{width:70px;text-align:center;color:#ffd400}}
td:nth-child(3){{width:190px;text-align:center;color:#00eaff;font-weight:bold}}
a{{color:#ffd400}}
</style>
</head>
<body>
<h1>AKYEL DAİKİN İZLEME</h1>
<div class="status">{status}</div>
<div class="info">Saat: {time.strftime("%H:%M:%S")} | Toplam Parametre: {len(snapshot)} | <a href="/json">JSON</a></div>
<table>
<tr><th>NO</th><th>PARAMETRE</th><th>DEĞER</th></tr>
{rows}
</table>
</body>
</html>"""
        body = page.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body)

def web_loop():
    ThreadingHTTPServer(("0.0.0.0", WEB_PORT), Handler).serve_forever()

threading.Thread(target=read_loop, daemon=True).start()
threading.Thread(target=web_loop, daemon=True).start()

font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
font_title = ImageFont.truetype(font_path, 21)
font_top = ImageFont.truetype(font_path, 14)
font_header = ImageFont.truetype(font_path, 13)
font_row = ImageFont.truetype(font_path, 13)
font_value = ImageFont.truetype(font_path, 15)

ffmpeg = start_ffmpeg()

while True:
    img = Image.new("RGB", (WIDTH, HEIGHT), (10, 10, 10))
    d = ImageDraw.Draw(img)

    with lock:
        snapshot = dict(rtsp_data)
        online = time.time() - last_update < 45

    status = "ONLINE" if online else "OFFLINE"
    status_color = (0, 255, 0) if online else (255, 0, 0)

    d.rectangle((0, 0, WIDTH, 34), fill=(28, 28, 28))
    d.text((8, 8), status, font=font_top, fill=status_color)
    d.text((178, 4), "AKYEL DAİKİN İZLEME", font=font_title, fill=(255, 220, 0))
    d.text((520, 6), time.strftime("%H:%M:%S"), font=font_value, fill=(255, 255, 255))

    top = 36
    row_h = 35
    left_x = 5
    right_x = 330
    col_w = 305
    value_x_offset = 213

    def draw_column(x, col_items):
        d.rectangle((x, top, x + col_w, top + 24), fill=(55, 55, 55), outline=(170, 170, 170))
        d.text((x + 6, top + 5), "PARAMETRE", font=font_header, fill=(255, 220, 0))
        d.text((x + value_x_offset, top + 5), "DEĞER", font=font_header, fill=(0, 220, 255))

        y = top + 24
        for i, (no, label) in enumerate(col_items):
            bg = (22, 22, 22) if i % 2 == 0 else (40, 40, 40)
            d.rectangle((x, y, x + col_w, y + row_h), fill=bg, outline=(90, 90, 90))

            item = snapshot.get(no, {"value": "--", "unit": ""})
            value = normalize(no, item["value"])
            unit = item.get("unit", "")
            shown = f"{value} {unit}".strip() if unit and unit not in value else value
            color = value_color(label, value)

            d.text((x + 5, y + 9), label[:26], font=font_row, fill=(240, 240, 240))
            d.text((x + value_x_offset, y + 8), shown[:12], font=font_value, fill=color)
            y += row_h

    draw_column(left_x, RTSP_LEFT)
    draw_column(right_x, RTSP_RIGHT)

    frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

    try:
        ffmpeg.stdin.write(frame.tobytes())
        ffmpeg.stdin.flush()
    except Exception:
        try:
            ffmpeg.kill()
        except Exception:
            pass
        time.sleep(2)
        ffmpeg = start_ffmpeg()

    time.sleep(1 / FPS)
