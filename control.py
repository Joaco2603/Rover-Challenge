"""Go-to-pose por dt. El caller aplica el intervalo; nada bloquea el loop."""

import math

STANDOFF_MM = 150
LLEGADA_MM = 20
VEL_MAX = 0.45
GIRO_MAX = 0.35
ANGULO_GIRO_EN_SITIO = 35
_ALINEADO_DEG = 8
_GIRO_MIN = 0.12
_LENTO_CELDAS = 5.0


def clamp(x, lo, hi):
    if x < lo:
        return lo
    if x > hi:
        return hi
    return x


def wrap180(grados):
    """shortest signed angle to [-180, 180]"""
    a = (grados + 180.0) % 360.0 - 180.0
    if a <= -180.0:
        a = 180.0
    return a


def celdas_desde_mm(mm, cell_mm):
    """mm / cell_mm  (cell_mm from telemetry grid, never assume 20 if passed in)"""
    return mm / float(cell_mm)


def rumbo_hacia(col, row, tcol, trow):
    """heading degrees to face the point, 0=+col CCW. atan2(-drow, dcol)"""
    dcol = tcol - col
    drow = trow - row
    return math.degrees(math.atan2(-drow, dcol))


def _norm360(grados):
    a = grados % 360.0
    if a < 0.0:
        a += 360.0
    return a


def pose_ataque(cubo_col, cubo_row, depot_col, depot_row, standoff_celdas):
    """Pose behind the cube, opposite the depot, facing the depot.

    Return (col, row, theta). If cube and depot coincide, return cube pose with theta 0.
    """
    dcol = depot_col - cubo_col
    drow = depot_row - cubo_row
    dist = math.sqrt(dcol * dcol + drow * drow)
    if dist < 1e-9:
        return (cubo_col, cubo_row, 0.0)
    ucol = dcol / dist
    urow = drow / dist
    col = cubo_col - ucol * standoff_celdas
    row = cubo_row - urow * standoff_celdas
    theta = _norm360(rumbo_hacia(col, row, depot_col, depot_row))
    return (col, row, theta)


def _giro(err):
    g = clamp(err / 40.0 * GIRO_MAX, -GIRO_MAX, GIRO_MAX)
    if abs(g) < _GIRO_MIN:
        if err > 0.0:
            g = _GIRO_MIN
        else:
            g = -_GIRO_MIN
    return g


def ir_a_pose(col, row, theta, tcol, trow, ttheta=None, llegada_celdas=1.0):
    """One control step. Returns (izq, der, llego)."""
    dcol = tcol - col
    drow = trow - row
    dist = math.sqrt(dcol * dcol + drow * drow)

    if dist <= llegada_celdas:
        if ttheta is None:
            return (0.0, 0.0, True)
        err_th = wrap180(ttheta - theta)
        if abs(err_th) <= _ALINEADO_DEG:
            return (0.0, 0.0, True)
        g = _giro(err_th)
        return (clamp(-g, -1.0, 1.0), clamp(g, -1.0, 1.0), False)

    deseado = rumbo_hacia(col, row, tcol, trow)
    err = wrap180(deseado - theta)

    if abs(err) > ANGULO_GIRO_EN_SITIO:
        g = _giro(err)
        return (clamp(-g, -1.0, 1.0), clamp(g, -1.0, 1.0), False)

    vel = VEL_MAX
    if dist < _LENTO_CELDAS:
        vel = VEL_MAX * dist / _LENTO_CELDAS
        if vel < 0.12:
            vel = 0.12

    g = clamp(err / 50.0 * GIRO_MAX, -GIRO_MAX, GIRO_MAX)
    izq = clamp(vel - g, -1.0, 1.0)
    der = clamp(vel + g, -1.0, 1.0)
    return (izq, der, False)
