"""Formulario de consola para cargar observaciones del productor.

La interfaz pregunta los signos clinicos definidos en el README, construye un
modelo Bovino y ejecuta el motor de inferencia para mostrar una orientacion
inicial.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import json
import sys

RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))

try:
    from modelos.bovino import Bovino, crear_bovino_desde_formulario
    from motor.motor_inferencia import explicar_resultado
except ImportError:
    from ..modelos.bovino import Bovino, crear_bovino_desde_formulario  # type: ignore
    from ..motor.motor_inferencia import explicar_resultado  # type: ignore


DatosFormulario = dict[str, Any]


OPCIONES_ESTADO_GENERAL = ("activo", "decaido", "postrado")
OPCIONES_APETITO = ("normal", "bajo", "nulo")
OPCIONES_TIPO_DIARREA = ("liquida", "pastosa", "con moco", "con sangre")
OPCIONES_RUMEN = ("normal", "reducida", "ausente")
OPCIONES_HIDRATACION = ("normal", "leve", "severa")
OPCIONES_TIEMPO = ("horas", "1 dia", "varios dias")


def preguntar_texto(mensaje: str, obligatorio: bool = False) -> str:
    """Pregunta un texto libre."""

    # Repite la pregunta hasta cumplir la condicion de obligatoriedad.
    while True:
        respuesta = input(f"{mensaje}: ").strip()
        if respuesta or not obligatorio:
            return respuesta
        print("Este dato es obligatorio.")


def preguntar_opcion(mensaje: str, opciones: tuple[str, ...]) -> str:
    """Pregunta una opcion numerada y devuelve su valor."""

    # Muestra las opciones numeradas para que el usuario no tenga que escribir exacto.
    while True:
        print(mensaje)
        for indice, opcion in enumerate(opciones, start=1):
            print(f"  {indice}. {opcion}")

        respuesta = input("Seleccione una opcion: ").strip().lower()
        # Se acepta tanto el numero de opcion como el texto literal de la opcion.
        if respuesta.isdigit():
            posicion = int(respuesta) - 1
            if 0 <= posicion < len(opciones):
                return opciones[posicion]

        if respuesta in opciones:
            return respuesta

        print("Opcion no valida. Intente nuevamente.")


def preguntar_si_no(mensaje: str) -> bool:
    """Pregunta una respuesta booleana."""

    # Convierte respuestas humanas simples en booleanos para el motor.
    while True:
        respuesta = input(f"{mensaje} (si/no): ").strip().lower()
        if respuesta in {"si", "s"}:
            return True
        if respuesta in {"no", "n"}:
            return False
        print("Respuesta no valida. Escriba si o no.")


def preguntar_temperatura() -> float | str:
    """Pregunta temperatura como valor numerico o linguistico."""

    # La temperatura puede ingresarse como etiqueta linguistica o como numero en Celsius.
    while True:
        respuesta = input(
            "Temperatura (normal, baja, hipotermia, elevada, muy alta o valor en grados C): "
        ).strip().lower()
        if respuesta in {"normal", "baja", "hipotermia", "elevada", "alta", "muy alta"}:
            return respuesta

        # Se toleran comas decimales y una letra C final para hacerlo mas flexible.
        respuesta_numerica = respuesta.replace(",", ".").replace("c", "").strip()
        try:
            return float(respuesta_numerica)
        except ValueError:
            print("Temperatura no valida. Ejemplo: 39.8, normal o elevada.")


def cargar_datos_interactivos() -> DatosFormulario:
    """Carga los datos del animal mediante preguntas de consola."""

    # Mensaje inicial para recordar el alcance orientativo del sistema.
    print("Sistema Experto Veterinario - Formulario del productor")
    print("El sistema brinda orientacion inicial y no reemplaza al veterinario.")
    print()

    # Se carga cada variable de entrada usando validadores especificos por tipo.
    datos: DatosFormulario = {
        "identificador": preguntar_texto("Identificador del animal"),
        "categoria": preguntar_texto("Categoria del animal"),
        "estado_general": preguntar_opcion("Estado general del animal", OPCIONES_ESTADO_GENERAL),
        "apetito": preguntar_opcion("Apetito", OPCIONES_APETITO),
        "presencia_diarrea": preguntar_si_no("Presenta diarrea"),
        "distension_abdominal": preguntar_si_no("Presenta distension abdominal"),
        "movimientos_rumen": preguntar_opcion("Movimientos del rumen", OPCIONES_RUMEN),
        "hidratacion": preguntar_opcion("Hidratacion estimada", OPCIONES_HIDRATACION),
        "temperatura": preguntar_temperatura(),
        "tiempo_evolucion": preguntar_opcion("Tiempo de evolucion de los sintomas", OPCIONES_TIEMPO),
        "cambios_alimentacion": preguntar_si_no("Hubo cambios recientes en la alimentacion"),
        "observaciones": preguntar_texto("Observaciones adicionales"),
    }

    # El tipo de diarrea solo tiene sentido si el animal presenta diarrea.
    if datos["presencia_diarrea"]:
        datos["tipo_diarrea"] = preguntar_opcion("Tipo de diarrea", OPCIONES_TIPO_DIARREA)
    else:
        datos["tipo_diarrea"] = ""

    return datos


def cargar_datos_desde_json(ruta: str) -> DatosFormulario:
    """Carga datos del formulario desde un archivo JSON."""

    # El JSON permite repetir casos de prueba o cargar datos sin usar el formulario interactivo.
    with open(ruta, "r", encoding="utf-8") as archivo:
        datos = json.load(archivo)

    # Se exige que la raiz del archivo sea un objeto con claves de formulario.
    if not isinstance(datos, dict):
        raise ValueError("El archivo JSON debe contener un objeto con datos del bovino.")
    return datos


def mostrar_resultado(bovino: Bovino, resultado: dict[str, Any]) -> None:
    """Imprime el resultado de forma legible para consola."""

    # Encabezado visual para separar el resultado de las preguntas anteriores.
    print()
    print("Resultado del sistema experto")
    print("-" * 36)

    # La identificacion se muestra solo si fue cargada.
    identificacion = bovino.resumen_identificacion()
    if identificacion["identificador"]:
        print(f"Animal: {identificacion['identificador']}")
    if identificacion["categoria"]:
        print(f"Categoria: {identificacion['categoria']}")

    # explicar_resultado convierte el diccionario tecnico en texto entendible.
    print(explicar_resultado(resultado))
    print()
    print("Aviso: este sistema no reemplaza la evaluacion de un veterinario.")


def ejecutar_formulario(datos: DatosFormulario | None = None, umbral_confianza: float = 0.0) -> dict[str, Any]:
    """Ejecuta el flujo completo de carga, diagnostico y presentacion."""

    # Si no se recibieron datos prearmados, se inicia el cuestionario interactivo.
    datos_formulario = datos if datos is not None else cargar_datos_interactivos()
    # Se transforma el diccionario en el modelo del dominio.
    bovino = crear_bovino_desde_formulario(datos_formulario)
    # El umbral filtra hipotesis de baja confianza sin cambiar los datos de entrada.
    resultado = bovino.diagnosticar(umbral_confianza=umbral_confianza)
    # La consola muestra una explicacion legible y tambien devuelve el resultado estructurado.
    mostrar_resultado(bovino, resultado)
    return resultado


def datos_demo() -> DatosFormulario:
    """Devuelve un caso de ejemplo para probar la interfaz."""

    # Caso representativo de diarrea infecciosa usado por consola y GUI.
    return {
        "identificador": "BOV-001",
        "categoria": "vaca adulta",
        "estado_general": "decaido",
        "apetito": "bajo",
        "presencia_diarrea": True,
        "tipo_diarrea": "liquida",
        "distension_abdominal": False,
        "movimientos_rumen": "reducida",
        "hidratacion": "leve",
        "temperatura": 40.0,
        "tiempo_evolucion": "1 dia",
        "cambios_alimentacion": False,
        "observaciones": "Caso de demostracion.",
    }


def crear_parser() -> argparse.ArgumentParser:
    """Configura argumentos de consola."""

    # Este parser permite ejecutar el formulario de manera independiente a main.py.
    parser = argparse.ArgumentParser(
        description="Formulario de consola para el sistema experto veterinario."
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Ejecuta el formulario con un caso de demostracion.",
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
        help="Umbral minimo de confianza para mostrar hipotesis.",
    )
    return parser


def main() -> None:
    """Punto de entrada de la interfaz."""

    # Se decide la fuente de datos segun los argumentos recibidos.
    argumentos = crear_parser().parse_args()

    if argumentos.demo:
        # El demo evita pedir datos y permite probar rapidamente el motor.
        ejecutar_formulario(datos_demo(), umbral_confianza=argumentos.umbral)
        return

    if argumentos.ruta_json:
        # El modo JSON permite reproducir casos definidos en archivos.
        datos = cargar_datos_desde_json(argumentos.ruta_json)
        ejecutar_formulario(datos, umbral_confianza=argumentos.umbral)
        return

    # Sin argumentos se usa el formulario interactivo.
    ejecutar_formulario(umbral_confianza=argumentos.umbral)


if __name__ == "__main__":
    main()
