import streamlit as st
import google.generativeai as genai

# ページ設定
st.set_page_config(
    page_title="面談メモ整理ツール",
    page_icon="📋",
    layout="wide"
)

# タイトル
st.title("📋 面談メモ整理ツール")

# 履歴の初期化
if "history" not in st.session_state:
    st.session_state.history = []

# APIキーの取得（Gemini APIを使用）
if "GEMINI_API_KEY" not in st.secrets:
    st.error("⚠️ `.streamlit/secrets.toml` に `GEMINI_API_KEY` が設定されていません。")
    st.info("💡 Google Gemini APIキーは無料で取得できます。")
    st.markdown("""
    **APIキーの取得方法：**
    1. [Google AI Studio](https://aistudio.google.com/apikey) にアクセス
    2. Googleアカウントでログイン
    3. 「Create API Key」をクリック
    4. 生成されたキーを `.streamlit/secrets.toml` に設定
    """)
    st.stop()

# Gemini APIクライアントの初期化
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
# 無料枠が利用可能な軽量モデルを使用
model = genai.GenerativeModel('gemini-flash-lite-latest')

# システムプロンプト
SYSTEM_PROMPT = """あなたはファイナンシャルプランナー（FP）の面談メモを整理・編集する専門家です。

【変換ルール】
- 保険業界用語の補正を行ってください（例：iOSM→あいおい生命、20日7日→27日など）。
- 文体は「だ・である」調で統一してください。
- 誤変換や文脈の乱れを自然に補正してください。
- 人名は漢字変換せず、カタカナで表記してください（例：たかしさん→タカシさん）。
- 敬称は「様」ではなく「さん」を使用してください。

【重要：不明な情報の扱い】
- 情報が不明な場合は、その項目を完全に省略してください。「不明」「不明の教室」「不明な場合」などの記述は一切不要です。
- 推測できない情報は書かないでください。空欄にするか、その項目自体を省略してください。

【不足情報のチェック】
以下の要素が入力内容に含まれているか確認してください：
1. 面談日時・形式
2. 決定事項・次回の予定
3. ToDo

これらが明確に含まれていない場合、出力の一番下に「⚠️ 未確認: （不足項目をカンマ区切りで列挙）」とだけ短く追記してください。
全て揃っている場合は、この警告行は表示しないでください。

【出力フォーマット】
以下の構成を厳守してください。

--------------------------------------------------
■面談日時・形式
YYYY年MM月DD日 HH:MM〜（形式）
※情報が不明な場合はこの項目を省略してください

■面談概要
（要約）

■詳細内容
（箇条書きで、何について話したかを記載）
例：「終身保険と定期保険の違いについて説明した」「保険金額の試算について話し合った」
※「検討した」ではなく「話した」「説明した」「話し合った」などの表現を使用

■決定事項・今後の予定
（内容）
※情報が不明な場合はこの項目を省略してください

■ToDo
（内容）
※なしの場合は「なし」と記述、情報が不明な場合はこの項目を省略してください

（不足がある場合のみ以下を表示）
--------------------------------------------------
⚠️ **未確認**: （不足項目名）, （不足項目名）
--------------------------------------------------
"""

# レイアウト：左右カラム
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("📝 入力")
    input_text = st.text_area(
        "メモを入力してください",
        height=500,
        placeholder="例：今日は生命保険について相談がありました。27日の午後2時から面談予定です。..."
    )
    
    generate_button = st.button("🚀 メモを整理", type="primary", use_container_width=True)

