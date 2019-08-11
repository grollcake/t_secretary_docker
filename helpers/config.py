import json
import logging
import os
from pprint import pprint

CONF_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config.json')


def get_config():
    """
    도커로 실행한 경우에는 환경변수가 들어오기 때문에 환경파일보다 우선 적용한다.
    환경변수는 설정파일에 기록하여 나중에 환경변수 없이 도커를 실행하더라도 유지토록 한다.
    환경변수가 없으면 설정파일을 읽어들인다.
    """
    logger = logging.getLogger('t_secretary')

    # 1. 환경파일을 먼저 읽어들인다.
    try:
        with open(CONF_FILE, 'r', encoding='utf-8') as f:
            file_config = json.load(f)
            logger.debug('Config from file: {}'.format(file_config))
    except Exception:
        raise RuntimeError('ConfigLoadError')

    # 2. 환경변수로 들어온 값을 우선 사용한다.
    config = file_config.copy()
    config['BOT_TOKEN'] = os.getenv('BOT_TOKEN', config['BOT_TOKEN'])
    config['DS_SERVER'] = os.getenv('DS_SERVER', config['DS_SERVER'])
    config['DS_USER'] = os.getenv('DS_USER', config['DS_USER'])
    config['DS_PASS'] = os.getenv('DS_PASS', config['DS_PASS'])
    config['DOWNLOAD_PATH'] = os.getenv('DOWNLOAD_PATH', config['DOWNLOAD_PATH'])

    # 3. 환경변수인해 값이 변경됐을 수도 있으니까 환경파일에 다시 기록한다.
    if config != file_config:
        save_config(config)

    # 4. 직전 버퍼와 비교한다.
    if not hasattr(get_config, "static_config"):
        get_config.static_config = config.copy()
        logger.info('Initial configs are loaded: {}'.format(config))
    elif get_config.static_config != config:
        get_config.static_config = config.copy()
        logger.info('configs are changed: {}'.format(config))

    return config


def set_config(config):
    """
    환경설정을 최신값으로 업데이트하고 파일로 저장한다.
    CHAT_USERS 추가할 때 사용하게 된다.
    """
    logger = logging.getLogger('t_secretary')
    curr_config = get_config()
    curr_config.update(config)
    save_config(curr_config)
    logger.info('Config is updated: {}'.format(curr_config))


def save_config(config):
    logger = logging.getLogger('t_secretary')

    try:
        with open(CONF_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
    except Exception:
        raise RuntimeError('ConfigSaveError')

    logger.debug('config.json is updated. path: {}'.format(CONF_FILE))


if __name__ == '__main__':
    conf = get_config()
    pprint(conf)
    set_config({"CHAT_USERS": ["55382697", "51151105"]})
    pprint(get_config())
