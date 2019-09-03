import re
import datetime
from pprint import pformat, pprint
import logging
import requests
from requests.compat import urljoin
from bs4 import BeautifulSoup


def torrent_search(keyword):
    logger = logging.getLogger('t_secretary')
    search_results = []
    req = requests.get(url='https://torrentwal.com/bbs/s.php', params={'k': keyword})
    if not req.ok:
        print('Something wrong')
        return

    soup = BeautifulSoup(req.text, 'html.parser')
    results = soup.select('table.board_list > tr.bg1')
    for result in results:
        magnet = None
        category = None
        subject = None
        timestr = None
        size = None

        try:
            magnet = result.select('td:first-child > a')[0].get('href')
        except Exception as e:
            pass

        try:
            tag1 = result.find('td', {'class': 'subject'})
            tag2 = tag1.find_all('a')
            if tag2:
                category = tag2[0].text.strip()
                subject = tag2[-1].text.strip()
            else:
                category = ''
                subject = tag1.text.strip()
        except Exception as e:
            pass

        try:
            timestr = result.select('td.datetime')[0].text.strip()
        except Exception as e:
            pass
        try:
            size = result.select('td.hit')[0].text.strip()
        except Exception as e:
            pass

        if magnet is None or subject is None:
            logger.warning('magnet 또는 subject를 찾을 수 없습니다.')
            logger.warning(result)
            continue

        info = {
            'magnet': magnet,
            'category': category,
            'subject': subject,
            'datetime': timestr,
            'size': size
        }

        logger.debug(info)

        # 데이타 정제 - 마그넷 링크 완성
        # FROM   javascript:Mag_dn('F9586F750FCB124CDEA6203F294C1E89C08E822E')
        # TO     magnet:?xt=urn:btih:f9586f750fcb124cdea6203f294c1e89c08e822e
        regex = re.compile(r"\'(\w+)'")
        matchobj = regex.search(info['magnet'])
        if matchobj:
            info['magnet'] = 'magnet:?xt=urn:btih:' + matchobj.group(1)
        else:
            info['magnet'] = None

        # 데이타 정제 - mmdd 형태로 받기 때문에 미래 월일인 경우에는 작년으로 변경한다.
        today = datetime.datetime.today()
        postday = datetime.datetime.strptime(info['datetime'], '%m-%d').replace(year=today.year)
        if postday > today:
            postday = postday.replace(year=postday.year - 1)
        info['datetime'] = postday

        # 데이타 정제 - 해상도
        regex = re.compile(r'\b\d{3,4}p\b', re.IGNORECASE)
        matchobj = regex.search(info['subject'])
        if matchobj:
            info['res'] = matchobj.group()
        else:
            info['res'] = 'unknown'

        search_results.append(info)

    logger.debug(pformat(search_results))

    return search_results


def torrent_popular_list():
    logger = logging.getLogger('t_secretary')
    search_results = []

    req = requests.get(url='https://torrentwal.com/bbs/popular.html')
    if not req.ok:
        print('Something wrong')
        return

    # 페이지 오류 수정
    req.encoding = 'utf-8'
    soup = BeautifulSoup(req.text, 'html.parser')
    
    # 예능 찾기
    results = soup.select('#fieldset_list > fieldset:nth-child(2) > table > tr > td > a')
    for idx, result in enumerate(results, start=1):
        subject = '[예능] ' + result.text.strip()
        url = urljoin('https://torrentwal.com/bbs', result.get('href'))
        search_results.append({'subject': subject, 'url': url})
        logger.debug('{}) {} - {}'.format(idx, subject, url))

    # 드라마 찾기
    results = soup.select('#fieldset_list > fieldset:nth-child(3) > table > tr > td > a')
    for idx, result in enumerate(results, start=1):
        subject = '[드라마] ' + result.text.strip()
        url = urljoin('https://torrentwal.com/bbs', result.get('href'))
        search_results.append({'subject': subject, 'url': url})
        logger.debug('{}) {} - {}'.format(idx, subject, url))

    # 다큐 찾기
    results = soup.select('#fieldset_list > fieldset:nth-child(4) > table > tr > td > a')
    for idx, result in enumerate(results, start=1):
        subject = '[다큐] ' + result.text.strip()
        url = urljoin('https://torrentwal.com/bbs', result.get('href'))
        search_results.append({'subject': subject, 'url': url})
        logger.debug('{}) {} - {}'.format(idx, subject, url))

    return search_results


def torrent_info_from_url(url):
    info = {'subject': None, 'magnet': None, 'size': None, 'timestr': None}
    logger = logging.getLogger('t_secretary')

    req = requests.get(url=url)
    if not req.ok:
        return None
    req.encoding = 'utf-8'

    # 토렌트 파일명 찾기
    soup = BeautifulSoup(req.text, 'html.parser')
    try:
        info['subject'] = soup.select('legend')[0].text.strip()
    except Exception as e:
        logger.error('토렌트 제목을 찾는 중 오류가 발생했습니다.\n{}'.format(e))

    # 마그넷링크 찾기
    regex = re.compile(r'<a href="(magnet:.+?)">')
    matchobj = regex.search(req.text)
    if matchobj:
        info['magnet'] = matchobj.group(1)

    # 파일사이즈 찾기
    regex = re.compile(r'<li>파일크기:(.+?)<')
    matchobj = regex.search(req.text)
    if matchobj:
        info['size'] = matchobj.group(1).strip()

    # 생성일자 찾기
    regex = re.compile(r'<li>시드생성일:(.+?)<')
    matchobj = regex.search(req.text)
    if matchobj:
        timestr = matchobj.group(1).strip()
        info['timestr'] = datetime.datetime.strptime(timestr, '%Y년%m월%d일')

    return info


if __name__ == '__main__':
    rs = torrent_popular_list()
    print(len(rs))
    print(rs)
    r1 = torrent_info_from_url(rs[0]['url'])
    print(r1)
    r2 = torrent_search('불타는 청춘')
    pprint(r2)
