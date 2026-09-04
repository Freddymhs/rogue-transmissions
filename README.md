# StarCraft: Remastered ARG · Bitácora

Bitácora de descubrimiento de un ARG en `starcraft.blizzard.com/en-us/`.
La página oficial expone transmissions clasificadas del Terran Dominion cuando
el cliente tiene sesión Blizzard activa. Acá las capturamos, las decodificamos
y las publicamos como lore.

**Sitio en vivo:** https://fmarcosdev.github.io/starcraft-arg/ _(pendiente: crear repo + activar Pages)_

---

## Estructura

```
data/transmissions.json    ← SSOT append-only (data)
template.html              ← CSS + skeleton HTML
render.py                  ← JSON + template → index.html
arg_fetch.py               ← fetch /partial-capture + decode + append
tests/                     ← unit + integration tests
index.html                 ← output (regenerado por render.py)
```

**SSOT = `data/transmissions.json`.** Cualquier nueva entrada se agrega
acá, después `make render` regenera `index.html`.

## Workflow local

```bash
# una vez
make test           # corre tests
make render         # regenera index.html

# loop continuo (manual o cron)
make fetch          # fetch + decode + append + commit (NO push)

# antes de pushear
make test           # valida todo
make push           # vos decidís cuándo
```

## Setup inicial

1. **Cookie Blizzard** — exportar la cookie de sesión desde DevTools:
   - Abrí `starcraft.blizzard.com/en-us/`
   - DevTools → Network → `partial-capture` → Request Headers → copiá `Cookie:`
   - Pegá en `~/starcraft-arg/.blizzard-cookie` (gitignored)

2. **Repo + GitHub Pages:**
   ```bash
   cd ~/starcraft-arg
   git remote add origin git@github.com:fmarcosdev/starcraft-arg.git
   git push -u origin main
   ```
   Settings → Pages → Branch: `main`, folder: `/`.

3. **Cron opcional** (Mac Mini):
   ```cron
   0 */6 * * * cd ~/starcraft-arg && /usr/bin/python3 arg_fetch.py >> .fetch.log 2>&1
   ```

## Reglas

- **No auto-push** — vos revisás commits locales y pusheás manual
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