from flask import Flask, render_template, request, redirect, url_for, flash
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'crudazure')

# Configuración del motor SQLAlchemy para Azure SQL con pyodbc
db_url = "mssql+pyodbc://adminpruebas:Helado123@sql-server-azure-prueba-nube.database.windows.net/sql-prueba-crud?driver=ODBC+Driver+17+for+SQL+Server"

engine = create_engine(db_url, pool_pre_ping=True)

# Inicializar la base de datos (crear tabla si no existe)
def init_db():
    try:
        with engine.begin() as conn:
            conn.execute(text('''
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='datos_cientificos' AND xtype='U')
                CREATE TABLE datos_cientificos (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    nombre NVARCHAR(100) NOT NULL,
                    descripcion NVARCHAR(255),
                    valor FLOAT NOT NULL,
                    unidad NVARCHAR(50),
                    fecha_registro DATETIME DEFAULT GETDATE()
                )
            '''))
    except SQLAlchemyError as e:
        print(f"Error al inicializar la base de datos: {e}")

@app.route('/')
def index():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM datos_cientificos ORDER BY fecha_registro DESC"))
            datos = result.fetchall()
        return render_template('index.html', datos=datos)
    except SQLAlchemyError as e:
        flash(f'Error al cargar datos: {str(e)}', 'danger')
        return render_template('index.html', datos=[])

@app.route('/agregar', methods=['GET', 'POST'])
def agregar():
    if request.method == 'POST':
        try:
            with engine.begin() as conn:
                conn.execute(text('''
                    INSERT INTO datos_cientificos (nombre, descripcion, valor, unidad)
                    VALUES (:nombre, :descripcion, :valor, :unidad)
                '''), {
                    'nombre': request.form['nombre'],
                    'descripcion': request.form['descripcion'],
                    'valor': float(request.form['valor']),
                    'unidad': request.form['unidad']
                })
            flash('Registro agregado correctamente', 'success')
        except SQLAlchemyError as e:
            flash(f'Error al agregar registro: {str(e)}', 'danger')
        return redirect(url_for('index'))
    return render_template('agregar.html')

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    try:
        with engine.connect() as conn:
            result = conn.execute(text('SELECT * FROM datos_cientificos WHERE id = :id'), {'id': id})
            dato = result.fetchone()
        if not dato:
            flash('Registro no encontrado', 'danger')
            return redirect(url_for('index'))

        if request.method == 'POST':
            try:
                with engine.begin() as conn:
                    conn.execute(text('''
                        UPDATE datos_cientificos
                        SET nombre = :nombre, descripcion = :descripcion, valor = :valor, unidad = :unidad
                        WHERE id = :id
                    '''), {
                        'nombre': request.form['nombre'],
                        'descripcion': request.form['descripcion'],
                        'valor': float(request.form['valor']),
                        'unidad': request.form['unidad'],
                        'id': id
                    })
                flash('Registro actualizado correctamente', 'success')
                return redirect(url_for('index'))
            except SQLAlchemyError as e:
                flash(f'Error al actualizar registro: {str(e)}', 'danger')
                return redirect(url_for('index'))

        return render_template('editar.html', dato=dato)

    except SQLAlchemyError as e:
        flash(f'Error al procesar solicitud: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/eliminar/<int:id>', methods=['GET', 'POST'])
def eliminar(id):
    try:
        with engine.connect() as conn:
            result = conn.execute(text('SELECT * FROM datos_cientificos WHERE id = :id'), {'id': id})
            dato = result.fetchone()
        if not dato:
            flash('Registro no encontrado', 'danger')
            return redirect(url_for('index'))

        if request.method == 'POST':
            try:
                with engine.begin() as conn:
                    conn.execute(text('DELETE FROM datos_cientificos WHERE id = :id'), {'id': id})
                flash('Registro eliminado correctamente', 'success')
                return redirect(url_for('index'))
            except SQLAlchemyError as e:
                flash(f'Error al eliminar registro: {str(e)}', 'danger')
                return redirect(url_for('index'))

        return render_template('eliminar.html', dato=dato)

    except SQLAlchemyError as e:
        flash(f'Error al cargar el registro: {str(e)}', 'danger')
        return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=8000)