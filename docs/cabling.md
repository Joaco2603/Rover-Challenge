# Cableado del CenfoBot que ya funciona

Copia estas conexiones en el segundo robot. Los pines son los de `code.py` (IdeaBoard / ESP32), no los del diagrama viejo de color ni los ejemplos con `TRIG` en `IO25`.

Antes de energizar: jumper **SELECT–Vin** puesto. Sin eso no hay motores ni ultrasónico.

Los pines están serigrafiados en la placa (`IO4`, `IO23`, `IO33`, …). Cada header suele ser **GND / V / señal**.

## Mapa rápido

| Cable | Dónde / módulo | Pin IdeaBoard |
| --- | --- | --- |
| **sen1** | adelante, izquierda | **IO36** |
| **sen2** | adelante, derecha | **IO39** |
| **sen3** | atrás, izquierda | **IO34** |
| **sen4** | atrás, derecha | **IO35** |
| IR alimentación | VCC de los 4 IR | **3.3V** |
| IR tierra | GND de los 4 IR | **GND** |
| Ultrasonido VCC | VCC | **5V** |
| Ultrasonido Trigger | TRIG | **IO23** |
| Ultrasonido Echo | ECHO | **IO26** |
| Ultrasonido tierra | GND | **GND** |
| Ultrasonido OUT | OUT | **no conectar** |
| Color VCC | VCC | **3.3V** (no 5V) |
| Color LED (cuadrado blanco) | DI | **IO4** |
| Color fotocelda | AO | **IO33** |
| Color tierra | GND | **GND** |
| IMU | cable Qwiic | conector **Qwiic** |
| Motor 1 | 2 cables del chasis Motor 1 | bornes **MOTOR 1** |
| Motor 2 | 2 cables del chasis Motor 2 | bornes **MOTOR 2** |
| Batería | caja de baterías | **Vin** y **GND** (bornes verdes) |

BOOT es el botón de la placa (`IO0`). No lleva cable.

## 1. Jumper y batería

1. Puente metálico entre **SELECT** y **Vin** (junto a los bornes de motores).
2. Batería a los bornes verdes: rojo → **Vin**, negro → **GND**. Polaridad al revés puede dañar la placa.

## 2. Infrarrojos (piso)

Solo la **señal** de cada IR (`sen1`–`sen4`). VCC de ese grupo a **3.3V**, GND a cualquier **GND**.

Mirando el robot hacia adelante (adelante = lado del ultrasónico; izquierda/derecha desde el robot, no desde vos si lo mirás de frente):

| Cable | Dónde está el sensor | Pin |
| --- | --- | --- |
| **sen1** | adelante, izquierda | **IO36** |
| **sen2** | adelante, derecha | **IO39** |
| **sen3** | atrás, izquierda | **IO34** |
| **sen4** | atrás, derecha | **IO35** |

No pongas el analógico de color en `IO39`: ese pin ya es sen2.

## 3. Ultrasonido (HC-SR04 de 5 pines)

Cables hacia abajo, transductores al frente. Solo 4 pines:

| Módulo | IdeaBoard |
| --- | --- |
| VCC | 5V |
| TRIG | IO23 |
| ECHO | IO26 |
| GND | GND |
| OUT | libre |

TRIG y ECHO son cables distintos. Si Echo va junto a Trig, la prueba da ~1 cm de ruido y no distancia.

No uses `IO25` para Trig: el robot que ya corre usa **IO23**.

Comprobar: `./test/correr_ultra.sh` — al acercar la mano tiene que bajar cm, no timeout ni ~1 cm fijo.

## 4. Sensor de color (luz + NeoPixel)

Cuatro cables soldados al módulo. El cuadrado blanco es el LED (`DI`). El chip al lado (`AO`) no prende.

| Módulo | IdeaBoard |
| --- | --- |
| VCC | 3.3V |
| DI | IO4 |
| AO | IO33 |
| GND | GND |

El diagrama de `conexiones/` pone AO en IO39. **Ignoralo.** En este robot AO va a **IO33** porque IO39 es sen2.

Comprobar: `./test/correr_color.sh` — el cuadrado blanco tiene que hacer rojo, verde, azul 1 s cada uno. Si solo cambia el LED de la IdeaBoard, `DI` no está en IO4.

## 5. IMU (Qwiic)

Cable Qwiic del chasis al conector **Qwiic** de la placa (junto al USB-C). Tiene sentido: no forzar. Si Z en reposo no está cerca de ~10 m/s², el cable está al revés o flojo.

## 6. Motores

Cada motor: 2 jumpers a su borne.

- Motor 1 → **MOTOR 1** (internamente IO12 / IO14)
- Motor 2 → **MOTOR 2** (internamente IO13 / IO15)

Si uno gira al revés al ir “adelante”, cruza **solo** los dos cables de ese motor.

## Cómo saber que el segundo quedó igual

USB a un `/dev/cu.usbserial-*` (esta placa no monta disco CIRCUITPY).

```bash
./test/correr.sh          # todo: IR, ultra, color, IMU, motores (BOOT)
./test/correr_ultra.sh    # solo ultrasónico
./test/correr_color.sh    # solo color
```

En `correr.sh`, antes de motores: levantar el robot y pulsar BOOT.
