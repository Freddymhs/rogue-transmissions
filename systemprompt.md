# systemprompt.md · ARG_CHECK

> Loop operacional para detectar nuevas transmissions del endpoint
> `/en-us/partial-capture` de `starcraft.blizzard.com/en-us/`.
> Append-only. SSOT = `data/transmissions.json`. Output = `index.html` regenerado.

**Estado actual: site publicado.** Repo `Freddymhs/rogue-transmissions`,
GitHub Pages activo en `https://freddymhs.github.io/rogue-transmissions/`.

---

## Pre-loop setup (una vez)

```bash
# 1. Repo GitHub — ya creado (rogue-transmissions)
gh repo create rogue-transmissions --public --source=. --remote=origin --push
# (ya hecho)

# 2. GitHub Pages — ya activado
#    github.com/Freddymhs/rogue-transmissions → Settings → Pages
#    Source: "Deploy from a branch" → Branch: main → Folder: / (root)
#    (ya hecho vía gh api POST /pages)

# 3. Sin cookie file. MCP browser session maneja auth.
#    Si MCP browser deslogueado: re-login manual + cookie extraído vía
#    browser_run_code_unsafe (ver §Loop sequence paso 1).

# 4. Validar antes del primer fetch
make test           # 11/11 deben pasar
make render         # regenera index.html desde JSON actual
git add -A && git commit -m "validate setup"
git push origin main
```

---

## State

```
data/transmissions.json     ← append-only, una entry por fetch nuevo
.last-hash                  ← sha256 del último body visto (diff detection)
.fetch.log                  ← log cronológico (timestamp + evento)
index.html                  ← regenerado por render.py (gitignored)
```

**Source of truth: `data/transmissions.json`.** `index.html` se regenera;
no editarlo a mano.

---

## Loop sequence (MCP browser path)

```
1. browser_run_code_unsafe: GET /en-us/partial-capture con Playwright MCP
   - Si cookies expiraron en MCP browser → log "cookie expired", exit
2. Parse JSON body
3. Si data.messages vacío → gate (CONNECTION BREACHED u otro) → no-op, exit
4. sha256(body) vs .last-hash
   - Si igual → no change, no-op, exit
5. Append entry a data/transmissions.json (día actual, último bloque)
6. Update .last-hash
7. python3 render.py → regenera index.html
8. git add -A && git commit -m "ARG: transmission XX @ YYYY-MM-DD HH:MM UTC"
9. NOT push (regla no-auto-push)
10. Append line a .fetch.log
```

---

## Prompt (copy-paste para `/loop`)

```
/loop 6h

Use Playwright MCP browser_run_code_unsafe to GET
https://starcraft.blizzard.com/en-us/partial-capture (browser session
is authenticated). If MCP browser cookies expired, stop and report.

Parse JSON response. If data.messages is empty (gate: CONNECTION BREACHED
or any other), exit silently.

Else:
  - sha256 of body. If equal to ~/starcraft-arg/.last-hash → exit silently.
  - Append entry to ~/starcraft-arg/data/transmissions.json (today UTC):
      {time: "HH:MM", type: "found", label: "transmission XX",
       title: "Transmission XX — N mensajes",
       body_html: "<pre class=\"memo\">...</pre>"}
    Dedupe: skip if last entry has same label.
  - Update .last-hash.
  - python3 render.py (regenerate index.html).
  - git add -A && git commit -m "ARG: transmission XX @ UTC".
  - Append to ~/starcraft-arg/.fetch.log: "[ISO] NEW transmission XX".
  - Report one line: "ARG: transmission XX · N mensajes".

Never git push. Report to chat.
```

---

## Output spec

