#!/usr/bin/env python3
"""
Kartlagger ALLA falt som forekommer i garagedata.json, inte bara i forsta posten.
Letar sarskilt efter falt som kan innehalla realtidsdata om lediga platser.

Anvandning:
    python3 inspect_garage.py data/garagedata.json
"""
import sys, json, collections

path = sys.argv[1] if len(sys.argv) > 1 else 'data/garagedata.json'
data = json.load(open(path, encoding='utf-8'))
print(f'Antal anlaggningar: {len(data)}\n')

# ── Alla faltnamn och hur ofta de forekommer ──
counts = collections.Counter()
for rec in data:
    counts.update(rec.keys())

print('=' * 62)
print('SAMTLIGA FALT')
print('=' * 62)
for name, n in sorted(counts.items()):
    andel = n / len(data) * 100
    print(f'  {name:<40} {n:>5} poster ({andel:.0f}%)')

# ── Falt som kan rora realtid ──
NYCKELORD = ['ledig', 'free', 'avail', 'belag', 'occup', 'aktuell', 'realtid', 'status']
traffar = [f for f in counts if any(k in f.lower() for k in NYCKELORD)]

print()
print('=' * 62)
print('MOJLIGA REALTIDSFALT')
print('=' * 62)
if traffar:
    for f in traffar:
        varden = [r.get(f) for r in data if r.get(f) is not None]
        unika = collections.Counter(map(str, varden))
        print(f'\n  {f}')
        print(f'    antal med varde: {len(varden)}')
        print(f'    exempel: {list(unika.items())[:8]}')
else:
    print('  Inga falt med lediga/free/available i namnet.')

# ── Ar kapacitetsfalten meningsfulla? ──
print()
print('=' * 62)
print('KAPACITET')
print('=' * 62)
for f in ['AntalBesokPlatser', 'AntalLaddplatserBesokBil',
          'AntalBesokPlatserRorelsehindrad', 'AntalBesokPlatserMc']:
    if f not in counts:
        continue
    v = [r.get(f) or 0 for r in data]
    nonzero = [x for x in v if x]
    print(f'  {f:<36} {len(nonzero):>5} med varde >0, summa {sum(nonzero):,}')

# ── Anlaggningstyper ──
print()
print('=' * 62)
print('ANLAGGNINGSTYPER')
print('=' * 62)
for t, n in collections.Counter(r.get('Anlaggningstyp') for r in data).most_common():
    print(f'  {str(t):<30} {n:>5}')

# ── Hela forsta posten med alla falt ──
print()
print('=' * 62)
print('EN POST MED FLEST FALT (rafullstandig)')
print('=' * 62)
rikast = max(data, key=lambda r: len(r))
print(json.dumps(rikast, ensure_ascii=False, indent=1)[:2500])
