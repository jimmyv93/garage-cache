#!/usr/bin/env python3
"""
Konverterar Adtraction-produktfeed (Google Merchant XML) till kompakt JSON.

Anvandning:
    python3 build_feed.py <url|--file path> <output.json> [flaggor]

Flaggor:
    --keep a,b,c     Behall endast dessa g:product_type
    --skip x,y       Hoppa over produkter vars titel matchar
    --limit N        Max antal produkter (default 20)
    --sort price|none
"""
import sys, json, re, urllib.request
import xml.etree.ElementTree as ET

NS = {'g': 'http://base.google.com/ns/1.0'}


def text(item, tag, namespaced=True):
    el = item.find(f'g:{tag}', NS) if namespaced else item.find(tag)
    return (el.text or '').strip() if el is not None and el.text else ''


def parse_price(raw):
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
    return f'{value:,}'.replace(',', '\u00a0') + f'\u00a0{currency}'


def build(xml_bytes, keep=None, skip=None, limit=20, sort='price'):
    root = ET.fromstring(xml_bytes)
    out = []

    for item in root.findall('.//item'):
        ptype = text(item, 'product_type')
        if keep and ptype not in keep:
            continue
        if text(item, 'availability') != 'in_stock':
            continue

        title = text(item, 'title', namespaced=False)
        link = text(item, 'link', namespaced=False)
        image = text(item, 'image_link')
        if not (title and link and image):
            continue
        if skip and any(s.lower() == title.lower() for s in skip):
            continue

        sale, sale_cur = parse_price(text(item, 'sale_price'))
        regular, reg_cur = parse_price(text(item, 'price'))
        current = sale or regular

        out.append({
            'id': text(item, 'id'),
            'name': title,
            'brand': text(item, 'brand'),
            'price': format_price(current, sale_cur or reg_cur),
            'oldPrice': format_price(regular, reg_cur) if sale and regular and sale < regular else '',
            'sortPrice': current or 0,
            'image': image,
            'url': link,
        })

    if sort == 'price':
        out.sort(key=lambda p: p['sortPrice'])
    out = out[:limit]
    for p in out:
        p.pop('sortPrice', None)
    return out


def main():
    args = sys.argv[1:]

    def flag(name, default=None):
        if name in args:
            return args[args.index(name) + 1]
        return default

    if not args or not args[0].strip():
        sys.exit('FEL: ingen feed-URL angavs. Kontrollera att repository-secreten ar satt.')

    if args[0] == '--file':
        source, out_path = args[1], args[2]
        data = open(source, 'rb').read()
    else:
        if not args[0].startswith(('http://', 'https://')):
            sys.exit(f'FEL: ogiltig URL: {args[0][:60]!r}')
        out_path = args[1]
        req = urllib.request.Request(args[0], headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()

    keep = [s.strip() for s in flag('--keep', '').split(',') if s.strip()] or None
    skip = [s.strip() for s in flag('--skip', '').split(',') if s.strip()] or None
    limit = int(flag('--limit', 20))
    sort = flag('--sort', 'price')

    items = build(data, keep=keep, skip=skip, limit=limit, sort=sort)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=1)
    print(f'Skrev {len(items)} produkter till {out_path}')


if __name__ == '__main__':
    main()
