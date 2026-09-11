"""Buffer NDJSON: corta por newline y se queda con el ultimo JSON v=1."""

import json

BUF_MAX = 8192


class BufferNDJSON:
    def __init__(self):
        self._buf = bytearray()
        self._ultimo = None

    def alimentar(self, trozo):
        """Acumula bytes, parsea lineas completas, conserva solo el ultimo v==1."""
        if trozo:
            self._buf.extend(trozo)
        while True:
            n = bytes(self._buf).find(b"\n")
            if n < 0:
                break
            linea = bytes(self._buf[:n])
            del self._buf[: n + 1]
            if not linea.strip():
                continue
            try:
                obj = json.loads(linea.decode("utf-8"))
            except (UnicodeError, ValueError, TypeError):
                continue
            if not isinstance(obj, dict):
                continue
            if obj.get("v") != 1:
                continue
            self._ultimo = obj
        if len(self._buf) > BUF_MAX:
            del self._buf[:]
        return self._ultimo

    def ultimo(self):
        return self._ultimo
