import os
from flask import Flask, request, abort
from dotenv import load_dotenv
from linebot.v3.messaging import MessagingApi, Configuration, ApiClient
from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage
from logic.chatgpt_logic import askChatgpt

# .envファイルを読み込む
load_dotenv()

# Flaskアプリケーション初期化
app = Flask(__name__)

# LINE Messaging API設定
configuration = Configuration(access_token=os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# Webhookエンドポイント
@app.route("/ai_butler_webhook", methods=["POST"])
def ai_butler_webhook():
    line_signature = request.headers.get("X-Line-Signature", "")
    request_body = request.get_data(as_text=True)
    print("📦 Webhook受信ボディ：", request_body)

    try:
        handler.handle(request_body, line_signature)
    except Exception as error:
        print("❌ Webhook handling failed:", error)
        abort(400)

    return "OK"

# LINEメッセージ受信処理
@handler.add(MessageEvent, message=TextMessageContent)
def handleMessage(event):
    user_message = event.message.text
    print("✅ メッセージイベント発火！ 📩", user_message)

    try:
        reply_text = askChatgpt(user_message)
        print("🧠 応答内容：", reply_text)
    except Exception as error:
        reply_text = f"応答処理エラー: {error}"

    with ApiClient(configuration) as api_client:
        messaging_api = MessagingApi(api_client)
        messaging_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )

# Flaskサーバ起動
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
