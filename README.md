# garage-cache

Hämtar automatiskt parkeringsdata från Stockholm Parkerings API var 10:e minut
och sparar som statisk JSON som kan läsas av externa tjänster.

## Filer

- `data/garagedata.json` — senaste datan från Stockholm Parkerings API
- `data/meta.json` — tidsstämpel för senaste uppdatering

## Rådata-URL (använd denna i chat.js)

Byt ut `DITT-ANVÄNDARNAMN` mot ditt GitHub-användarnamn:

```
https://raw.githubusercontent.com/DITT-ANVÄNDARNAMN/garage-cache/main/data/garagedata.json
```

## Manuell körning

Gå till Actions-fliken i GitHub och klicka "Run workflow" för att
trigga en omedelbar uppdatering.
