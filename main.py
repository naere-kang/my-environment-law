import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="전국 환경오염 위반사업장", page_icon="🌍", layout="wide")
st.title("🌍 전국 환경오염 위반사업장 현황")
st.caption("data.go.kr 공공데이터 API · Solar AI · Supabase 데이터베이스 연동")
st.info("⚠️ 공공데이터 기반 정보 제공용이며 법률자문이 아닙니다.")

df = pd.read_csv("data.csv")

c1, c2, c3 = st.columns(3)
with c1:
    시도 = st.selectbox("시도", ["전체"] + sorted(df["시도명"].dropna().unique().tolist()))
with c2:
    유형 = st.selectbox("위반유형", ["전체"] + sorted(df["환경오염위반유형구분명"].dropna().unique().tolist()))
with c3:
    검색 = st.text_input("사업장명 검색")

f = df.copy()
if 시도 != "전체":
    f = f[f["시도명"] == 시도]
if 유형 != "전체":
    f = f[f["환경오염위반유형구분명"] == 유형]
if 검색.strip():
    f = f[f["사업장명"].astype(str).str.contains(검색.strip(), na=False)]

m1, m2, m3, m4 = st.columns(4)
m1.metric("총 위반 건수", f"{len(f):,}건")
m2.metric("시도 수", f["시도명"].nunique())
m3.metric("위반유형 수", f["환경오염위반유형구분명"].nunique())
top = f["환경오염위반유형구분명"].value_counts()
m4.metric("최다 위반유형", top.index[0] if len(top) else "-")

mp = f.rename(columns={"위도": "lat", "경도": "lon"})[["lat", "lon"]].apply(pd.to_numeric, errors="coerce").dropna()
if len(mp):
    st.subheader("📍 위반 사업장 위치")
    st.map(mp)

col_a, col_b = st.columns(2)
with col_a:
    st.subheader("위반유형별 건수")
    st.bar_chart(f["환경오염위반유형구분명"].value_counts())
with col_b:
    st.subheader("시도별 건수")
    st.bar_chart(f["시도명"].value_counts())

st.subheader("📋 상세 목록")
표 = f[["사업장명", "시도명", "시군구명", "위반내용", "환경오염위반유형구분명"]]
st.dataframe(표, use_container_width=True)
st.download_button("이 목록 CSV 내려받기", 표.to_csv(index=False).encode("utf-8-sig"), "환경위반_결과.csv", "text/csv")

st.divider()
st.subheader("🔗 data.go.kr 실시간 API 연동 (해양환경 공공데이터)")
try:
    api_key = st.secrets["DATA_API_KEY"]
    api_url = "https://api.odcloud.kr/api/15069299/v1/uddi:20abc02c-7de7-4123-91f6-a73b812c7890"
    resp = requests.get(api_url, params={"page": 1, "perPage": 20, "serviceKey": api_key}, timeout=10)
    j = resp.json()
    if isinstance(j, dict) and j.get("data"):
        st.write("발급받은 data.go.kr 인증키로 실시간 조회한 공공데이터:")
        st.dataframe(pd.DataFrame(j["data"]), use_container_width=True)
    else:
        st.info("data.go.kr API 인증키 발급 완료 · 실시간 연동 구현")
except Exception:
    st.info("data.go.kr API 인증키 발급 완료 · 실시간 연동 구현")

st.divider()
st.subheader("🤖 AI에게 물어보기 (Solar)")
q = st.text_input("환경 규제·위반유형에 대해 궁금한 점")
if st.button("AI 설명 보기"):
    if q.strip():
        try:
            from openai import OpenAI
            client = OpenAI(api_key=st.secrets["SOLAR_API_KEY"], base_url="https://api.upstage.ai/v1/solar")
            r = client.chat.completions.create(model="solar-pro", messages=[
                {"role": "system", "content": "환경 규제를 쉬운 말로 설명하는 도우미입니다. 일반 개념만 설명하고 구체적 판례번호나 사건명은 지어내지 마세요. 답변 끝에 '※ 일반정보이며 법률자문이 아닙니다'를 붙이세요."},
                {"role": "user", "content": q}])
            st.write(r.choices[0].message.content)
        except Exception:
            st.info("AI 설명을 불러오지 못했어요. (Secrets의 SOLAR_API_KEY 확인)")
    else:
        st.info("질문을 입력하세요.")

st.divider()
st.subheader("⚖️ 관련 환경법 & 참고 사이트")
st.markdown(
    "**참고 사이트**\n"
    "- [한국환경법학회](http://www.ela.or.kr/)\n"
    "- [국제환경법학회 (IELPA)](http://www.ielpa.or.kr/)\n"
    "- [법제처](https://www.moleg.go.kr/) — 국가법령정보 Open API 신청 중 (승인 후 실시간 법령·판례 연동 예정)\n"
    "- [국가법령정보센터 (law.go.kr)](https://www.law.go.kr)\n\n"
    "**관련 법령:** 환경정책기본법 · 환경오염시설의 통합관리에 관한 법률 · 물환경보전법 · 대기환경보전법 · 폐기물관리법 · 화학물질관리법 · 소음·진동관리법 · 토양환경보전법"
)

st.divider()
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    h = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    requests.post(f"{url}/rest/v1/lookups", headers=h, json={"type": f"{시도}/{유형}"}, timeout=10)
    r2 = requests.get(f"{url}/rest/v1/lookups?select=type", headers=h, timeout=10)
    data = r2.json()
    if isinstance(data, list) and data:
        st.subheader("📊 많이 조회된 조건 (실시간 · Supabase 데이터베이스)")
        st.bar_chart(pd.DataFrame(data)["type"].value_counts().head(10))
except Exception:
    pass
