from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Usado para sesiones
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///estacionamiento.db'  # URI de la base de datos SQLite
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializando la base de datos
db = SQLAlchemy(app)

# Modelo de la base de datos
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class Vehiculo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    placa = db.Column(db.String(10), unique=True, nullable=False)
    fecha_ingreso = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_salida = db.Column(db.DateTime, nullable=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    usuario = db.relationship('Usuario', backref=db.backref('vehiculos', lazy=True))

# Crear la base de datos
with app.app_context():
    db.create_all()

# Rutas para el login
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    usuario = Usuario.query.filter_by(username=username).first()
    
    if usuario and check_password_hash(usuario.password, password):
        session['user_id'] = usuario.id
        return redirect(url_for('dashboard'))
    else:
        flash('Nombre de usuario o contraseña incorrectos')
        return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

# Ruta para el dashboard (espacio para gestionar el estacionamiento)
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    vehiculos = Vehiculo.query.filter_by(usuario_id=session['user_id'], fecha_salida=None).all()
    return render_template('dashboard.html', vehiculos=vehiculos)

# Ruta para agregar vehículos al estacionamiento
@app.route('/agregar_vehiculo', methods=['POST'])
def agregar_vehiculo():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    placa = request.form['placa']
    
    # Verificar si el vehículo ya está estacionado
    vehiculo_existente = Vehiculo.query.filter_by(placa=placa, fecha_salida=None).first()
    
    if vehiculo_existente:
        flash(f'El vehículo con placa {placa} ya está estacionado.')
        return redirect(url_for('dashboard'))

    nuevo_vehiculo = Vehiculo(placa=placa, usuario_id=session['user_id'])
    db.session.add(nuevo_vehiculo)
    db.session.commit()
    
    flash(f'Vehículo con placa {placa} agregado al estacionamiento.')
    return redirect(url_for('dashboard'))

# Ruta para marcar salida de un vehículo
@app.route('/salir_vehiculo/<int:id>', methods=['POST'])
def salir_vehiculo(id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    vehiculo = Vehiculo.query.get_or_404(id)
    if vehiculo.usuario_id != session['user_id']:
        flash('No tienes permiso para realizar esta acción.')
        return redirect(url_for('dashboard'))
    
    # Actualizar la fecha de salida
    vehiculo.fecha_salida = datetime.utcnow()
    db.session.commit()
    
    flash(f'Vehículo con placa {vehiculo.placa} ha salido del estacionamiento.')
    return redirect(url_for('dashboard'))

# Página de registro de usuario
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        
        if Usuario.query.filter_by(username=username).first():
            flash('El nombre de usuario ya existe.')
            return redirect(url_for('registro'))
        
        nuevo_usuario = Usuario(username=username, password=password)
        db.session.add(nuevo_usuario)
        db.session.commit()
        
        flash('Usuario registrado exitosamente. Inicia sesión.')
        return redirect(url_for('index'))
    
    return render_template('registro.html')

# Ruta para editar un vehículo
@app.route('/editar_vehiculo/<int:id>', methods=['GET', 'POST'])
def editar_vehiculo(id):
    if 'user_id' not in session:
        return redirect(url_for('index'))

    vehiculo = Vehiculo.query.get_or_404(id)
    if vehiculo.usuario_id != session['user_id']:
        flash('No tienes permiso para realizar esta acción.')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        nueva_placa = request.form['placa']
        vehiculo.placa = nueva_placa
        db.session.commit()

        flash(f'Vehículo con placa actualizada a {nueva_placa}.')
        return redirect(url_for('dashboard'))

    return render_template('editar_vehiculo.html', vehiculo=vehiculo)

# Ruta para eliminar un vehículo
@app.route('/eliminar_vehiculo/<int:id>', methods=['POST'])
def eliminar_vehiculo(id):
    if 'user_id' not in session:
        return redirect(url_for('index'))

    vehiculo = Vehiculo.query.get_or_404(id)
    if vehiculo.usuario_id != session['user_id']:
        flash('No tienes permiso para realizar esta acción.')
        return redirect(url_for('dashboard'))

    db.session.delete(vehiculo)
    db.session.commit()

    flash(f'Vehículo con placa {vehiculo.placa} eliminado del estacionamiento.')
    return redirect(url_for('dashboard'))

# Bloque para ejecutar la aplicación
if __name__ == '__main__':
    app.run(debug=True)


