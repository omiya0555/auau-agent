# auau-agent

## セットアップ

### Version
```
python3 -V
# Python 3.13.6
```

### リポジトリのクローン
```
git clone https://github.com/omiya0555/auau-agent.git
cd auau-agent
```

venv環境にアクセス
```
python3 -m venv .venv
source .venv/bin/activate
# プロンプトの最初に (venv) が追加される
```

### インストール
```
pip3 install -r requirements.txt
```

### AWS環境のセットアップ
```
aws configure
```
- 自身のアカウントのアクセスキーとシークレットを設定
- リージョンは us-west-2 
- 形式は json
※ 注意点：us-west-2 リージョンのBedrockから、claude4 のアクセスをリクエストしておく

### ローカル環境APIリクエストの検証
- APIサーバーの起動
```
uvicorn src.agents.base_sample.agent:app --reload --port 8000
```
- Curlコマンドでリクエスト
```
curl -X POST http://localhost:8000/stream \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"電気自動車の最近のトレンドを要約してください"}'
```
