#!/usr/bin/env python3
import os
import hashlib
import logging
import pickle
import pprint
from logging.handlers import RotatingFileHandler
from time import sleep
import sqlite3
import datetime
from telepot import Bot, glance
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from helpers.config import get_config, set_config
from helpers.download_station import ds_list, ds_add_magnet
from helpers.nas_files import nas_files
from helpers.torrent_search_torrentvery import torrent_search, torrent_popular_list, torrent_info_from_url

bot = None
conn = None
db_cursor = None
INTERACTIONS = {}
logger = logging.getLogger('t_secretary')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BUTTON_LENGTH = 52


def init_db():
    global conn
    db_file = os.path.join(BASE_DIR, 'database.db')
    conn = sqlite3.connect(db_file, check_same_thread=False)
    conn.set_trace_callback(None)  # sql을 출력하고 싶으면 None 대신에 Print 삽입
    conn.execute("""
    CREATE TABLE IF NOT EXISTS callback_cache (
        idx   INTEGER PRIMARY KEY,
        key   TEXT NOT NULL,
        type  TEXT NOT NULL,
        data  TEXT NOT NULL,
        cdt   TIMESTAMP
        );
    """)
    conn.commit()


def init_log():
    logfile = os.path.join(BASE_DIR, 't_secretary.log')

    logger.setLevel(logging.DEBUG)

    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    sh.setFormatter(
        logging.Formatter('%(asctime)s.%(msecs)03d:%(levelname)s:%(filename)s:%(funcName)s:%(lineno)d: %(message)s',
                          datefmt='%Y/%m/%d %H:%M:%S'))
    logger.addHandler(sh)

    fh = RotatingFileHandler(filename=logfile, encoding='utf-8', maxBytes=10 * 1024 * 1024, backupCount=0)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(
        logging.Formatter('%(asctime)s.%(msecs)03d:%(levelname)s:%(filename)s:%(funcName)s:%(lineno)d: %(message)s',
                          datefmt='%Y/%m/%d %H:%M:%S'))

    logger.addHandler(fh)
    logger.info('log is initialized')


def get_md5(string):
    return hashlib.md5(string.encode('utf-8')).hexdigest()


# commit 시 너무 느려지는 현상이 있어서 커서오픈/커밋을 한방에 처리하고자 별도 함수로 분리한다.
def db_open_cursor():
    global conn
    global db_cursor

    db_cursor = conn.cursor()


def db_commit_cursor():
    logger.debug("before db_cursor.commit()")
    db_cursor.commit()
    db_cursor.close()
    logger.debug("after db_cursor.commit()")


def db_set_data(key=None, type=None, data=None, datasets=None):
    if key and data:
        data_str = pickle.dumps(data)
        db_cursor.execute('INSERT INTO callback_cache (KEY, TYPE, DATA, CDT) VALUES (?, ?, ?, ?)',
                          (key, type, data_str, datetime.datetime.now()))
    else:
        for dataset in datasets:
            data_str = pickle.dumps(dataset['data'])
            db_cursor.execute('INSERT INTO callback_cache (KEY, TYPE, DATA, CDT) VALUES (?, ?, ?)',
                              (dataset['key'], dataset['type'], data_str, datetime.datetime.now()))

    # 마지막 10000개만 유지하기
    db_cursor.execute('SELECT COUNT(*) FROM callback_cache')
    rowcount = db_cursor.fetchone()[0]
    if rowcount >= 10000:
        db_cursor.execute('DELETE callback_cache WHERE idx NOT IN '
                          '(SELECT idx FROM callback_cache ORDERY BY idx DESC LIMIT 10000);')
        logger.info('callback_cache 테이블에서 {}개의 row를 삭제했습니다.'.format(rowcount - rowcount))

    logger.debug('{}개의 데이타를 db에 저장했습니다.'.format(len(datasets) if datasets else 1))


def db_get_data(key):
    c = conn.cursor()
    try:
        c.execute('SELECT type, data FROM callback_cache WHERE key = :key ORDER BY idx DESC;', {'key': key})
        datas = c.fetchone()
        logger.debug(datas)
    except sqlite3.Error as e:
        logger.error('DB 처리 중 오류 발생: key=[{}] error={}'.format(key, e))
        return None

    if not datas:
        logger.info('DB에서 데이타를 찾을 수 없음: key=[{}]'.format(key))
        return None

    type = datas[0]
    data = pickle.loads(datas[1])
    logger.debug('DB에서 데이타 찾음: key={}  data={}'.format(key, data))
    return type, data


