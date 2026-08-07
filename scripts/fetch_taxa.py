#!/usr/bin/env python3
"""
Hamtar taxeomraden (LTFRtaxa) fran Trafikkontorets WFS-tjanst.

Steg 1: GetCapabilities  -> lista tillgangliga lager
Steg 2: GetFeature       -> hamta taxelagret som GeoJSON
Steg 3: Rapportera storlek, antal ytor och attribut

Anvandning:
    python3 fetch_taxa.py <apikey> <output.geojson>
"""
import sys, json, gzip, io, urllib.request, urllib.error
import xml.etree.ElementTree as ET

BASE = 'https://openstreetgs.stockholm.se/geoservice/api/{key}/wfs'
UA = {'User-Agent': 'Mozilla/5.0 (stockholmsparkering.se datahamtning)'}


def get(url, timeout=120):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
    if raw[:2] == b'\x1f\x8b':
        raw = gzip.decompress(raw)
    return raw


def strip_ns(tag):
    return tag.split('}', 1)[-1]


def list_layers(base):
    """Hamta GetCapabilities och returnera alla FeatureType-namn."""
    url = f'{base}?service=WFS&version=1.1.0&request=GetCapabilities'
    print('--> GetCapabilities')
    raw = get(url)
    print(f'    svar: {len(raw):,} byte')

    try:
        root = ET.fromstring(raw)
    except ET.ParseError as e:
        print('    KUNDE INTE TOLKA XML. Forsta 600 tecken:')
        print(raw[:600].decode('utf-8', 'replace'))
        raise SystemExit(1)

    layers = []
    for ft in root.iter():
        if strip_ns(ft.tag) != 'FeatureType':
            continue
        name = title = ''
        for child in ft:
            t = strip_ns(child.tag)
            if t == 'Name':
                name = (child.text or '').strip()
            elif t == 'Title':
                title = (child.text or '').strip()
        if name:
            layers.append((name, title))
    return layers


def fetch_layer(base, typename, srs='EPSG:4326'):
    """Prova olika outputFormat tills nagot ger GeoJSON."""
    formats = ['application/json', 'json', 'GEOJSON', 'application/vnd.geo+json']
    for fmt in formats:
        url = (f'{base}?service=WFS&version=1.1.0&request=GetFeature'
               f'&typeName={typename}&outputFormat={fmt}&srsName={srs}')
        print(f'--> GetFeature outputFormat={fmt}')
        try:
            raw = get(url)
        except urllib.error.HTTPError as e:
            print(f'    HTTP {e.code}')
            continue
        except Exception as e:
            print(f'    fel: {e}')
            continue

        head = raw[:200].lstrip()
        if head.startswith(b'{'):
            print(f'    OK, {len(raw):,} byte JSON')
            return json.loads(raw)
        print(f'    inte JSON, borjar med: {head[:90]!r}')
    return None


def report(gj):
    feats = gj.get('features', [])
    print()
    print('=' * 58)
    print(f'Antal ytor: {len(feats)}')
    if not feats:
        return
    geo_types = {}
    for f in feats:
        g = (f.get('geometry') or {}).get('type', 'None')
        geo_types[g] = geo_types.get(g, 0) + 1
    print('Geometrityper:', geo_types)

    props = feats[0].get('properties', {})
    print(f'\nAttribut ({len(props)} st) pa forsta ytan:')
    for k, v in list(props.items())[:25]:
        s = str(v)
        print(f'   {k}: {s[:70]}')

    # Rakna koordinatpunkter -> avgor om forenkling behovs
    def count(coords):
        if not isinstance(coords, list):
            return 0
        if coords and isinstance(coords[0], (int, float)):
            return 1
        return sum(count(c) for c in coords)

    pts = sum(count((f.get('geometry') or {}).get('coordinates', [])) for f in feats)
    print(f'\nTotalt antal koordinatpunkter: {pts:,}')
    print('=' * 58)


def main():
    if len(sys.argv) < 3 or not sys.argv[1].strip():
        sys.exit('Anvandning: fetch_taxa.py <apikey> <output.geojson>')

    key, out = sys.argv[1].strip(), sys.argv[2]
    base = BASE.format(key=key)

    layers = list_layers(base)
    print(f'\nHittade {len(layers)} lager.')

    hits = [(n, t) for n, t in layers
            if 'taxa' in (n + t).lower() or 'avgift' in (n + t).lower()]

    print('\nLager som matchar taxa/avgift:')
    for n, t in hits:
        print(f'   {n}   ({t})')
    if not hits:
        print('   INGA. Forsta 40 lagren:')
        for n, t in layers[:40]:
            print(f'   {n}   ({t})')
        sys.exit(1)

    typename = hits[0][0]
    print(f'\nVal: {typename}')

    gj = fetch_layer(base, typename)
    if gj is None:
        sys.exit('Kunde inte hamta lagret som GeoJSON.')

    with open(out, 'w', encoding='utf-8') as f:
        json.dump(gj, f, ensure_ascii=False)

    import os
    print(f'\nSparade {out} ({os.path.getsize(out)/1024/1024:.2f} MB)')
    report(gj)


if __name__ == '__main__':
    main()
