"""Interfaz grafica para consultar al productor y obtener diagnostico.

Usa Tkinter, una libreria incluida con Python, para no agregar dependencias al
proyecto. La ventana construye un Bovino, ejecuta el motor de inferencia y
muestra la conclusion final junto con las hipotesis evaluadas.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import sys
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk

RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))

from interfaz.formulario_productor import datos_demo  # noqa: E402
from modelos.bovino import crear_bovino_desde_formulario  # noqa: E402


DatosFormulario = dict[str, Any]

OPCIONES_ESTADO_GENERAL = ("activo", "decaido", "postrado")
OPCIONES_CATEGORIA = ("ternero", "novillo", "vaca adulta", "toro")
OPCIONES_APETITO = ("normal", "bajo", "nulo")
OPCIONES_DIARREA = ("no", "si")
OPCIONES_TIPO_DIARREA = ("liquida", "pastosa", "con moco", "con sangre")
OPCIONES_DISTENSION = ("no", "si")
OPCIONES_RUMEN = ("normal", "reducida", "ausente")
OPCIONES_HIDRATACION = ("normal", "leve", "severa")
OPCIONES_TIEMPO = ("horas", "1 dia", "varios dias")
OPCIONES_CAMBIOS = ("no", "si")


class InterfazGraficaProductor(tk.Tk):
    """Ventana principal para cargar datos y visualizar conclusiones."""

    def __init__(self, umbral_confianza: float = 0.0) -> None:
        # Inicializa la ventana principal de Tkinter.
        super().__init__()
        self.title("Sistema Experto Veterinario")
        self.geometry("1020x760")
        self.minsize(900, 700)

        # Se guardan referencias a widgets y estado para usarlos desde callbacks.
        self.umbral_confianza = umbral_confianza
        self.variables: dict[str, tk.StringVar] = {}
        self.selectores: dict[str, ttk.Combobox] = {}
        self.vista_consulta: ttk.Frame | None = None
        self.vista_guia: ttk.Frame | None = None
        self.marco_resultado: ttk.LabelFrame | None = None
        self.boton_guia: ttk.Button | None = None
        self.boton_reglas_aplicadas: ttk.Button | None = None
        self.boton_copiar_diagnostico: ttk.Button | None = None
        self.observaciones_texto: tk.Text | None = None
        self.resultado_texto: scrolledtext.ScrolledText | None = None
        self.ultimo_resultado: dict[str, Any] | None = None
        self.mostrando_reglas_aplicadas = False

        # Se configura la apariencia, se crea la pantalla y se cargan valores iniciales.
        self._configurar_estilos()
        self._crear_layout()
        self.limpiar_formulario()

    def _configurar_estilos(self) -> None:
        # ttk.Style permite definir estilos reutilizables para etiquetas y botones.
        estilo = ttk.Style(self)
        estilo.configure("Titulo.TLabel", font=("Segoe UI", 15, "bold"))
        estilo.configure("Subtitulo.TLabel", font=("Segoe UI", 10))
        estilo.configure("Accion.TButton", padding=(10, 6))

    def _crear_layout(self) -> None:
        # Contenedor principal con dos columnas: formulario y resultado.
        contenedor = ttk.Frame(self, padding=14)
        contenedor.pack(fill="both", expand=True)
        contenedor.columnconfigure(0, weight=1)
        contenedor.columnconfigure(1, weight=1)
        contenedor.rowconfigure(1, weight=1)

        # Encabezado superior con titulo y acceso a la guia.
        encabezado = ttk.Frame(contenedor)
        encabezado.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        encabezado.columnconfigure(0, weight=1)

        bloque_titulo = ttk.Frame(encabezado)
        bloque_titulo.grid(row=0, column=0, sticky="w")
        ttk.Label(
            bloque_titulo,
            text="Sistema Experto Veterinario",
            style="Titulo.TLabel",
        ).pack(anchor="w")
        ttk.Label(
            bloque_titulo,
            text="Orientacion inicial para afecciones digestivas bovinas.",
            style="Subtitulo.TLabel",
        ).pack(anchor="w")

        self.boton_guia = ttk.Button(
            encabezado,
            text="Guia de utilización",
            command=self.mostrar_guia,
            style="Accion.TButton",
        )
        self.boton_guia.grid(row=0, column=1, sticky="ne")

        # Vista principal donde conviven formulario y panel de resultado.
        self.vista_consulta = ttk.Frame(contenedor)
        self.vista_consulta.grid(row=1, column=0, columnspan=2, sticky="nsew")
        self.vista_consulta.columnconfigure(0, weight=1)
        self.vista_consulta.columnconfigure(1, weight=1)
        self.vista_consulta.rowconfigure(0, weight=1)

        formulario = ttk.LabelFrame(self.vista_consulta, text="Consulta al productor", padding=12)
        formulario.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        formulario.columnconfigure(1, weight=1)

        resultado = ttk.LabelFrame(self.vista_consulta, text="Conclusion y diagnostico", padding=12)
        resultado.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        resultado.rowconfigure(1, weight=1)
        resultado.columnconfigure(0, weight=1)
        self.marco_resultado = resultado

        # Vista alternativa con la guia de uso, inicialmente creada pero luego ocultada.
        self.vista_guia = ttk.Frame(contenedor)
        self.vista_guia.grid(row=1, column=0, columnspan=2, sticky="nsew")
        self.vista_guia.rowconfigure(1, weight=1)
        self.vista_guia.columnconfigure(0, weight=1)

        # Se delega la construccion de cada zona en metodos especificos.
        self._crear_formulario(formulario)
        self._crear_resultado(resultado)
        self._crear_guia(self.vista_guia)
        self.mostrar_consulta()

    def _crear_formulario(self, padre: ttk.Frame) -> None:
        # La variable fila se incrementa por cada control agregado al formulario.
        fila = 0
        fila = self._agregar_entrada(padre, fila, "Identificador", "identificador")
        fila = self._agregar_selector(padre, fila, "Categoria", "categoria", OPCIONES_CATEGORIA)
        fila = self._agregar_selector(padre, fila, "Estado general", "estado_general", OPCIONES_ESTADO_GENERAL)
        fila = self._agregar_selector(padre, fila, "Apetito", "apetito", OPCIONES_APETITO)
        fila = self._agregar_selector(padre, fila, "Presenta diarrea", "presencia_diarrea", OPCIONES_DIARREA)
        fila = self._agregar_selector(padre, fila, "Tipo de diarrea", "tipo_diarrea", OPCIONES_TIPO_DIARREA)
        fila = self._agregar_selector(padre, fila, "Distension abdominal", "distension_abdominal", OPCIONES_DISTENSION)
        fila = self._agregar_selector(padre, fila, "Movimientos del rumen", "movimientos_rumen", OPCIONES_RUMEN)
        fila = self._agregar_selector(padre, fila, "Hidratacion", "hidratacion", OPCIONES_HIDRATACION)
        fila = self._agregar_entrada(padre, fila, "Temperatura", "temperatura")
        fila = self._agregar_selector(padre, fila, "Tiempo de evolucion", "tiempo_evolucion", OPCIONES_TIEMPO)
        fila = self._agregar_selector(padre, fila, "Cambios de alimentacion", "cambios_alimentacion", OPCIONES_CAMBIOS)
        fila = self._agregar_selector(padre, fila, "Inquietud", "inquietud", OPCIONES_CAMBIOS)
        fila = self._agregar_selector(padre, fila, "Dificultad respiratoria", "dificultad_respiratoria", OPCIONES_CAMBIOS)
        fila = self._agregar_selector(padre, fila, "Exceso de pasturas tiernas", "exceso_pasturas_tiernas", OPCIONES_CAMBIOS)
        fila = self._agregar_selector(padre, fila, "Consumo de leguminosas", "consumo_leguminosas", OPCIONES_CAMBIOS)

        ttk.Label(padre, text="Observaciones").grid(row=fila, column=0, sticky="nw", pady=5)
        self.observaciones_texto = tk.Text(padre, height=4, wrap="word")
        self.observaciones_texto.grid(row=fila, column=1, sticky="ew", pady=5)
        fila += 1

        # Botonera del formulario: ejecutar, cargar ejemplo y limpiar.
        controles = ttk.Frame(padre)
        controles.grid(row=fila, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        controles.columnconfigure((0, 1, 2), weight=1)
        ttk.Button(
            controles,
            text="Diagnosticar",
            command=self.diagnosticar,
            style="Accion.TButton",
        ).grid(row=0, column=0, sticky="ew", padx=(0, 5))
        ttk.Button(
            controles,
            text="Cargar demo",
            command=self.cargar_demo,
            style="Accion.TButton",
        ).grid(row=0, column=1, sticky="ew", padx=5)
        ttk.Button(
            controles,
            text="Limpiar",
            command=self.limpiar_formulario,
            style="Accion.TButton",
        ).grid(row=0, column=2, sticky="ew", padx=(5, 0))

        # Cuando cambia presencia_diarrea, se habilita o deshabilita tipo_diarrea.
        self.variables["presencia_diarrea"].trace_add("write", self._actualizar_tipo_diarrea)

    def _crear_resultado(self, padre: ttk.Frame) -> None:
        # Controles superiores del panel de resultado.
        controles = ttk.Frame(padre)
        controles.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        controles.columnconfigure(0, weight=1)

        # El boton se habilita despues de diagnosticar porque necesita ultimo_resultado.
        self.boton_reglas_aplicadas = ttk.Button(
            controles,
            text="Reglas aplicadas",
            command=self.alternar_resultado_reglas,
            style="Accion.TButton",
            state="disabled",
        )
        self.boton_reglas_aplicadas.grid(row=0, column=1, sticky="e")

        # Caja de texto de solo lectura donde se imprime conclusion o reglas aplicadas.
        self.resultado_texto = scrolledtext.ScrolledText(
            padre,
            wrap="word",
            height=24,
            state="disabled",
            font=("Consolas", 10),
        )
        self.resultado_texto.tag_configure("titulo", font=("Consolas", 10, "bold"))
        self.resultado_texto.grid(row=1, column=0, sticky="nsew")

        # Boton inferior para copiar al portapapeles el diagnostico principal.
        self.boton_copiar_diagnostico = ttk.Button(
            padre,
            text="Copiar diagnostico",
            command=self.copiar_diagnostico,
            style="Accion.TButton",
            state="disabled",
        )
        self.boton_copiar_diagnostico.grid(row=2, column=0, sticky="ew", pady=(10, 0))

        # Aviso fijo que queda visible bajo cualquier resultado.
        ttk.Label(
            padre,
            text="El sistema no reemplaza la evaluacion de un veterinario.",
            style="Subtitulo.TLabel",
        ).grid(row=3, column=0, sticky="w", pady=(10, 0))

    def _crear_guia(self, padre: ttk.Frame) -> None:
        # Encabezado de la vista guia con boton para volver a la consulta.
        encabezado = ttk.Frame(padre)
        encabezado.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        encabezado.columnconfigure(0, weight=1)

        ttk.Label(
            encabezado,
            text="Guia de utilización",
            style="Titulo.TLabel",
        ).grid(row=0, column=0, sticky="w")
        ttk.Button(
            encabezado,
            text="Volver a consulta",
            command=self.mostrar_consulta,
            style="Accion.TButton",
        ).grid(row=0, column=1, sticky="e")

        # Texto largo de ayuda en modo solo lectura.
        guia_texto = scrolledtext.ScrolledText(
            padre,
            wrap="word",
            state="normal",
            font=("Segoe UI", 10),
        )
        guia_texto.grid(row=1, column=0, sticky="nsew")
        guia_texto.insert("1.0", self._texto_guia())
        guia_texto.configure(state="disabled")

    def _texto_guia(self) -> str:
        # Se devuelve un bloque estatico para mantener el armado de widgets separado del contenido.
        return """Como funciona el sistema

