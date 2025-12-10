from telethon import TelegramClient as Client
from telethon import events
from telethon import Button

import aiohttp
import aiofiles
from aiohttp_socks import ProxyConnector
from aioclient import MoodleCli
from yarl import URL

import asyncio
import os
import time
import cryptg
import zipfile
import traceback
import urllib
from config import *
import socket
import threading

# ==================== SERVICIO WEB PARA RENDER ====================
def start_health_server(port):
    """Servidor web para Render"""
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('0.0.0.0', port))
        server_socket.listen(5)
        print(f"✅ Health check server running on port {port}")
        
        while True:
            try:
                client_socket, addr = server_socket.accept()
                request = client_socket.recv(1024).decode('utf-8')
                
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n🤖 Bot Telegram is running!"
                client_socket.send(response.encode('utf-8'))
                client_socket.close()
            except Exception as e:
                print(f"Health check error: {e}")
                break
                
    except Exception as e:
        print(f"❌ Health server failed: {e}")

# ==================== FUNCIONES DEL BOT ====================
botclient = Client('bot', api_id=api_id, api_hash=api_hash).start(bot_token=bot_token)
userstatus = {}

def mydata(username):
    user = getusern(username)
    if user:
        usern = user["user"]
        passw = user["passw"]
        page = user["host"]
        repoid = user["repoid"]
        proxy = user["proxy"]
        zips = user["zips"]
        if proxy != "__Desactivado❌__":
            proxy = "__Activado✅__"
        
        msg = f"🛂 Usuario: {usern}\n"
        msg += f"🔑 Contraseña: {passw}\n"
        msg += f"📡 Pagina: {page}\n"
        msg += f"📓 REPOID: {repoid}\n"
        msg += f"📚 Zips: {zips}\n"
        msg += f"⚡ Proxy: {proxy}\n"
        return msg

