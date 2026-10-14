# json2csv - Conversor de JSON a CSV

Herramienta de línea de comandos en Python que convierte un documento **JSON**
en un archivo **CSV**. La conversión se implementa con una **estrategia de
filtro** (estilo arquitectónico pipe-and-filter): los datos avanzan por una
cadena de etapas independientes, cada una con una única responsabilidad, y las
etapas se conectan entre sí mediante generadores:

```
origen -> análisis JSON -> registros -> valores planos -> columnas -> render CSV -> destino
```

Trabajo Práctico N.º 11 - Ingeniería de Software II.

## 1. Requisitos e instalación

- Python 3.10 o superior.
- Ambiente virtual (punto a de la consigna):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt      # herramientas de apoyo y control de calidad
```

El programa está en un único archivo y funciona sólo con la biblioteca
estándar (las librerías de `requirements.txt` son para las pruebas, la
documentación y los controles de calidad).

## 2. Uso

```
python json2csv.py {-i input.txt} {-o output.txt} {-d delimitador}
```

- Sin `-i` se lee de la **entrada estándar** (también `-`).
- Sin `-o` se escribe en la **salida estándar**.
- El delimitador por omisión es la **coma**; `-d` permite indicar otro.

```powershell
python json2csv.py -i datos.json -o salida.csv            # archivo -> archivo
python json2csv.py -i datos.json -o salida.csv -d ";"     # otro delimitador
Get-Content datos.json | python json2csv.py > salida.csv  # entrada estándar
python json2csv.py --version                               # VERSION y BUILD
python -m json2csv -i datos.json                           # también como módulo
```

### Formato de entrada admitido

- **Lista de objetos**: genera una fila por objeto. Las columnas son la unión
  de todas las claves, en orden de primera aparición; las claves ausentes en un
  registro quedan como celda vacía.
- **Objeto único**: genera una única fila.
- Cualquier otra estructura (número o cadena sueltos, lista de escalares, etc.)
  se rechaza con un mensaje de error.

### Reglas de conversión de valores

| Valor JSON               | Texto en el CSV               |
| ------------------------ | ----------------------------- |
| `null`                   | *(celda vacía)*               |
| `true` / `false`         | `true` / `false`              |
| número                   | representación original       |
| objeto o arreglo anidado | JSON compacto: `{"x":[1,2]}`  |
| cadena                   | tal cual                      |

El CSV entrecomilla sólo lo necesario (`QUOTE_MINIMAL`) y termina las líneas
con `\r\n` (RFC 4180).

## 3. Códigos de salida y control de errores

| Código | Significado                                        |
| ------ | -------------------------------------------------- |
| `0`    | conversión correcta                                |
| `1`    | error controlado o error inesperado                |
| `2`    | error de uso de la línea de comandos (`argparse`)   |
| `130`  | ejecución interrumpida con Ctrl+C                   |

Los errores se informan por la **salida de error estándar** con el prefijo
`error:` y nunca ensucian el CSV. Situaciones controladas: archivo inexistente,
ruta que es un directorio, faltas de permiso, documento vacío, JSON inválido
(con línea y columna), estructura no admitida, delimitador inválido, `-i` y
`-o` apuntando al mismo archivo, ruta de salida inválida, salida cerrada por
una tubería e interrupción por teclado.

## 4. Registro de VERSION y BUILD (punto h)

- `VERSION`: versión semántica (`X.Y.Z`).
- `BUILD`: identificador `AAAAMMDD.NNN` (fecha + número de compilación del día).

`python json2csv.py --version` muestra ambos valores.

## 5. Pruebas unitarias (punto o)

```powershell
pytest --cov=json2csv --cov-report=term-missing
```

- 64 pruebas unitarias en `tests/test_json2csv.py`, agrupadas por etapa del
  filtro; cada prueba documenta su **hipótesis** (comportamiento esperado y
  motivo).
- Cobertura actual: **98 %** (mínimo exigido por la consigna: 85 %,
  configurado con `--cov-fail-under=85`).

## 6. Controles de calidad (puntos i-n y p)

```powershell
black --check json2csv.py tests   # j) formato consistente
ruff check json2csv.py tests      # i) reglas de formato (incluye PEP8, k)
pydocstyle json2csv.py tests      # l) PEP257 en los docstrings
mypy                              # m) verificación estática de tipos
pyright                           # n) verificación estática de tipos
bandit -q -c pyproject.toml -r .  # p) análisis básico de seguridad
```

Todas las opciones están en `pyproject.toml`. Según el punto (q) **no** se usa
Trufflehog: el control de seguridad se hace sólo con bandit.

## 7. Integración continua (puntos t y u)

`.github/workflows/ci.yml` se ejecuta en cada *push* y *pull request*:

1. **Calidad**: instala dependencias y corre black, ruff, pydocstyle, mypy,
   pyright, pytest con cobertura mínima del 85 % y bandit.
2. **Documentación**: sólo si la calidad pasa, genera la documentación con
   **pdoc**, la publica como artefacto y, cuando el pipeline corre sobre
   `main`, la commitea en `docs/api/` (punto u).

## 8. Documentación automática (puntos g, r y u)

La documentación de la API se genera con **pdoc** a partir de los docstrings
del módulo (PEP 257):

```powershell
python -m pdoc -o docs/api json2csv.py     # abre docs/api/json2csv.html
```

La versión generada queda en `docs/api/` y se actualiza con cada PR exitoso.

## 9. Esqueleto basado en Cookiectter (punto b)

El esqueleto del proyecto se generó con **CookieCutter**
(`cookiecutter project-template --no-input`). La plantilla no se guarda en el
repositorio para no duplicar archivos; su uso queda documentado aquí y en
`CONTEXT.md`.

## 10. Estructura

```
json2csv.py        El programa completo: etapas del filtro + CLI
tests/
  test_json2csv.py Pruebas unitarias (64 casos, cobertura 98 %)
docs/api/          Documentación pdoc generada
.github/workflows/ci.yml   Pipeline de CI/CD
VERSION            Versión semántica
BUILD              Identificador de compilación
requirements.txt   Dependencias (puntos f y s)
pyproject.toml     Configuración de las herramientas (i-u)
README.md          Este archivo
CHANGELOG.md       Registro de cambios
CONTEXT.md         Prompts de IA documentados
LICENSE            Licencia MIT
```

## 11. Estado del trabajo práctico

| Punto | Requisito                                        | Estado |
| ----- | ------------------------------------------------ | ------ |
| a-h   | Programa y organización del proyecto             | listo  |
| i     | ruff sin errores                                 | listo  |
| j     | black, formato consistente                       | listo  |
| k     | Reglas PEP8 validadas                            | listo  |
| l     | PEP257 en docstrings, sin errores                | listo  |
| m     | MyPy sin errores                                 | listo  |
| n     | PyRight sin errores                              | listo  |
| o     | Pytest con cobertura ≥ 85 % (98 %)               | listo  |
| p     | bandit sin observaciones                         | listo  |
| q     | No usar Trufflehog                               | listo  |
| r     | Documentación del funcionamiento de los módulos  | listo  |
| s     | requirements.txt actualizado                     | listo  |
| t     | Workflow de CI/CD en GitHub                      | listo  |
| u     | Documentación actualizada por PR exitoso         | listo  |

## 12. Licencia (punto g)

Distribuido bajo licencia **MIT**. Ver `LICENSE`.
