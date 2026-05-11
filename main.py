"""Punto de entrada del Sistema Experto Veterinario.

Desde este archivo se puede ejecutar el formulario interactivo, correr un caso
de demostracion o diagnosticar un animal a partir de un archivo JSON.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import json
import sys

RAIZ_PROYECTO = Path(__file__).resolve().parent
if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))

from interfaz.formulario_productor import (  # noqa: E402
    cargar_datos_desde_json,
    datos_demo,
    ejecutar_formulario,
)


NOMBRE_SISTEMA = "Sistema Experto Veterinario"
VERSION = "1.0"


def crear_parser() -> argparse.ArgumentParser:
    """Configura los argumentos disponibles para ejecutar el sistema."""

    # El parser concentra todos los modos de ejecucion disponibles desde consola.
    parser = argparse.ArgumentParser(
        prog="python main.py",
        description=(
            "Sistema experto hibrido para orientacion inicial sobre afecciones "
            "digestivas bovinas."
        ),
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Ejecuta un caso de demostracion sin pedir datos por consola.",
    )
    parser.add_argument(
        "--json",
        dest="ruta_json",
        help="Carga los datos del bovino desde un archivo JSON.",
    )
    parser.add_argument(
        "--umbral",
        type=float,
        default=0.0,
        help="Confianza minima para incluir hipotesis en el resultado. Valor entre 0 y 1.",
    )
    parser.add_argument(
        "--salida-json",
        action="store_true",
        help="Ademas de mostrar el resultado, imprime la salida completa en formato JSON.",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Abre la interfaz grafica para cargar la consulta del productor.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"{NOMBRE_SISTEMA} {VERSION}",
    )
    return parser


def validar_argumentos(argumentos: argparse.Namespace) -> None:
    """Valida combinaciones y rangos de argumentos."""

    # La GUI es un modo independiente, por eso no se combina con entradas de consola.
    if argumentos.gui and (argumentos.demo or argumentos.ruta_json or argumentos.salida_json):
        raise ValueError("Use --gui sin --demo, --json ni --salida-json.")

    # Demo y JSON son dos fuentes de datos distintas; se evita ambiguedad.
    if argumentos.demo and argumentos.ruta_json:
        raise ValueError("Use --demo o --json, no ambos al mismo tiempo.")

    # El umbral se interpreta como proporcion, por eso debe estar entre 0 y 1.
    if not 0.0 <= argumentos.umbral <= 1.0:
        raise ValueError("El umbral debe estar entre 0 y 1.")


def seleccionar_datos(argumentos: argparse.Namespace) -> dict[str, Any] | None:
    """Obtiene datos segun el modo de ejecucion elegido."""

    # Con --demo se usa un caso interno ya preparado.
    if argumentos.demo:
        return datos_demo()

    # Con --json se carga el archivo indicado por el usuario.
    if argumentos.ruta_json:
        return cargar_datos_desde_json(argumentos.ruta_json)

    # Si no hay fuente predefinida, el formulario de consola preguntara los datos.
    return None


def imprimir_salida_json(resultado: dict[str, Any]) -> None:
    """Imprime el resultado completo en formato JSON."""

    # Se imprime separado de la explicacion legible para distinguir la salida estructurada.
    print()
    print("Salida JSON")
    print("-" * 36)
    print(json.dumps(resultado, indent=2, ensure_ascii=False))


def ejecutar(argumentos: argparse.Namespace) -> int:
    """Ejecuta el sistema y devuelve codigo de salida."""

    # Primero se validan combinaciones para fallar antes de abrir GUI o pedir datos.
    validar_argumentos(argumentos)

    # Si se pidio GUI, se importa Tkinter recien aqui y se abre la ventana.
    if argumentos.gui:
        from GUI.interfaz_grafica import iniciar_gui

        iniciar_gui(umbral_confianza=argumentos.umbral)
        return 0

    # En modo consola se obtiene la fuente de datos y se ejecuta el formulario.
    datos = seleccionar_datos(argumentos)
    resultado = ejecutar_formulario(datos=datos, umbral_confianza=argumentos.umbral)

    # La salida JSON es opcional para no sobrecargar el uso normal por consola.
    if argumentos.salida_json:
        imprimir_salida_json(resultado)

    return 0


def main() -> int:
    """Funcion principal invocada desde consola."""

    # Se parsean los argumentos antes de entrar al flujo principal.
    parser = crear_parser()
    argumentos = parser.parse_args()

    try:
        # ejecutar devuelve el codigo de salida final del programa.
        return ejecutar(argumentos)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        # Los errores esperados se muestran en stderr y devuelven codigo 1.
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        # Ctrl+C se informa como cancelacion voluntaria.
        print("\nOperacion cancelada por el usuario.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
