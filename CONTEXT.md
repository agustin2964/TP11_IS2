# CONTEXT.md - Uso de herramientas de IA

Documenta los *prompts* (instrucciones) enviados a herramientas de
inteligencia artificial durante el desarrollo, tal como pide el punto (c) de
la consigna del Trabajo Práctico N.º 11.

## Herramienta

- **Agente**: OpenCode (CLI de programación asistida).
- **Modelo**: Step 5 Preview Free.
- **Fecha**: 14 de octubre de 2026.
- **Repositorio**: `C:\Users\Agustin\vc code trabajos\3er año\is2\TP11_IS2`
  (remoto: https://github.com/agustin2964/TP11_IS2).
- **Alcance**: programa principal y puntos (a) a (u) de la consigna.

## Prompts registrados

1. **Consigna del TP, provista por el usuario**: desarrollar una herramienta en
   Python que convierta archivos de formato JSON a formato CSV, implementada
   con una estrategia de filtro, con el formato de ejecución
   `python json2csv.py {-i input.txt} {-o output.txt} {-d delimitador}`,
   entrada y salida estándar cuando no se informan `-i`/`-o`, coma como
   delimitador por omisión, controles robustos para las condiciones de
   excepción, y los puntos (a) a (u) de organización del proyecto.
2. **Repositorio de destino**: "quiero que hagas esto en el repositorio en
   C:\Users\Agustin\vc code trabajos\3er año\is2\TP11_IS2".
3. **Delimitación de alcance**: "desarrolles el programa especificado hasta el
   punto h".
4. **Pedido de resumen**: "haceme un resumen de lo que hiciste, lo que falta
   hacer y si tomaste alguna decisión propia fuera de lo que te mande".
5. **Pedido de simplificación**: "este es solo un punto de un tp, no hace falta
   meterle más tecnología que la que pide, así que lo mejor es hacerlo simple".
   Como resultado se redujo la entrega a un único archivo de programa más los
   archivos que pide la consigna.
6. **Pedido de continuar con los puntos restantes**: "segui con el resto de los
   puntos, verifica sobre lo que ya hiciste y dejame un resumen de lo que se
   trate de pruebas para hacer y documentar por mi cuenta". Se implementaron
   los puntos (i) a (u): pruebas unitarias con Pytest y cobertura, ruff, black,
   pydocstyle (PEP257), MyPy, PyRight, bandit, workflow de CI/CD en GitHub
   Actions y actualización de la documentación por PR exitoso.

## Decisiones propias (no pedidas explícitamente)

- **"Estrategia de filtro"** se interpretó como arquitectura pipe-and-filter:
  siete etapas independientes (origen, análisis JSON, registros, valores
  planos, columnas, render CSV y destino) encadenadas mediante generadores
  dentro de un único archivo.
- **Reglas de conversión** que la consigna no especificaba: `null` → celda
  vacía; booleanos → `true`/`false`; los números conservan la representación
  del documento original (se analizan con `Decimal`); objetos y arreglos
  anidados → JSON compacto; las columnas son la unión de las claves en orden
  de primera aparición; fin de línea `\r\n` (RFC 4180) y entrecomillado mínimo.
- **Códigos de salida** formalizados: 0 (correcto), 1 (error), 2 (error de uso
  de la línea de comandos), 130 (Ctrl+C).
- **Estructura**: un solo archivo `json2csv.py` más los archivos que pide la
  consigna. La plantilla de CookieCutter y la documentación generada con pdoc
  se mantienen fuera del repositorio salvo `docs/api/`, que sí se publica.
- **Se descartó** la opción `-e/--encoding` que se había agregado en una
  primera versión: el programa trabaja siempre con UTF-8 (aceptando BOM).
- **Archivo de dependencias**: se usa `requirements.txt` (minúsculas, punto s).
  El nombre `REQUIREMENTS.TXT` del punto (f) no puede convivir con él en
  sistema operativos Windows (el sistema de archivos no distingue mayúsculas),
  por lo que se documenta que se trata del mismo archivo.
- **bandit** se configura para analizar el programa y excluir los tests (los
  `assert` de las pruebas no son observaciones de seguridad). Según el punto
  (q) no se usa Trufflehog.

## Verificación

Ejecutado dentro del ambiente virtual (`.\.venv\Scripts\python.exe`):

- `pytest --cov=json2csv --cov-report=term-missing` → **64 pruebas en verde,
  cobertura 98 %** (mínimo exigido: 85 %).
- `black --check json2csv.py tests` → sin cambios pendientes.
- `ruff check json2csv.py tests` → sin errores (E/F/W, D, I, N, UP).
- `pydocstyle json2csv.py tests` → sin errores (PEP 257).
- `mypy` → sin errores.
- `pyright` → 0 errores, 0 advertencias.
- `bandit -q -c pyproject.toml -r .` → sin observaciones.
- Suite de 29 pruebas de humo por subproceso (casos válidos y de error de la
  CLI real) ejecutada previamente sobre la versión simplificada: todas verdes.

## Nota de transparencia

El código se generó con asistencia de IA y fue revisado y verificado
manualmente por el autor; las decisiones quedan documentadas en este archivo y
en `README.md`.
