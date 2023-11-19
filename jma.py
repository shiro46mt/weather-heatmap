import os
import io
import time
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import pandas as pd

base_url = 'https://www.data.jma.go.jp/gmd/risk/obsdl/'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:57.0) Gecko/20100101 Firefox/57.0',
}


def fetch(block_no, month):

    # 日付の範囲
    lastday = [0, 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month]
    today = datetime.now()
    year_to = today.year - (month >= today.month)  # 当月以降の場合は今年分のデータがない
    year_from = year_to - 100 + 1  # 100年分

    # メニューページ
    index_url = base_url + 'index.php'
    r = requests.get(index_url, headers=headers)
    if r.status_code != 200:
        raise Exception(r.status_code)
    time.sleep(0.5)

    # PHPSESSID の取得
    soup = BeautifulSoup(r.content, "html.parser")
    sid = soup.select_one("#sid").attrs['value']

    # 検索結果
    table_url = base_url + 'show/table'  # 'show/table.html'
    payload = {
        'stationNumList': f'["s{block_no}"]',
        'aggrgPeriod': '1',
        'elementNumList': '[["201",""],["202",""],["203",""]]',
        'interAnnualFlag': '2',
        'ymdList': f'["{year_from}","{year_to}","{month}","{month}","1","{lastday}"]',
        'optionNumList': '[]',
        'downloadFlag': 'true', # table.html の場合にコメントアウト
        'rmkFlag': '1',
        'disconnectFlag': '1',
        'kijiFlag': '0',
        'huukouFlag': '0',
        'csvFlag': '1', # table.html の場合にコメントアウト
        'youbiFlag': '0',
        'fukenFlag': '0',
        'jikantaiFlag': '0',
        'jikantaiList': '[]',
        'PHPSESSID': sid
    }
    r = requests.post(table_url, data=payload, headers=headers)
    if r.status_code != 200:
        raise Exception(r.content)

    r.encoding = r.apparent_encoding
    return r.text


def get_data(block_no, month):
    filename = os.path.dirname(__file__) + f'/data/{block_no}_{month:0>2d}.csv'
    read_args = {
        'header': None,
        'skiprows': 6,
        'names': ['年','月','日','平均気温','最高気温','最低気温'],
        'usecols': [0,1,2,3,6,9]
    }
    do_reload = True
    if os.path.isfile(filename):
        df = pd.read_csv(filename, **read_args)
        # 更新データがないか確認: 既存データの最新年が今年(今月以降の場合は昨年)と一致すれば更新不要
        year_max = int(df['年'].max())
        today = datetime.now()
        year = today.year
        if month >= today.month:
            year -= 1
        if year_max == year:
            do_reload = False
    if do_reload:
        lines = fetch(block_no, month)
        with open(filename, 'w', encoding='utf8', newline='') as f:
            f.write(lines)
        df = pd.read_csv(io.StringIO(lines), **read_args)
    return df


if __name__ == "__main__":
    for month in range(1, 13):
        df = get_data('47662', month)
        time.sleep(1)
    print(df)

