"""Pruebas unitarias de ``json2csv.py`` (punto o de la consigna).

Cada prueba declara su **hipótesis**: el comportamiento esperado y el motivo.
Se cubren las siete etapas del filtro, la conversión completa, la interfaz de
línea de comandos y las condiciones de error. La cobertura exigida por la
consigna es del 85 % o superior.
"""

from __future__ import annotations

import io
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

import json2csv
from json2csv import (
    ConfigurationError,
    DataError,
    InputError,
    OutputError,
    _a_texto,
    _delimitador,
    _describir_error,
    convert,
    fields_filter,
    main,
    output_filter,
    parse_filter,
    records_filter,
    render_filter,
    scalarize_filter,
    source_filter,
)


class _StdinFalso:
    """Objeto que imita ``sys.stdin`` exponiendo ``buffer`` (BytesIO)."""

    def __init__(self, datos: bytes) -> None:
        self.buffer = io.BytesIO(datos)


# ---------------------------------------------------------------------------
# Hipótesis: el registro de VERSION y BUILD se lee de los archivos del proyecto
# ---------------------------------------------------------------------------
def test_version_y_build_se_toman_de_los_archivos() -> None:
    """Si VERSION y BUILD existen, sus valores se exponen en el módulo."""
    raiz = Path(json2csv.__file__).resolve().parent
    version = (raiz / "VERSION").read_text(encoding="utf-8").strip()
    build = (raiz / "BUILD").read_text(encoding="utf-8").strip()
    assert json2csv.VERSION == version
    assert json2csv.BUILD == build


