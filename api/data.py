# -*- coding: utf-8 -*-
from operator import is_
import requests, json, datetime
from urllib.parse import quote
from .model import *
import random


pool_not_up = ['【联合行动】特选干员定向寻访', '常驻标准寻访', '联合行动', '跨年欢庆·相逢', '定制寻访', '未知寻访', '中坚寻访', '中坚甄选']

def f_hide_mid(info, count=4, fix='*'):
    """
       #隐藏/脱敏 中间几位
       info 字符串
       count 隐藏位数
       fix 替换符号
    """
    if not info:
        return ''
    count = int(count)
    str_len = len(info)
    if str_len == 1:
        return info
    elif str_len == 2:
        ret_str = info[0] + '*'
    elif count == 1:
        mid_pos = int(str_len / 2)
        ret_str = info[:mid_pos] + fix + info[mid_pos + 1:]
    else:
        if str_len - 2 > count:
            if count % 2 == 0:
                if str_len % 2 == 0:
                    ret_str = info[:int(str_len / 2 - count / 2)] + count * fix + info[int(str_len / 2 + count / 2):]
                else:
                    ret_str = info[:int((str_len + 1) / 2 - count / 2)] + count * fix + info[int((
                                                                                                             str_len + 1) / 2 + count / 2):]
            else:
                if str_len % 2 == 0:
                    ret_str = info[:int(str_len / 2 - (count - 1) / 2)] + count * fix + info[int(str_len / 2 + (
                                count + 1) / 2):]
                else:
                    ret_str = info[:int((str_len + 1) / 2 - (count + 1) / 2)] + count * fix + info[
                                                                                              int((str_len + 1) / 2 + (
                                                                                                          count - 1) / 2):]
        else:
            ret_str = info[0] + fix * (str_len - 2) + info[-1]
    return ret_str


def get_json_token(myjson):
    try:
        json_object = json.loads(myjson).get('data').get('content')
    except:
        return None
    return json_object


def token_format(token):
    real_token = token
    json_token = get_json_token(token)
    if json_token is not None:
        real_token = json_token
    return real_token.replace(' ', '')


def get_all_pool():
    osr_pool = []
    for pool in OSRPool.select():
        osr_pool.append(pool.name)
    return osr_pool


def get_new_lucky_rank(pool_name):
    osr_lucky = {}
    enable_accounts = []

    pool = OSRPool.get_or_none(OSRPool.name == pool_name)

    empty_info = {
        'time': {
            'start_time': "None",
            'end_time': "None"
        },
        'lucky': [],
        'unlucky': [],
        'pool_name': pool_name
    }

    if not pool:
        return empty_info

    for account in Account.select():
        if account.owner is not None and UserSettings.get_settings(account.owner).is_lucky_rank:
            enable_accounts.append(account)
            osr_lucky[account] = {
                'six': 0,
                'count': 0
            }

    records = OperatorSearchRecord.select().where(OperatorSearchRecord.pool == pool).where(
        OperatorSearchRecord.account.in_(enable_accounts)).order_by(OperatorSearchRecord.time)

    if len(records) == 0:
        return empty_info

    for record in records:
        operators = record.operators
        account = record.account
        for operator in operators:
            osr_lucky[account]['count'] += 1
            if operator.rarity == 6:
                osr_lucky[account]['six'] += 1

    osr_lucky_avg = {}
    osr_lucky_name = {}
    for osr_account in osr_lucky:
        osr_user_settings = UserSettings.get_settings(osr_account.owner)

        if osr_user_settings.is_display_name:
            if osr_user_settings.is_display_full:
                osr_account_name = osr_account.nickname
            else:
                osr_account_name = f_hide_mid(osr_account.nickname, count=7)
        else:
            uidlen = len(osr_account.uid) - 1
            osr_account_name = '已匿名{}'.format((osr_account.uid[0: 2] + osr_account.uid[uidlen - 2: uidlen]))
        if osr_user_settings.is_display_nick:
            osr_account_name += ' ({})'.format(osr_user_settings.get_nickname())

        osr_lucky_name[osr_account] = osr_account_name

        if osr_lucky[osr_account]['six'] > 1:
            osr_lucky_avg[osr_account] = osr_lucky[osr_account]['count'] / osr_lucky[osr_account]['six']

    osr_lucky_rank = []
    osr_lucky_rank_index = 1
    osr_lucky_added = []
    for key, value in sorted(osr_lucky_avg.items(), key=lambda x: x[1], reverse=False):
        if osr_lucky_rank_index > 10:
            break
        player = {
            'rank': osr_lucky_rank_index,
            'nickname': osr_lucky_name[key],
            'number': value
        }
        osr_lucky_rank.append(player)
        osr_lucky_added.append(key)
        osr_lucky_rank_index += 1

    osr_unlucky_rank = []
    osr_unlucky_rank_index = 1
    for key, value in sorted(osr_lucky_avg.items(), key=lambda x: x[1], reverse=True):
        if osr_unlucky_rank_index > 10:
            break
        if key in osr_lucky_added:
            continue
        player = {
            'rank': osr_unlucky_rank_index,
            'nickname': osr_lucky_name[key],
            'number': value
        }
        osr_unlucky_rank.append(player)
        osr_unlucky_rank_index += 1

    info = {
        'time': {
            'start_time': str(records[0].time),
            'end_time': str(records[len(records) - 1].time)
        },
        'lucky': osr_lucky_rank,
        'unlucky': osr_unlucky_rank,
        'pool_name': pool_name
    }
    return info


