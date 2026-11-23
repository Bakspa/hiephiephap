# Hiep Hiep Hap!

Website van **Hiep Hiep Hap!** – voor de leukste traktaties op school.

> **© Alle rechten voorbehouden.** Teksten, foto's, video's en het logo zijn
> auteursrechtelijk beschermd. Zie [LICENSE](LICENSE). Niet overnemen zonder
> schriftelijke toestemming via info@hiephiephap.nl.

## Waar staat wat?

| Wat | Waar |
|---|---|
| De website (wat gepubliceerd wordt) | `site/` |
| Pagina's | `site/index.html` (Over Hiep Hiep Hap!), `site/projecten/`, `site/over-ons/`, `site/contact/` |
| Foto's en logo | `site/wp-content/uploads/` |
| Opmaak (thema Twenty Seventeen) | `site/wp-content/themes/twentyseventeen/` |
| Publiceren | `.github/workflows/publiceren.yml` |
| Script waarmee de site uit WordPress is gehaald | `hulpmiddelen/bouw_uit_export.py` |

## Hoe is de site gemaakt?

De site is een statische kopie van de oude WordPress-site (export met de plugin
Simply Static, november 2026). Daarbij is:

- alleen overgenomen wat in het menu staat (Home, Projecten, Over ons, Contact);
  demo-pagina's van het thema zijn weggelaten;
- alles weggehaald wat zonder server niet werkt of niet nodig is: inloggen,
  zoeken, feeds, emoji-script en de demo-widgets in de footer;
- het contactformulier vervangen door een knop die een e-mail opent naar
  info@hiephiephap.nl (GitHub Pages kan geen formulieren versturen);
- elke foto opnieuw opgeslagen zonder metadata (zoals GPS-locatie) en maximaal
  2000 px breed; originelen in hoge resolutie staan **niet** in deze repo;
- YouTube ingesloten via `youtube-nocookie.com` (minder tracking);
- een copyrightvermelding in de footer gezet;
- `noindex, nofollow` behouden, zodat zoekmachines de site niet opnemen
  (net als op de oude site).

## Een tekst aanpassen

Open het juiste `index.html`-bestand in `site/`, zoek de tekst en pas die aan.
Doe dat via een eigen branch en een pull request. Na het mergen naar `main`
wordt de site binnen een paar minuten automatisch bijgewerkt.

## Publiceren

- *Settings → Pages → Source*: **GitHub Actions**.
- Adres: https://bakspa.github.io/hiephiephap/
- **Eigen domein (later):** vul in *Settings → Pages* `www.hiephiephap.nl` in,
  zet een bestand `site/CNAME` met `www.hiephiephap.nl` neer en laat bij de
  domeinregistrar een CNAME-record voor `www` naar `bakspa.github.io` wijzen
  (plus A-records voor het kale domein). Alle links in de site zijn relatief,
  dus er hoeft verder niets te veranderen.
