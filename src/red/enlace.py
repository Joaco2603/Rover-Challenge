# No llamar este archivo espnow.py: sombrearía `import espnow` de CircuitPython.

import config

try:
    import espnow as lib_espnow
except ImportError:
    lib_espnow = None

PEER_NULO = "AA:BB:CC:DD:EE:FF"


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
