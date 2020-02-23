import re
import datetime
from pprint import pformat, pprint
import logging

import dateutil.parser
import requests
from requests.compat import urljoin
from bs4 import BeautifulSoup

T_SITE = 'https://torrentvery.com'


def torrent_search(keyword):
    logger = logging.getLogger('t_secretary')
    search_results = []

    # 놀면 뭐하니 검색 URL
    # https://torrentvery.com/bbs/search.php?search_flag=search&stx=%EB%86%80%EB%A9%B4+%EB%AD%90%ED%95%98%EB%8B%88

    url = T_SITE + '/bbs/search.php'

    # 전체 검색으로 제목과 내용에서 검색
    req = requests.get(url=url, params={'stx': keyword, 'search_flag': 'search'}, verify=True)
    if not req.ok:
        print('Something wrong')
        return

    soup = BeautifulSoup(req.text, 'html.parser')
    results = soup.select('div.searchbox div.media-body')
    for result in results:
        subject = None
        page_url = None
        magnet = None
        category = None
        timestr = None
        size = None

        # 제목 찾기
        subject = result.select('div.media-heading')[0].text.strip()

        # 마그넷 찾기
        magnet = None

        # 카테고리 찾기
        category = None

        # 게시일자 찾기
        timestr = result.select('time')[0].get('datetime')
        postdate = dateutil.parser.isoparse(timestr)

        # 파일크기 찾기
        size = result.select('span.td_size2600')[0].text.strip()

        # PAGE URL 찾기
        link = result.select('a')[0].get('href')
        page_url = urljoin(url, link)
        logger.warning(page_url)

        info = {
            'subject': subject,
            'page_url': page_url,
            'magnet': magnet,
            'category': category,
            'datetime': postdate,
            'size': size
        }

        logger.warning(info)

        search_results.append(info)

    # 최신 데이타가 마지막 행에 나오도록 재정렬한다.
    search_results.reverse()

    logger.debug(pformat(search_results))

    return search_results


def torrent_popular_list():

    logger = logging.getLogger('t_secretary')
    search_results = []

    url = T_SITE + '/bbs/ranking.php'
    req = requests.get(url=url, verify=True)
    if not req.ok:
        print('Something wrong')
        return

    # 페이지 오류 수정
    req.encoding = 'utf-8'
    soup = BeautifulSoup(req.text, 'html.parser')
    
    # 예능 찾기
    results = soup.select('tbody > tr')
    for idx, result in enumerate(results, start=1):
        subject = result.select("td.list-subject > a")[0].text.strip()
        page_url = urljoin(url, result.select("td.list-subject > a")[0].get('href'))
        search_results.append({'subject': subject, 'page_url': page_url})
        logger.warning('{}) {} - {}'.format(idx, subject, page_url))

    search_results = search_results[:50]    # 너무 길면 텔레그램이 버튼들을 생성할 수가 없다. 적당한 개수로 자르자.
    search_results.reverse()

    return search_results


# 날짜와 시간을 나타내는 문자열로부터 일시 정보 반환
# 예) 오늘이 2020.02.23인 경우
#  02.20      => datetime(2020, 2, 20, 0, 0, 0)
#  2019.12.11 => datetime(2019, 12, 11, 0, 0, 0)
#  11:22      => datetime(2020, 2, 23, 11, 22, 0)
def get_datetime_from_string(timestr):
    today = datetime.datetime.today()
    postdate = None
    # 정규 표현식을 이용한 분류
    if re.match(r'^\d\d\.\d\d$', timestr):
        postdate = datetime.datetime.strptime(timestr, '%m.%d').replace(year=today.year)
    elif re.match(r'^\d\d\d\d\.\d\d\.\d\d$', timestr):
        postdate = datetime.datetime.strptime(timestr, '%Y.%m.%d')
    elif re.match(r'^\d\d\:\d\d$', timestr):
        postdate = datetime.datetime.strptime(timestr, '%H:%M').replace(year=today.year, month=today.month, day=today.day)

    return postdate


def torrent_info_from_url(url):
    info = {'subject': None, 'magnet': None, 'size': None, 'timestr': None}
    logger = logging.getLogger('t_secretary')

    req = requests.get(url=url, verify=True)
    if not req.ok:
        return None
    req.encoding = 'utf-8'

    # 토렌트 파일명 찾기
    soup = BeautifulSoup(req.text, 'html.parser')
    try:
        info['subject'] = soup.select('h1')[0].text.strip()
    except Exception as e:
        logger.error('토렌트 제목을 찾는 중 오류가 발생했습니다.\n{}'.format(e))

    # 마그넷링크 찾기
    regex = re.compile(r' href="(magnet:.+?)"')
    matchobj = regex.search(req.text)
    if matchobj:
        info['magnet'] = matchobj.group(1)

    # 파일사이즈 찾기
    try:
        info['size'] = soup.select('div.text-muted.panel-heading3.tpanel-heading3.moreless b')[0].text.strip()
    except Exception as e:
        logger.error('토렌트 파일 크기를 찾는 중 오류가 발생했습니다.\n{}'.format(e))

    # 생성일자 찾기
    try:
        timestr = soup.select('#bg-content > div > div.col-md-9.col-md-pull-0.m-col-mb-9 > div.view-wrap.view-wrap-title > div > div > div > span:nth-child(3)')[0].text.strip()
        info['timestr'] = get_datetime_from_string(timestr)
    except Exception as e:
        logger.error('토렌트 생성일자를 찾는 중 오류가 발생했습니다.\n{}'.format(e))

    return info


# 토렌트 페이지 URL에서 마그넷 링크를 검색한다.
# 'magnet:'으로 시작하는 첫번째 링크를 찾아 반환한다.
def get_magnet_from_page(page_url):
    magnet_link = ''
    
    req = requests.get(url=page_url, verify=True)
    if not req.ok:
        return None
    req.encoding = 'utf-8'
    
    # 마그넷링크 찾기
    regex = re.compile(r'<a href="(magnet:.+?)"')
    matchobj = regex.search(req.text)
    if matchobj:
        magnet_link = matchobj.group(1)
    
    return magnet_link


if __name__ == '__main__':
    # print(torrent_info_from_url('https://torrentvery.com/torrent_ani/4581'))
    # print(torrent_info_from_url('https://torrentvery.com/torrent_ent/5436'))
    # print(torrent_info_from_url('https://torrentvery.com/torrent_movieov/5932'))
    r2 = torrent_search('놀면 뭐하니')
    print(r2)
    # rs = torrent_popular_list()
    # print(len(rs))
    # torrent_info_from_url(rs[0]["url"])
    # r1 = torrent_info_from_url(rs[0]['url'])
    # print(r1)
    # pprint(r2)
