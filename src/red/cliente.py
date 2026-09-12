import config

try:
    import wifi
    import socketpool
except ImportError:
    wifi = None
    socketpool = None

RX = bytearray(512)


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


def cerrar(sock):
    if sock is None:
        return None
    try:
        sock.close()
    except Exception:
        pass
    return None
