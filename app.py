import streamlit as st
import google.generativeai as genai
import re
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="面談メモ整理ツール",
    page_icon="📋",
    layout="wide"
)

# Title
st.title("📋 面談メモ整理ツール")

# Initialize history in session state
if "history" not in st.session_state:
    st.session_state.history = []

# Get API key (using Gemini API)
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

# Initialize Gemini API client
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
# Use lightweight model available in free tier
model = genai.GenerativeModel('gemini-flash-lite-latest')

def remove_placeholder_names(text, input_text):
    """入力に無い人名を顧客に置換する"""
    name_chars = r'[ァ-ヶーｦ-ﾟa-zA-Zぁ-ん\u4e00-\u9fff々]{2,}'
    suffix = r'(?:さん|くん|ちゃん|君|様|氏)'
    pattern = rf'({name_chars})({suffix})'

    # 入力に登場する名前（敬称付き・なし両方）を収集
    input_names = set()
    for m in re.finditer(pattern, input_text):
        input_names.add(m.group(1))

    def replace_if_not_in_input(match):
        name = match.group(1)
        honorific = match.group(2)
        # 入力に名前自体が含まれていれば許可
        if name in input_names or name in input_text:
            return match.group(0)
        return '顧客'

    return re.sub(pattern, replace_if_not_in_input, text)

# Function to extract and remove unconfirmed items from generated text
def extract_unconfirmed_items(text):
    """未確認事項を抽出し、テキストから削除する"""
    # Pattern to match: ⚠️ 未確認: or ⚠️ **未確認**: followed by items
    pattern = r'⚠️\s*\*?\*?未確認\*?\*?:\s*([^\n]+)'
    match = re.search(pattern, text)
    
    if match:
        unconfirmed_items = match.group(1).strip()
        # Remove the unconfirmed line and any separator lines around it
        # Remove lines with ⚠️ 未確認 and surrounding separator lines (----)
        text_cleaned = re.sub(r'-{4,}\s*\n\s*⚠️\s*\*?\*?未確認\*?\*?:\s*[^\n]+\s*\n\s*-{4,}', '', text, flags=re.MULTILINE)
        text_cleaned = re.sub(r'⚠️\s*\*?\*?未確認\*?\*?:\s*[^\n]+', '', text_cleaned)
        text_cleaned = re.sub(r'-{4,}\s*\n\s*-{4,}', '', text_cleaned)  # Remove double separators
        text_cleaned = text_cleaned.strip()
        return text_cleaned, unconfirmed_items
    else:
        return text.strip(), None

