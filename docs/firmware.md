# Firmware ESP32: un code.py, dos robots

El mismo `code.py` va en las dos IdeaBoard. Lo que cambia por robot es `secrets.py` (o `config.py`): `ARUCO_ID`, Wi-Fi, `VISION_HOST`, `PEER_MAC`.

Los pines no se discuten acá: están en `README.md` del robot que ya anda. No “arreglarlos” con el diagrama viejo (`TRIG` en IO25, color AO en IO39).

## Quick path

1. Copiá `secrets.py.example` → `secrets.py` en la placa.
2. Poné SSID/clave y `VISION_HOST` = IPv4 de la laptop (macOS: `ipconfig getifaddr en0`). Puerto **2026**. Nunca `127.0.0.1`.
3. Subí el firmware: la IdeaBoard **no** monta disco CIRCUITPY. Usá Thonny (*Save as…* al dispositivo) o `test/subir.py` del repo padre.
4. En RUNNING tiene que imprimir su pose. Fuera de RUNNING, quieto.

## Details

| Tema | Decisión |
| --- | --- |
| Competencia | No usar `wifi_command_receiver.py`: descalifica. El cerebro está en la placa. |
| Loop | Drenar TCP (último JSON), opcional ESP-NOW, si `phase != RUNNING` o datos viejos → motores 0. `dt` / `sleep(0.02)`, no `sleep(2)` de giro. |
| GOTO | `MODO = "GOTO"` llama `control.ir_a_pose` hacia `GOTO_COL`/`GOTO_ROW`. `TELEMETRIA` solo imprime pose. |
| ESP-NOW | Si `PEER_MAC` es `AA:BB:CC:DD:EE:FF`, no se toca. Una MAC real puede mandar un claim mínimo; no hace falta para arrancar. |
| Watchdog | Sin mensaje completo en 400 ms → freno. |

## Checklist

- [ ] `VISION_HOST` es la IP de la laptop, no localhost
- [ ] Cada placa tiene su `ARUCO_ID` / `secrets.py`
- [ ] Fuera de `RUNNING` no se mueve
- [ ] Pines = README.md, no el diagrama de `conexiones/`

## Next step

P3: llegar a una celda a &lt; 2 cm varias veces (`control.py`). Este PR no implementa ASSIGN/PUSH/VERIFY.
