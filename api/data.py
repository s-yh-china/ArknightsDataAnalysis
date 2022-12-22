# -*- coding: utf-8 -*-
from operator import is_
import requests, json, datetime
from urllib.parse import quote
from .model import *


def get_json_token(myjson):
    try:
        json_object = json.loads(myjson).get('data').get('content')
    except ValueError:
        return None
    return json_object


def token_format(token):
    real_token = token
    json_token = get_json_token(token)
    if json_token is not None:
        real_token = json_token
    return real_token.replace(' ', '')


def get_statistics():
    pay_total_money = 0
    pay_records = PayRecord.select()
    for pay_record in pay_records:
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
        '6': [], '5': [], '4': [], '3': [],
        'count': {'6': 0, '5': 0, '4': 0, '3': 0}
    }
    osr_number_month = {}
    osr_pool = []

    records = OperatorSearchRecord.select().order_by(OperatorSearchRecord.time)
    pools = OSRPool.select()

    for pool in pools:
        osr_number[pool.name] = 0
        osr_pool.append(pool.name)

    for record in records:
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

            osr_lucky[str(rarity)].append(osr_lucky['count'][str(rarity)])
            osr_lucky['count'][str(rarity)] = 0

    osr_lucky_avg = {'6': [], '5': [], '4': [], '3': []}

    for r in range(3, 7):
        osr_lucky_avg[str(r)].extend(osr_lucky[str(r)])
    for r in range(3, 7):
        if len(osr_lucky_avg[str(r)]) == 0:
            osr_lucky_avg[str(r)] = 0
        else:
            osr_lucky_avg[str(r)] = sum(osr_lucky_avg[str(r)]) / len(osr_lucky_avg[str(r)])

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
        '6': [], '5': [], '4': [], '3': [],
        'count': {'6': 0, '5': 0, '4': 0, '3': 0}
    }
    osr_number_day = {}
    osr_six_lucky = {
        'all': 0
    }

    pool = OSRPool.get_or_create(name=pool_name, defaults={'type': '标准寻访'})[0]
    records = OperatorSearchRecord.select().filter(pool=pool).order_by(OperatorSearchRecord.time)

    for record in records:
        pool = record.pool.name
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

            if rarity == 6:
                if name not in osr_six_lucky:
                    osr_six_lucky[name] = 0
                osr_six_lucky[name] += 1
                osr_six_lucky['all'] += 1

            osr_lucky[str(rarity)].append(osr_lucky['count'][str(rarity)])
            osr_lucky['count'][str(rarity)] = 0

    osr_lucky_avg = {'6': [], '5': [], '4': [], '3': []}

    for r in range(3, 7):
        osr_lucky_avg[str(r)].extend(osr_lucky[str(r)])
    for r in range(3, 7):
        if len(osr_lucky_avg[str(r)]) == 0:
            osr_lucky_avg[str(r)] = 0
        else:
            osr_lucky_avg[str(r)] = sum(osr_lucky_avg[str(r)]) / len(osr_lucky_avg[str(r)])

    osr_number_day_sorted = {}
    for item in sorted(osr_number_day.keys(), reverse=True):
        osr_number_day_sorted[item] = osr_number_day[item]

    osr_six_lucky_sorted = {}
    for key, value in sorted(osr_six_lucky.items(), key=lambda x:x[1], reverse=True):
        osr_six_lucky_sorted[key] = value

    info = {
        'time': {
            'start_time': str(OperatorSearchRecord.select().filter(pool=pool).order_by(OperatorSearchRecord.time).limit(1)[0].time),
            'end_time': str(OperatorSearchRecord.select().filter(pool=pool).order_by(OperatorSearchRecord.time.desc()).limit(1)[0].time)
        },
        'pool': pool_name,
        'osr_number': osr_number,
        'osr_lucky_avg': osr_lucky_avg,
        'osr_number_day': osr_number_day_sorted,
        'osr_six_lucky': osr_six_lucky_sorted
    }
    return info

