import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import ace_tools as tools

# 엑셀 파일 경로 설정
file_path = '/mnt/data/LG_gong_1018.xlsx'

# 엑셀 파일 읽기
try:
    df = pd.read_excel(file_path, engine='openpyxl')
except FileNotFoundError:
    print('파일을 찾을 수 없습니다. 올바른 파일 경로를 확인하세요.')
    exit()

# 필요한 열만 선택
desired_columns = [
    "eqp_vend_nm", "srvc_net_cd", "eqp_own_bizr_cd", "sido_nm", "sgg_nm","eqp_fst_mapp_id", "cell_id", "pci", "frequency",
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
df['identifier'] = df['eqp_fst_mapp_id'].astype(str) + '_' + df['cell_id'].astype(str) + '_' + df['pci'].astype(str)

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

# 데이터베이스 파일 경로 설정
db_path = '/mnt/data/tnp_db.sqlite'

# SQLite 데이터베이스 연결
conn = sqlite3.connect(db_path)

# 데이터프레임을 TnP DB로 내보내기
table_name = 'lg_gong_data'
df.to_sql(table_name, conn, if_exists='replace', index=False)

# 기본 통계 추출 및 사용자에게 표시
df_statistics = df.describe()
tools.display_dataframe_to_user(name="LGU+ 공동망 데이터 기본 통계", dataframe=df_statistics)

# 시각화 - 각 열의 count를 바 차트로 표시
fig, axes = plt.subplots(3, 1, figsize=(10, 15))

# eqp_vend_nm count
df['eqp_vend_nm'].value_counts().plot(kind='bar', ax=axes[0])
axes[0].set_title('Count of eqp_vend_nm')
axes[0].set_xlabel('Vendor Name')
axes[0].set_ylabel('Count')

# sido_nm count
df['sido_nm'].value_counts().plot(kind='bar', ax=axes[1])
axes[1].set_title('Count of sido_nm')
axes[1].set_xlabel('Sido Name')
axes[1].set_ylabel('Count')

# sgg_nm count
df['sgg_nm'].value_counts().plot(kind='bar', ax=axes[2])
axes[2].set_title('Count of sgg_nm')
axes[2].set_xlabel('Sgg Name')
axes[2].set_ylabel('Count')

plt.tight_layout()
plt.show()
