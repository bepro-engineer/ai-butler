import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from dotenv import load_dotenv
from datetime import datetime

# .envファイルから環境変数を読み込む
load_dotenv()

# ✅ Google認証情報を取得（token.jsonベース）
def getCredentials():
    token_path = os.getenv("GOOGLE_TOKEN_JSON") or "/home/bepro/projects/ai_butler/token.json"
    if not token_path:
        raise ValueError("GOOGLE_TOKEN_JSON が未設定です")

    # token.json を元に認証情報を構築
    creds = Credentials.from_authorized_user_file(
        token_path,
        scopes=["https://www.googleapis.com/auth/tasks"]
    )

    # トークンが期限切れならリフレッシュ
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(token_path, "w") as token_file:
            token_file.write(creds.to_json())

    print("✅ GOOGLE_TOKEN_JSON:", token_path)
    return creds

# ✅ 「geeksさんのリスト」のIDをリスト一覧から検索
def getDefaultTasklistId(service):
    results = service.tasklists().list().execute()
    for item in results.get("items", []):
        print("🧩 リスト検出:", item["title"], "→", item["id"])
        if item["title"].strip() == "geeksさんのリスト":
            return item["id"]
    raise ValueError("『geeksさんのリスト』が見つかりませんでした。")

# ✅ タスク登録処理（タイトルのみ登録）
def registerTask(title):
    try:
        creds = getCredentials()
        service = build("tasks", "v1", credentials=creds)

        tasklist_id = getDefaultTasklistId(service)
        task = {
            "title": title
        }

        # タスク登録実行
        result = service.tasks().insert(tasklist=tasklist_id, body=task).execute()
        print("✅ 登録タスク:", result.get("title"))
        return f"タスク『{title}』を登録しました。"

    except Exception as e:
        print("❌ タスク登録エラー：", e)
        return "タスク登録中にエラーが発生しました。"

# ✅ タスク一覧を取得し、整形して返す
def listTasks():
    try:
        creds = getCredentials()
        service = build("tasks", "v1", credentials=creds)

        tasklist_id = getDefaultTasklistId(service)
        print("📦 使用中のtasklist_id:", tasklist_id)

        results = service.tasks().list(tasklist=tasklist_id, showCompleted=True).execute()
        tasks = results.get("items", [])
        print("📦 取得タスク数:", len(tasks))
        print("📦 取得タスク内容:", tasks)

        if not tasks:
            return "現在、タスクは登録されていません。"

        response = "現在のタスク一覧です：\n"
        for task in tasks:
            title = task.get("title", "").strip()
            status = task.get("status", "")
            due_str = task.get("due", None)

            # ✅ フィルタ：完了・空タイトルを除外
            if not title or status != "needsAction":
                continue

            # ✅ ゾンビ対策：過去すぎるタスクは除外（UI準拠）
            if due_str:
                try:
                    due = datetime.strptime(due_str[:10], "%Y-%m-%d")
                    if due.year < 2015:
                        continue
                except Exception as e:
                    print("⚠️ 日付パース失敗:", e)

            response += f"・{title}\n"

        if response.strip() == "現在のタスク一覧です：":
            return "現在、タイトルのあるタスクは登録されていません。"

        return response

    except Exception as e:
        print("❌ タスク一覧取得エラー：", e)
        return "タスクの一覧取得中にエラーが発生しました。"

# ✅ 指定タイトルのタスクを「完了」に変更
def completeTask(title):
    try:
        creds = getCredentials()
        service = build("tasks", "v1", credentials=creds)

        tasklist_id = getDefaultTasklistId(service)
        results = service.tasks().list(tasklist=tasklist_id).execute()
        tasks = results.get("items", [])

        for task in tasks:
            task_title = task.get("title", "").strip()
            if task_title == title:
                # ステータス変更 → update
                task["status"] = "completed"
                service.tasks().update(
                    tasklist=tasklist_id,
                    task=task["id"],
                    body=task
                ).execute()
                print("✅ タスク完了:", title)
                return f"タスク『{title}』を完了にしました。"

        return f"タスク『{title}』が見つかりませんでした。"

    except Exception as e:
        print("❌ タスク完了エラー：", e)
        return "タスク完了中にエラーが発生しました。"

