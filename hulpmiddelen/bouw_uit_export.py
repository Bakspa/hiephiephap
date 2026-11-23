#!/usr/bin/env python3
"""Zet een Simply Static-export van de WordPress-site om naar een schone
statische site voor GitHub Pages.

Gebruik:  python3 -I hulpmiddelen/bouw_uit_export.py <uitgepakte-export> <doelmap>

Wat het script doet:
- neemt alleen de echte pagina's over (Home, Projecten, Over ons, Contact);
- haalt WordPress-restanten weg (login, zoeken, feeds, emoji, demo-widgets,
  het Ninja Forms-contactformulier);
- maakt alle links relatief, zodat de site werkt op
  https://bakspa.github.io/hiephiephap/ en later op een eigen domein;
- kopieert alleen de bestanden die echt gebruikt worden;
- bewaart foto's opnieuw zonder metadata (EXIF/GPS) en zonder de grootste
  formaten (max. 2000 px breed).
"""
import re
import shutil
import sys
from pathlib import Path

from bs4 import BeautifulSoup, Comment
from PIL import Image

PAGINAS = {
    # bron in export        -> doel in site
    "index.html": "index.html",
    "projecten/index.html": "projecten/index.html",
    "over-ons-2/index.html": "over-ons/index.html",
    "contact/index.html": "contact/index.html",
}
PAD_HERNOEMD = {"/over-ons-2/": "/over-ons/"}
MAX_BREEDTE = 2000
JAAR = "2026"

FOOTER = (
    '<div class="site-info hhh-copyright">'
    f'<p>&copy; 2020&ndash;{JAAR} Hiep Hiep Hap! Alle rechten voorbehouden.</p>'
    "<p>Alle teksten, foto&rsquo;s en video&rsquo;s op deze site zijn auteursrechtelijk "
    "beschermd. Overnemen, kopi&euml;ren of hergebruiken (ook voor AI-training) "
    "is niet toegestaan zonder schriftelijke toestemming. "
    'Vragen? <a href="mailto:info@hiephiephap.nl">info@hiephiephap.nl</a></p>'
    "</div>"
)

CONTACT = (
    "<p>Wil je meer weten over het traktatieboek of de kook- en smaaklessen? "
    "Of wil je een afspraak maken? Stuur ons een e-mail, dan nemen we zo snel "
    "mogelijk contact met je op.</p>"
    '<p><a class="hhh-knop" href="mailto:info@hiephiephap.nl'
    '?subject=Vraag%20via%20hiephiephap.nl">Mail naar info@hiephiephap.nl</a></p>'
)

EXTRA_CSS = """
.hhh-copyright{font-size:.8rem;line-height:1.5;color:#666}
.hhh-copyright p{margin:0 0 .5em}
.hhh-knop{display:inline-block;padding:.7em 1.4em;background:#222;color:#fff!important;
  border-radius:4px;text-decoration:none!important;box-shadow:none!important}
.hhh-knop:hover{background:#767676}
"""


def stript_versie(url: str) -> str:
    return re.sub(r"\?ver=[^\"'\s)]*", "", url)


def normaliseer(url: str) -> str:
    """Maak van een absolute/test-URL een pad vanaf de root ('/…')."""
    url = re.sub(r"^https?://(test\.|www\.)?hiephiephap\.nl", "", url)
    url = stript_versie(url)
    for oud, nieuw in PAD_HERNOEMD.items():
        if url.startswith(oud):
            url = nieuw + url[len(oud):]
    return url


def relatief(url: str, diepte: int) -> str:
    if not url.startswith("/") or url.startswith("//"):
        return url
    voorvoegsel = "../" * diepte if diepte else "./"
    return voorvoegsel + url.lstrip("/")


