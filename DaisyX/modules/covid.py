import requests
from telegram import ParseMode, Update
from telegram.ext import CallbackContext, run_async

from DaisyX import dispatcher
from DaisyX.modules.disable import DisableAbleCommandHandler


@run_async
def covid(update: Update, context: CallbackContext):
    message = update.effective_message
    text = message.text.split(" ", 1)
    if len(text) == 1:
        r = requests.get("https://corona.lmao.ninja/v2/all").json()
        reply_text = f"*Total Global* 🦠\nkasus: {r['cases']:,}\nKasus Hari Ini: {r['todayCases']:,}\nMeninggal: {r['deaths']:,}\nKematian Hari Ini: {r['todayDeaths']:,}\nPulih: {r['recovered']:,}\nAktif: {r['active']:,}\nKritis: {r['critical']:,}\nKasus/Mil: {r['casesPerOneMillion']}\nKematian/Mil: {r['deathsPerOneMillion']}"
    else:
        variabla = text[1]
        r = requests.get(f"https://corona.lmao.ninja/v2/countries/{variabla}").json()
        reply_text = f"*Kasus untuk {r['country']} 🦠*\nkasus: {r['cases']:,}\nKasus Hari Ini: {r['todayCases']:,}\nMeninggal: {r['deaths']:,}\nKematian Hari Ini: {r['todayDeaths']:,}\nPulih: {r['recovered']:,}\nAktif: {r['active']:,}\nKritis: {r['critical']:,}\nKasus/Mil: {r['casesPerOneMillion']}\nKematian/Mil: {r['deathsPerOneMillion']}"
    message.reply_text(reply_text, parse_mode=ParseMode.MARKDOWN)


COVID_HANDLER = DisableAbleCommandHandler(["covid", "corona"], covid)
dispatcher.add_handler(COVID_HANDLER)
