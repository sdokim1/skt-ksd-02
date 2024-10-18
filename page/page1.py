import pandas as pd
import streamlit as st

# 엑셀 파일 읽기
file_path = 'LG_gong_1018.xlsx'
try:
    df = pd.read_excel(file_path)
except FileNotFoundError:
    st.error('파일을 찾을 수 없습니다. 올바른 파일 경로를 확인하세요.')
    st.stop()
else:
    st.error('파일을 찾을 수 없습니다. 올바른 파일 경로를 확인하세요.')
    st.stop()

# 필요한 열만 선택
desired_columns = [
    "eqp_vend_nm", "eqp_nm", "srvc_net_cd", "eqp_own_bizr_cd", "sido_nm", "sgg_nm", "cell_id", "pci", "frequency",
    "rrc_attempt", "rrc_success", "rrc_s_rate", "rre_attempt", "rre_success", "rre_s_rate", "rre_g_rate",
    "erab_attempt", "erab_success", "erab_s_rate", "cd_setup", "cd", "cd_rate", "cd_rlf", "dl_prb_use_rate",
    "ul_prb_use_rate", "packet_mac_dl_volume", "packet_mac_ul_volume", "endc_attempt", "endc_success", "endc_s_rate",
    "rach_attempt", "rach_success", "rach_s_rate", "pccu"
]
df = df[desired_columns]

# cell_id와 pci를 "_"로 연결하여 첫 번째 열에 추가
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
df.loc[condition_capacity, '구분'] = df['구분'] + ('; ' if df['구분'] != '' else '') + '용량'

# 조건에 맞는 값들을 빨간색으로 표시하는 스타일링 함수 정의
def highlight_cells(val, column_name):
    if column_name == 'rrc_s_rate' and val < 96:
        return 'color: red'
    elif column_name == 'erab_s_rate' and val < 96:
        return 'color: red'
    elif column_name == 'endc_s_rate' and val < 96:
        return 'color: red'
    elif column_name == 'cd' and val > 5000:
        return 'color: red'
    elif column_name == 'dl_prb_use_rate' and val >= 70:
        return 'color: red'
    elif column_name == 'ul_prb_use_rate' and val >= 70:
        return 'color: red'
    elif column_name == 'pccu' and val >= 600:
        return 'color: red'
    return ''

# Streamlit 앱 설정
st.title('LG 공공 데이터 분석')

# 데이터프레임 스타일링 적용 후 출력
styled_df = df.style.applymap(lambda val: highlight_cells(val, column_name=df.columns[df.columns.get_loc(val.name)]), subset=[
    'rrc_s_rate', 'erab_s_rate', 'endc_s_rate', 'cd', 'dl_prb_use_rate', 'ul_prb_use_rate', 'pccu'
])

st.dataframe(styled_df)
