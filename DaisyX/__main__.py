import html
import importlib
import json
import re
import time
import traceback
from sys import argv
from typing import Optional

from telegram import (
    Chat,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    ParseMode,
    Update,
    User,
)
from telegram.error import (
    BadRequest,
    ChatMigrated,
    NetworkError,
    TelegramError,
    TimedOut,
    Unauthorized,
)
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
)
from telegram.ext.dispatcher import DispatcherHandlerStop, run_async
from telegram.utils.helpers import escape_markdown

from DaisyX import (
    ALLOW_EXCL,
    BL_CHATS,
    CERT_PATH,
    DONATION_LINK,
    LOGGER,
    OWNER_ID,
    PORT,
    SUPPORT_CHAT,
    TOKEN,
    URL,
    WEBHOOK,
    WHITELIST_CHATS,
    StartTime,
    dispatcher,
    pbot,
    telethn,
    updater,
)

# needed to dynamically load modules
# NOTE: Module order is not guaranteed, specify that in the config file!
from DaisyX.modules import ALL_MODULES
from DaisyX.modules.helper_funcs.alternate import typing_action
from DaisyX.modules.helper_funcs.chat_status import is_user_admin
from DaisyX.modules.helper_funcs.misc import paginate_modules
from DaisyX.modules.helper_funcs.readable_time import get_readable_time

PM_START_TEXT = """
*👋🏻 Hallo, Nama saya* [𝗣𝗥𝗔𝗕𝗨](https://telegra.ph/file/0ba3d33fa76b33add2ac2.jpg)
*Dikelolah oleh* [sᴛᴇᴠᴀɴ](tg://user?id=1521165553)
*┈───────────────────┈
Saya adalah robot manajemen bertemakan Maung Bandung,
Saya disini untuk membantu anda melindungi grup anda dari para pengguna telegram yang meresahkan,
Dengan jurus super Raungan, saya bisa membasmi mereka semua dengan sangat mudah
┈───────────────────┈
🔻 Silahkan klik tombol bantuan untuk mendapatkan informasi*
"""

buttons = [
    [
        InlineKeyboardButton(
            text="💫 ᴛᴀᴍʙᴀʜᴋᴀɴ 𝗣𝗥𝗔𝗕𝗨 ᴋᴇ ɢʀᴜᴘ 💫", url="t.me/PrabuXRobot?startgroup=true"),
    ],
    [
        InlineKeyboardButton(text="⚔️ ʙᴀɴᴛᴜᴀɴ", callback_data="aboutmanu_"
        ),
        InlineKeyboardButton(
            text="sᴜᴘᴘᴏʀᴛ 💬", url="t.me/PrabuXSupport"
        ),
    ],
]


HELP_STRINGS = f"""
*Perintah Utama:* [🤖](https://telegra.ph/file/9b59e879018641b53ec5a.jpg)
*✪ /start: Mulai saya! Anda mungkin sudah menggunakan ini.
✪ /help: Klik ini, saya akan memberi tahu Anda tentang diri saya!
✪ /donate: Anda dapat mendukung pembuat saya menggunakan perintah ini.
✪ /settings:
   ◔ di PM: akan mengirimkan pengaturan Anda untuk semua modul yang didukung.
   ◔ di Grup: akan mengarahkan Anda ke pm, dengan semua pengaturan obrolan itu.‌‌*
""".format(
    dispatcher.bot.first_name,
    "" if not ALLOW_EXCL else "\nSemua perintah dapat digunakan dengan / atau !.\n",
)


DONATE_STRING = """*Hai Senang Rasanya Anda Mau Berdonasi*
*Donasi Pulsa:* 089525658633
*Donasi E-Wallet:* [SAWERIA](https://saweria.co/GohanRobotDonate]"""


IMPORTED = {}
MIGRATEABLE = []
HELPABLE = {}
STATS = []
USER_INFO = []
USER_BOOK = []
DATA_IMPORT = []
DATA_EXPORT = []

CHAT_SETTINGS = {}
USER_SETTINGS = {}

GDPR = []