with col_right:
    st.subheader("📄 生成結果")
    
    if generate_button:
        if not input_text.strip():
            st.warning("⚠️ 入力テキストが空です。メモを入力してください。")
        else:
            with st.spinner("AIがメモを整理中..."):
                try:
                    # Gemini API呼び出し（無料枠あり）
                    prompt = f"{SYSTEM_PROMPT}\n\n以下のメモを整理して整形してください：\n\n{input_text}"
                    response = model.generate_content(
                        prompt,
                        generation_config=genai.types.GenerationConfig(
                            temperature=0.3,
                        )
                    )
                    
                    generated_text = response.text
                    
                    # 履歴に追加（最新を先頭に）
                    from datetime import datetime
                    history_entry = {
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "input": input_text,
                        "output": generated_text
                    }
                    st.session_state.history.insert(0, history_entry)
                    
                    # 履歴は最大50件まで保持
                    if len(st.session_state.history) > 50:
                        st.session_state.history = st.session_state.history[:50]
                    
                    # 生成結果を表示
                    st.text_area(
                        "整理されたメモ",
                        value=generated_text,
                        height=400,
                        key="output_text"
                    )
                    
                    # クリップボードにコピー用のコードブロック（選択しやすくするため）
                    st.markdown("**📋 コピー用（全選択してCtrl+C）**")
                    st.code(generated_text, language=None)
                    
                except Exception as e:
                    error_message = str(e)
                    
                    # エラーメッセージを日本語に変換
                    if "Connection" in error_message or "connection" in error_message or "failed" in error_message.lower():
                        st.error("❌ **接続エラーが発生しました**")
                        st.warning("インターネット接続を確認してください。VPNを使用している場合は、VPNの接続状態を確認してください。")
                    elif "API key" in error_message or "api_key" in error_message or "authentication" in error_message.lower():
                        st.error("❌ **APIキーエラーが発生しました**")
                        st.warning("APIキーが正しく設定されているか確認してください。`.streamlit/secrets.toml` ファイルを確認してください。")
                    elif "quota" in error_message.lower() or "rate limit" in error_message.lower() or "limit" in error_message.lower():
                        st.error("❌ **リクエスト制限に達しました**")
                        st.warning("Gemini APIの無料枠には1分あたりのリクエスト数に制限があります。しばらく待ってから再試行してください。")
                    elif "timeout" in error_message.lower():
                        st.error("❌ **タイムアウトエラーが発生しました**")
                        st.warning("リクエストがタイムアウトしました。インターネット接続を確認して、もう一度お試しください。")
                    else:
                        st.error(f"❌ **エラーが発生しました**")
                        st.warning(f"エラー内容: {error_message}")
                    
                    st.info("💡 問題が解決しない場合は、APIキーが正しく設定されているか、インターネット接続を確認してください。")
    else:
        st.info("👈 左側に入力テキストを貼り付けて、「メモを整理」ボタンをクリックしてください。")

# 履歴セクション
st.markdown("---")
st.subheader("📚 生成履歴")

if st.session_state.history:
    # 履歴クリアボタン
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("🗑️ 履歴をクリア", type="secondary"):
            st.session_state.history = []
            st.rerun()
    
    # 履歴表示（タブ形式）
    for idx, entry in enumerate(st.session_state.history):
        with st.expander(f"📄 {entry['timestamp']}", expanded=(idx == 0)):
            col_input, col_output = st.columns([1, 1])
            
            with col_input:
                st.markdown("**📝 入力**")
                st.text_area(
                    "入力テキスト",
                    value=entry['input'],
                    height=200,
                    key=f"history_input_{idx}",
                    label_visibility="collapsed"
                )
            
            with col_output:
                st.markdown("**📄 生成結果**")
                st.text_area(
                    "生成結果",
                    value=entry['output'],
                    height=200,
                    key=f"history_output_{idx}",
                    label_visibility="collapsed"
                )
            
            # コピー用コードブロック
            st.markdown("**📋 コピー用（全選択してCtrl+C）**")
            st.code(entry['output'], language=None)
            st.markdown("---")
else:
    st.info("📝 履歴はまだありません。メモを整理すると、ここに履歴が表示されます。")

# フッター
st.markdown("---")
st.caption("🆓 Google Gemini APIを使用しているため、完全無料で利用できます。")
