import streamlit as st
from openai import OpenAI

st.title("🤖 記憶するAIチャットボット")

# APIキーの設定（※注意：本当はここには書きませんが、今は練習なのでOK）
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# 1. 「会話の履歴」を保存する場所を作る（ここが記憶の正体！）
# もし「messages」という箱がまだなかったら、新しく作る
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "あなたは優秀なアシスタントです。"}
    ]

# 2. 過去の会話を画面に表示する（これがないと履歴が見えない）
for msg in st.session_state.messages:
    # システム設定（裏設定）は画面に出さない
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

# 3. ユーザーの入力を受け付ける（チャットっぽい入力欄）
prompt = st.chat_input("何か話しかけてみて！")

if prompt:
    # ユーザーの入力を記憶に追加する
    st.session_state.messages.append({"role": "user", "content": prompt})
    # ユーザーの入力を画面に表示する
    with st.chat_message("user"):
        st.write(prompt)

    # AIに答えを考えてもらう
    with st.chat_message("assistant"):
        with st.spinner("考え中..."):
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                # ★ここで「過去の履歴すべて」をAIに渡す！だから文脈を理解できる
                messages=st.session_state.messages
            )
            ai_answer = response.choices[0].message.content
            st.write(ai_answer)
    
    # AIの答えも記憶に追加する
    st.session_state.messages.append({"role": "assistant", "content": ai_answer})