import os
import json
from datetime import datetime
from openai import OpenAI
from dateutil.parser import parse
from logic.calendar_utils import (
    registerSchedule,
    getScheduleByOffset,
    deleteEvent,
    updateEvent
)
from logic.task_utils import (
    registerTask,
    listTasks,
    completeTask,
    deleteTask,
    listCompletedTasks,
    registerTaskWithDue,
    listTasksWithDue
)

# 🔍 ユーザーの発言から意図を判定（登録・更新・削除・予定確認など）
def classifyIntent(user_input):
    user_input = user_input.lower()

    if "削除" in user_input:
        return "delete"
    elif "更新" in user_input or "変更" in user_input:
        return "update"
    elif "完了済" in user_input or "完了した" in user_input:
        return "task_list_completed"
    elif "期限付き" in user_input or "締め切り" in user_input or "期日" in user_input:
        return "task_list_due"
    elif "入れて" in user_input or "登録" in user_input or "追加" in user_input:
        return "register"
    elif "明後日" in user_input and "予定" in user_input:
        return "schedule+2"
    elif "明日" in user_input and "予定" in user_input:
        return "schedule+1"
    elif "今日" in user_input and "予定" in user_input:
        return "schedule+0"
    elif "予定" in user_input or "スケジュール" in user_input:
        return "schedule+0"
    elif "天気" in user_input:
        return "weather"
    elif "疲れた" in user_input or "やる気" in user_input:
        return "mental"
    elif "タスク" in user_input or "やること" in user_input:
        if "一覧" in user_input or "確認" in user_input:
            return "task_list"
        elif "完了" in user_input:
            return "task_complete"
        elif "削除" in user_input:
            return "task_delete"
        else:
            return "task_register"
    else:
        return "general"
    
# 📤 ChatGPTを使って予定のタイトルと（必要なら）開始時刻を抽出する
def extractNewEventDetails(user_input, require_time=True):
    today = datetime.now().strftime("%Y-%m-%d")

    if require_time:
        system_content = (
            f"あなたは自然文から予定の日時とタイトルを抽出するアシスタントです。\n"
            f"今日の日付は {today} です。『明日』『明後日』なども正しく認識してください。\n"
            f"絶対に自然文では返さず、以下の形式のJSONだけを返してください：\n"
            f"{{\"title\": \"予定名\", \"start_time\": \"2025-04-30 15:00:00\"}}\n"
            f"※形式が正しくないと処理ができません。"
        )
    else:
        system_content = (
            f"あなたは自然文から予定のタイトルだけを抽出するアシスタントです。\n"
            f"今日の日付は {today} です。『明日』『明後日』なども正しく認識してください。\n"
            f"絶対に自然文では返さず、以下の形式のJSONだけを返してください：\n"
            f"{{\"title\": \"予定名\"}}\n"
            f"※形式が正しくないと処理ができません。"
        )

    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_input}
    ]

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    content = response.choices[0].message.content
    print("📤 ChatGPTの返答（予定抽出）：", content)

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        print("❌ JSON解析失敗：ChatGPT応答が不正な形式")
        raise ValueError("ChatGPTの応答が正しい形式ではありません。")

    # タイトルの正規化処理（ゆらぎ防止）
    title = parsed.get("title", "").strip()
    for junk in [
        "の予定を変更", "の予定を削除", "の予定を追加", "の予定を登録",
        "を変更", "を削除", "を追加", "を登録",
        "の予定", "の予約", "予約"
    ]:
        title = title.replace(junk, "")
    title = title.strip()

    if require_time:
        start_time = parsed.get("start_time")
        return {"title": title, "start_time": start_time}
    else:
        return {"title": title}

