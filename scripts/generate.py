#!/usr/bin/env python3
"""Genera los SVG del perfil de GitHub (DonGeeo87) desde la API, sin servicios de terceros.

Uso local:  GH_TOKEN=$(gh auth token) python scripts/generate.py
En CI:      lo llama .github/workflows/update-profile.yml con secrets.GITHUB_TOKEN

Salida: assets/hero.svg, assets/stats.svg, assets/stack.svg, assets/activity.svg
Solo librería estándar. Determinista: si los datos no cambian, los archivos no cambian.
"""

import json
import os
import sys
import urllib.request
from datetime import date, datetime, timezone

USER = "DonGeeo87"
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets")

# Paleta Código Guerrero Dev
BG = "#0B0C0E"
CARD = "#121417"
BORDER = "#23272D"
GREEN = "#B8F35A"
CYAN = "#39BDF8"
TEXT = "#F7F8F8"
MUTED = "#8A8F98"
EMPTY = "#1A1D20"

FONT = "'Inter','Segoe UI',system-ui,-apple-system,'Helvetica Neue',Arial,sans-serif"
MONO = "'JetBrains Mono','SF Mono',ui-monospace,'Cascadia Code',Consolas,monospace"

QUERY = """
query($login: String!) {
  user(login: $login) {
    name
    login
    followers { totalCount }
    contributionsCollection {
      totalCommitContributions
      restrictedContributionsCount
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC) {
      totalCount
      nodes {
        stargazerCount
        primaryLanguage { name }
        languages(first: 12) { edges { size node { name } } }
      }
    }
  }
}
"""


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def gql(token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": f"{USER}-profile-readme",
        },
    )
    with urllib.request.urlopen(req, timeout=45) as r:
        payload = json.load(r)
    if "errors" in payload:
        sys.exit(f"GraphQL error: {payload['errors']}")
    return payload["data"]["user"]


def num(n):
    """1234 -> 1.234 (formato chileno)"""
    return f"{n:,}".replace(",", ".")


def frame(w, h, body, title):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" fill="none" role="img" aria-label="{esc(title)}">\n'
        f"<title>{esc(title)}</title>\n{body}\n</svg>\n"
    )


def hero():
    w, h = 1180, 300
    b = [
        f'<rect width="{w}" height="{h}" rx="16" fill="{BG}"/>',
        f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="15.5" stroke="{BORDER}"/>',
        # retícula tenue
        f'<g stroke="{BORDER}" stroke-width="1" opacity="0.55">',
    ]
    for x in range(40, w, 60):
        b.append(f'<path d="M{x} 0V{h}"/>')
    for y in range(40, h, 60):
        b.append(f'<path d="M0 {y}H{w}"/>')
    b.append("</g>")
    # bloque de acento
    b += [
        f'<rect x="0" y="0" width="6" height="{h}" rx="3" fill="{GREEN}"/>',
        f'<text x="56" y="86" font-family="{MONO}" font-size="14" letter-spacing="3" '
        f'fill="{GREEN}">CODIGO GUERRERO DEV</text>',
        f'<text x="56" y="150" font-family="{FONT}" font-size="52" font-weight="800" '
        f'fill="{TEXT}" letter-spacing="-1.5">Giorgio Interdonato</text>',
        f'<text x="56" y="190" font-family="{FONT}" font-size="21" font-weight="500" '
        f'fill="{MUTED}">Construyo productos digitales para negocios chicos.</text>',
        f'<text x="56" y="228" font-family="{FONT}" font-size="16" font-weight="400" '
        f'fill="{MUTED}">Web full-stack · Automatizacion con IA · Apps Android</text>',
    ]
    # chips
    chips = [("Limache, Chile", GREEN), ("codigoguerrero.dev", CYAN), ("abierto a proyectos", GREEN)]
    x = 56
    for label, color in chips:
        cw = 14 + len(label) * 8
        b += [
            f'<rect x="{x}" y="248" width="{cw}" height="28" rx="14" fill="{CARD}" stroke="{BORDER}"/>',
            f'<circle cx="{x + 14}" cy="262" r="4" fill="{color}"/>',
            f'<text x="{x + 26}" y="267" font-family="{FONT}" font-size="13" fill="{TEXT}">{esc(label)}</text>',
        ]
        x += cw + 10
    return frame(w, h, "\n".join(b), f"{USER} · Código Guerrero Dev")


