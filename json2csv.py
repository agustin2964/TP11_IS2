#!/usr/bin/env python3
"""Conversor de JSON a CSV por línea de comandos.

Convierte un documento JSON en un archivo CSV aplicando una estrategia de
filtro (estilo arquitectónico pipe-and-filter): los datos avanzan por una
cadena de etapas independientes, cada una con una única responsabilidad, y
cada etapa entrega su resultado a la siguiente mediante generadores::

    origen -> analisis JSON -> registros -> valores planos ->
    columnas -> render CSV -> destino

Uso (formato pedido en la consigna del TP)::

    python json2csv.py {-i input.txt} {-o output.txt} {-d delimitador}

- Sin ``-i`` se lee de la entrada estándar (``-`` también).
- Sin ``-o`` se escribe en la salida estándar.
- El delimitador por omisión es la coma.

Códigos de salida: 0 (correcto), 1 (error de conversión), 2 (error de uso
de la línea de comandos), 130 (interrupción con Ctrl+C).
"""

from __future__ import annotations

import argparse
import csv
import errno
import io
import json
import os
import sys
from collections.abc import Iterable, Iterator, Mapping, Sequence
from decimal import Decimal
from pathlib import Path
from typing import Any

#: Directorio raíz del proyecto (donde viven VERSION y BUILD).
_ROOT = Path(__file__).resolve().parent

#: Terminador de línea del CSV generado (RFC 4180).
LINETERMINATOR = "\r\n"


# ---------------------------------------------------------------------------
# Registro de VERSION y BUILD (punto h)
# ---------------------------------------------------------------------------
def _leer_registro(nombre: str, reserva: str) -> str:
    """Lee el archivo de registro ``nombre`` desde la raíz del proyecto."""
    try:
        valor = (_ROOT / nombre).read_text(encoding="utf-8").strip()
    except OSError:
        return reserva
    return valor or reserva


VERSION = _leer_registro("VERSION", "0.0.0")
"""Versión semántica del programa."""

BUILD = _leer_registro("BUILD", "0")
"""Identificador de compilación (AAAAMMDD.NNN)."""


