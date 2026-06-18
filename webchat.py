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
        "motor": "sqlite", # 'sqlite' o 'postgres'
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
    """Retorna una conexión activa según el motor configurado."""
    if db_config["motor"] == "postgres":
        if not HAS_POSTGRES:
            raise RuntimeError("Librería 'psycopg2' no instalada. Ejecutá: pip install psycopg2-binary")
        return psycopg2.connect(
            host=db_config["host"],
            database=db_config["database"],
            user=db_config["user"],
            password=db_config["password"],
            port=db_config["port"]
        )
    else:
        # Por defecto SQLite local
        return sqlite3.connect("chat_app.db")

def db_query(query, params=(), fetchall=False, commit=False):
    """Ejecuta una consulta abstrayendo si es SQLite o PostgreSQL."""
    es_postgres = (db_config["motor"] == "postgres")
    
    # Adaptar placeholders: SQLite usa '?', Postgres usa '%s'
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
            # En psycopg2, fetchone lanza error si la consulta no devuelve filas (como un INSERT)
            if cursor.description:
                res = cursor.fetchone()
    except Exception as e:
        print(f"[ERROR SQL CRÍTICO]: Motor: {db_config['motor']} | Query: {query} | Error: {e}")
        if commit:
            conn.rollback()
    finally:
        conn.close()
    return res

# ==========================================
# 1. BASE DE DATOS E INICIALIZACIÓN
# ==========================================
def init_db():
    try:
        # Crear tablas adaptando la sintaxis autoincremental de cada motor
        es_postgres = (db_config["motor"] == "postgres")
        pk_type = "SERIAL PRIMARY KEY" if es_postgres else "INTEGER PRIMARY KEY AUTOINCREMENT"
        
        # Tabla de usuarios
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
        
        # Tabla de stickers
        db_query(f"""
            CREATE TABLE IF NOT EXISTS stickers (
                id {pk_type},
                nombre TEXT NOT NULL,
                url TEXT NOT NULL,
                tipo TEXT NOT NULL DEFAULT 'sticker'
            )
        """, commit=True)
        
        # Tabla de salas de chat
        db_query(f"""
            CREATE TABLE IF NOT EXISTS salas (
                id {pk_type},
                nombre TEXT NOT NULL UNIQUE,
                icono TEXT NOT NULL DEFAULT '💬',
                limite INTEGER NOT NULL DEFAULT 150
            )
        """, commit=True)
        
        # Tabla para registrar bloqueos temporales de salas
        db_query(f"""
            CREATE TABLE IF NOT EXISTS bloqueos_salas (
                id {pk_type},
                username TEXT NOT NULL,
                sala TEXT NOT NULL,
                expira TEXT NOT NULL
            )
        """, commit=True)
        
        # Migraciones silenciosas por si faltan columnas
        columnas_usuarios = ["genero TEXT NOT NULL DEFAULT 'hombre'", "avatar TEXT DEFAULT ''", "ban_expira TEXT", "mute_expira TEXT"]
        for col in columnas_usuarios:
            try: db_query(f"ALTER TABLE usuarios ADD COLUMN {col}", commit=True)
            except: pass
            
        # Crear una sala por defecto si no existe ninguna
        res_salas = db_query("SELECT COUNT(*) FROM salas", fetchall=False)
        if res_salas and res_salas[0] == 0:
            db_query("INSERT INTO salas (nombre, icono, limite) VALUES (?, ?, ?)", ("Sala General", "🌍", 150), commit=True)
            print("-> [DB SETUP]: Sala por defecto 'Sala General' creada.")

        # Verificar e insertar el Administrador por defecto
        res_admin = db_query("SELECT id FROM usuarios WHERE username = 'Administrador'", fetchall=False)
        if not res_admin:
            db_query("INSERT INTO usuarios (username, password, rol, estado, genero, avatar) VALUES (?, ?, ?, ?, ?, ?)", 
                     ("Administrador", "1234", "admin", "activo", "hombre", ""), commit=True)
            print("-> [DB SETUP]: Cuenta 'Administrador' verificada y creada.")
        
        print(f"-> [DB SETUP SUCCESFUL]: Inicializado en modo [{db_config['motor'].upper()}]")
    except Exception as e:
        print(f"[ERROR INIT DB]: {e}")

# Ejecutar inicialización al arrancar
init_db()

