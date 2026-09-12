# Por-robot. El firmware (code.py) es el mismo en las dos placas.
# Preferí secrets.py en la IdeaBoard; estos valores son placeholders.

ARUCO_ID = 10
WIFI_SSID = "CAMBIAR"
WIFI_PASSWORD = "CAMBIAR"
VISION_HOST = "192.168.1.10"
VISION_PORT = 2026
PEER_MAC = "AA:BB:CC:DD:EE:FF"
MODO = "GOTO"  # GOTO until FSM lands; TELEMETRIA = only print pose, motors 0
GOTO_COL = 20.0
GOTO_ROW = 20.0

try:
    import secrets as _secrets
except ImportError:
    _secrets = None


def _desde_secrets(nombre, actual):
    if _secrets is None:
        return actual
    return getattr(_secrets, nombre, actual)


ARUCO_ID = _desde_secrets("ARUCO_ID", ARUCO_ID)
WIFI_SSID = _desde_secrets("WIFI_SSID", WIFI_SSID)
WIFI_PASSWORD = _desde_secrets("WIFI_PASSWORD", WIFI_PASSWORD)
VISION_HOST = _desde_secrets("VISION_HOST", VISION_HOST)
PEER_MAC = _desde_secrets("PEER_MAC", PEER_MAC)
