import requests
from DaisyX.events import register
from DaisyX import telethn as tbot


@register(pattern="^/asupan ?(.*)")
async def asupan(event):
    try:
        resp = requests.get("https://tede-api.herokuapp.com/api/asupan/ptl").json()
        asupannya = f"{resp['url']}"
        return await tbot.send_file(event.chat_id, asupannya)
    except Exception:
        await event.reply("`Tunggu bentar NYETT...`")


@register(pattern="^/wibu ?(.*)")
async def wibu(event):
    try:
        resp = requests.get("https://tede-api.herokuapp.com/api/asupan/wibu").json()
        wibunya = f"{resp['url']}"
        return await tbot.send_file(event.chat_id, wibunya)
    except Exception:
        await event.reply("`Tunggu bentar NYETT...`")