# ---------------------------------------------------------------------------
# Excepciones propias: la CLI captura una sola clase base
# ---------------------------------------------------------------------------
class Json2CsvError(Exception):
    """Error base de la herramienta."""

    def __init__(self, message: str, *, hint: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint


class InputError(Json2CsvError):
    """Fallos al obtener la información de entrada."""


class OutputError(Json2CsvError):
    """Fallos al emitir la información de salida."""


class DataError(Json2CsvError):
    """Datos de entrada con formato inesperado o inválido."""


class ConfigurationError(Json2CsvError):
    """Opciones de conversión inválidas."""


# ---------------------------------------------------------------------------
# Etapas del filtro
# ---------------------------------------------------------------------------
def source_filter(path: str | None) -> Iterator[str]:
    """Etapa 1 - origen: entrega el documento línea por línea.

    Lee del archivo indicado o, si ``path`` es ``None``, de la entrada
    estándar. Para UTF-8 se acepta el BOM si está presente.
    """
    if path is None:
        wrapper = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8-sig")
        try:
            yield from wrapper
        except UnicodeDecodeError as exc:
            raise InputError(
                "el documento de la entrada estándar no se pudo decodificar con UTF-8",
                hint=f"{exc.reason}; convierta el archivo a UTF-8",
            ) from None
        finally:
            wrapper.detach()
        return

    try:
        if os.path.isdir(path):
            raise InputError(f"la ruta de entrada '{path}' es un directorio")
        handle = open(path, "r", encoding="utf-8-sig", newline=None)
    except InputError:
        raise
    except OSError as exc:
        raise InputError(_describir_error("abrir para lectura", path, exc)) from None

    try:
        with handle:
            yield from handle
    except UnicodeDecodeError as exc:
        raise InputError(
            f"el documento de entrada '{path}' no se pudo decodificar con UTF-8",
            hint=f"{exc.reason}; convierta el archivo a UTF-8",
        ) from None


def parse_filter(lines: Iterable[str]) -> Any:
    """Etapa 2 - análisis: convierte el texto en una estructura Python.

    Devuelve el documento JSON completo (no es un generador porque para
    analizarlo es necesario haberlo leído entero).
    """
    text = "".join(lines)
    if not text.strip():
        raise DataError(
            "el documento de entrada está vacío",
            hint="se esperaba un objeto JSON o una lista de objetos JSON",
        )
    try:
        return json.loads(text, parse_float=Decimal)
    except json.JSONDecodeError as exc:
        raise DataError(
            f"JSON inválido (línea {exc.lineno}, columna {exc.colno}): {exc.msg}"
        ) from None
    except ValueError as exc:
        raise DataError(f"JSON inválido: {exc}") from None


def records_filter(document: Any) -> Iterator[dict[str, Any]]:
    """Etapa 3 - registros: normaliza el documento a una fila por elemento.

    Acepta una lista de objetos o un objeto único; cualquier otra estructura
    se rechaza indicando la posición del dato inesperado.
    """
    if isinstance(document, list):
        for index, item in enumerate(document):
            if not isinstance(item, dict):
                raise DataError(
                    "se esperaba una lista de objetos JSON",
                    hint=f"el elemento en la posición {index} es de tipo "
                    f"{type(item).__name__}",
                )
            yield dict(item)
    elif isinstance(document, dict):
        yield dict(document)
    else:
        raise DataError(
            "se esperaba un objeto JSON o una lista de objetos JSON",
            hint=f"el documento es de tipo {type(document).__name__}",
        )


def scalarize_filter(records: Iterable[dict[str, Any]]) -> Iterator[dict[str, str]]:
    """Etapa 4 - valores planos: normaliza cada valor a texto.

    Reglas: ``null`` -> celda vacía; booleanos -> ``true``/``false``; los
    números conservan la representación del documento; objetos y arreglos
    anidados -> JSON compacto.
    """
    for record in records:
        yield {str(key): _a_texto(value) for key, value in record.items()}


def fields_filter(
    records: Iterable[Mapping[str, str]],
) -> tuple[list[str], list[Mapping[str, str]]]:
    """Etapa 5 - columnas: calcula las columnas del CSV.

    El encabezado debe conocerse antes de la primera fila, por lo que aquí se
    materializan los registros. Las columnas son la unión de todas las claves
    en orden de primera aparición.
    """
    stored = list(records)
    columns: list[str] = []
    seen: set[str] = set()
    for record in stored:
        for key in record:
            if key not in seen:
                seen.add(key)
                columns.append(key)
    return columns, stored


def render_filter(
    columns: Sequence[str],
    records: Iterable[Mapping[str, str]],
    delimiter: str,
) -> Iterator[str]:
    """Etapa 6 - render: serializa los registros como CSV, fila por fila."""
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, delimiter=delimiter, lineterminator=LINETERMINATOR)
    header_written = False
    for record in records:
        if not header_written:
            writer.writerow(columns)
            header_written = True
        writer.writerow([record.get(column, "") for column in columns])
        chunk = buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)
        yield chunk


def output_filter(chunks: Iterable[str], path: str | None) -> int:
    """Etapa 7 - destino: escribe los fragmentos en el archivo o en stdout.

    Devuelve la cantidad de caracteres escritos.
    """
    written = 0
    if path is None:
        _ajustar_stdout()
        for chunk in chunks:
            sys.stdout.write(chunk)
            written += len(chunk)
        sys.stdout.flush()
        return written

    try:
        if os.path.isdir(path):
            raise OutputError(f"la ruta de salida '{path}' es un directorio")
        handle = open(path, "w", encoding="utf-8", newline="")
    except OutputError:
        raise
    except OSError as exc:
        raise OutputError(_describir_error("abrir para escritura", path, exc)) from None

    try:
        with handle:
            for chunk in chunks:
                handle.write(chunk)
                written += len(chunk)
            handle.flush()
    except OSError as exc:
        raise OutputError(_describir_error("escribir", path, exc)) from None
    return written


# ---------------------------------------------------------------------------
# Conversión: encadenado de las etapas (estrategia de filtro)
# ---------------------------------------------------------------------------
def convert(input_path: str | None, output_path: str | None, delimiter: str) -> int:
    """Ejecuta la cadena de filtros y devuelve la cantidad de registros.

    Raises
    ------
    Json2CsvError
        Si las opciones no son válidas o la conversión falla.
    """
    _validar(input_path, output_path, delimiter)
    lines = source_filter(input_path)
    document = parse_filter(lines)
    records = records_filter(document)
    rows = scalarize_filter(records)
    columns, rows = fields_filter(rows)
    chunks = render_filter(columns, rows, delimiter)
    output_filter(chunks, output_path)
    return len(rows)