def metric_card(x, y, w, h, value, label, color):
    return "\n".join([
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{CARD}" stroke="{BORDER}"/>',
        f'<rect x="{x}" y="{y}" width="4" height="{h}" rx="2" fill="{color}" opacity="0.9"/>',
        f'<text x="{x + 26}" y="{y + 56}" font-family="{FONT}" font-size="40" font-weight="800" '
        f'fill="{TEXT}" letter-spacing="-1.5">{esc(value)}</text>',
        f'<text x="{x + 26}" y="{y + 88}" font-family="{MONO}" font-size="12" letter-spacing="2" '
        f'fill="{MUTED}">{esc(label)}</text>',
    ])


def stats(user):
    repos = user["repositories"]
    stars = sum(n["stargazerCount"] for n in repos["nodes"])
    contrib = user["contributionsCollection"]["contributionCalendar"]["totalContributions"]
    followers = user["followers"]["totalCount"]

    w, h = 1180, 156
    gap = 16
    cw = (w - gap * 3) // 4
    cards = [
        (num(contrib), "CONTRIBUCIONES 12M", GREEN),
        (num(repos["totalCount"]), "REPOS PROPIOS", CYAN),
        (num(stars), "ESTRELLAS", GREEN),
        (num(followers), "SEGUIDORES", CYAN),
    ]
    body = [f'<rect width="{w}" height="{h}" rx="16" fill="{BG}"/>',
            f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="15.5" stroke="{BORDER}"/>']
    for i, (v, l, c) in enumerate(cards):
        body.append(metric_card(16 + i * (cw + gap), 16, cw, 124, v, l, c))
    return frame(w, h, "\n".join(body), "Estadísticas de GitHub")


def stack(user):
    totals = {}
    for n in user["repositories"]["nodes"]:
        for e in n["languages"]["edges"]:
            totals[e["node"]["name"]] = totals.get(e["node"]["name"], 0) + e["size"]
    grand = sum(totals.values()) or 1
    top = sorted(totals.items(), key=lambda kv: -kv[1])[:6]

    w, h = 1180, 300
    body = [
        f'<rect width="{w}" height="{h}" rx="16" fill="{BG}"/>',
        f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="15.5" stroke="{BORDER}"/>',
        f'<text x="32" y="50" font-family="{MONO}" font-size="13" letter-spacing="3" '
        f'fill="{GREEN}">STACK POR VOLUMEN DE CODIGO</text>',
        f'<text x="32" y="74" font-family="{FONT}" font-size="13" fill="{MUTED}">'
        f'Peso de cada lenguaje sumando el tamaño real de mis repositorios públicos</text>',
    ]
    bar_x, bar_w = 200, w - 200 - 120
    y = 108
    palette = [GREEN, GREEN, CYAN, CYAN, MUTED, MUTED]
    for i, (lang, size) in enumerate(top):
        pct = size / grand * 100
        fill_w = max(6, round(bar_w * pct / 100))
        color = palette[i] if i < len(palette) else MUTED
        body += [
            f'<text x="32" y="{y + 15}" font-family="{FONT}" font-size="15" font-weight="600" '
            f'fill="{TEXT}">{esc(lang)}</text>',
            f'<rect x="{bar_x}" y="{y}" width="{bar_w}" height="20" rx="10" fill="{EMPTY}"/>',
            f'<rect x="{bar_x}" y="{y}" width="{fill_w}" height="20" rx="10" fill="{color}" opacity="{0.95 - i * 0.12:.2f}"/>',
            f'<text x="{w - 32}" y="{y + 15}" text-anchor="end" font-family="{MONO}" font-size="13" '
            f'fill="{MUTED}">{pct:.1f}%</text>',
        ]
        y += 32
    return frame(w, h, "\n".join(body), "Lenguajes por volumen de código")


def activity(user):
    cal = user["contributionsCollection"]["contributionCalendar"]
    weeks = cal["weeks"]
    days = [d for wk in weeks for d in wk["contributionDays"]]
    peak = max((d["contributionCount"] for d in days), default=1) or 1

    cell, gap = 15, 5
    cols = len(weeks)
    grid_w = cols * (cell + gap)
    left, top = 64, 52
    w = left + grid_w + 56
    h = top + 7 * (cell + gap) + 58

    def level(c):
        if c == 0:
            return 0
        ratio = c / peak
        return 1 if ratio <= 0.15 else 2 if ratio <= 0.4 else 3 if ratio <= 0.7 else 4

    op = {0: 0, 1: 0.25, 2: 0.45, 3: 0.7, 4: 1.0}
    body = [
        f'<rect width="{w}" height="{h}" rx="16" fill="{BG}"/>',
        f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="15.5" stroke="{BORDER}"/>',
        f'<text x="24" y="32" font-family="{MONO}" font-size="13" letter-spacing="3" '
        f'fill="{GREEN}">ACTIVIDAD 12 MESES</text>',
        f'<text x="{w - 24}" y="32" text-anchor="end" font-family="{FONT}" font-size="13" '
        f'fill="{MUTED}">{num(cal["totalContributions"])} contribuciones</text>',
    ]
    # meses
    seen = set()
    for wi, wk in enumerate(weeks):
        first = wk["contributionDays"][0]["date"]
        m = MESES[datetime.strptime(first, "%Y-%m-%d").month - 1]
        key = (first[:7])
        if key in seen:
            continue
        seen.add(key)
        body.append(
            f'<text x="{left + wi * (cell + gap)}" y="{top - 10}" font-family="{FONT}" '
            f'font-size="11" fill="{MUTED}">{m}</text>'
        )
    # etiquetas de día
    for row, label in ((0, "L"), (2, "M"), (4, "V")):
        body.append(
            f'<text x="{left - 14}" y="{top + row * (cell + gap) + 11}" text-anchor="end" '
            f'font-family="{FONT}" font-size="11" fill="{MUTED}">{label}</text>'
        )
    for wi, wk in enumerate(weeks):
        for di, d in enumerate(wk["contributionDays"]):
            lv = level(d["contributionCount"])
            fill = EMPTY if lv == 0 else GREEN
            o = op[lv]
            opacity = f' opacity="{o}"' if lv else ""
            body.append(
                f'<rect x="{left + wi * (cell + gap)}" y="{top + di * (cell + gap)}" '
                f'width="{cell}" height="{cell}" rx="3" fill="{fill}"{opacity}><title>{d["date"]}: '
                f'{d["contributionCount"]}</title></rect>'
            )
    # leyenda
    ly = top + 7 * (cell + gap) + 18
    body.append(
        f'<text x="{left}" y="{ly + 11}" font-family="{FONT}" font-size="11" fill="{MUTED}">menos</text>'
    )
    lx = left + 46
    for lv in range(5):
        fill = EMPTY if lv == 0 else GREEN
        opacity = f' opacity="{op[lv]}"' if lv else ""
        body.append(f'<rect x="{lx}" y="{ly}" width="{cell}" height="{cell}" rx="3" fill="{fill}"{opacity}/>')
        lx += cell + 4
    body.append(
        f'<text x="{lx + 6}" y="{ly + 11}" font-family="{FONT}" font-size="11" fill="{MUTED}">más</text>'
    )
    return frame(w, h, "\n".join(body), "Mapa de actividad de los últimos 12 meses")


def main():
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("Falta GH_TOKEN. Local: GH_TOKEN=$(gh auth token) python scripts/generate.py")

    user = gql(token)
    os.makedirs(OUT, exist_ok=True)
    files = {
        "hero.svg": hero(),
        "stats.svg": stats(user),
        "stack.svg": stack(user),
        "activity.svg": activity(user),
    }
    changed = []
    for name, content in files.items():
        path = os.path.join(OUT, name)
        old = None
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                old = fh.read()
        if old != content:
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(content)
            changed.append(name)
    gen = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"generado {gen} · cambiaron: {changed or 'ninguno'}")


if __name__ == "__main__":
    main()
