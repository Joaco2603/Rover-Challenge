# Loop P2: Wi-Fi, cliente TCP :2026, freno fuera de RUNNING, GOTO por dt.
# IdeaBoard sin disco CIRCUITPY: Thonny o test/subir.py del repo padre.

import sys
import time

_raiz = __file__.rsplit("/", 1)[0]
if not _raiz:
    _raiz = "/"
_src = _raiz.rstrip("/") + "/src"
for _p in (_raiz, _src):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import config
import hardware
from hardware import pines
import red
from red import enlace

try:
    import mundo
    import tcp
    import control
except ImportError:
    mundo = None
    tcp = None
    control = None

WATCHDOG_S = 0.4


def llegada_celdas(mundo_obj):
    fn = getattr(control, "celdas_desde_mm", None) if control else None
    if fn is None:
        return 1.0
    return fn(getattr(control, "LLEGADA_MM", 20), getattr(mundo_obj, "cell_mm", 20))


def main():
    ib = hardware.IdeaBoard() if hardware.IdeaBoard is not None else None
    if ib is not None:
        ib.brightness = 0.3
    hardware.frenar(ib)
    hardware.pintar(ib, hardware.ROJO)
    if hardware.board is not None:
        hardware.pin_io(pines.IR_FL)
        hardware.pin_io(pines.US_TRIG)
        hardware.pin_io(pines.COLOR_AO)
    if mundo is None or tcp is None:
        print("faltan mundo/tcp (otros PRs). Conecto igual; sin parseo no me muevo.")
    if control is None:
        print("sin control.py: pose si, motores 0")
    while not red.conectar_wifi():
        hardware.frenar(ib)
        hardware.pintar(ib, hardware.ROJO)
        time.sleep(1)
    if red.socketpool is None:
        print("sin socketpool; quieto")
        while True:
            hardware.frenar(ib)
            time.sleep(0.5)
    pool = red.socketpool.SocketPool(red.wifi.radio)
    buf = tcp.BufferNDJSON() if tcp is not None else None
    radio = enlace.armar_espnow()
    sock = None
    seq_visto = None
    t_msg = None
    t_print = 0
    t_claim = 0
    while True:
        try:
            if sock is None:
                hardware.frenar(ib)
                hardware.pintar(ib, hardware.ROJO)
                sock = red.abrir_tcp(pool)
                if sock is None:
                    time.sleep(0.5)
                    continue
                seq_visto = None
                t_msg = None
            if not red.drenar_tcp(sock, buf):
                print("TCP cayo, reconecto")
                sock = red.cerrar(sock)
                hardware.frenar(ib)
                continue
            enlace.drenar_espnow(radio)
            ahora = time.monotonic()
            if radio is not None and ahora - t_claim >= 1.0:
                enlace.claim_espnow(radio)
                t_claim = ahora
            parsed = None
            msg = buf.ultimo() if buf is not None else None
            if mundo is not None and msg is not None:
                parsed = mundo.parsear(msg)
            if parsed is not None and parsed.seq != seq_visto:
                seq_visto = parsed.seq
                t_msg = ahora
            viejo = t_msg is None or (ahora - t_msg) > WATCHDOG_S
            se_juega = parsed is not None and parsed.se_juega()
            yo = parsed.rover(config.ARUCO_ID) if parsed is not None else None
            datos_viejos = True
            if parsed is not None:
                datos_viejos = parsed.datos_viejos(config.ARUCO_ID, parsed.ts_ms)
            mover = se_juega and not datos_viejos and not viejo and yo is not None
            izq = der = 0
            if not mover:
                hardware.frenar(ib)
                hardware.pintar(ib, hardware.AMARILLO if (datos_viejos or viejo) else hardware.ROJO)
            elif config.MODO == "GOTO" and control is not None:
                izq, der, _llego = control.ir_a_pose(
                    yo["col"], yo["row"], yo["theta"],
                    config.GOTO_COL, config.GOTO_ROW,
                    llegada_celdas=llegada_celdas(parsed),
                )
                hardware.escribir_motores(ib, izq, der)
                hardware.pintar(ib, hardware.VERDE if abs(izq) > 0.02 or abs(der) > 0.02 else hardware.ROJO)
            else:
                hardware.frenar(ib)
                hardware.pintar(ib, hardware.ROJO)
            if ahora - t_print >= 0.2:
                t_print = ahora
                phase = parsed.phase if parsed is not None else "?"
                if se_juega and yo is not None:
                    print(
                        "RUNNING id={} col={:.2f} row={:.2f} theta={:.1f} age={} moto={:.2f},{:.2f}".format(
                            config.ARUCO_ID, yo["col"], yo["row"], yo["theta"],
                            yo.get("age_ms", 0), izq, der,
                        )
                    )
                elif se_juega:
                    print("RUNNING id={} sin pose".format(config.ARUCO_ID))
                else:
                    print("quieto phase={} (no RUNNING o datos viejos)".format(phase))
            time.sleep(0.02)
        except KeyboardInterrupt:
            hardware.frenar(ib)
            raise
        except Exception as err:
            print("loop:", err)
            hardware.frenar(ib)
            hardware.pintar(ib, hardware.ROJO)
            sock = red.cerrar(sock)
            time.sleep(0.2)


if __name__ == "__main__":
    if red.wifi is None or red.socketpool is None:
        print("sin wifi/socketpool (no es la IdeaBoard); no arranco el loop")
    else:
        main()
