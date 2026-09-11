"""Mundo de telemetria v1: lookup por identidad, grid del mensaje."""

PROTOCOLO_V = 1
FASE_IDLE = "IDLE"
FASE_READY = "READY"
FASE_RUNNING = "RUNNING"
FASE_FINISHED = "FINISHED"
LATENCIA_MAX_MS = 500
AGE_PROPIO_MAX_MS = 400

_CAMPOS = (
    "v", "seq", "ts_ms", "phase", "grid",
    "rovers", "cubes", "obstacles", "start", "depots",
)
_GRID = ("cols", "rows", "cell_mm")


def _buscar(lista, clave, valor):
    for item in lista:
        if item[clave] == valor:
            return item
    return None


def parsear(msg):
    """msg es un dict. Mundo o None si v mala o faltan claves."""
    if not isinstance(msg, dict):
        return None
    for k in _CAMPOS:
        if k not in msg:
            return None
    if msg["v"] != PROTOCOLO_V:
        return None
    grid = msg["grid"]
    if not isinstance(grid, dict):
        return None
    for k in _GRID:
        if k not in grid:
            return None
    m = Mundo()
    m.v = msg["v"]
    m.seq = msg["seq"]
    m.ts_ms = msg["ts_ms"]
    m.phase = msg["phase"]
    m.grid_cols = grid["cols"]
    m.grid_rows = grid["rows"]
    m.cell_mm = grid["cell_mm"]
    m.rovers = msg["rovers"]
    m.cubes = msg["cubes"]
    m.obstacles = msg["obstacles"]
    m.start = msg["start"]
    m.depots = msg["depots"]
    return m


class Mundo:
    def rover(self, aruco_id):
        return _buscar(self.rovers, "id", aruco_id)

    def cubo(self, color):
        return _buscar(self.cubes, "color", color)

    def depot(self, color):
        return _buscar(self.depots, "color", color)

    def latencia_ms(self, ahora_ms):
        return int(ahora_ms) - int(self.ts_ms)

    def datos_viejos(self, aruco_id, ahora_ms):
        """True si hay que frenar: latencia, age_ms propio, o rover ausente."""
        if self.latencia_ms(ahora_ms) > LATENCIA_MAX_MS:
            return True
        r = self.rover(aruco_id)
        if r is None:
            return True
        return int(r["age_ms"]) > AGE_PROPIO_MAX_MS

    def se_juega(self):
        return self.phase == FASE_RUNNING
