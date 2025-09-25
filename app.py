from dash import Dash, html, dcc, dash_table, Input, Output, State, callback_context
import polars as pl
import pandas as pd
import os
import re
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from io import BytesIO
from datetime import datetime
from pathlib import Path
import flask
BASE_DIR = Path(__file__).parent
# ========== CONFIGURACIÓN INICIAL ==========
COLOR_PRIMARIO = '#611232'  # Verde oscuro
COLOR_SECUNDARIO = '#AE8640'  # Dorado
COLOR_FONDO = '#FFF8E7'  # Beige claro
COLOR_BORDE = '#7A1737'  # Bordó
COLOR_TEXTO = '#000000'  # Negro
COLOR_TITULO = '#AE8640'  # Dorado

# Crear una aplicación Flask para Dash
flask_server = flask.Flask(__name__)




# Inicialización de la app Dash
app = Dash(__name__, server=flask_server, suppress_callback_exceptions=True)

# Esto es necesario para Ploomber
server = app.server
app = Dash(
    __name__,
    server=flask_server,
    url_base_pathname="/infraestructura/",
    suppress_callback_exceptions=True,
    external_stylesheets=[
        'https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600&display=swap',
        dbc.themes.BOOTSTRAP,
    ]
)
server = app.server
# Cargar bases de datos
try:
    # Cargar bases
    df_infra = pl.read_excel(BASE_DIR / "data/infraestructura.xlsx")
    df_clues = pl.read_excel(BASE_DIR / "data/clues_julio.xlsx")

    # Merge
    df_merged = df_infra.join(df_clues.select(['clues_imb','entidad']), on='clues_imb', how='left')

    # Lista de entidades
    entidades_options = [{'label': e, 'value': e} for e in df_merged['entidad'].unique().sort().to_list()]
    
    print(f"Datos cargados correctamente. {len(df_merged)} registros encontrados.")
    print(f"Entidades disponibles: {[e['label'] for e in entidades_options]}")

except Exception as e:
    print(f"Error al cargar archivos: {e}")
    # Datos de ejemplo en caso de error
    datos_ejemplo = [
        {'clues_imb': '01ABC123', 'entidad': 'Aguascalientes', 'nombre_de_la_unidad': 'Hospital General de Aguascalientes', 
         'consultorios_generales_habilitados': 12, 'consultorios_generales_inhabilitados': 3, 'total_consultorios_generales': 15,
         'consultorios_de_especialidad_habilitados': 8, 'consultorios_de_especialidad_inhabilitados': 2, 'total_consultorios_de_especialidad': 10,
         'quirofanos_habilitados': 4, 'quirofanos_inhabilitados': 1, 'total_de_quirofanos': 5},
        {'clues_imb': '02DEF456', 'entidad': 'Baja California', 'nombre_de_la_unidad': 'Hospital General de Tijuana', 
         'consultorios_generales_habilitados': 15, 'consultorios_generales_inhabilitados': 5, 'total_consultorios_generales': 20,
         'consultorios_de_especialidad_habilitados': 10, 'consultorios_de_especialidad_inhabilitados': 2, 'total_consultorios_de_especialidad': 12,
         'quirofanos_habilitados': 5, 'quirofanos_inhabilitados': 1, 'total_de_quirofanos': 6},
    ]
    df_merged = pl.DataFrame(datos_ejemplo)
    entidades_options = [{'label': 'Aguascalientes', 'value': 'Aguascalientes'}, 
                        {'label': 'Baja California', 'value': 'Baja California'}]

# Servicios de consultorio
servicios_options = [
    {'label': 'Medicina General', 'value': 'medicina_general'},
    {'label': 'Pediatría', 'value': 'pediatria'},
    {'label': 'Ginecología', 'value': 'ginecologia'},
    {'label': 'Cirugía General', 'value': 'cirugia_general'},
    {'label': 'Traumatología', 'value': 'traumatologia'},
    {'label': 'Oftalmología', 'value': 'oftalmologia'},
    {'label': 'Otorrinolaringología', 'value': 'otorrinolaringologia'},
    {'label': 'Dermatología', 'value': 'dermatologia'},
    {'label': 'Psiquiatría', 'value': 'psiquiatria'},
    {'label': 'Odontología', 'value': 'odontologia'},
]

