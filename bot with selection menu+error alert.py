import mysql.connector
import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

# --- 1. CONFIGURATION ---
BOT_TOKEN = "8699169443:AAFPbQJ2V2PjlY-gRRw2g52OdeeBwb6c9uM"

# သင့်ရဲ့ Telegram User ID နံပါတ်
ADMIN_TELEGRAM_ID = 1999290358

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "sheet_music_db",
    "charset": "utf8mb4",
    "use_unicode": True,
}

bot = telebot.TeleBot(BOT_TOKEN)


def get_db_connection():
  db = mysql.connector.connect(**DB_CONFIG)
  cursor = db.cursor()
  cursor.execute("SET NAMES utf8mb4")
  cursor.execute("SET CHARACTER SET utf8mb4")
  cursor.close()
  return db


# --- 2. START & MAIN MENU ---
@bot.message_handler(commands=["start", "menu"])
def send_welcome(message):
  markup = InlineKeyboardMarkup(row_width=2)
  btn1 = InlineKeyboardButton(
      "🎵 အက္ခရာအလိုက် ရှာရန်", callback_data="menu_alphabet"
  )
  btn2 = InlineKeyboardButton(
      "🔍 အမည်ဖြင့် ရှာရန်", callback_data="menu_search"
  )
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

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    query = "SELECT id, song_title, file_id FROM sheet_music WHERE song_title LIKE %s LIMIT 10"
    cursor.execute(query, (f"{selected_letter}%",))
    results = cursor.fetchall()
    cursor.close()
    db.close()

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
    song_id = call.data.split("_")[1]
    bot.answer_callback_query(call.id)

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    query = "SELECT song_title, file_name, file_id FROM sheet_music WHERE id = %s"
    cursor.execute(query, (song_id,))
    row = cursor.fetchone()
    cursor.close()
    db.close()

    # Case A: Database ထဲမှာ file_id ရှိနေပါက Telegram မှတစ်ဆင့် ပို့မည်
    if row and row["file_id"] and str(row["file_id"]).strip() != "":
      caption = f"🎵 {row['song_title']}\nID: {song_id}"
      try:
        bot.send_document(
            call.message.chat.id, document=row["file_id"], caption=caption
        )
      except Exception as e:
        # Telegram Channel ထဲမှ ဖိုင် ပျက်နေပါက ဒီနေရာ အလုပ်လုပ်မည်
        bot.send_message(
            call.message.chat.id,
            f"❌ တောင်းပန်ပါတယ် ခင်ဗျာ။ '{row['song_title']}' နုတ်ဖိုင်ကို "
            f"ဆာဗာမှ ရှာမတွေ့တော့ပါ (သို့မဟုတ်) ဖျက်ထားပါသည် ဆက်စပ်တာဝန်ရှိသူထံ အကြောင်းကြားထားပါပြီ။",
        )

        # Plain Text အဖြစ် ပြောင်းလဲထားသဖြင့် Markdown Parse Error မတက်တော့ပါ
        admin_alert_text = (
            f"⚠️ [MISSING FILE ALERT]\n\n"
            f"🎵 သီချင်းနာမည်: {row['song_title']}\n"
            f"📂 ဖိုင်နာမည်: {row['file_name']}\n"
            f"🆔 Database ID: {song_id}\n"
            f"❌ အကြောင်းရင်း: Telegram Channel ထဲတွင် ဖိုင် မရှိတော့ပါ။"
        )
        try:
          bot.send_message(ADMIN_TELEGRAM_ID, admin_alert_text)
        except Exception as alert_err:
          print(f"Failed to send admin alert: {alert_err}")

    # Case B: Database ထဲမှာ file_id မရှိသေးပါက
    else:
      song_title = row["song_title"] if row else "Unknown"
      file_name = row["file_name"] if row else "Unknown"

      bot.send_message(
          call.message.chat.id, "❌ ဒီသီချင်းအတွက် Telegram File ID မရှိသေးပါ။"
      )

      # Plain Text အဖြစ် ပြောင်းလဲထားသဖြင့် Markdown Parse Error မတက်တော့ပါ
      admin_alert_text = (
          f"⚠️ [MISSING FILE ID IN DB]\n\n"
          f"🎵 သီချင်းနာမည်: {song_title}\n"
          f"📂 ဖိုင်နာမည်: {file_name}\n"
          f"🆔 Database ID: {song_id}\n"
          f"❌ အကြောင်းရင်း: Database ထဲတွင် file_id မရှိသေးပါ (ဖိုင် မတင်ရသေးပါ။)"
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

  db = get_db_connection()
  cursor = db.cursor(dictionary=True)

  query = "SELECT id, song_title, file_id FROM sheet_music WHERE song_title LIKE %s LIMIT 10"
  cursor.execute(query, (f"%{keyword}%",))
  results = cursor.fetchall()
  cursor.close()
  db.close()

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


# --- 5. RUN BOT ---
if __name__ == "__main__":
  print("Bot is running with Selection Menu...")
  bot.infinity_polling(skip_pending=True)