import logging
import os
from pprint import pprint
from urllib.parse import urlparse

from smb.SMBConnection import SMBConnection
from helpers.config import get_config

smb_conn = None


def size_conv(size):
    if size == 0:
        return '0'

    if size > 1024 * 1024 * 1024:
        return '{:.2f} GB'.format(size / 1024 / 1024 / 1024)
    elif size > 1024 * 1024:
        return '{:.2f} MB'.format(size / 1024 / 1024)
    elif size > 1024:
        return '{:.2f} KB'.format(size / 1024)
    else:
        return '{} B'.format(size)


def smb_connect(server, user, passwd):
    global smb_conn
    logger = logging.getLogger('t_secretary')

    smb_conn = SMBConnection(user, passwd, 't_secretary', 'diskstation', use_ntlm_v2=True, is_direct_tcp=True)

    if not smb_conn.connect(server, 139):
        logger.error('다운로드 경로에 smb로 연결하지 못했습니다. server={} user={} passwd={}'.format(server, user, passwd))
        return None

    logger.info('다운로드 경로에 smb로 연결했습니다')


def smb_path_split(smb_full_path):
    """
    하나의 문자열로 들어온 경로를 smb share와 path로 구분한다.
    torrents             -> torrents   /
    /torrents            -> torrents   /
    /torrents/           -> torrents   /
    nas/torrents/        -> nas        torrents
    /nas/torrents/       -> nas        torrents
    /nas/torrents        -> nas        torrents
    """
    logger = logging.getLogger('t_secretary')

    tokens = smb_full_path.split('/')

    # 맨 앞이 '/'이면 0번째는 null이 된다. 삭제한다.
    if not tokens[0]:
        del tokens[0]

    # 맨 뒤가 '/'이면 -1번째는 null이 된다. 삭제한다.
    if not tokens[-1]:
        del tokens[-1]

    smb_share = tokens[0]
    smb_path = '/'.join(tokens[1::])

    logger.debug('smb_path is splited. {} => {} + {}'.format(smb_full_path, smb_share, smb_path))

    return smb_share, smb_path


def files_from_smb(server, user, passwd, smb_full_path):
    global smb_conn
    logger = logging.getLogger('t_secretary')

    logger.debug('Listing files from {}:{} ({}/{})'.format(server, smb_full_path, user, passwd))

    if not smb_conn:
        smb_connect(server, user, passwd)

    if not smb_conn:
        return None, 'NAS에 연결하지 못했습니다'

    smb_share, smb_path = smb_path_split(smb_full_path)
    logger.debug('smb_share={} smb_path={}'.format(smb_share, smb_path))

    file_list = []
    try:
        files = smb_conn.listPath(smb_share, smb_path)
    except Exception as e:
        logger.error('Exception. {}'.format(e))
        return None, '경로가 올바르지 않습니다 ({})'.format(smb_full_path)

    for file in files:
        if file.filename in ['.', '..', '#recycle', '#snapshot']:
            continue

        info = {'filename': file.filename, 'isDirectory': file.isDirectory, 'file_size': file.file_size}

        if file.isDirectory:
            info['path'] = smb_share + '/' + smb_path + '/' + file.filename

        info['size'] = size_conv(file.file_size)

        file_list.append(info)

    return file_list, None


def files_from_path(local_path):
    file_list = []

    for f in os.listdir(local_path):
        if f in ['.', '..', '#recycle', '#snapshot']:
            continue

        fullspec = os.path.join(local_path, f)
        info = {'filename': f, 'isDirectory': os.path.isdir(fullspec), 'file_size': os.path.getsize(fullspec)}

        if os.path.isdir(fullspec):
            info['path'] = fullspec

        info['size'] = size_conv(info['file_size'])

        file_list.append(info)

    return file_list


def nas_files(path=None):
    logger = logging.getLogger('t_secretary')
    config = get_config()

    find_path = path if path else config['DOWNLOAD_PATH']

    # 2019.08.10 PC, Ubuntu 모두에서 테스트를 원할하게 하기위해 smb모드만 사용토록 한다.
    host = urlparse(config['DS_SERVER']).hostname
    files, error = files_from_smb(host, config['DS_USER'], config['DS_PASS'], find_path)
    if error:
        return None, error
    
    # 로컬 디렉토리(또는 docker 볼륨 마운트)인 경우의 처리
    # else:
    #    files = files_from_path(find_path)

    if find_path != config['DOWNLOAD_PATH']:
        files.insert(0, {
            'filename': '<상위 디렉토리>',
            'isDirectory': True,
            'file_size': 0,
            'size': 0,
            'path': os.path.dirname(find_path)
        })

    return files, None


if __name__ == '__main__':
    main_logger = logging.getLogger('t_secretary')
    main_logger.setLevel(logging.DEBUG)
    main_logger.addHandler(logging.StreamHandler())

    # r_files = nas_files()
    # pprint(r_files)

    r_files = nas_files('/nas/torrents')
    pprint(r_files)

    # main_logger.debug(smb_path_split('torrents'))
    # main_logger.debug(smb_path_split('/torrents'))
    # main_logger.debug(smb_path_split('/torrents/'))
    # main_logger.debug(smb_path_split('nas/torrents/'))
    # main_logger.debug(smb_path_split('/nas/torrents/'))
    # main_logger.debug(smb_path_split('/nas/torrents'))
    # main_logger.debug(smb_path_split('nas/torrents/a'))
    # main_logger.debug(smb_path_split('/nas/torrents/a/'))
    # main_logger.debug(smb_path_split('/nas/torrents/a'))