# Días de la semana
dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
turnos = ['Matutino', 'Vespertino', 'Nocturno']

# Layout principal
app.layout = html.Div([
    # Encabezado con logos
    html.Div([
        html.Div(className='header-logo', children=[
            html.Img(
                src='https://framework-gb.cdn.gob.mx/landing/img/logoheader.svg',
                style={'height': '50px', 'marginRight': '20px'}
            ),
            html.Img(
                src='https://imss.gob.mx/assets/img/logo_imss.svg',
                style={'height': '50px'}
            )
        ], style={'display': 'flex', 'alignItems': 'center'}),
    ], style={'backgroundColor': COLOR_PRIMARIO, 'padding': '10px', 'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center'}),
    
    # Contenido principal
    html.Div([
        html.Div([
            html.H1("Registro de Infraestructura Hospitalaria", 
                   className='text-center', 
                   style={'color': COLOR_PRIMARIO, 'marginBottom': '30px', 'fontWeight': 'bold'}),
            
            # Sección de selección de estado
            html.Div(className='mb-3', children=[
                html.Label("Entidad:", className='fw-bold', style={'fontSize': '18px'}),
                dcc.Dropdown(
                    id="dropdown-entidad",
                    options=entidades_options,
                    placeholder="Seleccione un estado...",
                    style={'borderRadius': '15px', 'padding': '5px', 'border': f'1px solid {COLOR_BORDE}'}
                )
            ]),
            
            # Sección CLUES
            html.Div(className='mb-3', children=[
                html.Label("CLUES:", className='fw-bold', style={'fontSize': '18px'}),
                dcc.Dropdown(
                    id="dropdown-clues",
                    options=[],
                    placeholder="Primero seleccione entidad",
                    disabled=True,
                    style={'borderRadius': '15px', 'padding': '5px', 'border': f'1px solid {COLOR_BORDE}'}
                )
            ]),
            
            html.Div(id="info-clues", className='font-montserrat'),
            html.Hr(style={'borderTop': f'2px solid {COLOR_BORDE}', 'marginBottom': '25px'}),
            
            # Sección de Consultorios
            html.Div([
                html.H3("Consultorios", className='mb-3', style={'color': COLOR_PRIMARIO}),
                html.Div([
                    html.Label("Total de consultorios según sistema:", className='fw-bold'),
                    dcc.Input(
                        id="total-consultorios-sistema",
                        type="number",
                        disabled=True,
                        className='mb-2',
                        style={'width': '100%', 'padding': '8px', 'borderRadius': '5px', 'border': f'1px solid {COLOR_BORDE}'}
                    ),
                    html.Label("¿Coincide con la realidad?", className='fw-bold mt-3'),
                    dcc.RadioItems(
                        id="coincide-consultorios",
                        options=[
                            {'label': 'Sí', 'value': 'si'},
                            {'label': 'No', 'value': 'no'}
                        ],
                        value=None,
                        labelStyle={'display': 'inline-block', 'marginRight': '15px'}
                    ),
                    html.Div(id="input-consultorios-real", style={'display': 'none'}, children=[
                        html.Label("Número actualizado de consultorios:", className='fw-bold mt-2'),
                        dcc.Input(
                            id="consultorios-real",
                            type="number",
                            style={'width': '100%', 'padding': '8px', 'borderRadius': '5px', 'border': f'1px solid {COLOR_BORDE}'}
                        )
                    ]),
                    html.Button("Guardar y Continuar", 
                               id="btn-guardar-consultorios", 
                               className='mt-3',
                               style={
                                   'backgroundColor': COLOR_SECUNDARIO,
                                   'color': 'white',
                                   'border': 'none',
                                   'padding': '10px 20px',
                                   'borderRadius': '5px',
                                   'cursor': 'pointer',
                                   'display': 'none'
                               })
                ])
            ], className='mb-4 p-3', style={'border': f'2px solid {COLOR_BORDE}', 'borderRadius': '10px', 'backgroundColor': 'white'}),
            
            # Sección de Servicios por Consultorio (inicialmente oculta)
            html.Div(id="seccion-servicios", style={'display': 'none'}, children=[
                html.H3("Servicios por Consultorio", className='mb-3', style={'color': COLOR_PRIMARIO}),
                
                # Consultorio 1
                html.Div([
                    html.H4("Consultorio 1", style={'color': COLOR_PRIMARIO, 'marginBottom': '15px'}),
                    html.Label("Seleccione los servicios disponibles:", className='fw-bold mb-2'),
                    dcc.Checklist(
                        id="servicios-consultorio-1",
                        options=servicios_options,
                        value=[],
                        labelStyle={'display': 'block', 'marginBottom': '5px'}
                    ),
                ], className='p-3 mb-3', style={'border': f'1px solid {COLOR_BORDE}', 'borderRadius': '5px', 'backgroundColor': '#f9f9f9'}),
                
                # Consultorio 2
                html.Div([
                    html.H4("Consultorio 2", style={'color': COLOR_PRIMARIO, 'marginBottom': '15px'}),
                    html.Label("Seleccione los servicios disponibles:", className='fw-bold mb-2'),
                    dcc.Checklist(
                        id="servicios-consultorio-2",
                        options=servicios_options,
                        value=[],
                        labelStyle={'display': 'block', 'marginBottom': '5px'}
                    ),
                ], className='p-3 mb-3', style={'border': f'1px solid {COLOR_BORDE}', 'borderRadius': '5px', 'backgroundColor': '#f9f9f9'}),
                
                html.Button("Guardar y Continuar", 
                           id="btn-guardar-servicios", 
                           className='mt-3',
                           style={
                               'backgroundColor': COLOR_SECUNDARIO,
                               'color': 'white',
                               'border': 'none',
                               'padding': '10px 20px',
                               'borderRadius': '5px',
                               'cursor': 'pointer'
                           })
            ]),
            
            # Sección de Horarios por Consultorio (inicialmente oculta)
            html.Div(id="seccion-horarios", style={'display': 'none'}, children=[
                html.H3("Horarios por Consultorio", className='mb-3', style={'color': COLOR_PRIMARIO}),
                
                # Selector de consultorio para horarios
                html.Div([
                    html.Label("Seleccione el consultorio:", className='fw-bold mb-2'),
                    dcc.RadioItems(
                        id="selector-consultorio-horarios",
                        options=[
                            {'label': 'Consultorio 1', 'value': 'consultorio-1'},
                            {'label': 'Consultorio 2', 'value': 'consultorio-2'}
                        ],
                        value='consultorio-1',
                        labelStyle={'display': 'inline-block', 'marginRight': '15px'}
                    ),
                ], className='mb-3 p-3', style={'border': f'1px solid {COLOR_BORDE}', 'borderRadius': '5px', 'backgroundColor': '#f9f9f9'}),
                
                # Información de servicios disponibles
                html.Div(id="info-servicios-consultorio", className='mb-3 p-3', 
                        style={'border': f'1px solid {COLOR_BORDE}', 'borderRadius': '5px', 'backgroundColor': '#f0f8ff'}),
                
                # Matriz de horarios
                html.Div([
                    html.Div("Seleccione un día y turno para asignar servicios:", 
                            className='fw-bold mb-2'),
                    
                    # Selectores de día y turno
                    html.Div([
                        html.Div([
                            html.Label("Día:", className='fw-bold'),
                            dcc.Dropdown(
                                id="selector-dia",
                                options=[{'label': dia, 'value': dia.lower()} for dia in dias_semana],
                                placeholder="Seleccione un día"
                            )
                        ], style={'width': '48%', 'display': 'inline-block', 'marginRight': '4%'}),
                        
                        html.Div([
                            html.Label("Turno:", className='fw-bold'),
                            dcc.Dropdown(
                                id="selector-turno",
                                options=[{'label': turno, 'value': turno.lower()} for turno in turnos],
                                placeholder="Seleccione un turno"
                            )
                        ], style={'width': '48%', 'display': 'inline-block'})
                    ], style={'marginBottom': '20px'}),
                    
                    # Selector de servicios para el día y turno seleccionados
                    html.Div(id="selector-servicios-horario", style={'marginBottom': '20px'}),
                    
                    # Botón para asignar servicio
                    html.Button("Asignar Servicio", 
                               id="btn-asignar-servicio", 
                               style={
                                   'backgroundColor': COLOR_PRIMARIO,
                                   'color': 'white',
                                   'border': 'none',
                                   'padding': '10px 20px',
                                   'borderRadius': '5px',
                                   'cursor': 'pointer',
                                   'marginBottom': '20px',
                                   'display': 'none'
                               }),
                    
                    # Tabla de horarios
                    html.Div("Horarios asignados:", className='fw-bold mb-2'),
                    html.Div(id="tabla-horarios-container")
                    
                ], className='p-3', style={'border': f'2px solid {COLOR_BORDE}', 'borderRadius': '10px', 'backgroundColor': 'white'}),
                
                html.Div([
                    html.Button("Guardar Información", 
                               id="btn-guardar-todo", 
                               className='mt-3',
                               style={
                                   'backgroundColor': COLOR_PRIMARIO,
                                   'color': 'white',
                                   'border': 'none',
                                   'padding': '10px 20px',
                                   'borderRadius': '5px',
                                   'cursor': 'pointer',
                                   'marginRight': '10px'
                               }),
                    html.Button("Exportar a Excel", 
                               id="btn-exportar-excel", 
                               className='mt-3',
                               style={
                                   'backgroundColor': COLOR_SECUNDARIO,
                                   'color': 'white',
                                   'border': 'none',
                                   'padding': '10px 20px',
                                   'borderRadius': '5px',
                                   'cursor': 'pointer'
                               })
                ], style={'marginTop': '20px'}),
                dcc.Download(id="download-excel"),
                
                # Almacenar datos de horarios
                dcc.Store(id='store-horarios-consultorio-1', data={}),
                dcc.Store(id='store-horarios-consultorio-2', data={})
            ]),
            
            # Notificaciones
            html.Div(id="notification", className='text-center mt-3'),
            
        ], className='p-4', style={'maxWidth': '1200px', 'margin': '0 auto'})
    ], style={
        'backgroundColor': COLOR_FONDO, 
        'minHeight': '100vh',
        'fontFamily': 'Montserrat, sans-serif'
    })
])

