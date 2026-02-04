import streamlit as st
from openai import OpenAI
import random

st.title("🔥 激怒クレーム対応シミュレーター")
st.write("時間帯責任者として、クレームの一次対応を行って下さい。")

# APIキーの設定
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error("APIキーの設定が必要です。.streamlit/secrets.toml を確認してください。")
    st.stop()

# --- 設定：ランダムなクレーム内容のリスト ---
complaint_scenarios = [
    {
        "issue": "ハンバーグの中に髪の毛が混入していた",
        "first_line": "おい！ちょっと店員！このハンバーグ、髪の毛が入ってるんだけど！？ふざけてんの！？"
    },
    {
        "issue": "提供されたステーキが生焼けだった",
        "first_line": "この肉、中が完全に生なんだけど。お腹壊したらどうすんのこれ？"
    },
    {
        "issue": "定食に付くはずの野菜が付いていない",
        "first_line": "ねえ、さっき受け取った定食、野菜がなかったんだけど？どうなってるの？"
    }
]

# --- 1. セッション（記憶）の初期化 ---
if "messages" not in st.session_state:
    selected_scenario = random.choice(complaint_scenarios)
    st.session_state.current_scenario = selected_scenario

    # システムプロンプト
    system_prompt = f"""
    あなたは飲食店に来店した、非常に理不尽で怒っているお客様です。
    以下の設定と手順を厳守してロールプレイをしてください。

    # クレーム内容
    {selected_scenario['issue']}

    # クリア条件（4つの要素）
    1. 【謝罪】（「申し訳ございません」など）
    2. 【原因】（なぜミスが起きたかの説明）
    3. 【改善】（今後どう再発を防ぐか）
    4. 【提案】（作り直し、または返金の具体的な提案）

    # 【最重要】判定の注意点（AIの思考プロセス）
    【重要指令】あなたは「演技をする役者」である前に、「冷静な採点者」です。感情的になる前に、まず入力文に含まれる要素を漏らさずチェックしてください。
    ユーザーの文章は、「申し訳ございません（謝罪）。返金させて頂いても良いでしょうか？（提案）」のように、**複数の要素が連続して書かれることが多い**です。
    あなたは返答を生成する前に、以下の手順で入力を分析してください。

    1. **【全文スキャン】**
       ユーザーの入力文を、**最初の1文字から最後の句点（。）まで**完全に読み込んでください。
       冒頭に謝罪があっても、そこで思考を止めず、**必ず文末まで読んで、他の要素（原因・改善・提案）が含まれていないか探してください。**
    
    2. **【一括採点】**
       1つのメッセージの中に「謝罪」と「原因」の両方が入っていた場合、**必ず両方を「クリア済み」として認定**してください。
       「謝罪はあったが、原因を聞いていない」という反応をするのは、文末まで読んでも本当に原因が書かれていなかった場合のみです。

    # 振る舞いのルール
    - 過去の会話履歴も含めて、まだ出てきていない要素だけを指摘して怒ってください。
    - 4要素がすべて揃うまでは、理不尽に怒り続けてください。
    - 4要素がすべて揃った瞬間、「わかった、そこまで言うなら今回は許すよ」と会話を終了してください。
    - 最初は非常に感情的になり、タメ口や荒い言葉で怒りをぶつけてください。
    - ユーザーがまだ言っていないのに、勝手に「店長を呼ぶな」などの発言をしないでください。
    - ユーザーが明確に「店長」や「責任者」という言葉を使った場合のみ、「お前じゃ話にならない！」「逃げるな！」と激昂してください。
    -「原因」や「改善」は、ユーザーがそれっぽいことを言っていれば（完全な正解でなくても）認めてあげてください。
    """

    st.session_state.messages = [
        {"role": "system", "content": system_prompt},
        {"role": "assistant", "content": selected_scenario['first_line']}
    ]

# --- サイドバーに状況を表示（親切設計） ---
with st.sidebar:
    st.header("現在の設定")
    if "current_scenario" in st.session_state:
        st.info(f"◆トラブル内容:\n{st.session_state.current_scenario['issue']}")
        st.caption("※リセットボタンを押すとシナリオが変わります")

# --- 2. 会話履歴の表示 ---
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

# --- 3. ユーザーの入力受付 ---
prompt = st.chat_input("返信を入力して送信...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("お客様が激怒しています..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=st.session_state.messages
                )
                ai_answer = response.choices[0].message.content
                st.write(ai_answer)
                st.session_state.messages.append({"role": "assistant", "content": ai_answer})
                
                # ★追加：クリア時の演出
                if "許す" in ai_answer or "気をつけて" in ai_answer or "今回は許す" in ai_answer:
                    st.balloons()
                    st.success("🎉 クレーム対応成功！お疲れ様でした！")
                    
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")

# --- リセットボタン ---
if st.button("次の客を対応する（リセット）"):
    st.session_state.clear()
    st.rerun()
