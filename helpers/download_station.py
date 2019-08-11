import logging
from pprint import pprint, pformat
import requests
from requests.compat import urljoin
from helpers.config import get_config


def ds_login(host, id, pw):
    logger = logging.getLogger('t_secretary')
    session = requests.Session()

    # 로그인하기
    api_url = urljoin(host, '/webapi/auth.cgi')
    req = session.get(api_url, params={'api': 'SYNO.API.Auth', 'version': '2', 'method': 'login', 'account': id, 'passwd':
        pw, 'session': 'DownloadStation', 'format': 'cookie'}, verify=False)
    if not req.ok:
        logger.error('Something error in login to DSM. status_code={}'.format(req.status_code))
        return None

    res = req.json()
    if not res['success']:
        logger.error('Something error in login to DSM\nReturn json data is..\n{}'.format(pformat(res)))
        return None

    return session


def ds_list(host, id, pw):
    logger = logging.getLogger('t_secretary')

    r_list = list()

    session = ds_login(host, id, pw)
    if not session:
        return None

    # 활성 목록 보기
    api_url = urljoin(host, '/webapi/DownloadStation/task.cgi')
    req = session.get(api_url, params={'api': 'SYNO.DownloadStation.Task', 'version': '1', 'method': 'list'}, verify=False)

    if not req.ok:
        logger.error('다운로드 목록을 가져오는 중 오류가 발생했습니다. status_code={}'.format(req.status_code))
        return None

    res = req.json()
    if not res['success']:
        logger.error('다운로드 목록을 가져오는 중 오류가 발생했습니다.\nReturn json data is..\n{}'.format(pformat(res)))
        return None
    for task in res['data']['tasks']:
        logger.debug('{} - {} - {} - {}'.format(task['id'], to_gb(task['size']), task['status'], task['title']))
        r_list.append({'id': task['id'], 'size': to_gb(task['size']), 'status': task['status'], 'title': task['title']})

    return r_list


def ds_add_magnet(host, id, pw, magnet):
    logger = logging.getLogger('t_secretary')

    session = ds_login(host, id, pw)
    if not session:
        return None

    # 활성 목록 보기
    api_url = urljoin(host, '/webapi/DownloadStation/task.cgi')
    req = session.get(api_url, params={'api': 'SYNO.DownloadStation.Task', 'version': '1', 'method': 'create',
                                       'uri': magnet}, verify=False)

    if not req.ok:
        logger.error('다운로드를 추가하는 중 오류가 발생했습니다. status_code={}'.format(req.status_code))
        return None

    res = req.json()
    logger.debug(res)
    pprint(res)
    if not res['success']:
        logger.error('다운로드를 추가하는 중 오류가 발생했습니다.\nReturn json data is..\n{}'.format(pformat(res)))
        return None

    return True


def to_gb(size):
    return '{:.2f} GB'.format(size / 1024 / 1024 / 1024)


if __name__ == '__main__':
    logger = logging.getLogger('t_secretary')
    logger.setLevel(logging.DEBUG)
    config = get_config()
    ds_list(host=config['DS_SERVER'], id=config['DS_USER'], pw=config['DS_PASS'])