def make_button_text(idx, torrent):
    text1 = '{}) '.format(idx)
    text1 += '[{}] '.format(torrent['category']) if ('category' in torrent and torrent['category'] is not None) else ''
    text1 += '{} '.format(torrent['subject'])
    text2 = ''

    if 'datetime' in torrent or 'size' in torrent:
        text2 = '('
        text2 += '{:02d}/{:02d}, '.format(torrent['datetime'].month,
                                          torrent['datetime'].day) if 'datetime' in torrent else ''
        text2 += '{}'.format(torrent['size']) if 'size' in torrent else ')'
        text2 += ')'

    button_text = text1 + text2
    if len(button_text) > BUTTON_LENGTH:
        slice_len = BUTTON_LENGTH - len(text2) - 3
        button_text = text1[:slice_len] + '.. ' + text2

    return button_text


def user_interactions(chat_id, action, status=None, path=None):
    global INTERACTIONS
    if action == 'clear':
        INTERACTIONS.pop(chat_id, None)
    elif action == 'get_status':
        if INTERACTIONS.get(chat_id, None):
            return INTERACTIONS[chat_id].get('status', None)
        else:
            return None
    elif action == 'set_status':
        if INTERACTIONS.get(chat_id, None):
            INTERACTIONS[chat_id]['status'] = status
        else:
            INTERACTIONS[chat_id] = {'status': status}
    elif action == 'get_path':
        if INTERACTIONS.get(chat_id, None) is None:
            return None
        path_buff = INTERACTIONS[chat_id].get('path_buff', None)
        if not path_buff:
            return None
        for p in path_buff:
            if p['hash'] == path:
                return p['path']
        return None
    elif action == 'set_path':
        if INTERACTIONS.get(chat_id, None) is None:
            INTERACTIONS[chat_id] = {'path_buff': []}
        path_hash = get_md5(path)
        INTERACTIONS[chat_id]['path_buff'].append({'hash': path_hash, 'path': path})
        INTERACTIONS[chat_id]['path_buff'] = INTERACTIONS[chat_id]['path_buff'][-100:]
        return path_hash


def chat_start(chat_id):
    help_msg = """
시놀로지 나스의 토렌트 비서입니다.
아래 명령어들을 처리할 수 있습니다.\n
/search - 토렌트 검색 (검색어 입력 필요)
/add - 토렌트 추가 (마그넷링크 입력 필요)
/list - 다운로드 중인 목록 보기
/popular - 인기있는 토렌트 목록
/files - 나스의 파일 목록 보기
/help - 도움말 보기
"""
    bot.sendMessage(chat_id, help_msg)


def chat_search(chat_id, keyword):
    if not keyword:
        bot.sendMessage(chat_id, '검색어를 입력하세요\n예) /search 무한도전')
        return

    bot.sendMessage(chat_id, '{}요? 찾아볼게요..'.format(keyword))

    try:
        torrents = torrent_search(keyword)
    except Exception as e:
        logger.error('토렌트 검색 중 오류가 발생했습니다.')
        logger.error(e)
        bot.sendMessage(chat_id, '검색 중 뭔가 문제가 발생했어요')
        return

    if not torrents:
        bot.sendMessage(chat_id, '검색 결과가 없습니다 ㅜ')
        return

    select_list = list()

    db_open_cursor()

    for idx, torrent in enumerate(torrents, start=1):
        button_text = make_button_text(idx, torrent)

        callback_key = get_md5(torrent['magnet']) if torrent['magnet'] else get_md5(torrent['page_url'])
        db_set_data(key=callback_key, type='TORRENT', data=torrent)  # DB에 저장
        select_list.append([InlineKeyboardButton(text=button_text, callback_data=callback_key)])

    db_commit_cursor()

    keyboard = InlineKeyboardMarkup(inline_keyboard=select_list)

    logger.debug(pprint.pformat(keyboard))

    bot.sendMessage(chat_id, '{}개를 찾았습니다.'.format(len(select_list)), reply_markup=keyboard)


def chat_search_step2(chat_id, torrent):
    if not torrent:
        bot.sendMessage(chat_id, '뭔가 문제가 있어요.')
        return

    logger.info(torrent)
    if torrent['magnet']:
        chat_add_magnet(chat_id=chat_id, magnet=torrent['magnet'], subject=torrent['subject'], size=torrent['size'])
    else:
        chat_popular_step2(chat_id, torrent['page_url'])  # 한번 확인하고 다운받게 한다.


