# -*- coding: utf-8 -*-
from .config import *
from .data import *
from .user import *
from .model import DBUser


class ada_api():
    ################################
    # 初始化并将官网数据增量更新到数据库
    # params:
    #   token: token
    ################################
    def __init__(self, token, only_read=False, force_refresh=False):
        self.a_data = ada_data(token)
        if not only_read:
            self.a_data.fetch_data(force_refresh)
        else:
            self.a_data.fetch_account_info()
        self.account = self.a_data.account

    ################################
    # 显示当前用户数据
    # return:
    #   {
    #       "uid": "用户UID",
    #       "nickName": "昵称"
    #   }
    ################################
    def get_account_info(self):
        if self.account is None:
            acc_info = {
                'tokenAlive': False
            }
        else:
            acc_info = {
                'uid': self.account.uid,
                'nickName': self.account.nickname,
                'token': self.account.token,
                'tokenAlive': True
            }
        # print(acc_info)
        return acc_info

    ################################
    # 获取抽卡详细数据，即总计抽数，以及每个星级的抽数
    # return:
    #   {
    #       'time': {
    #           'start_time': "抽卡记录开始时间",
    #           'end_time': "抽卡记录结束时间"
    #       },
    #       'osr_number': "抽卡详细数据及各卡池抽卡次数"
    #       'osr_lucky_avg': "平均出货次数",
    #       'osr_lucky_count': "各卡池保底情况",
    #       'osr_six_record': "6星历史记录",
    #       'osr_number_month': "每月抽卡次数"
    #   }
    ################################
    def get_osr_info(self):
        osr_info = self.a_data.get_osr_info()
        return osr_info

    def get_pool_osr_info(self, pool):
        ors_info = self.a_data.get_pool_osr_info(pool)
        return ors_info

    ################################
    # 获取充值记录
    # return:
    #   'total_money': "重置总记录"
    #   'pr_info': [{
    #       'time': "时间"
    #       'name': "名称",
    #       'amount': "金额",
    #       'platform': "平台"
    #   },...]
    ################################
    def get_pay_record(self):
        total_money, pr_info = self.a_data.get_pay_record()
        return total_money, pr_info
    
    ################################
    # 获取所有信息
    ################################
    def get_all_info(self):
        osr_info = self.get_osr_info()
        acc_info = self.get_account_info()
        total_money, pay_info = self.get_pay_record()
        info = {
            'acc_info': acc_info,
            'osr_info': osr_info,
            'pay_info': {
                'total_money': total_money, 
                'pay_info': pay_info
            }
        }
        return info
        
    ################################
    # 获取源石信息
    ################################
    def get_diamond_record(self):
        diamond_record = self.a_data.get_diamond_record()
        acc_info = self.get_account_info()
        info = {
            'acc_info': acc_info,
            'diamond_record': diamond_record,
        }
        return info
        
    ################################
    # 自动领取礼包
    ################################
    def auto_get_gift(self):
        self.a_data.auto_gift_get()
