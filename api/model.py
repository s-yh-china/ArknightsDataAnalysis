# -*- coding: utf-8 -*-
from peewee import *
from playhouse.migrate import *
from .config import ada_config

database_proxy = Proxy()


class BaseModel(Model):
    class Meta:
        database = database_proxy


class DBUser(BaseModel):
    authenticated = BooleanField(default=False)
    username = CharField(max_length=20, unique=True)
    password = CharField(max_length=30)
    accept_disclaimers = BooleanField(default=False)

    def is_authenticated(self):
        return self.authenticated
    
    def is_active(self):
        return True
    
    def get_id(self):
        return self.id
    
    def is_anonymous(self):
        return False


class Account(BaseModel):
    uid = CharField(max_length=20, unique=True)
    nickname = CharField(max_length=50)
    token = CharField(max_length=300)
    owner = ForeignKeyField(DBUser, backref='ark_accs', null=True)
    channel = CharField(max_length=2)


class OSRPool(BaseModel):
    name = CharField(max_length=20, unique=True)
    type = CharField()


class OperatorSearchRecord(BaseModel):
    account = ForeignKeyField(Account, backref='records')
    time = DateTimeField()
    pool = ForeignKeyField(OSRPool, backref='records')


class OSROperator(BaseModel):
    name = CharField(max_length=10)
    rarity = IntegerField()
    is_new = BooleanField()
    index = IntegerField()
    record = ForeignKeyField(OperatorSearchRecord, backref='operators')


class PayRecord(BaseModel):
    name = CharField()
    pay_time = DateTimeField()
    account = ForeignKeyField(Account, backref='pay_records')
    platform = CharField()
    order_id = CharField(unique=True)
    amount = IntegerField()


class UserSettings(BaseModel):
    user = ForeignKeyField(DBUser, backref='user_settings')
    is_statistics = BooleanField(default=True)
    is_lucky_rank = BooleanField(default=False)
    is_display_name = BooleanField(default=False)
    is_display_full = BooleanField(default=False)
    private_qq = CharField(max_length=20, null=True)
    is_display_nick = BooleanField(default=False)
    nickname = CharField(max_length=20, unique=True)
    is_auto_gift = BooleanField(default=False)

    def get_nickname(self):
        if self.nickname == '':
            self.nickname = self.user.username
            self.save()
        return self.nickname

    @staticmethod
    def get_settings(user):
        return UserSettings.get_or_create(user=user, defaults={'nickname': user.username})[0]

        
class DiamondRecord(BaseModel):
    account = ForeignKeyField(Account, backref='diamond_records')
    operation = CharField()
    platform = CharField()
    operate_time = DateTimeField()
    before = IntegerField()
    after = IntegerField()


class GiftRecord(BaseModel):
    account = ForeignKeyField(Account, backref='gift_records')
    time = DateTimeField()
    code = CharField()
    name = CharField()


def update_database_version(a_config, database_version, mgrt):
    if database_version == 'v0.0.0':
        database_version = 'v1.0.0'
        migrate(
            mgrt.add_column(table='DBUser',column_name='accept_disclaimers',field=BooleanField(default=False)),
        )
    if database_version == 'v1.0.0':
        database_version = 'v1.1.0'
        migrate(
            mgrt.add_column(table='UserSettings',column_name='is_auto_gift',field=BooleanField(default=False)),
        )
    a_config.config['database']['database_version'] = database_version
    a_config.update_config()

    
a_config = ada_config()
database_type, database_type_config, database_version = a_config.load_config_database()
if database_type == 'sqlite3':
    db_name = database_type_config.get('filename')
    db = SqliteDatabase(db_name)
    mgrt = SqliteMigrator(db)
if database_type == 'mysql':
    db_host = database_type_config.get('host')
    db_user = database_type_config.get('user')
    db_pass = database_type_config.get('password')
    db_name = database_type_config.get('database')
    db = MySQLDatabase(db_name, host=db_host, user=db_user, passwd=db_pass, port=3306)
    mgrt = MySQLMigrator(db)
    
if database_version != a_config.database_version:
    update_database_version(a_config, database_version, mgrt)

database_proxy.initialize(db)
database_proxy.create_tables([DBUser, Account, OSRPool, OperatorSearchRecord, OSROperator, PayRecord, UserSettings, DiamondRecord])