# 📤 ChatGPTを使ってタスク名を抽出する（余計な語句は除去）
def extractTaskTitle(user_input):
    today = datetime.now().strftime("%Y-%m-%d")

    system_content = (
        f"あなたは自然文からタスク名を抽出するアシスタントです。\n"
        f"今日の日付は {today} です。『明日までにやること』などの文脈を正しく判断してください。\n"
        f"絶対に自然文では返さず、以下の形式のJSONだけを返してください：\n"
        f"{{\"title\": \"タスク名\"}}\n"
        f"※形式が正しくないと処理ができません。"
    )

    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_input}
    ]

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    content = response.choices[0].message.content
    print("📤 ChatGPTの返答（タスク抽出）：", content)

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        print("❌ JSON解析失敗：ChatGPT応答が不正な形式")
        raise ValueError("ChatGPTの応答が正しい形式ではありません。")

    title = parsed.get("title", "").strip()

    # ✅ 正規化：削除・完了などの余計な語句を取り除く
    for junk in [
        "を削除", "を登録", "を追加", "を変更", "を完了にする", "を完了にして",
        "を完了", "を実行", "してください", "して"
    ]:
        title = title.replace(junk, "")

    return {"title": title.strip()}

# 🗓️ 予定登録用：ChatGPTで抽出 → 登録処理 → 成功メッセージ返却
def registerScheduleFromText(user_message, client):
    try:
        new_event = extractNewEventDetails(user_message, require_time=True)
        title = new_event["title"]
        start_time = datetime.strptime(new_event["start_time"], "%Y-%m-%d %H:%M:%S")

        # ✅ 結果メッセージをそのまま返す
        result = registerSchedule(title, start_time)
        return result

    except Exception as error:
        print("❌ 予定登録エラー：", error)
        return "日付とタイトルの解析に失敗しました。"

# 📥 タスクのタイトル＋期限（due）を抽出する
def extractTaskDetails(user_input):
    today = datetime.now().strftime("%Y-%m-%d")

    system_content = (
        f"あなたは自然文からタスク名と期限日を抽出するアシスタントです。\n"
        f"今日の日付は {today} です。『明日までに』などの文脈も正しく解釈してください。\n"
        f"絶対に自然文では返さず、以下の形式のJSONだけを返してください：\n"
        f"{{\"title\": \"タスク名\", \"due\": \"2025-05-10T00:00:00.000Z\"}}\n"
        f"期限がない場合は \"due\": null を設定してください。\n"
        f"※形式が正しくないと処理ができません。"
    )

    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_input}
    ]

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )

    content = response.choices[0].message.content
    print("📥 ChatGPTの返答（タスク抽出＋期限）:", content)

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as e:
        print("❌ JSON解析エラー：", e)
        raise ValueError("ChatGPTの応答が正しいJSON形式ではありません。")

    # タイトル正規化（不要な文言の除去）
    title = parsed.get("title", "").strip()
    for junk in [
        "のタスクを追加", "のタスクを登録", "を追加", "を登録",
        "を完了", "を削除", "を更新", "タスク", "追加", "登録"
    ]:
        title = title.replace(junk, "")
    title = title.strip()

    # due の正規化
    due = parsed.get("due")
    if isinstance(due, str) and due.lower() == "null":
        due = None

    return {"title": title, "due": due}