# ✅ 指定タイトルのタスクを削除（先頭一致1件）
def deleteTask(target_title):
    try:
        creds = getCredentials()
        service = build("tasks", "v1", credentials=creds)

        tasklist_id = getDefaultTasklistId(service)
        results = service.tasks().list(tasklist=tasklist_id, showCompleted=True).execute()
        tasks = results.get("items", [])

        for task in tasks:
            title = task.get("title", "").strip()
            task_id = task.get("id")

            if title == target_title:
                service.tasks().delete(tasklist=tasklist_id, task=task_id).execute()
                print(f"✅ タスク削除成功：{title}")
                return f"タスク『{title}』を削除しました。"

        return f"指定されたタスク『{target_title}』は見つかりませんでした。"

    except Exception as e:
        print("❌ タスク削除エラー：", e)
        return "タスク削除中にエラーが発生しました。"

# ✅ 指定されたタイトルのタスクを完了状態にする
def completeTask(target_title):
    try:
        creds = getCredentials()
        service = build("tasks", "v1", credentials=creds)

        tasklist_id = getDefaultTasklistId(service)
        print("📦 使用中のtasklist_id:", tasklist_id)

        # 未完了タスクのみ取得（完了済みは対象外）
        results = service.tasks().list(tasklist=tasklist_id, showCompleted=False).execute()
        tasks = results.get("items", [])

        # タイトルが一致するタスクを探して完了に変更
        for task in tasks:
            title = task.get("title", "").strip()
            if title == target_title:
                task["status"] = "completed"
                service.tasks().update(tasklist=tasklist_id, task=task["id"], body=task).execute()
                print(f"✅ 完了マークを付けたタスク: {title}")
                return f"タスク『{title}』を完了にしました。"

        return f"指定されたタスク『{target_title}』は見つかりませんでした。"

    except Exception as e:
        print("❌ タスク完了エラー：", e)
        return "タスクの完了処理中にエラーが発生しました。"

# ✅ 完了済みタスク一覧を返す関数
def listCompletedTasks():
    try:
        creds = getCredentials()
        service = build("tasks", "v1", credentials=creds)

        tasklist_id = getDefaultTasklistId(service)
        print("📦 使用中のtasklist_id（完了済み確認）:", tasklist_id)

        results = service.tasks().list(
            tasklist=tasklist_id,
            showCompleted=True
        ).execute()

        tasks = results.get("items", [])
        completed_tasks = [task for task in tasks if task.get("status") == "completed"]

        print("📦 完了済みタスク数:", len(completed_tasks))
        print("📦 完了済みタスク内容:", completed_tasks)

        if not completed_tasks:
            return "完了済みのタスクはありません。"

        response = "✅ 完了済みタスク一覧です：\n"
        for task in completed_tasks:
            title = task.get("title", "").strip()
            if title:
                response += f"・{title}\n"

        return response

    except Exception as e:
        print("❌ 完了済みタスク取得エラー：", e)
        return "完了済みタスク一覧の取得中にエラーが発生しました。"

# ✅ 完了済みタスク一覧を取得して整形して返す
def listCompletedTasks():
    try:
        creds = getCredentials()
        service = build("tasks", "v1", credentials=creds)

        tasklist_id = getDefaultTasklistId(service)
        print("📦 使用中のtasklist_id（完了）:", tasklist_id)

        # 完了タスクのみ取得（showCompleted=True + statusで絞り込み）
        results = service.tasks().list(
            tasklist=tasklist_id,
            showCompleted=True,
            showHidden=True
        ).execute()

        tasks = results.get("items", [])
        print("📦 取得タスク数（完了）:", len(tasks))

        completed_tasks = [
            task for task in tasks if task.get("status") == "completed"
        ]

        if not completed_tasks:
            return "現在、完了済みのタスクはありません。"

        response = "✅ 完了済みのタスク一覧です：\n"
        for task in completed_tasks:
            title = task.get("title", "").strip()
            if title:
                response += f"・{title}\n"

        return response

    except Exception as e:
        print("❌ 完了済みタスク一覧取得エラー：", e)
        return "完了済みタスクの一覧取得中にエラーが発生しました。"