# ========== CALLBACKS ==========

# Actualizar opciones de CLUES según estado seleccionado
@app.callback(
    [Output("dropdown-clues", "options"), Output("dropdown-clues", "disabled")],
    Input("dropdown-entidad", "value")
)
def update_clues_options(entidad_seleccionada):
    if not entidad_seleccionada:
        return [], True
    
    try:
        # Filtrar las CLUES por el estado seleccionado
        df_filtrado = df_merged.filter(pl.col("entidad") == entidad_seleccionada)
        options = [{"label": f"{row['clues_imb']} - {row.get('nombre_de_la_unidad', 'Unidad de salud')}", "value": row['clues_imb']} 
                  for row in df_filtrado.rows(named=True)]
        
        print(f"CLUES encontradas para {entidad_seleccionada}: {len(options)}")
        return options, False
        
    except Exception as e:
        print(f"Error al filtrar CLUES: {e}")
        return [], True

# Mostrar información de la CLUES seleccionada
@app.callback(
    Output("info-clues", "children"),
    Input("dropdown-clues", "value")
)
def show_clues_info(clues_seleccionada):
    if not clues_seleccionada:
        return ""
    
    try:
        # Buscar la información de la CLUES seleccionada
        info = df_merged.filter(pl.col("clues_imb") == clues_seleccionada).rows(named=True)[0]
        
        # Calcular total de consultorios
        consultorios_generales = info.get('total_consultorios_generales', 0) or 0
        consultorios_especialidad = info.get('total_consultorios_de_especialidad', 0) or 0
        total_consultorios = consultorios_generales + consultorios_especialidad
        
        return html.Div([
            html.P(f"CLUES: {clues_seleccionada}", style={'margin': '5px 0', 'fontWeight': 'bold'}),
            html.P(f"Entidad: {info.get('entidad', 'N/A')}", style={'margin': '5px 0'}),
            html.P(f"Consultorios generales: {consultorios_generales}", style={'margin': '5px 0'}),
            html.P(f"Consultorios especialidad: {consultorios_especialidad}", style={'margin': '5px 0'}),
            html.P(f"Total consultorios: {total_consultorios}", style={'margin': '5px 0', 'fontWeight': 'bold'}),
            html.P(f"Quirófanos: {info.get('total_de_quirofanos', 'N/A')}", style={'margin': '5px 0'}),
        ], style={
            'backgroundColor': '#f8f9fa',
            'padding': '15px',
            'borderRadius': '5px',
            'marginTop': '15px',
            'border': f'1px solid {COLOR_BORDE}'
        })
    except Exception as e:
        print(f"Error al mostrar info de CLUES: {e}")
        return html.Div("Error al cargar información de la unidad", style={'color': 'red', 'padding': '10px'})

