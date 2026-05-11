"""Motor de inferencia para el sistema experto veterinario.

El motor aplica encadenamiento hacia adelante sobre los hechos ingresados por
el productor. Actualmente integra las reglas digestivas, pero deja una
estructura simple para sumar nuevos modulos de reglas.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import json
import sys
import unicodedata

RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))

try:
    from reglas.reglas_digestivas import (
        derivar_hechos_digestivos,
        evaluar_reglas_digestivas,
    )
except ImportError:
    from ..reglas.reglas_digestivas import (  # type: ignore
        derivar_hechos_digestivos,
        evaluar_reglas_digestivas,
    )


Hechos = dict[str, Any]


VARIABLES_ENTRADA = (
    "estado_general",
    "apetito",
    "presencia_diarrea",
    "tipo_diarrea",
    "distension_abdominal",
    "movimientos_rumen",
    "hidratacion",
    "temperatura",
    "tiempo_evolucion",
    "cambios_alimentacion",
)

VARIABLES_BOOLEANAS = {
    "presencia_diarrea",
    "distension_abdominal",
    "cambios_alimentacion",
    "inquietud",
    "dificultad_respiratoria",
    "exceso_pasturas_tiernas",
    "consumo_leguminosas",
}

VALORES_VALIDOS = {
    "estado_general": {"activo", "decaido", "postrado"},
    "apetito": {"normal", "bajo", "nulo"},
    "tipo_diarrea": {"", "liquida", "pastosa", "con moco", "moco", "con sangre", "sangre"},
    "movimientos_rumen": {"normal", "reducida", "ausente"},
    "hidratacion": {"normal", "leve", "severa"},
    "tiempo_evolucion": {"horas", "1 dia", "un dia", "varios dias"},
}

SIN_DIAGNOSTICO = {
    "diagnostico_presuntivo": "Sin diagnostico digestivo concluyente",
    "nivel_confianza": 0.0,
    "gravedad": "leve",
    "accion_recomendada": (
        "Continuar observacion, registrar temperatura, apetito y evolucion. "
        "Consultar al veterinario si aparecen diarrea, distension, fiebre o postracion."
    ),
    "requiere_veterinario": False,
}


@dataclass
class ResultadoInferencia:
    """Resultado completo de una ejecucion del motor."""

    diagnostico_presuntivo: str
    nivel_confianza: float
    gravedad: str
    accion_recomendada: str
    requiere_veterinario: bool
    hipotesis: list[dict[str, Any]] = field(default_factory=list)
    hechos_iniciales: Hechos = field(default_factory=dict)
    hechos_derivados: Hechos = field(default_factory=dict)
    advertencias: list[str] = field(default_factory=list)

    def como_diccionario(self) -> dict[str, Any]:
        """Devuelve el resultado en formato serializable."""

        # Se arma un diccionario puro para poder imprimirlo como JSON o pasarlo a la GUI.
        return {
            "diagnostico_presuntivo": self.diagnostico_presuntivo,
            "nivel_confianza": self.nivel_confianza,
            "gravedad": self.gravedad,
            "accion_recomendada": self.accion_recomendada,
            "requiere_veterinario": self.requiere_veterinario,
            "hipotesis": self.hipotesis,
            "hechos_iniciales": self.hechos_iniciales,
            "hechos_derivados": self.hechos_derivados,
            "advertencias": self.advertencias,
        }


class MotorInferencia:
    """Ejecuta el razonamiento del sistema experto."""

    def __init__(self, umbral_confianza: float = 0.0) -> None:
        # El umbral funciona como filtro de hipotesis y debe ser una proporcion valida.
        if not 0.0 <= umbral_confianza <= 1.0:
            raise ValueError("El umbral de confianza debe estar entre 0 y 1.")
        self.umbral_confianza = umbral_confianza

    def inferir(self, hechos: Hechos) -> ResultadoInferencia:
        """Ejecuta el motor y devuelve un resultado estructurado."""

        # Primero se homogenizan los datos para que las reglas reciban valores comparables.
        hechos_normalizados, advertencias = normalizar_hechos(hechos)
        # Despues se agregan advertencias por datos faltantes o dominios invalidos.
        advertencias.extend(validar_hechos(hechos_normalizados))

        # Los hechos derivados representan condiciones clinicas simples usadas por las reglas.
        hechos_derivados = derivar_hechos_digestivos(hechos_normalizados)
        # Se evaluan todas las reglas digestivas y se conservan las hipotesis que superan el umbral.
        hipotesis = evaluar_reglas_digestivas(hechos_normalizados)
        hipotesis = [
            hipotesis_item
            for hipotesis_item in hipotesis
            if hipotesis_item["nivel_confianza"] >= self.umbral_confianza
        ]

        # La primera hipotesis ya viene ordenada por confianza; si no hay ninguna, se usa salida neutra.
        principal = hipotesis[0] if hipotesis else SIN_DIAGNOSTICO
        return ResultadoInferencia(
            diagnostico_presuntivo=principal["diagnostico_presuntivo"],
            nivel_confianza=principal["nivel_confianza"],
            gravedad=principal["gravedad"],
            accion_recomendada=principal["accion_recomendada"],
            requiere_veterinario=principal["requiere_veterinario"],
            hipotesis=hipotesis,
            hechos_iniciales=hechos_normalizados,
            hechos_derivados=hechos_derivados,
            advertencias=advertencias,
        )


def _normalizar_texto(valor: Any) -> str:
    # None se trata como texto vacio para simplificar validaciones posteriores.
    if valor is None:
        return ""
    # Se pasa a minusculas, se recortan espacios y se quitan acentos.
    texto = str(valor).strip().lower()
    texto = unicodedata.normalize("NFD", texto)
    return "".join(caracter for caracter in texto if unicodedata.category(caracter) != "Mn")


def _normalizar_booleano(valor: Any) -> bool | None:
    # Si ya llega como bool, no hace falta interpretarlo.
    if isinstance(valor, bool):
        return valor

    # Se aceptan varias formas comunes de escribir si/no.
    texto = _normalizar_texto(valor)
    if texto in {"si", "s", "true", "verdadero", "1"}:
        return True
    if texto in {"no", "n", "false", "falso", "0"}:
        return False
    return None


def _normalizar_temperatura(valor: Any) -> float | str:
    # Los numeros se convierten a float para que las reglas puedan comparar rangos.
    if isinstance(valor, (int, float)):
        return float(valor)

    # Tambien se permiten etiquetas linguisticas usadas por productores.
    texto = _normalizar_texto(valor)
    if texto in {"normal", "baja", "hipotermia", "elevada", "alta", "muy alta", ""}:
        return texto

    # Si el usuario escribio "39,8 C", se limpia antes de intentar convertir.
    texto_numerico = texto.replace(",", ".").replace("c", "").strip()
    try:
        return float(texto_numerico)
    except ValueError:
        return texto


def normalizar_hechos(hechos: Hechos) -> tuple[Hechos, list[str]]:
    """Convierte entradas del usuario a un formato esperado por las reglas."""

    # normalizados contiene los datos listos para reglas; advertencias registra problemas no fatales.
    normalizados: Hechos = {}
    advertencias: list[str] = []

    # Cada clave se normaliza segun su tipo esperado.
    for clave, valor in hechos.items():
        if clave in VARIABLES_BOOLEANAS:
            booleano = _normalizar_booleano(valor)
            if booleano is None:
                # Se mantiene el valor original si no se pudo interpretar, pero se avisa.
                advertencias.append(f"No se pudo interpretar {clave} como valor booleano.")
                normalizados[clave] = valor
            else:
                normalizados[clave] = booleano
        elif clave == "temperatura":
            normalizados[clave] = _normalizar_temperatura(valor)
        elif isinstance(valor, str):
            normalizados[clave] = _normalizar_texto(valor)
        else:
            normalizados[clave] = valor

    # Si no hay diarrea, el tipo de diarrea no aplica y queda vacio.
    if not normalizados.get("presencia_diarrea"):
        normalizados.setdefault("tipo_diarrea", "")

    return normalizados, advertencias


def validar_hechos(hechos: Hechos) -> list[str]:
    """Genera advertencias por datos faltantes o valores fuera del dominio."""

    advertencias: list[str] = []

    # tipo_diarrea solo se exige cuando presencia_diarrea es verdadero.
    variables_requeridas = [
        variable
        for variable in VARIABLES_ENTRADA
        if variable != "tipo_diarrea" or hechos.get("presencia_diarrea")
    ]
    # Se listan variables ausentes o vacias para informar carga incompleta.
    faltantes = [
        variable
        for variable in variables_requeridas
        if variable not in hechos or hechos.get(variable) in {None, ""}
    ]
    if faltantes:
        advertencias.append("Faltan datos de entrada: " + ", ".join(faltantes) + ".")

    # Las variables categoricas se comparan con el dominio permitido.
    for clave, permitidos in VALORES_VALIDOS.items():
        valor = hechos.get(clave)
        if valor is None or valor == "":
            continue
        if isinstance(valor, str) and valor not in permitidos:
            advertencias.append(f"Valor no reconocido para {clave}: {valor}.")

    # Rango amplio para detectar temperaturas bovinas claramente improbables.
    # Los extremos <20 y >50 tienen reglas especiales, por eso no se advierten aqui.
    temperatura = hechos.get("temperatura")
    if (
        isinstance(temperatura, (int, float))
        and not 35.0 <= float(temperatura) <= 43.5
        and not (float(temperatura) < 20.0 or float(temperatura) > 50.0)
    ):
        advertencias.append("La temperatura ingresada esta fuera del rango bovino esperado.")

    return advertencias


def inferir(hechos: Hechos, umbral_confianza: float = 0.0) -> dict[str, Any]:
    """Funcion de conveniencia para usar el motor sin instanciar la clase."""

    # Se crea una instancia corta del motor y se devuelve la version serializable.
    motor = MotorInferencia(umbral_confianza=umbral_confianza)
    return motor.inferir(hechos).como_diccionario()


def explicar_resultado(resultado: ResultadoInferencia | dict[str, Any]) -> str:
    """Crea una explicacion breve y legible del resultado."""

    # La funcion acepta tanto el dataclass como el diccionario final.
    datos = resultado.como_diccionario() if isinstance(resultado, ResultadoInferencia) else resultado
    # Lineas principales que siempre se muestran.
    lineas = [
        f"Diagnostico presuntivo: {datos['diagnostico_presuntivo']}",
        f"Confianza: {datos['nivel_confianza']}",
        f"Gravedad: {datos['gravedad']}",
        f"Requiere veterinario: {'si' if datos['requiere_veterinario'] else 'no'}",
        f"Accion recomendada: {datos['accion_recomendada']}",
    ]

    # Si hubo reglas activadas, se detallan como hipotesis evaluadas.
    if datos.get("hipotesis"):
        lineas.append("Hipotesis evaluadas:")
        for hipotesis in datos["hipotesis"]:
            evidencia = ", ".join(hipotesis.get("evidencia", [])) or "sin evidencia detallada"
            lineas.append(
                f"- {hipotesis['diagnostico_presuntivo']} "
                f"({hipotesis['nivel_confianza']}): {evidencia}"
            )

    # Las advertencias ayudan a detectar entradas incompletas o poco confiables.
    if datos.get("advertencias"):
        lineas.append("Advertencias:")
        lineas.extend(f"- {advertencia}" for advertencia in datos["advertencias"])

    return "\n".join(lineas)


if __name__ == "__main__":
    caso_demo = {
        "estado_general": "decaido",
        "apetito": "bajo",
        "presencia_diarrea": "si",
        "tipo_diarrea": "liquida",
        "distension_abdominal": "no",
        "movimientos_rumen": "reducida",
        "hidratacion": "leve",
        "temperatura": "40.0",
        "tiempo_evolucion": "1 dia",
        "cambios_alimentacion": "no",
    }
    resultado_demo = inferir(caso_demo)
    print(json.dumps(resultado_demo, indent=2, ensure_ascii=False))
