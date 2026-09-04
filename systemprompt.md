# systemprompt.md · ARG_CHECK

> Loop operacional para detectar nuevas transmissions del endpoint
> `/en-us/partial-capture` de `starcraft.blizzard.com/en-us/`.
> Append-only. SSOT = `data/transmissions.json`. Output = `index.html` regenerado.

**Estado actual: site NO publicado.** Repo local existe (`~/starcraft-arg/`),
sin remote, sin GitHub Pages. Antes del primer run, ver §Pre-loop setup.

---

## Pre-loop setup (una vez)

```bash
# 1. Repo GitHub (elegí nombre + visibility)
gh repo create starcraft-arg --public --source=. --remote=origin --push
# Si gh no autenticado, manual:
#   ir a github.com/new → crear repo → git remote add origin <url>

# 2. Activar GitHub Pages
#    github.com/<user>/starcraft-arg → Settings → Pages
#    Source: "Deploy from a branch" → Branch: main → Folder: / (root)
#    Save. Esperá ~30s. URL: https://<user>.github.io/starcraft-arg/

# 3. Cookie Blizzard
#    Abrí starcraft.blizzard.com/en-us/ en tu browser logueado
#    DevTools → Network → click cualquier request → Request Headers → Cookie
#    Copiá el valor completo de Cookie y pegá en archivo local:
echo "session=e30=...; session.sig=...; locale=en_US" > ~/starcraft-arg/.blizzard-cookie
chmod 600 ~/starcraft-arg/.blizzard-cookie

# 4. Validar antes del primer fetch
make test           # 11/11 deben pasar
make render         # regenera index.html desde JSON actual
git add -A && git commit -m "initial commit"
git push origin main

# 5. Esperá 1-2 min, refrescá https://<user>.github.io/starcraft-arg/
#    → debés ver la página renderizada con la paleta StarCraft
```

**Sin estos pasos el loop es no-op perpetuo.** Cookie vacía → gate 404. Repo
inexistente → git push falla. Pages no activado → site no sirve.

---

## State

```
data/transmissions.json     ← append-only, una entry por fetch nuevo
.last-hash                  ← sha256 del último body visto (diff detection)
.blizzard-cookie            ← cookie Blizzard session (gitignored)
.fetch.log                  ← log cronológico (timestamp + evento)
index.html                  ← regenerado por render.py (gitignored)
```

**Source of truth: `data/transmissions.json`.** `index.html` se regenera;
no editarlo a mano.

---

## Loop sequence

```
1. fetch /en-us/partial-capture con Cookie de .blizzard-cookie
2. sha256(body)
3. sha == .last-hash ? → no-op silent
4. body parseado con status != 200 ? → no-op silent (gated)
5. append entry a data/transmissions.json (día actual, último bloque)
6. update .last-hash
7. python3 render.py  → regenera index.html
8. git add -A && git commit -m "ARG: transmission {XX}"
9. NOT push (regla no-auto-push)
10. append line a .fetch.log
```

---

## Prompt (copy-paste para Claude o `/loop`)

```
ARG_CHECK

State read:
 - ~/starcraft-arg/.last-hash  (sha256 del último body)
 - ~/starcraft-arg/data/transmissions.json  (entries existentes)

Fetch:
 - GET https://starcraft.blizzard.com/en-us/partial-capture
 - Headers: Cookie de ~/starcraft-arg/.blizzard-cookie, Accept: application/json

Diff:
 - sha256(body) vs .last-hash
 - Si igual → no-op. Exit.
 - Si body parsea con status != 200 o message != "CONNECTION SUCCESSFUL"
   → no-op (gate activo). Exit.

Append (solo si diff):
 - Localiza el day-block con date == today (UTC) en transmissions.json
 - Si no existe, crealo al final con open:true
 - Append entry:
   {
     "time": "HH:MM",                   // UTC HH:MM del momento
     "type": "found",
     "label": "transmission XX",
     "title": "Transmission XX — {N} mensajes",
     "body_html": "<pre class=\"memo\">{texto decoded de messages[0..N]}</pre>"
   }
 - Deduplica: si la última entry tiene el mismo label, no append
 - Update transmissions.json (preservar indent 2, ensure_ascii=False)

Write:
 - .last-hash = nuevo sha256
 - python3 render.py   (regenera index.html desde JSON)
 - git add -A && git commit -m "ARG: transmission XX @ YYYY-MM-DD HH:MM UTC"

Log:
 - Append a .fetch.log:
   "[ISO] NEW transmission XX"  o  "[ISO] no change"  o  "[ISO] gated"

Output al chat:
 - Si new: "ARG: transmission XX · {N} mensajes"
 - Si no change: (silencio)
 - Si gated/error: "ARG: gate activo (cookie expirada o IP bloqueada)"

EXIT.
```

---

## Output spec

| Evento | .fetch.log | Chat al usuario |
|---|---|---|
| Diff nuevo | `[ts] NEW transmission XX` | `ARG: transmission XX · N mensajes` |
| Sin cambio | `[ts] no change` | (silencio) |
| Gate (404) | `[ts] gated` | `ARG: gate activo` |
| Cookie expirada | `[ts] cookie expired` | `ARG: cookie expirada — renová .blizzard-cookie` |
| Network error | `[ts] network: {error}` | `ARG: network error` |
| Render falló | `[ts] render failed` | `ARG: render failed — revisar transmissions.json` |
| Git commit failed | `[ts] git commit failed` | (commit local igual queda) |

**No notificar** si el run fue no-op (gated o sin cambio).

---

## Failure modes & recovery

| Failure | Causa probable | Recovery |
|---|---|---|
| Gate 404 persistente | Cookie Blizzard expiró (~30 días) | Re-login en browser, exportar Cookie header nueva, reemplazar `.blizzard-cookie` |
| Network timeout | Blizzard caído o rate-limit | Reintentar próxima corrida |
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

## Cron usage

```cron
0 */6 * * * cd ~/starcraft-arg && /usr/bin/python3 arg_fetch.py >> .fetch.log 2>&1
```

Cada 6h. Blizzard rota lento. Menos = OK. Más = ruido sin valor.

Loop más frecuente solo si transmission XX está cambiando en tiempo real
(detectable por cambios de sha256 entre corridas).

---

## Files

```
arg_fetch.py            ← implementación (entry point)
data/transmissions.json ← SSOT append-only
render.py               ← JSON → HTML
template.html           ← CSS + skeleton
index.html              ← output (regenerado)
tests/test_decode.py    ← unit decoder
tests/test_render.py    ← JSON schema + render idempotente
Makefile                ← make test/render/fetch/push/serve
.git/hooks/pre-push     ← corre tests antes de push
.github/workflows/ci.yml ← CI GitHub Actions
```

---

## Honestidad

- Cookie Blizzard expira → loop falla silent hasta renovar
- Sin cookie válida → endpoint siempre gated, loop nunca appends
- Si Blizzard decide cerrar ARG → loop no-op perpetuo, .fetch.log crece sin entradas
- Si querés saber "qué pasó en la última semana", `tail .fetch.log`