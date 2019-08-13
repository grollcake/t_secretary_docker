import re
import datetime
from pprint import pformat, pprint
import logging
import requests
from requests.compat import urljoin
from bs4 import BeautifulSoup


def torrent_search(keyword):
    logger = logging.getLogger('t_secretary')

    # 애니메이션 '애니 검색어' 형태로 입력했을때만 검색한다.
    if keyword.split(' ')[0] == '애니':
        keyword = ' '.join(keyword.split(' ')[1:])
        boards = {'tani': '애니'}
    else:
        boards = {'tent': '예능', 'tv': 'TV', 'tdrama': '드라마'}

    search_results = []

    for board in boards.keys():
        req = requests.get(url='https://www.tfreeca2.com/board.php', params={'b_id': board, 'mode': 'list', 'sc': keyword})
        if not req.ok:
            print('Something wrong')
            return

        req.encoding = 'utf8'
        soup = BeautifulSoup(req.text, 'html.parser')

        results = soup.select('td.subject > div.list_subject > a:nth-child(2)')
        for idx, result in enumerate(results, start=1):
            category = boards[board]
            subject = result.text.strip()
            url = urljoin('http://www.tfreeca22.com', result.get('href'))

            info = {
                'url': url,
                'magnet': None,
                'category': category,
                'subject': subject
            }

            logger.debug(info)

            search_results.append(info)

            if idx >= 20: break

    logger.debug(pformat(search_results))

    return search_results


def torrent_popular_list():
    logger = logging.getLogger('t_secretary')
    search_results = []

    req = requests.get(url='http://www.tfreeca22.com/top100.php?b_id=tent&hit=Week')
    if not req.ok:
        print('Something wrong')
        return

    # 페이지 오류 수정
    req.encoding = 'utf-8'
    soup = BeautifulSoup(req.text, 'html.parser')
    
    # 예능에서 20개만 찾기
    results = soup.select('td.subject > div.list_subject > a:nth-child(2)')
    for idx, result in enumerate(results, start=1):
        subject = '[예능] ' + result.text.strip()
        url = urljoin('http://www.tfreeca22.com', result.get('href'))
        search_results.append({'subject': subject, 'url': url})
        logger.debug('{}) {} - {}'.format(idx, subject, url))
        if idx == 20: break

    return search_results


def torrent_info_from_url(url):
    logger = logging.getLogger('t_secretary')
    info = {'subject': None, 'magnet': None, 'size': None, 'timestr': None}
    logger = logging.getLogger('t_secretary')

    req = requests.get(url=url)
    if not req.ok:
        return None
    req.encoding = 'utf-8'

    # 토렌트 파일명 찾기
    soup = BeautifulSoup(req.text, 'html.parser')
    try:
        info['subject'] = soup.select('td.view_t2')[0].get('title')
    except Exception as e:
        logger.error('토렌트 제목을 찾는 중 오류가 발생했습니다.\n{}'.format(e))

    # 생성일자 찾기:  " 등록일: 2019-05-24 23:27:49"
    regex = re.compile(r'> 등록일: (.+?)<')
    matchobj = regex.search(req.text)
    if matchobj:
        timestr = matchobj.group(1).strip()
        info['timestr'] = datetime.datetime.strptime(timestr, '%Y-%m-%d %H:%M:%S')

    # 마그넷 링크와 사이즈 정보 획득
    info2 = get_magnet_from_page(url)
    info['magnet'] = info2['magnet']
    info['size'] = info2['size']

    logger.info(info)
    return info


def get_magnet_from_page(page_url):
    """ 티프리카의 토렌트 페이지 url을 받아 magnet link와 사이즈를 리턴한다."""
    logger = logging.getLogger('t_secretary')
    info = {}

    # url에서 보드명과 글번호 검색
    regex = re.compile(r'\Wb_id=(\w+)')
    matchobj = regex.search(page_url)
    if matchobj:
        b_id = matchobj.group(1)

    regex = re.compile(r'\Wid=(\w+)')
    matchobj = regex.search(page_url)
    if matchobj:
        wr_id = matchobj.group(1)

    # magnet 정보 요청
    info_url = 'http://www.tfreeca22.com/info.php?bo_table={}&wr_id={}'.format(b_id, wr_id)
    req = requests.get(url=info_url)

    # 마그넷링크 찾기
    regex = re.compile(r'<a href="(magnet:.+?)">')
    matchobj = regex.search(req.text)
    if matchobj:
        info['magnet'] = matchobj.group(1)

    # 파일사이즈 찾기
    regex = re.compile(r'\(([\d.]+(GB|MB))\)')
    matchobj = regex.search(req.text)
    if matchobj:
        info['size'] = matchobj.group(1).strip()

    logger.info(info)
    return info


if __name__ == '__main__':
    # rs = torrent_popular_list()
    # print(len(rs))
    # print(rs)
    # info = torrent_info_from_url('http://www.tfreeca22.com/board.php?mode=view&b_id=tent&id=976573&page=1')
    # pprint(info)
    rs = torrent_search('애니 명탐정')
    pprint(rs)

