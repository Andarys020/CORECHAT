import os
import json
import sqlite3
import datetime
import re
<<<<<<< HEAD
import hashlib
from typing import Optional, Dict, Any, List, Tuple
=======
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
from flask import Flask, render_template_string, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room

# Intentar importar psycopg2 para soporte PostgreSQL online
try:
    import psycopg2
    from psycopg2 import extras
    HAS_POSTGRES = True
except ImportError:
    HAS_POSTGRES = False

app = Flask(__name__)
<<<<<<< HEAD
app.config['SECRET_KEY'] = os.urandom(24).hex()
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB

# === CONFIGURACIÓN PARA HUGGING FACE ===
=======
app.config['SECRET_KEY'] = 'secreto123!'

# ✅ Aumentar límite de tamaño de solicitud
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB

# === CONFIGURACIÓN PARA HUGGING FACE ===
# En Hugging Face Spaces, usamos gevent con el worker adecuado
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='gevent',
    logger=False,
    engineio_logger=False,
    ping_timeout=60,
    ping_interval=25,
    transports=['websocket', 'polling'],
    allow_upgrades=True,
    always_connect=True,
    max_http_buffer_size=10 * 1024 * 1024
)

<<<<<<< HEAD
# Variable global en memoria
admin_visible: bool = False
usuarios_conectados: Dict[str, Dict[str, Any]] = {}

# FILE CONFIG PARA GUARDAR PARAMETROS ONLINE
CONFIG_FILE: str = "db_config.json"

def cargar_config_db() -> Dict[str, str]:
=======
# Variable global en memoria para controlar si el admin decide hacerse visible
admin_visible = False
usuarios_conectados = {}

# FILE CONFIG PARA GUARDAR PARAMETROS ONLINE
CONFIG_FILE = "db_config.json"

def cargar_config_db():
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {
        "motor": "sqlite",
        "host": "",
        "database": "",
        "user": "",
        "password": "",
        "port": "5432"
    }

<<<<<<< HEAD
def guardar_config_db(config: Dict[str, str]) -> None:
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

db_config: Dict[str, str] = cargar_config_db()

# ==========================================
# GESTOR DE CONEXIONES HÍBRIDO
=======
def guardar_config_db(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

# Cargar configuración inicial
db_config = cargar_config_db()

# ==========================================
# GESTOR DE CONEXIONES HÍBRIDO (SQLITE / POSTGRES)
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
# ==========================================
def obtener_conexion():
    if db_config["motor"] == "postgres":
        if not HAS_POSTGRES:
            raise RuntimeError("Librería 'psycopg2' no instalada.")
        return psycopg2.connect(
            host=db_config["host"],
            database=db_config["database"],
            user=db_config["user"],
            password=db_config["password"],
            port=db_config["port"]
        )
    else:
        return sqlite3.connect("chat_app.db")

<<<<<<< HEAD
def db_query(query: str, params: tuple = (), fetchall: bool = False, commit: bool = False):
=======
def db_query(query, params=(), fetchall=False, commit=False):
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
    es_postgres = (db_config["motor"] == "postgres")
    if es_postgres:
        query = query.replace("?", "%s")
        
    conn = obtener_conexion()
    cursor = conn.cursor()
    res = None
    try:
        cursor.execute(query, params)
        if commit:
            conn.commit()
        if fetchall:
            res = cursor.fetchall()
        else:
            if cursor.description:
                res = cursor.fetchone()
    except Exception as e:
        print(f"[ERROR SQL]: {e}")
        if commit:
            conn.rollback()
    finally:
        conn.close()
    return res

# ==========================================
<<<<<<< HEAD
# FUNCIONES DE SEGURIDAD
# ==========================================
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

# ==========================================
# BASE DE DATOS E INICIALIZACIÓN
# ==========================================
def init_db() -> None:
=======
# BASE DE DATOS E INICIALIZACIÓN
# ==========================================
def init_db():
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
    try:
        es_postgres = (db_config["motor"] == "postgres")
        pk_type = "SERIAL PRIMARY KEY" if es_postgres else "INTEGER PRIMARY KEY AUTOINCREMENT"
        
        db_query(f"""
            CREATE TABLE IF NOT EXISTS usuarios (
                id {pk_type},
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                rol TEXT NOT NULL DEFAULT 'user',
                estado TEXT NOT NULL DEFAULT 'activo',
                genero TEXT NOT NULL DEFAULT 'hombre',
                avatar TEXT DEFAULT '',
                ban_expira TEXT,
                mute_expira TEXT
            )
        """, commit=True)
        
        db_query(f"""
            CREATE TABLE IF NOT EXISTS stickers (
                id {pk_type},
                nombre TEXT NOT NULL,
                url TEXT NOT NULL,
                tipo TEXT NOT NULL DEFAULT 'sticker'
            )
        """, commit=True)
        
        db_query(f"""
            CREATE TABLE IF NOT EXISTS salas (
                id {pk_type},
                nombre TEXT NOT NULL UNIQUE,
                icono TEXT NOT NULL DEFAULT '💬',
                limite INTEGER NOT NULL DEFAULT 150
            )
        """, commit=True)
        
        db_query(f"""
            CREATE TABLE IF NOT EXISTS bloqueos_salas (
                id {pk_type},
                username TEXT NOT NULL,
                sala TEXT NOT NULL,
                expira TEXT NOT NULL
            )
        """, commit=True)
        
<<<<<<< HEAD
=======
        # Verificar y agregar columnas faltantes
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
        if not es_postgres:
            check = db_query("PRAGMA table_info(usuarios)", fetchall=True)
            columnas_existentes = [row[1] for row in check] if check else []
            
            columnas_para_agregar = [
                ("genero", "TEXT NOT NULL DEFAULT 'hombre'"),
                ("avatar", "TEXT DEFAULT ''"),
                ("ban_expira", "TEXT"),
                ("mute_expira", "TEXT")
            ]
            
            for col, tipo in columnas_para_agregar:
                if col not in columnas_existentes:
                    try:
                        db_query(f"ALTER TABLE usuarios ADD COLUMN {col} {tipo}", commit=True)
                        print(f"-> Columna '{col}' agregada a la tabla usuarios.")
                    except Exception as e:
                        print(f"-> Error agregando columna '{col}': {e}")
        
<<<<<<< HEAD
=======
        # Crear sala por defecto
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
        res_salas = db_query("SELECT COUNT(*) FROM salas", fetchall=False)
        if res_salas and res_salas[0] == 0:
            db_query("INSERT INTO salas (nombre, icono, limite) VALUES (?, ?, ?)", 
                    ("Sala General", "🌍", 150), commit=True)
            print("-> Sala por defecto 'Sala General' creada.")

<<<<<<< HEAD
        res_admin = db_query("SELECT id FROM usuarios WHERE username = 'Administrador'", fetchall=False)
        if not res_admin:
            admin_hash = hash_password("1234")
            db_query("INSERT INTO usuarios (username, password, rol, estado, genero, avatar) VALUES (?, ?, ?, ?, ?, ?)", 
                     ("Administrador", admin_hash, "admin", "activo", "hombre", ""), commit=True)
            print("-> Cuenta 'Administrador' creada.")
        
        print(f"-> Base de datos inicializada en modo [{db_config['motor'].upper()}] con Python 3.14")
=======
        # Crear administrador por defecto
        res_admin = db_query("SELECT id FROM usuarios WHERE username = 'Administrador'", fetchall=False)
        if not res_admin:
            db_query("INSERT INTO usuarios (username, password, rol, estado, genero, avatar) VALUES (?, ?, ?, ?, ?, ?)", 
                     ("Administrador", "1234", "admin", "activo", "hombre", ""), commit=True)
            print("-> Cuenta 'Administrador' creada.")
        
        print(f"-> Base de datos inicializada en modo [{db_config['motor'].upper()}]")
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
    except Exception as e:
        print(f"[ERROR INIT DB]: {e}")

init_db()

# ==========================================
# FUNCIONES AUXILIARES
# ==========================================
<<<<<<< HEAD
def verificar_y_limpiar_sanciones(username: str) -> None:
=======
def verificar_y_limpiar_sanciones(username):
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
    res = db_query("SELECT estado, ban_expira, mute_expira FROM usuarios WHERE username=?", (username,))
    if not res:
        return
    estado, ban_expira, mute_expira = res
    ahora = datetime.datetime.now()

    if estado == 'ban' and ban_expira:
        try:
            dt_exp = datetime.datetime.fromisoformat(ban_expira)
            if ahora > dt_exp:
                db_query("UPDATE usuarios SET estado='activo', ban_expira=NULL WHERE username=?", (username,), commit=True)
<<<<<<< HEAD
        except (ValueError, TypeError) as e:
            print(f"Error al parsear ban_expira para {username}: {e}")
=======
        except:
            pass
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939

    if estado == 'silenciado' and mute_expira:
        try:
            dt_exp = datetime.datetime.fromisoformat(mute_expira)
            if ahora > dt_exp:
                db_query("UPDATE usuarios SET estado='activo', mute_expira=NULL WHERE username=?", (username,), commit=True)
<<<<<<< HEAD
        except (ValueError, TypeError) as e:
            print(f"Error al parsear mute_expira para {username}: {e}")

def calcular_fecha_expiracion(minutos_str: str) -> Optional[str]:
    if minutos_str == "perm":
        return None
    try:
        mins = int(minutos_str)
        return (datetime.datetime.now() + datetime.timedelta(minutes=mins)).isoformat()
    except ValueError:
        return None

def validar_url_imagen(url: str) -> bool:
=======
        except:
            pass

def calcular_fecha_expiracion(minutos_str):
    if minutos_str == "perm":
        return None
    mins = int(minutos_str)
    return (datetime.datetime.now() + datetime.timedelta(minutes=mins)).isoformat()

# ✅ Función para validar URL de imagen
def validar_url_imagen(url):
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
    if not url:
        return False
    patron = r'^(https?:\/\/.*\.(?:png|jpg|jpeg|gif|bmp|webp|svg))(?:\?.*)?$'
    return re.match(patron, url, re.IGNORECASE) is not None

# ==========================================
<<<<<<< HEAD
# ENDPOINTS HTTP Y API REST
=======
# 2. ENDPOINTS HTTP Y API REST
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
# ==========================================
@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    user = data.get("username", "").strip()
    passw = data.get("password", "").strip()
    
    verificar_y_limpiar_sanciones(user)
    
<<<<<<< HEAD
    res = db_query("SELECT username, rol, estado, genero, avatar, password FROM usuarios WHERE username=?", (user,))
    if not res:
        return jsonify({"success": False, "message": "Usuario no existe."})
    
    username, rol, estado, genero, avatar, hashed_pass = res
    if not verify_password(passw, hashed_pass):
        return jsonify({"success": False, "message": "Contraseña incorrecta."})
    
=======
    res = db_query("SELECT username, rol, estado, genero, avatar FROM usuarios WHERE username=? AND password=?", (user, passw))
    if not res:
        return jsonify({"success": False, "message": "Usuario o contraseña incorrectos."})
    
    username, rol, estado, genero, avatar = res
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
    if estado == 'ban':
        return jsonify({"success": False, "message": "Tu cuenta se encuentra baneada."})
        
    return jsonify({"success": True, "username": username, "rol": rol, "estado": estado, "genero": genero, "avatar": avatar})

@app.route('/api/registro', methods=['POST'])
def api_registro():
    data = request.json
    user = data.get("username", "").strip()
    passw = data.get("password", "").strip()
    gender = data.get("genero", "hombre")
    
    if not user or not passw:
        return jsonify({"success": False, "message": "Campos incompletos."})
<<<<<<< HEAD
    
    if len(passw) < 4:
        return jsonify({"success": False, "message": "La contraseña debe tener al menos 4 caracteres."})
=======
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
        
    res = db_query("SELECT id FROM usuarios WHERE username=?", (user,))
    if res:
        return jsonify({"success": False, "message": "El nombre de usuario ya existe."})
<<<<<<< HEAD
    
    hashed = hash_password(passw)
    db_query("INSERT INTO usuarios (username, password, rol, estado, genero, avatar) VALUES (?, ?, 'user', 'activo', ?, '')", 
             (user, hashed, gender), commit=True)
=======
        
    db_query("INSERT INTO usuarios (username, password, rol, estado, genero, avatar) VALUES (?, ?, 'user', 'activo', ?, '')", 
             (user, passw, gender), commit=True)
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
    return jsonify({"success": True})

@app.route('/api/usuario/actualizar_avatar', methods=['POST'])
def api_actualizar_avatar():
    data = request.json
    user = data.get("username", "").strip()
    avatar = data.get("avatar", "")
    
    if avatar and not validar_url_imagen(avatar):
        return jsonify({"success": False, "message": "La URL debe ser una imagen válida (png, jpg, jpeg, gif, bmp, webp, svg)."})
    
    if len(avatar) > 500:
        return jsonify({"success": False, "message": "La URL es demasiado larga (máximo 500 caracteres)."})
    
    db_query("UPDATE usuarios SET avatar=? WHERE username=?", (avatar, user), commit=True)
    return jsonify({"success": True})

@app.route('/api/salas/list', methods=['GET'])
def api_salas_list():
    rows = db_query("SELECT id, nombre, icono, limite FROM salas ORDER BY id ASC", fetchall=True)
    lista = []
    if rows:
        for r in rows:
            conteo_en_sala = 0
            for u in usuarios_conectados.values():
                if u.get("sala_actual") == r[1]:
                    if u.get("username") == "Administrador" and not admin_visible:
                        continue
                    conteo_en_sala += 1

            lista.append({
                "id": r[0],
                "nombre": r[1],
                "icono": r[2],
                "limite": r[3],
                "conectados": conteo_en_sala
            })
    return jsonify(lista)

@app.route('/api/admin/crear_sala', methods=['POST'])
def api_admin_crear_sala():
    data = request.json
    nombre = data.get("nombre", "").strip()
    icono = data.get("icono", "").strip() or "💬"
    try: 
        limite = int(data.get("limite", 150))
    except: 
        limite = 150
        
    if not nombre:
        return jsonify({"success": False, "message": "El nombre de la sala es obligatorio."})
    if limite > 150:
        return jsonify({"success": False, "message": "El límite máximo permitido es de 150 usuarios."})
        
    if db_query("SELECT id FROM salas WHERE nombre=?", (nombre,)):
        return jsonify({"success": False, "message": "Ya existe una sala con ese nombre."})
        
    db_query("INSERT INTO salas (nombre, icono, limite) VALUES (?, ?, ?)", (nombre, icono, limite), commit=True)
    return jsonify({"success": True})

@app.route('/api/admin/eliminar_sala', methods=['POST'])
def api_admin_eliminar_sala():
    data = request.json
    sala_id = data.get("id")
    res = db_query("SELECT nombre FROM salas WHERE id=?", (sala_id,))
    if res:
        nombre_sala = res[0]
        db_query("DELETE FROM salas WHERE id=?", (sala_id,), commit=True)
        socketio.emit('sala_eliminada_force', {"sala": nombre_sala}, broadcast=True)
    return jsonify({"success": True})

<<<<<<< HEAD
=======
# --- ENDPOINTS EXCLUSIVOS DE ADMINISTRACIÓN ---
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
@app.route('/api/admin/users', methods=['GET'])
def api_admin_users():
    rows = db_query("SELECT id, username, password, rol, estado, genero FROM usuarios ORDER BY id DESC", fetchall=True)
    online_usernames = [info["username"] for info in usuarios_conectados.values()]
    
    usuarios = []
    if rows:
        for r in rows:
            uname = r[1]
            verificar_y_limpiar_sanciones(uname)
            res_releer = db_query("SELECT estado FROM usuarios WHERE id=?", (r[0],))
            est_db = res_releer[0] if res_releer else 'activo'
            
            if est_db == 'ban': 
                status_visual = 'baneado'
            elif uname in online_usernames: 
                status_visual = 'conectado'
            else: 
                status_visual = 'desconectado'
                
            usuarios.append({
                "id": r[0],
                "username": uname,
                "password": r[2],
                "rol": r[3],
                "estado": est_db,
                "status_visual": status_visual,
                "genero": r[5] if len(r) > 5 else 'hombre'
            })
    
    admin_room = None
    for u in usuarios_conectados.values():
        if u.get("username") == "Administrador":
            admin_room = u.get("sala_actual")
            break

    return jsonify({"usuarios": usuarios, "admin_visible": admin_visible, "admin_room": admin_room})

@app.route('/api/admin/toggle_visibilidad', methods=['POST'])
def api_admin_toggle_visibilidad():
    global admin_visible
    admin_visible = not admin_visible
    broadcast_user_list_all_rooms()
    return jsonify({"success": True, "admin_visible": admin_visible})

@app.route('/api/admin/crear_usuario', methods=['POST'])
def api_admin_crear_usuario():
    data = request.json
    user = data.get("username", "").strip()
    passw = data.get("password", "").strip()
    gender = data.get("genero", "hombre")
    rol = data.get("rol", "user")
    
    if not user or not passw:
        return jsonify({"success": False, "message": "Campos incompletos."})
        
    if db_query("SELECT id FROM usuarios WHERE username=?", (user,)):
        return jsonify({"success": False, "message": "El usuario ya existe."})
<<<<<<< HEAD
    
    hashed = hash_password(passw)
    db_query("INSERT INTO usuarios (username, password, rol, estado, genero, avatar) VALUES (?, ?, ?, 'activo', ?, '')", 
             (user, hashed, rol, gender), commit=True)
=======
        
    db_query("INSERT INTO usuarios (username, password, rol, estado, genero, avatar) VALUES (?, ?, ?, 'activo', ?, '')", 
             (user, passw, rol, gender), commit=True)
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
    return jsonify({"success": True})

@app.route('/api/admin/modificar_usuario_completo', methods=['POST'])
def api_admin_modificar_usuario_completo():
    data = request.json
    user_id = data.get("id")
    nuevo_nick = data.get("username", "").strip()
    nueva_pass = data.get("password", "").strip()
    nuevo_rol = data.get("rol", "user")
    
    antiguo_res = db_query("SELECT username FROM usuarios WHERE id=?", (user_id,))
    if not antiguo_res:
        return jsonify({"success": False, "message": "Usuario no encontrado."})
    antiguo_nick = antiguo_res[0]

    if antiguo_nick == "Administrador" and nuevo_nick != "Administrador":
        return jsonify({"success": False, "message": "No se permite renombrar la cuenta raíz 'Administrador'"})

    if antiguo_nick != nuevo_nick:
        if db_query("SELECT id FROM usuarios WHERE username=?", (nuevo_nick,)):
            return jsonify({"success": False, "message": "El nuevo nombre de usuario ya está en uso."})

<<<<<<< HEAD
    hashed = hash_password(nueva_pass)
    db_query("UPDATE usuarios SET username=?, password=?, rol=? WHERE id=?", 
            (nuevo_nick, hashed, nuevo_rol, user_id), commit=True)
=======
    db_query("UPDATE usuarios SET username=?, password=?, rol=? WHERE id=?", 
            (nuevo_nick, nueva_pass, nuevo_rol, user_id), commit=True)
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
    socketio.emit('force_action', {"target": antiguo_nick, "accion": "rol_change", "nuevo_rol": nuevo_rol}, broadcast=True)
    broadcast_user_list_all_rooms()
    return jsonify({"success": True})

@app.route('/api/admin/cambiar_estado', methods=['POST'])
def api_admin_cambiar_estado():
    data = request.json
    user = data.get("username")
    accion = data.get("accion") 
    tiempo = data.get("tiempo") 
    sala_admin = data.get("sala_admin") 
    
    expiracion = calcular_fecha_expiracion(tiempo)
    
    if accion == "silenciar":
        db_query("UPDATE usuarios SET estado='silenciado', mute_expira=? WHERE username=?", (expiracion, user), commit=True)
        socketio.emit('force_action', {"target": user, "accion": "silenciar"}, broadcast=True)
    elif accion == "ban":
        db_query("UPDATE usuarios SET estado='ban', ban_expira=? WHERE username=?", (expiracion, user), commit=True)
        socketio.emit('force_action', {"target": user, "accion": "ban"}, broadcast=True)
    elif accion == "patear_sala":
        if not sala_admin:
            return jsonify({"success": False, "message": "El administrador no está posicionado en ninguna sala."})
        db_query("INSERT INTO bloqueos_salas (username, sala, expira) VALUES (?, ?, ?)", 
                (user, sala_admin, expiracion if expiracion else "perm"), commit=True)
        socketio.emit('force_action', {"target": user, "accion": "kick_sala", "sala": sala_admin}, broadcast=True)
        
    return jsonify({"success": True})

@app.route('/api/admin/eliminar_usuario', methods=['POST'])
def api_admin_eliminar_usuario():
    data = request.json
    user = data.get("username")
    if user == "Administrador":
        return jsonify({"success": False, "message": "No se puede eliminar la cuenta raíz"})
    db_query("DELETE FROM usuarios WHERE username=?", (user,), commit=True)
    return jsonify({"success": True})

@app.route('/api/stickers/list', methods=['GET'])
def api_stickers_list():
    rows = db_query("SELECT id, nombre, url, tipo FROM stickers ORDER BY id DESC", fetchall=True)
    lista = []
    if rows:
        lista = [{"id": r[0], "nombre": r[1], "url": r[2], "tipo": r[3]} for r in rows]
    return jsonify(lista)

@app.route('/api/admin/crear_sticker', methods=['POST'])
def api_admin_crear_sticker():
    data = request.json
    nom = data.get("nombre")
    url = data.get("url")
    tipo = data.get("tipo", "sticker")
    if not nom or not url:
        return jsonify({"success": False, "message": "Nombre y URL son obligatorios"})
    db_query("INSERT INTO stickers (nombre, url, tipo) VALUES (?, ?, ?)", (nom, url, tipo), commit=True)
    return jsonify({"success": True})

@app.route('/api/admin/eliminar_sticker', methods=['POST'])
def api_admin_eliminar_sticker():
    data = request.json
    sid = data.get("id")
    db_query("DELETE FROM stickers WHERE id=?", (sid,), commit=True)
    return jsonify({"success": True})

<<<<<<< HEAD
=======
# --- ENDPOINTS DE CONFIGURACIÓN DE CONEXIÓN ---
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
@app.route('/api/admin/get_db_config', methods=['GET'])
def api_get_db_config():
    cfg = db_config.copy()
    cfg["password"] = "********" if cfg["password"] else ""
    cfg["has_pg_library"] = HAS_POSTGRES
    return jsonify(cfg)

@app.route('/api/admin/save_db_config', methods=['POST'])
def api_save_db_config():
    global db_config
    data = request.json
    nuevo_motor = data.get("motor", "sqlite")
    
    if nuevo_motor == "postgres" and not HAS_POSTGRES:
        return jsonify({"success": False, "message": "No se puede activar Postgres porque la librería 'psycopg2-binary' no está instalada en el servidor."})
        
    pass_ingresado = data.get("password", "")
    if pass_ingresado == "********":
        pass_ingresado = db_config["password"]
        
    db_config = {
        "motor": nuevo_motor,
        "host": data.get("host", "").strip(),
        "database": data.get("database", "").strip(),
        "user": data.get("user", "").strip(),
        "password": pass_ingresado,
        "port": data.get("port", "5432").strip()
    }
    
    try:
        conn = obtener_conexion()
        conn.close()
    except Exception as e:
        db_config["motor"] = "sqlite"
        return jsonify({"success": False, "message": f"Falló la conexión al servidor remoto: {e}. Se revirtió a SQLite Local."})
        
    guardar_config_db(db_config)
    init_db()
    return jsonify({"success": True})

# ==========================================
<<<<<<< HEAD
# LÓGICA DE WEBSOCKETS (SOCKET.IO)
=======
# 3. LÓGICA DE WEBSOCKETS (SOCKET.IO)
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
# ==========================================
@socketio.on('join_chat')
def handle_join(data):
    username = data.get('username')
    if not username: 
        return
    
    verificar_y_limpiar_sanciones(username)
    res = db_query("SELECT rol, genero, avatar, estado FROM usuarios WHERE username=?", (username,))
    if res:
        rol, genero, avatar, estado = res
        if estado == 'ban': 
            return
        
        usuarios_conectados[request.sid] = {
            "username": username,
            "rol": rol,
            "genero": genero,
            "avatar": avatar or "",
            "sala_actual": None
        }
        broadcast_user_list_all_rooms()

@socketio.on('cambiar_sala')
def handle_cambiar_sala(data):
    if request.sid not in usuarios_conectados: 
        return
    user_info = usuarios_conectados[request.sid]
    username = user_info["username"]
    
    sala_vieja = user_info["sala_actual"]
    sala_nueva = data.get("sala")
    
    bloqueos = db_query("SELECT id, expira FROM bloqueos_salas WHERE username=? AND sala=?", (username, sala_nueva), fetchall=True)
    if bloqueos:
        ahora = datetime.datetime.now()
        for b_id, b_exp in bloqueos:
            if b_exp == "perm":
                emit('error_sala_llena', {"message": f"Fuiste pateado permanentemente de la sala '{sala_nueva}'."})
                return
            else:
                try:
                    dt_exp = datetime.datetime.fromisoformat(b_exp)
                    if ahora < dt_exp:
                        emit('error_sala_llena', {"message": f"Fuiste pateado de esta sala. Expira: {dt_exp.strftime('%H:%M:%S')}"})
                        return
                    else:
                        db_query("DELETE FROM bloqueos_salas WHERE id=?", (b_id,), commit=True)
<<<<<<< HEAD
                except (ValueError, TypeError) as e:
                    print(f"Error al parsear expira para bloqueo {b_id}: {e}")
                    db_query("DELETE FROM bloqueos_salas WHERE id=?", (b_id,), commit=True)
=======
                except: 
                    pass
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
    
    res_sala = db_query("SELECT limite FROM salas WHERE nombre=?", (sala_nueva,))
    if not res_sala:
        emit('sys_msg', {"texto": "La sala solicitada ya no existe."})
        return
        
    limite_max = res_sala[0]
    conteo_actual = 0
    for u in usuarios_conectados.values():
        if u.get("sala_actual") == sala_nueva:
            if u.get("username") == "Administrador" and not admin_visible: 
                continue
            conteo_actual += 1
    
    if conteo_actual >= limite_max:
        emit('error_sala_llena', {"message": f"La sala '{sala_nueva}' está llena (Máximo {limite_max} usuarios)."})
        return

    if sala_vieja:
        leave_room(sala_vieja)
        if not (username == "Administrador" and not admin_visible):
            emit('sys_msg', {"texto": f"« {username} salió de la sala."}, to=sala_vieja)
            
    user_info["sala_actual"] = sala_nueva
    join_room(sala_nueva)
    
    if not (username == "Administrador" and not admin_visible):
        emit('sys_msg', {"texto": f"» {username} ingresó a la sala: {sala_nueva}."}, to=sala_nueva)
        
    emit('cambiar_sala_ok', {"sala": sala_nueva})
    broadcast_user_list_all_rooms()

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in usuarios_conectados:
        user_info = usuarios_conectados[request.sid]
        username = user_info["username"]
        sala_actual = user_info["sala_actual"]
        del usuarios_conectados[request.sid]
        
        if sala_actual:
            if not (username == "Administrador" and not admin_visible):
                emit('sys_msg', {"texto": f"« {username} salió del chat."}, to=sala_actual)
        broadcast_user_list_all_rooms()

@socketio.on('send_msg')
def handle_msg(data):
    if request.sid not in usuarios_conectados: 
        return
    user_info = usuarios_conectados[request.sid]
    username = user_info["username"]
    sala_destino = user_info["sala_actual"]
    if not sala_destino: 
        return
    
    verificar_y_limpiar_sanciones(username)
    res = db_query("SELECT estado, rol FROM usuarios WHERE username=?", (username,))
    if res and res[0] == 'silenciado':
        emit('sys_msg', {"texto": "No podés enviar mensajes, estás silenciado."})
        return
        
    rol_actual = res[1] if res else user_info["rol"]
    
    payload = {
        "sender": username,
        "rol": rol_actual,
        "texto": data.get("texto"),
        "is_img": data.get("is_img", False),
        "genero": data.get("genero", "hombre"),
        "avatar": data.get("avatar", ""),
        "msg_color": data.get("msg_color", "white"),
        "msg_font": data.get("msg_font", "Arial"),
        "msg_size": data.get("msg_size", "14px"),
        "nick_color": data.get("nick_color", "default"),
        "nick_font": data.get("nick_font", "Arial"),
        "nick_size": data.get("nick_size", "15px")
    }
    emit('receive_msg', payload, to=sala_destino)

@socketio.on('send_private_msg')
def handle_private_msg(data):
    if request.sid not in usuarios_conectados: 
        return
    sender = usuarios_conectados[request.sid]["username"]
    target = data.get("target")
    texto = data.get("texto")
    
    verificar_y_limpiar_sanciones(sender)
    res = db_query("SELECT estado FROM usuarios WHERE username=?", (sender,))
    if res and res[0] == 'silenciado': 
        return
    
    payload = {"sender": sender, "target": target, "texto": texto}
    for sid, info in usuarios_conectados.items():
        if info["username"] == target or info["username"] == sender:
            socketio.emit('receive_private_msg', payload, to=sid)

@socketio.on('admin_action')
def handle_admin_action(data):
    emit('force_action', data, broadcast=True)

def broadcast_user_list_all_rooms():
    rows = db_query("SELECT username, rol, genero, avatar, estado FROM usuarios", fetchall=True)
    salas_activas = set([u["sala_actual"] for u in usuarios_conectados.values() if u["sala_actual"] is not None])
    
    db_users_dict = {}
    if rows:
        for r in rows:
            db_users_dict[r[0]] = {"rol": r[1], "genero": r[2], "avatar": r[3] or "", "estado": r[4]}

    for sala in salas_activas:
        lista_sala = []
        for sid, info in usuarios_conectados.items():
            if info["sala_actual"] == sala:
                uname = info["username"]
                if uname == "Administrador" and not admin_visible: 
                    continue
                    
                meta = db_users_dict.get(uname, {"rol": "user", "genero": "hombre", "avatar": "", "estado": "activo"})
                status_visual = 'baneado' if meta["estado"] == 'ban' else 'conectado'
                
                lista_sala.append({
                    "username": uname,
                    "rol": meta["rol"],
                    "genero": meta["genero"],
                    "avatar": meta["avatar"],
                    "status_visual": status_visual
                })
        socketio.emit('update_users', lista_sala, to=sala)

# ==========================================
<<<<<<< HEAD
# PLANTILLA HTML COMPLETA CON CORECHAT
=======
# 4. PLANTILLA HTML (COMPLETA CON TODAS LAS FUNCIONES)
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
# ==========================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<<<<<<< HEAD
    <title>💬 CORECHAT - Chat en Vivo</title>
=======
    <title>WebChat Profesional - Flask</title>
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
    <script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/@twemoji/api@14.1.0/dist/twemoji.min.js" crossorigin="anonymous"></script>
    <script src="https://cdn.jsdelivr.net/npm/emoji-mart@5.6.0/dist/browser.js"></script>
    <style>
<<<<<<< HEAD
        /* === ESTILOS BASE === */
        * { box-sizing: border-box; }
        html, body { 
            height: 100%; 
            margin: 0; 
            padding: 0; 
            background-color: #121212; 
            color: #ffffff; 
            font-family: Arial, sans-serif; 
            overflow: hidden; 
        }
        
        /* === ESTILOS PC (Originales) === */
        .box-container { 
            max-width: 450px; 
            margin: 80px auto; 
            background: #1e1e1e; 
            padding: 30px; 
            border-radius: 8px; 
            border: 1px solid #333; 
            box-shadow: 0 4px 15px rgba(0,0,0,0.5); 
        }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 5px; color: #bbb; font-size: 14px; }
        .input-control { 
            width: 100%; 
            padding: 10px; 
            background: #2d2d2d; 
            border: 1px solid #444; 
            color: white; 
            border-radius: 4px; 
            box-sizing: border-box; 
            font-size: 14px; 
        }
        .input-control:focus { border-color: #0d6efd; outline: none; }
        .btn-block { 
            width: 100%; 
            padding: 12px; 
            background: #0d6efd; 
            border: none; 
            color: white; 
            border-radius: 4px; 
            cursor: pointer; 
            font-size: 16px; 
            font-weight: bold; 
            margin-top: 10px; 
        }
        .btn-block:hover { background: #0b5ed7; }
        .btn-link { 
            background: none; 
            border: none; 
            color: #0dcaf0; 
            cursor: pointer; 
            display: block; 
            margin: 15px auto 0; 
            text-decoration: underline; 
            font-size: 14px; 
        }
        .d-none { display: none !important; }
        
        #lobby-section { 
            max-width: 800px; 
            margin: 50px auto; 
            background: #1e1e1e; 
            padding: 25px; 
            border-radius: 8px; 
            border: 1px solid #333; 
            box-shadow: 0 4px 15px rgba(0,0,0,0.5); 
        }
        .salas-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); 
            gap: 15px; 
            margin-top: 20px; 
        }
        .sala-card { 
            background: #252525; 
            border: 1px solid #444; 
            border-radius: 6px; 
            padding: 15px; 
            cursor: pointer; 
            text-align: center; 
            transition: transform 0.2s, border-color 0.2s; 
        }
