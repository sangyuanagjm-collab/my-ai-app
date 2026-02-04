import streamlit as st
from openai import OpenAI
import random

# =============================
# アプリ設定
# =============================
st.set_page_config(page_title="激怒クレーム対応シミュレーター", layout="centered")
st.title("🔥 激怒クレーム対応シミュレーター")
st.caption("新人スタッフ向け｜理不尽クレーム一次対応トレーニング")

# =============================
# OpenAI クライアント
# =============================
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("OPENAI_API_KEY が設定されていません")
    st.stop()

# =============================
# シナリオ
# =============================
SCENARIOS = [
    {
        "issue": "ハンバーグに髪の毛が混入していた",
        "first_line": "おい！このハンバーグに髪の毛が入ってるんだけど！？どういう管理してるんだ！"
    },
    {
        "issue": "ステーキが生焼けだった",
        "first_line": "中が完全に生なんだけど？これで金取る気？"
    },
    {
        "issue": "定食に付くはずの野菜がなかった",
        "first_line": "野菜が付いてないんだけど？おかしくない？"
    }
]

# =============================
# 判定ロジック（AIに任せない）
# =============================
def check_elements(text: str):
    return {
        "謝罪": any(w in text for w in ["申し訳", "すみません"]),
        "原因": any(w in text for w in ["原因", "不注意", "確認不足"]),
        "改善": any(w in text for w in ["今後", "再発防止", "改善"]),
        "提案": any(w in text for w in ["作り直し", "返金", "お取り替え"]),
    }

# =============================
# セッション初期化
# =============================
if "messages" not in st.session_state:
    scenario = random.choice(SCENARIOS)

    st.session_state.scenario = scenario
    st.session_state.messages = []
    st.session_state.cleared = {
        "謝罪": False,
        "原因": False,
        "改善": False,
        "提案": False
    }
    st.session_state.turns = 0

    system_prompt = f"""
あなたは飲食店でクレームを言う、非常に怒っている客です。
以下の条件でロールプレイをしてください。

【クレーム内容】
{scenario["issue"]}

【ルール】
- まだ満たされていない要素についてのみ怒ってください
- 4要素すべて揃ったら
「わかった、そこまで言うなら今回は許すよ」
と言って会話を終了してください
- 口調は終始高圧的で理不尽
"""

    st.session_state.messages.append(
        {"role": "assistant", "content": scenario["first_line"]}
    )
    st.session_state.system_prompt = system_prompt

# =============================
# サイドバー（進捗表示）
# =============================
with st.sidebar:
    st.subheader("対応チェック")
    for k, v in st.session_state.cleared.items():
        st.write(f"{k}：{'✅' if v else '❌'}")

    st.divider()
    st.caption(f"対応ターン数：{st.session_state.turns}")

# =============================
# 会話表示
# =============================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# =============================
# 入力処理
# =============================
user_input = st.chat_input("あなたの対応を入力してください")

if user_input:
    st.session_state.turns += 1

    # ユーザー入力表示
    with st.chat_message("user"):
        st.write(user_input)

    st.session_state.messages.append(
        {"role": "user", "content": user_input}
    )

    # 判定更新
    result = check_elements(user_input)
    for k in st.session_state.cleared:
        if result[k]:
            st.session_state.cleared[k] = True

    # 未クリア要素をAIに渡す
    remaining = [k for k, v in st.session_state.cleared.items() if not v]

    judge_prompt = f"""
未達成の要素は以下です：
{", ".join(remaining) if remaining else "なし"}

この状況に合ったクレーム客のセリフを1つ返してください。
"""

    with st.chat_message("assistant"):
        with st.spinner("お客様が激怒しています…"):
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": st.session_state.system_prompt},
                    {"role": "user", "content": judge_prompt}
                ]
            )

            reply = response.choices[0].message.content
            st.write(reply)

    st.session_state.messages.append(
        {"role": "assistant", "content": reply}
    )

    # クリア演出
    if all(st.session_state.cleared.values()):
        st.balloons()
        st.success("🎉 クレーム対応成功！")

# =============================
# リセット
# =============================
if st.button("次の客を対応する"):
    st.session_state.clear()
    st.rerun()
