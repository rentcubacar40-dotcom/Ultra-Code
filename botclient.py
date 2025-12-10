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
from aiohttp import web
import threading
import sys

# Variables globales
botclient = None
userstatus = {}
handler_registered = False

# ==================== SERVICIO WEB PARA RENDER ====================
async def health_check(request):
    """Endpoint para verificaciones de salud"""
    return web.Response(
        text='🤖 Bot Telegram activo y funcionando\n📡 Puerto: 5000\n🔄 Estado: OK',
        content_type='text/plain'
    )

async def webserver():
    """Servidor web forzando puerto 5000 para Render"""
    app = web.Application()
    
    # Agregar más endpoints para mejor monitoreo
    app.router.add_get('/', health_check)
    app.router.add_get('/health', health_check)
    app.router.add_get('/status', lambda r: web.Response(text='Online'))
    
    # FORZAR PUERTO 5000 - Render permite este puerto
    port = 5000
    
    # Configurar opciones del servidor
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Intentar con puerto 5000 específicamente
    try:
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        print(f"✅ Servidor web en puerto {port} - http://0.0.0.0:{port}")
        return runner, site
    except OSError as e:
        # Si falla el 5000, intentar con puerto dinámico
        print(f"⚠️  Puerto {port} no disponible: {e}")
        print("🔄 Intentando con puerto dinámico...")
        port = int(os.environ.get('PORT', 10000))
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        print(f"✅ Servidor web en puerto {port} - http://0.0.0.0:{port}")
        return runner, site

