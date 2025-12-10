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
botclient = Client('bot', api_id=api_id, api_hash=api_hash).start(bot_token=bot_token)
userstatus = {}

# Servidor web para Render
async def health_check(request):
    """Endpoint para verificaciones de salud"""
    return web.Response(text='🤖 Bot Telegram activo y funcionando')

async def webserver():
    """Servidor web minimal para Render"""
    app = web.Application()
    app.router.add_get('/', health_check)
    app.router.add_get('/health', health_check)
    
    port = int(os.environ.get('PORT', 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"✅ Servidor web escuchando en http://0.0.0.0:{port}")
    return runner, site

def run_webserver():
    """Ejecutar servidor web en hilo separado"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        runner, site = loop.run_until_complete(webserver())
        
        # Mantener el servidor activo
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            print("🛑 Servidor web detenido")
    except Exception as e:
        print(f"❌ Error en servidor web: {e}")

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
        await botclient.send_message(id, "❌ No tiene acceso ❌")
        return
    
    userstatus[username] = {"statusdownload": "active"}
    
    if msg.lower().startswith("/start"):
        msgtext = f"Sea bienvenido al bot @{username}.\nUtilize /mydata para recordar sus datos🙌."
        await event.reply(msgtext)
    
    if msg.lower().startswith("/acc"):
        splitmsg = msg.split(" ")
        
        if len(splitmsg) != 3:
            await event.reply("❌ Fallo en la escritura del comando\n👉 /acc username password 👈.")
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
            await event.reply("❌ Fallo en la escritura del comando\n👉 /host https://moodle.dominio.cu 👈.")
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
            await event.reply("❌ Fallo en la escritura del comando\n👉 /repoid repoid 👈.")
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
            await event.reply("❌ Fallo en la escritura del comando\n👉 /proxy proxy 👈.")
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
            await event.reply("❌ Fallo en la escritura del comando\n👉 /zips size 👈.")
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
            await event.reply("❌ Fallo en la escritura del comando\n👉 /add username 👈.")
        else:
            usuario = splitmsg[1]
            
            makeuser(usuario)
            await event.reply(f"✅ Añadido @{usuario} al uso del bot.")
    
    if msg.lower().startswith("/ban"):
        splitmsg = msg.split(" ")
        
        if len(splitmsg) != 2:
            await event.reply("❌ Fallo en la escritura del comando\n👉 /ban username 👈.")
        else:
            usuario = splitmsg[1]
            
            outusern(usuario)
            await event.reply("❌ Baneado @{usuario} del uso del bot.")
    
    if msg.lower().startswith("https"):
        async with aiohttp.ClientSession() as session:
            async with session.get(msg) as response:
                try:
                    name = response.content_disposition.filename
                except:
                    name = msg.split("/")[-1]
                
                size = int(response.headers.get("content-length"))
                
                message = await botclient.send_message(id, "💠 Preparando descarga 💠")
                
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
                    speed = chunkcurrent / currenttime
                    secs += len(chunk)
                    
                    if secs >= 5242880:
                        await downloadprogressmust(chunkcurrent, size, speed, message, name)
                        secs = 0
                    await fi.write(chunk)
                fi.close()
                
                if userstatus[username]["statusdownload"] == "active":
                    await botclient.edit_message(message, "✅ Descarga Finalizada ✅")
                    await upload(pathfull, message, username)
                else:
                    await botclient.edit_message(message, "❌ Descarga Eliminada ❌")
    
    if event.message.media:
        name = event.file.name
        size = event.file.size
        
        message = await botclient.send_message(id, "💠 Preparando descarga 💠")
        
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
            speed = chunkcurrent / currenttime
            secs += len(chunk)
            
            if secs >= 5242880:
                await downloadprogressmust(chunkcurrent, size, speed, message, name)
                secs = 0
            fi.write(chunk)
        fi.close()
        
        if userstatus[username]["statusdownload"] == "active":
            await botclient.edit_message(message, "✅ Descarga Finalizada ✅")
            await upload(pathfull, message, username)
        else:
            await botclient.edit_message(message, "❌ Descarga Eliminada ❌")

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

def main():
    """Función principal mejorada"""
    print("🚀 Iniciando Bot de Telegram...")
    print(f"👤 Owner: {OWNER}")
    
    # Iniciar servidor web para Render
    server_thread = threading.Thread(target=run_webserver, daemon=True)
    server_thread.start()
    
    print("✅ Servidor web iniciado en segundo plano")
    
    # Dar tiempo al servidor para iniciar
    time.sleep(1)
    
    # Ejecutar el bot principal
    try:
        print("🤖 Conectando a Telegram...")
        botclient.run_until_disconnected()
    except KeyboardInterrupt:
        print("\n👋 Bot detenido por usuario")
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        print(traceback.format_exc())
    finally:
        print("👋 Bot detenido")

if __name__ == "__main__":
    main()
