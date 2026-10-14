# Registro de cambios

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y
el proyecto adhiere al [Versionado Semántico](https://semver.org/lang/es/).

## [Sin publicar]

## [0.2.0] - 2026-10-14

### Añadido
- Pruebas unitarias con Pytest (`tests/test_json2csv.py`): 64 casos con la
  hipótesis documentada en cada uno y cobertura del 98 % (mínimo exigido:
  85 %). Punto (o).
- Configuración de las herramientas en `pyproject.toml`: ruff (i), black (j),
  pydocstyle/PEP257 (l), MyPy (m), PyRight (n), pytest y cobertura (o) y
  bandit (p).
- Workflow de CI/CD en `.github/workflows/ci.yml`: control de calidad en cada
  push y pull request, y generación/actualización de la documentación con pdoc
  cuando el pipeline termina en verde (puntos t y u).
- `requirements.txt` con todas las dependencias de las herramientas (punto s).
  Reemplaza a `REQUIREMENTS.TXT`; en sistemas de archivos que no distinguen
  mayúsculas (Windows) ambos nombres son el mismo archivo.
- Documentación de la API generada con pdoc en `docs/api/` (puntos g, r y u).

### Cambiado
- El código se formateó con black y se ajustó para pasar ruff, pydocstyle,
  MyPy y PyRight sin errores ni advertencias.

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
- `README.md`, `CHANGELOG.md`, `CONTEXT.md`, dependencias y licencia MIT.
- Esqueleto de proyecto generado con CookieCutter.

### Notas
- Punto (q): según la consigna no se utiliza Trufflehog; el control de
  seguridad se realiza únicamente con bandit.
- El pipeline de CI/CD se activa al subir el repositorio a GitHub.
