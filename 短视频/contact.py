# 把若干时刻的静帧拼成一张联系表：python3 contact.py 模块名 t1 t2 ...
import sys, os, importlib
mod = importlib.import_module(sys.argv[1])
ts = [float(s) for s in sys.argv[2:]]
from PIL import Image, ImageDraw
sc = 3
w, h = mod.W // sc, mod.H // sc
cols = min(5, len(ts))
rows = (len(ts) + cols - 1) // cols
sheet = Image.new("RGB", (cols * w, rows * (h + 24)), (30, 30, 30))
d = ImageDraw.Draw(sheet)
for k, t in enumerate(ts):
    im = mod.draw_frame(t).resize((w, h), Image.LANCZOS)
    x, y = (k % cols) * w, (k // cols) * (h + 24)
    sheet.paste(im, (x, y + 24))
    d.text((x + 6, y + 4), f"t={t}", fill=(255, 255, 255))
sheet.save(os.path.join(mod.HERE, "previews", "contact.png"))