# 📌 期限付きタスクを登録する
def registerTaskWithDue(title, due):
    try:
        creds = getCredentials()
        service = build("tasks", "v1", credentials=creds)

        tasklist_id = getDefaultTasklistId(service)
        print("📦 使用中のtasklist_id:", tasklist_id)

        task_body = {
            "title": title
        }

        if due:
            # 文字列からdatetimeへ変換し、UTCのISO形式にする
            from datetime import datetime, timezone
            due_dt = datetime.strptime(due, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            task_body["due"] = due_dt.isoformat()

        result = service.tasks().insert(tasklist=tasklist_id, body=task_body).execute()
        print("✅ 登録されたタスク:", result)
        return f"✅ タスク『{title}』を登録しました。期限: {due if due else '指定なし'}"

    except Exception as e:
        print("❌ タスク登録（期限付き）エラー：", e)
        return "タスク登録中にエラーが発生しました。"

# ✅ 期限付きのタスク（未完了）だけを抽出して一覧表示
def registerTaskWithDue(title, due_raw):
    try:
        creds = getCredentials()
        service = build("tasks", "v1", credentials=creds)
        tasklist_id = getDefaultTasklistId(service)
        print("📦 使用中のtasklist_id:", tasklist_id)

        # ISO 8601形式かどうかを検証＆変換（例：2025-05-03 → 2025-05-03T00:00:00.000Z）
        try:
            if "T" not in due_raw:
                # もし日付だけだったら00:00:00にしてUTC形式に
                dt = datetime.strptime(due_raw, "%Y-%m-%d")
                due = dt.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
            else:
                # そのままISOとして使う（形式崩れていたら下でエラーになる）
                dt = datetime.fromisoformat(due_raw.replace("Z", "+00:00"))
                due = dt.isoformat().replace("+00:00", "Z")
        except Exception as e:
            print("❌ 期限形式エラー：", e)
            return "期限の形式が正しくありません（例：2025-05-03）。"

        task_body = {
            "title": title,
            "due": due
        }

        result = service.tasks().insert(tasklist=tasklist_id, body=task_body).execute()
        print("✅ 登録されたタスク:", result)
        
  # 🔧 ここでフォーマット変換（末尾の"Z"は除去）
        formatted_due = datetime.strptime(due.replace("Z", ""), "%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%d")

        return f"✅ タスク『{title}』を登録しました（期限: {formatted_due}）"
        #return f"✅ タスク『{title}』を登録しました （期限: {due}）\n🔗 {result.get('webViewLink')}"

    except Exception as e:
        print("❌ タスク登録（期限付き）エラー：", e)
        return "タスク登録中にエラーが発生しました。"

# ✅ 期限付きタスク（未完了）を一覧で返す
def listTasksWithDue():
    try:
        creds = getCredentials()
        service = build("tasks", "v1", credentials=creds)
        tasklist_id = getDefaultTasklistId(service)
        print("📦 使用中のtasklist_id:", tasklist_id)

        results = service.tasks().list(tasklist=tasklist_id, showCompleted=True).execute()
        tasks = results.get("items", [])

        response = "期限付きタスク一覧：\n"
        for task in tasks:
            title = task.get("title", "").strip()
            due = task.get("due")
            status = task.get("status")

            if due and status != "completed":
                due_date = due.split("T")[0]
                response += f"・{title}：期限 {due_date}\n"

        if response.strip() == "期限付きタスク一覧：":
            return "現在、期限付きのタスクは登録されていません。"

        return response

    except Exception as e:
        print("❌ 期限付きタスク一覧取得エラー：", e)
        return "期限付きタスク一覧の取得中にエラーが発生しました。"