class Bouwer:
    def __init__(self, bron: Path, doel: Path):
        self.bron, self.doel = bron, doel
        self.assets: set[str] = set()

    # ---- assets -------------------------------------------------------
    def registreer(self, pad: str) -> None:
        pad = pad.split("#")[0].split("?")[0]
        if pad.startswith("/wp-"):
            self.assets.add(pad)

    def kopieer_assets(self) -> None:
        # CSS kan zelf weer naar bestanden verwijzen (lettertypen).
        for pad in list(self.assets):
            if pad.endswith(".css"):
                tekst = (self.bron / pad.lstrip("/")).read_text(encoding="utf-8")
                for u in re.findall(r"url\(['\"]?([^'\")]+)", tekst):
                    if u.startswith("/"):
                        self.registreer(stript_versie(u))
        for pad in sorted(self.assets):
            src = self.bron / pad.lstrip("/")
            dst = self.doel / pad.lstrip("/")
            if not src.exists():
                print("ONTBREEKT:", pad)
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            if src.suffix.lower() in (".jpg", ".jpeg", ".png"):
                self.bewaar_foto(src, dst)
            elif src.suffix == ".css":
                tekst = src.read_text(encoding="utf-8")
                diepte = pad.lstrip("/").count("/")
                tekst = re.sub(
                    r"url\((['\"]?)(/[^'\")]+)",
                    lambda m: "url(" + m.group(1) + relatief(stript_versie(m.group(2)), diepte),
                    tekst,
                )
                dst.write_text(tekst, encoding="utf-8")
            else:
                shutil.copyfile(src, dst)

    def bewaar_foto(self, src: Path, dst: Path) -> None:
        with Image.open(src) as im:
            if im.width > MAX_BREEDTE:
                im = im.resize((MAX_BREEDTE, round(im.height * MAX_BREEDTE / im.width)))
            if src.suffix.lower() == ".png":
                im.save(dst, optimize=True)  # zonder tekst-/EXIF-chunks
            else:
                im.convert("RGB").save(dst, quality=85, optimize=True, progressive=True)

    # ---- html ---------------------------------------------------------
    def pagina(self, bron_pad: str, doel_pad: str) -> None:
        html = (self.bron / bron_pad).read_text(encoding="utf-8")
        s = BeautifulSoup(html, "html.parser")
        diepte = doel_pad.count("/")

        # WordPress-kop opruimen
        for sel in [
            'link[rel="EditURI"]', 'link[rel="profile"]', 'link[rel="canonical"]',
            'link[rel="shortlink"]', 'link[rel="alternate"]', 'link[rel="https://api.w.org/"]',
            'meta[name="generator"]', "#wp-emoji-styles-inline-css",
            'script[type="speculationrules"]', "#wp-emoji-settings",
        ]:
            for t in s.select(sel):
                t.decompose()
        for t in s.find_all("script"):
            src = t.get("src") or ""
            tekst = t.string or ""
            if (
                "ninja-forms" in src or "backbone" in src or "underscore" in src
                or (t.get("id") or "").startswith(("nf-", "tmpl-nf"))
                or "nfForms" in tekst or "wp-emoji-settings" in tekst
            ):
                t.decompose()
        for t in s.find_all("link", href=True):
            if "ninja-forms" in t["href"] or "dashicons" in t["href"]:
                t.decompose()
        for t in s.find_all("style"):
            if t.string and ".recentcomments" in t.string:
                t.decompose()
        for c in s.find_all(string=lambda x: isinstance(x, Comment)):
            if "page builders" in c:
                c.extract()

        # Footer: demo-widgets en "Ondersteund door WordPress" eruit, copyright erin
        for t in s.select("#colophon aside.widget-area, #colophon .site-info"):
            t.decompose()
        wrap = s.select_one("#colophon .wrap")
        if wrap:
            wrap.append(BeautifulSoup(FOOTER, "html.parser"))

        # Contact: Ninja Forms vervangen door mailto
        if bron_pad.startswith("contact/"):
            inhoud = s.select_one(".entry-content")
            inhoud.clear()
            inhoud.append(BeautifulSoup(CONTACT, "html.parser"))

        # Extra stijl
        stijl = s.new_tag("style", id="hhh-extra")
        stijl.string = EXTRA_CSS
        s.head.append(stijl)

        # YouTube zonder tracking-cookies
        for t in s.find_all("iframe", src=True):
            t["src"] = t["src"].replace("www.youtube.com/embed/", "www.youtube-nocookie.com/embed/")

        # Links en bronnen omzetten
        for t in s.find_all(True):
            for attr in ("href", "src", "content", "poster"):
                if attr in t.attrs and isinstance(t[attr], str):
                    waarde = t[attr]
                    if attr == "content" and not re.match(r"^(/|https?://(test\.|www\.)?hiephiephap)", waarde):
                        continue
                    n = normaliseer(waarde)
                    if n.startswith("/"):
                        self.registreer(n)
                        t[attr] = relatief(n, diepte)
            if "srcset" in t.attrs:
                delen = []
                for d in t["srcset"].split(","):
                    url, *w = d.strip().split()
                    if w and w[0].endswith("w") and int(w[0][:-1]) > MAX_BREEDTE:
                        continue
                    n = normaliseer(url)
                    self.registreer(n)
                    delen.append(" ".join([relatief(n, diepte), *w]))
                t["srcset"] = ", ".join(delen)
        # Inline scripts (bijv. instellingen van de headervideo) bevatten ook URL's
        for t in s.find_all("script"):
            if t.string and "hiephiephap.nl" in t.string:
                def vervang(m):
                    n = normaliseer(m.group(0).replace("\\/", "/"))
                    self.registreer(n)
                    return relatief(n, diepte)
                t.string = re.sub(r"https?:(?:\\?/){2}(?:test\.|www\.)?hiephiephap\.nl[^\"']*", vervang, t.string)

        uit = self.doel / doel_pad
        uit.parent.mkdir(parents=True, exist_ok=True)
        uit.write_text(str(s), encoding="utf-8")

    def bouw(self) -> None:
        for b, d in PAGINAS.items():
            self.pagina(b, d)
        self.kopieer_assets()
        (self.doel / ".nojekyll").write_text("")


if __name__ == "__main__":
    bron, doel = Path(sys.argv[1]), Path(sys.argv[2])
    if doel.exists():
        shutil.rmtree(doel)
    doel.mkdir(parents=True)
    Bouwer(bron, doel).bouw()
    print("Klaar:", doel)
