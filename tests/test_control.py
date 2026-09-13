import math
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from control import (
    LLEGADA_MM,
    STANDOFF_MM,
    celdas_desde_mm,
    ir_a_pose,
    pose_ataque,
    rumbo_hacia,
    wrap180,
)


def _simular(col, row, theta, tcol, trow, llegada_celdas, ttheta=None):
    dt = 0.02
    speed_cells_s = 8.0
    turn_deg_s = 120.0
    timeout_s = 25.0
    t = 0.0
    while t < timeout_s:
        izq, der, llego = ir_a_pose(
            col, row, theta, tcol, trow, ttheta, llegada_celdas
        )
        if llego:
            break
        v = (izq + der) / 2.0 * speed_cells_s
        omega = (der - izq) / 2.0 * turn_deg_s
        rad = math.radians(theta)
        col = col + v * dt * math.cos(rad)
        row = row + v * dt * (-math.sin(rad))
        theta = (theta + omega * dt) % 360.0
        if theta < 0.0:
            theta += 360.0
        t = t + dt
    dist = math.sqrt((tcol - col) ** 2 + (trow - row) ** 2)
    return dist, llego, t, col, row, theta


class TestControl(unittest.TestCase):
    def test_wrap180_bordes(self):
        self.assertAlmostEqual(wrap180(0.0), 0.0, places=6)
        self.assertAlmostEqual(wrap180(90.0), 90.0, places=6)
        self.assertAlmostEqual(wrap180(-90.0), -90.0, places=6)
        self.assertAlmostEqual(abs(wrap180(180.0)), 180.0, places=6)
        self.assertAlmostEqual(abs(wrap180(-180.0)), 180.0, places=6)
        self.assertAlmostEqual(wrap180(181.0), -179.0, places=5)
        self.assertAlmostEqual(wrap180(-181.0), 179.0, places=5)
        self.assertAlmostEqual(wrap180(270.0), -90.0, places=5)
        self.assertAlmostEqual(wrap180(-270.0), 90.0, places=5)
        self.assertAlmostEqual(wrap180(360.0), 0.0, places=6)

    def test_rumbo_hacia_ejes(self):
        self.assertAlmostEqual(rumbo_hacia(0.0, 0.0, 5.0, 0.0), 0.0, places=5)
        self.assertAlmostEqual(rumbo_hacia(0.0, 0.0, 0.0, -5.0), 90.0, places=5)
        self.assertAlmostEqual(rumbo_hacia(0.0, 0.0, 0.0, 5.0), -90.0, places=5)

    def test_pose_ataque_detras_del_cubo(self):
        cell_mm = 20.0
        standoff = celdas_desde_mm(STANDOFF_MM, cell_mm)
        col, row, theta = pose_ataque(10.0, 10.0, 10.0, 0.0, standoff)
        self.assertAlmostEqual(col, 10.0, places=5)
        self.assertGreater(row, 10.0)
        self.assertAlmostEqual(row, 10.0 + standoff, places=5)
        self.assertAlmostEqual(wrap180(theta - 90.0), 0.0, delta=5.0)
        mismo = pose_ataque(4.0, 4.0, 4.0, 4.0, standoff)
        self.assertEqual(mismo, (4.0, 4.0, 0.0))

    def test_ir_a_pose_ya_en_objetivo(self):
        izq, der, llego = ir_a_pose(3.0, 3.0, 45.0, 3.0, 3.0)
        self.assertTrue(llego)
        self.assertAlmostEqual(izq, 0.0, places=6)
        self.assertAlmostEqual(der, 0.0, places=6)

    def test_ir_a_pose_frente_ambos_positivos(self):
        izq, der, llego = ir_a_pose(0.0, 0.0, 0.0, 5.0, 0.0)
        self.assertFalse(llego)
        self.assertGreater(izq, 0.0)
        self.assertGreater(der, 0.0)

    def test_ir_a_pose_ccw_izq_menor_que_der(self):
        izq, der, llego = ir_a_pose(0.0, 0.0, 0.0, 0.0, -5.0)
        self.assertFalse(llego)
        self.assertLess(izq, der)

    def test_sim_llega_a_varios_objetivos(self):
        cell_mm = 20.0
        gate = celdas_desde_mm(LLEGADA_MM, cell_mm)
        casos = [
            ((0.0, 0.0, 0.0), (6.0, 0.0)),
            ((0.0, 0.0, 0.0), (0.0, -6.0)),
            ((0.0, 0.0, 0.0), (0.0, 6.0)),
            ((2.0, 8.0, 90.0), (2.0, 1.0)),
            ((12.0, 12.0, 180.0), (4.0, 9.0)),
        ]
        for inicio, meta in casos:
            dist, llego, t, col, row, theta = _simular(
                inicio[0],
                inicio[1],
                inicio[2],
                meta[0],
                meta[1],
                gate,
            )
            msg = "start=%s target=%s dist=%.4f llego=%s t=%.2fs pose=(%.3f,%.3f,%.1f)" % (
                inicio,
                meta,
                dist,
                llego,
                t,
                col,
                row,
                theta,
            )
            self.assertTrue(llego, msg)
            self.assertLess(dist, gate, msg)

    def test_control_no_usa_sleep(self):
        ruta = os.path.join(ROOT, "control.py")
        with open(ruta, "r") as fh:
            src = fh.read()
        self.assertNotIn("sleep(", src)
        self.assertNotIn("time.sleep", src)


if __name__ == "__main__":
    unittest.main()
