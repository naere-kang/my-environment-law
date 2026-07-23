
import streamlit as st
import pandas as pd

st.set_page_config(page_title="전국 환경오염 위반사업장", page_icon="🌍", layout="wide")
st.title("🌍 전국 환경오염 위반사업장 현황")
st.caption("공공데이터 기반 · 지역·위반유형별로 보기")
st.info("⚠️ 공공데이터 기반 정보 제공용이며 법률자문이 아닙니다.")

df = pd.read_csv("data.csv")

c1, c2 = st.columns(2)
with c1:
    시도 = st.selectbox("시도", ["전체"] + sorted(df["시도명"].dropna().unique().tolist()))
with c2:
    유형 = st.selectbox("위반유형", ["전체"] + sorted(df["환경오염위반유형구분명"].dropna().unique().tolist()))

f = df.copy()
if 시도 != "전체":
    f = f[f["시도명"] == 시도]
if 유형 != "전체":
    f = f[f["환경오염위반유형구분명"] == 유형]

st.subheader(f"총 {len(f)}건")

m = f.rename(columns={"위도": "lat", "경도": "lon"})[["lat", "lon"]].apply(pd.to_numeric, errors="coerce").dropna()
if len(m):
    st.map(m)

st.subheader("위반유형별 건수")
st.bar_chart(f["환경오염위반유형구분명"].value_counts())
st.subheader("시도별 건수")
st.bar_chart(f["시도명"].value_counts())

st.subheader("상세 목록")
st.dataframe(f[["사업장명", "시도명", "시군구명", "위반내용", "환경오염위반유형구분명"]], use_container_width=True)
