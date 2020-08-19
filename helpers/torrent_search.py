from pprint import pformat, pprint
import logging
from urllib import parse

import feedparser

T_SITE = 'https://www.ifwind.net'


def torrent_search(keyword):
    logger = logging.getLogger('t_secretary')
    search_results = []

    url = T_SITE + '/torr/torr.php?b=ent&k=' + parse.quote(keyword)

    logger.info('사이트 검색: {}'.format(url))

    fp = feedparser.parse(url)
    if not fp:
        print('Something wrong')
        return

    for entry in fp.entries:
        subject = entry['title']
        page_url = entry['comments']
        magnet = entry['link']
        category = '예능'
        postdate = None
        size = None

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

    url = T_SITE + '/torr/torr.php'

    fp = feedparser.parse(url)
    if not fp:
        print('Something wrong')
        return

    for entry in fp.entries:
        subject = entry['title']
        page_url = entry['comments']
        magnet = entry['link']
        category = '예능'
        postdate = None
        size = None

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



def torrent_info_from_url(url):
    logger = logging.getLogger('t_secretary')

    info = {'subject': None, 'magnet': None, 'size': None, 'timestr': None}
    logger.error('URL로부터 토렌트 정보 찾기는 지원하지 않습니다.')

    return info


if __name__ == '__main__':
    # print(torrent_info_from_url('https://torrentvery.com/torrent_ani/4581'))
    # print(torrent_info_from_url('https://torrentvery.com/torrent_ent/5436'))
    # print(torrent_info_from_url('https://torrentvery.com/torrent_movieov/5932'))
    #r2 = torrent_search('놀면 뭐하니')
    # print(r2)
    rs = torrent_popular_list()
    print(len(rs))
    pprint(rs)
    # torrent_info_from_url(r2[0]["page_url"])
    # print(torrent_info_from_url(
    #    'https://torrentsir8.com/bbs/board.php?bo_table=entertain&wr_id=14615'))
    # r1 = torrent_info_from_url(rs[0]['url'])
    # print(r1)
    # pprint(r2)