@botclient.on(events.NewMessage)
async def messages(event):
    username = event.message.chat.username
    id = event.message.chat.id
    msg = event.message.text
    
    usernames = getusern(username)
    if username == OWNER or usernames:
        if usernames is None:
            makeuser(username)
    else:
        await botclient.send_message(id, "❌No tiene acceso❌")
        return
    
    userstatus[username] = {"statusdownload": "active"}
    
    if msg.lower().startswith("/start"):
        msgtext = f"Sea bienvenido al bot @{username}.\nUtilize /mydata para recordar sus datos🙌."
        await event.reply(msgtext)
    
    if msg.lower().startswith("/acc"):
        splitmsg = msg.split(" ")
        
        if len(splitmsg) != 3:
            await event.reply("❌Fallo en la escritura del comando\n👉/acc username password👈.")
        else:
            usern = splitmsg[1]
            password = splitmsg[2]
            
            user = getusern(username)
            if user:
                user["user"] = usern
                user["passw"] = password
                savedata(username, user)
                message = mydata(username)
                await event.reply(message)
    
    if msg.lower().startswith("/host"):
        splitmsg = msg.split(" ")
        
        if len(splitmsg) != 2:
            await event.reply("❌Fallo en la escritura del comando\n👉/host https://moodle.dominio.cu👈.")
        else:
            host = splitmsg[1]
            
            user = getusern(username)
            if user:
                user["host"] = host
                savedata(username, user)
                message = mydata(username)
                await event.reply(message)
    
    if msg.lower().startswith("/repoid"):
        splitmsg = msg.split(" ")
        
        if len(splitmsg) != 2:
            await event.reply("❌Fallo en la escritura del comando\n👉/repoid repoid👈.")
        else:
            repoid = splitmsg[1]
            
            user = getusern(username)
            if user:
                user["repoid"] = repoid
                savedata(username, user)
                message = mydata(username)
                await event.reply(message)
    
    if msg.lower().startswith("/proxy"):
        splitmsg = msg.split(" ")
        
        if len(splitmsg) != 2:
            await event.reply("❌Fallo en la escritura del comando\n👉/proxy proxy👈.")
        else:
            proxymsg = splitmsg[1]
            proxys = proxyparsed(proxymsg)
            proxy = f"socks5://{proxys}"
            
            user = getusern(username)
            if user:
                user["proxy"] = proxy
                savedata(username, user)
                message = mydata(username)
                await event.reply(message)
    
    if msg.lower().startswith("/zips"):
        splitmsg = msg.split(" ")
        
        if len(splitmsg) != 2:
            await event.reply("❌Fallo en la escritura del comando\n👉/zips size👈.")
        else:
            zips = splitmsg[1]
            
            user = getusern(username)
            if user:
                user["zips"] = zips
                savedata(username, user)
                message = mydata(username)
                await event.reply(message)
    
    if msg.lower().startswith("/mydata"):
        message = mydata(username)
        await event.reply(message)
    
    if msg.lower().startswith("/add"):
        splitmsg = msg.split(" ")
        
        if len(splitmsg) != 2:
            await event.reply("❌Fallo en la escritura del comando\n👉/add username👈.")
        else:
            usuario = splitmsg[1]
            
            makeuser(usuario)
            await event.reply(f"✅ Añadido @{usuario} al uso del bot.")
    
    if msg.lower().startswith("/ban"):
        splitmsg = msg.split(" ")
        
        if len(splitmsg) != 2:
            await event.reply("❌Fallo en la escritura del comando\n👉/ban username👈.")
        else:
            usuario = splitmsg[1]
            
            outusern(usuario)
            await event.reply("❌ Baneado @{usuario} del uso del bot.")
    
    if msg.lower().startswith("https"):
        # PASO 1: PREPARAR DESCARGA
        message = await botclient.send_message(id, "🔍 Preparando descarga...\n\nVerificando enlace...")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(msg) as response:
                try:
                    name = response.content_disposition.filename
                except:
                    name = msg.split("/")[-1]
                
                size = int(response.headers.get("content-length"))
                size_mb = size / (1024 * 1024)
                
                await message.edit(f"📥 Descarga preparada\n\n"
                                  f"📌 Nombre: {name}\n"
                                  f"📦 Tamaño: {size_mb:.2f} MB\n"
                                  f"⏳ Iniciando descarga...")
                
                if os.path.exists(username):
                    pass
                else:
                    os.mkdir(username)
                
                userpath = username
                pathfull = os.path.join(os.getcwd(), userpath, name)
                fi = await aiofiles.open(pathfull, "wb")
                chunkcurrent = 0
                starttime = time.time()
                secs = 0
                
                async for chunk in response.content.iter_chunked(1024 * 1024):
                    if userstatus[username]["statusdownload"] != "active":
                        break
                    chunkcurrent += len(chunk)
                    currenttime = time.time() - starttime
                    speed = chunkcurrent / currenttime if currenttime > 0 else 0
                    secs += len(chunk)
                    
                    if secs >= 5242880:
                        await downloadprogressmust(chunkcurrent, size, speed, message, name)
                        secs = 0
                    await fi.write(chunk)
                fi.close()
                
                if userstatus[username]["statusdownload"] == "active":
                    await message.edit("✅ Descarga finalizada\n\nPreparando subida a Moodle...")
                    await upload(pathfull, message, username)
                else:
                    await message.edit("❌ Descarga cancelada por el usuario")
    
    if event.message.media:
        # PASO 1: PREPARAR DESCARGA DE MEDIA
        name = event.file.name
        size = event.file.size
        size_mb = size / (1024 * 1024)
        
        message = await botclient.send_message(id, f"📥 Descarga preparada\n\n"
                                                   f"📌 Nombre: {name}\n"
                                                   f"📦 Tamaño: {size_mb:.2f} MB\n"
                                                   f"⏳ Iniciando descarga...")
        
        if os.path.exists(username):
            pass
        else:
            os.mkdir(username)
        
        userpath = username
        pathfull = os.path.join(os.getcwd(), userpath, name)
        fi = open(pathfull, "wb")
        chunkcurrent = 0
        starttime = time.time()
        secs = 0
        
        async for chunk in botclient.iter_download(event.message.media, chunk_size=1024 * 1024):
            if userstatus[username]["statusdownload"] != "active":
                break
            chunkcurrent += len(chunk)
            currenttime = time.time() - starttime
            speed = chunkcurrent / currenttime if currenttime > 0 else 0
            secs += len(chunk)
            
            if secs >= 5242880:
                await downloadprogressmust(chunkcurrent, size, speed, message, name)
                secs = 0
            fi.write(chunk)
        fi.close()
        
        if userstatus[username]["statusdownload"] == "active":
            await message.edit("✅ Descarga finalizada\n\nPreparando subida a Moodle...")
            await upload(pathfull, message, username)
        else:
            await message.edit("❌ Descarga cancelada por el usuario")

@botclient.on(events.CallbackQuery)
async def callback(event):
    username = event.chat.username
    if event.data == b"cancelado":
        userstatus[username]["statusdownload"] = "pasive"

