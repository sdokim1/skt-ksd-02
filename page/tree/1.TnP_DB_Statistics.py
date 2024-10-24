import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# Streamlit 설정
st.title("TnP DB and Statistics")

# 엑셀 파일 읽기
file_path = '/workspaces/skt-ksd-02/LG_gong_1018.xlsx'
df = pd.read_excel(file_path, engine='openpyxl')

# 필요한 열만 선택
desired_columns = [
    "eqp_vend_nm", "srvc_net_cd", "eqp_own_bizr_cd", "sido_nm", "sgg_nm", 'eqp_fst_mapp_id', "cell_id", "pci", "frequency",
    "rrc_attempt", "rrc_success", "rrc_s_rate", "rre_attempt", "rre_success", "rre_s_rate", "rre_g_rate",
    "erab_attempt", "erab_success", "erab_s_rate", "cd_setup", "cd", "cd_rate", "cd_rlf", "dl_prb_use_rate",
    "ul_prb_use_rate", "packet_mac_dl_volume", "packet_mac_ul_volume", "endc_attempt", "endc_success", "endc_s_rate",
    "rach_attempt", "rach_success", "rach_s_rate", "pccu"
]
df = df[desired_columns]

# 열 이름 변경 (inform_1, inform_2 형식으로 변경)
df.columns = [f'inform_{i+1}' for i in range(len(df.columns))]

# 특정 열의 값들을 지정한 값으로 변경
df['inform_1'] = df['inform_1'].replace({
    "삼성전자(주)": "SS",
    "에릭슨엘지": "EL"
})
df['inform_4'] = df['inform_4'].replace({
    "전북": "JB",
    "전남": "JN",
    "광주": "KJ",
    "제주": "JJ"
})

# inform_5의 각 고유 값을 A, B, C... 순으로 변경
unique_sgg_nm = df['inform_5'].unique()
alphabet_mapping = {name: chr(65 + i) for i, name in enumerate(unique_sgg_nm)}
df['inform_5'] = df['inform_5'].map(alphabet_mapping)

# inform_9의 각 고유 값을 A, B, C 순으로 변경
unique_frequency = df['inform_9'].unique()
frequency_mapping = {name: chr(65 + i) for i, name in enumerate(unique_frequency)}
df['inform_9'] = df['inform_9'].map(frequency_mapping)

# inform_6, inform_7, inform_8을 "_"로 연결하여 identifier 열 추가 
df['identifier'] = df['inform_6'].astype(str) + '_' + df['inform_7'].astype(str) + '_' + df['inform_8'].astype(str)

# identifier가 생성되지 않은 행 삭제
df = df.dropna(subset=['identifier'])

# inform_10과 inform_28이 100건 이하인 행 삭제
df = df[(df['inform_10'] > 100) & (df['inform_28'] > 100)]

# "구분" 열 생성 및 조건에 따라 값 할당
df['구분'] = ''
condition_kpi = (
    (df['inform_12'] < 96) |
    (df['inform_18'] < 96) |
    (df['inform_30'] < 96) |
    (df['inform_21'] > 5000)
)
df.loc[condition_kpi, '구분'] = 'KPI'

condition_capacity = (
    (df['inform_24'] >= 70) |
    (df['inform_25'] >= 70) |
    (df['inform_34'] >= 600)
)
df.loc[condition_capacity, '구분'] = df['구분'] + df['구분'].apply(lambda x: '; ' if x != '' else '') + '용량'

# 2개 열로 레이아웃 설정
col1, col2 = st.columns(2)

# 공동망 TnP 추출 테이블 왼쪽 열에 출력
with col1:
    st.subheader("공동망 TnP 추출 데이터")
    st.dataframe(df)

# 항목별 데이터 분포 오른쪽 열에 시각화
with col2:
    st.subheader("TnP Statistics")
    fig, ax = plt.subplots(figsize=(10, 5))
    sgg_nm_counts = df['inform_5'].value_counts()
    sgg_nm_counts.plot(kind='bar', ax=ax, color='coral')
    ax.set_title("SGG Name Count")
    ax.set_xlabel("SGG Name")
    ax.set_ylabel("Count")
    st.pyplot(fig)
