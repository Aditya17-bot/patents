"""Replace the threshold annotation of Figure 11 with the best-method thresholds."""
from PIL import Image, ImageDraw, ImageFont
import matplotlib, os

src = "orig/x/word/media/image12.png"
im = Image.open(src).convert("RGB")
px = im.load()
BAND = (244, 244, 244)
for x in range(240, 512):
    for y in range(25, 125):
        px[x, y] = px[530, y]
d = ImageDraw.Draw(im)
fdir = os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data", "fonts", "ttf")
f = ImageFont.truetype(os.path.join(fdir, "DejaVuSans.ttf"), 21)
x0, k = 223.0, 586.0


def vdash(x, color):
    y = 22
    while y < 910:
        d.line([(x, y), (x, min(y + 12, 910))], fill=color, width=3)
        y += 20


vdash(x0 + 0.30 * k, (176, 58, 46))
vdash(x0 + 0.75 * k, (168, 116, 26))
def label(x, y, t, col, anchor):
    bb = d.textbbox((x, y), t, font=f, anchor=anchor)
    d.rectangle([bb[0] - 4, bb[1] - 3, bb[2] + 4, bb[3] + 3], fill=(255, 255, 255))
    d.text((x, y), t, font=f, fill=col, anchor=anchor)


label(390, 42, "admissible θ: 0.018–0.559", (90, 100, 110), "mm")
label(408, 78, "θ = 0.30", (176, 58, 46), "lm")
label(672, 78, "θ_esc = 0.75", (168, 116, 26), "lm")
os.makedirs("figs", exist_ok=True)
im.save("figs/fig11.png")
print("wrote figs/fig11.png")