La aplicacion carga observaciones simples del productor sobre un bovino y las transforma en hechos para el motor de inferencia. El motor aplica reglas SI-ENTONCES, genera hechos derivados como fiebre o deshidratacion y calcula diagnosticos presuntivos con un nivel de confianza. El resultado es una orientacion inicial: no reemplaza la revision ni el tratamiento indicado por un veterinario.

Guia de utilización de los datos de la consulta

Identificador
Hace referencia al nombre, numero de caravana o codigo interno del animal.
Ejemplo: BOV-001, Caravana 45, Lote 3 Animal 12.

Categoria
Indica el tipo o etapa productiva del bovino.
Ejemplo: ternero, novillo, vaca adulta, toro.

Estado general
Describe el nivel de actividad visible del animal.
Ejemplo: activo si se mueve y responde normalmente; decaido si esta apatico; postrado si permanece echado o no puede levantarse.

Apetito
Indica cuanto alimento esta consumiendo.
Ejemplo: normal si come como siempre; bajo si come menos; nulo si no come.

Presenta diarrea
Indica si se observa materia fecal anormalmente blanda o liquida.
Ejemplo: si, cuando hay heces liquidas o muy pastosas; no, cuando las heces son normales.

Tipo de diarrea
Describe el aspecto visible de la diarrea. Solo se usa si el animal presenta diarrea.
Ejemplo: liquida, pastosa, con moco o con sangre.

