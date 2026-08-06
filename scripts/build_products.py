#!/usr/bin/env python3
"""
Hämtar Adtraction-produktfeed, filtrerar och sparar som kompakt JSON.
Körs av GitHub Actions i garage-cache-repot.

Användning:
    python3 build_products.py <feed-url> <output.json>
    python3 build_products.py --file feed.xml <output.json>
"""
import sys, json, re, urllib.request
import xml.etree.ElementTree as ET

NS = {'g': 'http://base.google.com/ns/1.0'}

# Vilka produkttyper som ska visas, i prioritetsordning
KEEP_TYPES = ['wallbox']
MAX_PRODUCTS = 20


def text(item, tag, namespaced=True):
    el = item.find(f'g:{tag}', NS) if namespaced else item.find(tag)
    return (el.text or '').strip() if el is not None and el.text else ''


def parse_price(raw):
    """'5990 SEK' -> (5990, 'SEK')"""
    m = re.match(r'([\d\s.,]+)\s*([A-Z]{3})?', raw or '')
    if not m:
        return None, ''
    num = m.group(1).replace(' ', '').replace(',', '.')
    try:
        return int(float(num)), (m.group(2) or 'SEK')
    except ValueError:
        return None, ''


def format_price(value, currency):
    if value is None:
        return ''
    return f'{value:,}'.replace(',', ' ') + f' {currency}'


def build(xml_bytes):
    root = ET.fromstring(xml_bytes)
    products = []

    for item in root.findall('.//item'):
        ptype = text(item, 'product_type')
        if KEEP_TYPES and ptype not in KEEP_TYPES:
            continue
        if text(item, 'availability') != 'in_stock':
            continue

        link = text(item, 'link', namespaced=False)
        image = text(item, 'image_link')
        title = text(item, 'title', namespaced=False)
        if not (link and image and title):
            continue

        sale, sale_cur = parse_price(text(item, 'sale_price'))
        regular, reg_cur = parse_price(text(item, 'price'))

        products.append({
            'id': text(item, 'id'),
            'name': title,
            'brand': text(item, 'brand'),
            'price': format_price(sale or regular, sale_cur or reg_cur),
            'oldPrice': format_price(regular, reg_cur) if sale and regular and sale < regular else '',
            'sortPrice': sale or regular or 0,
            'image': image,
            'url': link,
        })

    products.sort(key=lambda p: p['sortPrice'])
    products = products[:MAX_PRODUCTS]
    for p in products:
        p.pop('sortPrice', None)
    return products


def main():
    args = sys.argv[1:]
    if args and args[0] == '--file':
        with open(args[1], 'rb') as f:
            data = f.read()
        out = args[2]
    else:
        req = urllib.request.Request(args[0], headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
        out = args[1]

    products = build(data)
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=1)
    print(f'Skrev {len(products)} produkter till {out}')


if __name__ == '__main__':
    main()
