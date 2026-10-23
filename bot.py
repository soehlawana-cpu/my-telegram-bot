import json
import mysql.connector

# XAMPP MySQL ချိတ်ဆက်ရန်
db = mysql.connector.connect(
    host="localhost", user="root", password="", database="sheet_music_db"
)
cursor = db.cursor(dictionary=True)

# sheet_music စားပွဲ (Table) ထဲက အချက်အလက်အားလုံးကို ယူမည်
cursor.execute("SELECT id, song_title, file_name, file_id FROM sheet_music")
rows = cursor.fetchall()

cursor.close()
db.close()

# JSON ဖိုင်အဖြစ် သိမ်းဆည်းမည်
with open("songs.json", "w", encoding="utf-8") as f:
    json.dump(rows, f, ensure_ascii=False, indent=4)

print("JSON ဖိုင်သို့ အောင်မြင်စွာ ပြောင်းပြီးပါပြီ! (songs.json ဖိုင် ထွက်လာပါပြီ)")
