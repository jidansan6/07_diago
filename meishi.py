import streamlit as st
import base64, json, os
from dotenv import load_dotenv
from openai import AzureOpenAI, OpenAI

# Load environment variables from .env file
load_dotenv()

# ———————— OpenAI クライアント設定 ————————
azure_client = AzureOpenAI(
    api_key=os.getenv("AZURE_API_KEY"),
    api_version=os.getenv("AZURE_API_VERSION", "2024-12-01-preview"),
    azure_endpoint=os.getenv("AZURE_ENDPOINT")
)
openai_client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

MODEL_DEPLOYMENT = os.getenv("MODEL_DEPLOYMENT", "tech0-gpt4o")

# ———————— ユーティリティ関数 ————————
def encode_image_to_base64(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode('utf-8')

def ocr_image(b64: str) -> str:
    response = azure_client.chat.completions.create(
        model=MODEL_DEPLOYMENT,
        temperature=0.0,
        messages=[
            {"role": "system", "content": (
                "You are an Optical Character Recognition (OCR) machine. "
                "Extract all text from the image and return only the raw text."
            )},
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
            ]}
        ]
    )
    return response.choices[0].message.content

def extract_name_company(text: str) -> dict:
    response = azure_client.chat.completions.create(
        model=MODEL_DEPLOYMENT,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": (
                "あなたは JSON モードで応答するアシスタントです。"
                "テキストから氏名と会社名を抽出し、{'name', 'company'} の JSON を返してください。"
            )},
            {"role": "user", "content": text}
        ]
    )
    return response.choices[0].message.content

def web_search(corp: str) -> str:
    resp = openai_client.responses.create(
        model=os.getenv("WEB_SEARCH_MODEL", "gpt-4.1"),
        tools=[{
            "type": "web_search_preview",
            "search_context_size": "high",
            "user_location": {
                "type":"approximate",
                "country": os.getenv("SEARCH_COUNTRY", "JP"),
                "city": os.getenv("SEARCH_CITY", "Tokyo"),
                "region": os.getenv("SEARCH_REGION", "Tokyo")
            }
        }],
        input=f"{corp} の会社概要と直近のプレスリリースを教えて。フレンドリーな口調で返事をして。また、その会社の人が目の前にいます。より親睦が深まるように芸人のごとく取り計らって"
    )
    return resp.output_text

# ———————— Streamlit UI ————————
st.set_page_config(page_title="懇親会お手伝いAI「エゴサ君」")

# タブを作成
tab_instructions, tab_app = st.tabs(["使い方", "エゴサ君"])

# 使い方タブ
with tab_instructions:
    st.header("使い方")
    st.markdown(
        """
        1. "エゴサ君" タブに切り替えてください。
        2. 名刺画像をアップロードします。
        3. OCRで氏名・会社名を自動で抽出します。
        4. 抽出結果をもとに会社情報をWeb検索し表示します。

        **ポイント**
        - JPG/PNG形式の名刺画像をスマホで撮影もしくはアップロードします。
        - 人名検索機能は現在実装中です。お楽しみに。
        - 検索結果の真偽はぜひ名刺交換のお相手にお伺いください。
        - あくまでAIによる検索結果のため、出力結果が事実と異なる場合があります。
        """
    )

# アプリ本体タブ
with tab_app:
    st.title("懇親会お手伝いAI「エゴサ君」")
    st.write("名刺を貰ったら相手の会社を簡単に調べられますよ！人名検索は実装中…")
    st.write("---")

    uploaded_file = st.file_uploader(
        "名刺画像をアップロードしてください！", type=["png", "jpg", "jpeg"]
    )
    if uploaded_file:
        image_bytes = uploaded_file.read()
        st.image(image_bytes, caption="アップロードされた名刺画像", use_column_width=True)
        b64 = encode_image_to_base64(image_bytes)

        with st.spinner("画像から文字起こし中... ⏳"):
            ocr_text = ocr_image(b64)

        with st.spinner("氏名・会社名を抽出中... ⏳"):
            info = json.loads(extract_name_company(ocr_text))
            name = info.get("name")
            company = info.get("company")

        if company and name:
            st.success(f"{company}の{name}さんと名刺交換したんですね！📇")

            with st.spinner("ウェブ検索中...ちょっと待ってね 🌐"):
                result = web_search(company)
            st.subheader("検索結果")
            st.write(result)
        else:
            st.error(
                "氏名または会社名が抽出できませんでした。別の画像を試してください。"
            )
    
    st.markdown("---")
    st.markdown("### ↓このアプリを1時間で作れるようになるには？↓")
    banner_url = "https://github.com/jidansan6/07_diago/blob/b179dbd6478fe3545fe52978d8febf5708e821d7/banner.png"
    link_url ="https://liff.line.me/1657315760-N459xXV3/landing?follow=@143yqdhm&lp=3TE72t&liff_id=1657315760-N459xXV3&_gl=1*awj8rr*_gcl_au*MjA4NjQwNzE4NS4xNzQ3MTEwMDIz*_ga*MTMzMjExMTgyNy4xNzQ3MTEwMDIz*_ga_0PV16Y9CZG*czE3NDcxMTAwMjIkbzEkZzEkdDE3NDcxMTAwMzIkajUwJGwwJGgw"
    st.markdown(
        f"<a href='{link_url}' target='_blank'><img src='{banner_url}' alt='Learn Streamlit in 1 hour' style='width:100%;'></a>",
        unsafe_allow_html=True
    )

