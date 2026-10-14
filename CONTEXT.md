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
- **Alcance**: programa principal y puntos (a) a (h). Los puntos (i) a (u)
  quedan pendientes (ver `CHANGELOG.md`).

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

## Decisiones propias (no pedidas explícitamente)

- **"Estrategia de filtro"** se interpretó como arquitectura pipe-and-filter:
  siete etapas independientes (origen, análisis JSON, registros, valores
  planos, columnas, render CSV y destino) encadenadas mediante generadores
  dentro de un único archivo.
- **Reglas de conversión** que la consigna no especificaba: `null` → celda
  vacía; booleanos → `true`/`false`; los números conservan la representación
  del documento original; objetos y arreglos anidados → JSON compacto; las
  columnas son la unión de las claves en orden de primera aparición; fin de
  línea `\r\n` (RFC 4180) y entrecomillado mínimo.
- **Códigos de salida** formalizados: 0 (correcto), 1 (error), 2 (error de uso
  de la línea de comandos), 130 (Ctrl+C).
- **Estructura mínima**: un solo archivo `json2csv.py` más los archivos que
  pide la consigna (README, CHANGELOG, CONTEXT, REQUIREMENTS.TXT, LICENSE,
  VERSION, BUILD). La plantilla de Cookiectter y la documentación generada con
  pdoc se mantienen **fuera** del repositorio para no engordar la entrega.
- **Se descartó** la opción `-e/--encoding` que se había agregado en una
  primera versión: el programa trabaja siempre con UTF-8 (aceptando BOM).

## Verificación

Se ejecutó una suite de 33 pruebas de humo por subproceso dentro del ambiente
virtual (casos válidos, delimitadores, entrada y salida estándar, documento con
BOM, y 12 condiciones de error controladas). Todas las pruebas finalizaron en
verde.

## Nota de transparencia

El código se generó con asistencia de IA y fue revisado y verificado
manualmente por el autor; las decisiones quedan documentadas en este archivo y
en `README.md`.