def get_lucky_rank():
    osr_lucky = {}
    enable_accounts = []

    accounts = Account.select()
    for account in accounts:
        if account.available and account.owner is not None and UserSettings.get_settings(account.owner).is_lucky_rank:
            enable_accounts.append(account)
            osr_lucky[account] = {
                'six': 0,
                'count': 0
            }

    records = OperatorSearchRecord.select().order_by(OperatorSearchRecord.time)

    for record in records:
        if record.account not in enable_accounts:
            continue
        operators = record.operators
        account = record.account
        for operator in operators:
            osr_lucky[account]['count'] += 1
            if operator.rarity == 6:
                osr_lucky[account]['six'] += 1

    osr_lucky_avg = {}
    osr_lucky_name = {}
    for osr_account in osr_lucky:
        osr_user_settings = UserSettings.get_settings(osr_account.owner)

        if osr_user_settings.is_display_name:
            if osr_user_settings.is_display_full:
                osr_account_name = osr_account.nickname
            else:
                osr_account_name = f_hide_mid(osr_account.nickname, count=7)
        else:
            uidlen = len(osr_account.uid) - 1
            osr_account_name = '已匿名{}'.format((osr_account.uid[0: 2] + osr_account.uid[uidlen - 2: uidlen]))
        if osr_user_settings.is_display_nick:
            osr_account_name += ' ({})'.format(osr_user_settings.get_nickname())

        osr_lucky_name[osr_account] = osr_account_name

        if osr_lucky[osr_account]['six'] > 0:
            osr_lucky_avg[osr_account] = osr_lucky[osr_account]['count'] / osr_lucky[osr_account]['six']

    osr_lucky_rank = []
    osr_lucky_rank_index = 1
    osr_lucky_added = []
    for key, value in sorted(osr_lucky_avg.items(), key=lambda x: x[1], reverse=False):
        if osr_lucky_rank_index > 10:
            break
        if osr_lucky[key]['six'] < 3:
            continue
        player = {
            'rank': osr_lucky_rank_index,
            'nickname': osr_lucky_name[key],
            'number': value
        }
        osr_lucky_rank.append(player)
        osr_lucky_added.append(key)
        osr_lucky_rank_index += 1

    osr_unlucky_rank = []
    osr_unlucky_rank_index = 1
    for key, value in sorted(osr_lucky_avg.items(), key=lambda x: x[1], reverse=True):
        if osr_unlucky_rank_index > 10:
            break
        if key in osr_lucky_added:
            continue
        player = {
            'rank': osr_unlucky_rank_index,
            'nickname': osr_lucky_name[key],
            'number': value
        }
        osr_unlucky_rank.append(player)
        osr_unlucky_rank_index += 1

    info = {
        'time': {
            'start_time': str(OperatorSearchRecord.select().order_by(OperatorSearchRecord.time).limit(1)[0].time),
            'end_time': str(OperatorSearchRecord.select().order_by(OperatorSearchRecord.time.desc()).limit(1)[0].time)
        },
        'lucky': osr_lucky_rank,
        'unlucky': osr_unlucky_rank
    }
    return info


