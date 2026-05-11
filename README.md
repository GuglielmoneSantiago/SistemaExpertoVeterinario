# Sistema Experto Veterinario

Proyecto academico para la materia Sistemas Inteligentes. El sistema asiste a productores ganaderos en la identificacion temprana de posibles afecciones digestivas bovinas, brindando una orientacion inicial, diagnosticos presuntivos y recomendaciones basicas de accion.

El sistema no reemplaza la evaluacion de un veterinario.

## Tipo de sistema

Es un sistema experto hibrido porque combina tres enfoques:

- Basado en reglas: aplica reglas SI-ENTONCES para relacionar sintomas con posibles diagnosticos.
- Probabilistico: maneja incertidumbre mediante niveles de confianza y multiples hipotesis.
- Difuso: interpreta variables linguisticas como `decaido`, `hidratacion severa` o `temperatura alta`.

El razonamiento se realiza mediante encadenamiento hacia adelante: el sistema parte de los datos ingresados por el productor, deriva hechos clinicos simples y luego evalua reglas digestivas.

## Como ejecutar

Desde la carpeta del proyecto:

```powershell
cd "C:\Facu\Sistemas inteligentes\TP2"
```

Abrir la interfaz grafica:

```powershell
python main.py --gui
```

Ejecutar el caso demo por consola:

```powershell
python main.py --demo
```

Ejecutar un caso JSON:

```powershell
python main.py --json casos_prueba\caso_1.json --salida-json
```

Validar todos los casos de prueba:

```powershell
python casos_prueba\ejecutar_casos.py
```

## Entradas principales

El productor ingresa observaciones simples del animal:

| Variable | Descripcion |
|---|---|
| `estado_general` | activo, decaido o postrado |
| `apetito` | normal, bajo o nulo |
| `presencia_diarrea` | indica si hay diarrea |
| `tipo_diarrea` | liquida, pastosa, con moco o con sangre |
| `distension_abdominal` | indica posible hinchazon o empaste |
| `movimientos_rumen` | normal, reducida o ausente |
| `hidratacion` | normal, leve o severa |
| `temperatura` | normal, baja, hipotermia, elevada, muy alta o valor numerico |
| `tiempo_evolucion` | horas, 1 dia o varios dias |
| `cambios_alimentacion` | indica si hubo cambios recientes de dieta |

## Salidas principales

El sistema devuelve:

- Diagnostico presuntivo.
- Nivel de confianza.
- Gravedad.
- Accion recomendada.
- Indicacion de si requiere veterinario.
- Hipotesis evaluadas y reglas aplicadas.

## Estructura del proyecto

```text
TP2/
  main.py
  README.md
  GUI/
    interfaz_grafica.py
  interfaz/
    formulario_productor.py
  modelos/
    bovino.py
  motor/
    motor_inferencia.py
  reglas/
    reglas_digestivas.py
    reglasdigestivas.py
  casos_prueba/
    caso_1.json
    caso_2.json
    caso_3.json
    caso_4.json
    caso_5.json
    caso_6.json
    caso_ambiguo.json
    caso_hipotermia.json
    ejecutar_casos.py
```

## Casos de prueba

Los casos JSON permiten probar distintas combinaciones de entradas:

| Caso | Combinacion principal | Diagnostico esperado |
|---|---|---|
| `caso_1.json` | Diarrea liquida, fiebre, decaimiento e hidratacion leve | Diarrea infecciosa / enteritis |
| `caso_2.json` | Diarrea con sangre, postracion, apetito nulo y deshidratacion severa | Coccidiosis / lesion intestinal con diarrea sanguinolenta |
| `caso_3.json` | Distension abdominal, rumen ausente, sin diarrea y cambio de alimentacion | Timpanismo / empaste ruminal |
| `caso_4.json` | Cambio de alimentacion, apetito bajo, rumen reducido y diarrea pastosa | Indigestion digestiva / posible acidosis ruminal |
| `caso_5.json` | Diarrea liquida prolongada, postracion y deshidratacion severa | Deshidratacion asociada a cuadro digestivo |
| `caso_6.json` | Signos normales, sin diarrea ni distension | Sin diagnostico digestivo concluyente |
| `caso_ambiguo.json` | Diarrea liquida con fiebre leve, distension abdominal, rumen reducido y cambio de alimentacion | Diarrea infecciosa / enteritis |
| `caso_hipotermia.json` | Temperatura menor a 37 C, postracion, apetito nulo, rumen ausente y deshidratacion severa | Hipotermia / posible shock digestivo o septicemia |

## Regla de hipotermia

El sistema incorpora la condicion `hipotermia` cuando la temperatura ingresada es menor a 37 C. Tambien puede interpretarla si el usuario escribe `baja` o `hipotermia` como valor de temperatura.

Cuando se detecta hipotermia junto con signos de compromiso general, como postracion, apetito nulo, rumen reducido o ausente, deshidratacion y evolucion prolongada, se genera la hipotesis:

`Hipotermia / posible shock digestivo o septicemia`

Esta hipotesis se considera grave y requiere contactar a un veterinario de urgencia, porque una temperatura menor a 37 C puede indicar shock, septicemia o compromiso sistemico severo.

## Caso ambiguo

`caso_ambiguo.json` es un caso limite porque mezcla sintomas que pueden apuntar a diagnosticos diferentes.

Por un lado, la diarrea liquida, la temperatura elevada, el estado general decaido, el apetito bajo y la hidratacion leve forman un patron compatible con diarrea infecciosa o enteritis. Por eso el sistema toma ese diagnostico como conclusion principal.

Al mismo tiempo, la distension abdominal, los movimientos ruminales reducidos y el cambio reciente de alimentacion tambien pueden sugerir timpanismo o empaste ruminal. Ademas, el cambio de dieta, el apetito bajo, el rumen reducido y la diarrea liquida pueden asociarse con indigestion digestiva o posible acidosis ruminal.

La ambiguedad aparece porque hay evidencia cruzada: algunos datos favorecen un cuadro infeccioso, otros un problema ruminal y otros una indigestion por alimentacion. En una situacion real, el sistema podria equivocarse si prioriza una regla sin contar con mas informacion clinica. Por eso este caso sirve para verificar que el motor muestre varias hipotesis y permita revisar las reglas aplicadas.
