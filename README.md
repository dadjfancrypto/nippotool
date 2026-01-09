# FP業務日報 生成ツール

ファイナンシャルプランナー（FP）向けの業務日報を自動生成するStreamlitアプリです。

## 🆓 無料で利用可能！

このツールは**Google Gemini API**を使用しており、**完全無料**で利用できます。

## 📋 機能

- 音声入力メモ（AquaVoice等）の誤変換を自動補正
- 指定フォーマットで業務日報を自動生成
- 不足情報（面談日時・決定事項・ToDo）の自動チェック

## 🚀 セットアップ方法

### 1. 必要なもの

- Python 3.8以上
- Google Gemini APIキー（**無料**で取得可能）

### 2. インストール手順

#### ステップ1: 必要なパッケージをインストール

```bash
pip install -r requirements.txt
```

または、個別にインストール：

```bash
pip install streamlit google-generativeai
```

#### ステップ2: APIキーを取得（無料）

1. [Google AI Studio](https://aistudio.google.com/apikey) にアクセス
2. Googleアカウントでログイン
3. 「Create API Key」をクリック
4. 生成されたAPIキーをコピー

#### ステップ3: APIキーを設定

`.streamlit/secrets.toml` ファイルを開いて、Gemini APIキーを設定してください：

```toml
GEMINI_API_KEY = "あなたのAPIキーをここに貼り付け"
```

**重要**: `your-api-key-here` の部分を実際のAPIキーに置き換えてください。

### 3. アプリの起動

以下のコマンドを実行：

```bash
streamlit run app.py
```

ブラウザが自動的に開き、アプリが表示されます（通常は `http://localhost:8501`）。

## 💻 使い方

### 基本的な操作手順

1. **左側のテキストエリア**に、音声入力で取得したメモを貼り付けます
   - 例：「今日はiOSMの保険について相談がありました。20日7日の午後2時から面談予定です...」

2. **「🚀 日報を生成」ボタン**をクリックします

3. **右側**に整形された業務日報が表示されます

4. **コピー用のコードブロック**を選択して、Ctrl+Cでコピーします

### 出力フォーマット

生成される日報は以下の形式です：

```
■面談日時・形式
2024年1月27日 14:00〜（対面）

■面談概要
あいおい生命の保険商品について相談があった。

■詳細内容
- 終身保険と定期保険の違いについて説明
- 保険金額の試算を実施
- 次回の面談日程を調整

■決定事項・今後の予定
次回は1月30日に詳細プランを提示予定

■ToDo（当方タスク）
- 保険商品の比較資料を作成
- 次回面談の日程を確定
```

不足情報がある場合は、最後に警告が表示されます：

```
⚠️ **未確認**: 面談日時, ToDo
```

## 🌐 Streamlit Community Cloudで公開する方法

### ステップ1: GitHubにプッシュ

1. GitHubで新しいリポジトリを作成
2. 以下のファイルをコミット・プッシュ：
   - `app.py`
   - `requirements.txt`
   - `.streamlit/secrets.toml` は**プッシュしない**（後で設定します）

### ステップ2: Streamlit Community Cloudでアプリを作成

1. [Streamlit Community Cloud](https://share.streamlit.io/) にアクセス
2. GitHubアカウントでログイン
3. 「New app」をクリック
4. リポジトリとブランチを選択
5. Main file path に `app.py` を指定

### ステップ3: APIキーを設定

1. アプリの「Settings」→「Secrets」を開く
2. 以下の形式でAPIキーを入力：

```toml
GEMINI_API_KEY = "あなたのAPIキー"
```

3. 「Save」をクリック

**注意**: Gemini APIは無料ですが、1分あたりのリクエスト数に制限があります。大量に使用する場合は、しばらく待ってから再試行してください。

### ステップ4: アプリを起動

「Run」ボタンをクリックしてアプリを起動します。

## ⚠️ 注意事項

- このツールは**ステートレス**です。履歴は保存されません
- APIキーは絶対に公開しないでください
- `.streamlit/secrets.toml` は `.gitignore` に追加することを推奨します
- Gemini APIは無料ですが、1分あたりのリクエスト数に制限があります（通常は十分な量です）

## 🐛 トラブルシューティング

### エラー: APIキーが設定されていません

→ `.streamlit/secrets.toml` に正しく `GEMINI_API_KEY` が設定されているか確認してください

### エラー: リクエスト制限に達しました

→ Gemini APIの無料枠には1分あたりのリクエスト数に制限があります。しばらく待ってから再試行してください

### エラー: モジュールが見つかりません

→ `pip install -r requirements.txt` を実行してください

### アプリが起動しない

→ Pythonのバージョンが3.8以上か確認してください：
```bash
python --version
```

## 📝 ファイル構成

```
fp-tool1/
├── app.py                 # メインアプリケーション
├── requirements.txt       # 依存パッケージ
├── .streamlit/
│   └── secrets.toml       # APIキー設定（ローカル用）
└── README.md             # このファイル
```