# Mostrar total de consultorios según sistema
@app.callback(
    Output("total-consultorios-sistema", "value"),
    Input("dropdown-clues", "value")
)
def update_total_consultorios(clues_seleccionada):
    if not clues_seleccionada:
        raise PreventUpdate
    
    try:
        info = df_merged.filter(pl.col("clues_imb") == clues_seleccionada).rows(named=True)[0]
        consultorios_generales = info.get('total_consultorios_generales', 0) or 0
        consultorios_especialidad = info.get('total_consultorios_de_especialidad', 0) or 0
        return consultorios_generales + consultorios_especialidad
    except Exception as e:
        print(f"Error al calcular consultorios: {e}")
        return 0

# Mostrar/ocultar input para número real de consultorios y botón de guardar
@app.callback(
    [Output("input-consultorios-real", "style"),
     Output("btn-guardar-consultorios", "style")],
    Input("coincide-consultorios", "value")
)
def toggle_consultorios_real_input(coincide):
    if coincide == 'no':
        return {'display': 'block', 'marginTop': '15px'}, {'display': 'block'}
    elif coincide == 'si':
        return {'display': 'none'}, {'display': 'block'}
    return {'display': 'none'}, {'display': 'none'}

# Mostrar sección de servicios cuando se guarde la información de consultorios
@app.callback(
    Output("seccion-servicios", "style"),
    Input("btn-guardar-consultorios", "n_clicks"),
    [State("coincide-consultorios", "value"),
     State("consultorios-real", "value")],
    prevent_initial_call=True
)
def mostrar_seccion_servicios(n_clicks, coincide, consultorios_real):
    if n_clicks and n_clicks > 0:
        if coincide == 'si' or (coincide == 'no' and consultorios_real is not None):
            return {'display': 'block', 'marginTop': '20px'}
    return {'display': 'none'}

