VPS環境（Ubuntu）での動作・GitHubクローン・環境構成が前提の構成になっています。

📚 詳細な解説はこちら<br><br>
本プロジェクトの詳しい背景や仕組み、導入手順については、以下のブログ記事で解説しています。<br>
👉 AI執事システム｜自分のスケジュールを自動で管理する仕組みを公開中<br>
詳しい説明は[こちらのブログ記事 (Beエンジニア) ](https://www.pmi-sfbac.org/category/product/ai-butler-system/)をご覧ください。

---
## 💻 AI執事の動作画面

以下は、実際にAI執事をLINE上で利用した際の画面例です。
-本プロジェクトでは、LINEメッセージを通じて自然な文章を送信するだけで、Googleカレンダー上の予定を即時操作できます。
-ユーザーが「明日の午後3時に通院」と入力すると、予定がGoogleカレンダーに自動登録されます
-「明日の通院を削除して」と送れば、該当予定が削除されます
-すべての処理は ChatGPTによる自然言語解析 → GoogleカレンダーAPI操作 によってリアルタイムで行われます
（左イメージ：予定　右イメージ：タスク）

<div align="center">
  <img src="https://github.com/bepro-engineer/ai_butler/blob/main/images/ai_butler_screen.png" width="600">
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
⭐️ 予定（いつ、なんじ、なんの予定を、「なんじに」、〇〇して）
明日14時に歯医者の予定を入れて
明日の14時の歯医者の予定を削除して
明日の14時の歯医者の予定を16時に変更して
明日の14時の歯医者の予定をキャンセル
明日の14時の歯医者の予定を明後日に変更して
明日の予定をすべて一覧で教えて

⭐️タスク
タスクを追加して：プロポーザル作戦
明日までにレポートを提出するタスクを登録して
タスク一覧を確認
プロポーザル作戦を完了にして
レポートを提出するタスクを削除して
完了したタスクを教えて
期限付きタスクを確認
```

## 🛡️ 注意事項
* 本プロジェクトは**研究・学習用途**です。商用利用はライセンスを確認の上、自己責任で行ってください。
* OpenAIのAPIコストが発生します。使用量には十分注意してください。

## 📝 ライセンス
```plaintext
MIT License
```