# 🎯 メイン処理：ユーザーの意図に応じて処理分岐し、結果を返す
def askChatgpt(user_message):
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        intent = classifyIntent(user_message)
        print(f"🎯 intent 判定: {intent}")

        # 📆 特定日の予定確認（今日・明日・明後日など）
        if intent.startswith("schedule+"):
            day_offset = int(intent.split("+")[1])
            return getScheduleByOffset(day_offset)

        # 📝 新規登録（予定 or タスクの自動判別）
        elif intent == "register":
            try:
                task_info = extractTaskDetails(user_message)
                title = task_info.get("title")
                due = task_info.get("due")

                # ✅ 修正ポイント：括弧を見直し、title が None なら予定扱い
                if due or (title and ("タスク" in title or "やること" in title)):
                    if not title:
                        return "タスク名がうまく抽出できませんでした。"
                    if due:
                        return registerTaskWithDue(title, due)
                    else:
                        return registerTask(title)
                else:
                    return registerScheduleFromText(user_message, client)

            except Exception as e:
                print("❌ 登録エラー（タスク/予定）：", e)
                return "登録中にエラーが発生しました。"

        # 🗑️ 予定の削除（タイトル＋開始時刻を厳密に抽出して削除）
        elif intent == "delete":
            try:
                new_event = extractNewEventDetails(user_message, require_time=True)
                title = new_event.get("title")
                start_time_raw = new_event.get("start_time")

                if not title or not start_time_raw:
                    return "削除対象の予定が正しく抽出できませんでした。予定名と時間を明記してください。"

                start_time = datetime.strptime(start_time_raw, "%Y-%m-%d %H:%M:%S")
                return deleteEvent(title, start_time)

            except Exception as e:
                print("❌ 削除エラー：", e)
                return "削除中にエラーが発生しました。"

        # ♻️ 予定の更新（旧予定を削除 → 新予定を登録）
        elif intent == "update":
            try:
                new_event = extractNewEventDetails(user_message, require_time=True)
                title = new_event.get("title")
                start_time_raw = new_event.get("start_time")

                if not title or not start_time_raw:
                    return "更新対象の予定が正しく抽出できませんでした。予定名と時間を明記してください。"

                start_time = datetime.strptime(start_time_raw, "%Y-%m-%d %H:%M:%S")
                return updateEvent(title, {"title": title, "start_time": start_time})
            except Exception as e:
                print("❌ 更新エラー：", e)
                return "更新中にエラーが発生しました。"

        # ✅ タスク登録
        elif intent == "task_register":
            try:
                new_task = extractTaskTitle(user_message)
                title = new_task.get("title")
                if not title:
                    return "タスク名がうまく抽出できませんでした。"
                return registerTask(title)
            except Exception as e:
                print("❌ タスク登録エラー：", e)
                return "タスク登録中にエラーが発生しました。"

        # 📋 タスク一覧表示
        elif intent == "task_list":
            return listTasks()

        # ✅ タスク完了処理
        elif intent == "task_complete":
            try:
                new_task = extractTaskTitle(user_message)
                title = new_task.get("title")
                if not title:
                    return "完了させたいタスク名が見つかりませんでした。"
                return completeTask(title)
            except Exception as e:
                print("❌ タスク完了エラー：", e)
                return "タスク完了中にエラーが発生しました。"
            
        # 🗑️ タスク削除
        elif intent == "task_delete":
            try:
                new_task = extractTaskTitle(user_message)
                title = new_task.get("title")
                if not title:
                    return "削除したいタスク名が見つかりませんでした。"
                return deleteTask(title)
            except Exception as e:
                print("❌ タスク削除エラー：", e)
                return "タスク削除中にエラーが発生しました。"
            
        # 完了済みタスク一覧
        elif intent == "task_list_completed":
            return listCompletedTasks()

        # ✅ タスク登録（期限付きも含む）
        elif intent == "task_register":
            try:
                task_info = extractTaskDetails(user_message)
                title = task_info.get("title")
                due = task_info.get("due")

                if not title:
                    return "タスク名がうまく抽出できませんでした。"

                if due:
                    return registerTaskWithDue(title, due)
                else:
                    return registerTask(title)

            except Exception as e:
                print("❌ タスク登録エラー：", e)
                return "タスク登録中にエラーが発生しました。"
            
        # 📅 期限付きタスクの一覧表示
        elif intent == "task_list_due":
            return listTasksWithDue()

        # 🤖 雑談など（ChatGPTへそのまま転送）
        messages = [
            {"role": "system", "content": "あなたは親切で柔軟なAIアシスタントです。"},
            {"role": "user", "content": user_message}
        ]
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        return response.choices[0].message.content

    except Exception as error:
        print("❌ ChatGPT応答全体エラー：", error)
        return "AI応答中にエラーが発生しました。"

