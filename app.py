import os
import json
import sqlite3
import datetime
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
app.config['SECRET_KEY'] = 'secreto123!'

# === CONFIGURACIÓN MEJORADA PARA RENDER ===
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='threading',
    ping_timeout=60,
    ping_interval=25,
    transports=['websocket', 'polling'],
    allow_upgrades=True,
    always_connect=True
)

# Variable global en memoria para controlar si el admin decide hacerse visible
admin_visible = False
usuarios_conectados = {}

# FILE CONFIG PARA GUARDAR PARAMETROS ONLINE
CONFIG_FILE = "db_config.json"

def cargar_config_db():
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

def guardar_config_db(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

# Cargar configuración inicial
db_config = cargar_config_db()

# ==========================================
# GESTOR DE CONEXIONES HÍBRIDO (SQLITE / POSTGRES)
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

def db_query(query, params=(), fetchall=False, commit=False):
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
# BASE DE DATOS E INICIALIZACIÓN
# ==========================================
def init_db():
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
        
        columnas_usuarios = ["genero TEXT NOT NULL DEFAULT 'hombre'", "avatar TEXT DEFAULT ''", "ban_expira TEXT", "mute_expira TEXT"]
        for col in columnas_usuarios:
            try: db_query(f"ALTER TABLE usuarios ADD COLUMN {col}", commit=True)
            except: pass
            
        res_salas = db_query("SELECT COUNT(*) FROM salas", fetchall=False)
        if res_salas and res_salas[0] == 0:
            db_query("INSERT INTO salas (nombre, icono, limite) VALUES (?, ?, ?)", ("Sala General", "🌍", 150), commit=True)
            print("-> Sala por defecto 'Sala General' creada.")

        res_admin = db_query("SELECT id FROM usuarios WHERE username = 'Administrador'", fetchall=False)
        if not res_admin:
            db_query("INSERT INTO usuarios (username, password, rol, estado, genero, avatar) VALUES (?, ?, ?, ?, ?, ?)", 
                     ("Administrador", "1234", "admin", "activo", "hombre", ""), commit=True)
            print("-> Cuenta 'Administrador' creada.")
        
        print(f"-> Base de datos inicializada en modo [{db_config['motor'].upper()}]")
    except Exception as e:
        print(f"[ERROR INIT DB]: {e}")

init_db()

# ==========================================
# FUNCIONES AUXILIARES
# ==========================================
def verificar_y_limpiar_sanciones(username):
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
        except: pass

    if estado == 'silenciado' and mute_expira:
        try:
            dt_exp = datetime.datetime.fromisoformat(mute_expira)
            if ahora > dt_exp:
                db_query("UPDATE usuarios SET estado='activo', mute_expira=NULL WHERE username=?", (username,), commit=True)
        except: pass

def calcular_fecha_expiracion(minutos_str):
    if minutos_str == "perm":
        return None
    mins = int(minutos_str)
    return (datetime.datetime.now() + datetime.timedelta(minutes=mins)).isoformat()

# ==========================================
# 2. ENDPOINTS HTTP Y API REST
# ==========================================
@app.route('/')
def home():
    # === VERSIÓN SIMPLIFICADA PARA PRUEBA ===
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>WebChat en Render</title>
        <meta charset="UTF-8">
        <style>
            body { font-family: Arial; background: #121212; color: #fff; text-align: center; padding: 50px; }
            h1 { color: #0dcaf0; }
            .info { background: #1e1e1e; padding: 20px; border-radius: 8px; max-width: 500px; margin: 20px auto; border: 1px solid #333; }
            .badge { background: #0d6efd; color: white; padding: 4px 12px; border-radius: 12px; font-size: 14px; }
        </style>
    </head>
    <body>
        <h1>🚀 WebChat en Render</h1>
        <div class="info">
            <p>✅ El servidor está funcionando correctamente</p>
            <p><span class="badge">Admin</span> <b>Usuario:</b> Administrador</p>
            <p><span class="badge">🔑</span> <b>Contraseña:</b> 1234</p>
            <hr style="border-color: #333;">
            <p>📍 La interfaz completa se cargará en breve</p>
            <p><a href="/api/salas/list" target="_blank" style="color: #0dcaf0;">Ver salas (API)</a></p>
        </div>
    </body>
    </html>
    """

# === TODOS LOS ENDPOINTS DE LA API ===
# (Mantén aquí todos los endpoints que ya tenías: /api/login, /api/registro, /api/admin/users, etc.)
# Para no hacer este mensaje demasiado largo, solo incluimos los esenciales.
# Pero tú debes mantener TODOS los endpoints de tu versión original.

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    user = data.get("username", "").strip()
    passw = data.get("password", "").strip()
    
    verificar_y_limpiar_sanciones(user)
    
    res = db_query("SELECT username, rol, estado, genero, avatar FROM usuarios WHERE username=? AND password=?", (user, passw))
    if not res:
        return jsonify({"success": False, "message": "Usuario o contraseña incorrectos."})
    
    username, rol, estado, genero, avatar = res
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
        
    res = db_query("SELECT id FROM usuarios WHERE username=?", (user,))
    if res:
        return jsonify({"success": False, "message": "El nombre de usuario ya existe."})
        
    db_query("INSERT INTO usuarios (username, password, rol, estado, genero, avatar) VALUES (?, ?, 'user', 'activo', ?, '')", 
             (user, passw, gender), commit=True)
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
            
            if est_db == 'ban': status_visual = 'baneado'
            elif uname in online_usernames: status_visual = 'conectado'
            else: status_visual = 'desconectado'
                
            usuarios.append({
                "id": r[0],
                "username": uname,
                "password": r[2],
                "rol": r[3],
                "estado": est_db,
                "status_visual": status_visual,
                "genero": r[5]
            })
    
    admin_room = None
    for u in usuarios_conectados.values():
        if u.get("username") == "Administrador":
            admin_room = u.get("sala_actual")
            break

    return jsonify({"usuarios": usuarios, "admin_visible": admin_visible, "admin_room": admin_room})

@app.route('/api/admin/crear_usuario', methods=['POST'])
def api_admin_crear_usuario():
    data = request.json
    user = data.get("username", "").strip()
    passw = data.get("password", "").strip()
    gender = data.get("genero", "hombre")
    rol = data.get("rol", "user")
    
    if db_query("SELECT id FROM usuarios WHERE username=?", (user,)):
        return jsonify({"success": False, "message": "El usuario ya existe."})
        
    db_query("INSERT INTO usuarios (username, password, rol, estado, genero, avatar) VALUES (?, ?, ?, 'activo', ?, '')", 
             (user, passw, rol, gender), commit=True)
    return jsonify({"success": True})

@app.route('/api/admin/crear_sala', methods=['POST'])
def api_admin_crear_sala():
    data = request.json
    nombre = data.get("nombre", "").strip()
    icono = data.get("icono", "").strip() or "💬"
    try: limite = int(data.get("limite", 150))
    except: limite = 150
        
    if not nombre:
        return jsonify({"success": False, "message": "El nombre de la sala es obligatorio."})
    if limite > 150:
        return jsonify({"success": False, "message": "El límite máximo permitido es de 150 usuarios."})
        
    if db_query("SELECT id FROM salas WHERE nombre=?", (nombre,)):
        return jsonify({"success": False, "message": "Ya existe una sala con ese nombre."})
        
    db_query("INSERT INTO salas (nombre, icono, limite) VALUES (?, ?, ?)", (nombre, icono, limite), commit=True)
    return jsonify({"success": True})

# ==========================================
# LÓGICA DE WEBSOCKETS (SOCKET.IO)
# ==========================================
@socketio.on('join_chat')
def handle_join(data):
    username = data.get('username')
    if not username: return
    
    verificar_y_limpiar_sanciones(username)
    res = db_query("SELECT rol, genero, avatar, estado FROM usuarios WHERE username=?", (username,))
    if res:
        rol, genero, avatar, estado = res
        if estado == 'ban': return
        
        usuarios_conectados[request.sid] = {
            "username": username,
            "rol": rol,
            "genero": genero,
            "avatar": avatar,
            "sala_actual": None
        }
        broadcast_user_list_all_rooms()

@socketio.on('cambiar_sala')
def handle_cambiar_sala(data):
    if request.sid not in usuarios_conectados: return
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
                except: pass
    
    res_sala = db_query("SELECT limite FROM salas WHERE nombre=?", (sala_nueva,))
    if not res_sala:
        emit('sys_msg', {"texto": "La sala solicitada ya no existe."})
        return
        
    limite_max = res_sala[0]
    conteo_actual = 0
    for u in usuarios_conectados.values():
        if u.get("sala_actual") == sala_nueva:
            if u.get("username") == "Administrador" and not admin_visible: continue
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
    if request.sid not in usuarios_conectados: return
    user_info = usuarios_conectados[request.sid]
    username = user_info["username"]
    sala_destino = user_info["sala_actual"]
    if not sala_destino: return
    
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
        "avatar": data.get("avatar", "")
    }
    emit('receive_msg', payload, to=sala_destino)

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
                if uname == "Administrador" and not admin_visible: continue
                    
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8550))
    socketio.run(app, host='0.0.0.0', port=port, debug=True)