# System prompt for AI (current_year and current_date are filled at runtime)
def get_system_prompt():
    now = datetime.now()
    current_year = now.year
    current_date = now.strftime("%Y年%m月%d日")
    return f"""あなたはファイナンシャルプランナー（FP）の面談メモを整理・編集する専門家です。

【人物名の扱い（最優先・厳守）】
- **出力に使っていい名前は、入力テキストに実際に登場した名前だけ。** それ以外の名前は一切禁止。
- 「入力に登場した名前」とは、入力テキスト内に「〇〇さん」「〇〇くん」「〇〇ちゃん」「〇〇」のように文字として書かれている人名のみ。
- タカシ、田中、佐藤、山田など、過去の例や学習データに含まれるような名前を勝手に補完・使用することは絶対禁止。
- 誰かと話したが名前が入力に無い場合は「顧客」と書く。架空・補完・推測の名前は一切使わない。
- **人名はカタカナで表記すること。** 入力に「いさおさん」とあれば「イサオさん」、「あけみさん」とあれば「アケミさん」のようにカタカナに変換すること。ただし、入力に「ななちゃん」とあれば「ナナちゃん」のように、読み方は入力のままカタカナに変換すること（「ナミさん」など別の名前に変えるのは禁止）。
- **入力に登場した異なる名前は、必ず別人物として区別すること。** 入力に「あけみさん」と「愛さん」が両方登場する場合は、それぞれ「アケミさん」「アイさん」として区別し、混同しないこと。

【発言者の区別（最重要・厳守）】
- **FP側が説明したことと、顧客が言ったことを明確に区別すること。**
- 「お伝え」「説明した」「提案した」などの表現がある場合は、それがFP側の説明であることが文脈から明確になるように記載すること。
- 特に「〜と思うとお伝え」「〜と説明した」のような表現がある場合、その「〜」の部分がFP側が説明した内容であることを明確にすること。顧客の発言のように誤解されないよう、主語や文の構造を調整すること。
- 例：「それでもガンの自由診療はご家族が助かってほしいという気持ちがあるから残してほしいと思うとお伝え」→「それでもガンの自由診療特約については、ご家族が助かってほしいという気持ちがあるから残してほしいと説明し」のように、FP側が説明したことが明確になるように記載すること。
- **「〜という意向があるため」「〜という意向がある」のような表現は、顧客の発言を示す場合にのみ使用すること。FP側が説明した内容を「〜という意向があるため」のように書いてはいけない。**
- **入力に「〜と思うとお伝え」「〜と説明した」がある場合、その「〜」の部分は必ずFP側が説明した内容として記載すること。これを「〜という意向があるため」のように顧客の発言として書いてはいけない。**
- 顧客の発言は「〇〇さんは〜と話した」「〇〇さんは〜とのこと」など、明確に主語を付けて記載すること。
- FP側の説明が顧客の発言のように読まれないよう注意すること。必要に応じて主語を追加するか、文の構造を調整すること。

【変換ルール】
- 保険業界用語の補正を行ってください（例：iOSM→あいおい生命、20日7日→27日など）。
- 文体はカジュアルで簡潔なメモ調（「〜した」「〜の予定」など）にしてください。フォーマルな表現は不要です。
- 誤変換や文脈の乱れを自然に補正してください。
- 敬称は「様」ではなく「さん」を使用してください。
- 「同席」と「共に説明を行った」は意味が異なる。「同席」は聞き手として参加していたことを意味し、「共に説明を行った」は説明者として参加したことを意味する。入力に「同席」とあれば、それを「共に説明を行った」に変更しないこと。入力に「〇〇さんも同席」とあれば、「〇〇さんも同席した」または「〇〇さんも同席して説明を行った」のように記載し、「〇〇さんと共に説明を行った」とは書かないこと。

【ボイス入力の補正と用語の統一】
- 入力はボイス入力（音声認識）であるため、聞き間違い・同音異義・そのまま文字になっただけの表現が含まれる。文脈や似たニュアンスから意味を汲み取り、**正しい保険・FP用語でメモとして書き足し・書き換え**して出力すること。
- 次の用語は、言い換えや似た表現が話されていれば、出力では正式な用語で記載すること：
  - 解約したときにもらえるお金・解約で戻るお金 → **解約返戻金**
  - 保険を扱っている会社・保険の会社 → **保険会社**
  - 市場の価格で調整する・時価調整・価格の調整 → **市場価格調整**
  - 定期的に払うお金・毎月の支払い・定期の支払 → **定期支払金**（ただし、保険料の合計を表す場合は「保険料」を使用すること）
  - 生命保険会社名（あいおい、にほん、すみとも など） → **〇〇生命**（例：あいおい生命、日本生命、住友生命）
  - 就寝保険・終身ほけん・しゅうしんほけん・終身の保険 → **終身保険**
- 上記に限らず、保険・年金・資産運用などで使う正式な用語が推測できる場合は、その用語で出力に反映すること。入力の「そのまま」ではなく、**こういうメモとして残すべき形**に整えて出力すること。

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

【日付・西暦の扱い（必須）】
- **西暦が入力に含まれていない場合、ユーザーが言わなくても必ず現在の西暦（{current_year}年）で補完すること。** 今日は{current_date}。年を省略した日付（例：27日、3月15日、来月5日）はすべて「{current_year}年」をつけて出力すること。
- 面談日時・予定・期日などは、必ず「YYYY年MM月DD日」のように**期日まで省略せずに**書くこと。

【出力フォーマット】
以下の構成を厳守してください。**各セクション（■で始まる見出し）の前後には必ず空行を1行入れること。** 見出しと内容の間にも空行を入れること。

--------------------------------------------------
■面談日時・形式
YYYY年MM月DD日 HH:MM〜（形式）
※情報が不明な場合はこの項目を省略してください。日付がある場合は上記のルールで年を補完し、期日まで記載すること

■面談概要
（今回の面談のテーマを1〜2文で。詳細内容・決定事項・ToDoに書く内容は繰り返さない）

■詳細内容
（箇条書きで話した内容を記載。面談概要・決定事項・ToDoと重複する内容は書かない）
※「検討した」ではなく「話した」「説明した」「話し合った」などの表現を使用

■決定事項・今後の予定
（決まったこと・次回の予定のみ。詳細内容と重複する内容は書かない）
※情報が不明な場合はこの項目を省略してください

■ToDo
（やること。決定事項・今後の予定と重複する内容は書かない）
※なしの場合は「なし」と記述、情報が不明な場合はこの項目を省略してください

（不足がある場合のみ以下を表示）
--------------------------------------------------
⚠️ **未確認**: （不足項目名）, （不足項目名）
--------------------------------------------------
"""