for module_name in ALL_MODULES:
    imported_module = importlib.import_module("DaisyX.modules." + module_name)
    if not hasattr(imported_module, "__mod_name__"):
        imported_module.__mod_name__ = imported_module.__name__

    if not imported_module.__mod_name__.lower() in IMPORTED:
        IMPORTED[imported_module.__mod_name__.lower()] = imported_module
    else:
        raise Exception("Can't have two modules with the same name! Please change one")

    if hasattr(imported_module, "__help__") and imported_module.__help__:
        HELPABLE[imported_module.__mod_name__.lower()] = imported_module

    # Chats to migrate on chat_migrated events
    if hasattr(imported_module, "__migrate__"):
        MIGRATEABLE.append(imported_module)

    if hasattr(imported_module, "__stats__"):
        STATS.append(imported_module)

    if hasattr(imported_module, "__gdpr__"):
        GDPR.append(imported_module)

    if hasattr(imported_module, "__user_info__"):
        USER_INFO.append(imported_module)

    if hasattr(imported_module, "__user_book__"):
        USER_BOOK.append(imported_module)

    if hasattr(imported_module, "__import_data__"):
        DATA_IMPORT.append(imported_module)

    if hasattr(imported_module, "__export_data__"):
        DATA_EXPORT.append(imported_module)

    if hasattr(imported_module, "__chat_settings__"):
        CHAT_SETTINGS[imported_module.__mod_name__.lower()] = imported_module

    if hasattr(imported_module, "__user_settings__"):
        USER_SETTINGS[imported_module.__mod_name__.lower()] = imported_module


# do not async
def send_help(chat_id, text, keyboard=None):
    if not keyboard:
        keyboard = InlineKeyboardMarkup(paginate_modules(0, HELPABLE, "help"))
    dispatcher.bot.send_message(
        chat_id=chat_id, text=text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard
    )


@run_async
def test(update, context):
    try:
        print(update)
    except:
        pass
    update.effective_message.reply_text(
        "Halo penguji! Saya sudah `markdown`", parse_mode=ParseMode.MARKDOWN
    )
    update.effective_message.reply_text("This person edited a message")
    print(update.effective_message)


@run_async
def start(update: Update, context: CallbackContext):
    args = context.args
    uptime = get_readable_time((time.time() - StartTime))
    if update.effective_chat.type == "private":
        if len(args) >= 1:
            if args[0].lower() == "help":
                send_help(update.effective_chat.id, HELP_STRINGS)
            elif args[0].lower().startswith("ghelp_"):
                mod = args[0].lower().split("_", 1)[1]
                if not HELPABLE.get(mod, False):
                    return
                send_help(
                    update.effective_chat.id,
                    HELPABLE[mod].__help__,
                    InlineKeyboardMarkup(
                        [[InlineKeyboardButton(text="Kembali", callback_data="help_back")]]
                    ),
                )

            elif args[0].lower().startswith("stngs_"):
                match = re.match("stngs_(.*)", args[0].lower())
                chat = dispatcher.bot.getChat(match.group(1))

                if is_user_admin(chat, update.effective_user.id):
                    send_settings(match.group(1), update.effective_user.id, False)
                else:
                    send_settings(match.group(1), update.effective_user.id, True)

            elif args[0][1:].isdigit() and "rules" in IMPORTED:
                IMPORTED["rules"].send_rules(update, args[0], from_pm=True)

        else:
            update.effective_message.reply_text(
                PM_START_TEXT,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.MARKDOWN,
                timeout=60,
            )
    else:
        update.effective_message.reply_text(
            "Aku sudah bangun!\n<b>Belum tidur sejak:</b> <code>{}</code>".format(
                uptime
            ),
            parse_mode=ParseMode.HTML,
        )


