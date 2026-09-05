# StarCraft: Remastered ARG · Bitácora

Bitácora de descubrimiento de un ARG en `starcraft.blizzard.com/en-us/`.
La página oficial expone transmissions clasificadas del Terran Dominion cuando
el cliente tiene sesión Blizzard activa. Acá las capturamos, las decodificamos
y las publicamos como lore.

**Sitio en vivo:** https://freddymhs.github.io/rogue-transmissions/

---

## Estructura

```
data/transmissions.json    ← SSOT append-only (data)
template.html              ← CSS + skeleton HTML
render.py                  ← JSON + template → index.html
arg_fetch.py               ← fetch /partial-capture + decode + append (fallback)
tests/                     ← unit + integration tests
index.html                 ← output (regenerado por render.py)
```

**SSOT = `data/transmissions.json`.** Cualquier nueva entrada se agrega
acá, después `make render` regenera `index.html`.

## Workflow local

```bash
make test           # corre tests
make render         # regenera index.html
make fetch          # fetch + decode + append + commit local (NO push)
make serve          # preview local en http://localhost:8000
```

## Fetch — primario vs fallback

**Primario** (recomendado): Playwright MCP browser.
MCP session ya está autenticada en Blizzard, así que alcanza con
`browser_run_code_unsafe` apuntando a `/partial-capture`. Sin cookie file.

**Fallback** (`make fetch`): `arg_fetch.py` corre standalone con `urllib`.
Requiere `~/starcraft-arg/.blizzard-cookie` con cookies Blizzard
(extraído vía DevTools). Útil para cron/headless cuando MCP no disponible.

## Loop con `/loop` de Claude Code

```bash
/loop 6h Use Playwright MCP browser_run_code_unsafe to GET
https://starcraft.blizzard.com/en-us/partial-capture.
Parse JSON. If data.messages is non-empty: append to
~/starcraft-arg/data/transmissions.json (today UTC), python3 render.py,
git add -A, git commit -m "ARG: ..." (no push).
Report outcome one line or silent if gated.
```

## Reglas

- **No auto-push** — vos revisás commits locales y `git push origin main` manual
- **Sin análisis técnico en el doc** — solo lore + mystery
- **Hipótesis tagged "generada por IA"** — explícito en el render
- **Append-only** — entries previas no se editan

## Tests

```bash
make test
```

Cubre:
- `test_decode.py` — unit del decoder binario
- `test_render.py` — JSON schema, render idempotente, HTML válido

Pre-push hook corre ambos automáticamente. CI en GitHub Actions los corre
en cada push/PR.