=======
        /* === ESTILOS ORIGINALES DE PC === */
        html, body { height: 100%; margin: 0; padding: 0; background-color: #121212; color: #ffffff; font-family: Arial, sans-serif; overflow: hidden; }
        
        .box-container { max-width: 450px; margin: 80px auto; background: #1e1e1e; padding: 30px; border-radius: 8px; border: 1px solid #333; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 5px; color: #bbb; font-size: 14px; }
        .input-control { width: 100%; padding: 10px; background: #2d2d2d; border: 1px solid #444; color: white; border-radius: 4px; box-sizing: border-box; font-size: 14px; }
        .input-control:focus { border-color: #0d6efd; outline: none; }
        .btn-block { width: 100%; padding: 12px; background: #0d6efd; border: none; color: white; border-radius: 4px; cursor: pointer; font-size: 16px; font-weight: bold; margin-top: 10px; }
        .btn-block:hover { background: #0b5ed7; }
        .btn-link { background: none; border: none; color: #0dcaf0; cursor: pointer; display: block; margin: 15px auto 0; text-decoration: underline; font-size: 14px; }
        .d-none { display: none !important; }
        
        #lobby-section { max-width: 800px; margin: 50px auto; background: #1e1e1e; padding: 25px; border-radius: 8px; border: 1px solid #333; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
        .salas-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 15px; margin-top: 20px; }
        .sala-card { background: #252525; border: 1px solid #444; border-radius: 6px; padding: 15px; cursor: pointer; text-align: center; transition: transform 0.2s, border-color 0.2s; }
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
        .sala-card:hover { transform: translateY(-3px); border-color: #0dcaf0; background: #2a2a2a; }
        .sala-icon { font-size: 32px; margin-bottom: 8px; display: block; }
        .sala-name { font-weight: bold; font-size: 16px; color: #fff; margin-bottom: 5px; }
        .sala-count { font-size: 12px; color: #aaa; }

<<<<<<< HEAD
        #chat-section { 
            display: flex; 
            flex-direction: column; 
            height: 100vh; 
            padding: 15px; 
            box-sizing: border-box; 
        }
        .chat-header-container { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            margin-bottom: 15px; 
            position: relative; 
            flex-shrink: 0; 
        }
        .chat-layout { 
            display: flex; 
            flex-grow: 1; 
            height: calc(100vh - 100px); 
            min-height: 0; 
            position: relative; 
        }
        .main-chat { 
            flex: 3; 
            display: flex; 
            flex-direction: column; 
            height: 100%; 
            min-height: 0; 
            position: relative; 
            padding-right: 10px; 
        }
        #chat-box { 
            flex-grow: 1; 
            background: #151515; 
            border: 1px solid #333; 
            padding: 15px; 
            overflow-y: auto; 
            border-radius: 6px; 
            margin-bottom: 15px; 
            min-height: 0; 
        }
        .controls-row { 
            display: flex; 
            gap: 10px; 
            flex-shrink: 0; 
            position: relative; 
        }
        .flex-grow { flex-grow: 1; }
        .toggle-divider-zone { 
            position: relative; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            width: 20px; 
            flex-shrink: 0; 
            z-index: 10; 
        }
        
        #toggle-panel-btn { 
            background: #222; 
            border: 1px solid #444; 
            color: #0dcaf0; 
            width: 22px; 
            height: 45px; 
            border-radius: 4px; 
            cursor: pointer; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            font-size: 11px; 
            font-weight: bold; 
            padding: 0; 
            box-shadow: 0 2px 8px rgba(0,0,0,0.5); 
            position: absolute; 
        }

        .side-users { 
            width: 280px; 
            background: #1e1e1e; 
            border-radius: 6px; 
            border: 1px solid #333; 
            height: 100%; 
            box-sizing: border-box; 
            display: flex; 
            flex-direction: column; 
            min-height: 0; 
            transition: width 0.3s, opacity 0.2s; 
            overflow: hidden; 
            flex-shrink: 0; 
        }
        .side-users-inner { 
            display: flex; 
            flex-direction: column; 
            width: 280px; 
            height: 100%; 
            padding: 15px; 
            box-sizing: border-box; 
            min-height: 0; 
        }
=======
        #chat-section { display: flex; flex-direction: column; height: 100vh; padding: 15px; box-sizing: border-box; }
        .chat-header-container { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; position: relative; flex-shrink: 0; }
        .chat-layout { display: flex; flex-grow: 1; height: calc(100vh - 100px); min-height: 0; position: relative; }
        .main-chat { flex: 3; display: flex; flex-direction: column; height: 100%; min-height: 0; position: relative; padding-right: 10px; }
        #chat-box { flex-grow: 1; background: #151515; border: 1px solid #333; padding: 15px; overflow-y: auto; border-radius: 6px; margin-bottom: 15px; min-height: 0; }
        .controls-row { display: flex; gap: 10px; flex-shrink: 0; position: relative; }
        .flex-grow { flex-grow: 1; }
        .toggle-divider-zone { position: relative; display: flex; align-items: center; justify-content: center; width: 20px; flex-shrink: 0; z-index: 10; }
        
        #toggle-panel-btn { background: #222; border: 1px solid #444; color: #0dcaf0; width: 22px; height: 45px; border-radius: 4px; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: bold; padding: 0; box-shadow: 0 2px 8px rgba(0,0,0,0.5); position: absolute; }

        .side-users { width: 280px; background: #1e1e1e; border-radius: 6px; border: 1px solid #333; height: 100%; box-sizing: border-box; display: flex; flex-direction: column; min-height: 0; transition: width 0.3s, opacity 0.2s; overflow: hidden; flex-shrink: 0; }
        .side-users-inner { display: flex; flex-direction: column; width: 280px; height: 100%; padding: 15px; box-sizing: border-box; min-height: 0; }
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
        #lista-usuarios { flex-grow: 1; overflow-y: auto; min-height: 0; }
        .side-users.collapsed { width: 0 !important; opacity: 0; border: none; }
        
        .status-dot { width: 9px; height: 9px; border-radius: 50%; display: inline-block; margin-right: 8px; }
        .dot-green { background-color: #2ec4b6; box-shadow: 0 0 6px #2ec4b6; }
        .dot-red { background-color: #e71d36; }
        .dot-gray { background-color: #6c757d; }
        
        .badge-admin { color: #ffc107; font-size: 13px; margin-left: 3px; }
        .badge-mod { color: #0dcaf0; font-size: 13px; margin-left: 3px; }
        
        .chat-msg-line { display: flex; align-items: center; flex-wrap: wrap; margin: 8px 0; }
        .msg-avatar-img { width: 24px; height: 24px; border-radius: 50%; object-fit: cover; border: 1px solid #555; margin-right: 6px; display: inline-block; }
<<<<<<< HEAD
        .msg-avatar-initials { 
            width: 24px; 
            height: 24px; 
            border-radius: 50%; 
            display: inline-flex; 
            align-items: center; 
            justify-content: center; 
            font-size: 10px; 
            font-weight: bold; 
            color: #ffffff; 
            text-transform: uppercase; 
            border: 1px solid rgba(255,255,255,0.15); 
            margin-right: 6px; 
        }
        .chat-img-msg { max-width: 120px; max-height: 120px; display: block; margin-top: 5px; border-radius: 4px; }
        .clickable-nick { cursor: pointer; user-select: none; }
        
        .custom-context-menu { 
            position: fixed; 
            background: #252525; 
            border: 1px solid #444; 
            border-radius: 4px; 
            box-shadow: 0 4px 10px rgba(0,0,0,0.5); 
            z-index: 1000; 
            display: none; 
            min-width: 160px; 
            padding: 5px 0; 
        }
        .context-menu-item { padding: 8px 12px; font-size: 13px; color: #eee; cursor: pointer; touch-action: manipulation; }
        .context-menu-item:hover { background: #0d6efd; color: white; }

        .private-chat-window { 
            position: fixed; 
            bottom: 15px; 
            right: 310px; 
            width: 320px; 
            height: 380px; 
            background: #1e1e1e; 
            border: 1px solid #0dcaf0; 
            border-radius: 6px; 
            z-index: 500; 
            display: flex; 
            flex-direction: column; 
            overflow: hidden; 
            box-shadow: 0 4px 15px rgba(0,0,0,0.6); 
        }
        .private-chat-window.minimized { height: 40px !important; }
        .private-chat-header { 
            background: #151515; 
            padding: 10px; 
            border-bottom: 1px solid #333; 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            cursor: move; 
            user-select: none; 
        }
        .private-chat-header span { font-size: 13px; font-weight: bold; color: #0dcaf0; pointer-events: none; }
        .private-chat-actions { display: flex; gap: 8px; }
        .private-chat-btn-action { 
            background: none; 
            border: none; 
            font-weight: bold; 
            cursor: pointer; 
            font-size: 14px; 
            padding: 0 4px; 
            touch-action: manipulation; 
        }
=======
        .msg-avatar-initials { width: 24px; height: 24px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 10px; font-weight: bold; color: #ffffff; text-transform: uppercase; border: 1px solid rgba(255,255,255,0.15); margin-right: 6px; }
        .chat-img-msg { max-width: 120px; max-height: 120px; display: block; margin-top: 5px; border-radius: 4px; }
        .clickable-nick { cursor: pointer; user-select: none; }
        
        .custom-context-menu { position: fixed; background: #252525; border: 1px solid #444; border-radius: 4px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); z-index: 1000; display: none; min-width: 160px; padding: 5px 0; }
        .context-menu-item { padding: 8px 12px; font-size: 13px; color: #eee; cursor: pointer; touch-action: manipulation; }
        .context-menu-item:hover { background: #0d6efd; color: white; }

        .private-chat-window { position: fixed; bottom: 15px; right: 310px; width: 320px; height: 380px; background: #1e1e1e; border: 1px solid #0dcaf0; border-radius: 6px; z-index: 500; display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.6); }
        .private-chat-window.minimized { height: 40px !important; }
        .private-chat-header { background: #151515; padding: 10px; border-bottom: 1px solid #333; display: flex; justify-content: space-between; align-items: center; cursor: move; user-select: none; }
        .private-chat-header span { font-size: 13px; font-weight: bold; color: #0dcaf0; pointer-events: none; }
        .private-chat-actions { display: flex; gap: 8px; }
        .private-chat-btn-action { background: none; border: none; font-weight: bold; cursor: pointer; font-size: 14px; padding: 0 4px; touch-action: manipulation; }
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
        .private-chat-min { color: #ffc107; }
        .private-chat-close { color: #dc3545; }
        .private-chat-box { flex-grow: 1; background: #121212; padding: 10px; overflow-y: auto; font-size: 13px; }
        .private-chat-footer { padding: 8px; background: #151515; display: flex; gap: 5px; border-top: 1px solid #333; }
<<<<<<< HEAD
        .private-msg-input { 
            flex-grow: 1; 
            background: #252525; 
            border: 1px solid #444; 
            color: white; 
            padding: 6px; 
            border-radius: 4px; 
        }
        .private-msg-btn { 
            background: #0dcaf0; 
            color: black; 
            border: none; 
            padding: 6px 12px; 
            font-weight: bold; 
            border-radius: 4px; 
            cursor: pointer; 
            touch-action: manipulation; 
        }

        .media-modal { 
            position: absolute; 
            bottom: 55px; 
            left: 60px; 
            width: 360px; 
            background: #1e1e1e; 
            border: 1px solid #444; 
            border-radius: 8px; 
            z-index: 100; 
            padding: 12px; 
            display: none; 
        }
        .media-modal-tabs { display: flex; gap: 5px; margin-bottom: 10px; border-bottom: 1px solid #333; padding-bottom: 5px; }
        .media-tab-btn { 
            flex: 1; 
            background: #2a2a2a; 
            color: #aaa; 
            border: 1px solid #333; 
            padding: 6px; 
            cursor: pointer; 
            font-size: 12px; 
            border-radius: 4px; 
            touch-action: manipulation; 
        }
        .media-tab-btn.active { background: #0d6efd; color: white; border-color: #0d6efd; }
        .search-row { margin-bottom: 10px; }
        .search-control { 
            width: 100%; 
            padding: 8px; 
            background: #151515; 
            border: 1px solid #444; 
            color: white; 
            border-radius: 4px; 
            box-sizing: border-box; 
        }
        .media-grid-container { 
            height: 180px; 
            overflow-y: auto; 
            background: #151515; 
            border-radius: 4px; 
            padding: 8px; 
            border: 1px solid #2d2d2d; 
        }
        .media-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
        .media-item { 
            width: 100%; 
            height: 60px; 
            object-fit: contain; 
            cursor: pointer; 
            border: 1px solid #333; 
            border-radius: 4px; 
            background: #121212; 
            touch-action: manipulation; 
        }
        .media-item:hover { border-color: #0dcaf0; }
        
        img.emoji { height: 1.35em; width: 1.35em; margin: 0 .07em 0 .1em; vertical-align: -0.15em; display: inline-block; }
        #emoji-mart-floating-picker { 
            position: absolute; 
            bottom: 55px; 
            left: 10px; 
            z-index: 110; 
            display: none; 
            box-shadow: 0 4px 15px rgba(0,0,0,0.6); 
            max-width: 90vw; 
        }

        .avatar-upload-modal { 
            position: fixed; 
            top: 50%; 
            left: 50%; 
            transform: translate(-50%, -50%); 
            width: 340px; 
            background: #1e1e1e; 
            border: 1px solid #444; 
            border-radius: 8px; 
            z-index: 300; 
            padding: 20px; 
            display: none; 
            max-width: 92vw; 
        }
        .avatar-preview-box { 
            width: 90px; 
            height: 90px; 
            border-radius: 50%; 
            object-fit: cover; 
            border: 2px solid #0dcaf0; 
            display: block; 
            margin: 15px auto; 
        }
        
        .profile-menu-container { 
            position: relative; 
            display: flex; 
            align-items: center; 
            cursor: pointer; 
            user-select: none; 
            padding: 5px 10px; 
            border-radius: 20px; 
            touch-action: manipulation; 
        }
        .profile-menu-container:hover { background: #252525; }
        .profile-text-link { color: #ffffff; font-size: 14px; font-weight: bold; margin-right: 10px; }
        .profile-avatar-img { width: 35px; height: 35px; border-radius: 50%; object-fit: cover; border: 1px solid #444; }
        .profile-avatar-initials { 
            width: 35px; 
            height: 35px; 
            border-radius: 50%; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            font-size: 13px; 
            font-weight: bold; 
            color: #ffffff; 
            text-transform: uppercase; 
            border: 1px solid rgba(255,255,255,0.2); 
        }
        
        .profile-dropdown-list { 
            position: absolute; 
            top: 45px; 
            right: 0; 
            width: 230px; 
            background: #1e1e1e; 
            border: 1px solid #333; 
            border-radius: 6px; 
            z-index: 200; 
            display: none; 
            padding: 5px 0; 
        }
        .profile-dropdown-item { 
            padding: 10px 15px; 
            font-size: 14px; 
            color: #bbb; 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            touch-action: manipulation; 
            cursor: pointer; 
        }
        .profile-dropdown-item:hover { background: #2d2d2d; color: #fff; }
        .profile-dropdown-divider { height: 1px; background: #333; margin: 5px 0; }
        .profile-submenu-panel { 
            background: #151515; 
            padding: 10px 15px; 
            border-bottom: 1px solid #2d2d2d; 
            display: none; 
        }
        .submenu-title { font-size: 11px; color: #0dcaf0; font-weight: bold; text-transform: uppercase; margin-bottom: 8px; display: block; }
        .submenu-grid { display: flex; flex-direction: column; gap: 8px; }
        .submenu-field { display: flex; align-items: center; justify-content: space-between; font-size: 12px; color: #aaa; }
        .submenu-select { 
            background: #252525; 
            border: 1px solid #444; 
            color: white; 
            padding: 4px 6px; 
            border-radius: 4px; 
            font-size: 12px; 
            width: 110px; 
        }
        
        #admin-section { 
            height: 100vh; 
            overflow-y: auto; 
            padding: 20px; 
            box-sizing: border-box; 
        }
        .admin-box { 
            background: #1e1e1e; 
            padding: 25px; 
            border-radius: 8px; 
            border: 1px solid #333; 
            margin-bottom: 20px; 
        }
        .admin-nav { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            border-bottom: 1px solid #333; 
            padding-bottom: 15px; 
            margin-bottom: 20px; 
            flex-wrap: wrap; 
            gap: 10px; 
        }
        .admin-nav h2 { margin: 0; }
        .admin-nav .admin-nav-buttons { display: flex; gap: 10px; flex-wrap: wrap; }
        .tabs-header { 
            display: flex; 
            gap: 5px; 
            margin-bottom: 20px; 
            border-bottom: 1px solid #333; 
            flex-wrap: wrap; 
        }
        .tab-btn { 
            background: #2d2d2d; 
            color: #aaa; 
            border: 1px solid #333; 
            border-bottom: none; 
            padding: 10px 20px; 
            cursor: pointer; 
            font-weight: bold; 
            border-top-left-radius: 4px; 
            border-top-right-radius: 4px; 
            touch-action: manipulation; 
        }
        .tab-btn.active { background: #0d6efd; color: white; border-color: #0d6efd; }
        .form-inline-admin { 
            display: flex; 
            gap: 10px; 
            background: #151515; 
            padding: 15px; 
            border-radius: 6px; 
            border: 1px solid #333; 
            flex-wrap: wrap; 
            align-items: flex-end;
        }
        
        table { 
            width: 100%; 
            border-collapse: collapse; 
            margin-top: 15px; 
            background: #151515; 
        }
        th, td { 
            padding: 12px; 
            border: 1px solid #333; 
            text-align: left; 
            font-size: 14px; 
        }
        th { background: #2d2d2d; color: #aaa; }
        .btn-sm { 
            padding: 5px 8px; 
            font-size: 12px; 
            cursor: pointer; 
            border: none; 
            border-radius: 3px; 
            font-weight: bold; 
            margin-right: 2px; 
            touch-action: manipulation; 
        }
        .badge { padding: 3px 8px; border-radius: 3px; font-size: 11px; font-weight: bold; text-transform: uppercase; display: inline-block; }
        .admin-sticker-preview { width: 40px; height: 40px; object-fit: contain; background: #121212; }
        .admin-rol-select { 
            background: #252525; 
            border: 1px solid #555; 
            color: white; 
            font-size: 12px; 
            padding: 4px; 
            border-radius: 4px; 
        }
        
        .btn-visibilidad { 
            background: #6f42c1; 
            color: white; 
            padding: 10px 20px; 
            border: none; 
            border-radius: 4px; 
            cursor: pointer; 
            font-weight: bold; 
            font-size: 14px; 
            transition: background 0.2s; 
            margin-bottom: 15px; 
            display: inline-block; 
            touch-action: manipulation; 
        }
        .btn-visibilidad:hover { background: #59359a; }
        
        .table-input-edit { 
            background: #252525; 
            border: 1px solid #555; 
            color: white; 
            font-size: 13px; 
            padding: 4px 8px; 
            border-radius: 4px; 
            width: 110px; 
            box-sizing: border-box; 
        }
        .table-input-edit:focus { border-color: #0dcaf0; outline: none; }
        .admin-time-select { 
            background: #222; 
            border: 1px solid #555; 
            color: #ffc107; 
            font-size: 11px; 
            padding: 4px; 
            border-radius: 4px; 
            font-weight: bold; 
            margin-right: 4px; 
        }
        .admin-action-container { display: flex; align-items: center; margin-bottom: 4px; flex-wrap: wrap; gap: 4px; }

        .db-status-banner { 
            padding: 15px; 
            border-radius: 6px; 
            margin-bottom: 20px; 
            display: flex; 
            align-items: center; 
            justify-content: space-between; 
            font-weight: bold; 
            flex-wrap: wrap; 
            gap: 10px; 
        }
=======
        .private-msg-input { flex-grow: 1; background: #252525; border: 1px solid #444; color: white; padding: 6px; border-radius: 4px; }
        .private-msg-btn { background: #0dcaf0; color: black; border: none; padding: 6px 12px; font-weight: bold; border-radius: 4px; cursor: pointer; touch-action: manipulation; }

        .media-modal { position: absolute; bottom: 55px; left: 60px; width: 360px; background: #1e1e1e; border: 1px solid #444; border-radius: 8px; z-index: 100; padding: 12px; display: none; }
        .media-modal-tabs { display: flex; gap: 5px; margin-bottom: 10px; border-bottom: 1px solid #333; padding-bottom: 5px; }
        .media-tab-btn { flex: 1; background: #2a2a2a; color: #aaa; border: 1px solid #333; padding: 6px; cursor: pointer; font-size: 12px; border-radius: 4px; touch-action: manipulation; }
        .media-tab-btn.active { background: #0d6efd; color: white; border-color: #0d6efd; }
        .search-row { margin-bottom: 10px; }
        .search-control { width: 100%; padding: 8px; background: #151515; border: 1px solid #444; color: white; border-radius: 4px; box-sizing: border-box; }
        .media-grid-container { height: 180px; overflow-y: auto; background: #151515; border-radius: 4px; padding: 8px; border: 1px solid #2d2d2d; }
        .media-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
        .media-item { width: 100%; height: 60px; object-fit: contain; cursor: pointer; border: 1px solid #333; border-radius: 4px; background: #121212; touch-action: manipulation; }
        .media-item:hover { border-color: #0dcaf0; }
        
        img.emoji { height: 1.35em; width: 1.35em; margin: 0 .07em 0 .1em; vertical-align: -0.15em; display: inline-block; }
        #emoji-mart-floating-picker { position: absolute; bottom: 55px; left: 10px; z-index: 110; display: none; box-shadow: 0 4px 15px rgba(0,0,0,0.6); }

        .avatar-upload-modal { position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 340px; background: #1e1e1e; border: 1px solid #444; border-radius: 8px; z-index: 300; padding: 20px; display: none; }
        .avatar-preview-box { width: 90px; height: 90px; border-radius: 50%; object-fit: cover; border: 2px solid #0dcaf0; display: block; margin: 15px auto; }
        
        .profile-menu-container { position: relative; display: flex; align-items: center; cursor: pointer; user-select: none; padding: 5px 10px; border-radius: 20px; touch-action: manipulation; }
        .profile-menu-container:hover { background: #252525; }
        .profile-text-link { color: #ffffff; font-size: 14px; font-weight: bold; margin-right: 10px; }
        .profile-avatar-img { width: 35px; height: 35px; border-radius: 50%; object-fit: cover; border: 1px solid #444; }
        .profile-avatar-initials { width: 35px; height: 35px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: bold; color: #ffffff; text-transform: uppercase; border: 1px solid rgba(255,255,255,0.2); }
        
        .profile-dropdown-list { position: absolute; top: 45px; right: 0; width: 230px; background: #1e1e1e; border: 1px solid #333; border-radius: 6px; z-index: 200; display: none; padding: 5px 0; }
        .profile-dropdown-item { padding: 10px 15px; font-size: 14px; color: #bbb; display: flex; justify-content: space-between; align-items: center; touch-action: manipulation; }
        .profile-dropdown-item:hover { background: #2d2d2d; color: #fff; }
        .profile-dropdown-divider { height: 1px; background: #333; margin: 5px 0; }
        .profile-submenu-panel { background: #151515; padding: 10px 15px; border-bottom: 1px solid #2d2d2d; display: none; }
        .submenu-title { font-size: 11px; color: #0dcaf0; font-weight: bold; text-transform: uppercase; margin-bottom: 8px; display: block; }
        .submenu-grid { display: flex; flex-direction: column; gap: 8px; }
        .submenu-field { display: flex; align-items: center; justify-content: space-between; font-size: 12px; color: #aaa; }
        .submenu-select { background: #252525; border: 1px solid #444; color: white; padding: 4px 6px; border-radius: 4px; font-size: 12px; width: 110px; }
        
        #admin-section { height: 100vh; overflow-y: auto; padding: 20px; box-sizing: border-box; }
        .admin-box { background: #1e1e1e; padding: 25px; border-radius: 8px; border: 1px solid #333; margin-bottom: 20px; }
        .admin-nav { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #333; padding-bottom: 15px; margin-bottom: 20px; flex-wrap: wrap; gap: 10px; }
        .admin-nav h2 { margin: 0; }
        .admin-nav .admin-nav-buttons { display: flex; gap: 10px; flex-wrap: wrap; }
        .tabs-header { display: flex; gap: 5px; margin-bottom: 20px; border-bottom: 1px solid #333; flex-wrap: wrap; }
        .tab-btn { background: #2d2d2d; color: #aaa; border: 1px solid #333; border-bottom: none; padding: 10px 20px; cursor: pointer; font-weight: bold; border-top-left-radius: 4px; border-top-right-radius: 4px; touch-action: manipulation; }
        .tab-btn.active { background: #0d6efd; color: white; border-color: #0d6efd; }
        .form-inline-admin { display: flex; gap: 10px; background: #151515; padding: 15px; border-radius: 6px; border: 1px solid #333; flex-wrap: wrap; align-items: flex-end;}
        
        table { width: 100%; border-collapse: collapse; margin-top: 15px; background: #151515; }
        th, td { padding: 12px; border: 1px solid #333; text-align: left; font-size: 14px; }
        th { background: #2d2d2d; color: #aaa; }
        .btn-sm { padding: 5px 8px; font-size: 12px; cursor: pointer; border: none; border-radius: 3px; font-weight: bold; margin-right: 2px; touch-action: manipulation; }
        .badge { padding: 3px 8px; border-radius: 3px; font-size: 11px; font-weight: bold; text-transform: uppercase; display: inline-block; }
        .admin-sticker-preview { width: 40px; height: 40px; object-fit: contain; background: #121212; }
        .admin-rol-select { background: #252525; border: 1px solid #555; color: white; font-size: 12px; padding: 4px; border-radius: 4px; }
        
        .btn-visibilidad { background: #6f42c1; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 14px; transition: background 0.2s; margin-bottom: 15px; display: inline-block; touch-action: manipulation; }
        .btn-visibilidad:hover { background: #59359a; }
        
        .table-input-edit { background: #252525; border: 1px solid #555; color: white; font-size: 13px; padding: 4px 8px; border-radius: 4px; width: 110px; box-sizing: border-box; }
        .table-input-edit:focus { border-color: #0dcaf0; outline: none; }
        .admin-time-select { background: #222; border: 1px solid #555; color: #ffc107; font-size: 11px; padding: 4px; border-radius: 4px; font-weight: bold; margin-right: 4px; }
        .admin-action-container { display: flex; align-items: center; margin-bottom: 4px; flex-wrap: wrap; gap: 4px; }

        .db-status-banner { padding: 15px; border-radius: 6px; margin-bottom: 20px; display: flex; align-items: center; justify-content: space-between; font-weight: bold; flex-wrap: wrap; gap: 10px; }
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
        .status-local-mode { background: rgba(13, 110, 253, 0.15); border: 1px solid #0d6efd; color: #0dcaf0; }
        .status-online-mode { background: rgba(25, 135, 84, 0.15); border: 1px solid #198754; color: #198754; }
        .form-db-config { background: #151515; padding: 20px; border-radius: 6px; border: 1px solid #333; max-width: 600px; }

<<<<<<< HEAD
        /* === HEADER MÓVIL === */
        #mobile-header {
            display: none;
            background: #1e1e1e;
            padding: 6px 10px;
            border-bottom: 1px solid #333;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 999;
            box-shadow: 0 2px 10px rgba(0,0,0,0.5);
            min-height: 48px;
        }
        
        #mobile-header .mobile-header-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 6px;
        }
        
        #mobile-room-name {
            color: #0dcaf0;
            font-weight: bold;
            font-size: 14px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            flex: 1;
            min-width: 0;
        }
        
        #mobile-header .mobile-header-buttons {
            display: flex;
            gap: 4px;
            flex-shrink: 0;
        }
        
        #mobile-header .mobile-btn {
            background: #333;
            color: white;
            border: 1px solid #555;
            padding: 4px 8px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            touch-action: manipulation;
            min-height: 34px;
            min-width: 34px;
            display: flex;
            align-items: center;
            justify-content: center;
            white-space: nowrap;
        }
        
        #mobile-header .mobile-btn-admin {
            background: #ffc107;
            color: black;
            border: none;
        }

=======
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
        /* === ADAPTACIÓN PARA CELULAR === */
        @media only screen and (max-width: 768px) {
            #mobile-header {
                display: block !important;
<<<<<<< HEAD
            }
            
            #lobby-section {
                margin-top: 60px !important;
                margin-left: 8px !important;
                margin-right: 8px !important;
                padding: 12px !important;
                max-width: 100% !important;
            }
            
            #chat-section {
                padding-top: 60px !important;
                padding-left: 6px !important;
                padding-right: 6px !important;
                padding-bottom: 6px !important;
            }
            
            .chat-header-container {
                padding: 4px 0;
                gap: 4px;
                flex-wrap: wrap;
            }
            
            .chat-header-container h3 {
                font-size: 13px !important;
                margin: 0;
            }
            
            .chat-header-container button {
                font-size: 11px !important;
                padding: 4px 8px !important;
                min-height: 32px !important;
=======
                background: #1e1e1e;
                padding: 10px 15px;
                border-bottom: 1px solid #333;
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                z-index: 999;
                box-shadow: 0 2px 10px rgba(0,0,0,0.3);
            }
            
            #mobile-header .mobile-header-content {
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            #mobile-room-name {
                color: #0dcaf0;
                font-weight: bold;
                font-size: 16px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                max-width: 50%;
            }
            
            #mobile-header .mobile-header-buttons {
                display: flex;
                gap: 6px;
                flex-shrink: 0;
            }
            
            #mobile-header .mobile-btn {
                background: #333;
                color: white;
                border: 1px solid #555;
                padding: 6px 10px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 13px;
                touch-action: manipulation;
                min-height: 38px;
                min-width: 38px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            #mobile-header .mobile-btn:hover {
                background: #444;
            }
            
            #mobile-header .mobile-btn-admin {
                background: #ffc107;
                color: black;
                border: none;
            }
            
            #chat-section {
                padding-top: 65px !important;
            }
            
            #lobby-section {
                padding-top: 10px !important;
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
            }
            
            .side-users {
                width: 100% !important;
<<<<<<< HEAD
                height: 180px !important;
                margin-top: 4px !important;
                border-radius: 4px !important;
                display: none !important;
                position: relative;
                z-index: 50;
                flex-shrink: 0;
=======
                height: 200px !important;
                margin-top: 8px !important;
                border-radius: 6px !important;
                display: none !important;
                position: relative;
                z-index: 50;
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
            }
            
            .side-users.mobile-visible {
                display: flex !important;
            }
            
            .side-users-inner {
                width: 100% !important;
<<<<<<< HEAD
                padding: 8px !important;
                height: 100% !important;
            }
            
            .side-users-inner h4 {
                font-size: 13px !important;
                margin-bottom: 6px !important;
                padding-bottom: 3px !important;
            }
            
            .chat-layout {
                flex-direction: column !important;
                height: calc(100vh - 130px) !important;
            }
            
            .main-chat {
                flex: 1 !important;
                padding-right: 0 !important;
                height: 100% !important;
                min-height: 0 !important;
            }
            
            #chat-box {
                padding: 8px !important;
                margin-bottom: 6px !important;
                font-size: 14px !important;
                min-height: 120px !important;
                max-height: calc(100vh - 280px) !important;
            }
            
            .controls-row {
                gap: 4px !important;
                flex-wrap: nowrap !important;
            }
            
            .controls-row button {
                font-size: 16px !important;
                padding: 0 8px !important;
                min-height: 38px !important;
                min-width: 38px !important;
            }
            
            .controls-row #message-input {
                font-size: 14px !important;
                padding: 8px !important;
                min-height: 38px !important;
            }
            
            .controls-row .btn-enviar {
                font-size: 12px !important;
                padding: 0 12px !important;
                min-height: 38px !important;
            }
            
            .toggle-divider-zone {
                display: none !important;
            }
            
            .profile-text-link {
                font-size: 12px !important;
            }
            
            .profile-avatar-img, .profile-avatar-initials {
                width: 28px !important;
                height: 28px !important;
                font-size: 10px !important;
            }
            
            .profile-dropdown-list {
                width: 200px !important;
                right: -5px !important;
            }
            
            .chat-msg-line {
                font-size: 13px !important;
                margin: 4px 0 !important;
                gap: 2px !important;
            }
            
            .msg-avatar-img, .msg-avatar-initials {
                width: 20px !important;
                height: 20px !important;
                font-size: 8px !important;
                margin-right: 3px !important;
            }
            
            .chat-img-msg {
                max-width: 80px !important;
                max-height: 80px !important;
=======
                padding: 10px !important;
            }
            
            .btn-block, .btn-sm, .btn-visibilidad {
                font-size: 16px !important;
                padding: 14px 20px !important;
                min-height: 48px !important;
            }
            
            .input-control, .search-control {
                font-size: 16px !important;
                padding: 14px !important;
                min-height: 48px !important;
            }
            
            .chat-msg-line {
                font-size: 15px !important;
                margin: 8px 0 !important;
                gap: 4px !important;
            }
            
            .msg-avatar-img, .msg-avatar-initials {
                width: 28px !important;
                height: 28px !important;
                font-size: 11px !important;
            }
            
            .chat-img-msg {
                max-width: 100px !important;
                max-height: 100px !important;
            }
            
            .chat-header-container {
                flex-wrap: wrap !important;
                gap: 6px !important;
                padding-top: 4px !important;
            }
            
            .chat-header-container h3 {
                font-size: 14px !important;
            }
            
            .chat-header-container button {
                font-size: 12px !important;
                padding: 4px 10px !important;
                min-height: 38px !important;
            }
            
            .controls-row button {
                font-size: 20px !important;
                padding: 0 16px !important;
                min-height: 48px !important;
                min-width: 48px !important;
            }
            
            .controls-row #message-input {
                font-size: 16px !important;
                padding: 12px !important;
                min-height: 48px !important;
            }
            
            .controls-row .btn-enviar {
                font-size: 14px !important;
                padding: 0 18px !important;
                min-height: 48px !important;
            }
            
            .private-chat-window {
                width: 92% !important;
                max-width: 360px !important;
                height: 55vh !important;
                right: 4% !important;
                bottom: 10px !important;
            }
            
            .private-chat-header span {
                font-size: 14px !important;
            }
            
            .private-msg-input {
                font-size: 15px !important;
                padding: 10px !important;
                min-height: 44px !important;
            }
            
            .private-msg-btn {
                min-height: 44px !important;
                min-width: 60px !important;
                font-size: 14px !important;
            }
            
            .avatar-upload-modal {
                width: 92% !important;
                max-width: 380px !important;
                padding: 20px !important;
                top: 50% !important;
                left: 50% !important;
                transform: translate(-50%, -50%) !important;
            }
            
            .avatar-upload-modal button {
                min-height: 48px !important;
                font-size: 16px !important;
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
            }
            
            .salas-grid {
                grid-template-columns: repeat(2, 1fr) !important;
<<<<<<< HEAD
                gap: 6px !important;
            }
            
            .sala-card {
                padding: 10px !important;
                min-height: 60px !important;
            }
            
            .sala-icon {
                font-size: 22px !important;
            }
            
            .sala-name {
                font-size: 12px !important;
            }
            
            .sala-count {
                font-size: 10px !important;
            }
            
            .btn-block, .btn-sm, .btn-visibilidad {
                font-size: 14px !important;
                padding: 10px 14px !important;
                min-height: 40px !important;
            }
            
            .input-control, .search-control {
                font-size: 14px !important;
                padding: 8px !important;
                min-height: 40px !important;
            }
            
            .private-chat-window {
                width: 94% !important;
                max-width: 340px !important;
                height: 50vh !important;
                right: 3% !important;
                bottom: 8px !important;
                left: 3% !important;
            }
            
            .private-chat-header span {
                font-size: 12px !important;
            }
            
            .private-msg-input {
                font-size: 13px !important;
                padding: 6px !important;
                min-height: 34px !important;
            }
            
            .private-msg-btn {
                min-height: 34px !important;
                min-width: 50px !important;
                font-size: 12px !important;
            }
            
            .avatar-upload-modal {
                width: 94% !important;
                max-width: 360px !important;
                padding: 16px !important;
            }
            
            .avatar-upload-modal button {
                min-height: 40px !important;
                font-size: 14px !important;
            }
            
            #admin-section {
                padding: 8px !important;
                padding-top: 60px !important;
            }
            
            .admin-box {
                padding: 12px !important;
                margin-bottom: 10px !important;
            }
            
            .admin-nav h2 {
                font-size: 16px !important;
            }
            
            .admin-nav .admin-nav-buttons button {
                font-size: 11px !important;
                padding: 6px 10px !important;
                min-height: 34px !important;
            }
            
            .tab-btn {
                font-size: 10px !important;
                padding: 6px 10px !important;
                min-height: 32px !important;
            }
            
            .form-inline-admin {
                flex-direction: column !important;
                gap: 6px !important;
                padding: 10px !important;
            }
            
            .form-inline-admin > div {
                width: 100% !important;
            }
            
            .form-inline-admin button {
                width: 100% !important;
                padding: 10px !important;
                min-height: 40px !important;
=======
                gap: 10px !important;
            }
            
            .sala-card {
                padding: 12px !important;
                min-height: 80px !important;
                display: flex !important;
                flex-direction: column !important;
                align-items: center !important;
                justify-content: center !important;
            }
            
            .sala-icon {
                font-size: 28px !important;
            }
            
            .sala-name {
                font-size: 14px !important;
            }
            
            .sala-count {
                font-size: 11px !important;
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
            }
            
            .table-responsive {
                overflow-x: auto !important;
                -webkit-overflow-scrolling: touch !important;
                display: block !important;
                width: 100% !important;
            }
            
            table {
<<<<<<< HEAD
                font-size: 11px !important;
                min-width: 500px !important;
            }
            
            th, td {
                padding: 6px 4px !important;
                font-size: 11px !important;
            }
            
            .table-input-edit {
                font-size: 10px !important;
                padding: 2px 4px !important;
                width: 60px !important;
                min-height: 28px !important;
            }
            
            .admin-time-select {
                font-size: 9px !important;
                padding: 2px !important;
                min-height: 26px !important;
            }
            
            .btn-sm {
                font-size: 9px !important;
                padding: 2px 4px !important;
                min-height: 26px !important;
=======
                font-size: 12px !important;
                min-width: 600px !important;
            }
            
            th, td {
                padding: 8px 6px !important;
                font-size: 12px !important;
            }
            
            .table-input-edit {
                font-size: 11px !important;
                padding: 3px 5px !important;
                width: 70px !important;
                min-height: 32px !important;
            }
            
            .admin-time-select {
                font-size: 10px !important;
                padding: 2px !important;
                min-height: 30px !important;
            }
            
            .btn-sm {
                font-size: 10px !important;
                padding: 4px 6px !important;
                min-height: 30px !important;
            }
            
            body, p, span, div, input, button, select, label {
                font-size: 15px !important;
            }
            
            h2 { font-size: 20px !important; }
            h3 { font-size: 17px !important; }
            h4 { font-size: 15px !important; }
            
            #lobby-section {
                margin: 15px !important;
                padding: 15px !important;
            }
            
            .profile-text-link {
                font-size: 13px !important;
            }
            
            .profile-avatar-img, .profile-avatar-initials {
                width: 32px !important;
                height: 32px !important;
                font-size: 12px !important;
            }
            
            .profile-dropdown-list {
                width: 210px !important;
                right: -5px !important;
            }
            
            .profile-dropdown-item {
                font-size: 14px !important;
                padding: 10px 14px !important;
                min-height: 44px !important;
            }
            
            #admin-section {
                padding: 10px !important;
            }
            
            .admin-box {
                padding: 15px !important;
            }
            
            .admin-nav {
                flex-wrap: wrap !important;
                gap: 8px !important;
            }
            
            .admin-nav h2 {
                font-size: 16px !important;
            }
            
            .admin-nav .admin-nav-buttons button {
                font-size: 12px !important;
                padding: 8px 12px !important;
                min-height: 40px !important;
            }
            
            .tabs-header {
                flex-wrap: wrap !important;
                gap: 4px !important;
            }
            
            .tab-btn {
                font-size: 11px !important;
                padding: 8px 12px !important;
                min-height: 38px !important;
            }
            
            .form-inline-admin {
                flex-direction: column !important;
                gap: 8px !important;
                align-items: stretch !important;
            }
            
            .form-inline-admin > div {
                min-width: unset !important;
                width: 100% !important;
            }
            
            .form-inline-admin button {
                width: 100% !important;
                padding: 12px !important;
                min-height: 48px !important;
            }
            
            .form-inline-admin select {
                min-height: 48px !important;
            }
            
            .form-db-config {
                padding: 15px !important;
            }
            
            .db-status-banner {
                font-size: 13px !important;
                padding: 12px !important;
                flex-wrap: wrap !important;
                gap: 8px !important;
            }
            
            #toggle-panel-btn {
                display: none !important;
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
            }
            
            .media-modal {
                left: 50% !important;
                transform: translateX(-50%) !important;
<<<<<<< HEAD
                width: 94% !important;
                max-width: 340px !important;
                bottom: 55px !important;
=======
                width: 92% !important;
                max-width: 360px !important;
                bottom: 70px !important;
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
            }
            
            #emoji-mart-floating-picker {
                left: 50% !important;
                transform: translateX(-50%) !important;
<<<<<<< HEAD
                max-width: 94% !important;
                bottom: 55px !important;
            }
            
            .custom-context-menu {
                min-width: 180px !important;
            }
            
            .context-menu-item {
                padding: 10px 14px !important;
                font-size: 14px !important;
                min-height: 38px !important;
            }
            
            .form-db-config {
                padding: 12px !important;
            }
            
            .db-status-banner {
                font-size: 12px !important;
                padding: 10px !important;
            }
            
            #current-room-indicator {
                font-size: 10px !important;
                padding: 2px 8px !important;
            }
            
            .box-container {
                margin: 60px 8px !important;
                padding: 20px !important;
                max-width: 100% !important;
=======
                max-width: 92% !important;
                bottom: 70px !important;
            }
            
            .custom-context-menu {
                min-width: 200px !important;
            }
            
            .context-menu-item {
                padding: 12px 16px !important;
                font-size: 15px !important;
                min-height: 44px !important;
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
            }
        }
    </style>
</head>
<body>
    <!-- HEADER MÓVIL -->
<<<<<<< HEAD
    <div id="mobile-header">
        <div class="mobile-header-content">
            <span id="mobile-room-name">💬 CORECHAT</span>
=======
    <div id="mobile-header" style="display: none;">
        <div class="mobile-header-content">
            <span id="mobile-room-name">💬 Chat</span>
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
            <div class="mobile-header-buttons">
                <button class="mobile-btn" id="mobile-toggle-users">👥</button>
                <button class="mobile-btn" id="mobile-back-lobby">🏠</button>
                <button class="mobile-btn mobile-btn-admin d-none" id="mobile-go-admin">⚙️</button>
            </div>
        </div>
    </div>

    <div id="custom-context-menu" class="custom-context-menu">
        <div class="context-menu-item" onclick="abrirVentanaPrivadoDesdeContexto()">💬 Chat privado</div>
        <div id="context-option-mute" class="context-menu-item" onclick="ejecutarMuteLocal()">🔇 Silenciar localmente</div>
    </div>

    <div id="private-chats-container"></div>

    <!-- AUTH SECTION -->
    <div id="auth-section" class="box-container">
<<<<<<< HEAD
        <h2 id="auth-title" style="margin-top: 0; margin-bottom: 20px; text-align: center;">💬 CORECHAT</h2>
=======
        <h2 id="auth-title" style="margin-top: 0; margin-bottom: 20px; text-align: center;">Iniciar Sesión</h2>
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
        <div class="form-group">
            <label>Usuario</label>
            <input type="text" id="username" class="input-control" placeholder="Usuario" onkeypress="if(event.key==='Enter') procesarAutenticacion()">
        </div>
        <div class="form-group">
            <label>Contraseña</label>
            <input type="password" id="password" class="input-control" placeholder="Contraseña" onkeypress="if(event.key==='Enter') procesarAutenticacion()">
        </div>
        <div class="form-group d-none" id="gender-group">
            <label>Género</label>
            <select id="gender" class="input-control">
                <option value="hombre">Hombre</option>
                <option value="mujer">Mujer</option>
            </select>
        </div>
        <button id="btn-login" class="btn-block" onclick="procesarAutenticacion()">Ingresar al Sistema</button>
        <button id="btn-toggle-auth" class="btn-link" onclick="toggleAuthMode()">¿No tenés cuenta? Registrate acá</button>
    </div>

    <!-- LOBBY SECTION -->
    <div id="lobby-section" class="d-none">
<<<<<<< HEAD
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #333; padding-bottom: 10px; flex-wrap: wrap; gap: 6px;">
            <h2 style="margin: 0; font-size: 18px;">💬 CORECHAT - Salas</h2>
            <div style="display: flex; gap: 6px; flex-wrap: wrap;">
                <button id="btn-go-admin-lobby" style="background: #ffc107; color: black; padding: 6px 12px; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 12px;" class="d-none" onclick="irAlPanelDesdeLobby()">Admin</button>
                <button style="background: #dc3545; color: white; padding: 6px 12px; border: none; border-radius: 4px; cursor: pointer; touch-action: manipulation; font-size: 12px;" onclick="location.reload()">Salir</button>
=======
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #333; padding-bottom: 15px; flex-wrap: wrap; gap: 10px;">
            <h2 style="margin: 0;">Seleccionar Sala de Chat</h2>
            <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                <button id="btn-go-admin-lobby" style="background: #ffc107; color: black; padding: 8px 15px; border: none; border-radius: 4px; cursor: pointer; font-weight: bold;" class="d-none" onclick="irAlPanelDesdeLobby()">Admin Panel</button>
                <button style="background: #dc3545; color: white; padding: 8px 15px; border: none; border-radius: 4px; cursor: pointer; touch-action: manipulation;" onclick="location.reload()">Salir</button>
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
            </div>
        </div>
        <div id="contenedor-salas-grid" class="salas-grid"></div>
    </div>

    <!-- CHAT SECTION -->
    <div id="chat-section" class="d-none">
        <div class="chat-header-container">
<<<<<<< HEAD
            <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap; flex:1; min-width:0;">
                <button style="background: #333; color: #0dcaf0; border: 1px solid #555; padding: 4px 10px; border-radius: 4px; cursor: pointer; font-weight: bold; touch-action: manipulation; font-size: 12px;" onclick="volverAlLobbyDeSalas()">◀</button>
                <h3 id="welcome-msg" style="margin: 0; font-size: 13px; flex:1; min-width:0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">Conectado</h3>
                <span id="current-room-indicator" style="background: #0d6efd; color: white; padding: 2px 8px; border-radius: 10px; font-size: 10px; font-weight: bold; white-space: nowrap;">Sala</span>
            </div>
            <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap; flex-shrink:0;">
                <button id="btn-go-admin" style="background: #ffc107; color: black; padding: 6px 12px; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; touch-action: manipulation; font-size: 12px;" class="d-none" onclick="irAlPanelDesdeChat()">⚙️</button>
=======
            <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
                <button style="background: #333; color: #0dcaf0; border: 1px solid #555; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-weight: bold; touch-action: manipulation;" onclick="volverAlLobbyDeSalas()">< Volver a las Salas</button>
                <h3 id="welcome-msg" style="margin: 0;">Conectado</h3>
                <span id="current-room-indicator" style="background: #0d6efd; color: white; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: bold;">Sala</span>
            </div>
            <div style="display: flex; align-items: center; gap: 15px; flex-wrap: wrap;">
                <button id="btn-go-admin" style="background: #ffc107; color: black; padding: 10px 18px; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; touch-action: manipulation;" class="d-none" onclick="irAlPanelDesdeChat()">Ir al panel de administrador</button>
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
                
                <div class="profile-menu-container" id="profile-trigger" onclick="toggleProfileDropdown(event)">
                    <span class="profile-text-link">Perfil</span>
                    <div id="profile-avatar-slot"></div>
                    
                    <div class="profile-dropdown-list" id="profile-dropdown">
<<<<<<< HEAD
                        <div class="profile-dropdown-item" style="font-size:11px; color:#666; pointer-events: none;" id="dropdown-user-info">Usuario</div>
=======
                        <div class="profile-dropdown-item" style="font-size:12px; color:#666; pointer-events: none;" id="dropdown-user-info">Usuario</div>
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
                        <div class="profile-dropdown-divider"></div>
                        
                        <div class="profile-dropdown-item" onclick="toggleSubmenu(event, 'submenu-nick')">
                            <span>Nick</span> <span>▶</span>
                        </div>
                        <div id="submenu-nick" class="profile-submenu-panel" onclick="event.stopPropagation()">
                            <span class="submenu-title">Estilo del Nick</span>
                            <div class="submenu-grid">
                                <div class="submenu-field">
                                    <span>Fuente:</span>
                                    <select id="nick-font-select" class="submenu-select">
                                        <option value="Arial">Arial</option>
                                        <option value="Courier New">Courier New</option>
                                        <option value="Consolas">Consolas</option>
                                    </select>
                                </div>
                                <div class="submenu-field">
                                    <span>Tamaño:</span>
                                    <select id="nick-size-select" class="submenu-select">
                                        <option value="15px" selected>Normal</option>
                                        <option value="18px">Grande</option>
                                    </select>
                                </div>
                                <div class="submenu-field">
                                    <span>Color:</span>
                                    <select id="nick-color-select" class="submenu-select">
                                        <option value="default">Por defecto</option>
                                        <option value="#ff5722">Naranja</option>
                                        <option value="#00bcd4">Cian</option>
                                    </select>
                                </div>
                            </div>
                        </div>

                        <div class="profile-dropdown-item" onclick="toggleSubmenu(event, 'submenu-letra')">
                            <span>Letra</span> <span>▶</span>
                        </div>
                        <div id="submenu-letra" class="profile-submenu-panel" onclick="event.stopPropagation()">
                            <span class="submenu-title">Estilo del Mensaje</span>
                            <div class="submenu-grid">
                                <div class="submenu-field">
                                    <span>Fuente:</span>
                                    <select id="msg-font-select" class="submenu-select">
                                        <option value="Arial">Arial</option>
                                        <option value="Georgia">Georgia</option>
                                    </select>
                                </div>
                                <div class="submenu-field">
                                    <span>Tamaño:</span>
                                    <select id="msg-size-select" class="submenu-select">
                                        <option value="14px" selected>Normal</option>
                                        <option value="17px">Grande</option>
                                    </select>
                                </div>
                                <div class="submenu-field">
                                    <span>Color:</span>
                                    <select id="msg-color-select" class="submenu-select">
                                        <option value="white">Blanco</option>
                                        <option value="yellow">Amarillo</option>
                                        <option value="#0dcaf0">Celeste</option>
                                    </select>
                                </div>
                            </div>
                        </div>

                        <div class="profile-dropdown-item" onclick="abrirModalAvatar(event)">
                            <span>Agregar Avatar</span> <span style="font-size: 11px; color: #0dcaf0;">📷</span>
                        </div>
                        <div class="profile-dropdown-divider"></div>
                        <div class="profile-dropdown-item" style="color: #dc3545; touch-action: manipulation;" onclick="location.reload()">Cerrar Sesión</div>
                    </div>
                </div>
            </div>
        </div>

        <div class="chat-layout">
            <div class="main-chat">
                <div id="chat-box"></div>
                <div id="emoji-mart-floating-picker"></div>

                <div id="media-floating-modal" class="media-modal">
                    <div class="media-modal-tabs">
                        <button id="media-tab-gif" class="media-tab-btn active" onclick="switchMediaTab('gif')">GIFs</button>
                        <button id="media-tab-sticker" class="media-tab-btn" onclick="switchMediaTab('sticker')">Stickers</button>
                    </div>
                    <div id="search-container-gif" class="search-row">
<<<<<<< HEAD
                        <input type="text" id="media-search-gif" class="search-control" placeholder="Buscar GIF..." oninput="filtrarMedia('gif')">
                    </div>
                    <div id="search-container-sticker" class="search-row d-none">
                        <input type="text" id="media-search-sticker" class="search-control" placeholder="Buscar Sticker..." oninput="filtrarMedia('sticker')">
=======
                        <input type="text" id="media-search-gif" class="search-control" placeholder="Buscar GIF por nombre..." oninput="filtrarMedia('gif')">
                    </div>
                    <div id="search-container-sticker" class="search-row d-none">
                        <input type="text" id="media-search-sticker" class="search-control" placeholder="Buscar Sticker por nombre..." oninput="filtrarMedia('sticker')">
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
                    </div>
                    <div id="grid-container-gif" class="media-grid-container">
                        <div id="media-items-gif" class="media-grid"></div>
                    </div>
                    <div id="grid-container-sticker" class="media-grid-container d-none">
                        <div id="media-items-sticker" class="media-grid"></div>
                    </div>
                </div>

                <div class="controls-row">
<<<<<<< HEAD
                    <button style="background: #2d2d2d; color: #ffc107; border: 1px solid #444; border-radius: 4px; padding: 0 12px; cursor: pointer; font-size: 16px; font-weight: bold; touch-action: manipulation; min-height:38px;" onclick="toggleEmojiPicker(event)">😀</button>
                    <button style="background: #2d2d2d; color: #0dcaf0; border: 1px solid #444; border-radius: 4px; padding: 0 12px; cursor: pointer; font-size: 14px; font-weight: bold; touch-action: manipulation; min-height:38px;" onclick="toggleMediaModal(event)">🖼️</button>
                    
                    <input type="text" id="message-input" class="input-control flex-grow" placeholder="Escribí un mensaje..." onkeypress="if(event.key==='Enter') enviarMensaje()">
                    <button class="btn-enviar" style="background: #198754; color: white; padding: 0 18px; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; touch-action: manipulation; min-height:38px; font-size:13px;" onclick="enviarMensaje()">Enviar</button>
=======
                    <button style="background: #2d2d2d; color: #ffc107; border: 1px solid #444; border-radius: 4px; padding: 0 15px; cursor: pointer; font-size: 18px; font-weight: bold; touch-action: manipulation;" onclick="toggleEmojiPicker(event)">😀</button>
                    <button style="background: #2d2d2d; color: #0dcaf0; border: 1px solid #444; border-radius: 4px; padding: 0 15px; cursor: pointer; font-size: 16px; font-weight: bold; touch-action: manipulation;" onclick="toggleMediaModal(event)">🖼️</button>
                    
                    <input type="text" id="message-input" class="input-control flex-grow" placeholder="Escribí un mensaje..." onkeypress="if(event.key==='Enter') enviarMensaje()">
                    <button class="btn-enviar" style="background: #198754; color: white; padding: 0 25px; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; touch-action: manipulation;" onclick="enviarMensaje()">Enviar</button>
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
                </div>
            </div>

            <div class="toggle-divider-zone">
                <button id="toggle-panel-btn" onclick="toggleSidePanel()">▶</button>
            </div>

            <div class="side-users" id="side-panel-users">
                <div class="side-users-inner">
<<<<<<< HEAD
                    <h4 style="margin-top: 0; margin-bottom: 10px; border-bottom: 1px solid #333; padding-bottom: 4px; font-size:14px;">Conectados</h4>
=======
                    <h4 style="margin-top: 0; margin-bottom: 15px; border-bottom: 1px solid #333; padding-bottom: 5px;">Conectados</h4>
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
                    <div id="lista-usuarios"></div>
                </div>
            </div>
        </div>
    </div>

<<<<<<< HEAD
    <!-- AVATAR MODAL -->
    <div id="avatar-upload-modal" class="avatar-upload-modal">
        <h4 style="margin-top: 0; margin-bottom: 10px; text-align: center; color: #0dcaf0; font-size:16px;">Configurar Avatar</h4>
        <div class="form-group">
            <label style="font-size: 12px; color: #aaa;">URL de tu imagen:</label>
            <input type="text" id="avatar-url-input" class="input-control" placeholder="https://ejemplo.com/avatar.png" oninput="vistaPreviaAvatarUrl()">
            <small style="color: #666; font-size: 10px; display: block; margin-top: 4px;">Formatos: PNG, JPG, JPEG, GIF, BMP, WEBP, SVG</small>
        </div>
        <div style="text-align: center;">
            <img id="avatar-preview-img" src="" class="avatar-preview-box" style="display: none;">
            <p id="avatar-preview-text" style="color: #666; font-size: 12px;">Pegá una URL para previsualizar</p>
        </div>
        <div style="display: flex; gap: 10px; margin-top: 15px;">
            <button style="flex: 1; background: #2d2d2d; color: white; border: 1px solid #444; padding: 8px; border-radius: 4px; cursor: pointer; touch-action: manipulation; font-size:13px;" onclick="cerrarModalAvatar()">Cancelar</button>
            <button style="flex: 1; background: #198754; color: white; border: none; padding: 8px; border-radius: 4px; font-weight: bold; cursor: pointer; touch-action: manipulation; font-size:13px;" onclick="guardarAvatarPropio()">Guardar</button>
=======
    <!-- AVATAR MODAL (SOLO URL) -->
    <div id="avatar-upload-modal" class="avatar-upload-modal">
        <h4 style="margin-top: 0; margin-bottom: 10px; text-align: center; color: #0dcaf0;">Configurar mi Avatar</h4>
        <div class="form-group">
            <label style="font-size: 12px; color: #aaa;">Pegá la URL de tu imagen:</label>
            <input type="text" id="avatar-url-input" class="input-control" placeholder="https://ejemplo.com/mi-avatar.png" oninput="vistaPreviaAvatarUrl()" style="font-size: 14px;">
            <small style="color: #666; font-size: 11px; display: block; margin-top: 4px;">Formatos: PNG, JPG, JPEG, GIF, BMP, WEBP, SVG</small>
        </div>
        <div style="text-align: center;">
            <img id="avatar-preview-img" src="" class="avatar-preview-box" style="display: none;">
            <p id="avatar-preview-text" style="color: #666; font-size: 13px;">Pegá una URL para ver la previsualización</p>
        </div>
        <div style="display: flex; gap: 10px; margin-top: 15px;">
            <button style="flex: 1; background: #2d2d2d; color: white; border: 1px solid #444; padding: 8px; border-radius: 4px; cursor: pointer; touch-action: manipulation;" onclick="cerrarModalAvatar()">Cancelar</button>
            <button style="flex: 1; background: #198754; color: white; border: none; padding: 8px; border-radius: 4px; font-weight: bold; cursor: pointer; touch-action: manipulation;" onclick="guardarAvatarPropio()">Guardar</button>
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
        </div>
    </div>

    <!-- ADMIN SECTION -->
    <div id="admin-section" class="d-none">
        <div class="admin-box">
            <div class="admin-nav">
<<<<<<< HEAD
                <h2 style="margin: 0; font-size:18px;">⚙️ Panel de Control - CORECHAT</h2>
                <div class="admin-nav-buttons">
                    <button id="btn-admin-view-chat" style="background: #0d6efd; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; touch-action: manipulation; font-size:13px;" onclick="irAlLobbyDesdePanel()">Salas</button>
                    <button style="background: #dc3545; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; touch-action: manipulation; font-size:13px;" onclick="location.reload()">Salir</button>
=======
                <h2 style="margin: 0;">Panel de Control</h2>
                <div class="admin-nav-buttons">
                    <button id="btn-admin-view-chat" style="background: #0d6efd; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; touch-action: manipulation;" onclick="irAlLobbyDesdePanel()">Ir a las salas</button>
                    <button style="background: #dc3545; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; touch-action: manipulation;" onclick="location.reload()">Cerrar Sesión</button>
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
                </div>
            </div>

            <div class="tabs-header">
                <button id="admin-tab-users" class="tab-btn active" onclick="switchAdminTab('users')">Usuarios</button>
                <button id="admin-tab-rooms" class="tab-btn" onclick="switchAdminTab('rooms')">Salas</button>
<<<<<<< HEAD
                <button id="admin-tab-stickers" class="tab-btn" onclick="switchAdminTab('stickers')">GIFs</button>
=======
                <button id="admin-tab-stickers" class="tab-btn" onclick="switchAdminTab('stickers')">GIFs/Stickers</button>
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
                <button id="admin-tab-connection" class="tab-btn" style="color:#0dcaf0;" onclick="switchAdminTab('connection')">🔌 DB</button>
            </div>

            <div id="admin-panel-users">
<<<<<<< HEAD
                <button id="btn-toggle-visibilidad" class="btn-visibilidad" onclick="cambiarVisibilidadAdminWeb()">Cargando...</button>
                <div id="admin-current-room-status" style="margin-bottom: 12px; color: #0dcaf0; font-weight: bold; font-size: 13px;">
                    Posición: <span id="admin-room-label" style="color: #ffc107;">Fuera</span>
                </div>

                <h3 style="font-size:15px;">Crear Usuario</h3>
                <div class="form-inline-admin" style="margin-bottom: 20px;">
                    <div style="flex: 1; min-width: 120px;">
                        <input type="text" id="adm-u-name" class="input-control" placeholder="Nombre" style="font-size:13px; padding:8px;">
                    </div>
                    <div style="flex: 1; min-width: 120px;">
                        <input type="text" id="adm-u-pass" class="input-control" placeholder="Contraseña" style="font-size:13px; padding:8px;">
                    </div>
                    <div style="flex: 1; min-width: 100px;">
                        <select id="adm-u-rol" class="input-control" style="font-size:13px; padding:8px;">
=======
                <button id="btn-toggle-visibilidad" class="btn-visibilidad" onclick="cambiarVisibilidadAdminWeb()">Cargando Modo...</button>
                <div id="admin-current-room-status" style="margin-bottom: 15px; color: #0dcaf0; font-weight: bold; font-size: 14px;">
                    Posición actual del Administrador: <span id="admin-room-label" style="color: #ffc107;">Fuera de las salas</span>
                </div>

                <h3>Crear Usuario Nuevo</h3>
                <div class="form-inline-admin" style="margin-bottom: 25px;">
                    <div style="flex: 1; min-width: 140px;">
                        <input type="text" id="adm-u-name" class="input-control" placeholder="Nombre">
                    </div>
                    <div style="flex: 1; min-width: 140px;">
                        <input type="text" id="adm-u-pass" class="input-control" placeholder="Contraseña">
                    </div>
                    <div style="flex: 1; min-width: 120px;">
                        <select id="adm-u-rol" class="input-control">
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
                            <option value="user">User</option>
                            <option value="mod">Mod</option>
                            <option value="admin">Admin</option>
                        </select>
                    </div>
<<<<<<< HEAD
                    <div style="flex: 1; min-width: 100px;">
                        <select id="adm-u-gender" class="input-control" style="font-size:13px; padding:8px;">
=======
                    <div style="flex: 1; min-width: 120px;">
                        <select id="adm-u-gender" class="input-control">
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
                            <option value="hombre">Hombre</option>
                            <option value="mujer">Mujer</option>
                        </select>
                    </div>
<<<<<<< HEAD
                    <button style="background: #198754; color: white; border:none; padding:8px 16px; border-radius:4px; font-weight:bold; cursor:pointer; touch-action: manipulation; font-size:13px;" onclick="crearUsuarioDesdeAdmin()">Agregar</button>
                </div>

                <h3 style="font-size:15px;">Listado de Cuentas</h3>
=======
                    <button style="background: #198754; color: white; border:none; padding:10px 20px; border-radius:4px; font-weight:bold; cursor:pointer; touch-action: manipulation;" onclick="crearUsuarioDesdeAdmin()">Agregar</button>
                </div>

                <h3>Listado de Cuentas del Servidor</h3>
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
                <div style="width: 100%; overflow-x: auto;" class="table-responsive">
                    <table>
                        <thead>
                            <tr>
                                <th>Red</th>
                                <th>ID</th>
                                <th>Nick</th>
                                <th>Pass</th>
                                <th>Rol</th>
                                <th>Estado</th>
                                <th>Género</th>
<<<<<<< HEAD
                                <th style="min-width: 280px;">Acciones</th>
=======
                                <th style="min-width: 320px;">Acciones</th>
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
                            </tr>
                        </thead>
                        <tbody id="tabla-adm-usuarios"></tbody>
                    </table>
                </div>
            </div>

            <div id="admin-panel-rooms" class="d-none">
<<<<<<< HEAD
                <h3 style="font-size:15px;">Crear Nueva Sala</h3>
                <div class="form-inline-admin" style="margin-bottom: 20px;">
                    <div style="flex: 2; min-width: 140px;">
                        <label style="font-size:11px; color:#aaa; display:block; margin-bottom:2px;">Nombre:</label>
                        <input type="text" id="adm-r-name" class="input-control" placeholder="Sala de Juegos" style="font-size:13px; padding:8px;">
                    </div>
                    <div style="flex: 1; min-width: 60px;">
                        <label style="font-size:11px; color:#aaa; display:block; margin-bottom:2px;">Ícono:</label>
                        <input type="text" id="adm-r-icon" class="input-control" placeholder="🎮" maxlength="4" style="font-size:13px; padding:8px;">
                    </div>
                    <div style="flex: 1; min-width: 100px;">
                        <label style="font-size:11px; color:#aaa; display:block; margin-bottom:2px;">Límite (Máx 150):</label>
                        <input type="number" id="adm-r-limit" class="input-control" value="150" min="1" max="150" style="font-size:13px; padding:8px;">
                    </div>
                    <button style="background: #198754; color: white; border:none; padding:8px 16px; border-radius:4px; font-weight:bold; cursor:pointer; touch-action: manipulation; font-size:13px;" onclick="crearSalaDesdeAdmin()">Crear</button>
                </div>

                <h3 style="font-size:15px;">Salas Registradas</h3>
=======
                <h3>Crear Nueva Sala de Chat</h3>
                <div class="form-inline-admin" style="margin-bottom: 25px;">
                    <div style="flex: 2; min-width: 180px;">
                        <label style="font-size:12px; color:#aaa; display:block; margin-bottom:2px;">Nombre de Sala:</label>
                        <input type="text" id="adm-r-name" class="input-control" placeholder="Ej: Sala de Juegos">
                    </div>
                    <div style="flex: 1; min-width: 90px;">
                        <label style="font-size:12px; color:#aaa; display:block; margin-bottom:2px;">Ícono (Emoji):</label>
                        <input type="text" id="adm-r-icon" class="input-control" placeholder="🎮" maxlength="4">
                    </div>
                    <div style="flex: 1; min-width: 140px;">
                        <label style="font-size:12px; color:#aaa; display:block; margin-bottom:2px;">Límite Usuarios (Máx 150):</label>
                        <input type="number" id="adm-r-limit" class="input-control" value="150" min="1" max="150">
                    </div>
                    <button style="background: #198754; color: white; border:none; padding:10px 20px; border-radius:4px; font-weight:bold; cursor:pointer; touch-action: manipulation;" onclick="crearSalaDesdeAdmin()">Crear Sala</button>
                </div>

                <h3>Salas de Chat Registradas</h3>
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
                <div class="table-responsive">
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Ícono</th>
<<<<<<< HEAD
                                <th>Nombre</th>
                                <th>Límite</th>
                                <th>Operación</th>
=======
                                <th>Nombre de Sala</th>
                                <th>Límite de Capacidad</th>
                                <th>Operaciones</th>
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
                            </tr>
                        </thead>
                        <tbody id="tabla-adm-salas"></tbody>
                    </table>
                </div>
            </div>

            <div id="admin-panel-stickers" class="d-none">
<<<<<<< HEAD
                <h3 style="font-size:15px;">Añadir Multimedia</h3>
                <div class="form-inline-admin" style="margin-bottom: 20px;">
                    <div style="flex: 1; min-width: 120px;">
                        <input type="text" id="adm-s-name" class="input-control" placeholder="Nombre" style="font-size:13px; padding:8px;">
                    </div>
                    <div style="flex: 2; min-width: 180px;">
                        <input type="text" id="adm-s-url" class="input-control" placeholder="https://.../imagen.gif" style="font-size:13px; padding:8px;">
                    </div>
                    <div style="flex: 1; min-width: 100px;">
                        <select id="adm-s-tipo" class="input-control" style="font-size:13px; padding:8px;">
=======
                <h3>Añadir Nuevo Contenido Multimedia</h3>
                <div class="form-inline-admin" style="margin-bottom: 25px;">
                    <div style="flex: 1; min-width: 150px;">
                        <input type="text" id="adm-s-name" class="input-control" placeholder="Ej: Messi saludo">
                    </div>
                    <div style="flex: 2; min-width: 220px;">
                        <input type="text" id="adm-s-url" class="input-control" placeholder="https://.../imagen.gif">
                    </div>
                    <div style="flex: 1; min-width: 130px;">
                        <select id="adm-s-tipo" class="input-control">
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
                            <option value="sticker">Sticker</option>
                            <option value="gif">GIF</option>
                        </select>
                    </div>
<<<<<<< HEAD
                    <button style="background: #198754; color: white; border:none; padding:8px 16px; border-radius:4px; font-weight:bold; cursor:pointer; touch-action: manipulation; font-size:13px;" onclick="crearStickerDesdeAdmin()">Guardar</button>
                </div>

                <h3 style="font-size:15px;">Galería</h3>
=======
                    <button style="background: #198754; color: white; border:none; padding:10px 20px; border-radius:4px; font-weight:bold; cursor:pointer; touch-action: manipulation;" onclick="crearStickerDesdeAdmin()">Guardar Item</button>
                </div>

                <h3>Galería de Elementos Registrados</h3>
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
                <div class="table-responsive">
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Nombre</th>
                                <th>Tipo</th>
<<<<<<< HEAD
                                <th>Vista</th>
                                <th>URL</th>
=======
                                <th>Previsualización</th>
                                <th>URL Absoluta</th>
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
                                <th>Operación</th>
                            </tr>
                        </thead>
                        <tbody id="tabla-adm-stickers"></tbody>
                    </table>
                </div>
            </div>

            <div id="admin-panel-connection" class="d-none">
<<<<<<< HEAD
                <h3 style="font-size:15px;">Configuración de Base de Datos</h3>
                <p style="color: #aaa; font-size: 13px; max-width: 700px;">
                    Modo <strong>Local</strong> (SQLite) o <strong>Online</strong> (PostgreSQL en la nube).
                </p>

                <div id="db-status-container" class="db-status-banner status-local-mode">
                    <div>Estado: <span id="lbl-motor-actual">SQLITE LOCAL</span></div>
=======
                <h3>Conectividad del Servidor de Base de Datos</h3>
                <p style="color: #aaa; font-size: 14px; max-width: 700px;">
                    Podés configurar este sistema para que corra de modo <strong>Local</strong> (guardando todo en el archivo local de la PC) o de modo <strong>Online</strong> (conectándose en la nube mediante un servidor remoto PostgreSQL como Supabase, Render o Railway).
                </p>

                <div id="db-status-container" class="db-status-banner status-local-mode">
                    <div>Estado Actual: <span id="lbl-motor-actual">SQLITE LOCAL</span></div>
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
                </div>

                <div class="form-db-config">
                    <div class="form-group">
<<<<<<< HEAD
                        <label style="font-size:12px;">Motor Activo:</label>
                        <select id="cfg-db-motor" class="input-control" onchange="alternarVisibilidadCamposNube()" style="font-size:13px; padding:8px;">
                            <option value="sqlite">Local (SQLite)</option>
                            <option value="postgres">Online (PostgreSQL)</option>
=======
                        <label>Seleccionar Motor Activo:</label>
                        <select id="cfg-db-motor" class="input-control" onchange="alternarVisibilidadCamposNube()">
                            <option value="sqlite">Local (SQLite - Archivo Interno)</option>
                            <option value="postgres">Online Remoto (PostgreSQL - Servidor en la nube)</option>
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
                        </select>
                    </div>

                    <div id="panel-campos-nube" class="d-none">
                        <div class="form-group">
<<<<<<< HEAD
                            <label style="font-size:12px;">Host Remoto:</label>
                            <input type="text" id="cfg-db-host" class="input-control" placeholder="ej: aws-0-us-east-1.pooler.supabase.com" style="font-size:13px; padding:8px;">
                        </div>
                        <div style="display: flex; gap:10px; flex-wrap:wrap;">
                            <div class="form-group" style="flex:1; min-width:120px;">
                                <label style="font-size:12px;">Base de Datos:</label>
                                <input type="text" id="cfg-db-name" class="input-control" placeholder="postgres" style="font-size:13px; padding:8px;">
                            </div>
                            <div class="form-group" style="flex:1; min-width:80px;">
                                <label style="font-size:12px;">Puerto:</label>
                                <input type="text" id="cfg-db-port" class="input-control" placeholder="5432" value="5432" style="font-size:13px; padding:8px;">
                            </div>
                        </div>
                        <div style="display: flex; gap:10px; flex-wrap:wrap;">
                            <div class="form-group" style="flex:1; min-width:120px;">
                                <label style="font-size:12px;">Usuario:</label>
                                <input type="text" id="cfg-db-user" class="input-control" placeholder="postgres.tu_id" style="font-size:13px; padding:8px;">
                            </div>
                            <div class="form-group" style="flex:1; min-width:120px;">
                                <label style="font-size:12px;">Contraseña:</label>
                                <input type="password" id="cfg-db-pass" class="input-control" placeholder="Tu contraseña" style="font-size:13px; padding:8px;">
=======
                            <label>Host Remoto (Servidor / Endpoint):</label>
                            <input type="text" id="cfg-db-host" class="input-control" placeholder="ej: aws-0-us-east-1.pooler.supabase.com">
                        </div>
                        <div style="display: flex; gap:10px;">
                            <div class="form-group" style="flex:1;">
                                <label>Base de Datos Name:</label>
                                <input type="text" id="cfg-db-name" class="input-control" placeholder="postgres">
                            </div>
                            <div class="form-group" style="flex:1;">
                                <label>Puerto (Port):</label>
                                <input type="text" id="cfg-db-port" class="input-control" placeholder="5432" value="5432">
                            </div>
                        </div>
                        <div style="display: flex; gap:10px;">
                            <div class="form-group" style="flex:1;">
                                <label>Usuario (User):</label>
                                <input type="text" id="cfg-db-user" class="input-control" placeholder="postgres.tu_id">
                            </div>
                            <div class="form-group" style="flex:1;">
                                <label>Contraseña (Password):</label>
                                <input type="password" id="cfg-db-pass" class="input-control" placeholder="Tu Contraseña de la Nube">
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
                            </div>
                        </div>
                    </div>

<<<<<<< HEAD
                    <button style="background: #0dcaf0; color: black; border: none; padding: 10px 20px; border-radius: 4px; font-weight: bold; cursor: pointer; touch-action: manipulation; margin-top: 10px; font-size:14px;" onclick="guardarConfiguracionConexionMecanismo()">
                        💾 Guardar Cambios
=======
                    <button style="background: #0dcaf0; color: black; border: none; padding: 12px 25px; border-radius: 4px; font-weight: bold; cursor: pointer; touch-action: manipulation; margin-top: 10px;" onclick="guardarConfiguracionConexionMecanismo()">
                        💾 Guardar y Aplicar Cambios
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
                    </button>
                </div>
            </div>

        </div>
    </div>

    <script>
        let socket = null;
        let currentUser = "";
        let currentRol = "";
        let currentGenero = "hombre";
        let currentAvatar = "";
        let isRegisterMode = false;
        let currentSalaName = null;
        let adminRoomPos = null; 
        
        let cacheMediaLocal = [];
        let cacheUltimaListaUsuarios = [];
        let localMutedUsernames = new Set();
        let targetMenuUsername = null;

        document.addEventListener("DOMContentLoaded", function() {
            const pickerOptions = {
                set: 'apple', theme: 'dark', locale: 'es',
                onEmojiSelect: function(emoji) {
                    let input = document.getElementById("message-input");
                    input.value += emoji.native;
                    input.focus();
                }
            };
            const picker = new EmojiMart.Picker(pickerOptions);
            document.getElementById("emoji-mart-floating-picker").appendChild(picker);
            
<<<<<<< HEAD
=======
            // === DETECCIÓN DE DISPOSITIVO ===
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
            function esCelular() {
                return window.innerWidth <= 768 || 
                       /Android|iPhone|iPad|iPod|BlackBerry|Opera Mini|IEMobile/i.test(navigator.userAgent);
            }

            if (esCelular()) {
                const mobileHeader = document.getElementById('mobile-header');
                if (mobileHeader) mobileHeader.style.display = 'block';
                
                const toggleUsersBtn = document.getElementById('mobile-toggle-users');
                if (toggleUsersBtn) {
                    toggleUsersBtn.addEventListener('click', function(e) {
                        e.stopPropagation();
                        const panel = document.getElementById('side-panel-users');
                        if (panel) {
                            panel.classList.toggle('mobile-visible');
                        }
                    });
                }
                
                const backLobbyBtn = document.getElementById('mobile-back-lobby');
                if (backLobbyBtn) {
                    backLobbyBtn.addEventListener('click', function() {
                        volverAlLobbyDeSalas();
                    });
                }
                
                const goAdminBtn = document.getElementById('mobile-go-admin');
                if (goAdminBtn) {
                    goAdminBtn.addEventListener('click', function() {
                        irAlPanelDesdeChat();
                    });
                }
            }
        });

        function actualizarNombreSalaMobile(nombreSala) {
            const roomName = document.getElementById('mobile-room-name');
            if (roomName) {
<<<<<<< HEAD
                roomName.textContent = '💬 ' + (nombreSala || 'CORECHAT');
=======
                roomName.textContent = '💬 ' + (nombreSala || 'Chat');
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
            }
        }

        function actualizarBotonesMobile() {
            const goAdminBtn = document.getElementById('mobile-go-admin');
            if (goAdminBtn) {
                if (currentRol === 'admin') {
                    goAdminBtn.classList.remove('d-none');
                } else {
                    goAdminBtn.classList.add('d-none');
                }
            }
        }

        function toggleEmojiPicker(e) {
            e.stopPropagation();
            document.getElementById("media-floating-modal").style.display = "none";
            let pickerDiv = document.getElementById("emoji-mart-floating-picker");
            pickerDiv.style.display = (pickerDiv.style.display === "block") ? "none" : "block";
        }

        function toggleMediaModal(e) {
            e.stopPropagation();
            document.getElementById("emoji-mart-floating-picker").style.display = "none";
            let modal = document.getElementById("media-floating-modal");
            modal.style.display = (modal.style.display === "block") ? "none" : "block";
            if(modal.style.display === "block") cargarYRenderizarMediaMecanismo();
        }

        function toggleAuthMode() {
            isRegisterMode = !isRegisterMode;
            let title = document.getElementById("auth-title");
            let btnLogin = document.getElementById("btn-login");
            let btnToggle = document.getElementById("btn-toggle-auth");
            let genderGroup = document.getElementById("gender-group");

            if (isRegisterMode) {
<<<<<<< HEAD
                title.innerText = "💬 CORECHAT - Registro";
=======
                title.innerText = "Registrar Nueva Cuenta";
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
                btnLogin.innerText = "Completar Registro";
                btnToggle.innerText = "¿Ya tenés cuenta? Iniciá sesión acá";
                genderGroup.classList.remove("d-none");
            } else {
<<<<<<< HEAD
                title.innerText = "💬 CORECHAT";
=======
                title.innerText = "Iniciar Sesión";
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
                btnLogin.innerText = "Ingresar al Sistema";
                btnToggle.innerText = "¿No tenés cuenta? Registrate acá";
                genderGroup.classList.add("d-none");
            }
        }

        function procesarAutenticacion() {
            let u = document.getElementById("username").value;
            let p = document.getElementById("password").value;
            let g = document.getElementById("gender").value;

            if (!u || !p) { alert("Por favor completá los datos."); return; }

            let endpoint = isRegisterMode ? '/api/registro' : '/api/login';
            let payload = isRegisterMode ? { username: u, password: p, genero: g } : { username: u, password: p };

            fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
            .then(r => r.json())
            .then(data => {
                if (!data.success) { alert(data.message || "Ocurrió un error."); return; }
                if (isRegisterMode) {
                    alert("¡Registro Exitoso!");
                    toggleAuthMode();
                } else {
                    currentUser = data.username;
                    currentRol = data.rol;
                    currentGenero = data.genero;
                    currentAvatar = data.avatar || "";
                    
                    inicializarEntornoChat();
                    document.getElementById("auth-section").classList.add("d-none");
                    
                    actualizarBotonesMobile();
                    
                    if (currentRol === 'admin') {
                        document.getElementById("btn-go-admin-lobby").classList.remove("d-none");
                        document.getElementById("btn-go-admin").classList.remove("d-none");
                        document.getElementById("mobile-go-admin").classList.remove("d-none");
                    } else {
                        document.getElementById("btn-go-admin-lobby").classList.add("d-none");
                        document.getElementById("btn-go-admin").classList.add("d-none");
                        document.getElementById("mobile-go-admin").classList.add("d-none");
                    }
                    
                    solicitarYRenderizarLobbySalas();
                }
<<<<<<< HEAD
            })
            .catch(err => {
                alert("Error de conexión al servidor. Reintentando...");
                console.error(err);
=======
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
            });
        }

        function solicitarYRenderizarLobbySalas() {
            document.getElementById("chat-section").classList.add("d-none");
            document.getElementById("admin-section").classList.add("d-none");
            document.getElementById("lobby-section").classList.remove("d-none");
            actualizarNombreSalaMobile('Lobby');
            
            fetch('/api/salas/list')
            .then(r => r.json())
            .then(salas => {
                let grid = document.getElementById("contenedor-salas-grid");
                grid.innerHTML = "";
                salas.forEach(s => {
                    let card = document.createElement("div");
                    card.className = "sala-card";
                    card.onclick = function() { entrarASalaMecanismo(s.nombre); };
                    card.innerHTML = `
                        <span class="sala-icon">${s.icono}</span>
                        <div class="sala-name">${s.nombre}</div>
                        <div class="sala-count">Usuarios: ${s.conectados} / ${s.limite}</div>
                    `;
                    grid.appendChild(card);
                });
<<<<<<< HEAD
            })
            .catch(err => {
                console.error("Error cargando salas:", err);
                alert("Error al cargar las salas. Reintentando...");
=======
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
            });
        }

        function entrarASalaMecanismo(nombreSala) {
            if (socket && socket.connected) {
                socket.emit('cambiar_sala', { sala: nombreSala });
                actualizarNombreSalaMobile(nombreSala);
<<<<<<< HEAD
            } else {
                alert("No estás conectado al servidor. Reintentando...");
                if (socket) socket.connect();
=======
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
            }
        }

        function volverAlLobbyDeSalas() { 
            solicitarYRenderizarLobbySalas(); 
            actualizarNombreSalaMobile('Lobby');
        }

        function inicializarEntornoChat() {
            let tagRango = obtenerLoguitoRango(currentRol);
            document.getElementById("welcome-msg").innerHTML = `Usuario: <strong>${currentUser}</strong>${tagRango}`;
            document.getElementById("dropdown-user-info").innerText = `@${currentUser} (${currentRol.toUpperCase()})`;
            renderizarSlotAvatarCabecera();

            if (currentRol === 'admin') {
                document.getElementById("btn-go-admin").classList.remove("d-none");
                document.getElementById("btn-go-admin-lobby").classList.remove("d-none");
                document.getElementById("mobile-go-admin").classList.remove("d-none");
            } else {
                document.getElementById("btn-go-admin").classList.add("d-none");
                document.getElementById("btn-go-admin-lobby").classList.add("d-none");
                document.getElementById("mobile-go-admin").classList.add("d-none");
            }

            socket = io({
                reconnection: true,
                reconnectionAttempts: 15,
                reconnectionDelay: 1000,
                reconnectionDelayMax: 5000,
                transports: ['websocket', 'polling'],
                timeout: 20000
            });
            
            socket.on('connect', function() {
<<<<<<< HEAD
                console.log('✅ Conectado al servidor CORECHAT');
=======
                console.log('✅ Conectado al servidor Socket.IO');
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
                socket.emit('join_chat', { username: currentUser });
            });

            socket.on('connect_error', function(error) {
                console.error('❌ Error de conexión Socket.IO:', error);
                if (socket.io.opts.transports.indexOf('polling') === -1) {
                    socket.io.opts.transports = ['polling', 'websocket'];
                }
            });

            socket.on('disconnect', function() {
                console.log('⚠️ Desconectado del servidor. Reintentando...');
            });

            socket.on('reconnect', function() {
<<<<<<< HEAD
                console.log('✅ Reconectado al servidor CORECHAT.');
=======
                console.log('✅ Reconectado al servidor.');
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
                socket.emit('join_chat', { username: currentUser });
                if (currentSalaName) {
                    socket.emit('cambiar_sala', { sala: currentSalaName });
                }
            });

            socket.on('cambiar_sala_ok', function(data) {
                currentSalaName = data.sala;
                document.getElementById("current-room-indicator").innerText = currentSalaName;
                document.getElementById("chat-box").innerHTML = "";
                document.getElementById("lobby-section").classList.add("d-none");
                document.getElementById("chat-section").classList.remove("d-none");
                actualizarNombreSalaMobile(currentSalaName);
            });

            socket.on('error_sala_llena', function(data) { alert(data.message); });

            socket.on('sala_eliminada_force', function(data) {
                if (currentSalaName === data.sala) {
                    alert("La sala actual ha sido eliminada por el administrador.");
                    currentSalaName = null;
                    solicitarYRenderizarLobbySalas();
                }
            });

            socket.on('sys_msg', function(data) {
                let box = document.getElementById("chat-box");
                let p = document.createElement("p");
                p.style.color = "#888"; p.style.fontSize = "13px"; p.style.margin = "4px 0"; p.style.fontStyle = "italic";
                p.innerText = data.texto;
                box.appendChild(p);
                box.scrollTop = box.scrollHeight;
            });

            socket.on('receive_msg', function(data) {
                if (localMutedUsernames.has(data.sender)) return;
                let box = document.getElementById("chat-box");
                let line = document.createElement("div");
                line.className = "chat-msg-line";

                let avBox = document.createElement("div");
                if (data.avatar) {
                    avBox.innerHTML = `<img src="${data.avatar}" class="msg-avatar-img">`;
                } else {
                    let col = data.genero === 'mujer' ? '#e91e63' : '#0d6efd';
                    let inicial = data.sender.substring(0, 2).toUpperCase();
                    avBox.innerHTML = `<span class="msg-avatar-initials" style="background:${col};">${inicial}</span>`;
                }
                line.appendChild(avBox);

                let nickSpan = document.createElement("span");
                nickSpan.className = "clickable-nick";
                nickSpan.style.fontFamily = data.nick_font || 'Arial';
                nickSpan.style.fontSize = data.nick_size || '15px';
                nickSpan.style.fontWeight = 'bold';
                
                if (data.nick_color && data.nick_color !== 'default') {
                    nickSpan.style.color = data.nick_color;
                } else {
                    if (data.rol === 'admin') nickSpan.style.color = '#ffc107';
                    else if (data.rol === 'mod') nickSpan.style.color = '#0dcaf0';
                    else nickSpan.style.color = '#ffffff';
                }

                nickSpan.innerText = data.sender;
                if (data.sender !== currentUser) {
                    nickSpan.addEventListener('contextmenu', function(e) { abrirMenuContextualPersonalizado(e, data.sender); });
                }
                line.appendChild(nickSpan);

                let rangoLoguito = obtenerLoguitoRango(data.rol);
                if (rangoLoguito) {
                    let rSpan = document.createElement("span"); rSpan.innerHTML = rangoLoguito; line.appendChild(rSpan);
                }

                let sep = document.createElement("span"); sep.innerText = ": "; line.appendChild(sep);

                let textSpan = document.createElement("span");
                textSpan.style.fontFamily = data.msg_font || 'Arial'; textSpan.style.fontSize = data.msg_size || '14px'; textSpan.style.color = data.msg_color || 'white';

                if (data.is_img) {
                    textSpan.innerHTML = `<img src="${data.texto}" class="chat-img-msg">`;
                } else {
                    textSpan.innerText = data.texto;
                }
                
                line.appendChild(textSpan);
                box.appendChild(line);
                twemoji.parse(line, { folder: 'svg', ext: '.svg' });
                box.scrollTop = box.scrollHeight;
            });

            socket.on('receive_private_msg', function(data) {
                let interlocutor = (data.sender === currentUser) ? data.target : data.sender;
                asegurarVentanaPrivadoExistente(interlocutor);
                let pBox = document.getElementById(`p-chat-box-${interlocutor}`);
                if (pBox) {
                    let d = document.createElement("div"); d.style.margin = "4px 0";
                    d.innerHTML = `<strong style="color:${data.sender===currentUser?'#0dcaf0':'#ffc107'}">@${data.sender}:</strong> ${data.texto}`;
                    pBox.appendChild(d);
                    twemoji.parse(d, { folder: 'svg', ext: '.svg' });
                    pBox.scrollTop = pBox.scrollHeight;
                }
            });

            socket.on('update_users', function(usersList) {
                cacheUltimaListaUsuarios = usersList;
                renderizarListaUsuariosConectados(usersList);
                if (document.getElementById("admin-section").classList.contains("d-none") === false) {
                    cargarTablaUsuariosAdmin();
                }
            });

            socket.on('force_action', function(data) {
                if (currentUser === data.target) {
                    if (data.accion === "ban") { alert("Tu cuenta fue baneada del servidor."); location.reload(); }
                    else if (data.accion === "silenciar") { alert("Fuiste silenciado por moderación."); }
                    else if (data.accion === "kick_sala") { alert(`Fuiste pateado de la sala: ${data.sala}`); currentSalaName = null; solicitarYRenderizarLobbySalas(); }
                    else if (data.accion === "rol_change") {
                        if (currentUser !== "Administrador" && data.nuevo_rol) { alert("Tus permisos cambiaron. El sistema se recargará."); location.reload(); }
                    }
                }
            });
        }

        function obtenerLoguitoRango(rol) {
            if (rol === 'admin') return '<span class="badge-admin" title="Administrador">⚡</span>';
            if (rol === 'mod') return '<span class="badge-mod" title="Moderador">🛡️</span>';
            return '';
        }

        function renderizarSlotAvatarCabecera() {
            let slot = document.getElementById("profile-avatar-slot");
            if (currentAvatar) {
                slot.innerHTML = `<img src="${currentAvatar}" class="profile-avatar-img">`;
            } else {
                let col = currentGenero === 'mujer' ? '#e91e63' : '#0d6efd';
                let inicial = currentUser.substring(0,2).toUpperCase();
                slot.innerHTML = `<span class="profile-avatar-initials" style="background:${col};">${inicial}</span>`;
            }
        }

        function toggleSidePanel() {
            let panel = document.getElementById("side-panel-users");
            let btn = document.getElementById("toggle-panel-btn");
            if (panel.classList.contains("collapsed")) {
                panel.classList.remove("collapsed"); btn.innerText = "▶";
            } else {
                panel.classList.add("collapsed"); btn.innerText = "◀";
            }
        }

        function renderizarListaUsuariosConectados(list) {
            let div = document.getElementById("lista-usuarios"); div.innerHTML = "";
            list.forEach(u => {
<<<<<<< HEAD
                let row = document.createElement("div"); row.style.display = "flex"; row.style.alignItems = "center"; row.style.margin = "8px 0";
                let dot = document.createElement("span"); dot.className = "status-dot dot-green"; row.appendChild(dot);

                let av = document.createElement("div"); av.style.marginRight = "6px";
                if (u.avatar) {
                    av.innerHTML = `<img src="${u.avatar}" class="msg-avatar-img" style="width:22px; height:22px; margin:0;">`;
                } else {
                    let col = u.genero === 'mujer' ? '#e91e63' : '#0d6efd';
                    let ini = u.username.substring(0,2).toUpperCase();
                    av.innerHTML = `<span class="msg-avatar-initials" style="width:22px; height:22px; font-size:8px; background:${col}; margin:0;">${ini}</span>`;
=======
                let row = document.createElement("div"); row.style.display = "flex"; row.style.alignItems = "center"; row.style.margin = "10px 0";
                let dot = document.createElement("span"); dot.className = "status-dot dot-green"; row.appendChild(dot);

                let av = document.createElement("div"); av.style.marginRight = "8px";
                if (u.avatar) {
                    av.innerHTML = `<img src="${u.avatar}" class="msg-avatar-img" style="width:26px; height:26px; margin:0;">`;
                } else {
                    let col = u.genero === 'mujer' ? '#e91e63' : '#0d6efd';
                    let ini = u.username.substring(0,2).toUpperCase();
                    av.innerHTML = `<span class="msg-avatar-initials" style="width:26px; height:26px; font-size:9px; background:${col}; margin:0;">${ini}</span>`;
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
                }
                row.appendChild(av);

                let nameSpan = document.createElement("span");
<<<<<<< HEAD
                nameSpan.className = "clickable-nick"; nameSpan.style.fontSize = "13px"; nameSpan.style.fontWeight = "bold";
=======
                nameSpan.className = "clickable-nick"; nameSpan.style.fontSize = "14px"; nameSpan.style.fontWeight = "bold";
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
                if (u.rol === 'admin') nameSpan.style.color = '#ffc107';
                else if (u.rol === 'mod') nameSpan.style.color = '#0dcaf0';
                else nameSpan.style.color = '#eee';
                nameSpan.innerText = u.username;
                
                if (u.username !== currentUser) {
                    nameSpan.addEventListener('contextmenu', function(e) { abrirMenuContextualPersonalizado(e, u.username); });
                }
                row.appendChild(nameSpan); div.appendChild(row);
            });
        }

        function enviarMensaje() {
            let inp = document.getElementById("message-input");
            let txt = inp.value.trim(); if (!txt) return;

            if (socket && socket.connected) {
                socket.emit('send_msg', {
                    texto: txt, is_img: false, genero: currentGenero, avatar: currentAvatar,
                    msg_color: document.getElementById("msg-color-select").value,
                    msg_font: document.getElementById("msg-font-select").value,
                    msg_size: document.getElementById("msg-size-select").value,
                    nick_color: document.getElementById("nick-color-select").value,
                    nick_font: document.getElementById("nick-font-select").value,
                    nick_size: document.getElementById("nick-size-select").value
                });
                inp.value = "";
                document.getElementById("emoji-mart-floating-picker").style.display = "none";
            } else {
                alert("No estás conectado al servidor. Reintentando conexión...");
                if (socket) {
                    socket.connect();
                }
            }
        }

        function cargarYRenderizarMediaMecanismo() {
            fetch('/api/stickers/list').then(r => r.json()).then(data => {
                cacheMediaLocal = data;
                renderizarGrillaEspecifica('gif'); renderizarGrillaEspecifica('sticker');
            });
        }

        function renderizarGrillaEspecifica(tipo, query = '') {
            let gridElement = document.getElementById(`media-items-${tipo}`); gridElement.innerHTML = '';
            let filtrados = cacheMediaLocal.filter(item => item.tipo === tipo && item.nombre.toLowerCase().includes(query.toLowerCase()));

            filtrados.forEach(item => {
                let img = document.createElement("img"); img.src = item.url; img.className = "media-item";
                img.onclick = function() {
                    socket.emit('send_msg', {
                        texto: item.url, is_img: true, genero: currentGenero, avatar: currentAvatar,
                        msg_color: document.getElementById("msg-color-select").value,
                        msg_font: document.getElementById("msg-font-select").value,
                        msg_size: document.getElementById("msg-size-select").value,
                        nick_color: document.getElementById("nick-color-select").value,
                        nick_font: document.getElementById("nick-font-select").value,
                        nick_size: document.getElementById("nick-size-select").value
                    });
                    document.getElementById("media-floating-modal").style.display = "none";
                };
                gridElement.appendChild(img);
            });
        }

        function switchMediaTab(tipoDestino) {
            document.getElementById("media-tab-gif").classList.toggle("active", tipoDestino === 'gif');
            document.getElementById("media-tab-sticker").classList.toggle("active", tipoDestino === 'sticker');
            document.getElementById("search-container-gif").classList.toggle("d-none", tipoDestino !== 'gif');
            document.getElementById("search-container-sticker").classList.toggle("d-none", tipoDestino !== 'sticker');
            document.getElementById("grid-container-gif").classList.toggle("d-none", tipoDestino !== 'gif');
            document.getElementById("grid-container-sticker").classList.toggle("d-none", tipoDestino !== 'sticker');
        }

        function filtrarMedia(tipo) {
            let val = document.getElementById(`media-search-${tipo}`).value;
            renderizarGrillaEspecifica(tipo, val);
        }

        function abrirMenuContextualPersonalizado(e, targetUser) {
            e.preventDefault(); targetMenuUsername = targetUser;
            let menu = document.getElementById("custom-context-menu");
            document.getElementById("context-option-mute").innerText = localMutedUsernames.has(targetUser) ? `Quitar silencio a @${targetUser}` : `Silenciar localmente a @${targetUser}`;
<<<<<<< HEAD
            menu.style.left = Math.min(e.clientX, window.innerWidth - 180) + "px"; 
            menu.style.top = Math.min(e.clientY, window.innerHeight - 100) + "px"; 
            menu.style.display = "block";
=======
            menu.style.left = e.clientX + "px"; menu.style.top = e.clientY + "px"; menu.style.display = "block";
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
        }

        function ejecutarMuteLocal() {
            if (localMutedUsernames.has(targetMenuUsername)) localMutedUsernames.delete(targetMenuUsername);
            else localMutedUsernames.add(targetMenuUsername);
            document.getElementById("custom-context-menu").style.display = "none";
        }

        function abrirVentanaPrivadoDesdeContexto() {
            asegurarVentanaPrivadoExistente(targetMenuUsername);
            document.getElementById("custom-context-menu").style.display = "none";
        }

        function asegurarVentanaPrivadoExistente(targetUser) {
            if (document.getElementById(`private-win-${targetUser}`)) return;
            let win = document.createElement("div"); win.id = `private-win-${targetUser}`; win.className = "private-chat-window";
            let total = document.querySelectorAll(".private-chat-window").length;
            let rightOffset = 310 + (total * 340);
            if (window.innerWidth <= 768) {
                rightOffset = 10 + (total * 10);
<<<<<<< HEAD
                win.style.left = "3%";
                win.style.right = "3%";
=======
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
            }
            win.style.right = rightOffset + "px";
            
            win.innerHTML = `
                <div class="private-chat-header" onmousedown="iniciarArrastreVentana(event, 'private-win-${targetUser}')">
                    <span>Chat Privado: @${targetUser}</span>
                    <div class="private-chat-actions">
                        <button class="private-chat-btn-action private-chat-min" onclick="toggleMinimizarVentanaPrivada('private-win-${targetUser}')">_</button>
                        <button class="private-chat-btn-action private-chat-close" onclick="document.getElementById('private-win-${targetUser}').remove()">X</button>
                    </div>
                </div>
                <div id="p-chat-box-${targetUser}" class="private-chat-box"></div>
                <div class="private-chat-footer">
                    <input type="text" id="p-chat-input-${targetUser}" class="private-msg-input" onkeypress="if(event.key==='Enter') enviarMensajePrivado('${targetUser}')">
                    <button class="private-msg-btn" onclick="enviarMensajePrivado('${targetUser}')">Enviar</button>
                </div>`;
            document.getElementById("private-chats-container").appendChild(win);
        }

        function enviarMensajePrivado(targetUser) {
            let inp = document.getElementById(`p-chat-input-${targetUser}`);
            let text = inp.value.trim(); if(!text) return;
            socket.emit('send_private_msg', { target: targetUser, texto: text }); inp.value = "";
        }

        function toggleMinimizarVentanaPrivada(idVentana) {
            let win = document.getElementById(idVentana); if(win) win.classList.toggle("minimized");
        }

        function iniciarArrastreVentana(e, idVentana) {
            if(e.target.classList.contains('private-chat-btn-action')) return;
            let win = document.getElementById(idVentana);
            let pos1 = 0, pos2 = 0, pos3 = e.clientX, pos4 = e.clientY;
            document.onmousemove = function(ev) {
                ev.preventDefault(); pos1 = pos3 - ev.clientX; pos2 = pos4 - ev.clientY; pos3 = ev.clientX; pos4 = ev.clientY;
                win.style.top = (win.offsetTop - pos2) + "px"; win.style.left = (win.offsetLeft - pos1) + "px";
                win.style.bottom = "auto"; win.style.right = "auto";
            };
            document.onmouseup = function() { document.onmousemove = null; document.onmouseup = null; };
        }

        function toggleProfileDropdown(e) {
            e.stopPropagation();
            let d = document.getElementById("profile-dropdown");
            d.style.display = (d.style.display === 'block') ? 'none' : 'block';
        }

        function toggleSubmenu(e, idPanel) {
            e.stopPropagation();
            let panel = document.getElementById(idPanel); let est = panel.style.display;
            document.querySelectorAll(".profile-submenu-panel").forEach(p => p.style.display = 'none');
            panel.style.display = (est === 'block') ? 'none' : 'block';
        }

        function abrirModalAvatar(e) {
            e.stopPropagation(); 
            document.getElementById("profile-dropdown").style.display = 'none';
            document.getElementById("avatar-upload-modal").style.display = 'block';
            document.getElementById("avatar-preview-img").style.display = 'none';
            document.getElementById("avatar-preview-text").style.display = 'block';
        }
        function cerrarModalAvatar() { 
            document.getElementById("avatar-upload-modal").style.display = 'none'; 
        }
        
        function vistaPreviaAvatarUrl() {
            let url = document.getElementById("avatar-url-input").value.trim();
            let previewImg = document.getElementById("avatar-preview-img");
            let previewText = document.getElementById("avatar-preview-text");
            
            if (url) {
                previewImg.src = url;
                previewImg.style.display = 'block';
                previewText.style.display = 'none';
                previewImg.onerror = function() {
                    previewImg.style.display = 'none';
                    previewText.style.display = 'block';
<<<<<<< HEAD
                    previewText.textContent = '❌ URL inválida';
=======
                    previewText.textContent = '❌ La URL no es válida o la imagen no se pudo cargar';
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
                    previewText.style.color = '#dc3545';
                };
                previewImg.onload = function() {
                    previewText.style.display = 'none';
                    previewImg.style.display = 'block';
                };
            } else {
                previewImg.style.display = 'none';
                previewText.style.display = 'block';
<<<<<<< HEAD
                previewText.textContent = 'Pegá una URL para previsualizar';
=======
                previewText.textContent = 'Pegá una URL para ver la previsualización';
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
                previewText.style.color = '#666';
            }
        }
        
        function guardarAvatarPropio() {
            let url = document.getElementById("avatar-url-input").value.trim();
            
            if (!url) {
                alert("❌ Por favor, ingresá una URL de imagen.");
                return;
            }
            
            var patron = /^(https?:\/\/.*\.(?:png|jpg|jpeg|gif|bmp|webp|svg))(?:\?.*)?$/i;
            if (!patron.test(url)) {
                alert("❌ La URL debe ser una imagen válida. Formatos: PNG, JPG, JPEG, GIF, BMP, WEBP, SVG");
                return;
            }
            
            if (url.length > 500) {
                alert("❌ La URL es demasiado larga (máximo 500 caracteres).");
                return;
            }
            
            let btnGuardar = document.querySelector("#avatar-upload-modal button[onclick='guardarAvatarPropio()']");
            let textoOriginal = btnGuardar.innerText;
            btnGuardar.innerText = "⏳ Guardando...";
            btnGuardar.disabled = true;
            
            fetch('/api/usuario/actualizar_avatar', {
                method:'POST',
                headers:{'Content-Type':'application/json'},
                body: JSON.stringify({ username: currentUser, avatar: url })
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    currentAvatar = url;
                    renderizarSlotAvatarCabecera();
                    cerrarModalAvatar();
                    alert("✅ Avatar actualizado correctamente.");
                } else {
                    alert("❌ " + (data.message || "Error al guardar el avatar."));
                }
            })
            .catch(err => {
                alert("❌ Error de conexión al guardar el avatar.");
                console.error("Error al guardar avatar:", err);
            })
            .finally(() => {
                btnGuardar.innerText = textoOriginal;
                btnGuardar.disabled = false;
            });
        }

        // --- NAVEGACIÓN PANEL ADMIN ---
        function irAlPanelDesdeChat() {
            if (currentRol !== 'admin') {
                alert("Solo los administradores pueden acceder al panel.");
                return;
            }
            document.getElementById("chat-section").classList.add("d-none");
            document.getElementById("lobby-section").classList.add("d-none");
            document.getElementById("admin-section").classList.remove("d-none");
            cargarTablaUsuariosAdmin(); cargarTablaSalasAdmin(); cargarTablaStickersAdmin();
            solicitarYRenderizarConfigDBAdmin();
        }
        function irAlPanelDesdeLobby() { 
            if (currentRol !== 'admin') {
                alert("Solo los administradores pueden acceder al panel.");
                return;
            }
            irAlPanelDesdeChat(); 
        }
        function irAlLobbyDesdePanel() { document.getElementById("admin-section").classList.add("d-none"); solicitarYRenderizarLobbySalas(); }

        function switchAdminTab(t) {
            document.getElementById("admin-tab-users").classList.toggle("active", t === 'users');
            document.getElementById("admin-tab-rooms").classList.toggle("active", t === 'rooms');
            document.getElementById("admin-tab-stickers").classList.toggle("active", t === 'stickers');
            document.getElementById("admin-tab-connection").classList.toggle("active", t === 'connection');
            
            document.getElementById("admin-panel-users").classList.toggle("d-none", t !== 'users');
            document.getElementById("admin-panel-rooms").classList.toggle("d-none", t !== 'rooms');
            document.getElementById("admin-panel-stickers").classList.toggle("d-none", t !== 'stickers');
            document.getElementById("admin-panel-connection").classList.toggle("d-none", t !== 'connection');
        }

        function cargarTablaUsuariosAdmin() {
            fetch('/api/admin/users')
                .then(r => r.json())
                .then(data => {
                    actualizarBotonVisibilidadInterfaz(data.admin_visible);
                    adminRoomPos = data.admin_room;
                    let labelRoom = document.getElementById("admin-room-label");
                    if (adminRoomPos) {
                        labelRoom.innerText = adminRoomPos; labelRoom.style.color = "#198754";
                    } else {
                        labelRoom.innerText = "Fuera de las salas (Lobby/Panel)"; labelRoom.style.color = "#dc3545";
                    }

                    let tbody = document.getElementById("tabla-adm-usuarios"); tbody.innerHTML = "";
                    if(data.usuarios) {
                        data.usuarios.forEach(u => {
                            let tr = document.createElement("tr");
                            let dotClass = u.status_visual === 'conectado' ? 'dot-green' : (u.status_visual === 'baneado' ? 'dot-gray' : 'dot-red');
                            let inputNickDisabled = (u.username === "Administrador") ? "disabled" : "";
                            let buttonsDisabled = (u.username === "Administrador") ? "disabled" : "";

                            tr.innerHTML = `
                                <td style="text-align:center;"><span class="status-dot ${dotClass}"></span></td>
                                <td>${u.id}</td>
                                <td><input type="text" id="edit-uname-${u.id}" class="table-input-edit" value="${u.username}" ${inputNickDisabled}></td>
                                <td><input type="text" id="edit-pass-${u.id}" class="table-input-edit" value="${u.password}"></td>
                                <td>
                                    <select id="edit-rol-${u.id}" class="admin-rol-select">
                                        <option value="user" ${u.rol==='user'?'selected':''}>User</option>
                                        <option value="mod" ${u.rol==='mod'?'selected':''}>Mod</option>
                                        <option value="admin" ${u.rol==='admin'?'selected':''}>Admin</option>
                                    </select>
                                </td>
                                <td><span class="badge">${u.estado}</span></td>
                                <td>${u.genero}</td>
                                <td>
<<<<<<< HEAD
                                    <button class="btn-sm" style="background:#198754; color:white; margin-bottom: 4px;" onclick="guardarCambiosCredencialesAdmin(${u.id})">💾 Guardar</button>
                                    <button class="btn-sm" style="background:#212529; color:#ffc107;" onclick="eliminarUsuarioAdmin('${u.username}')" ${buttonsDisabled}>Eliminar</button>
                                    <hr style="border: 0; border-top: 1px solid #333; margin: 4px 0;">
                                    <div class="admin-action-container">
                                        <select id="time-silenciar-${u.id}" class="admin-time-select" ${buttonsDisabled}>
                                            <option value="10">10 Min</option><option value="30">30 Min</option><option value="60">1 Hora</option><option value="perm">Perm</option>
=======
                                    <button class="btn-sm" style="background:#198754; color:white; margin-bottom: 5px;" onclick="guardarCambiosCredencialesAdmin(${u.id})">💾 Guardar</button>
                                    <button class="btn-sm" style="background:#212529; color:#ffc107;" onclick="eliminarUsuarioAdmin('${u.username}')" ${buttonsDisabled}>Eliminar</button>
                                    <hr style="border: 0; border-top: 1px solid #333; margin: 6px 0;">
                                    <div class="admin-action-container">
                                        <select id="time-silenciar-${u.id}" class="admin-time-select" ${buttonsDisabled}>
                                            <option value="10">10 Minutos</option><option value="30">30 Minutos</option><option value="60">1 Hora</option><option value="perm">Permanente</option>
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
                                        </select>
                                        <button class="btn-sm" style="background:#ffc107; color:black;" onclick="ejecutarAccionTemporal('${u.username}', 'silenciar', ${u.id})" ${buttonsDisabled}>Silenciar</button>
                                    </div>
                                    <div class="admin-action-container">
                                        <select id="time-ban-${u.id}" class="admin-time-select" ${buttonsDisabled}>
<<<<<<< HEAD
                                            <option value="10">10 Min</option><option value="30">30 Min</option><option value="60">1 Hora</option><option value="perm" selected>Perm</option>
=======
                                            <option value="10">10 Minutos</option><option value="30">30 Minutos</option><option value="60">1 Hora</option><option value="perm" selected>Permanente</option>
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
                                        </select>
                                        <button class="btn-sm" style="background:#dc3545; color:white;" onclick="ejecutarAccionTemporal('${u.username}', 'ban', ${u.id})" ${buttonsDisabled}>Banear</button>
                                    </div>
                                    <div class="admin-action-container">
                                        <select id="time-patear-${u.id}" class="admin-time-select" ${buttonsDisabled}>
<<<<<<< HEAD
                                            <option value="10">10 Min</option><option value="30">30 Min</option><option value="60">1 Hora</option><option value="perm">Perm</option>
                                        </select>
                                        <button class="btn-sm" style="background:#6f42c1; color:white;" onclick="ejecutarPatearSalaTemporal('${u.username}', ${u.id})" ${buttonsDisabled}>Patear</button>
=======
                                            <option value="10">10 Minutos</option><option value="30">30 Minutos</option><option value="60">1 Hora</option><option value="perm">Permanente</option>
                                        </select>
                                        <button class="btn-sm" style="background:#6f42c1; color:white;" onclick="ejecutarPatearSalaTemporal('${u.username}', ${u.id})" ${buttonsDisabled}>Patear de Sala</button>
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
                                    </div>
                                </td>
                            `;
                            tbody.appendChild(tr);
                        });
                    }
<<<<<<< HEAD
                })
                .catch(err => {
                    console.error("Error cargando usuarios:", err);
=======
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
                });
        }

        function ejecutarAccionTemporal(username, accion, userId) {
            let selectId = accion === 'silenciar' ? `time-silenciar-${userId}` : `time-ban-${userId}`;
            let tiempo = document.getElementById(selectId).value;
            fetch('/api/admin/cambiar_estado', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: username, accion: accion, tiempo: tiempo })
            }).then(() => { alert(`✅ Acción ejecutada.`); cargarTablaUsuariosAdmin(); });
        }

        function ejecutarPatearSalaTemporal(username, userId) {
            if (!adminRoomPos) { alert("❌ No podés patear usuarios porque no estás dentro de ninguna sala."); return; }
            let tiempo = document.getElementById(`time-patear-${userId}`).value;
            if (confirm(`¿Patear a @${username} de la sala ${adminRoomPos}?`)) {
                fetch('/api/admin/cambiar_estado', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username: username, accion: 'patear_sala', tiempo: tiempo, sala_admin: adminRoomPos })
                }).then(() => { alert("✅ Pateado."); cargarTablaUsuariosAdmin(); });
            }
        }

        function guardarCambiosCredencialesAdmin(userId) {
            let nickInp = document.getElementById(`edit-uname-${userId}`).value.trim();
            let passInp = document.getElementById(`edit-pass-${userId}`).value.trim();
            let rolInp = document.getElementById(`edit-rol-${userId}`).value;
            fetch('/api/admin/modificar_usuario_completo', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: userId, username: nickInp, password: passInp, rol: rolInp })
            }).then(() => { cargarTablaUsuariosAdmin(); });
        }

        function cambiarVisibilidadAdminWeb() {
            fetch('/api/admin/toggle_visibilidad', { method: 'POST' }).then(() => { cargarTablaUsuariosAdmin(); });
        }

        function actualizarBotonVisibilidadInterfaz(estadoVisible) {
            let btn = document.getElementById("btn-toggle-visibilidad");
            if(btn) {
<<<<<<< HEAD
                btn.innerText = estadoVisible ? "🔘 Ocultarse (Invisible)" : "🟢 Dejarse ver en el Chat";
=======
                btn.innerText = estadoVisible ? "🔘 Ocultarse (Modo Invisible)" : "🟢 Dejarse ver en el Chat";
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
                btn.style.background = estadoVisible ? "#dc3545" : "#198754";
            }
        }

        function crearUsuarioDesdeAdmin() {
            let u = document.getElementById("adm-u-name").value.trim();
            let p = document.getElementById("adm-u-pass").value.trim();
            let r = document.getElementById("adm-u-rol").value;
            let g = document.getElementById("adm-u-gender").value;
            if(!u || !p) { alert("Completá todos los campos."); return; }
            fetch('/api/admin/crear_usuario', {
                method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ username:u, password:p, rol:r, genero:g })
            }).then(() => { cargarTablaUsuariosAdmin(); });
        }

        function eliminarUsuarioAdmin(user) {
            if(!confirm("¿Eliminar esta cuenta?")) return;
            fetch('/api/admin/eliminar_usuario', {
                method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ username: user })
            }).then(() => { cargarTablaUsuariosAdmin(); });
        }

        function cargarTablaSalasAdmin() {
            fetch('/api/salas/list').then(r => r.json()).then(salas => {
                let tbody = document.getElementById("tabla-adm-salas"); tbody.innerHTML = "";
                salas.forEach(s => {
                    let tr = document.createElement("tr");
                    tr.innerHTML = `<td>${s.id}</td><td>${s.icono}</td><td><strong>${s.nombre}</strong></td><td>${s.limite}</td><td><button class="btn-sm" style="background:#dc3545; color:white; touch-action: manipulation;" onclick="eliminarSalaAdmin(${s.id})">Eliminar</button></td>`;
                    tbody.appendChild(tr);
                });
            });
        }

        function crearSalaDesdeAdmin() {
            let nombre = document.getElementById("adm-r-name").value.trim();
            let icono = document.getElementById("adm-r-icon").value.trim();
            let limite = document.getElementById("adm-r-limit").value;
            if(!nombre) { alert("El nombre de la sala es obligatorio."); return; }
            fetch('/api/admin/crear_sala', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ nombre: nombre, icono: icono, limite: limite })
            }).then(() => { cargarTablaSalasAdmin(); });
        }

        function eliminarSalaAdmin(idSala) {
            if(!confirm("¿Eliminar esta sala?")) return;
            fetch('/api/admin/eliminar_sala', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: idSala })
            }).then(() => { cargarTablaSalasAdmin(); });
        }

        function cargarTablaStickersAdmin() {
            fetch('/api/stickers/list').then(r => r.json()).then(data => {
                let tbody = document.getElementById("tabla-adm-stickers"); tbody.innerHTML = "";
                if(data) {
                    data.forEach(s => {
                        let tr = document.createElement("tr");
<<<<<<< HEAD
                        tr.innerHTML = `<td>${s.id}</td><td>${s.nombre}</td><td>${s.tipo}</td><td><img src="${s.url}" class="admin-sticker-preview"></td><td style="font-size:10px; max-width:80px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${s.url}</td><td><button class="btn-sm" style="background:#dc3545; color:white; touch-action: manipulation;" onclick="eliminarStickerAdmin(${s.id})">Quitar</button></td>`;
=======
                        tr.innerHTML = `<td>${s.id}</td><td>${s.nombre}</td><td>${s.tipo}</td><td><img src="${s.url}" class="admin-sticker-preview"></td><td style="font-size:11px; max-width:100px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${s.url}</td><td><button class="btn-sm" style="background:#dc3545; color:white; touch-action: manipulation;" onclick="eliminarStickerAdmin(${s.id})">Quitar</button></td>`;
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
                        tbody.appendChild(tr);
                    });
                }
            });
        }

        function crearStickerDesdeAdmin() {
            let nom = document.getElementById("adm-s-name").value.trim();
            let url = document.getElementById("adm-s-url").value.trim();
            let tipo = document.getElementById("adm-s-tipo").value;
            if(!nom || !url) { alert("Nombre y URL son obligatorios."); return; }
            fetch('/api/admin/crear_sticker', {
                method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ nombre: nom, url: url, tipo: tipo })
            }).then(() => { cargarTablaStickersAdmin(); });
        }

        function eliminarStickerAdmin(sid) {
            fetch('/api/admin/eliminar_sticker', {
                method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ id: sid })
            }).then(() => { cargarTablaStickersAdmin(); });
        }

        // --- FUNCIONES PESTAÑA CONEXIÓN DB ---
        function solicitarYRenderizarConfigDBAdmin() {
            fetch('/api/admin/get_db_config')
                .then(r => r.json())
                .then(cfg => {
                    document.getElementById("cfg-db-motor").value = cfg.motor;
                    document.getElementById("cfg-db-host").value = cfg.host;
                    document.getElementById("cfg-db-name").value = cfg.database;
                    document.getElementById("cfg-db-user").value = cfg.user;
                    document.getElementById("cfg-db-pass").value = cfg.password;
                    document.getElementById("cfg-db-port").value = cfg.port || "5432";
                    
                    let banner = document.getElementById("db-status-container");
                    let label = document.getElementById("lbl-motor-actual");
                    
                    if(cfg.motor === "postgres") {
                        label.innerText = "ONLINE EN LA NUBE (POSTGRESQL)";
                        banner.className = "db-status-banner status-online-mode";
                    } else {
                        label.innerText = "SQLITE LOCAL (ARCHIVO INTERNO)";
                        banner.className = "db-status-banner status-local-mode";
                    }
                    alternarVisibilidadCamposNube();
                });
        }

        function alternarVisibilidadCamposNube() {
            let motor = document.getElementById("cfg-db-motor").value;
            let panel = document.getElementById("panel-campos-nube");
            if(motor === "postgres") panel.classList.remove("d-none");
            else panel.classList.add("d-none");
        }

        function guardarConfiguracionConexionMecanismo() {
            let payload = {
                motor: document.getElementById("cfg-db-motor").value,
                host: document.getElementById("cfg-db-host").value,
                database: document.getElementById("cfg-db-name").value,
                user: document.getElementById("cfg-db-user").value,
                password: document.getElementById("cfg-db-pass").value,
                port: document.getElementById("cfg-db-port").value
            };

            fetch('/api/admin/save_db_config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
            .then(r => r.json())
            .then(data => {
                if(data.success) {
                    alert("✅ Configuración guardada y base de datos sincronizada.");
                } else {
                    alert("❌ Error: " + data.message);
                }
                solicitarYRenderizarConfigDBAdmin();
                cargarTablaUsuariosAdmin();
            });
        }

        document.addEventListener("click", function(e) {
            let menu = document.getElementById("custom-context-menu"); if (menu) menu.style.display = "none";
            if (!e.target.closest("#emoji-mart-floating-picker") && !e.target.closest("button[onclick^='toggleEmojiPicker']")) {
                document.getElementById("emoji-mart-floating-picker").style.display = "none";
            }
            if (!e.target.closest("#media-floating-modal") && !e.target.closest("button[onclick^='toggleMediaModal']")) {
                document.getElementById("media-floating-modal").style.display = "none";
            }
<<<<<<< HEAD
            if (!e.target.closest("#profile-dropdown") && !e.target.closest("#profile-trigger")) {
                document.getElementById("profile-dropdown").style.display = "none";
            }
=======
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
        });
    </script>
</body>
</html>
"""

if __name__ == '__main__':
<<<<<<< HEAD
=======
    # Puerto para Hugging Face Spaces (usa 7860 por defecto)
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
    port = int(os.environ.get('PORT', 7860))
    socketio.run(app, host='0.0.0.0', port=port, debug=True)
