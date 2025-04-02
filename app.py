from flask import Flask, render_template, request, redirect, url_for, flash
import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')
conn = None

# Configuración de conexión a Azure SQL
def get_db_connection():
    server = os.getenv('sql-server-azure-prueba-nube.database.windows.net')
    database = os.getenv('sql-prueba-crud')
    username = os.getenv('adminpruebas')
    password = os.getenv('Helado123')
    driver = '{ODBC Driver 17 for SQL Server}'
    
    conn = pyodbc.connect(
        f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}'
    )
    return conn

# Crear tabla si no existe
def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
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
        print(f"Error al inicializar DB: {e}")
    finally:
        conn.close()

# Rutas de la aplicación
@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM datos_cientificos ORDER BY fecha_registro DESC')
    datos = cursor.fetchall()
    conn.close()
    return render_template('index.html', datos=datos)

@app.route('/agregar', methods=['GET', 'POST'])
def agregar():
    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        valor = float(request.form['valor'])
        unidad = request.form['unidad']
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO datos_cientificos (nombre, descripcion, valor, unidad) VALUES (?, ?, ?, ?)',
                (nombre, descripcion, valor, unidad)
            )
            conn.commit()
            flash('Registro agregado correctamente', 'success')
        except Exception as e:
            flash(f'Error al agregar registro: {str(e)}', 'danger')
        finally:
            conn.close()
        return redirect(url_for('index'))
    
    return render_template('agregar.html')

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        valor = float(request.form['valor'])
        unidad = request.form['unidad']
        
        try:
            cursor.execute(
                'UPDATE datos_cientificos SET nombre=?, descripcion=?, valor=?, unidad=? WHERE id=?',
                (nombre, descripcion, valor, unidad, id)
            )
            conn.commit()
            flash('Registro actualizado correctamente', 'success')
        except Exception as e:
            flash(f'Error al actualizar registro: {str(e)}', 'danger')
        finally:
            conn.close()
        return redirect(url_for('index'))
    
    cursor.execute('SELECT * FROM datos_cientificos WHERE id = ?', (id,))
    dato = cursor.fetchone()
    conn.close()
    
    if dato is None:
        flash('Registro no encontrado', 'danger')
        return redirect(url_for('index'))
    
    return render_template('editar.html', dato=dato)

@app.route('/eliminar/<int:id>', methods=['GET', 'POST'])
def eliminar(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        try:
            cursor.execute('DELETE FROM datos_cientificos WHERE id = ?', (id,))
            conn.commit()
            flash('Registro eliminado correctamente', 'success')
        except Exception as e:
            flash(f'Error al eliminar registro: {str(e)}', 'danger')
        finally:
            conn.close()
        return redirect(url_for('index'))
    
    cursor.execute('SELECT * FROM datos_cientificos WHERE id = ?', (id,))
    dato = cursor.fetchone()
    conn.close()
    
    if dato is None:
        flash('Registro no encontrado', 'danger')
        return redirect(url_for('index'))
    
    return render_template('eliminar.html', dato=dato)

if __name__ == '__main__':
    init_db()
    app.run()