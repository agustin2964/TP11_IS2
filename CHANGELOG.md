# Registro de cambios

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y
el proyecto adhiere al [Versionado Semántico](https://semver.org/lang/es/).

## [Sin publicar]

### Planificado
- Puntos (i) a (u) de la consigna: GitHub Actions, ruff, black, validación
  PEP8/PEP257, MyPy, PyRight, Pytest con cobertura, bandit y documentación
  actualizada por PR exitoso.

## [0.1.0] - 2026-10-14

### Añadido
- `json2csv.py`: conversor de JSON a CSV por línea de comandos con interfaz
  `-i` / `-o` / `-d`, entrada y salida estándar, y coma como delimitador por
  omisión.
- Estrategia de filtro (pipe-and-filter): siete etapas (origen, análisis JSON,
  registros, valores planos, columnas, render CSV y destino) encadenadas con
  generadores.
- Controles de excepción robustos: errores de lectura y escritura, JSON
  inválido con indicación de línea y columna, documento vacío, estructuras no
  admitidas, delimitador inválido, `-i` y `-o` iguales, salida cerrada por una
  tubería e interrupción por teclado. Códigos de salida 0, 1, 2 y 130.
- Registro de VERSION y BUILD (`VERSION`, `BUILD` y `--version`).
- `README.md`, `CHANGELOG.md`, `CONTEXT.md`, `REQUIREMENTS.TXT` y licencia MIT.
- Esqueleto de proyecto generado con CookieCutter.