def chat_list(chat_id):
    config = get_config()
    try:
        downloads = ds_list(host=config['DS_SERVER'], id=config['DS_USER'], pw=config['DS_PASS'])
    except Exception as e:
        logger.error('다운로드 목록 확인 중 오류가 발생했습니다.')
        logger.error(e)
        bot.sendMessage(chat_id, '다운로드 목록 확인 중 뭔가 문제가 발생했어요.')
        return

    if downloads:
        msg = '{}개의 다운로드가 있습니다.\n\n'.format(len(downloads))
        for idx, download in enumerate(downloads, start=1):
            msg += '{}) {} ({}, {})\n'.format(idx, download['title'], download['size'], download['status'])
    else:
        msg = '진행 중인 다운로드가 없습니다.\n'

    logger.info('Bot replied: {}'.format(msg))
    bot.sendMessage(chat_id, msg)


def chat_add_magnet(chat_id, magnet, subject=None, size=None):
    if not magnet:
        bot.sendMessage(chat_id, '마그넷 링크를 입력하세요\n예) /search magnet:...')
        return

    config = get_config()
    try:
        logger.info('다운로드를 추가하겠습니다. magnet: {}'.format(magnet))
        ret = ds_add_magnet(host=config['DS_SERVER'], id=config['DS_USER'],
                            pw=config['DS_PASS'], magnet=magnet)
    except Exception as e:
        logger.error('다운로드 추가 중 오류가 발생했습니다.')
        logger.error(e)
        bot.sendMessage(chat_id, '다운로드 추가 중 뭔가 문제가 발생했어요.')
        return

    if ret:
        msg = '다운로드를 시작합니다.\n'
        if subject:
            msg += ' * 파일명: {}\n'.format(subject)
        if size:
            msg += ' * 사이즈: {}\n'.format(size)
        msg += '/list 명령으로 확인해보세요.'
    else:
        msg = '다운로드 추가 중 뭔가 문제가 발생했어요.'
    bot.sendMessage(chat_id, msg)


def chat_popular(chat_id):
    bot.sendMessage(chat_id, '인기 토렌트를 검색합니다...')

    populars = torrent_popular_list()
    select_list = list()

    if not isinstance(populars, list):
        bot.sendMessage(chat_id, '뭔가 문제가 생겼습니다.')
        return

    db_open_cursor()

    for idx, popular in enumerate(populars, start=1):
        button_text = make_button_text(idx, popular)
        callback_key = get_md5(popular['page_url'])
        select_list.append([InlineKeyboardButton(text=button_text, callback_data=callback_key)])
        db_set_data(key=callback_key, type='POPULAR', data=popular['page_url'])  # DB에 저장

    db_commit_cursor()

    keyboard = InlineKeyboardMarkup(inline_keyboard=select_list)

    logger.debug(pprint.pformat(keyboard))

    bot.sendMessage(chat_id, '{}개를 찾았습니다.'.format(len(select_list)), reply_markup=keyboard)


def chat_popular_step2(chat_id, url):
    torrent = torrent_info_from_url(url)

    # 묻지 않고 바로 다운로드 시작 (2020.01.12)
    chat_add_magnet(chat_id=chat_id, magnet=torrent['magnet'], subject=torrent['subject'], size=torrent['size'])

    # # 토렌트 정보를 보여주고 진짜로 다운로드 받을거냐고 물어야 함
    # callback_key = get_md5(torrent['magnet'])
    # db_set_data(key=callback_key, type='MAGNET', data=torrent['magnet'])
    #
    # msg = '{}\n * 크기: {}\n * 생성일자: {}\n다운로드 받을까요?'.format(
    #     torrent['subject'], torrent['size'], torrent['timestr'].strftime('%Y-%m-%d'))
    #
    # select_list = list()
    # select_list.append([InlineKeyboardButton(text='네', callback_data=callback_key),
    #                     InlineKeyboardButton(text='아니오', callback_data='Nothing')])
    # keyboard = InlineKeyboardMarkup(inline_keyboard=select_list)
    # bot.sendMessage(chat_id, msg, reply_markup=keyboard)

    return


