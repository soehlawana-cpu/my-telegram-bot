import json
import os
import threading
from flask import Flask
import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

# --- Render ရဲ့ Free Web Service Port Error ကျော်ရန် Flask Server ---
app = Flask("")


@app.route("/")
def home():
  return "Bot is running online 24/7!"


def run_flask():
  port = int(os.environ.get("PORT", 8080))
  app.run(host="0.0.0.0", port=port)


# --- 1. CONFIGURATION ---
BOT_TOKEN = "8699169443:AAFPbQJ2V2PjlY-gRRw2g52OdeeBwb6c9uM"
ADMIN_TELEGRAM_ID = 1999290358

# JSON ဖိုင်ရှိရာ လမ်းကြောင်း
JSON_FILE_PATH = "songs.json"

bot = telebot.TeleBot(BOT_TOKEN)


def load_songs():
  """JSON ဖိုင်ထဲမှ သီချင်းအချက်အလက်များကို ဖတ်ယူရန်"""
  if not os.path.exists(JSON_FILE_PATH):
    return []
  with open(JSON_FILE_PATH, "r", encoding="utf-8") as f:
    try:
      return json.load(f)
    except json.JSONDecodeError:
      return []


# --- 2. START & MAIN MENU ---
@bot.message_handler(commands=["start", "menu"])
def send_welcome(message):
  markup = InlineKeyboardMarkup(row_width=2)
  btn1 = InlineKeyboardButton(
      "🎵 အက္ခရာအလိုက် ရှာရန်", callback_data="menu_alphabet"
  )
  btn2 = InlineKeyboardButton("🔍 အမည်ဖြင့် ရှာရန်", callback_data="menu_search")
  btn3 = InlineKeyboardButton("📂 အမျိုးအစားအလိုက်", callback_data="menu_genres")
  markup.add(btn1, btn2, btn3)

  welcome_text = (
      "🎵 **မင်္ဂလာပါ ခင်ဗျာ!**\n\n"
      "ဤဘော့တ်သည် သင့်အတွက် နုတ်ဖိုင် (Sheet Music) များကို "
      "လွယ်ကူလျင်မြန်စွာ ရှာဖွေပေးမည့် Bot ဖြစ်ပါသည်။\n\n"
      "အောက်ပါ Menu မှ လိုအပ်သည်များကို ရွေးချယ်နိုင်ပါသည် -"
  )
  bot.send_message(
      message.chat.id,
      welcome_text,
      reply_markup=markup,
      parse_mode="Markdown",
  )


