import streamlit as st

# 제목
st.title("공동망 불랑국소 TnP 발췌 및 이상치 추정 설정 기준")

# 리스트로 조건 정리
st.subheader("설정 기준:")
st.markdown("""
1. **identifier**가 생성되지 않은 행 삭제
2. **inform_10**과 **inform_28**이 100건 이하인 행 삭제
3. **KPI TnP 조건**:
   - inform_12 < 96
   - inform_18 < 96
   - inform_30 < 96
   - inform_21 > 5000
4. **용량 TnP 조건**:
   - inform_24 >= 70
   - inform_25 >= 70
   - inform_34 >= 600
""")

# 표로 요약할 수도 있음
import pandas as pd

data = {
    "조건명": ["KPI TnP", "KPI TnP", "KPI TnP", "KPI TnP", "용량 TnP", "용량 TnP", "용량 TnP"],
    "필드명": ["inform_12", "inform_18", "inform_30", "inform_21", "inform_24", "inform_25", "inform_34"],
    "조건": ["< 96", "< 96", "< 96", "> 5000", ">= 70", ">= 70", ">= 600"]
}

df = pd.DataFrame(data)