# Mostrar sección de horarios cuando se guarden los servicios
@app.callback(
    Output("seccion-horarios", "style"),
    Input("btn-guardar-servicios", "n_clicks"),
    prevent_initial_call=True
)
def mostrar_seccion_horarios(n_clicks):
    if n_clicks and n_clicks > 0:
        return {'display': 'block', 'marginTop': '20px'}
    return {'display': 'none'}

# Mostrar información de servicios disponibles para el consultorio seleccionado
@app.callback(
    Output("info-servicios-consultorio", "children"),
    [Input("selector-consultorio-horarios", "value"),
     Input("servicios-consultorio-1", "value"),
     Input("servicios-consultorio-2", "value")]
)
def mostrar_servicios_consultorio(consultorio_seleccionado, servicios_1, servicios_2):
    if consultorio_seleccionado == 'consultorio-1':
        servicios = servicios_1
        texto = "Consultorio 1"
    else:
        servicios = servicios_2
        texto = "Consultorio 2"
    
    if not servicios:
        return html.P(f"{texto}: No hay servicios seleccionados", style={'margin': '0'})
    
    # Obtener nombres de servicios seleccionados
    nombres_servicios = []
    for servicio in servicios:
        for option in servicios_options:
            if option['value'] == servicio:
                nombres_servicios.append(option['label'])
                break
    
    return html.Div([
        html.P(f"{texto}: Servicios disponibles", style={'margin': '0', 'fontWeight': 'bold'}),
        html.Ul([html.Li(servicio) for servicio in nombres_servicios])
    ])