def run_webserver():
    """Ejecutar servidor web en hilo separado"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        runner, site = loop.run_until_complete(webserver())
        
        # Información adicional
        print("=" * 50)
        print("🌐 SERVICIO WEB INICIADO")
        print(f"📍 Puerto: {site._server.sockets[0].getsockname()[1]}")
        print(f"📡 Host: 0.0.0.0")
        print("=" * 50)
        
        # Mantener el servidor activo
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            print("🛑 Servidor web detenido")
    except Exception as e:
        print(f"❌ Error en servidor web: {e}")
        traceback.print_exc()

# ==================== FUNCIONES DEL BOT ====================
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

def register_handlers():
    """Registra los handlers UNA SOLA VEZ"""
    global handler_registered
    
    if handler_registered:
        return
    
    handler_registered = True
    
    @botclient.on(events.NewMessage)
    async def messages(event):
        # Evitar procesar mensajes antiguos
        if event.message.date < (time.time() - 10):
            return
        
        username = event.message.chat.username
        if not username:
            return
        
        id = event.message.chat.id
        msg = event.message.text
        
        print(f"📨 [{time.strftime('%H:%M:%S')}] @{username}: {msg[:50]}")
        
        # Validar acceso
        usernames = getusern(username)
        if username == OWNER or usernames:
            if usernames is None:
                makeuser(username)
        else:
            await botclient.send_message(id, "❌ No tiene acceso ❌")
            return
        
        # Manejar comandos
        if msg is None:
            return
        
        msg_lower = msg.lower()
        
        if msg_lower.startswith("/start"):
            msgtext = f"Sea bienvenido al bot @{username}.\nUtilice /mydata para recordar sus datos🙌."
            await event.reply(msgtext, link_preview=False)
        
        elif msg_lower.startswith("/acc"):
            splitmsg = msg.split(" ")
            
            if len(splitmsg) != 3:
                await event.reply("❌ Fallo en la escritura del comando\n👉 /acc username password 👈.", link_preview=False)
            else:
                usern = splitmsg[1]
                password = splitmsg[2]
                
                user = getusern(username)
                if user:
                    user["user"] = usern
                    user["passw"] = password
                    savedata(username, user)
                    message = mydata(username)
                    await event.reply(message, link_preview=False)
        
        elif msg_lower.startswith("/host"):
            splitmsg = msg.split(" ")
            
            if len(splitmsg) != 2:
                await event.reply("❌ Fallo en la escritura del comando\n👉 /host https://moodle.dominio.cu 👈.", link_preview=False)
            else:
                host = splitmsg[1]
                
                user = getusern(username)
                if user:
                    user["host"] = host
                    savedata(username, user)
                    message = mydata(username)
                    await event.reply(message, link_preview=False)
        
        elif msg_lower.startswith("/repoid"):
            splitmsg = msg.split(" ")
            
            if len(splitmsg) != 2:
                await event.reply("❌ Fallo en la escritura del comando\n👉 /repoid repoid 👈.", link_preview=False)
            else:
                repoid = splitmsg[1]
                
                user = getusern(username)
                if user:
                    user["repoid"] = repoid
                    savedata(username, user)
                    message = mydata(username)
                    await event.reply(message, link_preview=False)
        
        elif msg_lower.startswith("/proxy"):
            splitmsg = msg.split(" ")
            
            if len(splitmsg) != 2:
                await event.reply("❌ Fallo en la escritura del comando\n👉 /proxy proxy 👈.", link_preview=False)
            else:
                proxymsg = splitmsg[1]
                proxys = proxyparsed(proxymsg)
                proxy = f"socks5://{proxys}"
                
                user = getusern(username)
                if user:
                    user["proxy"] = proxy
                    savedata(username, user)
                    message = mydata(username)
                    await event.reply(message, link_preview=False)
        
        elif msg_lower.startswith("/zips"):
            splitmsg = msg.split(" ")
            
            if len(splitmsg) != 2:
                await event.reply("❌ Fallo en la escritura del comando\n👉 /zips size 👈.", link_preview=False)
            else:
                zips = splitmsg[1]
                
                user = getusern(username)
                if user:
                    user["zips"] = zips
                    savedata(username, user)
                    message = mydata(username)
                    await event.reply(message, link_preview=False)
        
        elif msg_lower.startswith("/mydata"):
            message = mydata(username)
            await event.reply(message, link_preview=False)
        
        elif msg_lower.startswith("/add"):
            splitmsg = msg.split(" ")
            
            if len(splitmsg) != 2:
                await event.reply("❌ Fallo en la escritura del comando\n👉 /add username 👈.", link_preview=False)
            else:
                usuario = splitmsg[1]
                
                makeuser(usuario)
                await event.reply(f"✅ Añadido @{usuario} al uso del bot.", link_preview=False)
        
        elif msg_lower.startswith("/ban"):
            splitmsg = msg.split(" ")
            
            if len(splitmsg) != 2:
                await event.reply("❌ Fallo en la escritura del comando\n👉 /ban username 👈.", link_preview=False)
            else:
                usuario = splitmsg[1]
                
                outusern(usuario)
                await event.reply(f"❌ Baneado @{usuario} del uso del bot.", link_preview=False)
        
        elif msg_lower.startswith("http"):
            await handle_download(event, username, id, msg)
        
        elif event.message.media:
            await handle_media_download(event, username, id)
    
    @botclient.on(events.CallbackQuery)
    async def callback(event):
        username = event.chat.username
        if event.data == b"cancelado":
            user_key = f"{username}_{event.chat.id}"
            if user_key in userstatus:
                userstatus[user_key]["statusdownload"] = "pasive"

# ==================== FUNCIONES AUXILIARES ====================
async def handle_download(event, username, id, url):
    """Manejar descargas HTTP"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    await event.reply("❌ Error al descargar el archivo")
                    return
                
                try:
                    name = response.content_disposition.filename
                except:
                    name = url.split("/")[-1]
                
                size = int(response.headers.get("content-length", 0))
                
                message = await botclient.send_message(id, "💠 Preparando descarga 💠")
                
                if not os.path.exists(username):
                    os.mkdir(username)
                
                userpath = username
                pathfull = os.path.join(os.getcwd(), userpath, name)
                
                async with aiofiles.open(pathfull, "wb") as fi:
                    chunkcurrent = 0
                    starttime = time.time()
                    secs = 0
                    
                    user_key = f"{username}_{id}"
                    async for chunk in response.content.iter_chunked(1024 * 1024):
                        if userstatus.get(user_key, {}).get("statusdownload") != "active":
                            break
                        
                        chunkcurrent += len(chunk)
                        currenttime = time.time() - starttime
                        speed = chunkcurrent / currenttime if currenttime > 0 else 0
                        secs += len(chunk)
                        
                        if secs >= 5242880:
                            await downloadprogressmust(chunkcurrent, size, speed, message, name)
                            secs = 0
                        
                        await fi.write(chunk)
                
                if userstatus.get(user_key, {}).get("statusdownload") == "active":
                    await botclient.edit_message(message, "✅ Descarga Finalizada ✅")
                    await upload(pathfull, message, username)
                else:
                    await botclient.edit_message(message, "❌ Descarga Cancelada ❌")
                    if os.path.exists(pathfull):
                        os.remove(pathfull)
                        
    except Exception as e:
        print(f"❌ Error en descarga: {e}")
        await event.reply(f"❌ Error al procesar la descarga: {str(e)}")