def error_handler(update, context):
    """Catat kesalahan dan kirim pesan telegram untuk memberi tahu pengembang."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    LOGGER.error(msg="Pengecualian saat menangani pembaruan:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(
        None, context.error, context.error.__traceback__
    )
    tb = "".join(tb_list)

    # Build the message with some markup and additional information about what happened.
    message = (
        "Pengecualian muncul saat menangani pembaruan\n"
        "<pre>update = {}</pre>\n\n"
        "<pre>{}</pre>"
    ).format(
        html.escape(json.dumps(update.to_dict(), indent=2, ensure_ascii=False)),
        html.escape(tb),
    )

    if len(message) >= 4096:
        message = message[:4096]
    # Finally, send the message
    context.bot.send_message(chat_id=OWNER_ID, text=message, parse_mode=ParseMode.HTML)


# for test purposes
def error_callback(update: Update, context: CallbackContext):
    error = context.error
    try:
        raise error
    except Unauthorized:
        print("no nono1")
        print(error)
        # remove update.message.chat_id from conversation list
    except BadRequest:
        print("no nono2")
        print("BadRequest caught")
        print(error)

        # handle malformed requests - read more below!
    except TimedOut:
        print("no nono3")
        # handle slow connection problems
    except NetworkError:
        print("no nono4")
        # handle other connection problems
    except ChatMigrated as err:
        print("no nono5")
        print(err)
        # the chat_id of a group has changed, use e.new_chat_id instead
    except TelegramError:
        print(error)
        # handle all other telegram related errors


@run_async
def help_button(update, context):
    query = update.callback_query
    mod_match = re.match(r"help_module\((.+?)\)", query.data)
    prev_match = re.match(r"help_prev\((.+?)\)", query.data)
    next_match = re.match(r"help_next\((.+?)\)", query.data)
    back_match = re.match(r"help_back", query.data)
    try:
        if mod_match:
            module = mod_match.group(1)
            text = (
                "*⚊❮❮❮❮ ｢  Bantuan untuk  {}  module 」❯❯❯❯⚊*\n".format(
                    HELPABLE[module].__mod_name__
                )
                + HELPABLE[module].__help__
            )
            query.message.edit_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(text="Kembali", callback_data="help_back")]]
                ),
            )

        elif prev_match:
            curr_page = int(prev_match.group(1))
            query.message.edit_text(
                HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(curr_page - 1, HELPABLE, "help")
                ),
            )

        elif next_match:
            next_page = int(next_match.group(1))
            query.message.edit_text(
                HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(next_page + 1, HELPABLE, "help")
                ),
            )

        elif back_match:
            query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, HELPABLE, "help")
                ),
            )

        # ensure no spinny white circle
        context.bot.answer_callback_query(query.id)
        # query.message.delete()
    except Exception as excp:
        if excp.message == "Message is not modified":
            pass
        elif excp.message == "Query_id_invalid":
            pass
        elif excp.message == "Message can't be deleted":
            pass
        else:
            query.message.edit_text(excp.message)
            LOGGER.exception("Pengecualian di tombol bantuan. %s", str(query.data))


@run_async
def DaisyX_about_callback(update, context):
    query = update.callback_query
    if query.data == "aboutmanu_":
        query.message.edit_text(
            text=""" ℹ️ Saya 𝗣𝗥𝗔𝗕𝗨, bot manajemen grup yang kuat yang dibuat untuk membantu Anda mengelola grup dengan mudah.
                 \n✪ Saya dapat membatasi pengguna.
                 \n✪ Saya dapat menyapa pengguna dengan pesan selamat datang yang dapat disesuaikan dan bahkan menetapkan aturan grup.
                 \n✪ Saya memiliki sistem anti-banjir yang canggih.
                 \n✪ Saya dapat memperingatkan pengguna hingga mereka mencapai peringatan maksimal, dengan setiap tindakan yang telah ditentukan sebelumnya seperti larangan, bisu, tendangan, dll.
                 \n✪ Saya memiliki sistem pencatatan, daftar hitam, dan bahkan balasan yang telah ditentukan sebelumnya pada kata kunci tertentu.
                 \n✪ Saya memeriksa izin admin sebelum menjalankan perintah apa pun dan lebih banyak barang
                 \n\n𝗣𝗥𝗔𝗕𝗨 licensed under the GNU General Public License v3.0
                 \n✪ Pengembang saya: [sᴛᴇᴠᴀɴ](tg://user?id=1521165553)
                 \n\nJika Anda memiliki pertanyaan tentang 𝗣𝗥𝗔𝗕𝗨, beri tahu kami""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="ᴀᴅᴍɪɴ sᴇᴛᴛɪɴɢs", callback_data="aboutmanu_permis"
                        ),
                        InlineKeyboardButton(
                            text="ᴀɴᴛɪ sᴘᴀᴍ", callback_data="aboutmanu_spamprot"
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            text="❔ ʙᴀɴᴛᴜᴀɴ & ᴘᴇʀɪɴᴛᴀʜ ❔", callback_data="help_back"
                        )
                    ],
                    [InlineKeyboardButton(text="Kembali", callback_data="aboutmanu_back")],
                ]
            ),
        )
    elif query.data == "aboutmanu_back":
        query.message.edit_text(
            PM_START_TEXT,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.MARKDOWN,
            timeout=60,
        )

    elif query.data == "aboutmanu_howto":
        query.message.edit_text(
            text=""" ℹ️ Saya 𝗣𝗥𝗔𝗕𝗨, bot manajemen grup yang kuat yang dibuat untuk membantu Anda mengelola grup dengan mudah.
                 \n✪ Saya dapat membatasi pengguna.
                 \n✪ Saya dapat menyapa pengguna dengan pesan selamat datang yang dapat disesuaikan dan bahkan menetapkan aturan grup.
                 \n✪ Saya memiliki sistem anti-banjir yang canggih.
                 \n✪ Saya dapat memperingatkan pengguna hingga mereka mencapai peringatan maksimal, dengan setiap tindakan yang telah ditentukan sebelumnya seperti larangan, bisu, tendangan, dll.
                 \n✪ Saya memiliki sistem pencatatan, daftar hitam, dan bahkan balasan yang telah ditentukan sebelumnya pada kata kunci tertentu.
                 \n✪ Saya memeriksa izin admin sebelum menjalankan perintah apa pun dan lebih banyak barang
                 \n\n𝗣𝗥𝗔𝗕𝗨 licensed under the GNU General Public License v3.0
                 \n✪ Pengembang saya: [sᴛᴇᴠᴀɴ](tg://user?id=1521165553)
                 \n\nJika Anda memiliki pertanyaan tentang 𝗣𝗥𝗔𝗕𝗨, beri tahu kami""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="Admins Settings", callback_data="aboutmanu_permis"
                        ),
                        InlineKeyboardButton(
                            text="Anti Spam", callback_data="aboutmanu_spamprot"
                        ),
                    ],
                    [InlineKeyboardButton(text="Kembali", callback_data="aboutmanu_")],
                ]
            ),
        )
    elif query.data == "aboutmanu_credit":
        query.message.edit_text(
            text=f"*{dispatcher.bot.first_name} Is the redisigned version of Daisy and Naruto for the best performance.*"
            f"\n\nBased on [Daisy](https://github.com/inukaasith/daisy) + [Naruto](https://github.com/imjanindu/narutorobot)."
            f"\n\n{dispatcher.bot.first_name}'s source code was written by InukaASiTH and Imjanindu"
            f"\n\nIf Any Question About {dispatcher.bot.first_name}, \nLet Us Know At @{SUPPORT_CHAT}.",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Back", callback_data="aboutmanu_tac")]]
            ),
        )

    elif query.data == "aboutmanu_permis":
        query.message.edit_text(
            text=f"<b> ｢ Izin Admin 」</b>"
            f"\nUntuk menghindari perlambatan, {dispatcher.bot.first_name} cache hak admin untuk setiap pengguna. Cache ini berlangsung sekitar 10 menit; ini dapat berubah di masa depan. Ini berarti jika Anda mempromosikan pengguna secara manual (tanpa menggunakan perintah /promote), {dispatcher.bot.first_name} hanya akan mengetahuinya ~ 10 menit kemudian."
            f"\n\nJIKA Anda ingin segera memperbaruinya, Anda dapat menggunakan perintah /admincache, itu akan memaksa {dispatcher.bot.first_name} untuk memeriksa siapa adminnya lagi dan izinnya"
            f"\n\nJika Anda mendapatkan pesan yang mengatakan:"
            f"\nAnda harus menjadi administrator obrolan ini untuk melakukan tindakan ini!"
            f"\nIni tidak ada hubungannya dengan {dispatcher.bot.first_name} hak; ini semua tentang izin ANDA sebagai admin. {dispatcher.bot.first_name} menghormati izin admin; jika Anda tidak memiliki izin Larangan Pengguna sebagai admin telegram, Anda tidak akan dapat memblokir pengguna dengan {dispatcher.bot.first_name}. Demikian pula, untuk mengubah {dispatcher.bot.first_name} pengaturan, Anda harus memiliki izin Ubah info grup."
            f"\n\nPesannya dengan sangat jelas mengatakan bahwa Anda membutuhkan hak-hak ini - tidak {dispatcher.bot.first_name}",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Kembali", callback_data="aboutmanu_")]]
            ),
        )
    elif query.data == "aboutmanu_spamprot":
        query.message.edit_text(
            text="* ｢ Pengaturan Anti-Spam 」*"
            "\n- /antispam <on/off/yes/no>: Ubah pengaturan keamanan antispam dalam grup, atau kembalikan pengaturan Anda saat ini (bila tidak ada argumen)."
            "\nIni membantu melindungi Anda dan grup Anda dengan menghapus pembanjir spam secepat mungkin."
            "\n\n- /setflood <int/'no'/'off'>: mengaktifkan atau menonaktifkan pengendalian banjir"
            "\n- /setfloodmode <ban/kick/mute/tban/tmute> <value>: Tindakan yang harus dilakukan ketika pengguna telah melampaui batas banjir. ban/kick/mute/tmute/tban"
            "\nanti banjir memungkinkan Anda untuk mengambil tindakan pada pengguna yang mengirim lebih dari x pesan berturut-turut. Melebihi banjir yang ditetapkan akan mengakibatkan pembatasan pengguna itu."
            "\n\n- /addblacklist <triggers>: Tambahkan pemicu ke daftar hitam. Setiap baris dianggap sebagai satu pemicu, jadi menggunakan baris yang berbeda akan memungkinkan Anda untuk menambahkan beberapa pemicu."
            "\n- /blacklistmode <off/del/warn/ban/kick/mute/tban/tmute>: Tindakan yang harus dilakukan ketika seseorang mengirim kata-kata yang masuk daftar hitam."
            "\nTindakan yang dilakukan ketika seseorang mengirim kata-kata yang masuk daftar hitam. daftar hitam digunakan untuk menghentikan pemicu tertentu agar tidak diucapkan dalam grup. Setiap kali pemicu disebutkan, pesan akan segera dihapus. Kombo yang bagus terkadang memasangkan ini dengan filter peringatan!"
            "\n\n- /reports <on/off>: Ubah setelan laporan, atau lihat status saat ini."
            "\n • Jika dilakukan di malam hari, matikan status Anda."
            "\n • Jika dalam obrolan, matikan status obrolan itu."
            "\nJika seseorang di grup Anda merasa seseorang perlu melaporkan, mereka sekarang memiliki cara mudah untuk memanggil semua admin."
            "\n\n- /lock <type>: Kunci item dari jenis tertentu (tidak tersedia secara pribadi)"
            "\n- /locktypes: Daftar semua kemungkinan tipe kunci"
            "\nModul kunci memungkinkan Anda untuk mengunci beberapa item umum di dunia telegram; bot akan secara otomatis menghapusnya!"
            '\n\n- /addwarn <keyword> <reply message>: Menetapkan filter peringatan pada kata kunci tertentu. Jika Anda ingin kata kunci Anda menjadi kalimat, lampirkan dengan tanda kutip, seperti: /addwarn "sangat marah" Ini adalah pengguna yang marah. '
            "\n- /warn <userhandle>: Memperingatkan pengguna. Setelah 3 kali peringatan, pengguna akan diblokir dari grup. Bisa juga digunakan sebagai balasan."
            "\n- /strongwarn <on/yes/off/no>: Jika disetel ke aktif, melebihi batas peringatan akan mengakibatkan larangan. Lain, hanya akan menendang."
            "\nJika Anda mencari cara untuk memperingatkan pengguna secara otomatis ketika mereka mengatakan hal-hal tertentu, gunakan perintah /addwarn."
            "\n\n- /welcomemute <off/soft/strong>: Semua pengguna yang bergabung, dibisukan"
            "\nSebuah tombol ditambahkan ke pesan selamat datang agar mereka dapat mengaktifkan suara mereka sendiri. Ini membuktikan bahwa mereka bukan bot! lunak - membatasi kemampuan pengguna untuk memposting media selama 24 jam. kuat - mematikan suara saat bergabung sampai mereka membuktikan bahwa mereka benar bukan bot.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Kembali", callback_data="aboutmanu_")]]
            ),
        )
    elif query.data == "aboutmanu_tac":
        query.message.edit_text(
            text=f"<b> ｢ Terms and Conditions 」</b>\n"
            f"\n<i>To Use This Bot, You Need To Read Terms and Conditions Carefully.</i>\n"
            f"\n✪ We always respect your privacy \n  We never log into bot's api and spying on you \n  We use a encripted database \n  Bot will automatically stops if someone logged in with api."
            f"\n✪ Always try to keep credits, so \n  This hardwork is done by Infinity_Bots team spending many sleepless nights.. So, Respect it."
            f"\n✪ Some modules in this bot is owned by different authors, So, \n  All credits goes to them \n  Also for <b>Paul Larson for Marie</b>."
            f"\n✪ If you need to ask anything about \n  this bot, Go @{SUPPORT_CHAT}."
            f"\n✪ If you asking nonsense in Support \n  Chat, you will get warned/banned."
            f"\n✪ All api's we used owned by originnal authors \n  Some api's we use Free version \n  Please don't overuse AI Chat."
            f"\n✪ We don't Provide any support to forks,\n  So these terms and conditions not applied to forks \n  If you are using a fork of DaisyXBot we are not resposible for anything."
            f"\n\nFor any kind of help, related to this bot, Join @{SUPPORT_CHAT}."
            f"\n\n<i>Terms & Conditions will be changed anytime</i>\n",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="Kredit", callback_data="aboutmanu_credit"
                        ),
                        InlineKeyboardButton(text="Kembali", callback_data="aboutmanu_"),
                    ]
                ]
            ),
        )


@run_async
@typing_action
def get_help(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    args = update.effective_message.text.split(None, 1)

    # ONLY send help in PM
    if chat.type != chat.PRIVATE:
        if len(args) >= 2 and any(args[1].lower() == x for x in HELPABLE):
            module = args[1].lower()
            update.effective_message.reply_text(
                f"Hubungi saya di PM untuk mendapatkan bantuan {module.capitalize()}",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="Bantuan",
                                url="t.me/{}?start=ghelp_{}".format(
                                    context.bot.username, module
                                ),
                            )
                        ]
                    ]
                ),
            )
            return
        update.effective_message.reply_text(
            "Hubungi saya di PM untuk mendapatkan daftar kemungkinan perintah.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="Bantuan",
                            url="t.me/{}?start=help".format(context.bot.username),
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="Support Chat",
                            url="https://t.me/{}".format(SUPPORT_CHAT),
                        )
                    ],
                ]
            ),
        )
        return

    elif len(args) >= 2 and any(args[1].lower() == x for x in HELPABLE):
        module = args[1].lower()
        text = (
            "Berikut adalah bantuan yang tersedia untuk *{}* module:\n".format(
                HELPABLE[module].__mod_name__
            )
            + HELPABLE[module].__help__
        )
        send_help(
            chat.id,
            text,
            InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Kembali", callback_data="help_back")]]
            ),
        )

    else:
        send_help(chat.id, HELP_STRINGS)


def send_settings(chat_id, user_id, user=False):
    if user:
        if USER_SETTINGS:
            settings = "\n\n".join(
                "*{}*:\n{}".format(mod.__mod_name__, mod.__user_settings__(user_id))
                for mod in USER_SETTINGS.values()
            )
            dispatcher.bot.send_message(
                user_id,
                "These are your current settings:" + "\n\n" + settings,
                parse_mode=ParseMode.MARKDOWN,
            )

        else:
            dispatcher.bot.send_message(
                user_id,
                "Sepertinya tidak ada pengaturan khusus pengguna yang tersedia :'(",
                parse_mode=ParseMode.MARKDOWN,
            )

    else:
        if CHAT_SETTINGS:
            chat_name = dispatcher.bot.getChat(chat_id).title
            dispatcher.bot.send_message(
                user_id,
                text="Modul mana yang ingin Anda periksa {}'s pengaturan untuk?".format(
                    chat_name
                ),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, CHAT_SETTINGS, "stngs", chat=chat_id)
                ),
            )
        else:
            dispatcher.bot.send_message(
                user_id,
                "Sepertinya tidak ada pengaturan obrolan yang tersedia :'(\nKirim ini "
                "dalam obrolan grup tempat Anda menjadi admin untuk menemukan pengaturannya saat ini!",
                parse_mode=ParseMode.MARKDOWN,
            )


@run_async
def settings_button(update, context):
    query = update.callback_query
    user = update.effective_user
    mod_match = re.match(r"stngs_module\((.+?),(.+?)\)", query.data)
    prev_match = re.match(r"stngs_prev\((.+?),(.+?)\)", query.data)
    next_match = re.match(r"stngs_next\((.+?),(.+?)\)", query.data)
    back_match = re.match(r"stngs_back\((.+?)\)", query.data)
    try:
        if mod_match:
            chat_id = mod_match.group(1)
            module = mod_match.group(2)
            chat = context.bot.get_chat(chat_id)
            text = "*{}* memiliki pengaturan berikut untuk *{}* module:\n\n".format(
                escape_markdown(chat.title), CHAT_SETTINGS[module].__mod_name__
            ) + CHAT_SETTINGS[module].__chat_settings__(chat_id, user.id)
            query.message.edit_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="Kembali",
                                callback_data="stngs_back({})".format(chat_id),
                            )
                        ]
                    ]
                ),
            )

        elif prev_match:
            chat_id = prev_match.group(1)
            curr_page = int(prev_match.group(2))
            chat = context.bot.get_chat(chat_id)
            query.message.edit_text(
                "Halo! Ada beberapa pengaturan untuk *{}* - pergi ke depan dan memilih apa "
                "kamu tertarik.".format(chat.title),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(
                        curr_page - 1, CHAT_SETTINGS, "stngs", chat=chat_id
                    )
                ),
            )

        elif next_match:
            chat_id = next_match.group(1)
            next_page = int(next_match.group(2))
            chat = context.bot.get_chat(chat_id)
            query.message.edit_text(
                "Halo! Ada beberapa pengaturan untuk *{}* - pergi ke depan dan memilih apa "
                "kamu tertarik.".format(chat.title),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(
                        next_page + 1, CHAT_SETTINGS, "stngs", chat=chat_id
                    )
                ),
            )

        elif back_match:
            chat_id = back_match.group(1)
            chat = context.bot.get_chat(chat_id)
            query.message.edit_text(
                text="Halo! Ada beberapa pengaturan untuk *{}* - pergi ke depan dan memilih apa "
                "kamu tertarik.".format(escape_markdown(chat.title)),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, CHAT_SETTINGS, "stngs", chat=chat_id)
                ),
            )

        # ensure no spinny white circle
        context.bot.answer_callback_query(query.id)
        # query.message.delete()
    except Exception as excp:
        if excp.message == "Message is not modified":
            pass
        elif excp.message == "Query_id_invalid":
            pass
        elif excp.message == "Message can't be deleted":
            pass
        else:
            query.message.edit_text(excp.message)
            LOGGER.exception("Exception in settings buttons. %s", str(query.data))


@run_async
def get_settings(update: Update, context: CallbackContext):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]

    # ONLY send settings in PM
    if chat.type != chat.PRIVATE:
        if is_user_admin(chat, user.id):
            text = "Klik di sini untuk mendapatkan pengaturan obrolan ini, serta pengaturan Anda."
            msg.reply_text(
                text,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="Pengaturan",
                                url="t.me/{}?start=stngs_{}".format(
                                    context.bot.username, chat.id
                                ),
                            )
                        ]
                    ]
                ),
            )
        else:
            text = "Klik di sini untuk memeriksa pengaturan Anda."

    else:
        send_settings(chat.id, user.id, True)


def migrate_chats(update, context):
    msg = update.effective_message  # type: Optional[Message]
    if msg.migrate_to_chat_id:
        old_chat = update.effective_chat.id
        new_chat = msg.migrate_to_chat_id
    elif msg.migrate_from_chat_id:
        old_chat = msg.migrate_from_chat_id
        new_chat = update.effective_chat.id
    else:
        return

    LOGGER.info("Migrating from %s, to %s", str(old_chat), str(new_chat))
    for mod in MIGRATEABLE:
        mod.__migrate__(old_chat, new_chat)

    LOGGER.info("Berhasil bermigrasi!")
    raise DispatcherHandlerStop


def is_chat_allowed(update, context):
    if len(WHITELIST_CHATS) != 0:
        chat_id = update.effective_message.chat_id
        if chat_id not in WHITELIST_CHATS:
            context.bot.send_message(
                chat_id=update.message.chat_id, text="Obrolan yang tidak diizinkan! Meninggalkan..."
            )
            try:
                context.bot.leave_chat(chat_id)
            finally:
                raise DispatcherHandlerStop
    if len(BL_CHATS) != 0:
        chat_id = update.effective_message.chat_id
        if chat_id in BL_CHATS:
            context.bot.send_message(
                chat_id=update.message.chat_id, text="Obrolan yang tidak diizinkan! Meninggalkan..."
            )
            try:
                context.bot.leave_chat(chat_id)
            finally:
                raise DispatcherHandlerStop
    if len(WHITELIST_CHATS) != 0 and len(BL_CHATS) != 0:
        chat_id = update.effective_message.chat_id
        if chat_id in BL_CHATS:
            context.bot.send_message(
                chat_id=update.message.chat_id, text="Obrolan yang tidak diizinkan, pergi"
            )
            try:
                context.bot.leave_chat(chat_id)
            finally:
                raise DispatcherHandlerStop
    else:
        pass


@run_async
def donate(update: Update, context: CallbackContext):
    update.effective_message.from_user
    chat = update.effective_chat  # type: Optional[Chat]
    context.bot
    if chat.type == "private":
        update.effective_message.reply_text(
            DONATE_STRING, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True
        )
        update.effective_message.reply_text(
            "Anda juga dapat menyumbang kepada orang yang saat ini menjalankan saya "
            "[sini]({})".format(DONATION_LINK),
            parse_mode=ParseMode.MARKDOWN,
        )

    else:
        pass


def main():

    if SUPPORT_CHAT is not None and isinstance(SUPPORT_CHAT, str):
        try:
            dispatcher.bot.sendMessage(f"@{SUPPORT_CHAT}", "𝗣𝗥𝗔𝗕𝗨 sudah aktif!")
        except Unauthorized:
            LOGGER.warning(
                "Bot tidak dapat mengirim pesan untuk support_chat, buka dan periksa!"
            )
        except BadRequest as e:
            LOGGER.warning(e.message)

    # test_handler = CommandHandler("test", test)
    start_handler = CommandHandler("start", start, pass_args=True)

    help_handler = CommandHandler("help", get_help)
    help_callback_handler = CallbackQueryHandler(help_button, pattern=r"help_")

    settings_handler = CommandHandler("settings", get_settings)
    settings_callback_handler = CallbackQueryHandler(settings_button, pattern=r"stngs_")

    about_callback_handler = CallbackQueryHandler(
        DaisyX_about_callback, pattern=r"aboutmanu_"
    )

    donate_handler = CommandHandler("donate", donate)

    migrate_handler = MessageHandler(Filters.status_update.migrate, migrate_chats)
    is_chat_allowed_handler = MessageHandler(Filters.group, is_chat_allowed)

    # dispatcher.add_handler(test_handler)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(about_callback_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(settings_handler)
    dispatcher.add_handler(help_callback_handler)
    dispatcher.add_handler(settings_callback_handler)
    dispatcher.add_handler(migrate_handler)
    dispatcher.add_handler(is_chat_allowed_handler)
    dispatcher.add_handler(donate_handler)

    dispatcher.add_error_handler(error_handler)

    if WEBHOOK:
        LOGGER.info("Using webhooks.")
        updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN)

        if CERT_PATH:
            updater.bot.set_webhook(url=URL + TOKEN, certificate=open(CERT_PATH, "rb"))
        else:
            updater.bot.set_webhook(url=URL + TOKEN)
            client.run_until_disconnected()

    else:
        LOGGER.info("Using long polling.")
        updater.start_polling(timeout=15, read_latency=4, clean=True)

    if len(argv) not in (1, 3, 4):
        telethn.disconnect()
    else:
        telethn.run_until_disconnected()

    updater.idle()


if __name__ == "__main__":
    LOGGER.info("Successfully loaded modules: " + str(ALL_MODULES))
    telethn.start(bot_token=TOKEN)
    pbot.start()
    main()