def get_statistics():
    pay_total_money = 0
    pay_records = PayRecord.select()
    for pay_record in pay_records:
        a_user = pay_record.account.owner
        if a_user is not None:
            if not UserSettings.get_settings(a_user).is_statistics:
                continue
        pay_total_money += pay_record.amount / 100

    osr_number = {
        'total': {
            'all': 0,
            '3': 0,
            '4': 0,
            '5': 0,
            '6': 0
        }
    }
    osr_lucky = {
        '6': 0, '5': 0, '4': 0, '3': 0,
        'count': {'6': 0, '5': 0, '4': 0, '3': 0}
    }
    osr_number_month = {}
    osr_pool = []

    osr_number['常驻标准寻访'] = 0
    osr_pool.append('常驻标准寻访')

    records = OperatorSearchRecord.select().order_by(OperatorSearchRecord.time)

    for i in range(len(records) - 1, -1, -1):
        pool = records[i].pool.name
        if pool not in osr_pool:
            osr_number[pool] = 0
            osr_pool.append(pool)

    for record in records:
        a_user = record.account.owner
        if a_user is not None:
            if not UserSettings.get_settings(a_user).is_statistics:
                continue
        else:
            continue

        pool = record.pool.name
        month = record.time.strftime('%Y-%m')
        if month not in osr_number_month:
            osr_number_month[month] = 0

        operators = record.operators
        for operator in operators:
            rarity = operator.rarity
            osr_number[pool] += 1
            osr_number['total']['all'] += 1
            osr_number['total'][str(rarity)] += 1
            osr_number_month[month] += 1

            for r in range(3, 7):
                osr_lucky['count'][str(r)] += 1
            osr_lucky[str(rarity)] += 1

    osr_lucky_avg = {'6': [], '5': [], '4': [], '3': []}

    for r in range(3, 7):
        if osr_lucky[str(r)] == 0:
            osr_lucky_avg[str(r)] = 0
        else:
            osr_lucky_avg[str(r)] = osr_lucky['count'][str(r)] / osr_lucky[str(r)]

    osr_number_month_sorted = {}
    for item in sorted(osr_number_month.keys(), reverse=True):
        osr_number_month_sorted[item] = osr_number_month[item]

    info = {
        'time': {
            'start_time': str(OperatorSearchRecord.select().order_by(OperatorSearchRecord.time).limit(1)[0].time),
            'end_time': str(OperatorSearchRecord.select().order_by(OperatorSearchRecord.time.desc()).limit(1)[0].time)
        },
        'osr_number': osr_number,
        'osr_lucky_avg': osr_lucky_avg,
        'pay_total_money': pay_total_money,
        'osr_number_month': osr_number_month_sorted,
        'osr_pool': osr_pool,
    }
    return info


def get_pool_statistics(pool_name):
    osr_number = {
        'all': 0,
        '3': 0,
        '4': 0,
        '5': 0,
        '6': 0
    }
    osr_lucky = {
        '6': 0, '5': 0, '4': 0, '3': 0,
        'count': {'6': 0, '5': 0, '4': 0, '3': 0}
    }
    osr_number_day = {}
    osr_six_lucky = {
        'all': 0
    }

    pool = OSRPool.get_or_create(name=pool_name)[0]
    records = OperatorSearchRecord.select().filter(pool=pool).order_by(OperatorSearchRecord.time)

    for record in records:
        a_user = record.account.owner
        if a_user is not None:
            if not UserSettings.get_settings(a_user).is_statistics:
                continue

        day = record.time.strftime('%Y-%m-%d')
        if day not in osr_number_day:
            osr_number_day[day] = 0

        operators = record.operators
        for operator in operators:
            rarity = operator.rarity
            name = operator.name
            osr_number['all'] += 1
            osr_number[str(rarity)] += 1
            osr_number_day[day] += 1

            for r in range(3, 7):
                osr_lucky['count'][str(r)] += 1
            osr_lucky[str(rarity)] += 1

            if rarity == 6:
                if name not in osr_six_lucky:
                    osr_six_lucky[name] = 0
                osr_six_lucky[name] += 1
                osr_six_lucky['all'] += 1

    osr_lucky_avg = {'6': [], '5': [], '4': [], '3': []}

    for r in range(3, 7):
        if osr_lucky[str(r)] == 0:
            osr_lucky_avg[str(r)] = 0
        else:
            osr_lucky_avg[str(r)] = osr_lucky['count'][str(r)] / osr_lucky[str(r)]

    osr_number_day_sorted = {}
    for item in sorted(osr_number_day.keys(), reverse=True):
        osr_number_day_sorted[item] = osr_number_day[item]

    osr_six_lucky_sorted = {}
    for key, value in sorted(osr_six_lucky.items(), key=lambda x: x[1], reverse=True):
        osr_six_lucky_sorted[key] = value

    info = {
        'time': {
            'start_time': str(
                OperatorSearchRecord.select().filter(pool=pool).order_by(OperatorSearchRecord.time).limit(1)[0].time),
            'end_time': str(
                OperatorSearchRecord.select().filter(pool=pool).order_by(OperatorSearchRecord.time.desc()).limit(1)[
                    0].time)
        },
        'pool': pool_name,
        'osr_number': osr_number,
        'osr_lucky_avg': osr_lucky_avg,
        'osr_number_day': osr_number_day_sorted,
        'osr_six_lucky': osr_six_lucky_sorted
    }
    return info


def recalculate_pool_up():
    pool_ups = {}

    for pool in OSRPool.select():
        pool_ups[pool] = []
        for up in pool.ups:
            pool_ups[pool].append(up.name)

    for operator in OSROperator.select():
        if operator.rarity == 6:
            if (operator.name in pool_ups[operator.record.pool]) ^ operator.up:
                operator.up = not operator.up
                operator.save()