Distension abdominal
Indica si el abdomen se ve hinchado, especialmente como posible empaste o timpanismo.
Ejemplo: si, cuando el flanco se ve aumentado o tenso; no, cuando el abdomen se ve normal.

Movimientos del rumen
Representa la actividad ruminal estimada por observacion o palpacion simple.
Ejemplo: normal si hay actividad habitual; reducida si se percibe menor movimiento; ausente si no se detecta movimiento.

Hidratacion
Estima si el animal podria estar perdiendo liquidos.
Ejemplo: normal si no hay signos de deshidratacion; leve si hay ojos algo hundidos o menor elasticidad de piel; severa si esta muy decaido, con mucosas secas o no bebe.

Temperatura
Permite ingresar una descripcion o un valor en grados Celsius.
Ejemplo: normal, elevada, muy alta, 39.8 o 40.5.

Tiempo de evolucion
Indica desde cuando se observan los sintomas.
Ejemplo: horas si empezo recientemente; 1 dia si lleva aproximadamente un dia; varios dias si el cuadro persiste.

Cambios de alimentacion
Indica si hubo modificaciones recientes en dieta, pastura, balanceado o acceso a alimento fermentable.
Ejemplo: si, cuando se cambio de lote o se agrego alimento nuevo; no, cuando la dieta no cambio.