def chat_files(chat_id, nas_path=None):
    config = get_config()

    if nas_path is None:
        nas_path = config['DOWNLOAD_PATH']

    logger.info('Download path listing for {}'.format(nas_path))

    dir_list = list()
    file_list = ''
    file_cnt = 0

    files, error = nas_files(nas_path)
    if error:
        bot.sendMessage(chat_id, '뭔가 오류가 발생했습니다\n{}'.format(error))
        return

    db_open_cursor()

    for file in files:
        if file['isDirectory']:
            logger.debug(file)
            callback_key = get_md5(file['path'])
            db_set_data(key=callback_key, type='DIRECTORY', data=file['path'])
            dir_list.append([InlineKeyboardButton(text=file['filename'], callback_data=callback_key)])
        else:
            file_cnt += 1
            file_list += '{}) {} ({})\n'.format(file_cnt, file['filename'], file['size'])

    db_commit_cursor()

    if dir_list:
        keyboard = InlineKeyboardMarkup(inline_keyboard=dir_list)
        bot.sendMessage(chat_id, '{}에는 {}개의 폴더와 {}개의 파일이 있습니다.'.format(nas_path, len(dir_list), file_cnt),
                        reply_markup=keyboard)
    if file_list:
        bot.sendMessage(chat_id, file_list)


def on_chat_message(msg):
    config = get_config()
    content_type, chat_type, chat_id = glance(msg)
    logger.info('New message: content_type=[{}] chat_type=[{}] chat_id=[{}]'.format(content_type, chat_type, chat_id))

    # VALID_CHAT_USER가 공란이면 최초 채팅상대를 허용 목록에 등록한다.
    if 'VALID_CHAT_USERS' not in config or not config['VALID_CHAT_USERS']:
        logger.info('첫 대화 상대를 허용 목록에 추가합니다. chat_id: {}'.format(chat_id))
        set_config({'VALID_CHAT_USERS': [chat_id]})
    elif chat_id not in config['VALID_CHAT_USERS']:
        bot.sendMessage(chat_id, '서비스를 이용할 수 없습니다.\n관리자에게 chat_id ({}) 등록을 요청하세요'.format(chat_id))
        return

    if content_type == 'text':
        user_input = msg['text'].strip()
        logger.info('User input: {}'.format(user_input))

        if user_input == '/start' or user_input == '/help':
            user_interactions(chat_id=chat_id, action='clear')
            chat_start(chat_id)
            return

        elif user_input.startswith('/search'):
            if user_input == '/search':
                user_interactions(chat_id=chat_id, action='set_status', status='wait_search_keyword')
                bot.sendMessage(chat_id, '검색어를 입력하세요')
            else:
                keyword = ' '.join(user_input.split(' ')[1::])
                chat_search(chat_id, keyword)
            return
        elif user_input == '/list':
            chat_list(chat_id)

        elif user_input == '/popular':
            chat_popular(chat_id)

        elif user_input == '/files':
            chat_files(chat_id)

        elif user_input.startswith('/add'):
            if user_input == '/add':
                user_interactions(chat_id=chat_id, action='set_status', status='wait_magnet_link')
                bot.sendMessage(chat_id, '마그넷 주소를 입력하세요')
            else:
                magnet = ' '.join(user_input.split(' ')[1::])
                chat_add_magnet(chat_id=chat_id, magnet=magnet)
            return

        elif user_interactions(chat_id=chat_id, action='get_status') == 'wait_search_keyword':
            chat_search(chat_id, user_input)

        elif user_interactions(chat_id=chat_id, action='get_status') == 'wait_magnet_link':
            chat_add_magnet(chat_id=chat_id, magnet=user_input)

        elif user_input.startswith(r'magnet:?'):
            chat_add_magnet(chat_id=chat_id, magnet=user_input)

        else:
            chat_search(chat_id, user_input)
    else:
        bot.sendMessage(chat_id, '이해할 수 없는 요청입니다.')


def on_callback_query(msg):
    query_id, from_id, query_data = glance(msg, flavor='callback_query')
    logger.debug('Callback Query: {} {} {}'.format(query_id, from_id, query_data))

    bot.answerCallbackQuery(query_id, text='Got it')

    if msg == 'Nothing':
        return

    type, data = db_get_data(query_data)

    if type == 'TORRENT':
        chat_search_step2(from_id, data)  # data -> torrent dict
    elif type == 'MAGNET':
        chat_add_magnet(chat_id=from_id, magnet=data)  # data -> magnet link
    elif type == 'POPULAR':
        chat_popular_step2(from_id, data)  # data -> torrent page url
    elif type == 'DIRECTORY':
        chat_files(from_id, data)  # data -> path of nas directory


def init_bot():
    global bot
    config = get_config()
    bot = Bot(config['BOT_TOKEN'])
    logger.info('Telegram bot is ready >>> {}'.format(bot.getMe()))
    MessageLoop(bot, {'chat': on_chat_message, 'callback_query': on_callback_query}).run_as_thread()


def main():
    init_log()
    init_bot()
    init_db()

    while True:
        sleep(10)


if __name__ == '__main__':
    main()
