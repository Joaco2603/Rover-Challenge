# Plan de algoritmo (pensar, no programar)

Objetivo: una política que **siempre tiene siguiente paso**. “100% de los casos” acá significa: cada geometría y cada fallo típico tiene recuperación, y la FSM no se queda sin movimiento legal. No significa que las ruedas nunca patinen; significa que si patinan, se aborta y se vuelve a adquirir el cubo, no se insiste a ciegas.

Esto vive **después** de que la tubería funcione (visión, pose, go-to-pose). Hasta que ir a una celda no sea aburrido, este plan no se implementa.

## Quick path

1. Un cubo a la vez en todo el campo (token global).
2. Si el cubo no se puede atacar desde atrás, primero se saca al centro.
3. Empuje colineal rover–cubo–depot, lento, con aborto si el cubo se escapa de la línea.
4. Entrega con margen interno + retroceso para que la cámara confirme.
5. El segundo rover espera fuera de la cápsula. Si el que trabaja se pierde, el otro toma el token.
6. Paralelizar solo cuando dos cápsulas no se toquen. Eso es velocidad, no corrección.

## Invariantes (si se rompe uno, no es 100%)

| # | Invariante | Para qué |
| --- | --- | --- |
| I1 | A lo sumo un rover en ALIGN/PUSH | No se chocan ni se tapan dos cubos a la vez |
| I2 | Nunca empujar hacia afuera del tablero | Un cubo fuera es peor que un reintento |
| I3 | Nunca seguir un empuje si el cubo se desvía de la línea | El glance mata más rondas que ir lento |
| I4 | Un cubo en depot (margen interno) es terminal | No volver a tocarlo |
| I5 | Asignación = función pura del mundo + ids | Los dos cerebros calculan lo mismo aunque falle ESP-NOW |
| I6 | Pose propia vieja ⇒ frenar | No se navega a ciegas |
| I7 | Verificar entrega con el cubo **visible** (`age_ms` bajo) | Tapar el cubo no cuenta como gol |

El token no es un mensaje mágico. Cada rover, con el último JSON, calcula el mismo `cubo_activo` y el mismo `dueño`. ESP-NOW solo adelanta “estoy encima” y “estoy trabado”.

## Un cubo: la skill atómica `entregar`

El campo se trata como abierto (en esta edición `obstacles` viene vacío). Los únicos obstáculos son el otro rover, los otros cubos y el borde.

```
si en_depot_interno(cubo): éxito

si no hay pose de ataque válida (atrás del cubo, dentro de la cancha):
    EXTRAER hacia el centro hasta que sí la haya
si no:
    ir al standoff → alinear → EMPUJAR por la recta cubo→depot

en EMPUJAR:
    el cubo tiene que moverse con el rover
    si error lateral > ε: abortar, retroceder, recalcular
    si el cubo entra al margen interno: parar, retroceder, VERIFY
```

Pose de ataque: en la recta depot ← cubo, a ~12–18 cm detrás del cubo, mirando al depot. Unidad: celdas float. `drow = -sin(theta)`.

Modo de contacto: **empuje frontal colineal**. Meter un cubo en una esquina no deja espacio para un barrido lateral. Las paletas laterales son red de seguridad si el cubo se escapa al costado, no el plan principal.

Go-to-standoff: línea recta si la cápsula (rover inflado) no pisa otro cubo, al otro rover ni el borde. Si pisa: waypoint en el centro de la cancha y de ahí al standoff.

## Predicados

Calcularlos del último mensaje, sin memoria rara salvo “última pose conocida” que ya trae la visión.

| Predicado | Definición operativa |
| --- | --- |
| `en_depot_interno(c)` | Cubo de 6 cm **entero** dentro de un AABB chico en la esquina de su color, con margen por ruido de visión. Calibrar el AABB en la cancha; no adivinarlo. |
| `pendiente(c)` | No `en_depot_interno` |
| `standoff_legal(c)` | La pose de ataque está dentro de la cancha inflada y no coincide con otro cuerpo |
| `cluster(c1,c2)` | Distancia menor a ~2 radios de cubo + margen |
| `yo_tapo(c)` | `age_ms` alto **y** estoy a distancia de contacto de la última pose del cubo |
| `progreso` | Distancia cubo→depot baja, o el cubo se acercó al centro en EXTRAER |

Si no hay `progreso` en N segundos: RECOVER (parar, retroceder, reasignar). Eso evita el loop infinito de empujar contra la nada.

## Qué cubo toca (determinista)

Entre los `pendiente`:

1. Si hay cluster, la acción global es **separar**: apartar el cubo más fácil hacia un parking (punto abierto, lejos de depots y del cubo activo), no entregar todavía.
2. Si no, el cubo cuya distancia a **su** depot es menor (cerrar los que ya casi están, para no tirarlos).
3. Empate: orden fijo de color `blue < green < red`.
4. Dueño del token: rover más cercano al standoff de ese cubo. Empate: ArUco de id menor.
5. El otro rover va a `wait_point`: fuera de la cápsula de empuje, fuera de todos los depots, de ser posible cerca de la salida.

Un cubo ya en su depot no se elige. Un cubo en el depot **equivocado** es `pendiente`: extraer al centro y entregar al color correcto.

Si solo queda un rover fresco (el otro `age_ms` alto o no aparece): ese rover es dueño de todo. El algoritmo de un cubo no cambia.

## Catálogo de casos

Cada fila tiene acción. Si aparece un caso sin fila, el plan está incompleto.

| Caso | Qué hacer |
| --- | --- |
| Cubo en campo abierto, standoff libre | Entregar en línea |
| Cubo pegado a una pared, atrás = fuera | EXTRAER al centro, después entregar |
| Cubo en una esquina (incluida la de salida) | Empujar hacia el interior, nunca “desde atrás” contra la pared |
| Cubo casi en su depot, no del todo | Micro-empuje por la diagonal **hacia adentro** de la esquina, margen interno, VERIFY |
| Cubo en depot correcto | No tocarlo (I4) |
| Cubo en depot de otro color | EXTRAER al centro, luego depot propio |
| Dos cubos juntos | SEPARAR: apartar uno a parking, después entregar el otro |
| Tres cubos en el medio | Parking de a uno hasta que las rectas a depot no se crucen con otro cubo |
| Otro cubo en la recta de empuje | No empujar a través. Parking del que estorba, o EXTRAER el activo fuera de la recta |
| Otro rover en la cápsula | El dueño espera o el que estorba va a `wait_point` |
| Cubo se escapa a un costado | Abortar (I3), recaptura corta con paleta si está al lado, re-standoff |
| Cubo no se mueve y el rover sí | Perdiste contacto: abortar, no acelerar |
| `age_ms` del cubo alto y yo encima | Seguir última pose, más lento; al VERIFY hay que destaparlo |
| `age_ms` del cubo alto y yo lejos | No correr hacia un fantasma; acercarse a la última pose y parar a mirar |
| Mi `age_ms` o latencia altos | Frenar (I6) |
| `phase != RUNNING` | Frenar ya, incluso a mitad de empuje |
| Overshoot, cubo pasó el depot | No seguir. Rodear por el interior y empujar **hacia** la esquina, no hacia afuera |
| Cubo cerca del borde exterior | Primero al centro (I2), después al depot |
| Un rover muerto / trabado | Timeout de progreso → el otro toma todos los pendientes |
| Los dos calculan dueños distintos un frame | Gana la regla de empate (id menor); no “reclamar más fuerte” |
| Visión tira el cubo un salto | Filtro: ignorar saltos mayores a X cm en un frame salvo que yo lo estuviera empujando |
| 2 cubos en juego, no 3 | La misma política; `pendiente` tiene 2 |

## Dos rovers

Para que sea 100%, el segundo rover **no es un segundo empujador libre**. Es un relevo.

```
cada frame:
    cubo_activo, dueño = asignar(mundo)   # puro
    si yo soy dueño: entregar(cubo_activo)
    si no: ir a wait_point y quedarme
    si soy dueño y no hay progreso: soltar (el otro va a ganar la regla)
```

Cuando `entregar` de un cubo verifica I7, ese cubo sale de `pendiente` y la función pura elige el siguiente. No hace falta un líder.

Paralelismo (después, opcional): dos `entregar` a la vez **solo si** las cápsulas infladas no se intersectan y ningún depot es compartido en ese instante. Si la predicado falla, se vuelve a un token. No diseñar el 100% encima de este atajo.

## Qué no hacer

- Los dos al cubo más cercano (carrera, choque, oclusión doble).
- Empujar “un poquito más fuerte” cuando el cubo no sigue.
- Planificar en celdas enteras (se tira la mitad de una celda).
- Asumir esquina por color; el depot se lee del mensaje.
- A* pesado en el ESP32: con obstáculos vacíos, recta + centro alcanza.
- Barrido lateral como plan A: no entra en la esquina del depot.

## Cómo saber que el plan cubre el 100%

Antes de codear el juego, recorrer el catálogo en papel o en el simulador (mover cubos a pared, esquina, cluster, depot incorrecto) y marcar que cada fila termina en `en_depot_interno` o en un aborto que vuelve a una fila. Si una geometría no tiene fila, se agrega acá, no se “ve en el código”.

## Relación con el otro plan

`docs/plan.md` es tubería y cuerpo (P0–P3). Este archivo es el cerebro de P4–P7. No mezclar: sin go-to-pose estable, `entregar` no existe.