# ---------------------------------------------------------------------------
# Funciones auxiliares
# ---------------------------------------------------------------------------
def _validar(input_path: str | None, output_path: str | None, delimiter: str) -> None:
    """Revisa las opciones antes de ejecutar la cadena de filtros."""
    if len(delimiter) != 1:
        raise ConfigurationError(
            "el delimitador debe ser un único carácter", hint=f"se recibió {delimiter!r}"
        )
    if delimiter in {'"', "\r", "\n"}:
        raise ConfigurationError(
            f"delimitador no admitido: {delimiter!r}",
            hint='no puede ser la comilla doble (") ni un salto de línea',
        )
    if input_path is not None and output_path is not None:
        try:
            mismo = Path(input_path).resolve() == Path(output_path).resolve()
        except OSError:
            mismo = False
        if mismo:
            raise ConfigurationError(
                "el archivo de salida no puede ser el mismo que el de entrada",
                hint="use rutas distintas para -i y -o",
            )


def _a_texto(value: Any) -> str:
    """Convierte un valor JSON en el texto que se escribirá en el CSV."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return value
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return str(value)


def _ajustar_stdout() -> None:
    """Fija UTF-8 y evita que Windows duplique el salto de línea del CSV."""
    try:
        sys.stdout.reconfigure(encoding="utf-8", newline="")
    except (AttributeError, LookupError, OSError, ValueError):
        pass  # el flujo no admite reconfiguración (p. ej. en pruebas)


def _describir_error(action: str, path: str, exc: OSError) -> str:
    """Devuelve un mensaje en español para un error del sistema operativo."""
    reasons = {
        errno.ENOENT: "el archivo no existe",
        errno.EACCES: "permiso denegado",
        errno.EISDIR: "la ruta es un directorio",
        errno.ENOTDIR: "un componente de la ruta no es un directorio",
        errno.ENOSPC: "no hay espacio suficiente en el dispositivo",
        errno.EROFS: "el sistema de archivos es de solo lectura",
    }
    reason = reasons.get(exc.errno, exc.strerror or str(exc))
    return f"no se pudo {action} '{path}': {reason}"


# ---------------------------------------------------------------------------
# Interfaz de línea de comandos
# ---------------------------------------------------------------------------
def _delimitador(text: str) -> str:
    """Valida el delimitador de ``-d``: debe ser un único carácter."""
    if len(text) != 1:
        raise argparse.ArgumentTypeError(
            f"el delimitador debe ser un único carácter, se recibieron {len(text)}"
        )
    if text in "\r\n":
        raise argparse.ArgumentTypeError("el delimitador no puede ser un salto de línea")
    if text == '"':
        raise argparse.ArgumentTypeError("el delimitador no puede ser la comilla doble")
    return text


def _construir_parser() -> argparse.ArgumentParser:
    """Construye el analizador de argumentos del programa."""
    parser = argparse.ArgumentParser(
        prog="json2csv.py",
        description="Convierte un documento JSON en CSV (estrategia de filtro).",
        epilog=(
            "ejemplos:\n"
            "  python json2csv.py -i datos.json -o salida.csv\n"
            '  python json2csv.py -i datos.json -o salida.csv -d ";"\n'
            "  python json2csv.py < datos.json > salida.csv\n"
            "  python json2csv.py -i datos.json -\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-i", "--input", metavar="ARCHIVO", default=None,
        help="archivo JSON de entrada; si se omite, se lee de la entrada estándar",
    )
    parser.add_argument(
        "-o", "--output", metavar="ARCHIVO", default=None,
        help="archivo CSV de salida; si se omite, se escribe en la salida estándar",
    )
    parser.add_argument(
        "-d", "--delimiter", metavar="SEP", type=_delimitador, default=",",
        help="delimitador de columnas del CSV (por omisión: la coma)",
    )
    parser.add_argument(
        "--version", action="version",
        version=f"json2csv {VERSION} (build {BUILD})",
        help="muestra la versión y el build, y termina",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Punto de entrada: devuelve el código de salida del proceso."""
    args = _construir_parser().parse_args(argv)
    entrada = None if args.input in (None, "-") else args.input

    try:
        registros = convert(entrada, args.output, args.delimiter)
    except Json2CsvError as exc:
        print(f"error: {exc.message}", file=sys.stderr)
        if exc.hint:
            print(f"sugerencia: {exc.hint}", file=sys.stderr)
        return 1
    except BrokenPipeError:
        try:
            os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        except OSError:
            pass
        print("aviso: la salida fue cerrada antes de completar la conversión",
              file=sys.stderr)
        return 0
    except KeyboardInterrupt:
        print("operación interrumpida por el usuario", file=sys.stderr)
        return 130
    except Exception as exc:  # error inesperado: nunca se oculta
        print(f"error inesperado ({type(exc).__name__}): {exc}", file=sys.stderr)
        return 1

    if args.output is not None:
        print(f"listo: {registros} registro(s) escritos en '{args.output}'", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
