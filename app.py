from flask import Flask, render_template, request, redirect, url_for, flash
import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'crudazure')

# Configuración mejorada de conexión a Azure SQL
def get_db_connection():
    try:
        server = "sql-server-azure-prueba-nube.database.windows.net"  # Sin tcp:
        database = "sql-prueba-crud"
        username = "adminpruebas"
        password = "Helado123"
        
        conn_str = (
            "Driver={ODBC Driver 17 for SQL Server};"
            f"Server={server};"  # ¡Importante sin tcp:!
            f"Database={database};"
            f"Uid={username};"
            f"Pwd={password};"
            "Encrypt=yes;"
            "TrustServerCertificate=no;"
            "Connection Timeout=30;"
        )
        return pyodbc.connect(conn_str)
    except pyodbc.Error as e:
        print(f"ERROR DE CONEXIÓN: {str(e)}")
        return None
    
# Función init_db corregida
def init_db():
    conn = None
    try:
        conn = get_db_connection()
        if conn:
            with conn.cursor() as cursor:
                cursor.execute('''
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='datos_cientificos' AND xtype='U')
                CREATE TABLE datos_cientificos (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    nombre NVARCHAR(100) NOT NULL,
                    descripcion NVARCHAR(255),
                    valor FLOAT NOT NULL,
                    unidad NVARCHAR(50),
                    fecha_registro DATETIME DEFAULT GETDATE()
                )
                ''')
                conn.commit()
    except Exception as e:
        print(f"Error al inicializar DB: {str(e)}")
    finally:
        if conn:
            conn.close()

# Rutas con manejo seguro de conexiones
@app.route('/')
def index():
    try:
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cursor:
                    cursor.execute('SELECT * FROM datos_cientificos ORDER BY fecha_registro DESC')
                    datos = cursor.fetchall()
                    return render_template('index.html', datos=datos)
        return render_template('index.html', datos=[])
    except Exception as e:
        flash(f'Error al cargar datos: {str(e)}', 'danger')
        return render_template('index.html', datos=[])

@app.route('/agregar', methods=['GET', 'POST'])
def agregar():
    if request.method == 'POST':
        try:
            with get_db_connection() as conn:
                if conn:
                    with conn.cursor() as cursor:
                        cursor.execute(
                            'INSERT INTO datos_cientificos (nombre, descripcion, valor, unidad) VALUES (?, ?, ?, ?)',
                            (
                                request.form['nombre'],
                                request.form['descripcion'],
                                float(request.form['valor']),
                                request.form['unidad']
                            )
                        )
                        conn.commit()
                        flash('Registro agregado correctamente', 'success')
        except Exception as e:
            flash(f'Error al agregar registro: {str(e)}', 'danger')
        return redirect(url_for('index'))
    
    return render_template('agregar.html')

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    try:
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cursor:
                    if request.method == 'POST':
                        cursor.execute(
                            'UPDATE datos_cientificos SET nombre=?, descripcion=?, valor=?, unidad=? WHERE id=?',
                            (
                                request.form['nombre'],
                                request.form['descripcion'],
                                float(request.form['valor']),
                                request.form['unidad'],
                                id
                            )
                        )
                        conn.commit()
                        flash('Registro actualizado correctamente', 'success')
                        return redirect(url_for('index'))
                    
                    cursor.execute('SELECT * FROM datos_cientificos WHERE id = ?', (id,))
                    dato = cursor.fetchone()
                    if not dato:
                        flash('Registro no encontrado', 'danger')
                        return redirect(url_for('index'))
                    
                    return render_template('editar.html', dato=dato)
    except Exception as e:
        flash(f'Error al procesar solicitud: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/eliminar/<int:id>', methods=['GET', 'POST'])
def eliminar(id):
    try:
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cursor:
                    if request.method == 'POST':
                        cursor.execute('DELETE FROM datos_cientificos WHERE id = ?', (id,))
                        conn.commit()
                        flash('Registro eliminado correctamente', 'success')
                        return redirect(url_for('index'))
                    
                    cursor.execute('SELECT * FROM datos_cientificos WHERE id = ?', (id,))
                    dato = cursor.fetchone()
                    if not dato:
                        flash('Registro no encontrado', 'danger')
                        return redirect(url_for('index'))
                    
                    return render_template('eliminar.html', dato=dato)
    except Exception as e:
        flash(f'Error al eliminar registro: {str(e)}', 'danger')
        return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=8000)