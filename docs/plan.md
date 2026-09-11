# Plan para completar el Vision Rover Challenge

Los dos CenfoBots deben entregar solos los cubos rojo, verde y azul en el depot de su color. Toda la decision corre en los ESP32. La laptop sirve para desarrollar y probar; en ronda oficial no calcula rutas ni manda motores.

## Quick path

1. Clavar hardware del segundo robot (mismo cableado que el primero).
2. Consumir telemetria TCP:2026 (ultimo JSON, rover por `id`, cubo/depot por `color`, quieto si `phase != RUNNING`).
3. Cerrar go-to-pose con la camara (sin `sleep()` bloqueante).
4. Empujar un cubo desde la pose de ataque hasta su depot.
5. Sumar el segundo rover con claims por ESP-NOW.

## Arquitectura

Mismo `code.py` en las dos placas. Cambia la config: `ARUCO_ID`, `PEER_MAC`, Wi-Fi.

| Pieza | Rol |
| --- | --- |
| Vision oficial | Publica el mundo. No planifica. |
| TCP NDJSON :2026 | Cada rover es cliente. Buffer hasta `\n`. Se queda con el ultimo mensaje. |
| Cerebro en el ESP32 | Asigna, navega, empuja, corrige. |
| ESP-NOW | Claims de cubos y zona de keep-out. No es el mapa. |
| Laptop | Banco de pruebas y simulador. Fuera del loop en ronda. |

No usar lider/seguidor: el seguidor igual necesita pose de camara, y un lider caido pierde la ronda. No usar `wifi_command_receiver.py` en competencia: descalifica.

## Loop

En cada vuelta: drenar TCP, drenar ESP-NOW, si no es `RUNNING` frenar, si no actualizar la FSM y escribir throttle. Giros y avances van por `dt`, no por `sleep(2)`.

FSM por cubo: `QUIET → ASSIGN → GOTO_STANDOFF → ALIGN → PUSH → VERIFY → ASSIGN`. `RECOVER` vuelve a asignar si la pose es vieja, el cubo no se mueve o el otro rover esta encima.

Asignacion: costo = distancia a la pose detras del cubo, opuesta al depot. Gana el de menor costo; empate lo gana el ArUco de id menor. El rover libre toma el cubo que queda.

## Empuje

Sin pala extra. Standoff ~12–18 cm detras del cubo, rumbo hacia el depot, avance lento. Si el cubo no se mueve en la telemetria, re-alinear. `age_ms` alto es oclusion, no desaparicion. Entrega = cubo completamente en su zona; la orientacion no cuenta.

## Fases y gates

| Fase | Gate para pasar |
| --- | --- |
| P0 Hardware | `./test/correr.sh` en verde en los dos robots |
| P1 Cliente laptop | Parsea el mock, obedece `phase`, no indexa listas |
| P2 TCP en ESP32 | Imprime su pose en `RUNNING`, quieto en el resto, reconecta |
| P3 Go-to-pose | Llega a una celda a < 2 cm, varias veces |
| P4 Un cubo | Un rover deja un cubo en su depot |
| P5 Tres cubos, un rover | Recupera si un empuje falla |
| P6 Dos rovers | No se pelean el mismo cubo; el idle toma el restante |
| P7 Ronda | `FINISHED` frena; oclusion y latencia no los tiran |

## Checklist

- [ ] No moverse fuera de `RUNNING`
- [ ] Buscar rover por `id` de ArUco, cubo y depot por `color`
- [ ] Leer `grid` del mensaje; no hardcodear 43×43
- [ ] Frenar si la latencia o `age_ms` del propio rover se disparan
- [ ] Drenar el socket; no encolar telemetria vieja
- [ ] Config distinta por robot, mismo firmware
- [ ] Obstaculos: iterar la lista aunque hoy venga vacia

## Algoritmo de juego

Cuando la tubería ya no falle: [`docs/plan-algoritmo.md`](plan-algoritmo.md). Todavía no se programa.

## Next step

P0: cablear y validar el segundo robot con el mapa de pines de `docs/readme.md`. En paralelo, P1 en la laptop contra `vision-system/contrato/mock_publisher.py`.
