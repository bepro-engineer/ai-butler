from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/tasks"
]

def main():
    flow = InstalledAppFlow.from_client_secrets_file(
        "client_secret.json",
        scopes=SCOPES
    )

    # ✅ 明示的に redirect_uri を指定（これがないとGoogleが拒否）
    flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'

    # ✅ 認証URL生成（ここで redirect_uri が含まれるようになる）
    auth_url, _ = flow.authorization_url(prompt='consent')

    print("🔗 以下のURLをブラウザで開いて認証してください：")
    print(auth_url)

    code = input("🔑 認証後に表示されるコードを貼り付けてください: ")
    flow.fetch_token(code=code)

    with open("token.json", "w") as token_file:
        token_file.write(flow.credentials.to_json())

    print("✅ token.json を保存しました（refresh_token 含む）")

if __name__ == "__main__":
    main()

