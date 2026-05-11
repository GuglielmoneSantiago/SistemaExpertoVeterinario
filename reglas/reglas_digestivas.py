"""Reglas digestivas para el sistema experto veterinario.

El modulo implementa reglas SI-ENTONCES con un calculo simple de confianza.
Cada regla aporta un diagnostico presuntivo cuando coinciden sus condiciones.
No reemplaza el criterio veterinario: solo organiza orientacion inicial.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable
import unicodedata


Hechos = dict[str, Any]
Predicado = Callable[[Hechos], bool]


@dataclass(frozen=True)
class Condicion:
    """Condicion clinica evaluable dentro de una regla."""

    descripcion: str
    predicado: Predicado
    peso: float = 1.0


@dataclass(frozen=True)
class ReglaDigestiva:
    """Regla SI-ENTONCES orientada a diagnostico digestivo."""

    codigo: str
    nombre: str
    diagnostico: str
    condiciones: tuple[Condicion, ...]
    confianza_base: float
    gravedad: str
    accion_recomendada: str
    requiere_veterinario: bool
    condiciones_requeridas: tuple[Predicado, ...] = ()

    def evaluar(self, hechos: Hechos) -> dict[str, Any] | None:
        """Evalua la regla y devuelve una conclusion si hay evidencia suficiente."""

        # Las condiciones requeridas son puertas de entrada: si fallan, la regla no aplica.
        if any(not predicado(hechos) for predicado in self.condiciones_requeridas):
            return None

        # Se calcula el peso total para medir que proporcion de evidencia se cumple.
        peso_total = sum(condicion.peso for condicion in self.condiciones)
        condiciones_cumplidas = [
            condicion
            for condicion in self.condiciones
            if condicion.predicado(hechos)
        ]
        peso_cumplido = sum(condicion.peso for condicion in condiciones_cumplidas)

        # Una regla sin peso no puede aportar confianza.
        if peso_total == 0:
            return None

        # Si se cumple poca evidencia, la regla se descarta.
        proporcion = peso_cumplido / peso_total
        if proporcion < 0.55:
            return None

        # La confianza combina la base de la regla con la proporcion de evidencia cumplida.
        confianza = min(1.0, round(self.confianza_base * proporcion, 2))
        return {
            "codigo_regla": self.codigo,
            "regla": self.nombre,
            "diagnostico_presuntivo": self.diagnostico,
            "nivel_confianza": confianza,
            "gravedad": self.gravedad,
            "accion_recomendada": self.accion_recomendada,
            "requiere_veterinario": self.requiere_veterinario,
            "evidencia": [condicion.descripcion for condicion in condiciones_cumplidas],
        }


def _normalizar_texto(valor: Any) -> str:
    # None se interpreta como texto vacio para evitar errores de comparacion.
    if valor is None:
        return ""

    # La normalizacion permite comparar "decaido" y "decaido" aunque haya acentos.
    texto = str(valor).strip().lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(caracter for caracter in texto if unicodedata.category(caracter) != "Mn")
    return texto


def _valor(hechos: Hechos, clave: str) -> str:
    # Extrae y normaliza un hecho textual por clave.
    return _normalizar_texto(hechos.get(clave))


def _es_verdadero(hechos: Hechos, clave: str) -> bool:
    # Si el dato ya es booleano, se usa directamente.
    valor = hechos.get(clave)
    if isinstance(valor, bool):
        return valor
    # Si viene como texto, se aceptan variantes comunes de verdadero.
    return _normalizar_texto(valor) in {"si", "s", "true", "1", "verdadero"}


def _esta_en(hechos: Hechos, clave: str, opciones: set[str]) -> bool:
    # Predicado generico para chequear si una variable pertenece a un conjunto esperado.
    return _valor(hechos, clave) in opciones


def _temperatura_float(hechos: Hechos) -> float | None:
    # Intenta convertir la temperatura a numero para poder comparar umbrales.
    valor = hechos.get("temperatura")
    if isinstance(valor, (int, float)):
        return float(valor)

    # Tambien se toleran valores textuales como "40,5 C".
    texto = _normalizar_texto(valor).replace(",", ".").replace("c", "")
    try:
        return float(texto)
    except (TypeError, ValueError):
        return None


def _temperatura_elevada(hechos: Hechos) -> bool:
    # Con numero se usa el umbral bovino; con texto se usan etiquetas linguisticas.
    temperatura = _temperatura_float(hechos)
    if temperatura is not None:
        return temperatura >= 39.5
    return _esta_en(hechos, "temperatura", {"elevada", "alta", "muy alta"})


def _temperatura_muy_alta(hechos: Hechos) -> bool:
    # La fiebre muy alta exige un umbral mayor o la etiqueta explicita.
    temperatura = _temperatura_float(hechos)
    if temperatura is not None:
        return temperatura >= 40.5
    return _esta_en(hechos, "temperatura", {"muy alta"})


def _temperatura_baja(hechos: Hechos) -> bool:
    # La hipotermia se considera cuando la temperatura bovina esta por debajo de 37 C.
    temperatura = _temperatura_float(hechos)
    if temperatura is not None:
        return temperatura < 37.0
    return _esta_en(hechos, "temperatura", {"baja", "hipotermia"})


def _sin_diarrea_o_no_indicada(hechos: Hechos) -> bool:
    # Se usa en reglas como timpanismo, donde la ausencia de diarrea refuerza el patron.
    return not _es_verdadero(hechos, "presencia_diarrea")


def _diarrea(hechos: Hechos) -> bool:
    # Predicado corto para consultar presencia de diarrea.
    return _es_verdadero(hechos, "presencia_diarrea")


def _diarrea_tipo(*tipos: str) -> Predicado:
    # Se normalizan los tipos al crear el predicado para no repetir trabajo al evaluarlo.
    tipos_normalizados = {_normalizar_texto(tipo) for tipo in tipos}

    def predicado(hechos: Hechos) -> bool:
        # Solo se considera el tipo si efectivamente hay diarrea.
        return _diarrea(hechos) and _esta_en(hechos, "tipo_diarrea", tipos_normalizados)

    return predicado


def _hidratacion(*niveles: str) -> Predicado:
    # Devuelve un predicado reutilizable para uno o varios niveles de hidratacion.
    niveles_normalizados = {_normalizar_texto(nivel) for nivel in niveles}
    return lambda hechos: _esta_en(hechos, "hidratacion", niveles_normalizados)


def _estado_general(*estados: str) -> Predicado:
    # Devuelve un predicado para consultar estado general contra varios estados posibles.
    estados_normalizados = {_normalizar_texto(estado) for estado in estados}
    return lambda hechos: _esta_en(hechos, "estado_general", estados_normalizados)


def _apetito(*valores: str) -> Predicado:
    # Devuelve un predicado para evaluar apetito bajo, nulo u otros valores.
    valores_normalizados = {_normalizar_texto(valor) for valor in valores}
    return lambda hechos: _esta_en(hechos, "apetito", valores_normalizados)


def _rumen(*valores: str) -> Predicado:
    # Devuelve un predicado para actividad ruminal normal, reducida o ausente.
    valores_normalizados = {_normalizar_texto(valor) for valor in valores}
    return lambda hechos: _esta_en(hechos, "movimientos_rumen", valores_normalizados)


def _tiempo(*valores: str) -> Predicado:
    # Devuelve un predicado para comparar el tiempo de evolucion informado.
    valores_normalizados = {_normalizar_texto(valor) for valor in valores}
    return lambda hechos: _esta_en(hechos, "tiempo_evolucion", valores_normalizados)


def derivar_hechos_digestivos(hechos: Hechos) -> Hechos:
    """Agrega hechos clinicos simples usados por el encadenamiento hacia adelante."""

    # Se copia la entrada para conservar los hechos originales junto con los derivados.
    derivados = dict(hechos)
    # Cada derivado resume una condicion clinica que varias reglas pueden reutilizar.
    derivados["fiebre"] = _temperatura_elevada(hechos)
    derivados["fiebre_muy_alta"] = _temperatura_muy_alta(hechos)
    derivados["hipotermia"] = _temperatura_baja(hechos)
    derivados["diarrea_con_sangre"] = _diarrea_tipo("con sangre", "sangre")(hechos)
    derivados["diarrea_con_moco"] = _diarrea_tipo("con moco", "moco")(hechos)
    derivados["rumen_comprometido"] = _rumen("reducida", "ausente")(hechos)
    derivados["rumen_ausente"] = _rumen("ausente")(hechos)
    derivados["anorexia"] = _apetito("nulo")(hechos)
    derivados["deshidratacion"] = _hidratacion("leve", "severa")(hechos)
    derivados["deshidratacion_severa"] = _hidratacion("severa")(hechos)
    derivados["cuadro_prolongado"] = _tiempo("varios dias", "varios dias")(hechos)
    derivados["cambio_dieta"] = _es_verdadero(hechos, "cambios_alimentacion")
    return derivados


def _hecho(clave: str) -> Predicado:
    # Convierte una clave booleana del diccionario en un predicado de regla.
    return lambda hechos: bool(hechos.get(clave))


REGLAS_DIGESTIVAS: tuple[ReglaDigestiva, ...] = (
    ReglaDigestiva(
        codigo="RD-01",
        nombre="Diarrea infecciosa o enteritis",
        diagnostico="Diarrea infecciosa / enteritis",
        confianza_base=0.86,
        gravedad="moderado",
        accion_recomendada=(
            "Aislar al animal, ofrecer agua limpia, iniciar rehidratacion y consultar "
            "al veterinario si hay fiebre, sangre o empeoramiento."
        ),
        requiere_veterinario=True,
        condiciones=(
            Condicion("presencia de diarrea", _diarrea, 1.2),
            Condicion("diarrea liquida", _diarrea_tipo("liquida", "liquida"), 1.1),
            Condicion("temperatura elevada", _hecho("fiebre"), 1.0),
            Condicion("estado general decaido o postrado", _estado_general("decaido", "postrado"), 1.0),
            Condicion("apetito bajo o nulo", _apetito("bajo", "nulo"), 0.8),
            Condicion("deshidratacion leve o severa", _hecho("deshidratacion"), 0.9),
        ),
        condiciones_requeridas=(_diarrea,),
    ),
    ReglaDigestiva(
        codigo="RD-02",
        nombre="Coccidiosis o lesion intestinal",
        diagnostico="Coccidiosis / lesion intestinal con diarrea sanguinolenta",
        confianza_base=0.9,
        gravedad="grave",
        accion_recomendada=(
            "Contactar al veterinario, aislar al animal y priorizar rehidratacion. "
            "La presencia de sangre requiere evaluacion profesional."
        ),
        requiere_veterinario=True,
        condiciones=(
            Condicion("diarrea con sangre", _hecho("diarrea_con_sangre"), 1.5),
            Condicion("estado general decaido o postrado", _estado_general("decaido", "postrado"), 1.0),
            Condicion("apetito bajo o nulo", _apetito("bajo", "nulo"), 0.7),
            Condicion("deshidratacion leve o severa", _hecho("deshidratacion"), 0.9),
            Condicion("cuadro de 1 dia o varios dias", _tiempo("1 dia", "un dia", "varios dias"), 0.6),
        ),
        condiciones_requeridas=(_hecho("diarrea_con_sangre"),),
    ),
    ReglaDigestiva(
        codigo="RD-03",
        nombre="Timpanismo o empaste",
        diagnostico="Timpanismo / empaste ruminal",
        confianza_base=0.88,
        gravedad="grave",
        accion_recomendada=(
            "Retirar alimento fermentable, evitar que el animal se eche y llamar al "
            "veterinario de inmediato si la distension aumenta o hay dificultad."
        ),
        requiere_veterinario=True,
        condiciones=(
            Condicion("distension abdominal", lambda hechos: _es_verdadero(hechos, "distension_abdominal"), 1.5),
            Condicion("movimientos ruminales reducidos o ausentes", _hecho("rumen_comprometido"), 1.1),
            Condicion("sin diarrea marcada", _sin_diarrea_o_no_indicada, 0.6),
            Condicion("cambio reciente de alimentacion", _hecho("cambio_dieta"), 0.8),
            Condicion("estado general decaido o postrado", _estado_general("decaido", "postrado"), 0.8),
        ),
        condiciones_requeridas=(lambda hechos: _es_verdadero(hechos, "distension_abdominal"),),
    ),
    ReglaDigestiva(
        codigo="RD-04",
        nombre="Indigestion simple o acidosis ruminal leve",
        diagnostico="Indigestion digestiva / posible acidosis ruminal",
        confianza_base=0.78,
        gravedad="moderado",
        accion_recomendada=(
            "Suspender cambios bruscos de dieta, ofrecer fibra y agua, observar la "
            "evolucion y consultar si no mejora en pocas horas."
        ),
        requiere_veterinario=False,
        condiciones=(
            Condicion("cambio reciente de alimentacion", _hecho("cambio_dieta"), 1.2),
            Condicion("apetito bajo o nulo", _apetito("bajo", "nulo"), 1.0),
            Condicion("movimientos ruminales reducidos", _rumen("reducida"), 0.9),
            Condicion("diarrea pastosa o liquida", _diarrea_tipo("pastosa", "liquida"), 0.7),
            Condicion("temperatura normal", lambda hechos: not _temperatura_elevada(hechos), 0.5),
        ),
        condiciones_requeridas=(
            lambda hechos: hechos.get("cambio_dieta") or _rumen("reducida")(hechos),
        ),
    ),
    ReglaDigestiva(
        codigo="RD-05",
        nombre="Deshidratacion secundaria a diarrea",
        diagnostico="Deshidratacion asociada a cuadro digestivo",
        confianza_base=0.84,
        gravedad="grave",
        accion_recomendada=(
            "Priorizar rehidratacion y contactar al veterinario, especialmente si el "
            "animal esta postrado o no bebe por cuenta propia."
        ),
        requiere_veterinario=True,
        condiciones=(
            Condicion("presencia de diarrea", _diarrea, 1.0),
            Condicion("hidratacion severa", _hecho("deshidratacion_severa"), 1.4),
            Condicion("estado general postrado", _estado_general("postrado"), 1.1),
            Condicion("apetito nulo", _apetito("nulo"), 0.7),
            Condicion("cuadro prolongado", _hecho("cuadro_prolongado"), 0.8),
        ),
        condiciones_requeridas=(_hecho("deshidratacion_severa"),),
    ),
    ReglaDigestiva(
        codigo="RD-06",
        nombre="Alerta digestiva febril",
        diagnostico="Proceso digestivo agudo con compromiso sistemico",
        confianza_base=0.82,
        gravedad="grave",
        accion_recomendada=(
            "Solicitar atencion veterinaria. Fiebre muy alta con decaimiento puede "
            "indicar un cuadro agudo que necesita tratamiento especifico."
        ),
        requiere_veterinario=True,
        condiciones=(
            Condicion("temperatura muy alta", _hecho("fiebre_muy_alta"), 1.4),
            Condicion("estado general decaido o postrado", _estado_general("decaido", "postrado"), 1.0),
            Condicion("apetito bajo o nulo", _apetito("bajo", "nulo"), 0.8),
            Condicion("diarrea o rumen comprometido", lambda hechos: _diarrea(hechos) or hechos.get("rumen_comprometido"), 0.9),
        ),
        condiciones_requeridas=(_hecho("fiebre_muy_alta"),),
    ),
    ReglaDigestiva(
        codigo="RD-07",
        nombre="Hipotermia con compromiso sistemico",
        diagnostico="Hipotermia / posible shock digestivo o septicemia",
        confianza_base=0.89,
        gravedad="grave",
        accion_recomendada=(
            "Abrigarlo, evitar exposicion al frio, ofrecer soporte de hidratacion si puede "
            "beber y contactar al veterinario de urgencia. Temperaturas menores a 37 C "
            "pueden indicar shock, septicemia o compromiso sistemico severo."
        ),
        requiere_veterinario=True,
        condiciones=(
            Condicion("temperatura menor a 37 C o hipotermia", _hecho("hipotermia"), 1.4),
            Condicion("estado general decaido o postrado", _estado_general("decaido", "postrado"), 1.0),
            Condicion("apetito bajo o nulo", _apetito("bajo", "nulo"), 0.8),
            Condicion("movimientos ruminales reducidos o ausentes", _hecho("rumen_comprometido"), 0.8),
            Condicion("deshidratacion leve o severa", _hecho("deshidratacion"), 0.7),
            Condicion("cuadro prolongado", _hecho("cuadro_prolongado"), 0.5),
        ),
        condiciones_requeridas=(_hecho("hipotermia"),),
    ),
)


def evaluar_reglas_digestivas(hechos: Hechos) -> list[dict[str, Any]]:
    """Evalua todas las reglas digestivas y ordena conclusiones por confianza."""

    # Antes de evaluar se calculan hechos derivados como fiebre o deshidratacion.
    hechos_derivados = derivar_hechos_digestivos(hechos)
    # Cada regla devuelve una conclusion si alcanza evidencia suficiente.
    conclusiones = [
        conclusion
        for regla in REGLAS_DIGESTIVAS
        if (conclusion := regla.evaluar(hechos_derivados)) is not None
    ]
    # La GUI y el motor toman como principal la primera conclusion de esta lista.
    return sorted(conclusiones, key=lambda item: item["nivel_confianza"], reverse=True)


def diagnostico_principal(hechos: Hechos) -> dict[str, Any]:
    """Devuelve el diagnostico mas probable o una conclusion de observacion."""

    # Se evalua el conjunto completo y se toma la conclusion de mayor confianza.
    conclusiones = evaluar_reglas_digestivas(hechos)
    if conclusiones:
        return conclusiones[0]

    # Si ninguna regla aplica, se devuelve una conclusion neutra de seguimiento.
    return {
        "codigo_regla": "RD-00",
        "regla": "Sin patron digestivo suficiente",
        "diagnostico_presuntivo": "Sin diagnostico digestivo concluyente",
        "nivel_confianza": 0.0,
        "gravedad": "leve",
        "accion_recomendada": (
            "Continuar observacion, registrar temperatura, apetito y evolucion. "
            "Consultar al veterinario si aparecen diarrea, distension, fiebre o postracion."
        ),
        "requiere_veterinario": False,
        "evidencia": [],
    }


def generar_informe_digestivo(hechos: Hechos) -> dict[str, Any]:
    """Construye la salida esperada por el sistema experto."""

    # Reune todas las hipotesis para mostrar no solo el diagnostico principal.
    conclusiones = evaluar_reglas_digestivas(hechos)
    # Si no hay hipotesis, se usa la respuesta sin diagnostico concluyente.
    principal = conclusiones[0] if conclusiones else diagnostico_principal(hechos)
    return {
        "diagnostico_presuntivo": principal["diagnostico_presuntivo"],
        "nivel_confianza": principal["nivel_confianza"],
        "gravedad": principal["gravedad"],
        "accion_recomendada": principal["accion_recomendada"],
        "requiere_veterinario": principal["requiere_veterinario"],
        "hipotesis": conclusiones,
    }


if __name__ == "__main__":
    caso_demo = {
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
    }
    print(generar_informe_digestivo(caso_demo))
