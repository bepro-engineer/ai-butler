# 🤖 AI執事 – GoogleカレンダーとLINEで予定管理を自動化
<div align="center">
<img src="https://raw.githubusercontent.com/bepro-engineer/ai-butler/main/images/butler_screen_top.png" width="700">
</div>

# 🤖 AI執事（バトラー）– LINEに話すだけで予定が入る、未来の秘書

「予定を忘れるな。言ったのは“あなた自身”だ。」

---

## ✨ AI執事とは？

「明日の16時に歯医者」  
たったこれだけをLINEに送るだけで、Googleカレンダーに予定が自動登録される──  
それがAI執事（バトラー）です。

AI執事は、ChatGPTを活用し、あなたの自然な発話を解析。  
Googleカレンダーに「登録・削除・変更」までを自動処理するAI秘書です。

---

## 🚀 なぜAI執事は便利なのか？

| 手動カレンダー入力 | AI執事 |
|--------------------|--------|
| アプリを開いて手入力が必要 | **LINEに話すだけで完了** |
| 曜日・日付・時刻を毎回調整 | **自然な言葉から自動解析** |
| 予定の削除や変更も面倒 | **1メッセージで削除・変更OK** |
| 外出先では操作しづらい | **スマホ1つ、音声入力でも対応可能** |

---

## 💡 こんな人におすすめ

- 予定の管理が苦手で忘れがちな人
- 移動中や外出先で予定を簡単に入れたい人
- タスクアプリやGoogleカレンダー入力が面倒な人
- 「話すだけで済む」未来的な体験をしたい人

---

## 🔁 AI執事が対応する処理

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

---

## 📚 ブログ解説（導入背景・技術・構成）

このプロジェクトの詳しい背景・構成・実装意図については、以下の記事で完全解説しています。

👉 [AI執事の作り方｜予定を自動で管理する未来秘書AIを作る](https://www.pmi-sfbac.org/category/product/butler-system/)

---

## 💻 AI執事の動作画面

以下は、LINEでAI執事を実行した実際の画面イメージです：

- 左：予定の登録（自然な日本語）  
- 右：予定の削除や変更

<div align="center">
<img src="https://raw.githubusercontent.com/bepro-engineer/ai-butler/main/images/butler_screen.png" width="600">
</div>

✍️ AI執事は、送るだけで完了します。  
いちいちカレンダーを開かなくていい。入力欄もいらない。  
“言葉で動くカレンダー”──それがAI執事の正体です。

---

## 📌 プロジェクト構成

```plaintext
ai_butler/
├── app.py                   # Flaskアプリ本体（LINE受信・処理ルーティング）
├── .env                     # APIキーなどの環境変数
├── requirements.txt         # 必要ライブラリ
├── logic/
│   ├── chatgpt_logic.py     # ChatGPTの発話解析ロジック
│   ├── calendar_utils.py    # Googleカレンダー登録・削除・変更ロジック
│   ├── task_utils.py        # Googleタスク登録・削除・変更ロジック
│   ├── db_utils.py          # SQLite操作（予定の記録）
│   └── __init__.py
└── images/
    └── butler_screen.png    # 動作イメージ
```

---

## 🛠️ セットアップ手順（Ubuntu）

```bash
# 1. GitHubからクローン
git clone https://github.com/bepro-engineer/ai-butler.git
cd ai-butler

# 2. 仮想環境の構築と起動
python3 -m venv .venv
source .venv/bin/activate

# 3. ライブラリのインストール
pip install -r requirements.txt

# 4. .envファイルの作成
# 以下の内容を.envに記載（各種キーは自分で取得）
OPENAI_API_KEY=sk-xxxxxxx
LINE_CHANNEL_SECRET=xxxxxxxxxx
LINE_CHANNEL_ACCESS_TOKEN=xxxxxxxxxx
GOOGLE_CLIENT_SECRET=client_secret.json
PHASE_MODE=learn  # or reply

# 5. 初期化処理（データベース作成など）
python logic/db_utils.py

# 6. テスト起動
python app.py
```

---

## 💬 モードについて

| モード | 説明 |
|--------|------|
| learn  | ChatGPTで発言解析し、予定として登録・記録（学習モード） |
| reply  | ChatGPTが予定に応じてリマインド・返信（応答モード） |

`.env`内の`PHASE_MODE`を切り替えることで動作モードを変更可能です。

---

## 🛡️ 注意事項

- OpenAI APIやGoogleカレンダーAPIの利用には**課金が発生する可能性**があります。
- プライバシーを含む内容を記録する場合は**自己責任**で取り扱ってください。
- 本プロジェクトはあくまで**個人利用・学習目的**での構築を想定しています。

---

## 📜 ライセンス

MIT License

