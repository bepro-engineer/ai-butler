import os
from datetime import datetime, timedelta
import pytz
from googleapiclient.discovery import build
from google.oauth2 import service_account
from dateutil.parser import parse

# 🔐 Google API認証情報を取得
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# 📅 Googleカレンダーに予定を登録（30分間の固定枠）
from pytz import timezone

def getCredentials():
    token_path = os.getenv("GOOGLE_TOKEN_JSON") or "/home/bepro/projects/ai_butler/token.json"
    if not token_path:
        raise ValueError("GOOGLE_TOKEN_JSON が未設定です")

    creds = Credentials.from_authorized_user_file(
        token_path,
        scopes=["https://www.googleapis.com/auth/calendar"]
    )

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(token_path, "w") as token_file:
            token_file.write(creds.to_json())

    print("✅ GOOGLE_TOKEN_JSON:", token_path)
    return creds

# 📅 Googleカレンダーに予定を登録する関数  
#    └─ 同時間・同タイトルのイベントがあるとき “だけ” 登録を中止する安全版
def registerSchedule(title, start_time):
    try:
        credentials = getCredentials()
        service = build("calendar", "v3", credentials=credentials)

        # --- JST にそろえ、30分枠を計算 -----------------------------------
        jst = timezone("Asia/Tokyo")
        if start_time.tzinfo is None:
            start_time = jst.localize(start_time)
        end_time = start_time + timedelta(minutes=30)

        calendar_id = os.getenv("GOOGLE_CALENDAR_ID")
        if not calendar_id:
            raise ValueError("GOOGLE_CALENDAR_ID が未設定です")

        # --- 同時間帯イベント取得（30分幅） -------------------------------
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=start_time.isoformat(),
            timeMax=end_time.isoformat(),
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        events = events_result.get("items", [])

        # ★ タイトルも比較して完全重複だけブロック ------------------------
        for ev in events:
            if ev.get("summary") == title:
                print("⚠️ 同タイトル・同時間の予定が既にあります")
                return "その時間には同じ予定が既にあります。別の時間を指定してください。"

        # --- 重複なし → 登録 ----------------------------------------------
        event_body = {
            "summary": title,
            "start": {"dateTime": start_time.isoformat(), "timeZone": "Asia/Tokyo"},
            "end":   {"dateTime": end_time.isoformat(),   "timeZone": "Asia/Tokyo"}
        }
        created = service.events().insert(calendarId=calendar_id, body=event_body).execute()
        print("✅ 登録イベント情報：", created)

        return f"予定『{title}』を登録しました。"

    except Exception as error:
        # --- エラー時ログ＆ユーザー向け文言 -------------------------------
        print("❌ 登録エラー：", error)
        return "予定の登録中にエラーが発生しました。"

# 📆 任意日数後の予定を取得
def getScheduleByOffset(day_offset: int):
    credentials = getCredentials()
    service = build("calendar", "v3", credentials=credentials)

    jst = pytz.timezone("Asia/Tokyo")
    target_date = datetime.now(jst) + timedelta(days=day_offset)

    start = datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0, tzinfo=jst).isoformat()
    end = datetime(target_date.year, target_date.month, target_date.day, 23, 59, 59, tzinfo=jst).isoformat()

    calendar_id = os.getenv("GOOGLE_CALENDAR_ID")
    if not calendar_id:
        raise ValueError("GOOGLE_CALENDAR_ID が未設定です")

    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=start,
        timeMax=end,
        singleEvents=True,
        orderBy="startTime"
    ).execute()

    events = events_result.get("items", [])
    label = {0: "今日", 1: "明日", 2: "明後日"}.get(day_offset, f"{day_offset}日後")

    if not events:
        return f"{label}の予定はありません。"

    result = f"{label}の予定はこちらです：\n"
    for event in events:
        start_time = event["start"].get("dateTime", event["start"].get("date"))
        result += f"・{start_time}：{event['summary']}\n"
    return result

# 🗑️ 予定を名前と時刻で削除（JSTベースの30日前〜30日後範囲）
from dateutil.parser import parse  # 必須

