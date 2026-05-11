"""Modelo de datos para un bovino observado por el productor.

El modelo concentra los datos de entrada definidos en el README y ofrece
metodos para transformarlos en hechos consumibles por el motor de inferencia.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import sys

RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))

try:
    from motor.motor_inferencia import inferir, normalizar_hechos, validar_hechos
except ImportError:
    from ..motor.motor_inferencia import inferir, normalizar_hechos, validar_hechos  # type: ignore


Hechos = dict[str, Any]


@dataclass
class Bovino:
    """Representa un animal y sus signos digestivos observados."""

    estado_general: str = ""
    apetito: str = ""
    presencia_diarrea: bool | str = False
    tipo_diarrea: str = ""
    distension_abdominal: bool | str = False
    movimientos_rumen: str = ""
    hidratacion: str = ""
    temperatura: float | str | None = None
    tiempo_evolucion: str = ""
    cambios_alimentacion: bool | str = False

    identificador: str = ""
    categoria: str = ""
    observaciones: str = ""
    datos_extra: Hechos = field(default_factory=dict)

    def como_hechos(self, incluir_extra: bool = True) -> Hechos:
        """Devuelve los signos del bovino como hechos para el motor."""

        # Se arma un diccionario solo con las variables que participan en las reglas.
        hechos: Hechos = {
            "estado_general": self.estado_general,
            "apetito": self.apetito,
            "presencia_diarrea": self.presencia_diarrea,
            "tipo_diarrea": self.tipo_diarrea,
            "distension_abdominal": self.distension_abdominal,
            "movimientos_rumen": self.movimientos_rumen,
            "hidratacion": self.hidratacion,
            "temperatura": self.temperatura,
            "tiempo_evolucion": self.tiempo_evolucion,
            "cambios_alimentacion": self.cambios_alimentacion,
        }

        # Los datos extra permiten extender el modelo sin romper las reglas actuales.
        if incluir_extra:
            hechos.update(self.datos_extra)

        return hechos

    def como_hechos_normalizados(self) -> Hechos:
        """Devuelve los hechos normalizados segun las reglas del motor."""

        # El motor devuelve tambien advertencias; aqui solo interesa el diccionario normalizado.
        hechos_normalizados, _ = normalizar_hechos(self.como_hechos())
        return hechos_normalizados

    def validar(self) -> list[str]:
        """Valida los datos disponibles y devuelve advertencias."""

        # Primero se normalizan valores como "si"/"no" o temperaturas escritas como texto.
        hechos_normalizados, advertencias = normalizar_hechos(self.como_hechos())
        # Luego se agregan advertencias por datos faltantes o valores fuera del dominio esperado.
        advertencias.extend(validar_hechos(hechos_normalizados))
        return advertencias

    def diagnosticar(self, umbral_confianza: float = 0.0) -> dict[str, Any]:
        """Ejecuta el motor de inferencia para este bovino."""

        # Se envia al motor solo la informacion clinica usada por las reglas.
        resultado = inferir(self.como_hechos(), umbral_confianza=umbral_confianza)
        # La identificacion se agrega al final para mostrarla, pero no influye en el diagnostico.
        resultado["bovino"] = self.resumen_identificacion()
        return resultado

    def resumen_identificacion(self) -> dict[str, str]:
        """Devuelve datos descriptivos que no participan en la inferencia."""

        # Estos datos ayudan a reconocer el animal en la salida sin modificar la inferencia.
        return {
            "identificador": self.identificador,
            "categoria": self.categoria,
            "observaciones": self.observaciones,
        }

    @classmethod
    def desde_diccionario(cls, datos: Hechos) -> Bovino:
        """Construye un Bovino desde un diccionario de datos."""

        # Se separan los campos propios del dataclass de cualquier dato adicional recibido.
        campos_modelo = cls.__dataclass_fields__.keys()
        valores = {clave: valor for clave, valor in datos.items() if clave in campos_modelo}
        extras = {clave: valor for clave, valor in datos.items() if clave not in campos_modelo}

        # Los campos reconocidos inicializan el Bovino; los extras quedan guardados aparte.
        bovino = cls(**valores)
        if extras:
            bovino.datos_extra.update(extras)
        return bovino


def crear_bovino_desde_formulario(datos_formulario: Hechos) -> Bovino:
    """Funcion de conveniencia para la futura interfaz del productor."""

    # Centraliza la conversion para que consola, GUI y tests usen el mismo camino.
    return Bovino.desde_diccionario(datos_formulario)


if __name__ == "__main__":
    bovino_demo = Bovino(
        identificador="BOV-001",
        categoria="vaca adulta",
        estado_general="decaido",
        apetito="bajo",
        presencia_diarrea=True,
        tipo_diarrea="liquida",
        distension_abdominal=False,
        movimientos_rumen="reducida",
        hidratacion="leve",
        temperatura=40.0,
        tiempo_evolucion="1 dia",
        cambios_alimentacion=False,
        observaciones="Caso de demostracion.",
    )
    print(bovino_demo.diagnosticar())
