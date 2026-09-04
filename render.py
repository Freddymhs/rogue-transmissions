#!/usr/bin/env python3
"""render.py — data/transmissions.json + template.html → index.html"""
import json, sys, html, pathlib, re

DIR = pathlib.Path(__file__).parent
DATA = DIR / "data" / "transmissions.json"
TEMPLATE = DIR / "template.html"
OUT = DIR / "index.html"


def esc(s: str) -> str:
    return html.escape(s, quote=False)


def render_entry(entry: dict) -> str:
    parts = [f'<div class="note {entry["type"]}">']
    badge_class = entry["type"] if entry["type"] != "plain" else ""
    badge = f'<span class="badge {badge_class}">{esc(entry["label"])}</span>' if entry.get("label") else ""
    parts.append(f'  <div class="when"><span>{esc(entry["time"])}</span>{badge}</div>')
    if entry.get("title"):
        parts.append(f'  <h3>{esc(entry["title"])}</h3>')
    parts.append(f'  {entry["body_html"]}')
    parts.append('</div>')
    return "\n".join(parts)


def render_day(day: dict) -> str:
    n = len(day["entries"])
    if n == 0:
        meta = "sin entradas"
    else:
        meta = f'{n} entrada{"s" if n != 1 else ""}'
        if day.get("transmission"):
            meta += f' · transmission {day["transmission"]}'
    open_attr = " open" if day.get("open") else ""
    parts = [f'<details class="day"{open_attr}>']
    parts.append('  <summary>')
    parts.append(f'    <span class="day-date">{esc(day["date"])}</span>')
    parts.append(f'    <span class="day-meta">{meta}</span>')
    parts.append('  </summary>')
    if n > 0:
        parts.append('  <div class="log">')
        for e in day["entries"]:
            parts.append("    " + render_entry(e))
        parts.append('  </div>')
    parts.append('</details>')
    return "\n".join(parts)


def render_mystery(items: list) -> str:
    return "\n".join(f"    <li>{item}</li>" for item in items)


def render_hypothesis(items: list) -> str:
    return "\n".join(
        f'    <li><strong>{esc(it["label"])} ({it["pct"]}%):</strong> {esc(it["text"])}</li>'
        for it in items
    )


def main() -> int:
    if not DATA.exists():
        print(f"error: {DATA} not found", file=sys.stderr)
        return 1
    if not TEMPLATE.exists():
        print(f"error: {TEMPLATE} not found", file=sys.stderr)
        return 1

    data = json.loads(DATA.read_text(encoding="utf-8"))
    template = TEMPLATE.read_text(encoding="utf-8")

    # Build blocks
    days_html = "\n".join(render_day(d) for d in data.get("days", []))
    mystery_html = render_mystery(data.get("mystery", []))
    hypothesis_html = render_hypothesis(data.get("hypothesis", []))

    # Compute the active transmission (latest day with one)
    transmission = "--"
    for d in reversed(data.get("days", [])):
        if d.get("transmission"):
            transmission = d["transmission"]
            break

    # Replace placeholders
    out = template
    out = re.sub(r"<!-- BEGIN_DAYS -->.*?<!-- END_DAYS -->",
                 f"<!-- BEGIN_DAYS -->\n{days_html}\n<!-- END_DAYS -->",
                 out, flags=re.DOTALL)
    out = re.sub(r"<!-- BEGIN_MYSTERY -->.*?<!-- END_MYSTERY -->",
                 f"<!-- BEGIN_MYSTERY -->\n{mystery_html}\n<!-- END_MYSTERY -->",
                 out, flags=re.DOTALL)
    out = re.sub(r"<!-- BEGIN_HYPOTHESIS -->.*?<!-- END_HYPOTHESIS -->",
                 f"<!-- BEGIN_HYPOTHESIS -->\n{hypothesis_html}\n<!-- END_HYPOTHESIS -->",
                 out, flags=re.DOTALL)
    out = out.replace(
        '<span id="transmission">--</span>',
        f'<span id="transmission">{esc(transmission)}</span>',
    )

    OUT.write_text(out, encoding="utf-8")
    print(f"rendered {OUT} ({len(out)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())