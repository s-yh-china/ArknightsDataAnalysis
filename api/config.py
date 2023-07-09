# -*- coding: utf-8 -*-
import json
import os


class ada_config:
    version = 'v3.0.0'
    database_version = 'v2.0.0'
    config = {
        "version": "{}".format(version),
        "database": {
            "type": "sqlite3",
            "sqlite3": {
                "filename": "ak_server.db"
            },
            "mysql": {
                "host": "",
                "user": "",
                "password": "",
                "database": ""
            },
            "database_version": "{}".format(database_version),
        },
        "web": {
            "host": "127.0.0.1",
            "port": 8900,
            "debug": True,
            "hostname": "",
        },
        "data": {
            "luckyrank_pool": "标准寻访"
        }
    }

    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        if not os.path.exists(self.config_file):
            self.update_config()
            print('初始化 {} 完成，请前往完成相关配置！'.format(self.config_file))
            exit(1)
        else:
            self.check_version()
            self.load_config()

    def update_config_version(self, local_config):
        if local_config.get('version') == 'v2.0.0':
            local_config['version'] = 'v2.0.1'
        if local_config.get('version') == 'v2.0.1':
            local_config['version'] = 'v2.1.0'
        if local_config.get('version') == 'v2.1.0':
            force_refresh = {
                "enabled": 0
            }
            local_config['force_refresh'] = force_refresh
            local_config['version'] = 'v2.1.1'
        if local_config.get('version') == 'v2.1.1':
            del local_config['accounts']
            local_config['version'] = 'v2.2.0'
        if local_config.get('version') == 'v2.3.0':
            web = {
                "host": "127.0.0.1",
                "port": 8900,
                "debug": True
            }
            local_config['web'] = web
            local_config['version'] = 'v2.4.0'
        if local_config.get('version') == 'v2.4.0':
            local_config['web']['hostname'] = ''
            local_config['version'] = 'v2.4.1'
        if local_config.get('version') == 'v2.4.1':
            del local_config['push']
            del local_config['accounts']
            del local_config['force_refresh']
            data = {
                "luckyrank_pool": "标准寻访"
            }
            local_config['data'] = data
            local_config['version'] = 'v3.0.0'
        self.config = local_config
        self.update_config()

    def check_version(self):
        with open(self.config_file, encoding='utf-8') as json_file:
            local_config = json.load(json_file)
        if not local_config.get('version') == self.version:
            self.update_config_version(local_config)

    def load_config(self):
        with open(self.config_file, encoding='utf-8') as json_file:
            self.config = json.load(json_file)
        return self.config

    def update_config(self):
        with open(self.config_file, 'w', encoding='utf-8') as json_file:
            json.dump(self.config, json_file, indent=4, ensure_ascii=False)

    def load_config_database(self):
        self.load_config()
        database_config = self.config.get('database')
        database_type = database_config.get('type')
        database_type_list = ['sqlite3', 'mysql']
        if not database_type in database_type_list:
            exit("ERROR: DATABASE_TYPE must be in {}".format(database_type_list))
        type_config = database_config.get(database_type)
        return database_type, type_config, database_config.get('database_version', 'v0.0.0')