| Evento | .fetch.log | Chat al usuario |
|---|---|---|
| Diff nuevo | `[ts] NEW transmission XX` | `ARG: transmission XX · N mensajes` |
| Sin cambio | `[ts] no change` | (silencio) |
| Gate (BREACHED, etc.) | `[ts] gated` | (silencio) |
| Cookie MCP expirada | `[ts] cookie expired` | `ARG: cookie expirada — re-login en browser` |
| Network error | `[ts] network: {error}` | `ARG: network error` |
| Render falló | `[ts] render failed` | `ARG: render failed — revisar transmissions.json` |
| Git commit failed | `[ts] git commit failed` | (commit local igual queda) |

**No notificar** si el run fue no-op (gated o sin cambio).

---

## Failure modes & recovery

| Failure | Causa probable | Recovery |
|---|---|---|
| Gate persistente (BREACHED) | Cookie MCP expiró o IP bloqueada | Re-login en MCP browser; alternar `make fetch` con cookie file |
| Network timeout | Blizzard caído o rate-limit | Reintentar próxima wake |
| Render.py crash | JSON corrupto o entry malformada | `python3 -c "import json; json.load(open('data/transmissions.json'))"` para validar; restaurar desde `git log -- data/transmissions.json` |
| Git commit fail | Permisos o branch protection | `git status` para diagnosticar; el diff queda en working tree |
| transmission number stale | Endpoint rota el `transmission` field | Si transmisión no es `"01"` ni `"02"`, documentar cambio |

---

## Lo que NO debe hacer

- **NO push** a git remoto (regla no-auto-push)
- **NO inventar** contenido si el endpoint falla o está gated
- **NO editar** entries previas (append-only)
- **NO borrar** `.last-hash` para forzar re-detección
- **NO escribir** análisis técnico en `transmissions.json` (sin headers HTTP, sin DevTools trivia, sin RUM/GA/Lit/CDN)
- **NO especular** sobre lore sin evidencia del endpoint
- **NO romper schema** JSON — `transmissions.json` debe parsear
- **NO skip render.py** — siempre regenerar index.html después de append
- **NO usar cron** — solo `/loop`

---

## Lo que SÍ debe hacer

- Append entries con timestamps UTC
- Usar pre-class apropiado: `memo` (texto clasificado), `sensor` (sensores), `medical` (vital signs), `json` (estructuras), `binary` (binary decoded)
- Decodificar binary messages con split whitespace + parseInt(chunk, 2)
- Preservar `██████` blocks exactos (no reemplazar con placeholders)
- Respetar día actual UTC, no local time del user
- Deduplicar si mismo transmission vuelve

---

## Probing checklist (correr cuando hay tiempo, no cada loop)

- [ ] Probar `/de-de/partial-capture`, `/ko-kr/partial-capture` — ¿idioma cambia contenido?
- [ ] Probar paths alternativos: `/redacted`, `/classified`, `/transmission-02`, `/transmission-03`
- [ ] Probar sin cookie con `Origin: https://starcraft.blizzard.com` — ¿header anti-CSRF?
- [ ] Comparar sha256 entre timestamps distantes — ¿mismo SHA → contenido cacheado?
- [ ] Disparar fetch sin reload manual vs después de N segundos de inactividad

Hallazgos no triviales → agregar a `transmissions.json` como `hallazgo`.
Resultados ambiguos → `~/starcraft-arg/.probes.log`.

---

## Files

```
arg_fetch.py            ← fallback headless (urllib + cookie file)
data/transmissions.json ← SSOT append-only
render.py               ← JSON → HTML
template.html           ← CSS + skeleton
index.html              ← output (regenerado)
tests/test_decode.py    ← unit decoder
tests/test_render.py    ← JSON schema + render idempotente
Makefile                ← make test/render/fetch/commit/serve/clean/ci
.git/hooks/pre-push     ← corre tests antes de push
.github/workflows/ci.yml ← CI GitHub Actions
systemprompt.md         ← este archivo (loop spec)
```

---

## Honestidad

- MCP browser cookie expira → loop falla silent hasta re-login
- Si Blizzard decide cerrar ARG → loop no-op perpetuo, .fetch.log crece sin entradas
- Si querés saber "qué pasó en la última semana", `tail .fetch.log`