# Layout: left and right columns
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
                    # Call Gemini API (free tier available)
                    current_year = datetime.now().year
                    prompt = f"{get_system_prompt()}\n\n以下のメモを整理して整形してください。\n※現在の西暦は {current_year} 年です。年が指定されていない日付は必ず「{current_year}年」で補完すること。\n※入力に人名が含まれていない場合、タカシさん等の架空の名前は絶対に出力しないこと。\n\n{input_text}"
                    response = model.generate_content(
                        prompt,
                        generation_config=genai.types.GenerationConfig(
                            temperature=0.3,
                        )
                    )
                    
                    generated_text = response.text
                    
                    # Extract unconfirmed items and clean the text
                    cleaned_text, unconfirmed_items = extract_unconfirmed_items(generated_text)
                    # 入力に無い架空の人名を顧客に置換
                    cleaned_text = remove_placeholder_names(cleaned_text, input_text)
                    
                    # Display unconfirmed items if any
                    if unconfirmed_items:
                        st.warning(f"⚠️ **未確認**: {unconfirmed_items}")
                    
                    # Add to history (latest entry at the beginning)
                    history_entry = {
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "input": input_text,
                        "output": cleaned_text,
                        "unconfirmed": unconfirmed_items
                    }
                    st.session_state.history.insert(0, history_entry)
                    
                    # Keep maximum 50 history entries
                    if len(st.session_state.history) > 50:
                        st.session_state.history = st.session_state.history[:50]
                    
                    # Display generated result (session state を上書きして最新結果を表示)
                    st.session_state["output_text"] = cleaned_text
                    st.text_area(
                        "整理されたメモ",
                        value=cleaned_text,
                        height=400,
                        key="output_text"
                    )
                    
                    # Code block for clipboard copy (easy to select)
                    st.markdown("**📋 コピー用（全選択してCtrl+C）**")
                    st.code(cleaned_text, language=None)
                    
                except Exception as e:
                    error_message = str(e)
                    
                    # Convert error messages to Japanese
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

# History section
st.markdown("---")
st.subheader("📚 生成履歴")

if st.session_state.history:
    # Clear history button
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("🗑️ 履歴をクリア", type="secondary"):
            st.session_state.history = []
            st.rerun()
    
    # Display history (expandable format)
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
                # Display unconfirmed items if any (for backward compatibility, check if exists)
                if 'unconfirmed' in entry and entry['unconfirmed']:
                    st.warning(f"⚠️ **未確認**: {entry['unconfirmed']}")
                st.text_area(
                    "生成結果",
                    value=entry['output'],
                    height=200,
                    key=f"history_output_{idx}",
                    label_visibility="collapsed"
                )
            
            # Code block for clipboard copy
            st.markdown("**📋 コピー用（全選択してCtrl+C）**")
            st.code(entry['output'], language=None)
            st.markdown("---")
else:
    st.info("📝 履歴はまだありません。メモを整理すると、ここに履歴が表示されます。")

# Footer
st.markdown("---")
st.caption("🆓 Google Gemini APIを使用しているため、完全無料で利用できます。")