async def handle_media_download(event, username, id):
    """Manejar descargas de media de Telegram"""
    try:
        name = event.file.name or f"media_{int(time.time())}"
        size = event.file.size
        
        message = await botclient.send_message(id, "💠 Preparando descarga 💠")
        
        if not os.path.exists(username):
            os.mkdir(username)
        
        userpath = username
        pathfull = os.path.join(os.getcwd(), userpath, name)
        
        with open(pathfull, "wb") as fi:
            chunkcurrent = 0
            starttime = time.time()
            secs = 0
            
            user_key = f"{username}_{id}"
            async for chunk in botclient.iter_download(event.message.media, chunk_size=1024 * 1024):
                if userstatus.get(user_key, {}).get("statusdownload") != "active":
                    break
                
                chunkcurrent += len(chunk)
                currenttime = time.time() - starttime
                speed = chunkcurrent / currenttime if currenttime > 0 else 0
                secs += len(chunk)
                
                if secs >= 5242880:
                    await downloadprogressmust(chunkcurrent, size, speed, message, name)
                    secs = 0
                
                fi.write(chunk)
        
        if userstatus.get(user_key, {}).get("statusdownload") == "active":
            await botclient.edit_message(message, "✅ Descarga Finalizada ✅")
            await upload(pathfull, message, username)
        else:
            await botclient.edit_message(message, "❌ Descarga Cancelada ❌")
            if os.path.exists(pathfull):
                os.remove(pathfull)
                
    except Exception as e:
        print(f"❌ Error en descarga de media: {e}")
        await event.reply(f"❌ Error al procesar el archivo: {str(e)}")

async def downloadprogressmust(chunkcurrent, size, speed, message, name):
    buttons = [[Button.inline("❌ Cancelar ❌", "cancelado")]]
    bytesnormalsize = convertbytes(size)
    bytesnormalcurrent = convertbytes(chunkcurrent)
    bytesnormalspeed = convertbytes(speed)
    
    msgprogress = f"📌 File Name: {name}\n\n"
    msgprogress += f"📦 File Size: {bytesnormalsize}\n\n"
    msgprogress += f"📥 Downloading: {bytesnormalcurrent}\n\n"
    msgprogress += f"⚡ Speed: {bytesnormalspeed}/s"
    
    try:
        await botclient.edit_message(message, msgprogress, buttons=buttons)
    except:
        pass

