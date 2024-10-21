import pandas as pd
import streamlit as st

# 엑셀 파일 읽기
file_path = '/workspaces/skt-ksd-02/LG_gong_1018.xlsx'
try:
    df = pd.read_excel(file_path, engine='openpyxl')
except FileNotFoundError:
    st.error('파일을 찾을 수 없습니다. 올바른 파일 경로를 확인하세요.')
    st.stop()

# 필요한 열만 선택
desired_columns = [
    "eqp_vend_nm", "srvc_net_cd", "eqp_own_bizr_cd", "sido_nm", "sgg_nm", "cell_id", "pci", "frequency",
    "rrc_attempt", "rrc_success", "rrc_s_rate", "rre_attempt", "rre_success", "rre_s_rate", "rre_g_rate",
    "erab_attempt", "erab_success", "erab_s_rate", "cd_setup", "cd", "cd_rate", "cd_rlf", "dl_prb_use_rate",
    "ul_prb_use_rate", "packet_mac_dl_volume", "packet_mac_ul_volume", "endc_attempt", "endc_success", "endc_s_rate",
    "rach_attempt", "rach_success", "rach_s_rate", "pccu"
]
df = df[desired_columns]

# 특정 열의 값들을 지정한 값으로 변경
df['eqp_vend_nm'] = df['eqp_vend_nm'].replace({
    "삼성전자(주)": "SS",
    "에릭슨엘지": "EL"
})

df['sido_nm'] = df['sido_nm'].replace({
    "전북": "JB",
    "전남": "JN",
    "광주": "KJ",
    "제주": "JJ"
})

# sgg_nm의 각 고유 값을 A, B, C... 순으로 변경
unique_sgg_nm = df['sgg_nm'].unique()
alphabet_mapping = {name: chr(65 + i) for i, name in enumerate(unique_sgg_nm)}
df['sgg_nm'] = df['sgg_nm'].map(alphabet_mapping)

# frequency의 각 고유 값을 A, B, C 순으로 변경
unique_frequency = df['frequency'].unique()
frequency_mapping = {name: chr(65 + i) for i, name in enumerate(unique_frequency)}
df['frequency'] = df['frequency'].map(frequency_mapping)

# cell_id와 pci를 "_"로 연결하여 identifier 열 추가
df['identifier'] = df['cell_id'].astype(str) + '_' + df['pci'].astype(str)

# identifier가 생성되지 않은 행 삭제
df = df.dropna(subset=['identifier'])

# rrc_attempt와 endc_attempt가 100건 이하인 행 삭제
df = df[(df['rrc_attempt'] > 100) & (df['endc_attempt'] > 100)]

# "구분" 열 생성 및 조건에 따라 값 할당
df['구분'] = ''
condition_kpi = (
    (df['rrc_s_rate'] < 96) |
    (df['erab_s_rate'] < 96) |
    (df['endc_s_rate'] < 96) |
    (df['cd'] > 5000)
)
df.loc[condition_kpi, '구분'] = 'KPI'

condition_capacity = (
    (df['dl_prb_use_rate'] >= 70) |
    (df['ul_prb_use_rate'] >= 70) |
    (df['pccu'] >= 600)
)
df.loc[condition_capacity, '구분'] = df['구분'] + df['구분'].apply(lambda x: '; ' if x != '' else '') + '용량'

# 구분 열이 공백인 행 제외
df = df[df['구분'] != '']

# 조건에 맞는 값들을 빨간색으로 표시하는 스타일링 함수 정의
def highlight_cells(val, column_name):
    if column_name in ['rrc_s_rate', 'erab_s_rate', 'endc_s_rate'] and val < 96:
        return 'color: red'
    elif column_name == 'cd' and val > 5000:
        return 'color: red'
    elif column_name in ['dl_prb_use_rate', 'ul_prb_use_rate'] and val >= 70:
        return 'color: red'
    elif column_name == 'pccu' and val >= 600:
        return 'color: red'
    return ''

# Streamlit 앱 설정
st.title('LGU+ 공동망 데이터 분석')

# 스타일링 적용
styled_df = df.style.map(lambda val: highlight_cells(val, 'rrc_s_rate'), subset=['rrc_s_rate'])
styled_df = styled_df.map(lambda val: highlight_cells(val, 'erab_s_rate'), subset=['erab_s_rate'])
styled_df = styled_df.map(lambda val: highlight_cells(val, 'endc_s_rate'), subset=['endc_s_rate'])
styled_df = styled_df.map(lambda val: highlight_cells(val, 'cd'), subset=['cd'])
styled_df = styled_df.map(lambda val: highlight_cells(val, 'dl_prb_use_rate'), subset=['dl_prb_use_rate'])
styled_df = styled_df.map(lambda val: highlight_cells(val, 'ul_prb_use_rate'), subset=['ul_prb_use_rate'])
styled_df = styled_df.map(lambda val: highlight_cells(val, 'pccu'), subset=['pccu'])

# 최적화된 데이터프레임 출력 (높이, 너비 설정)
st.write(styled_df)

# 데이터 통계 출력
st.subheader('기본 통계')
st.write(df.describe())

# eqp_vend_nm, sido_nm, sgg_nm 각각의 count를 bar 형식으로 시각화
st.subheader('eqp_vend_nm, sido_nm, sgg_nm Count Plot')

# eqp_vend_nm count plot
eqp_vend_counts = df['eqp_vend_nm'].value_counts()
st.bar_chart(eqp_vend_counts)

# sido_nm count plot
sido_counts = df['sido_nm'].value_counts()
st.bar_chart(sido_counts)

# sgg_nm count plot
sgg_counts = df['sgg_nm'].value_counts()
st.bar_chart(sgg_counts)