def get_not_up_rank():
    osr_not_up = {}
    enable_accounts = []

    empty_info = {
        'time': {
            'start_time': "None",
            'end_time': "None"
        },
        'up': [],
        'not_up': [],
    }

    for account in Account.select():
        if account.owner is not None and UserSettings.get_settings(account.owner).is_lucky_rank:
            enable_accounts.append(account)
            osr_not_up[account] = {
                'six': 0,
                'not_up': 0
            }

    records = OperatorSearchRecord.select().where(
        OperatorSearchRecord.account.in_(enable_accounts)).order_by(OperatorSearchRecord.time)

    if len(records) == 0:
        return empty_info

    for record in records:
        if record.pool.name in pool_not_up:
            continue
        operators = record.operators
        account = record.account
        for operator in operators:
            if operator.rarity == 6:
                osr_not_up[account]['six'] += 1
                if not operator.up:
                    osr_not_up[account]['not_up'] += 1

    osr_not_up_avg = {}
    osr_not_up_name = {}
    for osr_account in osr_not_up:
        osr_user_settings = UserSettings.get_settings(osr_account.owner)

        if osr_user_settings.is_display_name:
            if osr_user_settings.is_display_full:
                osr_account_name = osr_account.nickname
            else:
                osr_account_name = f_hide_mid(osr_account.nickname, count=7)
        else:
            uidlen = len(osr_account.uid) - 1
            osr_account_name = '已匿名{}'.format((osr_account.uid[0: 2] + osr_account.uid[uidlen - 2: uidlen]))
        if osr_user_settings.is_display_nick:
            osr_account_name += ' ({})'.format(osr_user_settings.get_nickname())

        osr_not_up_name[osr_account] = osr_account_name

        if osr_not_up[osr_account]['six'] > 1:
            osr_not_up_avg[osr_account] = osr_not_up[osr_account]['not_up'] / osr_not_up[osr_account]['six']

    osr_not_up_rank = []
    osr_not_up_rank_index = 1
    osr_not_up_added = []
    for key, value in sorted(osr_not_up_avg.items(), key=lambda x: x[1], reverse=False):
        if osr_not_up_rank_index > 10:
            break
        player = {
            'rank': osr_not_up_rank_index,
            'nickname': osr_not_up_name[key],
            'number': value
        }
        osr_not_up_rank.append(player)
        osr_not_up_added.append(key)
        osr_not_up_rank_index += 1

    osr_up_rank = []
    osr_up_rank_index = 1
    for key, value in sorted(osr_not_up_avg.items(), key=lambda x: x[1], reverse=True):
        if osr_up_rank_index > 10:
            break
        if key in osr_not_up_added:
            continue
        player = {
            'rank': osr_up_rank_index,
            'nickname': osr_not_up_name[key],
            'number': value
        }
        osr_up_rank.append(player)
        osr_up_rank_index += 1

    info = {
        'time': {
            'start_time': str(records[0].time),
            'end_time': str(records[len(records) - 1].time)
        },
        'up': osr_up_rank,
        'not_up': osr_not_up_rank
    }
    return info


