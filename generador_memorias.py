import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import psycopg2
from psycopg2 import sql
import hashlib
import os
import pandas as pd
from datetime import datetime  # Para manejar fechas

class ProjectSelectionWindow(tk.Toplevel):
    def __init__(self, master, db_params, user_role):
        super().__init__(master)
        self.master = master
        self.title("Selección de Proyecto")
        self.geometry("500x450")  # Tamaño ajustado
        self.resizable(False, False)

        self.master.withdraw()

        self.db_params = db_params
        self.db_conn = None
        self.db_cursor = None
        self.user_role = user_role

        # --- ESTE ES EL CAMBIO IMPORTANTE: _setup_ui() debe ir primero ---
        self._setup_ui()  # Primero, creamos los widgets de la interfaz.

        if self._connect_db():
            self.load_projects()  # Luego, cargamos los proyectos y los mostramos en el widget project_listbox que ya existe.

        self.protocol("WM_DELETE_WINDOW", self._on_closing)

# --- CLASE PARA LA APLICACIÓN PRINCIPAL (EL TERCER FORMULARIO) ---
class MainApplication(tk.Toplevel):
    def __init__(self, master, db_params, current_project_id, current_project_name, user_role):
        super().__init__(master)
        self.master = master
        self.title(f"Sistema de Gestión de Predios - Proyecto: {current_project_name}")
        self.geometry("1000x700")
        self.db_params = db_params
        self.db_conn = None
        self.db_cursor = None
        self.current_project_id = current_project_id
        self.current_project_name = current_project_name
        self.user_role = user_role

        self.master.withdraw()

        # Configuración de los datos del predio (variables Tkinter para los 13 numerales)
        self.codigo_predio = tk.StringVar(value="")

        # Numeral 1: Condición Legal
        self.n1_condicion_juridica = tk.StringVar(value="")
        self.n1_documento_acredita_titularidad = tk.StringVar(value="")
        self.n1_numero_documento = tk.StringVar(value="")
        self.n1_fecha_documento = tk.StringVar(value="")  # Se manejará como string para la entrada
        self.n1_entidad = tk.StringVar(value="")
        self.n1_titulares = []  # Lista para almacenar los titulares cargados/añadidos

        # Numeral 2: Datos del Solicitante
        self.n2_entidad = tk.StringVar(value="")

        # Numeral 3: Datos Generales del Predio
        self.n3_progresiva_inicio = tk.StringVar(value="")
        self.n3_progresiva_final = tk.StringVar(value="")
        self.n3_lado = tk.StringVar(value="")
        self.n3_tipo = tk.StringVar(value="")
        self.n3_zonificacion = tk.StringVar(value="")
        self.n3_uso_actual = tk.StringVar(value="")
        self.n3_clasificacion_tierras_cum = tk.StringVar(value="")
        self.n3_unidad_catastral = tk.StringVar(value="")
        self.n3_sector = tk.StringVar(value="")
        self.n3_distrito = tk.StringVar(value="")
        self.n3_provincia = tk.StringVar(value="")
        self.n3_departamento = tk.StringVar(value="")
        self.n3_referencia = tk.StringVar(value="")
        self.n3_via = tk.StringVar(value="")
        self.n3_manzana = tk.StringVar(value="")
        self.n3_lote = tk.StringVar(value="")

        # El resto de variables del 4 al 12 siguen siendo StringVar simples por ahora
        self.ubicacion_str = tk.StringVar(value="")  # Este era el antiguo numeral 2
        self.antecedentes_str = tk.StringVar(value="")  # Este era el antiguo numeral 3
        self.colindancias_str = tk.StringVar(value="")  # Este era el antiguo numeral 4
        self.numeral5_str = tk.StringVar(value="")
        self.numeral6_str = tk.StringVar(value="")
        self.numeral7_str = tk.StringVar(value="")
        self.numeral8_str = tk.StringVar(value="")
        self.numeral9_str = tk.StringVar(value="")
        self.numeral10_str = tk.StringVar(value="")
        self.numeral11_str = tk.StringVar(value="")
        self.numeral12_str = tk.StringVar(value="")

        self.memoria_cuerpo_text = tk.StringVar(value="")

        # --- ORDEN DE INICIALIZACIÓN CRÍTICO ---
        self._setup_ui()
        self._setup_menubar()

        self._connect_db()
        if self.db_conn:
            self._create_tables()  # Se encarga de verificar/crear todas las tablas

        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _setup_menubar(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        project_menu = tk.Menu(menubar, tearoff=0)
        project_menu.add_command(label="Cambiar de Proyecto", command=self._change_project)
        project_menu.add_command(label="Cerrar Sesión", command=self._logout)
        menubar.add_cascade(label="Proyecto", menu=project_menu)

        memorias_menu = tk.Menu(menubar, tearoff=0)
        memorias_menu.add_command(label="1. Condición Legal", command=self._open_numeral1_window)
        # --- CAMBIO AQUÍ: Nueva entrada para Numerales 2 y 3 ---
        memorias_menu.add_command(label="2 y 3. Datos Solicitante / Generales Predio",
                                  command=self._open_numeral2and3_window)
        memorias_menu.add_command(label="4. Colindancias",
                                  command=lambda: self.open_section_window("4. Colindancias", self.colindancias_str))
        memorias_menu.add_command(label="5. Numeral 5",
                                  command=lambda: self.open_section_window("5. Numeral 5", self.numeral5_str))
        memorias_menu.add_command(label="6. Numeral 6",
                                  command=lambda: self.open_section_window("6. Numeral 6", self.numeral6_str))
        memorias_menu.add_command(label="7. Numeral 7",
                                  command=lambda: self.open_section_window("7. Numeral 7", self.numeral7_str))
        memorias_menu.add_command(label="8. Numeral 8",
                                  command=lambda: self.open_section_window("8. Numeral 8", self.numeral8_str))
        memorias_menu.add_command(label="9. Numeral 9",
                                  command=lambda: self.open_section_window("9. Numeral 9", self.numeral9_str))
        memorias_menu.add_command(label="10. Numeral 10",
                                  command=lambda: self.open_section_window("10. Numeral 10", self.numeral10_str))
        memorias_menu.add_command(label="11. Numeral 11",
                                  command=lambda: self.open_section_window("11. Numeral 11", self.numeral11_str))
        memorias_menu.add_command(label="12. Numeral 12",
                                  command=lambda: self.open_section_window("12. Numeral 12", self.numeral12_str))
        memorias_menu.add_command(label="13. Panel Fotográfico",
                                  command=lambda: self.open_section_window("13. Panel Fotográfico", tk.StringVar()))
        menubar.add_cascade(label="Gestionar Memorias", menu=memorias_menu)

        acciones_menu = tk.Menu(menubar, tearoff=0)
        acciones_menu.add_command(label="Generar Memoria Descriptiva", command=self.generate_memory_description)
        acciones_menu.add_command(label="Consultar Predios", command=self.query_predios)
        acciones_menu.add_command(label="Generar Reportes", command=self.generate_reports)
        menubar.add_cascade(label="Acciones", menu=acciones_menu)

        if self.user_role == 'administrador':
            admin_menu = tk.Menu(menubar, tearoff=0)
            admin_menu.add_command(label="Gestionar Usuarios", command=self._manage_users)
            menubar.add_cascade(label="Administración", menu=admin_menu)

    def _setup_ui(self):
        predio_frame = ttk.LabelFrame(self, text="Código de Predio y Búsqueda")
        predio_frame.pack(padx=10, pady=10, fill="x")

        ttk.Label(predio_frame, text="Código de Predio Actual:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Label(predio_frame, textvariable=self.codigo_predio, font=("Arial", 12, "bold")).grid(row=0, column=1,
                                                                                                  padx=5, pady=5,
                                                                                                  sticky="w")

        ttk.Button(predio_frame, text="Elegir Predio Existente", command=self._select_existing_predio).grid(row=1,
                                                                                                            column=0,
                                                                                                            padx=5,
                                                                                                            pady=5,
                                                                                                            sticky="w")
        ttk.Button(predio_frame, text="Generar Nuevo Código", command=self._generate_new_codigo).grid(row=1, column=1,
                                                                                                      padx=5, pady=5,
                                                                                                      sticky="w")

        self.log_text = tk.Text(self, height=5, state='disabled', wrap='word')
        self.log_text.pack(padx=10, pady=5, fill="both", expand=True)

        self.update_log("Bienvenido al sistema de gestión de predios. Selecciona o genera un código de predio.")

    def _connect_db(self):
        try:
            self.db_conn = psycopg2.connect(
                host=self.db_params['host'],
                database=self.db_params['dbname'],
                user=self.db_params['user'],
                password=self.db_params['password'],
                sslmode='disable'
            )
            self.db_cursor = self.db_conn.cursor()
            self.update_log("Conexión a la base de datos establecida.")
            return True
        except Exception as e:
            messagebox.showerror("Error de Conexión", f"No se pudo conectar a la base de datos: {e}")
            self.update_log(f"Error de conexión a DB: {e}")
            return False

    def _create_tables(self):
        try:
            # Usuarios y Proyectos ya se crean en LoginWindow
            self.db_cursor.execute("""
                CREATE TABLE IF NOT EXISTS predios (
                    id SERIAL PRIMARY KEY,
                    codigo_predio VARCHAR(100) UNIQUE NOT NULL,
                    proyecto_id INTEGER NOT NULL,
                    FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE
                );
            """)

            self.db_cursor.execute("""
                CREATE TABLE IF NOT EXISTS memorias_data (
                    id SERIAL PRIMARY KEY,
                    predio_id INTEGER NOT NULL,
                    -- Numeral 1
                    n1_condicion_juridica VARCHAR(50),
                    n1_documento_acredita_titularidad VARCHAR(100),
                    n1_numero_documento_titularidad VARCHAR(100),
                    n1_fecha_documento_titularidad DATE,
                    n1_entidad_titularidad VARCHAR(100),
                    -- Numeral 2
                    n2_entidad VARCHAR(100),
                    -- Numeral 3
                    n3_progresiva_inicio VARCHAR(50),
                    n3_progresiva_final VARCHAR(50),
                    n3_lado VARCHAR(20),
                    n3_tipo VARCHAR(20),
                    n3_zonificacion VARCHAR(100),
                    n3_uso_actual VARCHAR(50),
                    n3_clasificacion_tierras_cum VARCHAR(100),
                    n3_unidad_catastral VARCHAR(100),
                    n3_sector VARCHAR(100),
                    n3_distrito VARCHAR(100),
                    n3_provincia VARCHAR(100),
                    n3_departamento VARCHAR(100),
                    n3_referencia VARCHAR(255),
                    n3_via VARCHAR(100),
                    n3_manzana VARCHAR(50),
                    n3_lote VARCHAR(50),
                    -- Otros numerales (por ahora TEXT simple, se actualizarán)
                    numeral_4_colindancias TEXT,
                    numeral_5_datos TEXT,
                    numeral_6_datos TEXT,
                    numeral_7_datos TEXT,
                    numeral_8_datos TEXT,
                    numeral_9_datos TEXT,
                    numeral_10_datos TEXT,
                    numeral_11_datos TEXT,
                    numeral_12_datos TEXT,
                    FOREIGN KEY (predio_id) REFERENCES predios(id) ON DELETE CASCADE
                );
            """)
            self.db_cursor.execute("""
                CREATE TABLE IF NOT EXISTS titulares_predio (
                    id SERIAL PRIMARY KEY,
                    predio_id INTEGER NOT NULL,
                    nombre_titular VARCHAR(255) NOT NULL,
                    dni_titular VARCHAR(20),
                    FOREIGN KEY (predio_id) REFERENCES predios(id) ON DELETE CASCADE
                );
            """)

            self.db_conn.commit()
            self.update_log("Tablas de predios, memorias_data y titulares_predio verificadas/creadas.")
        except Exception as e:
            messagebox.showerror("Error al Crear Tablas",
                                 f"No se pudieron crear las tablas de predios/memorias/titulares: {e}")
            self.update_log(f"Error al crear tablas (MainApp): {e}")
            if self.db_conn:
                self.db_conn.rollback()

    def update_log(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert('end', message + "\n")
        self.log_text.see('end')
        self.log_text.config(state='disabled')

    def _select_existing_predio(self):
        try:
            self.db_cursor.execute("SELECT codigo_predio FROM predios WHERE proyecto_id = %s",
                                   (self.current_project_id,))
            predios_db = [row[0] for row in self.db_cursor.fetchall()]
            if not predios_db:
                messagebox.showinfo("Información", "No hay predios existentes para este proyecto. Genera uno nuevo.")
                return

            selected_predio = simpledialog.askstring("Seleccionar Predio",
                                                     f"Predios existentes para {self.current_project_name}:\n" + "\n".join(
                                                         predios_db) + "\n\nIngresa el código del predio a trabajar:",
                                                     parent=self)
            if selected_predio and selected_predio in predios_db:
                self.codigo_predio.set(selected_predio)
                self.update_log(f"Predio '{selected_predio}' seleccionado para trabajar.")
                self.load_predio_data(selected_predio)
            elif selected_predio:
                messagebox.showerror("Error", "Código de predio no válido o no encontrado para este proyecto.")
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar predios: {e}")
            if self.db_conn:
                self.db_conn.rollback()

    def _generate_new_codigo(self):
        new_code = simpledialog.askstring("Nuevo Código de Predio", "Ingresa el nuevo código de predio:", parent=self)
        if new_code:
            try:
                self.db_cursor.execute("SELECT id FROM predios WHERE codigo_predio = %s AND proyecto_id = %s",
                                       (new_code, self.current_project_id))
                if self.db_cursor.fetchone():
                    messagebox.showerror("Error", f"El código de predio '{new_code}' ya existe en este proyecto.")
                    return

                self.db_cursor.execute("INSERT INTO predios (codigo_predio, proyecto_id) VALUES (%s, %s) RETURNING id",
                                       (new_code, self.current_project_id))
                predio_id = self.db_cursor.fetchone()[0]
                self.db_conn.commit()
                self.codigo_predio.set(new_code)
                self.update_log(f"Nuevo predio '{new_code}' generado y guardado en la DB para el proyecto actual.")

                # Insertar/actualizar la entrada inicial en memorias_data para el nuevo predio
                self.db_cursor.execute("""
                    INSERT INTO memorias_data (predio_id) VALUES (%s)
                    ON CONFLICT (predio_id) DO NOTHING;
                """, (predio_id,))
                self.db_conn.commit()
                self.update_log(f"Entrada de memoria creada/verificada para el predio '{new_code}'.")
                self.load_predio_data(new_code)  # Cargar datos (que ahora también precarga los "fijos")
            except Exception as e:
                messagebox.showerror("Error", f"Error al generar nuevo código de predio: {e}")
                if self.db_conn:
                    self.db_conn.rollback()

    def get_predio_id(self, codigo_predio):
        """Obtiene el ID del predio para el código y proyecto actual."""
        self.db_cursor.execute("SELECT id FROM predios WHERE codigo_predio = %s AND proyecto_id = %s",
                               (codigo_predio, self.current_project_id))
        result = self.db_cursor.fetchone()
        return result[0] if result else None

    def _get_last_fixed_values(self):
        """
        Intenta obtener los últimos valores para los campos "fijos"
        (sector, distrito, provincia, departamento, referencia)
        del predio más reciente o de cualquier predio en el proyecto.
        """
        fixed_values = {
            "sector": "", "distrito": "", "provincia": "",
            "departamento": "", "referencia": ""
        }
        try:
            self.db_cursor.execute("""
                SELECT
                    n3_sector, n3_distrito, n3_provincia, n3_departamento, n3_referencia
                FROM memorias_data md
                JOIN predios p ON md.predio_id = p.id
                WHERE p.proyecto_id = %s
                ORDER BY p.id DESC -- Obtener el más reciente
                LIMIT 1
            """, (self.current_project_id,))
            last_data = self.db_cursor.fetchone()
            if last_data:
                fixed_values["sector"] = last_data[0] if last_data[0] else ""
                fixed_values["distrito"] = last_data[1] if last_data[1] else ""
                fixed_values["provincia"] = last_data[2] if last_data[2] else ""
                fixed_values["departamento"] = last_data[3] if last_data[3] else ""
                fixed_values["referencia"] = last_data[4] if last_data[4] else ""
        except Exception as e:
            self.update_log(f"Error al cargar valores fijos: {e}")
        return fixed_values

    def load_predio_data(self, codigo_predio):
        # Reiniciar variables para evitar datos de predios anteriores
        # Numeral 1
        self.n1_condicion_juridica.set("")
        self.n1_documento_acredita_titularidad.set("")
        self.n1_numero_documento.set("")
        self.n1_fecha_documento.set("")
        self.n1_entidad.set("")
        self.n1_titulares = []  # Limpiar la lista de titulares

        # Numeral 2
        self.n2_entidad.set("")

        # Numeral 3
        self.n3_progresiva_inicio.set("")
        self.n3_progresiva_final.set("")
        self.n3_lado.set("")
        self.n3_tipo.set("")
        self.n3_zonificacion.set("")
        self.n3_uso_actual.set("")
        self.n3_clasificacion_tierras_cum.set("")
        self.n3_unidad_catastral.set("")
        self.n3_sector.set("")
        self.n3_distrito.set("")
        self.n3_provincia.set("")
        self.n3_departamento.set("")
        self.n3_referencia.set("")
        self.n3_via.set("")
        self.n3_manzana.set("")
        self.n3_lote.set("")

        # Otros numerales (simples)
        self.ubicacion_str.set("")
        self.antecedentes_str.set("")
        self.colindancias_str.set("")
        self.numeral5_str.set("")
        self.numeral6_str.set("")
        self.numeral7_str.set("")
        self.numeral8_str.set("")
        self.numeral9_str.set("")
        self.numeral10_str.set("")
        self.numeral11_str.set("")
        self.numeral12_str.set("")

        predio_id = self.get_predio_id(codigo_predio)
        if not predio_id:
            messagebox.showerror("Error", "Predio no encontrado para cargar datos.")
            return

        try:
            # Cargar datos de memorias_data
            self.db_cursor.execute("""
                SELECT
                    n1_condicion_juridica, n1_documento_acredita_titularidad,
                    n1_numero_documento_titularidad, n1_fecha_documento_titularidad,
                    n1_entidad_titularidad,
                    n2_entidad, -- Numeral 2
                    n3_progresiva_inicio, n3_progresiva_final, n3_lado, n3_tipo, n3_zonificacion,
                    n3_uso_actual, n3_clasificacion_tierras_cum, n3_unidad_catastral,
                    n3_sector, n3_distrito, n3_provincia, n3_departamento, n3_referencia,
                    n3_via, n3_manzana, n3_lote, -- Numeral 3
                    numeral_4_colindancias, numeral_5_datos, numeral_6_datos, numeral_7_datos,
                    numeral_8_datos, numeral_9_datos, numeral_10_datos, numeral_11_datos,
                    numeral_12_datos
                FROM memorias_data
                WHERE predio_id = %s
            """, (predio_id,))
            data = self.db_cursor.fetchone()

            # Obtener valores "fijos" del último predio para precarga si el actual está vacío
            last_fixed_values = self._get_last_fixed_values()

            if data:
                # Numeral 1
                self.n1_condicion_juridica.set(data[0] if data[0] else "")
                self.n1_documento_acredita_titularidad.set(data[1] if data[1] else "")
                self.n1_numero_documento.set(data[2] if data[2] else "")
                self.n1_fecha_documento.set(data[3].strftime("%Y-%m-%d") if data[3] else "")  # Formatear fecha
                self.n1_entidad.set(data[4] if data[4] else "")

                # Numeral 2
                self.n2_entidad.set(data[5] if data[5] else "")

                # Numeral 3
                self.n3_progresiva_inicio.set(data[6] if data[6] else "")
                self.n3_progresiva_final.set(data[7] if data[7] else "")
                self.n3_lado.set(data[8] if data[8] else "")
                self.n3_tipo.set(data[9] if data[9] else "")
                self.n3_zonificacion.set(data[10] if data[10] else "")
                self.n3_uso_actual.set(data[11] if data[11] else "")
                self.n3_clasificacion_tierras_cum.set(data[12] if data[12] else "")
                self.n3_unidad_catastral.set(data[13] if data[13] else "")

                # Campos "fijos": Si el valor del predio actual es None, precargar con el último valor fijo
                self.n3_sector.set(data[14] if data[14] else last_fixed_values["sector"])
                self.n3_distrito.set(data[15] if data[15] else last_fixed_values["distrito"])
                self.n3_provincia.set(data[16] if data[16] else last_fixed_values["provincia"])
                self.n3_departamento.set(data[17] if data[17] else last_fixed_values["departamento"])
                self.n3_referencia.set(data[18] if data[18] else last_fixed_values["referencia"])

                self.n3_via.set(data[19] if data[19] else "")
                self.n3_manzana.set(data[20] if data[20] else "")
                self.n3_lote.set(data[21] if data[21] else "")

                # Otros numerales (índices ajustados)
                self.colindancias_str.set(data[22] if data[22] else "")  # Original numeral 4
                self.numeral5_str.set(data[23] if data[23] else "")
                self.numeral6_str.set(data[24] if data[24] else "")
                self.numeral7_str.set(data[25] if data[25] else "")
                self.numeral8_str.set(data[26] if data[26] else "")
                self.numeral9_str.set(data[27] if data[27] else "")
                self.numeral10_str.set(data[28] if data[28] else "")
                self.numeral11_str.set(data[29] if data[29] else "")
                self.numeral12_str.set(data[30] if data[30] else "")

                # Cargar titulares asociados (Numeral 1)
                self.db_cursor.execute("SELECT nombre_titular, dni_titular FROM titulares_predio WHERE predio_id = %s",
                                       (predio_id,))
                self.n1_titulares[:] = self.db_cursor.fetchall()  # Usar rebanado para actualizar la lista en su lugar

                self.update_log(f"Datos de memoria y titulares cargados para el predio '{codigo_predio}'.")
            else:
                self.update_log(
                    f"No se encontraron datos de memoria para el predio '{codigo_predio}'. Precargando valores fijos.")
                # Si no hay datos, las variables ya están vacías por la reinicialización inicial
                # Pero precargar los "fijos"
                self.n3_sector.set(last_fixed_values["sector"])
                self.n3_distrito.set(last_fixed_values["distrito"])
                self.n3_provincia.set(last_fixed_values["provincia"])
                self.n3_departamento.set(last_fixed_values["departamento"])
                self.n3_referencia.set(last_fixed_values["referencia"])


        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar datos del predio: {e}")
            if self.db_conn:
                self.db_conn.rollback()

    def save_predio_data(self, codigo_predio):
        if not codigo_predio:
            messagebox.showwarning("Advertencia", "No hay un predio seleccionado para guardar.")
            return

        predio_id = self.get_predio_id(codigo_predio)
        if not predio_id:
            messagebox.showerror("Error", "Predio no encontrado en este proyecto para guardar.")
            return

        try:
            # Preparar fecha para la DB (Numeral 1)
            fecha_doc = None
            if self.n1_fecha_documento.get():
                try:
                    fecha_doc = datetime.strptime(self.n1_fecha_documento.get(), "%Y-%m-%d").date()
                except ValueError:
                    messagebox.showwarning("Formato de Fecha",
                                           "El formato de fecha debe ser YYYY-MM-DD. No se guardará la fecha del Numeral 1.")

            # --- AGREGAR ESTOS PRINTS PARA DEPURACIÓN ---
            print(f"\n--- Iniciando guardado para predio_id: {predio_id} (Código: {codigo_predio}) ---")
            print(f"N1 Condición Jurídica: {self.n1_condicion_juridica.get()}")
            print(f"N1 Documento Acredita: {self.n1_documento_acredita_titularidad.get()}")
            print(f"N1 Número Documento: {self.n1_numero_documento.get()}")
            print(f"N1 Fecha Documento: {fecha_doc}")
            print(f"N1 Entidad: {self.n1_entidad.get()}")
            print(f"N1 Titulares: {self.n1_titulares}")

            print(f"N2 Entidad: {self.n2_entidad.get()}")

            print(f"N3 Progresiva Inicio: {self.n3_progresiva_inicio.get()}")
            print(f"N3 Progresiva Final: {self.n3_progresiva_final.get()}")
            print(f"N3 Lado: {self.n3_lado.get()}")
            print(f"N3 Tipo: {self.n3_tipo.get()}")
            print(f"N3 Zonificación: {self.n3_zonificacion.get()}")
            print(f"N3 Uso Actual: {self.n3_uso_actual.get()}")
            print(f"N3 Clasificación Tierras CUM: {self.n3_clasificacion_tierras_cum.get()}")
            print(f"N3 Unidad Catastral: {self.n3_unidad_catastral.get()}")
            print(f"N3 Sector: {self.n3_sector.get()}")
            print(f"N3 Distrito: {self.n3_distrito.get()}")
            print(f"N3 Provincia: {self.n3_provincia.get()}")
            print(f"N3 Departamento: {self.n3_departamento.get()}")
            print(f"N3 Referencia: {self.n3_referencia.get()}")
            print(f"N3 Vía: {self.n3_via.get()}")
            print(f"N3 Manzana: {self.n3_manzana.get()}")
            print(f"N3 Lote: {self.n3_lote.get()}")
            print(f"Numeral 4 (Colindancias): {self.colindancias_str.get()}")
            print("--- Intentando ejecutar la consulta UPDATE ---")
            # --- FIN DE LOS PRINTS ---

            # Guardar/Actualizar datos de memorias_data
            self.db_cursor.execute("""
                UPDATE memorias_data SET
                    n1_condicion_juridica = %s,
                    n1_documento_acredita_titularidad = %s,
                    n1_numero_documento_titularidad = %s,
                    n1_fecha_documento_titularidad = %s,
                    n1_entidad_titularidad = %s,
                    n2_entidad = %s, -- Numeral 2
                    n3_progresiva_inicio = %s, n3_progresiva_final = %s,
                    n3_lado = %s, n3_tipo = %s, n3_zonificacion = %s,
                    n3_uso_actual = %s, n3_clasificacion_tierras_cum = %s,
                    n3_unidad_catastral = %s, n3_sector = %s, n3_distrito = %s,
                    n3_provincia = %s, n3_departamento = %s, n3_referencia = %s,
                    n3_via = %s, n3_manzana = %s, n3_lote = %s, -- Numeral 3
                    numeral_4_colindancias = %s, numeral_5_datos = %s,
                    numeral_6_datos = %s, numeral_7_datos = %s,
                    numeral_8_datos = %s, numeral_9_datos = %s,
                    numeral_10_datos = %s, numeral_11_datos = %s,
                    numeral_12_datos = %s
                WHERE predio_id = %s
            """, (self.n1_condicion_juridica.get(),
                  self.n1_documento_acredita_titularidad.get(),
                  self.n1_numero_documento.get(),
                  fecha_doc,  # Usar el objeto date
                  self.n1_entidad.get(),
                  self.n2_entidad.get(),  # Numeral 2
                  self.n3_progresiva_inicio.get(), self.n3_progresiva_final.get(),
                  self.n3_lado.get(), self.n3_tipo.get(), self.n3_zonificacion.get(),
                  self.n3_uso_actual.get(), self.n3_clasificacion_tierras_cum.get(),
                  self.n3_unidad_catastral.get(), self.n3_sector.get(), self.n3_distrito.get(),
                  self.n3_provincia.get(), self.n3_departamento.get(), self.n3_referencia.get(),
                  self.n3_via.get(), self.n3_manzana.get(), self.n3_lote.get(),  # Numeral 3
                  self.colindancias_str.get(), self.numeral5_str.get(),
                  self.numeral6_str.get(), self.numeral7_str.get(),
                  self.numeral8_str.get(), self.numeral9_str.get(),
                  self.numeral10_str.get(), self.numeral11_str.get(),
                  self.numeral12_str.get(), predio_id))

            # Añade un print después de la ejecución y antes del commit para ver si llegó aquí
            print("--- Consulta UPDATE ejecutada. Intentando guardar titulares... ---")

            # Eliminar titulares antiguos y guardar los nuevos (Numeral 1)
            self.db_cursor.execute("DELETE FROM titulares_predio WHERE predio_id = %s", (predio_id,))
            for nombre, dni in self.n1_titulares:
                self.db_cursor.execute(
                    "INSERT INTO titulares_predio (predio_id, nombre_titular, dni_titular) VALUES (%s, %s, %s)",
                    (predio_id, nombre, dni)
                )

            # Añade un print antes del commit final
            print("--- Titulares guardados. Realizando commit... ---")
            self.db_conn.commit()
            print("--- Commit realizado. Guardado exitoso. ---")  # Confirmación final
            self.update_log(f"Datos del predio '{codigo_predio}' (incluyendo Numerales 1, 2 y 3) guardados con éxito.")
            messagebox.showinfo("Guardado", f"Datos del predio '{codigo_predio}' guardados con éxito.")
        except Exception as e:
            # Si hay un error, este print nos lo mostrará en la terminal
            print(f"--- ¡ERROR DURANTE EL GUARDADO!: {e} ---")
            messagebox.showerror("Error", f"Error al guardar datos del predio: {e}")
            if self.db_conn:
                self.db_conn.rollback()

    def _open_numeral1_window(self):
        if not self.codigo_predio.get():
            messagebox.showwarning("Advertencia", "Por favor, selecciona o genera un código de predio primero.")
            return

        Numeral1Window(self, self.codigo_predio.get(),
                       self.n1_condicion_juridica,
                       self.n1_documento_acredita_titularidad,
                       self.n1_numero_documento,
                       self.n1_fecha_documento,
                       self.n1_entidad,
                       self.n1_titulares,  # Pasamos la lista directamente
                       self.save_predio_data)  # Pasamos la función de guardado

    def _open_numeral2and3_window(self):
        if not self.codigo_predio.get():
            messagebox.showwarning("Advertencia", "Por favor, selecciona o genera un código de predio primero.")
            return

        # Pasamos todas las variables de Tkinter de los numerales 2 y 3
        Numeral2and3Window(self, self.codigo_predio.get(),
                           self.n2_entidad,
                           self.n3_progresiva_inicio,
                           self.n3_progresiva_final,
                           self.n3_lado,
                           self.n3_tipo,
                           self.n3_zonificacion,
                           self.n3_uso_actual,
                           self.n3_clasificacion_tierras_cum,
                           self.n3_unidad_catastral,
                           self.n3_sector,
                           self.n3_distrito,
                           self.n3_provincia,
                           self.n3_departamento,
                           self.n3_referencia,
                           self.n3_via,
                           self.n3_manzana,
                           self.n3_lote,
                           self.save_predio_data)

    def open_section_window(self, title, content_var):
        if not self.codigo_predio.get():
            messagebox.showwarning("Advertencia", "Por favor, selecciona o genera un código de predio primero.")
            return

        section_window = tk.Toplevel(self)
        section_window.title(f"{title} - Predio: {self.codigo_predio.get()}")
        section_window.geometry("600x400")

        lbl = ttk.Label(section_window, text=f"Contenido para {title}:")
        lbl.pack(padx=10, pady=5)

        if "Panel Fotográfico" in title:
            ttk.Label(section_window, text="Aquí se gestionarán las imágenes.").pack(padx=10, pady=10)
            ttk.Button(section_window, text="Cargar Imagen", command=lambda: self.load_image(section_window)).pack(
                pady=5)
            ttk.Button(section_window, text="Cerrar", command=section_window.destroy).pack(pady=10)
        else:
            text_area = tk.Text(section_window, wrap="word", height=15, width=70)
            text_area.pack(padx=10, pady=5, fill="both", expand=True)
            text_area.insert("1.0", content_var.get())

            def on_section_close():
                content_var.set(text_area.get("1.0", "end-1c"))
                self.save_predio_data(self.codigo_predio.get())
                section_window.destroy()

            ttk.Button(section_window, text="Guardar y Cerrar", command=on_section_close).pack(pady=10)
            section_window.protocol("WM_DELETE_WINDOW", on_section_close)

    def load_image(self, parent_window):
        file_path = filedialog.askopenfilename(
            parent=parent_window,
            title="Seleccionar imagen",
            filetypes=[("Archivos de Imagen", "*.png;*.jpg;*.jpeg;*.gif;*.bmp"), ("Todos los archivos", "*.*")]
        )
        if file_path:
            messagebox.showinfo("Imagen Cargada",
                                f"Imagen seleccionada: {os.path.basename(file_path)}\n(Aquí iría la lógica para mostrarla y guardarla en DB/ruta)")

    def generate_memory_description(self):
        if not self.codigo_predio.get():
            messagebox.showwarning("Advertencia", "Por favor, selecciona un código de predio para generar la memoria.")
            return

        self.load_predio_data(self.codigo_predio.get())  # Asegurarse de tener los datos más recientes

        memoria_texto = "MEMORIA DESCRIPTIVA\n"
        memoria_texto += f"Nombre del proyecto: {self.current_project_name}\n"
        memoria_texto += f"Código de Predio: {self.codigo_predio.get()}\n\n"

        memoria_texto += "1. CONDICIÓN LEGAL\n"
        memoria_texto += f"   Condición Jurídica: {self.n1_condicion_juridica.get()}\n"
        if self.n1_titulares:
            memoria_texto += "   Titulares:\n"
            for i, (nombre, dni) in enumerate(self.n1_titulares):
                memoria_texto += f"     - Titular {i + 1}: {nombre} (DNI: {dni})\n"
        else:
            memoria_texto += "   No se han registrado titulares.\n"
        memoria_texto += f"   Documento de Titularidad: {self.n1_documento_acredita_titularidad.get()}\n"
        memoria_texto += f"   N° Documento: {self.n1_numero_documento.get()}\n"
        memoria_texto += f"   Fecha: {self.n1_fecha_documento.get()}\n"
        memoria_texto += f"   Entidad: {self.n1_entidad.get()}\n\n"

        memoria_texto += "2. DATOS DEL SOLICITANTE\n"
        memoria_texto += f"   Entidad: {self.n2_entidad.get()}\n\n"

        memoria_texto += "3. DATOS GENERALES DEL PREDIO\n"
        memoria_texto += f"   Progresiva Inicio: {self.n3_progresiva_inicio.get()}\n"
        memoria_texto += f"   Progresiva Final: {self.n3_progresiva_final.get()}\n"
        memoria_texto += f"   Lado: {self.n3_lado.get()}\n"
        memoria_texto += f"   Tipo: {self.n3_tipo.get()}\n"
        memoria_texto += f"   Zonificación: {self.n3_zonificacion.get()}\n"
        memoria_texto += f"   Uso Actual: {self.n3_uso_actual.get()}\n"
        memoria_texto += f"   Clasificación de Tierras CUM: {self.n3_clasificacion_tierras_cum.get()}\n"
        memoria_texto += f"   Unidad Catastral: {self.n3_unidad_catastral.get()}\n"
        memoria_texto += f"   Sector: {self.n3_sector.get()}\n"
        memoria_texto += f"   Distrito: {self.n3_distrito.get()}\n"
        memoria_texto += f"   Provincia: {self.n3_provincia.get()}\n"
        memoria_texto += f"   Departamento: {self.n3_departamento.get()}\n"
        memoria_texto += f"   Referencia: {self.n3_referencia.get()}\n"
        memoria_texto += f"   Vía: {self.n3_via.get()}\n"
        memoria_texto += f"   Manzana: {self.n3_manzana.get()}\n"
        memoria_texto += f"   Lote: {self.n3_lote.get()}\n\n"

        memoria_texto += f"4. COLINDANCIAS\n{self.colindancias_str.get()}\n\n"
        memoria_texto += f"5. NUMERAL 5\n{self.numeral5_str.get()}\n\n"
        memoria_texto += f"6. NUMERAL 6\n{self.numeral6_str.get()}\n\n"
        memoria_texto += f"7. NUMERAL 7\n{self.numeral7_str.get()}\n\n"
        memoria_texto += f"8. NUMERAL 8\n{self.numeral8_str.get()}\n\n"
        memoria_texto += f"9. NUMERAL 9\n{self.numeral9_str.get()}\n\n"
        memoria_texto += f"10. NUMERAL 10\n{self.numeral10_str.get()}\n\n"
        memoria_texto += f"11. NUMERAL 11\n{self.numeral11_str.get()}\n\n"
        memoria_texto += f"12. NUMERAL 12\n{self.numeral12_str.get()}\n\n"
        memoria_texto += f"13. PANEL FOTOGRÁFICO\n(Aquí se adjuntarían las imágenes o referencias a ellas)\n"

        memoria_window = tk.Toplevel(self)
        memoria_window.title(f"Memoria Descriptiva - {self.codigo_predio.get()}")
        memoria_window.geometry("800x600")

        memoria_text_display = tk.Text(memoria_window, wrap="word", height=20, width=80)
        memoria_text_display.pack(padx=10, pady=10, fill="both", expand=True)
        memoria_text_display.insert("1.0", memoria_texto)
        memoria_text_display.config(state='disabled')

        ttk.Button(memoria_window, text="Exportar a PDF/Word (Simulado)",
                   command=lambda: messagebox.showinfo("Exportar",
                                                       "Funcionalidad de exportación aún no implementada.")).pack(
            pady=5)
        ttk.Button(memoria_window, text="Cerrar", command=memoria_window.destroy).pack(pady=5)

        self.update_log(f"Memoria descriptiva generada para el predio '{self.codigo_predio.get()}'.")

    def query_predios(self):
        query_window = tk.Toplevel(self)
        query_window.title("Consultar Predios")
        query_window.geometry("800x500")
        ttk.Label(query_window, text="Aquí podrás realizar consultas avanzadas sobre tus predios.").pack(pady=10)
        ttk.Button(query_window, text="Cerrar", command=query_window.destroy).pack(pady=5)
        self.update_log("Ventana de consulta de predios abierta.")

    def generate_reports(self):
        report_window = tk.Toplevel(self)
        report_window.title("Generar Reportes")
        report_window.geometry("700x400")
        ttk.Label(report_window, text="Aquí podrás generar diversos tipos de reportes.").pack(pady=10)
        ttk.Button(report_window, text="Cerrar", command=report_window.destroy).pack(pady=5)
        self.update_log("Ventana de reportes abierta.")

    def _manage_users(self):
        ManageUsersWindow(self, self.db_params)
        self.update_log("Ventana de gestión de usuarios abierta.")

    def _change_project(self):
        if messagebox.askyesno("Cambiar Proyecto",
                               "¿Estás seguro de que quieres cambiar de proyecto? Perderás cualquier cambio no guardado en el predio actual."):
            if self.db_conn:
                self.db_conn.close()
            self.destroy()
            self.master.deiconify()

    def _logout(self):
        if messagebox.askyesno("Cerrar Sesión", "¿Estás seguro de que quieres cerrar sesión?"):
            if self.db_conn:
                self.db_conn.close()
            self.destroy()
            self.master.master.deiconify()

    def _on_closing(self):
        if messagebox.askokcancel("Salir", "¿Estás seguro de que quieres salir?"):
            if self.db_conn:
                self.db_conn.close()
            self.master.master.destroy()


# --- CLASE PARA LA VENTANA DEL NUMERAL 1 (CONDICIÓN LEGAL) ---
class Numeral1Window(tk.Toplevel):
    def __init__(self, master, predio_codigo,
                 condicion_juridica_var,
                 documento_acredita_var,
                 numero_documento_var,
                 fecha_documento_var,
                 entidad_var,
                 titulares_list,  # Referencia a la lista de titulares de MainApplication
                 save_callback):  # Referencia a la función de guardado de MainApplication
        super().__init__(master)
        self.master = master
        self.title(f"1. Condición Legal - Predio: {predio_codigo}")
        self.geometry("700x550")  # Un tamaño más grande para acomodar los campos

        self.predio_codigo = predio_codigo
        self.condicion_juridica_var = condicion_juridica_var
        self.documento_acredita_var = documento_acredita_var
        self.numero_documento_var = numero_documento_var
        self.fecha_documento_var = fecha_documento_var
        self.entidad_var = entidad_var
        self.titulares_list = titulares_list  # ¡Ojo! Esto es una referencia a la lista original
        self.save_callback = save_callback

        # Variables temporales para añadir nuevo titular
        self.temp_nombre_titular = tk.StringVar()
        self.temp_dni_titular = tk.StringVar()

        self._setup_ui()
        self._populate_titulares_listbox()  # Cargar titulares al inicio

        self.protocol("WM_DELETE_WINDOW", self._on_closing_window)

    def _setup_ui(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)

        # Sección: Condición Jurídica
        condicion_frame = ttk.LabelFrame(main_frame, text="1.1 Condición Jurídica")
        condicion_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(condicion_frame, text="Condición:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        condiciones_juridicas = ["Propietario", "Posesionario", "Poseedor", "Ocupante", "Comunero",
                                 "Propietario No Inscrito"]
        self.condicion_combo = ttk.Combobox(condicion_frame, textvariable=self.condicion_juridica_var,
                                            values=condiciones_juridicas, state="readonly")
        self.condicion_combo.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        condicion_frame.grid_columnconfigure(1, weight=1)

        # Sección: Titulares
        titulares_frame = ttk.LabelFrame(main_frame, text="1.2 Titulares")
        titulares_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Listbox para mostrar titulares
        self.titulares_listbox = tk.Listbox(titulares_frame, height=5)
        self.titulares_listbox.pack(fill="both", expand=True, padx=5, pady=5)

        # Frame para añadir/eliminar titular
        add_remove_titular_frame = ttk.Frame(titulares_frame)
        add_remove_titular_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(add_remove_titular_frame, text="Nombre:").grid(row=0, column=0, padx=2, pady=2, sticky="w")
        ttk.Entry(add_remove_titular_frame, textvariable=self.temp_nombre_titular, width=30).grid(row=0, column=1,
                                                                                                  padx=2, pady=2,
                                                                                                  sticky="ew")

        ttk.Label(add_remove_titular_frame, text="DNI:").grid(row=1, column=0, padx=2, pady=2, sticky="w")
        ttk.Entry(add_remove_titular_frame, textvariable=self.temp_dni_titular, width=20).grid(row=1, column=1, padx=2,
                                                                                               pady=2, sticky="ew")

        ttk.Button(add_remove_titular_frame, text="Añadir Titular", command=self._add_titular).grid(row=0, column=2,
                                                                                                    padx=5, pady=2)
        ttk.Button(add_remove_titular_frame, text="Eliminar Titular Seleccionado", command=self._remove_titular).grid(
            row=1, column=2, padx=5, pady=2)
        add_remove_titular_frame.grid_columnconfigure(1, weight=1)

        # Sección: Documento que acredita titularidad
        documento_frame = ttk.LabelFrame(main_frame, text="1.3 Documento que Acredita Titularidad")
        documento_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(documento_frame, text="Tipo Documento:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        tipos_documento = ["Partida Registral", "Constancia De Posesión", "Certificado De Comunero Hábil"]
        self.doc_acredita_combo = ttk.Combobox(documento_frame, textvariable=self.documento_acredita_var,
                                               values=tipos_documento, state="readonly")
        self.doc_acredita_combo.grid(row=0, column=1, padx=5, pady=2, sticky="ew")

        ttk.Label(documento_frame, text="N° Documento:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(documento_frame, textvariable=self.numero_documento_var).grid(row=1, column=1, padx=5, pady=2,
                                                                                sticky="ew")

        ttk.Label(documento_frame, text="Fecha (YYYY-MM-DD):").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(documento_frame, textvariable=self.fecha_documento_var).grid(row=2, column=1, padx=5, pady=2,
                                                                               sticky="ew")

        ttk.Label(documento_frame, text="Entidad:").grid(row=3, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(documento_frame, textvariable=self.entidad_var).grid(row=3, column=1, padx=5, pady=2, sticky="ew")
        documento_frame.grid_columnconfigure(1, weight=1)

        # Botón de Guardar y Cerrar
        ttk.Button(main_frame, text="Guardar y Cerrar", command=self._on_closing_window).pack(pady=10)

    def _populate_titulares_listbox(self):
        self.titulares_listbox.delete(0, tk.END)
        for nombre, dni in self.titulares_list:
            self.titulares_listbox.insert(tk.END, f"Nombre: {nombre}, DNI: {dni}")

    def _add_titular(self):
        nombre = self.temp_nombre_titular.get().strip()
        dni = self.temp_dni_titular.get().strip()

        if not nombre:
            messagebox.showwarning("Advertencia", "El nombre del titular no puede estar vacío.")
            return

        self.titulares_list.append((nombre, dni))
        self._populate_titulares_listbox()
        self.temp_nombre_titular.set("")
        self.temp_dni_titular.set("")
        messagebox.showinfo("Titular Añadido", f"Titular '{nombre}' añadido. Recuerda guardar al cerrar la ventana.")

    def _remove_titular(self):
        selected_indices = self.titulares_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Advertencia", "Por favor, selecciona un titular para eliminar.")
            return

        index = selected_indices[0]
        nombre_removido = self.titulares_list[index][0]
        del self.titulares_list[index]
        self._populate_titulares_listbox()
        messagebox.showinfo("Titular Eliminado",
                            f"Titular '{nombre_removido}' eliminado. Recuerda guardar al cerrar la ventana.")

    def _on_closing_window(self):
        # Al cerrar, se llama a la función de guardado de MainApplication
        # para persistir todos los cambios (incluyendo los titulares)
        self.save_callback(self.predio_codigo)
        self.destroy()


# --- NUEVA CLASE PARA LA VENTANA DE LOS NUMERALES 2 Y 3 ---
class Numeral2and3Window(tk.Toplevel):
    def __init__(self, master, predio_codigo,
                 n2_entidad_var,
                 n3_progresiva_inicio_var, n3_progresiva_final_var, n3_lado_var, n3_tipo_var,
                 n3_zonificacion_var, n3_uso_actual_var, n3_clasificacion_tierras_cum_var,
                 n3_unidad_catastral_var, n3_sector_var, n3_distrito_var, n3_provincia_var,
                 n3_departamento_var, n3_referencia_var, n3_via_var, n3_manzana_var, n3_lote_var,
                 save_callback):
        super().__init__(master)
        self.master = master
        self.title(f"2 y 3. Datos del Solicitante / Datos Generales del Predio - Predio: {predio_codigo}")
        self.geometry("800x700")  # Un tamaño más grande para ambos numerales

        self.predio_codigo = predio_codigo
        self.n2_entidad_var = n2_entidad_var
        self.n3_progresiva_inicio_var = n3_progresiva_inicio_var
        self.n3_progresiva_final_var = n3_progresiva_final_var
        self.n3_lado_var = n3_lado_var
        self.n3_tipo_var = n3_tipo_var
        self.n3_zonificacion_var = n3_zonificacion_var
        self.n3_uso_actual_var = n3_uso_actual_var
        self.n3_clasificacion_tierras_cum_var = n3_clasificacion_tierras_cum_var
        self.n3_unidad_catastral_var = n3_unidad_catastral_var
        self.n3_sector_var = n3_sector_var
        self.n3_distrito_var = n3_distrito_var
        self.n3_provincia_var = n3_provincia_var
        self.n3_departamento_var = n3_departamento_var
        self.n3_referencia_var = n3_referencia_var
        self.n3_via_var = n3_via_var
        self.n3_manzana_var = n3_manzana_var
        self.n3_lote_var = n3_lote_var
        self.save_callback = save_callback

        self._setup_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_closing_window)

    def _setup_ui(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)

        # Usar un Canvas y un Scrollbar para permitir el desplazamiento
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- Numeral 2: Datos del Solicitante ---
        solicitante_frame = ttk.LabelFrame(scrollable_frame, text="2. Datos del Solicitante")
        solicitante_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(solicitante_frame, text="Entidad:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        entidades = ["PROVIAS NACIONAL - MTC", "Otros"]
        self.n2_entidad_combo = ttk.Combobox(solicitante_frame, textvariable=self.n2_entidad_var, values=entidades,
                                             state="readonly")
        self.n2_entidad_combo.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        solicitante_frame.grid_columnconfigure(1, weight=1)

        # --- Numeral 3: Datos Generales del Predio ---
        predio_general_frame = ttk.LabelFrame(scrollable_frame, text="3. Datos Generales del Predio")
        predio_general_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Progresivas
        ttk.Label(predio_general_frame, text="Progresiva Inicio:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(predio_general_frame, textvariable=self.n3_progresiva_inicio_var).grid(row=0, column=1, padx=5,
                                                                                         pady=2, sticky="ew")

        ttk.Label(predio_general_frame, text="Progresiva Final:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(predio_general_frame, textvariable=self.n3_progresiva_final_var).grid(row=1, column=1, padx=5, pady=2,
                                                                                        sticky="ew")

        # Lado
        ttk.Label(predio_general_frame, text="Lado:").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        lados = ["Derecho", "Izquierdo", "Ambos"]
        self.n3_lado_combo = ttk.Combobox(predio_general_frame, textvariable=self.n3_lado_var, values=lados,
                                          state="readonly")
        self.n3_lado_combo.grid(row=2, column=1, padx=5, pady=2, sticky="ew")

        # Tipo (Urbano/Rural)
        ttk.Label(predio_general_frame, text="Tipo:").grid(row=3, column=0, padx=5, pady=2, sticky="w")
        tipos_predio = ["Urbano", "Rural"]
        self.n3_tipo_combo = ttk.Combobox(predio_general_frame, textvariable=self.n3_tipo_var, values=tipos_predio,
                                          state="readonly")
        self.n3_tipo_combo.grid(row=3, column=1, padx=5, pady=2, sticky="ew")

        # Zonificación y Uso Actual
        ttk.Label(predio_general_frame, text="Zonificación:").grid(row=4, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(predio_general_frame, textvariable=self.n3_zonificacion_var).grid(row=4, column=1, padx=5, pady=2,
                                                                                    sticky="ew")

        ttk.Label(predio_general_frame, text="Uso Actual:").grid(row=5, column=0, padx=5, pady=2, sticky="w")
        usos_actuales = ["VIVIENDA", "AGRICOLA", "COMERCIO", "TERRENO"]
        self.n3_uso_actual_combo = ttk.Combobox(predio_general_frame, textvariable=self.n3_uso_actual_var,
                                                values=usos_actuales, state="readonly")
        self.n3_uso_actual_combo.grid(row=5, column=1, padx=5, pady=2, sticky="ew")

        # Clasificación de Tierras CUM y Unidad Catastral
        ttk.Label(predio_general_frame, text="Clasificación de Tierras CUM:").grid(row=6, column=0, padx=5, pady=2,
                                                                                   sticky="w")
        ttk.Entry(predio_general_frame, textvariable=self.n3_clasificacion_tierras_cum_var).grid(row=6, column=1,
                                                                                                 padx=5, pady=2,
                                                                                                 sticky="ew")

        ttk.Label(predio_general_frame, text="Unidad Catastral:").grid(row=7, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(predio_general_frame, textvariable=self.n3_unidad_catastral_var).grid(row=7, column=1, padx=5, pady=2,
                                                                                        sticky="ew")

        # Campos que se "fijan"
        ttk.Label(predio_general_frame, text="Sector:").grid(row=8, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(predio_general_frame, textvariable=self.n3_sector_var).grid(row=8, column=1, padx=5, pady=2,
                                                                              sticky="ew")

        ttk.Label(predio_general_frame, text="Distrito:").grid(row=9, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(predio_general_frame, textvariable=self.n3_distrito_var).grid(row=9, column=1, padx=5, pady=2,
                                                                                sticky="ew")

        ttk.Label(predio_general_frame, text="Provincia:").grid(row=10, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(predio_general_frame, textvariable=self.n3_provincia_var).grid(row=10, column=1, padx=5, pady=2,
                                                                                 sticky="ew")

        ttk.Label(predio_general_frame, text="Departamento:").grid(row=11, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(predio_general_frame, textvariable=self.n3_departamento_var).grid(row=11, column=1, padx=5, pady=2,
                                                                                    sticky="ew")

        ttk.Label(predio_general_frame, text="Referencia:").grid(row=12, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(predio_general_frame, textvariable=self.n3_referencia_var).grid(row=12, column=1, padx=5, pady=2,
                                                                                  sticky="ew")

        # Últimos campos
        ttk.Label(predio_general_frame, text="Vía:").grid(row=13, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(predio_general_frame, textvariable=self.n3_via_var).grid(row=13, column=1, padx=5, pady=2,
                                                                           sticky="ew")

        ttk.Label(predio_general_frame, text="Manzana:").grid(row=14, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(predio_general_frame, textvariable=self.n3_manzana_var).grid(row=14, column=1, padx=5, pady=2,
                                                                               sticky="ew")

        ttk.Label(predio_general_frame, text="Lote:").grid(row=15, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(predio_general_frame, textvariable=self.n3_lote_var).grid(row=15, column=1, padx=5, pady=2,
                                                                            sticky="ew")

        predio_general_frame.grid_columnconfigure(1, weight=1)

        # Botón de Guardar y Cerrar
        ttk.Button(main_frame, text="Guardar y Cerrar", command=self._on_closing_window).pack(pady=10)

    def _on_closing_window(self):
        self.save_callback(self.predio_codigo)
        self.destroy()


# --- CLASE PARA LA SELECCIÓN DE PROYECTO (EL SEGUNDO FORMULARIO) ---


    def _setup_ui(self):
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(expand=True, fill="both")

        ttk.Label(main_frame, text="Selecciona o Crea un Proyecto", font=("Arial", 14, "bold")).pack(pady=10)

        select_frame = ttk.LabelFrame(main_frame, text="Proyectos Existentes")
        select_frame.pack(pady=10, padx=5, fill="x")

        self.project_listbox = tk.Listbox(select_frame, height=5)
        self.project_listbox.pack(padx=10, pady=5, fill="both", expand=True)

        action_buttons_frame = ttk.Frame(main_frame)
        action_buttons_frame.pack(pady=5)

        self.select_project_button = ttk.Button(action_buttons_frame, text="Seleccionar Proyecto",
                                                command=self._select_project)
        self.select_project_button.pack(side="left", padx=5)

        if self.user_role == 'administrador':
            self.create_project_button = ttk.Button(action_buttons_frame, text="Crear Nuevo Proyecto",
                                                    command=self._create_project)
            self.create_project_button.pack(side="right", padx=5)

            ttk.Label(main_frame, text="Nombre del Nuevo Proyecto (Admin):").pack(padx=10, pady=5, anchor="w")
            self.new_project_name_entry = ttk.Entry(main_frame, width=40)
            self.new_project_name_entry.pack(padx=10, pady=5)

        ttk.Button(main_frame, text="Cerrar Sesión", command=self._logout).pack(pady=10)

    def _connect_db(self):
        try:
            self.db_conn = psycopg2.connect(
                host=self.db_params['host'],
                database=self.db_params['dbname'],
                user=self.db_params['user'],
                password=self.db_params['password'],
                sslmode='disable'
            )
            self.db_cursor = self.db_conn.cursor()
            return True
        except Exception as e:
            messagebox.showerror("Error de Conexión",
                                 f"No se pudo conectar a la base de datos para la selección de proyecto: {e}")
            return False

    def load_projects(self):
        if not self.db_conn:
            return
        try:
            self.db_cursor.execute("SELECT id, nombre_proyecto FROM proyectos ORDER BY nombre_proyecto")
            projects = self.db_cursor.fetchall()
            self.project_listbox.delete(0, tk.END)
            for project_id, project_name in projects:
                self.project_listbox.insert(tk.END, project_name)
            if not projects:
                messagebox.showinfo("Información", "No hay proyectos existentes. Crea uno nuevo.")
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar proyectos: {e}")
            if self.db_conn:
                self.db_conn.rollback()

    def _select_project(self):
        selected_index = self.project_listbox.curselection()
        if not selected_index:
            messagebox.showwarning("Advertencia", "Por favor, selecciona un proyecto de la lista.")
            return

        selected_name = self.project_listbox.get(selected_index[0])
        try:
            self.db_cursor.execute("SELECT id FROM proyectos WHERE nombre_proyecto = %s", (selected_name,))
            project_id = self.db_cursor.fetchone()[0]
            self.db_conn.close()
            self.destroy()
            MainApplication(self.master, self.db_params, project_id, selected_name, self.user_role)
        except Exception as e:
            messagebox.showerror("Error", f"Error al seleccionar el proyecto: {e}")
            if self.db_conn:
                self.db_conn.rollback()

    def _create_project(self):
        new_name = self.new_project_name_entry.get().strip()
        if not new_name:
            messagebox.showwarning("Advertencia", "El nombre del proyecto no puede estar vacío.")
            return

        try:
            self.db_cursor.execute("INSERT INTO proyectos (nombre_proyecto) VALUES (%s) RETURNING id", (new_name,))
            project_id = self.db_cursor.fetchone()[0]
            self.db_conn.commit()
            messagebox.showinfo("Éxito", f"Proyecto '{new_name}' creado con éxito.")

            self.db_conn.close()
            self.destroy()
            MainApplication(self.master, self.db_params, project_id, new_name, self.user_role)
        except psycopg2.errors.UniqueViolation:
            messagebox.showerror("Error", f"El proyecto '{new_name}' ya existe.")
            if self.db_conn:
                self.db_conn.rollback()
        except Exception as e:
            messagebox.showerror("Error", f"Error al crear proyecto: {e}")
            if self.db_conn:
                self.db_conn.rollback()

    def _logout(self):
        if messagebox.askyesno("Cerrar Sesión", "¿Estás seguro de que quieres cerrar sesión?"):
            if self.db_conn:
                self.db_conn.close()
            self.destroy()
            self.master.deiconify()

    def _on_closing(self):
        if messagebox.askokcancel("Salir", "¿Estás seguro de que quieres salir?"):
            if self.db_conn:
                self.db_conn.close()
            self.master.destroy()


# --- CLASE PARA LA VENTANA DE GESTIÓN DE USUARIOS (NUEVA) ---
class ManageUsersWindow(tk.Toplevel):
    def __init__(self, master, db_params):
        super().__init__(master)
        self.title("Gestionar Usuarios")
        self.geometry("600x400")
        self.db_params = db_params
        self.db_conn = None
        self.db_cursor = None

        self._connect_db()
        self._setup_ui()
        self.load_users()

    def _connect_db(self):
        try:
            self.db_conn = psycopg2.connect(
                host=self.db_params['host'],
                database=self.db_params['dbname'],
                user=self.db_params['user'],
                password=self.db_params['password'],
                sslmode='disable'
            )
            self.db_cursor = self.db_conn.cursor()
            return True
        except Exception as e:
            messagebox.showerror("Error de Conexión",
                                 f"No se pudo conectar a la base de datos para gestión de usuarios: {e}")
            return False

    def _setup_ui(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)

        user_list_frame = ttk.LabelFrame(main_frame, text="Usuarios Existentes")
        user_list_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.user_listbox = tk.Listbox(user_list_frame, height=10)
        self.user_listbox.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(user_list_frame, orient="vertical", command=self.user_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.user_listbox.config(yscrollcommand=scrollbar.set)

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", padx=5, pady=5)

        ttk.Button(button_frame, text="Cambiar Rol", command=self._change_user_role).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Eliminar Usuario", command=self._delete_user).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Cerrar", command=self.destroy).pack(side="right", padx=5)

    def load_users(self):
        if not self.db_conn:
            return
        try:
            self.db_cursor.execute("SELECT username, role FROM usuarios ORDER BY username")
            users = self.db_cursor.fetchall()
            self.user_listbox.delete(0, tk.END)
            for username, role in users:
                self.user_listbox.insert(tk.END, f"{username} ({role})")
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar usuarios: {e}")
            if self.db_conn:
                self.db_conn.rollback()

    def _change_user_role(self):
        selected_index = self.user_listbox.curselection()
        if not selected_index:
            messagebox.showwarning("Advertencia", "Por favor, selecciona un usuario.")
            return

        selected_user_text = self.user_listbox.get(selected_index[0])
        username = selected_user_text.split(' ')[0]

        if username == 'lfloresad':
            messagebox.showwarning("Advertencia",
                                   "No se puede cambiar el rol del usuario principal 'lfloresad' desde aquí.")
            return

        current_role_match = selected_user_text.split('(')
        current_role = current_role_match[1][:-1] if len(current_role_match) > 1 else 'invitado'

        new_role = simpledialog.askstring("Cambiar Rol",
                                          f"Cambiar rol de '{username}' (actual: {current_role}) a 'administrador' o 'invitado'?",
                                          parent=self)
        if new_role not in ['administrador', 'invitado']:
            messagebox.showwarning("Advertencia", "Rol no válido. Debe ser 'administrador' o 'invitado'.")
            return

        try:
            self.db_cursor.execute("UPDATE usuarios SET role = %s WHERE username = %s", (new_role, username))
            self.db_conn.commit()
            messagebox.showinfo("Éxito", f"Rol de '{username}' cambiado a '{new_role}'.")
            self.load_users()
        except Exception as e:
            messagebox.showerror("Error", f"Error al cambiar rol: {e}")
            if self.db_conn:
                self.db_conn.rollback()

    def _delete_user(self):
        selected_index = self.user_listbox.curselection()
        if not selected_index:
            messagebox.showwarning("Advertencia", "Por favor, selecciona un usuario para eliminar.")
            return

        selected_user_text = self.user_listbox.get(selected_index[0])
        username_to_delete = selected_user_text.split(' ')[0]

        if username_to_delete == 'lfloresad':
            messagebox.showwarning("Advertencia", "No se puede eliminar al usuario principal 'lfloresad'.")
            return

        if messagebox.askyesno("Confirmar Eliminación",
                               f"¿Estás seguro de que quieres eliminar al usuario '{username_to_delete}'?"):
            try:
                self.db_cursor.execute("DELETE FROM usuarios WHERE username = %s", (username_to_delete,))
                self.db_conn.commit()
                messagebox.showinfo("Éxito", f"Usuario '{username_to_delete}' eliminado con éxito.")
                self.load_users()
            except Exception as e:
                messagebox.showerror("Error", f"Error al eliminar usuario: {e}")
                if self.db_conn:
                    self.db_conn.rollback()


# --- CLASE PARA EL INICIO DE SESIÓN (EL PRIMER FORMULARIO) ---
class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Inicio de Sesión")
        self.geometry("350x250")
        self.resizable(False, False)

        self.db_params = {
            'host': 'localhost',
            'dbname': 'memorias_descriptivas',
            'user': 'lfloresad',
            'password': '253202'
        }

        self.db_conn = None
        self.db_cursor = None

        self._create_login_ui()
        self._connect_db_and_create_initial_tables()

    def _create_login_ui(self):
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(expand=True, fill="both")

        ttk.Label(main_frame, text="Usuario:").pack(pady=5, anchor="w")
        self.username_entry = ttk.Entry(main_frame, width=30)
        self.username_entry.pack(pady=5)

        ttk.Label(main_frame, text="Contraseña:").pack(pady=5, anchor="w")
        self.password_entry = ttk.Entry(main_frame, width=30, show="*")
        self.password_entry.pack(pady=5)

        ttk.Button(main_frame, text="Iniciar Sesión", command=self._login).pack(pady=10)

        self.register_button = ttk.Button(main_frame, text="Registrar Nuevo Usuario", command=self._register_user)
        self.register_button.pack(pady=5)

    def _connect_db_and_create_initial_tables(self):
        try:
            conn = psycopg2.connect(
                host=self.db_params['host'],
                database=self.db_params['dbname'],
                user=self.db_params['user'],
                password=self.db_params['password'],
                sslmode='disable'
            )
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(128) NOT NULL,
                    role VARCHAR(20) DEFAULT 'invitado' NOT NULL
                );
            """)
            try:
                cursor.execute(
                    "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'invitado' NOT NULL;")
                conn.commit()
            except psycopg2.errors.DuplicateColumn:
                conn.rollback()
            except Exception as e:
                conn.rollback()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS proyectos (
                    id SERIAL PRIMARY KEY,
                    nombre_proyecto VARCHAR(255) UNIQUE NOT NULL,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            messagebox.showerror("Error de Configuración DB",
                                 f"No se pudo conectar a la base de datos o crear las tablas iniciales. Asegúrate de que PostgreSQL esté corriendo y los datos de conexión sean correctos: {e}")
            self.destroy()

    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def _login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showwarning("Advertencia", "Por favor, ingresa usuario y contraseña.")
            return

        conn = None
        cursor = None
        try:
            conn = psycopg2.connect(
                host=self.db_params['host'],
                database=self.db_params['dbname'],
                user=self.db_params['user'],
                password=self.db_params['password'],
                sslmode='disable'
            )
            cursor = conn.cursor()

            hashed_password = self._hash_password(password)
            cursor.execute("SELECT id, role FROM usuarios WHERE username = %s AND password_hash = %s",
                           (username, hashed_password))
            user_data = cursor.fetchone()

            if user_data:
                user_id, user_role = user_data
                messagebox.showinfo("Éxito", f"¡Bienvenido, {username} (Rol: {user_role})!")
                self.username_entry.delete(0, tk.END)
                self.password_entry.delete(0, tk.END)

                cursor.close()
                conn.close()
                ProjectSelectionWindow(self, self.db_params, user_role)
            else:
                messagebox.showerror("Error de Login", "Usuario o contraseña incorrectos.")

        except Exception as e:
            messagebox.showerror("Error", f"Error al intentar iniciar sesión: {e}")
        finally:
            if cursor and not cursor.closed:
                cursor.close()
            if conn and not conn.closed:
                conn.close()

    def _register_user(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showwarning("Advertencia", "Por favor, ingresa usuario y contraseña para registrarte.")
            return

        conn = None
        cursor = None
        try:
            conn = psycopg2.connect(
                host=self.db_params['host'],
                database=self.db_params['dbname'],
                user=self.db_params['user'],
                password=self.db_params['password'],
                sslmode='disable'
            )
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM usuarios WHERE username = %s", (username,))
            if cursor.fetchone():
                messagebox.showerror("Error de Registro", "El nombre de usuario ya existe. Elige otro.")
                return

            hashed_password = self._hash_password(password)
            cursor.execute("INSERT INTO usuarios (username, password_hash, role) VALUES (%s, %s, %s)",
                           (username, hashed_password, 'invitado'))
            conn.commit()
            messagebox.showinfo("Registro Exitoso",
                                "Usuario registrado con éxito como 'invitado'. Ahora puedes iniciar sesión.")
            self.username_entry.delete(0, tk.END)
            self.password_entry.delete(0, tk.END)

        except Exception as e:
            messagebox.showerror("Error de Registro", f"Error al intentar registrar usuario: {e}")
            if conn:
                conn.rollback()
        finally:
            if cursor and not cursor.closed:
                cursor.close()
            if conn and not conn.closed:
                conn.close()


# --- INICIO DE LA APLICACIÓN ---
if __name__ == "__main__":
    app = LoginWindow()
    app.mainloop()
