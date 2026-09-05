# systemprompt.md · ARG_CHECK

> Loop operacional para detectar nuevas transmissions del endpoint
> `/en-us/partial-capture` de `starcraft.blizzard.com/en-us/`.
> SSOT = `data/transmissions.json`. Output = `index.html`.

**Estado:** site publicado en `https://freddymhs.github.io/rogue-transmissions/`.

---

## Modelo

Agente IA corre periódicamente (Mac Mini, desatendido). El agente:
investiga el endpoint, parsea respuesta, detecta cambios, edita
`data/transmissions.json` (append-only), regenera `index.html`,
commitea, pushea.

Sin scripts externos. Sin `/loop`. El agente es el loop.

---

## State

```
data/transmissions.json     ← SSOT append-only
index.html                  ← regenerado por agente
.git/                       ← history local
```

---

## Lo que el agente SÍ hace

- Investiga endpoint Blizzard con browser/curl/lo que tenga disponible
- Append entries con timestamps UTC cuando detecta cambio
- Commit local + push a `origin main` (regla [no-auto-push] NO aplica acá,
  firestarter desatendido pushea)
- Reporta one-line a chat cuando hay cambio real

## Lo que el agente NO hace

- NO editar entries previas (append-only)
- NO inventar contenido si endpoint gated/falla
- NO borrar `.last-hash` para forzar re-detección
- NO escribir análisis técnico en `transmissions.json`
- NO especular lore sin evidencia

---

## Honestidad

- Endpoint gated / cookie expirada → agente loggea y sigue
- Si Blizzard cierra ARG → agente no-op perpetuo, sin entries nuevas
- "¿Qué pasó esta semana?" → `git log data/transmissions.json` + `cat data/transmissions.json | tail`
