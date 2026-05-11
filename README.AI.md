# Sistema Experto Veterinario

Proyecto académico para la materia Sistemas Inteligentes.

Objetivo:
 El objetivo principal del sistema es asistir a productores ganaderos en la identificación temprana de posibles afecciones digestivas, brindando orientación inicial y recomendaciones básicas de acción.

Usuarios:
Productores ganaderos sin conocimientos técnicos avanzados.

Tipo de Sistema Experto:
Sistema Experto Híbrido

El sistema se define como híbrido porque combina distintos enfoques de representación del conocimiento.

1. Basado en reglas

Existen relaciones clínicas claras que pueden modelarse mediante reglas SI–ENTONCES.

Ejemplo:

temperatura elevada → fiebre.
2. Probabilístico

El diagnóstico veterinario presenta incertidumbre:

un mismo conjunto de síntomas puede corresponder a distintas enfermedades.

Por ello el sistema trabaja con:

diagnósticos presuntivos,
niveles de confianza,
múltiples hipótesis posibles.
3. Difuso

Muchas variables son subjetivas o lingüísticas:

"animal decaído",
"hidratación severa",
"temperatura alta".

Estas variables no poseen límites estrictos y deben interpretarse mediante lógica difusa.

Características:
- Encadenamiento hacia adelante
- Reglas SI-ENTONCES
- Variables lingüísticas y probabilísticas
- Orientado a diagnóstico preliminar



## Variables de entrada

Estas variables representan los datos que ingresa el productor a partir de la observación del animal.

| Variable | Descripción | Tipo de dato |
|---|---|---|
| estado_general | Nivel de actividad del animal: activo, decaído o postrado. | Lingüística (string/difusa) |
| apetito | Consumo de alimento: normal, bajo o nulo. | Lingüística (string) |
| presencia_diarrea | Indica si el animal presenta diarrea. | Booleana (true/false) |
| tipo_diarrea | Características visibles de la diarrea: líquida, pastosa, con moco o con sangre. | Categórica (string) |
| distension_abdominal | Presencia de hinchazón abdominal, posible empaste. | Booleana (true/false) |
| movimientos_rumen | Actividad ruminal estimada: normal, reducida o ausente. | Lingüística (string) |
| hidratacion | Nivel de hidratación estimado: normal, leve o severa. | Lingüística (string) |
| temperatura | Estado térmico: normal, elevada, muy alta, o valor en °C si se dispone. | Lingüística o continua (float) |
| tiempo_evolucion | Tiempo desde el inicio de síntomas: horas, 1 día o varios días. | Categórica / discreta |
| cambios_alimentacion | Indica si hubo cambios recientes en la dieta. | Booleana (true/false) |

## Variables de salida

Estas variables representan las conclusiones generadas por el sistema experto.

| Variable | Descripción | Tipo de dato |
|---|---|---|
| diagnostico_presuntivo | Enfermedad digestiva probable. | Categórica (string) |
| nivel_confianza | Grado de certeza del diagnóstico. | Continua (float, 0–1 o %) |
| gravedad | Nivel del cuadro: leve, moderado o grave. | Lingüística |
| accion_recomendada | Acción sugerida: rehidratación, dieta, observación o consulta veterinaria. | Categórica |
| requiere_veterinario | Indica si se debe contactar a un profesional. | Booleana |


El sistema NO reemplaza al veterinario.
Solo brinda orientación inicial.

## Arquitectura esperada
/TP2
│
├── README.md
├── reglas/
│   ├── reglas_digestivas.py
│   └── reglas_gravedad.py
│
├── motor/
│   └── motor_inferencia.py
│
├── modelos/
│   └── bovino.py
│
├── interfaz/
│   └── formulario_productor.py
│
├── casos_prueba/
│   └── caso_1.json
│
└── main.py