# --- 3. CALLBACK QUERY HANDLER (MENU ACTIONS) ---
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
  songs = load_songs()

  if call.data == "menu_alphabet":
    markup = InlineKeyboardMarkup(row_width=4)
    letters = ["က", "ခ", "ဂ", "ဃ", "င", "စ", "ဆ", "ဇ", "ဈ", "ည"]
    buttons = [
        InlineKeyboardButton(l, callback_data=f"alpha_{l}") for l in letters
    ]
    markup.add(*buttons)

    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        "🔠 ရှာလိုသော မြန်မာအက္ခရာကို ရွေးချယ်ပါ -",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
    )

  elif call.data == "menu_search":
    bot.answer_callback_query(call.id)
    bot.send_message(
        call.message.chat.id,
        "🔍 ရှာလိုသော သီချင်းနာမည် (သို့မဟုတ်) စာသားကို ရိုက်ထည့်ပေးပါ။",
    )

  elif call.data == "menu_genres":
    bot.answer_callback_query(
        call.id,
        text="❌ စလုံးနဲ့ စ တဲ့ သီချင်းတွေအထိပဲတင်ရသေးတယ် ခဏစောင့်ပေးနော်",
        show_alert=True,
    )

  elif call.data.startswith("alpha_"):
    selected_letter = call.data.split("_")[1]
    bot.answer_callback_query(call.id)

    # JSON ထဲမှ သတ်မှတ်ထားသော အက္ခရာဖြင့် စသော သီချင်းများကို ရှာမည် (Limit 10)
    results = [
        s
        for s in songs
        if s.get("song_title", "").startswith(selected_letter)
    ][:10]

    if results:
      markup = InlineKeyboardMarkup(row_width=1)
      for row in results:
        btn = InlineKeyboardButton(
            f"🎵 {row['song_title']}", callback_data=f"getfile_{row['id']}"
        )
        markup.add(btn)

      bot.send_message(
          call.message.chat.id,
          f"🎵 **{selected_letter}** ဖြင့်စသော သီချင်းများ (နှိပ်၍ နုတ်ဖိုင်ရယူပါ) -",
          reply_markup=markup,
          parse_mode="Markdown",
      )
    else:
      bot.send_message(
          call.message.chat.id,
          f"'{selected_letter}' ဖြင့်စသော သီချင်း မတွေ့ရှိသေးပါ။",
      )

  elif call.data.startswith("getfile_"):
    try:
      song_id = int(call.data.split("_")[1])
    except ValueError:
      song_id = call.data.split("_")[1]

    bot.answer_callback_query(call.id)

    # JSON ထဲမှ ID တူသော သီချင်းကို ရှာမည်
    row = next((s for s in songs if str(s.get("id")) == str(song_id)), None)

    # Case A: JSON ထဲမှာ file_id ရှိနေပါက Telegram မှတစ်ဆင့် ပို့မည်
    if row and row.get("file_id") and str(row["file_id"]).strip() != "":
      caption = f"🎵 {row['song_title']}\nID: {song_id}"
      try:
        bot.send_document(
            call.message.chat.id, document=row["file_id"], caption=caption
        )
      except Exception as e:
        bot.send_message(
            call.message.chat.id,
            f"❌ တောင်းပန်ပါတယ် ခင်ဗျာ။ '{row['song_title']}' နုတ်ဖိုင်ကို"
            f" ဆာဗာမှ ရှာမတွေ့တော့ပါ (သို့မဟုတ်) ဖျက်ထားပါသည် ဆက်စပ်တာဝန်ရှိသူထံ အကြောင်းကြားထားပါပြီ။",
        )

        admin_alert_text = (
            f"⚠️ [MISSING FILE ALERT]\n\n"
            f"🎵 သီချင်းနာမည်: {row['song_title']}\n"
            f"📂 ဖိုင်နာမည်: {row.get('file_name', 'N/A')}\n"
            f"🆔 Database ID: {song_id}\n"
            f"❌ အကြောင်းရင်း: Telegram Channel ထဲတွင် ဖိုင် မရှိတော့ပါ။"
        )
        try:
          bot.send_message(ADMIN_TELEGRAM_ID, admin_alert_text)
        except Exception as alert_err:
          print(f"Failed to send admin alert: {alert_err}")

    # Case B: JSON ထဲမှာ file_id မရှိသေးပါက
    else:
      song_title = row["song_title"] if row else "Unknown"
      file_name = row.get("file_name", "Unknown") if row else "Unknown"

      bot.send_message(
          call.message.chat.id, "❌ ဒီသီချင်းအတွက် Telegram File ID မရှိသေးပါ။"
      )

      admin_alert_text = (
          f"⚠️ [MISSING FILE ID IN JSON]\n\n"
          f"🎵 သီချင်းနာမည်: {song_title}\n"
          f"📂 ဖိုင်နာမည်: {file_name}\n"
          f"🆔 Database ID: {song_id}\n"
          f"❌ အကြောင်းရင်း: JSON ထဲတွင် file_id မရှိသေးပါ (ဖိုင် မတင်ရသေးပါ။)"
      )
      try:
        bot.send_message(ADMIN_TELEGRAM_ID, admin_alert_text)
      except Exception as alert_err:
        print(f"Failed to send admin alert: {alert_err}")


# --- 4. TEXT SEARCH HANDLER ---
@bot.message_handler(func=lambda message: True)
def search_sheets(message):
  keyword = message.text.strip()

  if keyword.startswith("/"):
    return

  songs = load_songs()
  # Keyword ပါဝင်သော သီချင်းများကို ရှာမည် (Limit 10)
  results = [
      s for s in songs if keyword.lower() in s.get("song_title", "").lower()
  ][:10]

  if results:
    markup = InlineKeyboardMarkup(row_width=1)
    for row in results:
      btn = InlineKeyboardButton(
          f"🎵 {row['song_title']}", callback_data=f"getfile_{row['id']}"
      )
      markup.add(btn)

    bot.send_message(
        message.chat.id,
        f"🔍 **'{keyword}'** အတွက် ရှာဖွေတွေ့ရှိသော သီချင်းများ (နှိပ်၍ နုတ်ဖိုင်ရယူပါ) -",
        reply_markup=markup,
        parse_mode="Markdown",
    )
  else:
    bot.send_message(
        message.chat.id, f"❌ '{keyword}' နှင့် ကိုက်ညီသော နုတ်ဖိုင် မတွေ့ပါ။"
    )


# --- 5. RUN BOT & FLASK SERVER ---
if __name__ == "__main__":
  # Flask Web Server ကို နောက်ကွယ် Thread အဖြစ် Run ပါမည်
  t = threading.Thread(target=run_flask)
  t.daemon = True
  t.start()

  print("Bot is running with JSON Database & Selection Menu...")
  bot.infinity_polling(skip_pending=True)
