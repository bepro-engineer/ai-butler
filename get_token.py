from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/tasks"
]

flow = InstalledAppFlow.from_client_secrets_file(
    "client_secret.json",
    scopes=SCOPES,
    redirect_uri='urn:ietf:wg:oauth:2.0:oob'
)

auth_url, _ = flow.authorization_url(prompt='consent')

print("以下のURLをローカルPCのブラウザで開いてください：")
print(auth_url)

code = input("認証後に表示されるコードをここに貼り付けてください: ")
flow.fetch_token(code=code)

with open("token.json", "w") as token:
    token.write(flow.credentials.to_json())