def deleteEvent(event_name, start_time):
    try:
        # ✅ タイトルを正規化
        for junk in ["の予定", "の予約", "予約"]:
            event_name = event_name.replace(junk, "")
        event_name = event_name.strip()
        
        credentials = getCredentials()
        service = build("calendar", "v3", credentials=credentials)

        jst = pytz.timezone("Asia/Tokyo")
        now = datetime.now(jst)
        past = now - timedelta(days=30)
        future = now + timedelta(days=30)

        # 🔍 文字列なら datetime に変換
        if isinstance(start_time, str):
            target_start = parse(start_time)
        else:
            target_start = start_time

        events_result = service.events().list(
            calendarId=os.getenv("GOOGLE_CALENDAR_ID"),
            timeMin=past.isoformat(),
            timeMax=future.isoformat(),
            singleEvents=True,
            orderBy="startTime"
        ).execute()

        for event in events_result.get("items", []):
            event_start_str = event["start"].get("dateTime")
            if not event_start_str:
                continue

            event_start = parse(event_start_str)

            # 🔁 厳密比較ではなく tz/microsec を除外して比較
            if (event.get("summary") == event_name and
                event_start.replace(tzinfo=None, microsecond=0) ==
                target_start.replace(tzinfo=None, microsecond=0)):

                service.events().delete(
                    calendarId=os.getenv("GOOGLE_CALENDAR_ID"),
                    eventId=event["id"]
                ).execute()
                print("✅ 削除成功：", event_name)
                return f"予定『{event_name}』を削除しました。"

        return f"予定『{event_name}』は見つかりませんでした。"

    except Exception as error:
        print("❌ 削除エラー：", error)
        return "予定削除中にエラーが発生しました。"

# 🔁 旧予定をすべて削除してから新しい内容で再登録する更新処理（タイトルゆらぎ対策）
def updateEvent(event_name, new_event):
    try:
        credentials = getCredentials()
        service = build("calendar", "v3", credentials=credentials)

        jst   = pytz.timezone("Asia/Tokyo")
        now   = datetime.now(jst)
        past  = now - timedelta(days=30)
        future= now + timedelta(days=30)

        calendar_id = os.getenv("GOOGLE_CALENDAR_ID")
        if not calendar_id:
            raise ValueError("GOOGLE_CALENDAR_ID が未設定です")

        # --- タイトル正規化関数（「歯医者」「歯医者の予定」→ 同一視） ----------
        def _normalize(t: str) -> str:
            for junk in ("の予定", "の予約", "予約"):
                t = t.replace(junk, "")
            return t.strip()

        # --- 30 日幅でタイトル一致候補を取得 -------------------------------
        events = service.events().list(
            calendarId=calendar_id,
            timeMin=past.isoformat(),
            timeMax=future.isoformat(),
            singleEvents=True,
            orderBy="startTime"
        ).execute().get("items", [])

        # --- 正規化タイトルが一致する旧予定を“全部”削除 --------------------
        deleted_any = False
        for ev in events:
            if _normalize(ev.get("summary", "")) == _normalize(event_name):
                service.events().delete(calendarId=calendar_id,
                                        eventId=ev["id"]).execute()
                print("🗑️ 削除：", ev["summary"], ev["start"].get("dateTime"))
                deleted_any = True   # break しない＝同タイトル複数も全削除

        if not deleted_any:
            return f"予定『{event_name}』は見つかりませんでした。"

        # --- 新しい予定を登録 ---------------------------------------------
        new_title      = new_event["title"]
        new_start_time = new_event["start_time"]
        if new_start_time.tzinfo is None:
            new_start_time = jst.localize(new_start_time)
        new_end_time   = new_start_time + timedelta(minutes=30)

        event_body = {
            "summary": new_title,
            "start": {"dateTime": new_start_time.isoformat(), "timeZone": "Asia/Tokyo"},
            "end":   {"dateTime": new_end_time.isoformat(),   "timeZone": "Asia/Tokyo"}
        }

        created = service.events().insert(
            calendarId=calendar_id,
            body=event_body
        ).execute()

        print("✅ 新予定を登録：", created.get("summary"))
        return f"予定『{event_name}』を新しい内容で更新しました。"

    except Exception as error:
        print("❌ 更新エラー：", error)
        return f"更新中にエラーが発生しました：{error}"
    