# Mostrar selector de servicios cuando se seleccione día y turno
@app.callback(
    [Output("selector-servicios-horario", "children"),
     Output("btn-asignar-servicio", "style")],
    [Input("selector-consultorio-horarios", "value"),
     Input("selector-dia", "value"),
     Input("selector-turno", "value"),
     Input("servicios-consultorio-1", "value"),
     Input("servicios-consultorio-2", "value")]
)
def mostrar_selector_servicios(consultorio, dia, turno, servicios_1, servicios_2):
    if not dia or not turno:
        return html.Div(), {'display': 'none'}
    
    if consultorio == 'consultorio-1':
        servicios_disponibles = servicios_1
    else:
        servicios_disponibles = servicios_2
    
    if not servicios_disponibles:
        return html.Div("No hay servicios disponibles para este consultorio", style={'color': 'red'}), {'display': 'none'}
    
    # Crear opciones de servicios
    opciones_servicios = []
    for servicio in servicios_disponibles:
        for option in servicios_options:
            if option['value'] == servicio:
                opciones_servicios.append(option)
                break
    
    return html.Div([
        html.Label("Seleccione el servicio para este horario:", className='fw-bold mb-2'),
        dcc.Dropdown(
            id="selector-servicio-horario",
            options=opciones_servicios,
            placeholder="Seleccione un servicio"
        )
    ]), {'display': 'block'}

# Generar tabla de horarios
@app.callback(
    Output("tabla-horarios-container", "children"),
    [Input("store-horarios-consultorio-1", "data"),
     Input("store-horarios-consultorio-2", "data"),
     Input("selector-consultorio-horarios", "value")]
)
def generar_tabla_horarios(horarios_1, horarios_2, consultorio_seleccionado):
    if consultorio_seleccionado == 'consultorio-1':
        horarios = horarios_1
        titulo = "Consultorio 1"
    else:
        horarios = horarios_2
        titulo = "Consultorio 2"
    
    # Crear datos para la tabla
    datos_tabla = []
    for turno in turnos:
        fila = {'turno': turno}
        for dia in dias_semana:
            clave = f"{dia.lower()}_{turno.lower()}"
            fila[dia.lower()] = horarios.get(clave, "")
        datos_tabla.append(fila)
    
    columnas = [{"name": "Turno", "id": "turno"}] + [
        {"name": dia, "id": dia.lower()} for dia in dias_semana
    ]
    
    return html.Div([
        html.H5(titulo, style={'marginBottom': '10px'}),
        dash_table.DataTable(
            id="tabla-horarios",
            columns=columnas,
            data=datos_tabla,
            style_cell={
                'textAlign': 'center', 
                'fontFamily': 'Montserrat',
                'padding': '8px',
                'minWidth': '80px',
                'height': '40px'
            },
            style_header={
                'backgroundColor': COLOR_PRIMARIO, 
                'color': 'white', 
                'fontWeight': 'bold',
                'textAlign': 'center'
            },
            style_data={
                'backgroundColor': 'white',
                'color': 'black'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgb(248, 248, 248)'
                }
            ]
        )
    ])

