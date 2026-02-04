import streamlit as st
from openai import OpenAI
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

st.title("🍚 牛めし処『あじわい亭』業務マニュアル検索")
st.write("新人さん向け：マニュアルから検索して回答します。")

# サイドバーに注意書き
with st.sidebar:
    st.write("※架空の牛めし屋のマニュアルです")

# APIキーの設定
try:
    # LangChainでもAPIキーが必要なので、環境変数として設定
    import os
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error("APIキーの設定が必要です。")
    st.stop()

# マニュアルを読み込んで「検索できる形（ベクトル）」にする
# 一度作ったデータベースを使い回すので早くなる！
@st.cache_resource
def create_vector_store():
    # テキストファイルを読み込む
    loader = TextLoader("manual.txt", encoding="utf-8")
    documents = loader.load()

    # 長い文章を「チャンク（塊）」に分割する
    text_splitter = CharacterTextSplitter(
        separator="\n",    # 改行コードで区切る
        chunk_size=500,    # 500文字ごとの塊にする
        chunk_overlap=0    # 重複はなし
    )
    chunks = text_splitter.split_documents(documents)

    # 文章を「数値（ベクトル）」に変換して、データベース(FAISS)に入れる
    embeddings = OpenAIEmbeddings()
    vector_store = FAISS.from_documents(chunks, embeddings)
    
    return vector_store

# データベースの作成（初回のみ実行され、2回目はキャッシュが使われる）
try:
    vector_store = create_vector_store()
    st.success("マニュアルの読み込み完了！質問どうぞ！")
except Exception as e:
    st.error(f"マニュアル読み込みエラー: {e}")
    st.stop()

# ユーザーの質問を受け付ける
prompt = st.chat_input("例：手洗いの手順は？ / 煮込み時間は？")

if prompt:
    # ユーザーの質問を表示
    with st.chat_message("user"):
        st.write(prompt)

    # マニュアルから「関係ありそうな部分」を検索する
    with st.chat_message("assistant"):
        with st.spinner("マニュアルを検索中..."):
            # データベースから、質問に近い文章を3つ探してくる
            docs = vector_store.similarity_search(prompt, k=3)
            
            # 検索で見つかったマニュアルの文章を合体させる
            context = "\n\n".join([doc.page_content for doc in docs])

            #  AIに回答を作らせる
            # 「検索結果(context)」と「質問(prompt)」をセットにして投げる
            system_prompt = f"""
            あなたは『牛めし処 あじわい亭』のベテラン店長です。
            以下の【マニュアルの抜粋】に基づいて、新人スタッフの質問に答えてください。
            
            # ルール
            - マニュアルに書いてあることだけを答えてください。
            - マニュアルにないことは「マニュアルには記載がありません」と答えてください。
            - 優しく、わかりやすく教えてください。

            # 【マニュアルの抜粋】
            {context}
            """

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ]
            )
            
            ai_answer = response.choices[0].message.content
            st.write(ai_answer)
            
            # （デバッグ用）どの部分を参照したか表示する
            with st.expander("参照したマニュアル箇所"):
                st.write(context)