async def upload(pathfull, message, username):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36'}
    user = getusern(username)
    proxy = user["proxy"]
    if proxy == "__Desactivado❌__":
        connector = aiohttp.TCPConnector()
    else:
        connector = ProxyConnector.from_url(proxy)
    
    zips = user["zips"]
    if zips == "__Sin Definir__":
        zips = 500
    
    name = pathfull.split("/")[-1]
    
    size = os.path.getsize(pathfull)
    esize = 1024 * 1024 * int(zips)
    
    if size > esize:
        await message.edit(f"✂ Picando en partes de {convertbytes(esize)} 📦")
        files = zipfile.MultiFile(pathfull, esize)
        zips = zipfile.ZipFile(files, mode="w", compression=zipfile.ZIP_DEFLATED)
        zips.write(pathfull)
        zips.close()
        files.close()
        
        await message.edit("💠 Preparando subida 💠")
        
        async with aiohttp.ClientSession(headers=headers, connector=connector) as session:
            usern = user["user"]
            pasw = user["passw"]
            host = user["host"]
            repoid = user["repoid"]
            client = MoodleCli(usern, pasw, host, repoid, session)
            urls = []
            i = 1
            while i < 10:
                try:
                    login = await client.login()
                    if login:
                        for f in files.files:
                            upload = await client.upload(f)
                            try:
                                await message.edit(f"📌 File Name: {name}\n\n📤 Uploading: {f.split('/')[-1]}\n\n📦 Part Size: {convertbytes(os.path.getsize(f))}\n\n")
                            except:
                                pass
                            tokenurl = await client.linkcalendar(upload)
                            if tokenurl:
                                token = await gettoken(usern, pasw, session, host)
                                urltoken = tokenurl.replace("pluginfile.php", "webservice/pluginfile.php")
                                upload = f"{urltoken}?token={token}"
                                urls.append(upload)
                        break
                    else:
                        await message.edit("❌ Credenciales invalidas ❌")
                except:
                    print(traceback.format_exc())
                    
                    await message.edit(f"❌ Fallos en la moodle ❌\n↩ Reintentando {i} ⤴")
                    i += 1
            
            if i == 10:
                await message.edit(f"❌ Se reintento {i} veces ❌\n🎃 Moodle completamente caida 🎃")
            else:
                msgurls = ""
                for url in urls:
                    shortsurls = await shorturl(url)
                    msgurls += f"🔗 {shortsurls} 🔗\n"
                await message.edit(f"✅ Subida Finalizada\n📌 Nombre: {name}\n📦 Tamaño: {convertbytes(size)}\n\n📌 Enlaces 📌\n{msgurls}")
    else:
        await message.edit("💠 Preparando subida 💠")
        
        async with aiohttp.ClientSession(headers=headers, connector=connector) as session:
            usern = user["user"]
            pasw = user["passw"]
            host = user["host"]
            repoid = user["repoid"]
            client = MoodleCli(usern, pasw, host, repoid, session)
            
            i = 1
            while i < 10:
                try:
                    login = await client.login()
                    if login:
                        upload = await client.upload(pathfull)
                        try:
                            await message.edit(f"📌 File Name: {name}\n\n📤 Uploading: {name}\n\n📦 File Size: {convertbytes(size)}\n\n")
                        except:
                            pass
                        tokenurl = await client.linkcalendar(upload)
                        if tokenurl:
                            token = await gettoken(usern, pasw, session, host)
                            urltoken = tokenurl.replace("pluginfile.php", "webservice/pluginfile.php")
                            upload = f"{urltoken}?token={token}"
                        break
                    else:
                        await message.edit("❌ Credenciales invalidas ❌")
                except:
                    print(traceback.format_exc())
                    
                    await message.edit(f"❌ Fallos en la moodle ❌\n↩ Reintentando {i} ⤴")
                    i += 1
            
            if i == 10:
                await message.edit(f"❌ Se reintento {i} veces ❌\n🎃 Moodle completamente caida 🎃")
            else:
                shortsurls = await shorturl(upload)
                await message.edit(f"✅ Subida Finalizada\n📌 Nombre: {name}\n📦 Tamaño: {convertbytes(size)}\n\n📌 Enlaces 📌\n🔗 {shortsurls} 🔗")

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

# ==================== MAIN ====================
def main():
    """Función principal"""
    global botclient
    
    print("=" * 60)
    print("🚀 INICIANDO BOT DE TELEGRAM CON PUERTO 5000")
    print("=" * 60)
    print(f"👤 Owner: {OWNER}")
    print(f"📡 Puerto forzado: 5000")
    print(f"🕐 Hora: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Inicializar el cliente UNA SOLA VEZ
    if botclient is None:
        botclient = Client('bot', api_id=api_id, api_hash=api_hash)
        botclient.start(bot_token=bot_token)
    
    # Iniciar servidor web en puerto 5000
    print("🌐 Iniciando servidor web en puerto 5000...")
    server_thread = threading.Thread(target=run_webserver, daemon=True)
    server_thread.start()
    
    # Esperar que el servidor web inicie
    time.sleep(2)
    
    # Registrar handlers UNA SOLA VEZ
    register_handlers()
    
    print("✅ Bot completamente inicializado")
    print("🤖 Esperando mensajes de Telegram...")
    print("=" * 60)
    
    # Ejecutar el bot principal
    try:
        botclient.run_until_disconnected()
    except KeyboardInterrupt:
        print("\n🛑 Bot detenido por usuario")
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        traceback.print_exc()
    finally:
        print("👋 Bot detenido")

if __name__ == "__main__":
    # Verificar ejecución única
    if hasattr(__name__, '_already_running'):
        print("⚠️  El bot ya está en ejecución")
        sys.exit(0)
    
    __name__._already_running = True
    main()