# ==========================================
# FUNCIONES AUXILIARES PARA CONTROL DE TIEMPOS
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
                estado = 'activo'
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
    return render_template_string(HTML_TEMPLATE)

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
        return jsonify({"success": False, "message": "Tu cuenta se encuentra baneada temporal o permanentemente."})
        
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

@app.route('/api/usuario/actualizar_avatar', methods=['POST'])
def api_actualizar_avatar():
    data = request.json
    user = data.get("username", "").strip()
    avatar = data.get("avatar", "")
    db_query("UPDATE usuarios SET avatar=? WHERE username=?", (avatar, user), commit=True)
    return jsonify({"success": True})

# --- ENDPOINTS DE SALAS ---
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

# --- ENDPOINTS EXCLUSIVOS DE ADMINISTRACIÓN ---
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
    
    if db_query("SELECT id FROM usuarios WHERE username=?", (user,)):
        return jsonify({"success": False, "message": "El usuario ya existe."})
        
    db_query("INSERT INTO usuarios (username, password, rol, estado, genero, avatar) VALUES (?, ?, ?, 'activo', ?, '')", 
             (user, passw, rol, gender), commit=True)
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

    db_query("UPDATE usuarios SET username=?, password=?, rol=? WHERE id=?", (nuevo_nick, nueva_pass, nuevo_rol, user_id), commit=True)
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
        db_query("INSERT INTO bloqueos_salas (username, sala, expira) VALUES (?, ?, ?)", (user, sala_admin, expiracion if expiracion else "perm"), commit=True)
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
    db_query("INSERT INTO stickers (nombre, url, tipo) VALUES (?, ?, ?)", (nom, url, tipo), commit=True)
    return jsonify({"success": True})

@app.route('/api/admin/eliminar_sticker', methods=['POST'])
def api_admin_eliminar_sticker():
    data = request.json
    sid = data.get("id")
    db_query("DELETE FROM stickers WHERE id=?", (sid,), commit=True)
    return jsonify({"success": True})

# --- NUEVOS ENDPOINTS DE CONFIGURACIÓN DE CONEXIÓN ---
@app.route('/api/admin/get_db_config', methods=['GET'])
def api_get_db_config():
    # Retornamos la config actual omitiendo el password por seguridad completa
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
        
    # Si ingresó asteriscos, conservamos el password que ya teníamos guardado
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
    
    # Probar conexión antes de dar por buena la configuración
    try:
        conn = obtener_conexion()
        conn.close()
    except Exception as e:
        # Revertir a modo sqlite local para evitar caídas totales si fallaron los credenciales en la nube
        db_config["motor"] = "sqlite"
        return jsonify({"success": False, "message": f"Falló la conexión al servidor remoto: {e}. Se revirtió a SQLite Local."})
        
    guardar_config_db(db_config)
    # Volver a inicializar tablas en el nuevo motor destino
    init_db()
    return jsonify({"success": True})


# ==========================================
# 3. LÓGICA DE WEBSOCKETS (SOCKET.IO)
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
    
    # CONTROL DE PATEOS / BLOQUEOS TEMPORALES
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
        emit('sys_msg', {"texto": "No podés enviar mensajes, estás silenciado temporal o permanentemente."})
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
    if request.sid not in usuarios_conectados: return
    sender = usuarios_conectados[request.sid]["username"]
    target = data.get("target")
    texto = data.get("texto")
    
    verificar_y_limpiar_sanciones(sender)
    res = db_query("SELECT estado FROM usuarios WHERE username=?", (sender,))
    if res and res[0] == 'silenciado': return
    
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

# ==========================================
# 4. PLANTILLA HTML DE LA INTERFAZ (COMPLETA)
# ==========================================
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>WebChat Profesional - Flask</title>
    <script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/@twemoji/api@14.1.0/dist/twemoji.min.js" crossorigin="anonymous"></script>
    <script src="https://cdn.jsdelivr.net/npm/emoji-mart@5.6.0/dist/browser.js"></script>
    <style>
        /* ... ESTILOS COMPLETOS DE TU INTERFAZ ... */
        /* (Mantén aquí todos los estilos CSS que ya tienes) */
    </style>
</head>
<body>
    <!-- ... TODO EL HTML DE TU INTERFAZ ... -->
    <script>
        // ... TODO EL JAVASCRIPT DE TU INTERFAZ ...
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    # === CAMBIO IMPORTANTE PARA RENDER ===
    port = int(os.environ.get('PORT', 8550))
    socketio.run(app, host='0.0.0.0', port=port, debug=True)
