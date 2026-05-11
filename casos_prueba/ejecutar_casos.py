"""Ejecuta los casos de prueba JSON y verifica el diagnostico esperado."""

from __future__ import annotations

from pathlib import Path
import json
import sys

RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))

from interfaz.formulario_productor import cargar_datos_desde_json  # noqa: E402
from modelos.bovino import crear_bovino_desde_formulario  # noqa: E402


CASOS_ESPERADOS = {
    "caso_1.json": "Diarrea infecciosa / enteritis",
    "caso_2.json": "Coccidiosis / lesion intestinal con diarrea sanguinolenta",
    "caso_3.json": "Timpanismo / empaste ruminal",
    "caso_4.json": "Indigestion digestiva / posible acidosis ruminal",
    "caso_5.json": "Deshidratacion asociada a cuadro digestivo",
    "caso_6.json": "Sin diagnostico digestivo concluyente",
    "caso_ambiguo.json": "Diarrea infecciosa / enteritis",
    "caso_hipotermia.json": "Hipotermia / posible shock digestivo o septicemia",
    "caso_asado.json": "Se te quema el asado",
    "caso_frezzer.json": "Saca la carne del frezzer",
}


def ejecutar_caso(ruta: Path) -> dict[str, object]:
    # Cada caso se carga igual que lo haria el programa principal con --json.
    datos = cargar_datos_desde_json(str(ruta))
    # Se construye el modelo para reutilizar la misma logica de diagnostico del sistema.
    bovino = crear_bovino_desde_formulario(datos)
    return bovino.diagnosticar()


def main() -> int:
    # La carpeta del script es tambien la carpeta donde viven los JSON de prueba.
    base = Path(__file__).resolve().parent
    resultados: list[dict[str, object]] = []
    hubo_error = False

    # Se ejecuta cada archivo y se compara su diagnostico principal con el esperado.
    for nombre_archivo, diagnostico_esperado in CASOS_ESPERADOS.items():
        ruta = base / nombre_archivo
        resultado = ejecutar_caso(ruta)
        diagnostico_obtenido = resultado["diagnostico_presuntivo"]
        advertencias = resultado.get("advertencias", [])
        # El caso pasa solo si coincide el diagnostico y no aparecieron advertencias.
        ok = diagnostico_obtenido == diagnostico_esperado and not advertencias
        hubo_error = hubo_error or not ok

        # Se guarda una salida resumida para que sea facil ver que fallo.
        resultados.append(
            {
                "caso": nombre_archivo,
                "ok": ok,
                "diagnostico_esperado": diagnostico_esperado,
                "diagnostico_obtenido": diagnostico_obtenido,
                "advertencias": advertencias,
            }
        )

    # El JSON final permite revisar todos los casos de una sola vez.
    print(json.dumps(resultados, indent=2, ensure_ascii=False))
    return 1 if hubo_error else 0


if __name__ == "__main__":
    raise SystemExit(main())
