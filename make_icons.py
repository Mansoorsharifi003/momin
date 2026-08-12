import os
from PIL import Image, ImageDraw

GOLD = (212, 175, 55)
GOLD_LIGHT = (245, 222, 138)
DARK = (23, 18, 8)

os.makedirs('ledger/static/ledger/icons', exist_ok=True)

def make_icon(size, path):
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # rounded dark background
    d.rounded_rectangle([0, 0, size, size], radius=int(size * 0.2), fill=DARK)

    s = size / 24.0  # scale from 24x24 gem
    lw = max(1, int(size * 0.02))

    gem = [(6,3),(18,3),(22,9),(12,22),(2,9)]
    gem = [(x*s, y*s) for x, y in gem]
    d.polygon(gem, fill=GOLD)

    # facet lines
    d.line([(2*s,9*s),(22*s,9*s)], fill=GOLD_LIGHT, width=lw)
    d.line([(6*s,3*s),(9*s,9*s)],  fill=GOLD_LIGHT, width=lw)
    d.line([(12*s,3*s),(10*s,9*s)],fill=GOLD_LIGHT, width=lw)
    d.line([(12*s,3*s),(14*s,9*s)],fill=GOLD_LIGHT, width=lw)
    d.line([(18*s,3*s),(15*s,9*s)],fill=GOLD_LIGHT, width=lw)
    d.line([(9*s,9*s),(12*s,22*s)],fill=GOLD_LIGHT, width=lw)
    d.line([(15*s,9*s),(12*s,22*s)],fill=GOLD_LIGHT, width=lw)
    d.line(gem + [gem[0]], fill=GOLD_LIGHT, width=lw)  # outline

    img.save(path)
    print('saved', path)

make_icon(192, 'ledger/static/ledger/icons/icon-192.png')
make_icon(512, 'ledger/static/ledger/icons/icon-512.png')