import os

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.colors import BoundaryNorm
import japanize_matplotlib
import seaborn as sns
import streamlit as st

import jma

sns.set_context('paper')

### ページ設定
st.set_page_config(
    page_title="気温ヒートマップ",
    page_icon="🌡️",
    layout="centered"
)

st.title('気温ヒートマップ')
link = '出典: [気象庁](https://www.data.jma.go.jp/risk/obsdl/index.php)'
st.markdown(link, unsafe_allow_html=True)

@st.cache_data
def load_block_list():
    filename = os.path.dirname(__file__) + '/block_list.csv'
    df = (
        pd.read_csv(filename, dtype=str, index_col=None)
        .query("地点区分 == 's' and 終了年月日 == '99999999' ")
    )
    return df

@st.cache_data(show_spinner='Loading data...')
def load_data(block_no, month):
    df = jma.get_data(block_no, month)

    if month == 2:
        df = df.query("月 == 2")

    # wide型に変換
    dfs = {}
    for kind in ['平均気温','最高気温','最低気温']:
        dfs[kind] = df.pivot_table(index='年', columns='日', values=kind, aggfunc='mean')

    return dfs

block_list = load_block_list()

# カラム
col1, col2 = st.columns(2)
col3, col4 = st.columns(2)

precs = block_list['都府県地方名'].drop_duplicates().tolist()
with col1:
    prec = st.selectbox('都府県・地方:', precs, index=24) # Default to '東京'

blocks = block_list.query("都府県地方名 == @prec")['地点名'].tolist()
with col2:
    block = st.selectbox('地点:', blocks)
block_no = str(block_list.query("地点名 == @block").iat[0, 3])  # ['地点番号']

with col3:
    month = st.selectbox('月:', range(1, 13))
dfs = load_data(block_no, month)

with col4:
    kind = st.selectbox('表示:', ['平均気温','最高気温','最低気温'])

fig, ax = plt.subplots(figsize=(9, 16))
cmap = ['#002080','#0041FF','#0096FF','#B9EBFF','#FFFFF0','#FFFF96','#FAF500','#FF9900','#FF2800','#B40068']
bounds = np.linspace(-10, 40, 11)
norm = BoundaryNorm(bounds, 10)
sns.heatmap(dfs[kind], square=True, cmap=cmap, norm=norm, linewidths=1, ax=ax, cbar_kws={'shrink': 0.3})
ax.set_title(f'{block}（{prec}）の{month}月の{kind}')
st.pyplot(fig)
