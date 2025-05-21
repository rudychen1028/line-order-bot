from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError
import sqlite3
import os

app = Flask(__name__)

# 用你在 LINE Developers 上的 token 與 secret
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("bxiVQtfZCs7ZUGrDUjW9gtx9hneFGufchIIVcaQ+sxcrdTSnHXy/x3QVceK+yB0lPQd29FrVrobewrz2/tF56J4BixU9+AKxbPvexdptDIBkNNDeBuk98pmN1lHIErbjHGgKsvKb84jhIEH6cf7CKgdB04t89/1O/w1cDnyilFU=")
LINE_CHANNEL_SECRET = os.environ.get("55696dcaf56f0f07b349f463ceda78e0")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    msg = event.message.text.strip()

    # 查詢訂單
    if msg == "查詢":
        orders = get_orders(user_id)
        if orders:
            reply = "\n".join([f"{o[0]}：{o[1]}（{o[2]}）" for o in orders])
        else:
            reply = "查無訂單。"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(reply))
        return

    # 一般視為下單
    save_order(user_id, msg)
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"已接單：{msg}"))

def save_order(user_id, order_text):
    conn = sqlite3.connect("orders.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO orders (user_id, order_text) VALUES (?, ?)", (user_id, order_text))
    conn.commit()
    conn.close()

def get_orders(user_id):
    conn = sqlite3.connect("orders.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, order_text, timestamp FROM orders WHERE user_id = ? ORDER BY timestamp DESC", (user_id,))
    result = cursor.fetchall()
    conn.close()
    return result

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