Inquietud
Indica si el animal se muestra nervioso, se mueve de forma anormal o no logra permanecer tranquilo.
Ejemplo: si, cuando camina, se mira el flanco o cambia de posicion repetidamente.

Dificultad respiratoria
Indica si se observa respiracion forzada o incomodidad para respirar, especialmente con distension abdominal.
Ejemplo: si, cuando respira con esfuerzo o parece agitado.

Exceso de pasturas tiernas
Indica si tuvo acceso reciente a abundante pastura joven o muy fermentable.
Ejemplo: si, cuando entro a un lote con pasto tierno luego de restriccion o cambio brusco.

Consumo de leguminosas
Indica si consumio alfalfa, trebol u otras leguminosas asociadas a empaste.
Ejemplo: si, cuando el potrero o la dieta tiene predominio de leguminosas.

Observaciones
Permite agregar informacion libre que ayude a interpretar el caso, aunque no modifica directamente las reglas.
Ejemplo: "El animal esta separado del rodeo y toma poca agua".

Uso recomendado

1. Complete los datos observados con la mayor precision posible.
2. Presione Diagnosticar.
3. Revise el diagnostico presuntivo, la confianza, la gravedad y la accion recomendada.
4. Si el sistema indica que requiere veterinario, contacte a un profesional.
"""

    def mostrar_guia(self) -> None:
        # Al mostrar la guia se oculta la consulta y tambien el boton de guia.
        if self.boton_guia is not None:
            self.boton_guia.grid_remove()
        if self.vista_consulta is not None:
            self.vista_consulta.grid_remove()
        if self.vista_guia is not None:
            self.vista_guia.grid()

    def mostrar_consulta(self) -> None:
        # Al volver a la consulta se restaura el formulario y el boton de guia.
        if self.vista_guia is not None:
            self.vista_guia.grid_remove()
        if self.vista_consulta is not None:
            self.vista_consulta.grid()
        if self.boton_guia is not None:
            self.boton_guia.grid()

    def _agregar_entrada(self, padre: ttk.Frame, fila: int, etiqueta: str, clave: str) -> int:
        # Cada entrada queda asociada a una StringVar guardada por clave.
        variable = tk.StringVar()
        self.variables[clave] = variable
        ttk.Label(padre, text=etiqueta).grid(row=fila, column=0, sticky="w", pady=5)
        ttk.Entry(padre, textvariable=variable).grid(row=fila, column=1, sticky="ew", pady=5)
        # Se devuelve la siguiente fila para encadenar la construccion del formulario.
        return fila + 1

    def _agregar_selector(
        self,
        padre: ttk.Frame,
        fila: int,
        etiqueta: str,
        clave: str,
        opciones: tuple[str, ...],
    ) -> int:
        # Los selectores usan StringVar igual que las entradas, pero con opciones cerradas.
        variable = tk.StringVar()
        self.variables[clave] = variable
        ttk.Label(padre, text=etiqueta).grid(row=fila, column=0, sticky="w", pady=5)
        selector = ttk.Combobox(
            padre,
            textvariable=variable,
            values=opciones,
            state="readonly",
        )
        selector.grid(row=fila, column=1, sticky="ew", pady=5)
        self.selectores[clave] = selector
        # Se avanza la fila para el siguiente control.
        return fila + 1

    def _actualizar_tipo_diarrea(self, *_args: object) -> None:
        # El selector de tipo solo se habilita si el productor marco diarrea.
        tipo = self.selectores["tipo_diarrea"]
        if self.variables["presencia_diarrea"].get() == "si":
            tipo.configure(state="readonly")
            # Al habilitarlo, se asigna una opcion por defecto si estaba vacio.
            if not self.variables["tipo_diarrea"].get():
                self.variables["tipo_diarrea"].set(OPCIONES_TIPO_DIARREA[0])
        else:
            # Si no hay diarrea, se limpia el tipo para no enviar un dato incoherente.
            self.variables["tipo_diarrea"].set("")
            tipo.configure(state="disabled")

    def _obtener_texto_observaciones(self) -> str:
        # Si el widget aun no existe, se devuelve texto vacio para evitar errores.
        if self.observaciones_texto is None:
            return ""
        # Tkinter agrega un salto final automaticamente; strip lo elimina.
        return self.observaciones_texto.get("1.0", "end").strip()

    def _si_no_a_booleano(self, valor: str) -> bool:
        # La GUI trabaja con "si"/"no", pero el modelo espera booleanos.
        return valor == "si"

    def obtener_datos_formulario(self) -> DatosFormulario:
        """Convierte la pantalla en un diccionario compatible con Bovino."""

        # Se leen todos los controles y se convierten al formato que entiende el modelo.
        datos: DatosFormulario = {
            "identificador": self.variables["identificador"].get().strip(),
            "categoria": self.variables["categoria"].get().strip(),
            "estado_general": self.variables["estado_general"].get(),
            "apetito": self.variables["apetito"].get(),
            "presencia_diarrea": self._si_no_a_booleano(self.variables["presencia_diarrea"].get()),
            "tipo_diarrea": self.variables["tipo_diarrea"].get(),
            "distension_abdominal": self._si_no_a_booleano(self.variables["distension_abdominal"].get()),
            "movimientos_rumen": self.variables["movimientos_rumen"].get(),
            "hidratacion": self.variables["hidratacion"].get(),
            "temperatura": self.variables["temperatura"].get().strip(),
            "tiempo_evolucion": self.variables["tiempo_evolucion"].get(),
            "cambios_alimentacion": self._si_no_a_booleano(self.variables["cambios_alimentacion"].get()),
            "inquietud": self._si_no_a_booleano(self.variables["inquietud"].get()),
            "dificultad_respiratoria": self._si_no_a_booleano(self.variables["dificultad_respiratoria"].get()),
            "exceso_pasturas_tiernas": self._si_no_a_booleano(self.variables["exceso_pasturas_tiernas"].get()),
            "consumo_leguminosas": self._si_no_a_booleano(self.variables["consumo_leguminosas"].get()),
            "observaciones": self._obtener_texto_observaciones(),
        }
        # Si no hay diarrea, tipo_diarrea no participa en las reglas.
        if not datos["presencia_diarrea"]:
            datos["tipo_diarrea"] = ""
        return datos

    def diagnosticar(self) -> None:
        """Ejecuta la inferencia y muestra el resultado final."""

        try:
            # Se captura la pantalla, se crea el Bovino y se ejecuta el motor.
            datos = self.obtener_datos_formulario()
            bovino = crear_bovino_desde_formulario(datos)
            resultado = bovino.diagnosticar(umbral_confianza=self.umbral_confianza)
            # Se guarda el ultimo resultado para poder mostrar luego las reglas aplicadas.
            self.ultimo_resultado = resultado
            self._mostrar_resultado(resultado)
        except Exception as error:
            # Cualquier error de carga o inferencia se informa sin cerrar la ventana.
            messagebox.showerror("No se pudo diagnosticar", str(error))

    def cargar_demo(self) -> None:
        """Carga un caso de ejemplo en el formulario."""

        # El demo llena la pantalla y ejecuta el diagnostico inmediatamente.
        self._cargar_datos(datos_demo())
        self.diagnosticar()

    def limpiar_formulario(self) -> None:
        """Restaura el formulario a valores iniciales."""

        # Valores seguros y neutros para iniciar una consulta nueva.
        valores_iniciales = {
            "identificador": "",
            "categoria": OPCIONES_CATEGORIA[0],
            "estado_general": "activo",
            "apetito": "normal",
            "presencia_diarrea": "no",
            "tipo_diarrea": "",
            "distension_abdominal": "no",
            "movimientos_rumen": "normal",
            "hidratacion": "normal",
            "temperatura": "normal",
            "tiempo_evolucion": "horas",
            "cambios_alimentacion": "no",
            "inquietud": "no",
            "dificultad_respiratoria": "no",
            "exceso_pasturas_tiernas": "no",
            "consumo_leguminosas": "no",
        }
        # Se actualizan las StringVar; esto tambien dispara traces como tipo_diarrea.
        for clave, valor in valores_iniciales.items():
            self.variables[clave].set(valor)

        # Se limpia el campo libre de observaciones.
        if self.observaciones_texto is not None:
            self.observaciones_texto.delete("1.0", "end")

        # No debe quedar un resultado anterior disponible para "Reglas aplicadas".
        self.ultimo_resultado = None
        self.mostrando_reglas_aplicadas = False
        self._actualizar_titulo_resultado("Conclusion y diagnostico")
        if self.boton_reglas_aplicadas is not None:
            self.boton_reglas_aplicadas.configure(text="Reglas aplicadas", state="disabled")
        if self.boton_copiar_diagnostico is not None:
            self.boton_copiar_diagnostico.configure(state="disabled")

        # Mensaje inicial del panel derecho.
        self._mostrar_texto(
            "Complete el formulario y presione Diagnosticar para obtener una conclusion."
        )

    def _cargar_datos(self, datos: DatosFormulario) -> None:
        # Cada campo del diccionario se lleva al widget correspondiente.
        self.variables["identificador"].set(str(datos.get("identificador", "")))
        self.variables["categoria"].set(str(datos.get("categoria", "")))
        self.variables["estado_general"].set(str(datos.get("estado_general", "activo")))
        self.variables["apetito"].set(str(datos.get("apetito", "normal")))
        self.variables["presencia_diarrea"].set("si" if datos.get("presencia_diarrea") else "no")
        self.variables["tipo_diarrea"].set(str(datos.get("tipo_diarrea", "")))
        self.variables["distension_abdominal"].set("si" if datos.get("distension_abdominal") else "no")
        self.variables["movimientos_rumen"].set(str(datos.get("movimientos_rumen", "normal")))
        self.variables["hidratacion"].set(str(datos.get("hidratacion", "normal")))
        self.variables["temperatura"].set(str(datos.get("temperatura", "normal")))
        self.variables["tiempo_evolucion"].set(str(datos.get("tiempo_evolucion", "horas")))
        self.variables["cambios_alimentacion"].set("si" if datos.get("cambios_alimentacion") else "no")
        self.variables["inquietud"].set("si" if datos.get("inquietud") else "no")
        self.variables["dificultad_respiratoria"].set("si" if datos.get("dificultad_respiratoria") else "no")
        self.variables["exceso_pasturas_tiernas"].set("si" if datos.get("exceso_pasturas_tiernas") else "no")
        self.variables["consumo_leguminosas"].set("si" if datos.get("consumo_leguminosas") else "no")

        # Las observaciones se cargan en el widget de texto multilnea.
        if self.observaciones_texto is not None:
            self.observaciones_texto.delete("1.0", "end")
            self.observaciones_texto.insert("1.0", str(datos.get("observaciones", "")))

    def _mostrar_resultado(self, resultado: dict[str, Any]) -> None:
        # Si la caja de texto todavia no existe, no hay nada que actualizar.
        if self.resultado_texto is None:
            return

        # Al volver al resultado normal se restaura el titulo del panel.
        self.mostrando_reglas_aplicadas = False
        self._actualizar_titulo_resultado("Conclusion y diagnostico")
        if self.boton_reglas_aplicadas is not None:
            self.boton_reglas_aplicadas.configure(text="Reglas aplicadas", state="normal")
        if self.boton_copiar_diagnostico is not None:
            self.boton_copiar_diagnostico.configure(state="normal")

        # Se habilita temporalmente el widget para reemplazar su contenido.
        self.resultado_texto.configure(state="normal")
        self.resultado_texto.delete("1.0", "end")

        # Se imprime la conclusion principal y luego las hipotesis detalladas.
        self._insertar_item_resultado(
            "Diagnostico presuntivo",
            str(resultado.get("diagnostico_presuntivo", "")),
        )
        self._insertar_hipotesis(resultado.get("hipotesis", []))
        self._insertar_item_resultado("Confianza", str(resultado.get("nivel_confianza", "")))
        self._insertar_item_resultado("Gravedad", str(resultado.get("gravedad", "")))
        self._insertar_item_resultado(
            "Requiere veterinario",
            "si" if resultado.get("requiere_veterinario") else "no",
        )
        self._insertar_item_resultado(
            "Acciones recomendadas",
            str(resultado.get("accion_recomendada", "")),
        )
        self._insertar_item_resultado(
            "Observaciones",
            str(resultado.get("bovino", {}).get("observaciones") or "Sin observaciones."),
            agregar_salto_final=False,
        )

        # Se vuelve a bloquear la edicion manual del resultado.
        self.resultado_texto.configure(state="disabled")

    def copiar_diagnostico(self) -> None:
        """Copia todo el texto visible del panel de resultado al portapapeles."""

        # Solo se puede copiar si ya existe un resultado generado por el motor y el widget.
        if self.ultimo_resultado is None or self.resultado_texto is None:
            messagebox.showinfo("Sin diagnostico", "Primero ejecute un diagnostico.")
            return

        # Se toma exactamente el texto que esta mostrando el panel derecho.
        texto_resultado = self.resultado_texto.get("1.0", "end").strip()
        if not texto_resultado:
            messagebox.showinfo("Sin diagnostico", "No hay texto para copiar.")
            return

        self.clipboard_clear()
        self.clipboard_append(texto_resultado)
        self.update()
        messagebox.showinfo("Texto copiado", "La conclusion y diagnostico fueron copiados al portapapeles.")

    def alternar_resultado_reglas(self) -> None:
        """Alterna entre conclusion diagnostica y reglas aplicadas."""

        # Si ya se estan viendo las reglas, el boton vuelve al diagnostico guardado.
        if self.mostrando_reglas_aplicadas:
            if self.ultimo_resultado is not None:
                self._mostrar_resultado(self.ultimo_resultado)
            return

        # Si se esta viendo el diagnostico, el boton muestra la explicacion por reglas.
        self.mostrar_reglas_aplicadas()

    def mostrar_reglas_aplicadas(self) -> None:
        """Muestra las reglas que se activaron para explicar la conclusion."""

        # Sin caja de texto no se puede presentar la explicacion.
        if self.resultado_texto is None:
            return

        # Cambia el titulo del panel para indicar que se esta viendo otra vista.
        self.mostrando_reglas_aplicadas = True
        self._actualizar_titulo_resultado("Reglas aplicadas")
        if self.boton_reglas_aplicadas is not None:
            self.boton_reglas_aplicadas.configure(text="Conclusión y diagnostico")
        self.resultado_texto.configure(state="normal")
        self.resultado_texto.delete("1.0", "end")

        # Si el usuario llega aqui sin diagnostico, se muestra una indicacion breve.
        if self.ultimo_resultado is None:
            self.resultado_texto.insert(
                "1.0",
                "Primero ejecute un diagnostico para ver las reglas aplicadas.",
            )
            self.resultado_texto.configure(state="disabled")
            return

        # La conclusion se repite arriba para conectar reglas con diagnostico final.
        self._insertar_item_resultado(
            "Conclusion",
            str(self.ultimo_resultado.get("diagnostico_presuntivo", "")),
        )

        # Las hipotesis son las reglas que efectivamente superaron el criterio de evidencia.
        hipotesis = self.ultimo_resultado.get("hipotesis", [])
        if not hipotesis:
            # En un caso sin diagnostico no hay regla aplicada; se explica la razon.
            self.resultado_texto.insert("end", "No se aplico ninguna regla diagnostica.\n\n", "titulo")
            self.resultado_texto.insert(
                "end",
                "El motor no encontro evidencia suficiente para activar una regla digestiva. "
                "Por eso la conclusion queda como observacion sin diagnostico concluyente.",
            )
            self.resultado_texto.configure(state="disabled")
            return

        # La primera hipotesis es la regla principal porque viene ordenada por confianza.
        self.resultado_texto.insert("end", "Regla principal aplicada:\n", "titulo")
        self._insertar_regla_aplicada(hipotesis[0])

        # Si hubo otras reglas activadas, se muestran como soporte secundario.
        reglas_secundarias = hipotesis[1:]
        if reglas_secundarias:
            self.resultado_texto.insert("end", "Otras reglas aplicadas:\n", "titulo")
            for regla in reglas_secundarias:
                self._insertar_regla_aplicada(regla)

        self.resultado_texto.configure(state="disabled")

    def _insertar_regla_aplicada(self, regla: dict[str, Any]) -> None:
        # Evita errores si se llama antes de construir el widget de resultado.
        if self.resultado_texto is None:
            return

        # Se extraen los campos que el motor agrega para cada hipotesis aplicada.
        codigo = regla.get("codigo_regla", "Sin codigo")
        nombre = regla.get("regla", "Regla no especificada")
        diagnostico = regla.get("diagnostico_presuntivo", "Diagnostico no especificado")
        confianza = regla.get("nivel_confianza", "")
        evidencia = regla.get("evidencia", [])

        # Se imprime la regla en formato legible con su evidencia cumplida.
        self.resultado_texto.insert("end", f"- {codigo}: {nombre}\n")
        self.resultado_texto.insert("end", f"  Diagnostico: {diagnostico}\n")
        self.resultado_texto.insert("end", f"  Confianza: {confianza}\n")
        self.resultado_texto.insert("end", "  Evidencia cumplida:\n")
        if evidencia:
            # Cada elemento describe una condicion de la regla que resulto verdadera.
            for condicion in evidencia:
                self.resultado_texto.insert("end", f"    - {condicion}\n")
        else:
            self.resultado_texto.insert("end", "    - Sin evidencia detallada\n")
        self.resultado_texto.insert("end", "\n")

    def _actualizar_titulo_resultado(self, titulo: str) -> None:
        # El LabelFrame permite cambiar el texto visible del apartado derecho.
        if self.marco_resultado is not None:
            self.marco_resultado.configure(text=titulo)

    def _insertar_item_resultado(
        self,
        titulo: str,
        valor: str,
        agregar_salto_final: bool = True,
    ) -> None:
        # Funcion auxiliar para escribir pares "titulo: valor" de forma consistente.
        if self.resultado_texto is None:
            return

        self.resultado_texto.insert("end", f"{titulo}: ", "titulo")
        self.resultado_texto.insert("end", valor.strip() or "Sin datos.")
        # Algunos campos necesitan separacion visual; el ultimo puede omitirla.
        if agregar_salto_final:
            self.resultado_texto.insert("end", "\n\n")

    def _insertar_hipotesis(self, hipotesis: list[dict[str, Any]]) -> None:
        # Muestra todas las hipotesis que el motor considero suficientemente confiables.
        if self.resultado_texto is None:
            return

        self.resultado_texto.insert("end", "Hipotesis evaluadas:\n", "titulo")
        if not hipotesis:
            # Caso sin reglas activadas.
            self.resultado_texto.insert("end", "Sin hipotesis evaluadas.\n\n")
            return

        for item in hipotesis:
            # Cada hipotesis incluye diagnostico, confianza y evidencia usada.
            diagnostico = item.get("diagnostico_presuntivo", "Diagnostico no especificado")
            confianza = item.get("nivel_confianza", "")
            evidencia = ", ".join(item.get("evidencia", [])) or "sin evidencia detallada"
            self.resultado_texto.insert("end", f"- {diagnostico} ({confianza}): {evidencia}\n")
        self.resultado_texto.insert("end", "\n")

    def _mostrar_texto(self, texto: str) -> None:
        # Reemplaza todo el panel de resultado por un mensaje simple.
        if self.resultado_texto is None:
            return
        self.resultado_texto.configure(state="normal")
        self.resultado_texto.delete("1.0", "end")
        self.resultado_texto.insert("1.0", texto)
        self.resultado_texto.configure(state="disabled")


def iniciar_gui(umbral_confianza: float = 0.0) -> None:
    """Abre la interfaz grafica."""

    # Se instancia la ventana y se entrega el control al loop de eventos de Tkinter.
    app = InterfazGraficaProductor(umbral_confianza=umbral_confianza)
    app.mainloop()


if __name__ == "__main__":
    iniciar_gui()
