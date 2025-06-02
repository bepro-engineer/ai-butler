以下は、AI執事（`ai-butler）プロジェクト用の `README.md` のサンプルです。<br>
VPS環境（Ubuntu）での動作・GitHubクローン・環境構成が前提の構成になっています。

---
## 💻 AI執事の動作画面

以下は、実際にAI執事をLINE上で利用した際の画面例です。
-本プロジェクトでは、LINEメッセージを通じて自然な文章を送信するだけで、Googleカレンダー上の予定を即時操作できます。
-ユーザーが「明日の午後3時に通院」と入力すると、予定がGoogleカレンダーに自動登録されます
-「明日の通院を削除して」と送れば、該当予定が削除されます
-すべての処理は ChatGPTによる自然言語解析 → GoogleカレンダーAPI操作 によってリアルタイムで行われます

<div align="center">
  <img src="https://github.com/bepro-engineer/ai-butler$/raw/main/images/ai_butler_screen.png" width="300">
</div>

```plaintext
# AI執事（ai-butler）

「LINEに話しかけるだけで、予定を登録・更新・削除できる。」

## 📌 プロジェクト概要

AI執事は、ChatGPT・GoogleカレンダーAPI・LINE Messaging API を組み合わせた予定管理AIです。  
ユーザーはLINE上で自然な文章を送るだけで、予定の登録・変更・削除が可能になります。  
Googleカレンダーとの同期機能は、OpenAIの自然言語解析を通じて実現しています。

## 🧩 構成ファイル
```
ai_butler/
  - app.py：エントリーポイント
  - config.py：設定ファイル
  - .env：環境変数
  - requirements.txt：ライブラリ一覧
  - logic/
    - __init__.py
    - chatgpt_logic.py：ChatGPT処理
    - db_utils.py：DB処理
```

## 🚀 セットアップ手順（Ubuntu）
1. GitHubからクローン  
   ※PAT（Personal Access Token）を使用してクローンする必要があります。
   ```bash
   cd ~/projects/ai_butler$
   git clone https://github.com/bepro-engineer/ai-butler$.git
````

2. 仮想環境の作成と起動
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. 依存ライブラリのインストール
   ```bash
   pip install -r requirements.txt
   ```

4. `.env`ファイルの作成
   `.env` に以下を記載（OpenAI APIキーは自身で取得）
   ```
   OPENAI_API_KEY=sk-xxxxxxx
   LINE_CHANNEL_SECRET=xxxxxxxxxx
   LINE_CHANNEL_ACCESS_TOKEN=xxxxxxxxxx
   GOOGLE_CALENDAR_ID=xxxxxxxxxxx@group.calendar.google.com
   GOOGLE_CREDENTIALS_PATH=credentials/calendar-credentials.json

   ```

5. データベース初期化（必要に応じて）
   ```bash
   python logic/db_utils.py
   ```

## 🧪 テスト起動
```bash
python app.py
```

## 💬 利用できる自然言語コマンド例

```plaintext
明日14時に歯医者                   → 予定を新規登録
来週月曜の9時に定例ミーティング    → 曜日指定の予定を新規登録
明日の歯医者を削除して             → キーワード一致で予定削除
明日の歯医者を16時に変更して       → 時間を更新
明日14時からの予定をキャンセル    → 時間指定で予定削除
明日キャンセルして                 → 日付指定の予定をすべて削除
明日の会議を30分前倒しして         → 時間を前倒しで更新
明日の予定を「病院」に書き換えて   → タイトルを更新
明日の会議を明後日に変更           → 日付を更新
明日の予定をすべて一覧で教えて     → 予定の一覧表示（拡張候補）
```

## 🛡️ 注意事項
* 本プロジェクトは**研究・学習用途**です。商用利用はライセンスを確認の上、自己責任で行ってください。
* OpenAIのAPIコストが発生します。使用量には十分注意してください。

## 📝 ライセンス
```plaintext
MIT License
```
