# Loop P2: Wi-Fi, cliente TCP :2026, freno fuera de RUNNING, GOTO por dt.
# IdeaBoard sin disco CIRCUITPY: Thonny o test/subir.py del repo padre.

import time

import config
import pines

try:
    import mundo
    import tcp
    import control
except ImportError:
    mundo = None
    tcp = None
    control = None

try:
    import board
    import wifi
    import socketpool
    from ideaboard import IdeaBoard
except ImportError:
    board = None
    wifi = None
    socketpool = None
    IdeaBoard = None

try:
    import espnow as lib_espnow
except ImportError:
    lib_espnow = None

WATCHDOG_S = 0.4
PEER_NULO = "AA:BB:CC:DD:EE:FF"
ROJO, VERDE, AMARILLO = (255, 0, 0), (0, 255, 0), (255, 180, 0)
RX = bytearray(512)


def pin_io(gpio):
    return getattr(board, pines.nombre_io(gpio))


def frenar(ib):
    if ib is not None:
        ib.motor_1.throttle = 0
        ib.motor_2.throttle = 0


def pintar(ib, rgb):
    if ib is not None:
        ib.pixel = rgb


def throttle(x):
    if x > 1:
        return 1
    if x < -1:
        return -1
    return x


def escribir_motores(ib, izq, der):
    if ib is None:
        return
    ib.motor_1.throttle = throttle(izq)
    ib.motor_2.throttle = throttle(der)


def conectar_wifi():
    if wifi is None:
        return False
    ssid = config.WIFI_SSID
    if not ssid or ssid == "CAMBIAR":
        print("WIFI_SSID=CAMBIAR: copia secrets.py.example a secrets.py")
        return False
    if not wifi.radio.ipv4_address:
        print("Wi-Fi a", ssid)
        wifi.radio.connect(ssid, config.WIFI_PASSWORD)
    print("Wi-Fi IP", wifi.radio.ipv4_address)
    return True


def abrir_tcp(pool):
    host = config.VISION_HOST
    if host in ("127.0.0.1", "localhost"):
        print("VISION_HOST no puede ser 127.0.0.1; usa la IP de la laptop")
        return None
    sock = pool.socket(pool.AF_INET, pool.SOCK_STREAM)
    try:
        sock.settimeout(3)
        sock.connect((host, int(config.VISION_PORT)))
        try:
            sock.setblocking(False)
        except AttributeError:
            sock.settimeout(0)
        print("TCP {}:{}".format(host, config.VISION_PORT))
        return sock
    except Exception as err:
        print("TCP fallo:", err)
        try:
            sock.close()
        except Exception:
            pass
        return None


def drenar_tcp(sock, buf):
    while True:
        try:
            n = sock.recv_into(RX)
        except OSError:
            return True
        if n is None or n == 0:
            return False
        if buf is not None:
            buf.alimentar(bytes(RX[:n]))


def armar_espnow():
    txt = config.PEER_MAC
    if not txt or txt.upper() == PEER_NULO or lib_espnow is None:
        print("ESP-NOW omitido")
        return None
    try:
        partes = txt.split(":")
        mac = bytes([int(p, 16) for p in partes])
        radio = lib_espnow.ESPNow()
        radio.peers.append(lib_espnow.Peer(mac=mac))
        print("ESP-NOW peer", txt)
        return radio
    except Exception as err:
        print("ESP-NOW no arranco:", err)
        return None


def drenar_espnow(radio):
    if radio is None:
        return
    for _ in range(8):
        try:
            if not radio.read():
                return
        except Exception:
            return


def claim_espnow(radio):
    if radio is None:
        return
    try:
        radio.send("id={}".format(config.ARUCO_ID).encode("utf-8"))
    except Exception:
        pass


def llegada_celdas(mundo_obj):
    fn = getattr(control, "celdas_desde_mm", None) if control else None
    if fn is None:
        return 1.0
    return fn(getattr(control, "LLEGADA_MM", 20), getattr(mundo_obj, "cell_mm", 20))


def cerrar(sock):
    if sock is None:
        return None
    try:
        sock.close()
    except Exception:
        pass
    return None


def main():
    ib = IdeaBoard() if IdeaBoard is not None else None
    if ib is not None:
        ib.brightness = 0.3
    frenar(ib)
    pintar(ib, ROJO)
    if board is not None:
        pin_io(pines.IR_FL)
        pin_io(pines.US_TRIG)
        pin_io(pines.COLOR_AO)
    if mundo is None or tcp is None:
        print("faltan mundo/tcp (otros PRs). Conecto igual; sin parseo no me muevo.")
    if control is None:
        print("sin control.py: pose si, motores 0")
    while not conectar_wifi():
        frenar(ib)
        pintar(ib, ROJO)
        time.sleep(1)
    if socketpool is None:
        print("sin socketpool; quieto")
        while True:
            frenar(ib)
            time.sleep(0.5)
    pool = socketpool.SocketPool(wifi.radio)
    buf = tcp.BufferNDJSON() if tcp is not None else None
    radio = armar_espnow()
    sock = None
    seq_visto = None
    t_msg = None
    t_print = 0
    t_claim = 0
    while True:
        try:
            if sock is None:
                frenar(ib)
                pintar(ib, ROJO)
                sock = abrir_tcp(pool)
                if sock is None:
                    time.sleep(0.5)
                    continue
                seq_visto = None
                t_msg = None
            if not drenar_tcp(sock, buf):
                print("TCP cayo, reconecto")
                sock = cerrar(sock)
                frenar(ib)
                continue
            drenar_espnow(radio)
            ahora = time.monotonic()
            if radio is not None and ahora - t_claim >= 1.0:
                claim_espnow(radio)
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
                frenar(ib)
                pintar(ib, AMARILLO if (datos_viejos or viejo) else ROJO)
            elif config.MODO == "GOTO" and control is not None:
                izq, der, _llego = control.ir_a_pose(
                    yo["col"], yo["row"], yo["theta"],
                    config.GOTO_COL, config.GOTO_ROW,
                    llegada_celdas=llegada_celdas(parsed),
                )
                escribir_motores(ib, izq, der)
                pintar(ib, VERDE if abs(izq) > 0.02 or abs(der) > 0.02 else ROJO)
            else:
                frenar(ib)
                pintar(ib, ROJO)
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
            frenar(ib)
            raise
        except Exception as err:
            print("loop:", err)
            frenar(ib)
            pintar(ib, ROJO)
            sock = cerrar(sock)
            time.sleep(0.2)


if __name__ == "__main__":
    if wifi is None or socketpool is None:
        print("sin wifi/socketpool (no es la IdeaBoard); no arranco el loop")
    else:
        main()
