import os
import re
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

# 🚦 detectExplicitType: 「予定」／「タスク」を “登録系・削除系・完了系の動詞” とセットで書いたときだけ強制ルート振り分けする
def detectExplicitType(user_message: str):
    """
    ● user_message に含まれる単語をみて
        'schedule' : Google Calendar の「登録」ルートへ直行
        'task'     : Google Tasks の「登録／削除／完了」ルートへ直行
        None       : 明示でないので classifyIntent() に任せる

    ＊トリガー条件＊
      - 予定 or タスク + 登録系動詞
      - タスク + 削除 or 完了系動詞
      - ただし「完了したタスク一覧を教えて」などは intent 推論へ回す
    """

    # 登録・削除・完了のキーワードを定義
    register_verbs  = ["入れて", "追加", "登録", "作成"]
    delete_verbs    = ["削除", "削除して", "消して", "消す", "消去"]
    complete_verbs  = ["完了", "完了して", "終わらせ", "終わった", "終了"]
    # ★ 「一覧要求」を示す語（完了一覧やタスクリスト要求を強制判定しないため）
    list_keywords   = ["一覧", "教えて", "確認", "リスト"]

    # --- 予定登録 --------------------------------------------------
    if "予定" in user_message and any(v in user_message for v in register_verbs):
        print("✅ detectExplicitType: 予定＋登録動詞 → 'schedule' を返します")
        return "schedule"

    # --- タスク登録 ------------------------------------------------
    if "タスク" in user_message and any(v in user_message for v in register_verbs):
        print("✅ detectExplicitType: タスク＋登録動詞 → 'task' を返します")
        return "task"

    # --- タスク削除 ------------------------------------------------
    if any(v in user_message for v in delete_verbs):
        # 「タスク」明示 もしくは 「〜を削除/消して」が入っていれば削除
        if "タスク" in user_message or "を削除" in user_message or "を消して" in user_message:
            print("✅ detectExplicitType: タスク削除と判定 → 'task' を返します")
            return "task"

    # --- タスク完了 ------------------------------------------------
    if any(v in user_message for v in complete_verbs):
        # ▽ 一覧を求めている時は intent 推論（task_list_completed 等）に委譲
        if any(k in user_message for k in list_keywords):
            print("ℹ️ detectExplicitType: 完了一覧要求 → None を返し intent 推論へ")
            return None
        # 通常の完了指示
        if "タスク" in user_message or "を完了" in user_message:
            print("✅ detectExplicitType: タスク完了と判定 → 'task' を返します")
            return "task"

    # --- ここまで該当なし → intent 推論へ ------------------------
    print("ℹ️ detectExplicitType: 判定できず None を返します（AI判定へ委譲）")
    return None

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

# タスク関連の動詞（削除や完了など）を除去する正規表現
_PAT_TAIL = re.compile(r"(タスク)?(を)?(削除|消す|完了)(する|して)?$")

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

    # ✅ 正規化：削除・完了などの余計な語句を取り除く（正規表現を使用）
    title = re.sub(_PAT_TAIL, "", title).strip()

    # 不要な語句（追加や変更など）を手動で除去
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
def askChatgpt(user_message, forced_type=None):
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # 🚩 明示ルールを優先して処理
        explicit_type = detectExplicitType(user_message)
        
        # schedule と task の処理を共通化
        if explicit_type == "schedule":
            return handleSchedule(user_message)
        elif explicit_type == "task":
            return handleTask(user_message)

        # intent判定による追加処理
        intent = classifyIntent(user_message)
        print(f"🎯 intent 判定: {intent}")

        if intent.startswith("schedule+"):
            day_offset = int(intent.split("+")[1])
            return getScheduleByOffset(day_offset)

        # 以下は意図に基づく処理を一つの関数でまとめる
        if intent in ["task_register", "task_list", "task_complete", "task_delete", "task_list_completed", "task_list_due"]:
            return handleTaskActions(intent, user_message)

        return "意図が不明です。再度入力してください。"

    except Exception as error:
        print("❌ ChatGPT応答全体エラー：", error)
        return "申し訳ありません。システムエラーが発生しました。後ほど再度お試しください。"

def handleSchedule(user_message):
    new_event = extractNewEventDetails(user_message, require_time=True)
    title = new_event["title"]
    start_time = datetime.strptime(new_event["start_time"], "%Y-%m-%d %H:%M:%S")
    return registerSchedule(title, start_time)

def handleTask(user_message):
    # 動詞セット（detectExplicitType と揃える）
    delete_verbs = ["削除", "削除して", "消して", "消す", "消去"]
    complete_verbs = ["完了", "完了して", "終わらせ", "終わった", "終了"]

    # 1) 削除指示なら deleteTask
    if any(v in user_message for v in delete_verbs):
        title = extractTaskTitle(user_message).get("title")
        return deleteTask(title)

    # 2) 完了指示なら completeTask
    if any(v in user_message for v in complete_verbs):
        title = extractTaskTitle(user_message).get("title")
        return completeTask(title)

    # 3) それ以外は登録（期限付きなら WithDue）
    task_info = extractTaskDetails(user_message)
    title, due = task_info["title"], task_info["due"]
    return registerTaskWithDue(title, due) if due else registerTask(title)

def handleTaskActions(intent, user_message):
    if intent == "task_register":
        title = extractTaskTitle(user_message).get("title")
        return registerTask(title) if title else "タスク名が抽出できませんでした。"

    elif intent == "task_list":
        return listTasks()

    elif intent == "task_complete":
        title = extractTaskTitle(user_message).get("title")
        return completeTask(title) if title else "完了させたいタスク名が見つかりませんでした。"

    elif intent == "task_delete":
        title = extractTaskTitle(user_message).get("title")
        return deleteTask(title) if title else "削除したいタスク名が見つかりませんでした。"

    elif intent == "task_list_completed":
        return listCompletedTasks()

    elif intent == "task_list_due":
        return listTasksWithDue()

        # 🤖 雑談や意図不明系はChatGPTへフォールバック
        # ✅ ここで forced_type による補強プロンプトを追加
        system_prompt = "あなたは親切で柔軟なAIアシスタントです。"

        if forced_type == "task":
            system_prompt += "\nこれはGoogle Tasksに関する命令です。恋愛やプロポーズなどとは関係ありません。"
        elif forced_type == "schedule":
            system_prompt += "\nこれはGoogle Calendarに関する命令です。"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        return response.choices[0].message.content
    