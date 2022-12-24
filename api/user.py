from ast import Pass
from flask_login import UserMixin
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm

from .model import *


def create_user(username, password):
    user = DBUser.get_or_create(username=username, defaults={'password': password})[0]
    UserSettings.get_or_create(user=user, defaults={'nickname': username})


def get_user(username):
    user = DBUser.get_or_none(DBUser.username == username)
    if user is not None:
        UserSettings.get_or_create(user=user, defaults={'nickname': username})
    return user


class User(UserMixin):
    def __init__(self, user):
        self.dbuser = user
        self.username = user.username
        self.password = user.password
        self.id = user.id
    
    def verify_password(self, password):
        if self.password is None:
            return False
        if self.password == password:
            return True
        return False
    
    def add_acc(self, acc_uid):
        acc = Account.get_or_none(Account.uid == acc_uid)
        if acc is not None:
            acc.owner = self.dbuser
            acc.save()

    def get_accs_token(self):
        accs_token = []
        for ark_acc in self.dbuser.ark_accs:
            accs_token.append(ark_acc.token)
        return accs_token

    def get_id(self):
        return self.id
    
    def get_settings(self):
        return UserSettings.get_settings(self.dbuser)

    def clear_data(self):
        accounts = Account.select().filter(owner=self.dbuser)
        for account in accounts:
            PayRecord.delete().where(PayRecord.account == account).execute()
            records = OperatorSearchRecord.select().filter(account=account)
            for record in records:
                OSROperator.delete().where(OSROperator.record == record).execute()
            OperatorSearchRecord.delete().where(OperatorSearchRecord.account == account).execute()
        Account.delete().where(Account.owner == self.dbuser).execute()
        UserSettings.delete().where(UserSettings.user == self.dbuser).execute()

        return True

    @staticmethod
    def get(user_id):
        if not user_id:
            return None
        user = DBUser.get_or_none(DBUser.id == user_id)
        return user


class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired()])
    password = PasswordField('密码', validators=[DataRequired()])


class RegisterForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired()])
    password1 = PasswordField('密码', validators=[DataRequired()])
    password2 = PasswordField('重复密码', validators=[DataRequired()])
