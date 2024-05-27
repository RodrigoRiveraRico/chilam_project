from flask import Flask, render_template, request, jsonify
from Var_Clss_Construction import dict_construction, df_construction
from tree_variables_from_db import creacion_ramas_arbol
import conteos
from config import fuente_de_datos_metadatos

app = Flask(__name__)

data_bases = []
for db_name in fuente_de_datos_metadatos:
    data_bases.append(db_name)
print("Bases de datos disponibles: {}".format(data_bases))

selected_names = []


# 1.- =============== Página principal (Seleccionar DBs) ----------
@app.route('/')
def index():
    return render_template('index.html', selected_names=selected_names, suggestions=data_bases)

@app.route('/add_name', methods=['POST'])
def add_name():
    name = request.form.get('name')
    if name and name not in selected_names:
        selected_names.append(name)
    return jsonify(selected_names=selected_names)


# 2.- =============== Seleccionar resoluciones compatibles de las DBs -------
@app.route('/res_db', methods=['POST'])
def res_db():
    Dict_res = {}

    # for i in selected_names:
    #     # Obtenemos las variables de cada DB seleccionada y las agregamos a un diccionario.
    #     L_v = pruebasPostgres.recolectar_variables(i)
    #     Dict_res[i] = L_v
    # print(selected_names)
    return render_template('resDB.html', Dict_res = Dict_res)


### pendiente .. 








# 3.- =============== Seleccionar los conjuntos de covariables y la clase (Árbol) -------
@app.route('/tree_data')
def get_tree_data():
    tree_data = [{"id": DB,
                 "text": DB, 
                 "children": creacion_ramas_arbol(DB)} for DB in selected_names]
    return jsonify(tree_data)

@app.route('/process', methods=['POST'])
def process():
    return render_template('arbol.html')


# 4.- =============== Desplegar las tablas con los cáclulos de Score y epsilon (pág. final) -------
@app.route('/select_variables', methods=['POST'])
def select_variables():
    selected_values1 = request.form['selectedVariables1']   # Covariables
    selected_values2 = request.form['selectedVariables2']   # Clase

    list_db_var = selected_values1.split('\r\n')
    list_db_clss = selected_values2.split('\r\n')

#### Construcción árbol (dict) de variables ####

    dict_db_variables = dict_construction(list_db_var)
#### ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ####

#### Construcción árbol (dict) de clase ####

    dict_db_class = dict_construction(list_db_clss)
#### ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ####

#### Construcción DataFrame de variables y clase ####

    df_all_variables_data = df_construction(dict_db_variables, 'Covariable')
    df_all_class_data = df_construction(dict_db_class, 'clase')

    # Extraemos el nombre de la clase
    nombre_clase = df_all_class_data.iloc[0, 0]
#### ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ####

#### Contamos el número de celdas de variables y clase ####
    # Las siguientes líneas modifican la tabla original df_all_variables_data
    conteos.df_count_cells(df_all_variables_data, df_all_class_data)
    conteos.epsilon(df_all_variables_data)
    conteos.score(df_all_variables_data)

    # Creamos un nuevo DataFrame con las celdas desanidadas.
    df_all_cells_data = df_all_variables_data.explode('celdas')

    # Cambiamos el nombre de la columna 'celdas' por 'celda' para indicar que cada registro corresponde a una única celda.
    df_all_cells_data = df_all_cells_data.rename(columns={'celdas':'celda'})

    # Definimos las funciones de agregación para cada columna
    # Utilizamos '<br>' para generar el salto de línea en HTML
    aggregations = {
        'Covariable': '<br>'.join,
        'epsilon': 'sum',
        'score': 'sum'
        }
    # Aplicamos groupby con agg
    df_all_cells_data = df_all_cells_data.groupby('celda').agg(aggregations).reset_index()

    # Renombramos la columna 'Covariable' por 'Covariables' para indicar que cada registro corresponde a una o varias covariables.
    df_all_cells_data = df_all_cells_data.rename(columns={'Covariable':'Covariables'})

    return render_template('resDf.html', 
                           df_resultado = df_all_variables_data.drop(['celdas'],axis=1).to_html(), 
                           df_resultado2 = df_all_cells_data.to_html(escape=False),
                           nombre_titulo = nombre_clase)

if __name__ == '__main__':
    app.run(debug=True)