class ada_data:
    class request_http:
        @staticmethod
        def get(url):
            r = requests.get(url)
            if r.status_code == 200:
                return r.content
            return 'ERROR'

        @staticmethod
        def post(url, data):
            r = requests.post(url, data=data)
            if r.status_code == 200:
                return r.content
            return 'ERROR'

        @staticmethod
        def post_with_csrf(url, data, token):
            headers = {
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36 Edg/112.0.1722.58',
                'x-csrf-token': token,
                'cookie': 'csrf_token={}'.format(token),
                'content-type': 'application/json;charset=UTF-8'
            }
            r = requests.post(url, data=data, headers=headers)
            if r.status_code == 200:
                return r.content
            return 'ERROR'

    url_user_info = 'https://as.hypergryph.com/u8/user/info/v1/basic'
    url_cards_record = 'http://ak.hypergryph.com/user/api/inquiry/gacha'
    url_pay_record = 'https://as.hypergryph.com/u8/pay/v1/recent'
    url_diamond_record = 'https://ak.hypergryph.com/user/api/inquiry/diamond'
    url_gift_record = 'https://ak.hypergryph.com/user/api/gift/getExchangeLog'
    url_gift_get = 'https://ak.hypergryph.com/user/api/gift/exchange'
    not_standard_pool = ['浊酒澄心', '跨年欢庆·相逢', '定制寻访', '未知寻访']

    gift_codes = ['2023SPECIALCANDY']

    def __init__(self, token):
        self.token = token_format(token)
        self.account = None

    def fetch_data(self, force_refresh=False):
        if not self.fetch_account_info():
            exit(1)
        self.fetch_osr(force_refresh)
        # self.fetch_osr_from_local()
        self.fetch_pay_record()
        self.fetch_diamond_record()
        self.fetch_gift_record()

    def fetch_account_info(self):
        bili_payload = '''
        {{
            "token":"{}"
        }}    
        '''.format(self.token)
        if self.fetch_account_info_by(bili_payload):
            return True
        ark_payload = '''
        {{
            "appId": 1,
            "channelMasterId": 1,
            "channelToken": {{
                "token": "{}"
            }}
        }}
        '''.format(self.token)
        if self.fetch_account_info_by(ark_payload):
            return True
        print('ERROR: ada_data::fetch_account_info, token: {}'.format(self.token))
        return False

    def fetch_account_info_by(self, payload):
        source_from_server = self.request_http.post(self.url_user_info, payload)
        if source_from_server == 'ERROR':
            self.account = None
            return False
        user_info_source = json.loads(source_from_server).get('data')
        uid = user_info_source.get('uid')
        nick_name = user_info_source.get('nickName')
        channel_id = str(user_info_source.get('channelMasterId'))
        account = \
        Account.get_or_create(uid=uid, defaults={'nickname': nick_name, 'token': self.token, 'channel': channel_id})[0]

        need_save = False
        if not account.token == self.token:
            account.token = self.token
            need_save = True
        if not account.nickname == nick_name:
            account.nickname = nick_name
            need_save = True
        if not account.available:
            account.available = True
            need_save = True

        if need_save:
            account.save()

        self.account = account
        return True

    def fetch_osr(self, flag_all=False):
        def get_osr_by_page(page):
            url_cards_record_page = '{}?page={}&token={}&channelId={}'.format(self.url_cards_record, page,
                                                                              quote(self.token, safe=""),
                                                                              self.account.channel)
            source_from_server = self.request_http.get(url_cards_record_page)
            if source_from_server == 'ERROR':
                print('ERROR: ada_data::get_osr::get_osr_by_page, page: {}, token: {}'.format(page, self.token))
                exit(1)
            cards_record_page_source = json.loads(source_from_server)
            cards_record_page_data_list = cards_record_page_source.get('data').get('list')
            return cards_record_page_data_list

        last_time = None
        if self.account.records.count() != 0 and not flag_all:
            records = self.account.records.order_by(OperatorSearchRecord.time.desc()).limit(1)[0]
            last_time = records.time

        flag_outdate = False
        for page in range(1, 75):
            if flag_outdate == True:
                break
            osr_page_data = get_osr_by_page(page)
            if osr_page_data == []:
                break
            for osr_page_data_item in osr_page_data:
                ts = osr_page_data_item['ts']
                pool = osr_page_data_item['pool']
                chars = osr_page_data_item['chars']
                pool_type = '标准寻访'
                if pool in self.not_standard_pool:
                    pool_type = pool
                osr_pool = OSRPool.get_or_create(name=pool, defaults={'type': pool_type})[0]
                time = datetime.datetime.fromtimestamp(ts)
                if last_time is not None and time <= last_time:
                    flag_outdate = True
                    break
                osr, f = OperatorSearchRecord.get_or_create(account=self.account, time=time,
                                                            defaults={'pool': osr_pool})
                if osr_pool != osr.pool:
                    osr.pool = osr_pool
                    osr.save()
                if f:
                    t_index = 0
                    for chars_item in chars:
                        name = chars_item['name']
                        rarity = chars_item['rarity'] + 1
                        is_new = chars_item['isNew']
                        osr_operator = OSROperator.create(name=name, rarity=rarity, is_new=is_new, index=t_index,
                                                          record=osr)
                        t_index += 1

    def fetch_diamond_record(self):
        def get_diamond_by_page(page):
            url_diamond_record_page = '{}?page={}&token={}&channelId={}'.format(self.url_diamond_record, page,
                                                                                quote(self.token, safe=""),
                                                                                self.account.channel)
            source_from_server = self.request_http.get(url_diamond_record_page)
            if source_from_server == 'ERROR':
                print('ERROR: ada_data::get_diamond_record::get_diamond_by_page, page: {}, token: {}'.format(page,
                                                                                                             self.token))
                exit(1)
            diamond_record_page_source = json.loads(source_from_server)
            diamond_record_page_data_list = diamond_record_page_source.get('data').get('list')
            return diamond_record_page_data_list

        last_time = None
        if self.account.diamond_records.count() != 0:
            records = self.account.diamond_records.order_by(DiamondRecord.operate_time.desc()).limit(1)[0]
            last_time = records.operate_time

        flag_outdate = False
        for page in range(1, 15):
            if flag_outdate:
                break
            diamond_page_data = get_diamond_by_page(page)
            if diamond_page_data == []:
                break
            for diamond_page_data_item in diamond_page_data:
                ts = diamond_page_data_item['ts']
                operation = diamond_page_data_item['operation']
                changes = diamond_page_data_item['changes']
                time = datetime.datetime.fromtimestamp(ts)
                if last_time is not None and time <= last_time:
                    flag_outdate = True
                    break
                for changes_item in changes:
                    platform = changes_item['type']
                    before = changes_item['before']
                    after = changes_item['after']
                    DiamondRecord.get_or_create(
                        account=self.account,
                        operate_time=time,
                        defaults={
                            'operation': operation,
                            'platform': platform,
                            'before': before,
                            'after': after
                        }
                    )

    def fetch_pay_record(self):
        payload = None
        if self.account.channel == '1':
            payload = '''
            {{
                "appId": 1,
                "channelMasterId": 1,
                "channelToken": {{
                    "token": "{}"
                }}
            }}
            '''.format(self.token)
        elif self.account.channel == '2':
            payload = '''
            {{
                "token":"{}"
            }}    
            '''.format(self.token)
        source_from_server = self.request_http.post(self.url_pay_record, payload)
        if source_from_server == 'ERROR':
            print('ERROR: ada_data::fetch_pay_record, token: {}'.format(self.token))
            exit(1)
        pay_record_source = json.loads(source_from_server).get('data')
        for pay_record_item in pay_record_source:
            amount = pay_record_item['amount']
            pay_time = datetime.datetime.fromtimestamp(int(pay_record_item['payTime']))
            name = pay_record_item['productName']
            platform = pay_record_item['platform']
            order_id = pay_record_item['orderId']
            # print(pay_time, name, amount, platform, order_id)
            PayRecord.get_or_create(
                order_id=order_id,
                defaults={
                    'name': name,
                    'pay_time': pay_time,
                    'account': self.account,
                    'platform': platform,
                    'amount': amount
                }
            )

    def fetch_gift_record(self):
        url_gift_record = '{}?token={}&channelId={}'.format(self.url_gift_record, quote(self.token, safe=""),
                                                            self.account.channel)
        source_from_server = self.request_http.get(url_gift_record)
        if source_from_server == 'ERROR':
            print('ERROR: ada_data::fetch_gift_record, token: {}'.format(self.token))
            exit(1)
        gift_record_source = json.loads(source_from_server).get('data')
        for gift_record_item in gift_record_source:
            time = datetime.datetime.fromtimestamp(int(gift_record_item['ts']))
            name = gift_record_item['giftName']
            code = gift_record_item['code']
            GiftRecord.get_or_create(
                account=self.account,
                time=time,
                defaults={
                    'code': code,
                    'name': name
                }
            )

    def get_osr_info(self):
        osr_not_up = {
            'total': 0
        }
        osr_six = {
            'total': 0
        }

        osr_number = {
            'total': {
                'all': 0,
                '3': 0,
                '4': 0,
                '5': 0,
                '6': 0
            }
        }
        osr_lucky = {}
        osr_pool = []
        osr_number_month = {}
        records = self.account.records.order_by(OperatorSearchRecord.time)
        for i in range(len(records) - 1, -1, -1):
            pool = records[i].pool.name
            pool_type = records[i].pool.type
            if pool not in osr_number:
                osr_number[pool] = 0
            if pool_type not in osr_lucky:
                osr_lucky[pool_type] = {
                    '6': [], '5': [], '4': [], '3': [],
                    'count': {'6': 0, '5': 0, '4': 0, '3': 0}
                }
            if pool not in osr_pool:
                osr_pool.append(pool)
            if pool not in pool_not_up:
                if pool not in osr_not_up:
                    osr_not_up[pool] = 0
                if pool not in osr_six:
                    osr_six[pool] = 0
        for record in records:
            pool_type = record.pool.type
            pool_name = record.pool.name

            month = record.time.strftime('%Y-%m')
            if month not in osr_number_month:
                osr_number_month[month] = 0
            operators = record.operators
            for operator in operators:
                rarity = operator.rarity
                osr_number[pool_name] += 1
                osr_number['total']['all'] += 1
                osr_number['total'][str(rarity)] += 1
                osr_number_month[month] += 1

                for r in range(3, 7):
                    osr_lucky[pool_type]['count'][str(r)] += 1

                osr_lucky[pool_type][str(rarity)].append(osr_lucky[pool_type]['count'][str(rarity)])
                osr_lucky[pool_type]['count'][str(rarity)] = 0

                if pool_name not in pool_not_up:
                    if rarity == 6:
                        osr_six[pool_name] += 1
                        osr_six['total'] += 1
                        if not operator.up:
                            osr_not_up[pool_name] += 1
                            osr_not_up['total'] += 1

        osr_lucky_avg = {'6': [], '5': [], '4': [], '3': []}
        osr_lucky_count = {}
        osr_lucky_count_pool_num = {'6': 0, '5': 0, '4': 0, '3': 0}
        for osr_lucky_pool in osr_lucky:
            for r in range(3, 7):
                osr_lucky_avg[str(r)].extend(osr_lucky[osr_lucky_pool][str(r)])
                if osr_lucky[osr_lucky_pool]['count'][str(r)] != 0:
                    osr_lucky_avg[str(r)].append(osr_lucky[osr_lucky_pool]['count'][str(r)])
                    osr_lucky_count_pool_num[str(r)] += 1
            osr_lucky_count[osr_lucky_pool] = osr_lucky[osr_lucky_pool]['count']
        for r in range(3, 7):
            if (len(osr_lucky_avg[str(r)]) - osr_lucky_count_pool_num[str(r)]) <= 0:
                osr_lucky_avg[str(r)] = 0
            else:
                osr_lucky_avg[str(r)] = (sum(osr_lucky_avg[str(r)])) / (
                            len(osr_lucky_avg[str(r)]) - osr_lucky_count_pool_num[str(r)])

        osr_number_month_sorted = {}
        for item in sorted(osr_number_month.keys(), reverse=True):
            osr_number_month_sorted[item] = osr_number_month[item]

        osr_not_up_avg = {}
        for osr_not_up_pool in osr_not_up:
            osr_not_up_avg[osr_not_up_pool] = osr_not_up[osr_not_up_pool] / osr_six[osr_not_up_pool]

        osr_info = {
            'osr_lucky_avg': osr_lucky_avg,
            'osr_lucky_count': osr_lucky_count,
            'osr_number_month': osr_number_month_sorted,
            'osr_number': osr_number,
            'osr_pool': osr_pool,
            'osr_not_up_avg': osr_not_up_avg
        }
        if (len(records) > 0):
            osr_info['time'] = {
                'start_time': str(self.account.records.order_by(OperatorSearchRecord.time).limit(1)[0].time),
                'end_time': str(self.account.records.order_by(OperatorSearchRecord.time.desc()).limit(1)[0].time)
            }
        else:
            osr_info['time'] = {
                'start_time': 'N/A',
                'end_time': 'N/A'
            }
            osr_info['osr_number']['total']['all'] = 0
        return osr_info

    def get_pool_osr_info(self, pool_name):
        pool_type = '标准寻访'
        if pool_name in self.not_standard_pool:
            pool_type = pool_name
        pool = OSRPool.get_or_create(name=pool_name, defaults={'type': pool_type})[0]

        osr_number = {
            'all': 0,
            '3': 0,
            '4': 0,
            '5': 0,
            '6': 0
        }
        osr_lucky = {
            '6': [], '5': [], '4': [], '3': [],
            'count': {'6': 0, '5': 0, '4': 0, '3': 0}
        }
        osr_six_record = []
        osr_five_record = []
        osr_number_day = {}
        records = self.account.records.filter(pool=pool).order_by(OperatorSearchRecord.time)

        for record in records:
            day = record.time.strftime('%Y-%m-%d')
            if day not in osr_number_day:
                osr_number_day[day] = 0
            operators = record.operators
            for operator in operators:
                rarity = operator.rarity
                osr_number['all'] += 1
                osr_number[str(rarity)] += 1
                osr_number_day[day] += 1

                for r in range(3, 7):
                    osr_lucky['count'][str(r)] += 1

                if rarity == 6 or rarity == 5:
                    s_record = {
                        'time': str(record.time),
                        'count': osr_lucky['count'][str(r)],
                        'name': operator.name,
                        'is_new': operator.is_new,
                    }
                    if rarity == 6:
                        osr_six_record.insert(0, s_record)
                    elif rarity == 5:
                        osr_five_record.insert(0, s_record)

                osr_lucky[str(rarity)].append(osr_lucky['count'][str(rarity)])
                osr_lucky['count'][str(rarity)] = 0

        osr_lucky_avg = {'6': [], '5': [], '4': [], '3': []}

        for r in range(3, 7):
            osr_lucky_avg[str(r)].extend(osr_lucky[str(r)])
        for r in range(3, 7):
            if len(osr_lucky_avg[str(r)]) == 0:
                osr_lucky_avg[str(r)] = 0
            else:
                osr_lucky_avg[str(r)] = (sum(osr_lucky_avg[str(r)]) + osr_lucky['count'][str(r)]) / len(
                    osr_lucky_avg[str(r)])

        osr_number_day_sorted = {}
        for item in sorted(osr_number_day.keys(), reverse=True):
            osr_number_day_sorted[item] = osr_number_day[item]

        osr_info = {
            'pool': pool_name,
            'osr_number': osr_number,
            'osr_lucky_avg': osr_lucky_avg,
            'osr_number_day': osr_number_day_sorted,
            'osr_six_record': osr_six_record,
            'osr_five_record': osr_five_record
        }

        return osr_info

    def get_pay_record(self):
        pr_info = []
        total_money = 0
        pay_records = self.account.pay_records.order_by(PayRecord.pay_time.desc())
        for pay_record in pay_records:
            t_r = {
                'time': str(pay_record.pay_time),
                'name': pay_record.name,
                'amount': pay_record.amount / 100,
                'platform': 'IOS' if int(pay_record.platform) == 0 else 'Android'
            }
            pr_info.append(t_r)
            total_money += pay_record.amount / 100
        # print(pr_info)
        return total_money, pr_info

    def get_diamond_record(self):
        records = self.account.diamond_records.order_by(DiamondRecord.operate_time.desc())
        diamond_info = {}

        diamond_total_info = {
            'now': {
                'Android': 'N/A',
                'iOS': 'N/A'
            },
            'totalget': {
                'Android': 'N/A',
                'iOS': 'N/A'
            },
            'totaluse': {
                'Android': 'N/A',
                'iOS': 'N/A'
            },
            'typeget': {},
            'typeuse': {},
        }

        diamond_day_info = {}

        if (len(records) > 0):
            diamond_info['time'] = {
                'start_time': str(
                    self.account.diamond_records.order_by(DiamondRecord.operate_time).limit(1)[0].operate_time),
                'end_time': str(
                    self.account.diamond_records.order_by(DiamondRecord.operate_time.desc()).limit(1)[0].operate_time)
            }

            diamond_typeget_info = {}
            diamond_typeuse_info = {}

            for record in records:
                if (diamond_total_info['now'][record.platform] == 'N/A'):
                    diamond_total_info['now'][record.platform] = str(record.after) + ' 个'

                change = record.after - record.before

                if change < 0:
                    if diamond_total_info['totaluse'][record.platform] == 'N/A':
                        diamond_total_info['totaluse'][record.platform] = 0
                    if record.operation not in diamond_typeuse_info:
                        diamond_typeuse_info[record.operation] = 0

                    diamond_total_info['totaluse'][record.platform] += -change
                    diamond_typeuse_info[record.operation] += -change
                else:
                    if diamond_total_info['totalget'][record.platform] == 'N/A':
                        diamond_total_info['totalget'][record.platform] = 0
                    if record.operation not in diamond_typeget_info:
                        diamond_typeget_info[record.operation] = 0

                    diamond_total_info['totalget'][record.platform] += change
                    diamond_typeget_info[record.operation] += change

                day = record.operate_time.strftime('%Y-%m-%d')
                if day not in diamond_day_info:
                    diamond_day_info[day] = 1
                diamond_day_info[day] += change

            for platform in diamond_total_info['totaluse'].keys():
                if diamond_total_info['totaluse'][platform] != 'N/A':
                    diamond_total_info['totaluse'][platform] = str(diamond_total_info['totaluse'][platform]) + ' 个'
                if diamond_total_info['totalget'][platform] != 'N/A':
                    diamond_total_info['totalget'][platform] = str(diamond_total_info['totalget'][platform]) + ' 个'

            diamond_typeget_info_sorted = {}
            for key, value in sorted(diamond_typeget_info.items(), key=lambda x: x[1], reverse=True):
                diamond_typeget_info_sorted[key] = value
            diamond_total_info['typeget'] = diamond_typeget_info_sorted

            diamond_typeuse_info_sorted = {}
            for key, value in sorted(diamond_typeuse_info.items(), key=lambda x: x[1], reverse=True):
                diamond_typeuse_info_sorted[key] = value
            diamond_total_info['typeuse'] = diamond_typeuse_info_sorted


        else:
            diamond_info['time'] = {
                'start_time': 'N/A',
                'end_time': 'N/A'
            }

        diamond_info['total'] = diamond_total_info
        diamond_info['day'] = diamond_day_info

        return diamond_info

    def auto_gift_get(self):
        used_gift_code = []
        for gift_record in GiftRecord.select().filter(account=self.account):
            used_gift_code.append(gift_record.code)

        csrf_token = ''
        for char in random.sample('abcdefghijklmnopqrstuvwxyzABCDEFGHIGKLMNO{QRSTUYWXYZ-', 24):
            csrf_token += char
        for gift_code in self.gift_codes:
            if gift_code in used_gift_code:
                continue
            payload = '''
            {{
                "giftCode": "{}",
                "token": "{}",
                "channelId": {}
            }}
            '''.format(gift_code, self.token, self.account.channel)
            source_from_server = self.request_http.post_with_csrf(self.url_gift_get, payload, csrf_token)
            if source_from_server == 'ERROR':
                print('ERROR: ada_data::auto_gift_get, token: {}'.format(self.token))
                exit(1)
