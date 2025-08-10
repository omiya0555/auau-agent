# auau-agent

## セットアップ
### リポジトリのクローン
```
git clone https://github.com/omiya0555/auau-agent.git
cd auau-agent
```

venv環境にアクセス
```
source .venv/bin/activate
# プロンプトの最初に (venv) が追加される
```

### インストール
```
pip install -r requirements.txt
```

### AWS環境のセットアップ
```
aws configure
```
- 自身のアカウントのアクセスキーとシークレットを設定
- リージョンは us-west-2 
- 形式は json
※ 注意点：us-west-2 リージョンのBedrockから、claude4 のアクセスをリクエストしておく