# Asignar servicio a horario
@app.callback(
    [Output("store-horarios-consultorio-1", "data", allow_duplicate=True),
     Output("store-horarios-consultorio-2", "data", allow_duplicate=True),
     Output("selector-dia", "value"),
     Output("selector-turno", "value"),
     Output("selector-servicio-horario", "value")],
    [Input("btn-asignar-servicio", "n_clicks")],
    [State("selector-consultorio-horarios", "value"),
     State("selector-dia", "value"),
     State("selector-turno", "value"),
     State("selector-servicio-horario", "value"),
     State("store-horarios-consultorio-1", "data"),
     State("store-horarios-consultorio-2", "data")],
    prevent_initial_call=True
)
def asignar_servicio_horario(n_clicks, consultorio, dia, turno, servicio, horarios_1, horarios_2):
    if not n_clicks or not dia or not turno or not servicio:
        raise PreventUpdate
    
    # Obtener nombre del servicio
    nombre_servicio = ""
    for option in servicios_options:
        if option['value'] == servicio:
            nombre_servicio = option['label']
            break
    
    # Actualizar horarios
    clave = f"{dia}_{turno}"
    
    if consultorio == 'consultorio-1':
        horarios_1 = horarios_1 or {}
        horarios_1[clave] = nombre_servicio
        return horarios_1, horarios_2, None, None, None
    else:
        horarios_2 = horarios_2 or {}
        horarios_2[clave] = nombre_servicio
        return horarios_1, horarios_2, None, None, None

# Notificación al guardar consultorios
@app.callback(
    Output("notification", "children"),
    Input("btn-guardar-consultorios", "n_clicks"),
    prevent_initial_call=True
)
def notificar_guardado_consultorios(n_clicks):
    if n_clicks and n_clicks > 0:
        return dbc.Alert("Información de consultorios guardada correctamente", color="success", style={'marginTop': '20px'})
    raise PreventUpdate

# Notificación al guardar servicios
@app.callback(
    Output("notification", "children", allow_duplicate=True),
    Input("btn-guardar-servicios", "n_clicks"),
    prevent_initial_call=True
)
def notificar_guardado_servicios(n_clicks):
    if n_clicks and n_clicks > 0:
        return dbc.Alert("Servicios guardados correctamente", color="success", style={'marginTop': '20px'})
    raise PreventUpdate

# Guardar toda la información
@app.callback(
    Output("notification", "children", allow_duplicate=True),
    Input("btn-guardar-todo", "n_clicks"),
    prevent_initial_call=True
)
def guardar_informacion(n_clicks):
    if not n_clicks:
        raise PreventUpdate
    
    return dbc.Alert("Información completa guardada correctamente", color="success", style={'marginTop': '20px'})

# Exportar a Excel
@app.callback(
    Output("download-excel", "data"),
    Input("btn-exportar-excel", "n_clicks"),
    [State("store-horarios-consultorio-1", "data"),
     State("store-horarios-consultorio-2", "data")],
    prevent_initial_call=True
)
def exportar_a_excel(n_clicks, horarios_1, horarios_2):
    if not n_clicks:
        raise PreventUpdate
    
    try:
        # Crear DataFrames con los horarios
        datos_exportar = []
        
        for consultorio, horarios in [("Consultorio 1", horarios_1 or {}), ("Consultorio 2", horarios_2 or {})]:
            for clave, servicio in horarios.items():
                dia, turno = clave.split('_')
                datos_exportar.append({
                    'Consultorio': consultorio,
                    'Día': dia.capitalize(),
                    'Turno': turno.capitalize(),
                    'Servicio': servicio
                })
        
        df = pl.DataFrame(datos_exportar)
        
        # Crear archivo Excel en memoria
        output = BytesIO()
        df.write_excel(output)
        output.seek(0)
        
        # Devolver el archivo para descarga
        return dcc.send_bytes(
            output.getvalue(),
            filename=f"horarios_consultorios_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )
    except Exception as e:
        print(f"Error al exportar a Excel: {e}")
        raise PreventUpdate

# Ejecutar la aplicación
if __name__ == '__main__':

    server = app.server
