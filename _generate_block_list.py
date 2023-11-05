import os
import re
import time
from tqdm import tqdm
import requests
from bs4 import BeautifulSoup

base_url = 'https://www.data.jma.go.jp/obd/stats/etrn/select/'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:57.0) Gecko/20100101 Firefox/57.0',
}


def main():

    # 都府県・地方の選択
    index_url = base_url + 'prefecture00.php'
    r = requests.get(index_url, headers=headers)
    if r.status_code != 200:
        raise Exception(r.status_code)
    time.sleep(0.5)

    # 地点の選択 のurl取得
    soup = BeautifulSoup(r.content, "html.parser")
    areas = []
    visited = set()
    for area in tqdm(soup.select("area")):
        name = area.attrs['alt']
        url = area.attrs['href']
        mob = re.search(r'prec_no=(\d+)&', url)
        prec_no = mob.group(1)

        # 地点の選択
        select_url = base_url + url
        r = requests.get(select_url, headers=headers)
        if r.status_code != 200:
            raise Exception(r.content)
        time.sleep(0.5)

        # 地点の選択 のurl取得
        soup = BeautifulSoup(r.content, "html.parser")
        for area_sub in soup.select("area"):
            if 'onmouseover' in area_sub.attrs:
                script = area_sub.attrs['onmouseover']
                mob = re.search(r'\((.+)\)', script)
                vars = mob.group(1).replace("'", "").split(',')
                block_no = vars[1]
                if block_no not in visited:
                    lat = '{:.6f}'.format(int(vars[4]) + float(vars[5]) / 60)
                    lng = '{:.6f}'.format(int(vars[6]) + float(vars[7]) / 60)
                    height = vars[8]
                    lastdate = ''.join(vars[15:18])
                    note = vars[18]
                    areas.append([prec_no, name, *vars[:4], lat, lng, height, *vars[9:15], lastdate, note])
                    visited.add(block_no)

    return areas


if __name__ == "__main__":
    areas = main()
    cols = ['都府県地方番号','都府県地方名','地点区分','地点番号','地点名','地点名カナ','緯度','経度','標高','降水量','気温','風','日照','積雪','湿度','終了年月日','備考']
    with open(os.path.dirname(__file__) + f'/block_list.csv', 'w', encoding='utf8', newline='') as f:
        f.write(','.join(cols) + '\r\n')
        for area in areas:
            f.write(','.join(area) + '\r\n')
