import streamlit as st
import pandas as pd
import numpy as np

# 1. 페이지 대시보드 기본 설정
st.set_page_config(
    page_title="연도별·연령별 인구 구조 분석 대시보드",
    page_icon="👥",
    layout="wide"
)

# 2. 데이터 로드 및 정제 함수 (@st.cache_data 적용)
@st.cache_data
def load_and_clean_pop_data(file_path='pop_data.csv'):
    # CSV 파일 읽기
    df = pd.read_csv(file_path)

    # 컬럼명 정리
    df.columns = df.columns.str.strip()

    # 쉼표(,) 제거 및 수치형 데이터 변환
    for col in df.columns:
        if col != '연도':
            df[col] = df[col].astype(str).str.replace(',', '').str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce')
        else:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # 이상치 처리: 0 미만의 비현실적인 값 제거
    num_cols = df.select_dtypes(include=['number']).columns
    for col in num_cols:
        df.loc[df[col] < 0, col] = np.nan

    # 결측치 정제: 중앙값 보정
    for col in num_cols:
        if df[col].isna().sum() > 0:
            df[col] = df[col].fillna(df[col].median())

    return df

# 3. 대시보드 메인 헤더
st.title("👥 연도별·연령별 인구 구조 분석 대시보드")
st.markdown("`pop_data.csv` 데이터를 자동으로 정제하여 2010년~2024년 연령대별 인구 변동 및 고령화 추이를 분석합니다.")
st.divider()

# 데이터 로드
try:
    df_pop = load_and_clean_pop_data('pop_data.csv')
    st.success("데이터 로드 완료!")
except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

# 4. 사이드바 필터링 옵션
st.sidebar.header("🔍 데이터 탐색 옵션")

min_year = int(df_pop['연도'].min())
max_year = int(df_pop['연도'].max())
selected_years = st.sidebar.slider("분석 연도 범위 선택", min_year, max_year, (min_year, max_year))

# 데이터 필터링
df_filtered = df_pop[(df_pop['연도'] >= selected_years[0]) & (df_pop['연도'] <= selected_years[1])].copy()

# 연령대 컬럼 선택
age_columns = [col for col in df_filtered.columns if col not in ['연도', '총인구']]
selected_age_cols = st.sidebar.multiselect("분석할 연령대 선택", age_columns, default=age_columns)

# 5. st.tabs를 이용한 3가지 반응형 탭 구성
tab1, tab2, tab3 = st.tabs([
    "📋 정제된 데이터셋", 
    "📈 주요 지표 및 요약 통계량", 
    "📊 인구 변동 트렌드 시각화"
])

# 탭 1: 정제 완료된 데이터 테이블
with tab1:
    st.subheader("📋 정제 완료된 인구 데이터")
    st.markdown(f"**{selected_years[0]}년~{selected_years[1]}년** 기준 정제 데이터입니다.")
    st.dataframe(df_filtered[['연도'] + selected_age_cols + ['총인구']], use_container_width=True)

# 탭 2: 주요 요약 통계량 및 핵심 지표 카드
with tab2:
    st.subheader("💡 인구 구조 핵심 변동 지표 (2010 vs 2024)")

    col1, col2, col3, col4 = st.columns(4)
    
    pop_2010 = df_pop[df_pop['연도'] == min_year].iloc[0]
    pop_latest = df_pop[df_pop['연도'] == max_year].iloc[0]

    youth_change = pop_latest['0-19세 (유소년/청소년)'] - pop_2010['0-19세 (유소년/청소년)']
    senior_change = pop_latest['60세 이상 (고령층)'] - pop_2010['60세 이상 (고령층)']
    total_change = pop_latest['총인구'] - pop_2010['총인구']
    senior_pct = (pop_latest['60세 이상 (고령층)'] / pop_latest['총인구']) * 100

    col1.metric("총인구 (2024년)", f"{pop_latest['총인구']:,} 명", f"{total_change:+,} 명")
    col2.metric("유소년/청소년 변화량", f"{pop_latest['0-19세 (유소년/청소년)']:,} 명", f"{youth_change:+,} 명")
    col3.metric("고령층 변화량", f"{pop_latest['60세 이상 (고령층)']:,} 명", f"{senior_change:+,} 명")
    col4.metric("고령층 비중 (2024년)", f"{senior_pct:.1f} %")

    st.divider()

    st.subheader("📊 기술통계량 (`describe()`)")
    st.dataframe(df_filtered.describe().round(2), use_container_width=True)

# 탭 3: 연도별/연령대별 그래프 시각화
with tab3:
    st.subheader("📊 연도별 연령대 인구 변화 추이")

    # 연령대별 추이 (꺾은선 차트)
    st.markdown("##### 📈 연령대별 인구수 변화 추이 (꺾은선 차트)")
    chart_data = df_filtered.set_index('연도')[selected_age_cols]
    st.line_chart(chart_data)

    st.divider()

    # 연도별 인구 구조 (막대 차트)
    st.markdown("##### 📊 연도별 연령 그룹 인구 비교 (막대 차트)")
    st.bar_chart(chart_data)