async def downloadprogressmust(chunkcurrent, size, speed, message, name):
    buttons = [[Button.inline("❌ Cancelar ❌", "cancelado")]]
    bytesnormalsize = convertbytes(size)
    bytesnormalcurrent = convertbytes(chunkcurrent)
    bytesnormalspeed = convertbytes(speed)
    
    percentage = (chunkcurrent / size * 100) if size > 0 else 0
    
    # Crear barra de progreso
    bar_length = 10
    filled_length = int(bar_length * chunkcurrent // size)
    bar = '█' * filled_length + '░' * (bar_length - filled_length)
    
    msgprogress = f"📥 Descargando: {name}\n\n"
    msgprogress += f"📊 Progreso: [{bar}] {percentage:.1f}%\n"
    msgprogress += f"📦 Descargado: {bytesnormalcurrent} / {bytesnormalsize}\n"
    msgprogress += f"⚡ Velocidad: {bytesnormalspeed}/s"
    
    try:
        await message.edit(msgprogress, buttons=buttons)
    except:
        pass

async def upload(pathfull, message, username):
    try:
        # PASO 1: OBTENER DATOS DEL USUARIO
        await message.edit("🔍 Obteniendo datos de usuario...")
        user = getusern(username)
        if not user:
            await message.edit("❌ Usuario no encontrado en la base de datos")
            return
            
        # PASO 2: EXTRAER CREDENCIALES
        await message.edit("📋 Extrayendo credenciales...")
        usern = user["user"]
        pasw = user["passw"]
        host = user["host"]
        repoid = user["repoid"]
        proxy = user.get("proxy", "")
        zips = user.get("zips", 500)
        
        if zips == "__Sin Definir__":
            zips = 500
            
        # PASO 3: CONFIGURAR PROXY
        if proxy and proxy != "__Desactivado❌__":
            await message.edit(f"🔌 Configurando proxy...\n{proxy[:50]}...")
            try:
                connector = ProxyConnector.from_url(proxy)
                proxy_status = "✅ Proxy configurado"
            except Exception as proxy_err:
                await message.edit(f"❌ Error en proxy:\n{str(proxy_err)[:100]}")
                return
        else:
            connector = aiohttp.TCPConnector()
            proxy_status = "✅ Conexión directa"
        
        # PASO 4: PREPARAR CONEXIÓN MOODLE
        await message.edit(f"🌐 Conectando a Moodle...\n\n"
                          f"🏫 Plataforma: {host}\n"
                          f"👤 Usuario: {usern}\n"
                          f"{proxy_status}")
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36'}
        
        async with aiohttp.ClientSession(headers=headers, connector=connector) as session:
            client = MoodleCli(usern, pasw, host, repoid, session)
            
            # PASO 5: INTENTAR LOGIN
            i = 1
            max_attempts = 10
            
            while i <= max_attempts:
                try:
                    attempt_msg = f"🔐 Intentando login ({i}/{max_attempts})..."
                    await message.edit(attempt_msg)
                    
                    login = await client.login()
                    
                    if login:
                        await message.edit("✅ ✅ ✅ LOGIN EXITOSO!\n\n"
                                          f"Bienvenido: {usern}\n"
                                          f"Servidor: {host}\n"
                                          f"Preparando subida...")
                        break
                    else:
                        await message.edit(f"❌ Login fallido ({i}/{max_attempts})\n\n"
                                          f"Credenciales incorrectas\n"
                                          f"Usuario: {usern}\n"
                                          f"Reintentando en 3 segundos...")
                        i += 1
                        await asyncio.sleep(3)
                        
                except aiohttp.ClientConnectorError as e:
                    await message.edit(f"🌐 Error de conexión ({i}/{max_attempts})\n\n"
                                      f"No se pudo conectar al servidor\n"
                                      f"{host}\n"
                                      f"Error: {str(e)[:100]}")
                    i += 1
                    await asyncio.sleep(3)
                    
                except aiohttp.ClientResponseError as e:
                    await message.edit(f"📡 Error del servidor ({i}/{max_attempts})\n\n"
                                      f"HTTP {e.status}: {e.message}\n"
                                      f"Servidor: {host}")
                    i += 1
                    await asyncio.sleep(3)
                    
                except Exception as e:
                    await message.edit(f"⚠️ Error desconocido ({i}/{max_attempts})\n\n"
                                      f"{str(e)[:150]}")
                    i += 1
                    await asyncio.sleep(3)
            
            # VERIFICAR SI LOGIN FALLÓ DESPUÉS DE TODOS LOS INTENTOS
            if i > max_attempts:
                await message.edit("❌❌❌ LOGIN FALLIDO\n\n"
                                  f"Se intentó {max_attempts} veces\n"
                                  f"Servidor: {host}\n"
                                  f"Usuario: {usern}\n\n"
                                  f"Posibles causas:\n"
                                  f"1. Credenciales incorrectas\n"
                                  f"2. Servidor fuera de línea\n"
                                  f"3. Proxy bloqueado\n"
                                  f"4. Red no disponible")
                return
            
            # PASO 6: OBTENER INFORMACIÓN DEL ARCHIVO
            name = os.path.basename(pathfull)
            size = os.path.getsize(pathfull)
            esize = 1024 * 1024 * int(zips)
            
            size_mb = size / (1024 * 1024)
            limit_mb = esize / (1024 * 1024)
            
            await message.edit(f"📄 Información del archivo:\n\n"
                              f"📌 Nombre: {name}\n"
                              f"📦 Tamaño: {size_mb:.2f} MB\n"
                              f"⚡ Límite por parte: {limit_mb:.0f} MB\n"
                              f"🔢 Partes necesarias: {1 if size <= esize else 'Múltiples'}")
            
            await asyncio.sleep(2)
            
            # PASO 7: VERIFICAR SI NECESITA COMPRIMIR
            if size > esize:
                await message.edit(f"🗜️ Archivo muy grande\n\n"
                                  f"Comprimiendo en partes de {limit_mb:.0f} MB...\n"
                                  f"Esto puede tomar unos momentos ⏳")
                
                files = zipfile.MultiFile(pathfull, esize)
                zfile = zipfile.ZipFile(files, mode="w", compression=zipfile.ZIP_DEFLATED)
                zfile.write(pathfull)
                zfile.close()
                files.close()
                
                await message.edit(f"✅ Compresión completada\n\n"
                                  f"📦 Partes creadas: {len(files.files)}\n"
                                  f"📁 Preparando subida...")
                
                # PASO 8: SUBIR ARCHIVOS MULTIPARTES
                urls = []
                total_parts = len(files.files)
                
                for part_num, f in enumerate(files.files, 1):
                    part_size = os.path.getsize(f)
                    part_size_mb = part_size / (1024 * 1024)
                    
                    await message.edit(f"📤 Subiendo parte {part_num}/{total_parts}\n\n"
                                      f"📌 Archivo: {os.path.basename(f)}\n"
                                      f"📦 Tamaño: {part_size_mb:.2f} MB\n"
                                      f"⏳ Por favor espere...")
                    
                    upload_result = await client.upload(f)
                    
                    if upload_result:
                        await message.edit(f"✅ Parte {part_num}/{total_parts} subida!\n\n"
                                          f"✓ {os.path.basename(f)}\n"
                                          f"✓ {part_size_mb:.2f} MB\n"
                                          f"✓ Generando enlace...")
                        
                        tokenurl = await client.linkcalendar(upload_result)
                        if tokenurl:
                            token = await gettoken(usern, pasw, session, host)
                            urltoken = tokenurl.replace("pluginfile.php", "webservice/pluginfile.php")
                            final_url = f"{urltoken}?token={token}"
                            urls.append(final_url)
                            
                            await message.edit(f"🔗 Enlace {part_num}/{total_parts} generado\n\n"
                                              f"✓ URL preparada\n"
                                              f"✓ Token aplicado\n"
                                              f"✓ Listo para uso")
                    else:
                        await message.edit(f"❌ Error subiendo parte {part_num}")
                        break
                    
                    await asyncio.sleep(1)
                
                # LIMPIAR ARCHIVOS TEMPORALES
                for f in files.files:
                    try:
                        os.unlink(f)
                    except:
                        pass
                
                # PASO 9: MOSTRAR RESULTADOS FINALES (MULTIPARTES)
                if len(urls) == total_parts:
                    msgurls = ""
                    for idx, url in enumerate(urls, 1):
                        short_url = await shorturl(url)
                        if short_url:
                            msgurls += f"🔗 Parte {idx}: {short_url}\n"
                        else:
                            msgurls += f"🔗 Parte {idx}: {url[:50]}...\n"
                    
                    await message.edit(f"🎉 ¡SUBIDA COMPLETADA CON ÉXITO!\n\n"
                                      f"📌 Nombre: {name}\n"
                                      f"📦 Tamaño total: {size_mb:.2f} MB\n"
                                      f"🔢 Partes: {total_parts}\n"
                                      f"✅ Estado: 100% completado\n\n"
                                      f"📋 Enlaces generados:\n{msgurls}")
                else:
                    await message.edit(f"⚠️ Subida parcialmente completada\n\n"
                                      f"Subidas exitosas: {len(urls)}/{total_parts}\n"
                                      f"Consulte los enlaces disponibles")
            
            else:
                # PASO 10: SUBIR ARCHIVO ÚNICO (sin comprimir)
                await message.edit(f"📤 Subiendo archivo único\n\n"
                                  f"📌 {name}\n"
                                  f"📦 {size_mb:.2f} MB\n"
                                  f"⏳ Por favor espere...")
                
                upload_result = await client.upload(pathfull)
                
                if upload_result:
                    await message.edit(f"✅ Archivo subido exitosamente!\n\n"
                                      f"✓ {name}\n"
                                      f"✓ {size_mb:.2f} MB\n"
                                      f"✓ Generando enlace final...")
                    
                    tokenurl = await client.linkcalendar(upload_result)
                    if tokenurl:
                        token = await gettoken(usern, pasw, session, host)
                        urltoken = tokenurl.replace("pluginfile.php", "webservice/pluginfile.php")
                        final_url = f"{urltoken}?token={token}"
                        
                        short_url = await shorturl(final_url)
                        
                        await message.edit(f"🎉 ¡ARCHIVO SUBIDO CON ÉXITO!\n\n"
                                          f"📌 Nombre: {name}\n"
                                          f"📦 Tamaño: {size_mb:.2f} MB\n"
                                          f"✅ Estado: Completado 100%\n\n"
                                          f"🔗 Enlace directo:\n"
                                          f"{short_url if short_url else final_url[:100]}...")
                    else:
                        await message.edit("⚠️ Archivo subido pero no se pudo generar enlace")
                else:
                    await message.edit("❌ Error al subir el archivo")
    
    except Exception as e:
        error_msg = str(e)
        await message.edit(f"🔥 ERROR CRÍTICO\n\n"
                          f"❌ {error_msg[:200]}\n\n"
                          f"📍 Paso fallido: Subida a Moodle\n"
                          f"👤 Usuario: {username}\n"
                          f"🕐 Hora: {time.strftime('%H:%M:%S')}")
        print(f"Error en upload: {traceback.format_exc()}")

async def shorturl(url):
    query = {"url": str(url)}
    daurl = URL("https://da.gd/shorten/")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(daurl.with_query(query)) as response:
                return URL(await response.text())
    except:
        return None

async def gettoken(usern, pasw, session, moodle):
    query = {"service": "moodle_mobile_app",
             "username": usern,
             "password": pasw}
    tokenurl = URL(moodle).with_path("login/token.php").with_query(query)
    try:
        async with session.get(tokenurl) as resp:
            respjson = await resp.json()
            return respjson["token"]
    except Exception as exc:
        print(exc)
        return None

def proxyparsed(proxy):
    trans = str.maketrans(
        "@./=#$%&:,;_-|0123456789abcd3fghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
        "ZYXWVUTSRQPONMLKJIHGFEDCBAzyIwvutsrqponmlkjihgf3dcba9876543210|-_;,:&%$#=/.@",
    )
    return str.translate(proxy[::2], trans)

def convertbytes(size):
    if size >= 1024 * 1024 * 1024:
        sizeconvert = "{:.2f}".format(size / (1024 * 1024 * 1024))
        normalbytes = f"{sizeconvert} GiB"
    
    elif size >= 1024 * 1024:
        sizeconvert = "{:.2f}".format(size / (1024 * 1024))
        normalbytes = f"{sizeconvert} MiB"
    
    elif size >= 1024:
        sizeconvert = "{:.2f}".format(size / 1024)
        normalbytes = f"{sizeconvert} KiB"
    
    else:
        normalbytes = f"{size} B"
    
    return normalbytes

# ==================== MAIN CON SERVIDOR WEB ====================
if __name__ == "__main__":
    # Obtener puerto de variable de entorno o usar 5000 por defecto
    port = int(os.environ.get("PORT", 5000))
    
    # INICIAR SERVIDOR WEB PRIMERO (para Render)
    print(f"🌐 Starting health server on port {port}...")
    
    # Crear y empezar servidor ANTES del bot
    server_thread = threading.Thread(target=start_health_server, args=(port,), daemon=False)
    server_thread.start()
    
    # Esperar un momento para que Render detecte
    print("⏳ Waiting for Render to detect server...")
    time.sleep(3)
    
    print(f"✅ Health server started on port {port}")
    print("🤖 Starting Telegram bot...")
    
    # INICIAR BOT
    try:
        botclient.run_until_disconnected()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Bot error: {e}")
        traceback.print_exc()
    finally:
        print("👋 Bot stopped")