def test_cli_version_muestra_version_y_build(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``--version`` informa VERSION y BUILD y termina con código 0."""
    with pytest.raises(SystemExit) as info:
        main(["--version"])
    assert info.value.code == 0
    salida = capsys.readouterr().out
    assert salida.strip() == f"json2csv {json2csv.VERSION} (build {json2csv.BUILD})"


# ---------------------------------------------------------------------------
# Hipótesis: la etapa origen lee de archivo o de entrada estándar
# ---------------------------------------------------------------------------
def test_source_filter_lee_archivo_linea_por_linea(tmp_path: Path) -> None:
    """Dado un archivo de texto, la etapa entrega sus líneas completas."""
    ruta = tmp_path / "entrada.json"
    ruta.write_text('{"a": 1}\n{"a": 2}\n', encoding="utf-8")
    assert list(source_filter(str(ruta))) == ['{"a": 1}\n', '{"a": 2}\n']


def test_source_filter_tolera_bom(tmp_path: Path) -> None:
    """Un documento UTF-8 con BOM se lee sin la marca de orden de bytes."""
    ruta = tmp_path / "bom.json"
    ruta.write_bytes(b"\xef\xbb\xbf" + b'{"a": 1}\n')
    assert "".join(source_filter(str(ruta))) == '{"a": 1}\n'


def test_source_filter_lee_entrada_estandar(monkeypatch: pytest.MonkeyPatch) -> None:
    """Si no se indica archivo, la etapa lee de la entrada estándar."""
    monkeypatch.setattr(sys, "stdin", _StdinFalso(b'{"a": 1}\n'))
    assert list(source_filter(None)) == ['{"a": 1}\n']


def test_source_filter_archivo_inexistente(tmp_path: Path) -> None:
    """Un archivo que no existe produce InputError con mensaje claro."""
    with pytest.raises(InputError) as info:
        list(source_filter(str(tmp_path / "no_existe.json")))
    assert "no existe" in str(info.value)


def test_source_filter_ruta_es_directorio(tmp_path: Path) -> None:
    """Indicar un directorio como entrada produce InputError."""
    with pytest.raises(InputError) as info:
        list(source_filter(str(tmp_path)))
    assert "directorio" in str(info.value)


def test_source_filter_documento_no_utf8(tmp_path: Path) -> None:
    """Un documento que no es UTF-8 produce InputError con sugerencia."""
    ruta = tmp_path / "binario.json"
    ruta.write_bytes(b'{"a": "\xff\xfe"}')
    with pytest.raises(InputError) as info:
        list(source_filter(str(ruta)))
    assert "no se pudo decodificar" in str(info.value)
    assert info.value.hint is not None


# ---------------------------------------------------------------------------
# Hipótesis: la etapa de análisis convierte texto JSON en estructuras Python
# ---------------------------------------------------------------------------
def test_parse_filter_convierte_objetos() -> None:
    """El análisis devuelve la estructura equivalente al documento."""
    assert parse_filter(['{"a": 1}']) == {"a": 1}
    assert parse_filter(["[1, 2]"]) == [1, 2]


def test_parse_filter_conserva_decimales() -> None:
    """Los números se analizan como Decimal para no perder la representación."""
    documento = parse_filter(['{"a": 1.50}'])
    assert isinstance(documento["a"], Decimal)
    assert documento["a"] == Decimal("1.50")


def test_parse_filter_documento_vacio() -> None:
    """Un documento vacío se rechaza con DataError."""
    with pytest.raises(DataError) as info:
        parse_filter(["   \n"])
    assert "vacío" in str(info.value)


def test_parse_filter_json_invalido() -> None:
    """Un JSON mal formado informa línea y columna del error."""
    with pytest.raises(DataError) as info:
        parse_filter(['{"a": 1,}'])
    mensaje = str(info.value)
    assert "JSON inválido" in mensaje
    assert "línea" in mensaje


# ---------------------------------------------------------------------------
# Hipótesis: la etapa de registros acepta lista de objetos u objeto único
# ---------------------------------------------------------------------------
def test_records_filter_lista_de_objetos() -> None:
    """Una lista de objetos produce un registro por elemento."""
    assert list(records_filter([{"a": 1}, {"b": 2}])) == [{"a": 1}, {"b": 2}]


def test_records_filter_objeto_unico() -> None:
    """Un objeto único produce exactamente un registro."""
    assert list(records_filter({"a": 1})) == [{"a": 1}]


def test_records_filter_no_modifica_el_original() -> None:
    """Los registros se entregan como copias (no se altera el documento)."""
    documento = [{"a": 1}]
    registros = list(records_filter(documento))
    registros[0]["a"] = 99
    assert documento[0]["a"] == 1


def test_records_filter_lista_de_escalares() -> None:
    """Una lista de escalares se rechaza indicando la posición."""
    with pytest.raises(DataError) as info:
        list(records_filter([{"a": 1}, 5]))
    assert str(info.value) == "se esperaba una lista de objetos JSON"
    assert info.value.hint is not None
    assert "posición 1" in info.value.hint


def test_records_filter_documento_escalar() -> None:
    """Un documento escalar se rechaza indicando su tipo."""
    with pytest.raises(DataError) as info:
        list(records_filter(7))
    assert str(info.value) == "se esperaba un objeto JSON o una lista de objetos JSON"
    assert info.value.hint is not None
    assert "tipo int" in info.value.hint


# ---------------------------------------------------------------------------
# Hipótesis: la etapa de valores planos aplica las reglas de conversión
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        (None, ""),
        (True, "true"),
        (False, "false"),
        ("texto", "texto"),
        (Decimal("1.50"), "1.50"),
        (Decimal("1E+5"), "100000"),
        (42, "42"),
        ({"a": 1}, '{"a":1}'),
        ([1, "a"], '[1,"a"]'),
    ],
)
def test_a_texto_aplica_las_reglas(valor: Any, esperado: str) -> None:
    """Cada valor JSON se convierte según las reglas documentadas."""
    assert _a_texto(valor) == esperado


def test_scalarize_filter_convierte_todos_los_valores() -> None:
    """La etapa deja todos los valores del registro como texto."""
    filas = list(scalarize_filter([{"a": None, "b": True, "c": {"x": 1}}]))
    assert filas == [{"a": "", "b": "true", "c": '{"x":1}'}]


# ---------------------------------------------------------------------------
# Hipótesis: la etapa de columnas une las claves en orden de aparición
# ---------------------------------------------------------------------------
def test_fields_filter_une_claves_en_orden() -> None:
    """Las columnas son la unión de claves sin repetir, en orden de aparición."""
    columnas, filas = fields_filter([{"b": "1", "a": "2"}, {"a": "3", "c": "4"}])
    assert columnas == ["b", "a", "c"]
    assert len(filas) == 2


def test_fields_filter_sin_registros() -> None:
    """Sin registros no hay columnas ni filas que escribir."""
    columnas, filas = fields_filter([])
    assert columnas == []
    assert filas == []


# ---------------------------------------------------------------------------
# Hipótesis: la etapa de render produce CSV con encabezado y CRLF
# ---------------------------------------------------------------------------
def test_render_filter_genera_encabezado_y_filas() -> None:
    """El render escribe el encabezado y una fila por registro, con CRLF."""
    texto = "".join(render_filter(["a", "b"], [{"a": "1", "b": "2"}], ","))
    assert texto == "a,b\r\n1,2\r\n"


def test_render_filter_sin_registros_no_escribe() -> None:
    """Sin registros no se escribe nada (ni siquiera el encabezado)."""
    assert list(render_filter(["a"], [], ",")) == []


def test_render_filter_completa_claves_ausentes() -> None:
    """Las claves ausentes en un registro quedan como celda vacía."""
    texto = "".join(render_filter(["a", "b"], [{"a": "1"}], ","))
    assert texto == "a,b\r\n1,\r\n"


def test_render_filter_entrecomilla_cuando_corresponde() -> None:
    """Los valores con comas o comillas se entrecomillan y se duplican éstas."""
    texto = "".join(render_filter(["a"], [{"a": 'x,"y"'}], ","))
    assert texto == 'a\r\n"x,""y"""\r\n'


def test_render_filter_conserva_salto_dentro_de_comillas() -> None:
    """Un salto de línea dentro del valor se mantiene entre las comillas."""
    texto = "".join(render_filter(["a"], [{"a": "1\n2"}], ","))
    assert texto == 'a\r\n"1\n2"\r\n'


def test_render_filter_acepta_otro_delimitador() -> None:
    """El separador de columnas se puede cambiar."""
    texto = "".join(render_filter(["a", "b"], [{"a": "1", "b": "2"}], ";"))
    assert texto == "a;b\r\n1;2\r\n"


# ---------------------------------------------------------------------------
# Hipótesis: la etapa destino escribe en archivo o en la salida estándar
# ---------------------------------------------------------------------------
def test_output_filter_escribe_archivo(tmp_path: Path) -> None:
    """La etapa escribe el CSV completo y devuelve los caracteres escritos."""
    destino = tmp_path / "salida.csv"
    escritos = output_filter(["a,b\r\n", "1,2\r\n"], str(destino))
    assert destino.read_bytes() == b"a,b\r\n1,2\r\n"
    assert escritos == len("a,b\r\n1,2\r\n")


def test_output_filter_escribe_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    """Si no hay archivo de salida, se escribe en la salida estándar."""
    escritos = output_filter(["a,b\r\n"], None)
    assert capsys.readouterr().out == "a,b\r\n"
    assert escritos == 5


def test_output_filter_rechaza_directorio(tmp_path: Path) -> None:
    """Escribir sobre un directorio produce OutputError."""
    with pytest.raises(OutputError) as info:
        output_filter(["x"], str(tmp_path))
    assert "directorio" in str(info.value)


def test_output_filter_directorio_inexistente(tmp_path: Path) -> None:
    """Escribir en un directorio inexistente produce OutputError."""
    with pytest.raises(OutputError) as info:
        output_filter(["x"], str(tmp_path / "no_existe" / "salida.csv"))
    assert "no existe" in str(info.value)


# ---------------------------------------------------------------------------
# Hipótesis: la conversión completa encadena las etapas del filtro
# ---------------------------------------------------------------------------
def test_convert_archivo_a_archivo(tmp_path: Path) -> None:
    """La conversión genera el CSV y devuelve la cantidad de registros."""
    entrada = tmp_path / "entrada.json"
    salida = tmp_path / "salida.csv"
    entrada.write_text('[{"a": 1, "b": null}, {"a": 2}]', encoding="utf-8")
    assert convert(str(entrada), str(salida), ",") == 2
    assert salida.read_bytes() == b"a,b\r\n1,\r\n2,\r\n"


def test_convert_con_otro_delimitador(tmp_path: Path) -> None:
    """El delimitador indicado se usa en todo el CSV."""
    entrada = tmp_path / "e.json"
    salida = tmp_path / "s.csv"
    entrada.write_text('[{"a": 1, "b": 2}]', encoding="utf-8")
    convert(str(entrada), str(salida), ";")
    assert salida.read_bytes() == b"a;b\r\n1;2\r\n"


def test_convert_de_entrada_estandar_a_stdout(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Sin rutas, la conversión lee de stdin y escribe en stdout."""
    monkeypatch.setattr(sys, "stdin", _StdinFalso(b'[{"a": 1, "b": null}]\n'))
    assert convert(None, None, ",") == 1
    assert capsys.readouterr().out == "a,b\r\n1,\r\n"


def test_convert_rechaza_mismo_archivo(tmp_path: Path) -> None:
    """Entrada y salida no pueden ser el mismo archivo."""
    ruta = tmp_path / "datos.json"
    ruta.write_text("[]", encoding="utf-8")
    with pytest.raises(ConfigurationError) as info:
        convert(str(ruta), str(ruta), ",")
    assert "mismo" in str(info.value)


@pytest.mark.parametrize("delimitador", ["", ";;", '"', "\n"])
def test_convert_rechaza_delimitador_invalido(delimitador: str) -> None:
    """El delimitador debe ser un carácter distinto de comilla y salto."""
    with pytest.raises(ConfigurationError):
        convert(None, None, delimitador)


def test_delimitador_valida_un_caracter() -> None:
    """El validador de argparse acepta un carácter y rechaza el resto."""
    assert _delimitador(";") == ";"
    with pytest.raises(Exception):
        _delimitador(";;")


# ---------------------------------------------------------------------------
# Hipótesis: la CLI informa errores por stderr y devuelve códigos de salida
# ---------------------------------------------------------------------------
def test_cli_conversion_exitosa(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Una conversión con -o informa el resumen por la salida de error."""
    entrada = tmp_path / "e.json"
    salida = tmp_path / "s.csv"
    entrada.write_text('[{"a": 1}]', encoding="utf-8")
    assert main(["-i", str(entrada), "-o", str(salida)]) == 0
    assert "listo: 1 registro(s)" in capsys.readouterr().err


def test_cli_error_de_datos(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Un error de datos informa 'error:' y una sugerencia, y devuelve 1."""
    entrada = tmp_path / "e.json"
    entrada.write_text("[]", encoding="utf-8")
    assert main(["-i", str(entrada), "-o", str(tmp_path / "no_existe" / "s.csv")]) == 1
    salida = capsys.readouterr()
    assert "error:" in salida.err
    assert "sugerencia:" not in salida.err  # este caso no lleva sugerencia


def test_cli_error_con_sugerencia(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Los errores que traen sugerencia la muestran por la salida de error."""
    entrada = tmp_path / "e.json"
    entrada.write_text("[1, 2]", encoding="utf-8")
    assert main(["-i", str(entrada)]) == 1
    salida = capsys.readouterr()
    assert "se esperaba una lista de objetos JSON" in salida.err
    assert "posición 0" in salida.err


def test_cli_uso_invalido_sale_con_codigo_2(tmp_path: Path) -> None:
    """Un delimitador de varios caracteres es error de uso (código 2)."""
    entrada = tmp_path / "e.json"
    entrada.write_text("[]", encoding="utf-8")
    with pytest.raises(SystemExit) as info:
        main(["-i", str(entrada), "-d", ";;"])
    assert info.value.code == 2


def test_cli_ayuda_sale_con_codigo_0(capsys: pytest.CaptureFixture[str]) -> None:
    """La opción -h muestra la ayuda y termina con código 0."""
    with pytest.raises(SystemExit) as info:
        main(["-h"])
    assert info.value.code == 0
    assert "usage" in capsys.readouterr().out


def test_cli_salida_cerrada_por_tuberia(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Si la salida se cierra (| head), se avisa y se devuelve 0."""

    def _cortar(*args: Any, **kwargs: Any) -> int:
        raise BrokenPipeError

    monkeypatch.setattr(json2csv, "convert", _cortar)
    assert main(["-i", "entrada.json"]) == 0
    assert "la salida fue cerrada" in capsys.readouterr().err


def test_cli_interrupcion_por_teclado(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Ctrl+C durante la conversión devuelve el código 130."""

    def _interrumpir(*args: Any, **kwargs: Any) -> int:
        raise KeyboardInterrupt

    monkeypatch.setattr(json2csv, "convert", _interrumpir)
    assert main(["-i", "entrada.json"]) == 130
    assert "interrumpida" in capsys.readouterr().err


def test_cli_error_inesperado(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Un error no previsto se informa con su tipo y devuelve 1."""

    def _romper(*args: Any, **kwargs: Any) -> int:
        raise RuntimeError("algo se rompió")

    monkeypatch.setattr(json2csv, "convert", _romper)
    assert main(["-i", "entrada.json"]) == 1
    salida = capsys.readouterr().err
    assert "error inesperado (RuntimeError)" in salida
    assert "algo se rompió" in salida


def test_cli_lee_entrada_estandar(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Sin -i ni -o, la CLI lee de la entrada estándar."""
    monkeypatch.setattr(sys, "stdin", _StdinFalso(b'[{"a": 1, "b": 2}]\n'))
    assert main([]) == 0
    assert capsys.readouterr().out == "a,b\r\n1,2\r\n"


# ---------------------------------------------------------------------------
# Hipótesis: los mensajes de error del sistema son legibles
# ---------------------------------------------------------------------------
def test_describir_error_traduce_errno() -> None:
    """Los códigos de error frecuentes se traducen a mensajes en español."""
    error = OSError(2, "No such file or directory")
    assert "el archivo no existe" in _describir_error("leer", "x.json", error)


def test_describir_error_sin_errno_conocido() -> None:
    """Si el errno no está mapeado se usa el texto del sistema."""
    error = OSError()
    error.errno = None
    assert "no se pudo leer" in _describir_error("leer", "x.json", error)


# ---------------------------------------------------------------------------
# Hipótesis: las rutas defensivas del código se comportan como están previstas
# ---------------------------------------------------------------------------
def test_leer_registro_usa_reserva_si_no_hay_archivo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Si falta el archivo de registro se devuelve el valor de reserva."""
    monkeypatch.setattr(json2csv, "_ROOT", tmp_path)
    assert json2csv._leer_registro("VERSION", "9.9.9") == "9.9.9"


def test_source_filter_stdin_no_utf8(monkeypatch: pytest.MonkeyPatch) -> None:
    """Una entrada estándar que no es UTF-8 produce InputError."""
    monkeypatch.setattr(sys, "stdin", _StdinFalso(b'{"a": "\xff\xfe"}'))
    with pytest.raises(InputError) as info:
        list(source_filter(None))
    assert "entrada estándar" in str(info.value)


def test_parse_filter_error_no_json(monkeypatch: pytest.MonkeyPatch) -> None:
    """Un error de valor ajeno a JSONDecodeError también se envuelve."""
    explotar = ValueError("valor imposible")
    monkeypatch.setattr(
        json2csv.json, "loads", lambda *a, **k: (_ for _ in ()).throw(explotar)
    )
    with pytest.raises(DataError) as info:
        parse_filter(['{"a": 1}'])
    assert "valor imposible" in str(info.value)


def test_validar_rutas_irresolubles(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Si las rutas no se pueden resolver, no se las trata como iguales."""
    monkeypatch.setattr(Path, "resolve", lambda self: (_ for _ in ()).throw(OSError()))
    ruta = tmp_path / "datos.json"
    # No debe lanzar ConfigurationError: no se pudo comparar, se continúa.
    json2csv._validar(str(ruta), str(ruta), ",")


def test_delimitador_rechaza_salto_y_comilla() -> None:
    """El delimitador tampoco puede ser un salto de línea ni la comilla doble."""
    with pytest.raises(Exception):
        _delimitador("\n")
    with pytest.raises(Exception):
        _delimitador('"')
