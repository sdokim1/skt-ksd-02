import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# Streamlit 설정
st.title("LGU+ 공동망 불량국소 추출")

# 엑셀 파일 읽기
file_path = '/workspaces/skt-ksd-02/LG_gong_1018.xlsx'
df = pd.read_excel(file_path, engine='openpyxl')

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

# 공동망 TnP추출 테이블 출력
st.subheader("공동망 TnP 추출 데이터")
st.dataframe(df)

# eqp_vend_nm, sido_nm, sgg_nm 항목별로 count해서 막대 그래프로 시각화
st.subheader("항목별 데이터 분포")
fig, ax = plt.subplots(3, 1, figsize=(10, 15))

# eqp_vend_nm count plot
eqp_vend_nm_counts = df['eqp_vend_nm'].value_counts()
eqp_vend_nm_counts.plot(kind='bar', ax=ax[0], color='skyblue')
ax[0].set_title("Equipment Vendor Name Count")
ax[0].set_xlabel("Vendor Name")
ax[0].set_ylabel("Count")

# sido_nm count plot
sido_nm_counts = df['sido_nm'].value_counts()
sido_nm_counts.plot(kind='bar', ax=ax[1], color='lightgreen')
ax[1].set_title("Sido Name Count")
ax[1].set_xlabel("Sido Name")
ax[1].set_ylabel("Count")

# sgg_nm count plot
sgg_nm_counts = df['sgg_nm'].value_counts()
sgg_nm_counts.plot(kind='bar', ax=ax[2], color='coral')
ax[2].set_title("SGG Name Count")
ax[2].set_xlabel("SGG Name")
ax[2].set_ylabel("Count")

st.pyplot(fig)

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

# rrc_attempt를 5000 단위로 그룹화하여 Rate로 끝나는 항목들은 표준편차 방법, 나머지는 IQR 방법으로 이상치 분석 수행 후 정리
df['rrc_attempt_bin'] = pd.cut(df['rrc_attempt'], bins=np.arange(0, df['rrc_attempt'].max() + 5000, 5000), right=False, include_lowest=True)

# 그룹화된 결과를 저장할 리스트
grouped_outliers_summary = []

# Rate로 끝나는 항목 분류
rate_columns = [col for col in desired_columns if col.endswith('rate')]
non_rate_columns = [col for col in desired_columns if col not in rate_columns]

# 각 그룹에 대해 이상치 분석 수행
for name, group in df.groupby('rrc_attempt_bin', observed=True):
    group_summary = {'rrc_attempt_bin': name}

    # Rate로 끝나는 항목에 대해 표준편차를 기준으로 이상치 여부 계산
    for col in rate_columns:
        if group[col].dtype in ['int64', 'float64']:
            mean = group[col].mean()
            std_dev = group[col].std()
            lower_bound = mean - 3 * std_dev
            upper_bound = mean + 3 * std_dev
            num_outliers = group[(group[col] < lower_bound) | (group[col] > upper_bound)].shape[0]
            group_summary[col] = num_outliers

    # Non-rate 항목에 대해 IQR 방법으로 이상치 여부 계산
    for col in non_rate_columns:
        if group[col].dtype in ['int64', 'float64']:
            Q1 = group[col].quantile(0.25)
            Q3 = group[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            num_outliers = group[(group[col] < lower_bound) | (group[col] > upper_bound)].shape[0]
            group_summary[col] = num_outliers

    grouped_outliers_summary.append(group_summary)

# 결과 요약을 위한 데이터프레임 생성
grouped_outliers_summary_df = pd.DataFrame(grouped_outliers_summary)

# Streamlit에서 그룹화된 이상치 분석 결과 출력
st.subheader("그룹별 이상치 분석 결과")
st.dataframe(grouped_outliers_summary_df)

# 구분자 별 이상치 분석 수행 및 '이상치분류' 열 추가
classification_outliers_summary = []

for name, group in df.groupby('구분'):
    group_summary = group.copy()
    group_summary['이상치분류'] = '정상'

    for col in rate_columns:
        if group[col].dtype in ['int64', 'float64']:
            mean = group[col].mean()
            std_dev = group[col].std()
            lower_bound = mean - 3 * std_dev
            upper_bound = mean + 3 * std_dev
            group_summary.loc[(group[col] < lower_bound) | (group[col] > upper_bound), '이상치분류'] = '비정상'

    for col in non_rate_columns:
        if group[col].dtype in ['int64', 'float64']:
            Q1 = group[col].quantile(0.25)
            Q3 = group[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            group_summary.loc[(group[col] < lower_bound) | (group[col] > upper_bound), '이상치분류'] = '비정상'

    classification_outliers_summary.append(group_summary)

classification_outliers_summary_df = pd.concat(classification_outliers_summary)
classification_outliers_summary_df = classification_outliers_summary_df[['구분', 'rrc_attempt_bin', '이상치분류'] + desired_columns]

# Streamlit에서 구분자 별 이상치 분석 결과 출력
st.subheader("구분자 별 이상치 분석 결과")
st.dataframe(classification_outliers_summary_df)