class ada_data():
    class request_http():
        def get(url):
            r = requests.get(url)
            if r.status_code == 200:
                return r.content
            return 'ERROR'

        def post(url, data):
            r = requests.post(url, data=data)
            if r.status_code == 200:
                return r.content
            return 'ERROR'
    
    url_user_info = 'https://as.hypergryph.com/u8/user/info/v1/basic'
    url_cards_record = 'http://ak.hypergryph.com/user/api/inquiry/gacha'
    url_pay_record = 'https://as.hypergryph.com/u8/pay/v1/recent'
    not_standard_pool = ['浊酒澄心', '跨年欢庆·相逢', '新年特别十连寻访']

    def __init__(self, token):
        self.token = token_format(token)
    
    def fetch_data(self, force_refresh=False):
        if not self.fetch_account_info():
            exit(1)
        self.fetch_osr(force_refresh)
        # self.fetch_osr_from_local()
        self.fetch_pay_record()

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
        nickName = user_info_source.get('nickName')
        channelId = str(user_info_source.get('channelMasterId'))
        account = Account.get_or_create(uid=uid, defaults={'nickname': nickName, 'token': self.token, 'channel': channelId})[0]
        if not account.token == self.token:
            account.token = self.token
            account.save()
        self.account = account
        return True

    def fetch_osr(self, flag_all=False):
        def get_osr_by_page(page):
            url_cards_record_page = '{}?page={}&token={}&channelId={}'.format(self.url_cards_record, page, quote(self.token, safe=""), self.account.channel)
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
                osr, f = OperatorSearchRecord.get_or_create(account=self.account, time=time, defaults={'pool': osr_pool})
                if osr_pool != osr.pool:
                    osr.pool = osr_pool
                    osr.save()
                if f:
                    t_index = 0
                    for chars_item in chars:
                        name = chars_item['name']
                        rarity = chars_item['rarity'] + 1
                        is_new = chars_item['isNew']
                        osr_operator = OSROperator.create(name=name, rarity=rarity, is_new=is_new, index=t_index, record=osr)
                        t_index += 1

    def fetch_osr_from_local(self):
        with open('local.json', encoding='utf-8') as json_file:
            local_osr = json.load(json_file)
        for ts in local_osr:
            time = datetime.datetime.fromtimestamp(int(ts))
            pool = local_osr[ts]['p']
            pool_type = '常规卡池'
            if pool in self.not_standard_pool:
                pool_type = pool
            osr_pool = OSRPool.get_or_create(name=pool, defaults={'type': pool_type})[0]
            osr = OperatorSearchRecord.create(account=self.account, time=time, pool=osr_pool)
            chars = local_osr[ts]['c']
            t_index = 0
            for chars_item in chars:
                name = chars_item[0]
                rarity = chars_item[1] + 1
                is_new = bool(chars_item[2])
                osr_operator = OSROperator.create(name=name, rarity=rarity, is_new=is_new, index=t_index, record=osr)
                t_index += 1

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

    def get_osr_info(self):
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
        for record in records:
            pool = record.pool.name
            pool_type = record.pool.type
            if not pool in osr_number:
                osr_number[pool] = 0
            if not pool_type in osr_lucky:
                osr_lucky[pool_type] = {
                    '6': [], '5': [], '4': [], '3': [],
                    'count': {'6': 0, '5': 0, '4': 0, '3': 0}
                }
            if pool not in osr_pool:
                osr_pool.insert(0, pool)

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
                    osr_lucky[pool_type]['count'][str(r)] += 1

                osr_lucky[pool_type][str(rarity)].append(osr_lucky[pool_type]['count'][str(rarity)])
                osr_lucky[pool_type]['count'][str(rarity)] = 0


        osr_lucky_avg = {'6': [], '5': [], '4': [], '3': []}
        osr_lucky_count = {}
        for osr_lucky_pool in osr_lucky:
            for r in range(3, 7):
                osr_lucky_avg[str(r)].extend(osr_lucky[osr_lucky_pool][str(r)])
            osr_lucky_count[osr_lucky_pool] = osr_lucky[osr_lucky_pool]['count']
        for r in range(3, 7):
            if len(osr_lucky_avg[str(r)]) == 0:
                osr_lucky_avg[str(r)] = 0
            else:
                osr_lucky_avg[str(r)] = sum(osr_lucky_avg[str(r)]) / len(osr_lucky_avg[str(r)])

        osr_number_month_sorted = {}
        for item in sorted(osr_number_month.keys(), reverse=True):
            osr_number_month_sorted[item] = osr_number_month[item]

        if (len(records) > 0):
            osr_info = {
                'time': {
                    'start_time': str(self.account.records.order_by(OperatorSearchRecord.time).limit(1)[0].time),
                    'end_time': str(self.account.records.order_by(OperatorSearchRecord.time.desc()).limit(1)[0].time)
                },
                'osr_number': osr_number,
                'osr_lucky_avg': osr_lucky_avg,
                'osr_lucky_count': osr_lucky_count,
                'osr_number_month': osr_number_month_sorted,
                'osr_pool': osr_pool
            }
        else:
            osr_info = {
                'time': {
                    'start_time': 'N/A',
                    'end_time': 'N/A'
                },
                'osr_number': {
                    'total': {
                        'all': -1,
                        '3': 0,
                        '4': 0,
                        '5': 0,
                        '6': 0
                    }
                },
                'osr_lucky_avg': osr_lucky_avg,
                'osr_lucky_count': osr_lucky_count,
                'osr_number_month': osr_number_month_sorted,
                'osr_pool': osr_pool
            }
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
                osr_lucky_avg[str(r)] = sum(osr_lucky_avg[str(r)]) / len(osr_lucky_avg[str(r)])

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
