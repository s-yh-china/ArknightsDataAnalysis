# -*- coding: utf-8 -*-

from api import *
import datetime

a_config = ada_config()

push_when_changed_enabled = a_config.load_config_push_when_changed()
force_refresh_enabled = a_config.load_config_force_refresh()

errorlog = open('errlog.txt', 'a')
print('data sync start')

for account in Account.select():
    token = account.token
    try:
        a_api = ada_api(token, force_refresh=force_refresh_enabled)
        a_info = a_api.get_account_info()
        if UserSettings.get_settings(account.owner).is_auto_gift:
            a_api.auto_get_gift()
            print('{}(uid:{}) gift get succees'.format(a_info.get('nickName'), a_info.get('uid')))
        print('{}(uid:{}) sync succees'.format(a_info.get('nickName'), a_info.get('uid')))
    except:
        a_user = account.owner
        qq = ''
        if a_user is not None:
            qq = UserSettings.get_settings(a_user).private_qq
        failMes = '{}(uid:{},qq:{}) sync fail by token({})'.format(account.nickname, account.uid, qq, account.token)
        print(failMes)
        errorlog.write(datetime.datetime.now().strftime('[%Y-%m-%d %H:%M:%S] ') + failMes + '\n')

print('data sync compelet')
errorlog.close()
