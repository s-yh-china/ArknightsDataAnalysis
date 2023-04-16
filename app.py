import uuid
import os.path
from flask import Flask, redirect, request, url_for
from flask import render_template, send_from_directory
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from flask_caching import Cache


import api.data
from api import *

app = Flask(__name__)

cache = Cache(app=app, config={'CACHE_TYPE': 'FileSystemCache', 'CACHE_DIR': 'cache'})

app.secret_key = 'secret_rianng.cn_8023_{}'.format(uuid.uuid1())

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

hostname = ada_config().config.get('web').get('hostname')
if hostname == '':
    hostname = None


@app.before_request
def host_check():
    if hostname and request.host != hostname:
        return redirect('http://' + hostname + request.path, code=301)
    return None


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    emsg = None
    if form.validate_on_submit():
        username = form.username.data
        password1 = form.password1.data
        password2 = form.password2.data
        user_info = get_user(username)
        if user_info is None:
            if password1 == password2:
                create_user(username, password1)
                register_user_info = get_user(username)
                register_user = User(register_user_info)
                login_user(register_user)
                return redirect(url_for('index'))
            else:
                emsg = 'Different password.'
        else:
            user = User(user_info)
            if user.verify_password(password1):
                login_user(user)
                return redirect(url_for('index'))
            emsg = 'Username exists.'
    return render_template('register.html', form=form, emsg=emsg)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    emsg = None
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user_info = get_user(username)
        if user_info is None:
            emsg = 'Wrong username or password.'
        else:
            user = User(user_info)
            if user.verify_password(password):
                login_user(user)
                return redirect(request.args.get('next') or url_for('index'))
            else:
                emsg = 'Wrong username or password.'
    return render_template('login.html', form=form, emsg=emsg)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/cleardata', methods=['GET', 'POST'])
@login_required
def clear_data():
    if request.method == 'GET':
        return redirect(url_for('user_settings'))
    user = User(current_user)
    possword = request.form.get('password')
    if user.verify_password(possword):
        cache.delete('user_accs_{}'.format(user.username))
        user.clear_data()
        return redirect('/')
    else:
        return redirect(url_for('user_settings'))


@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    accs_info = get_user_accs()
    
    if request.method == 'GET':
        addnew = request.args.get('addnew')
        if addnew is not None:
            return render_template('index.html', accounts=accs_info, add_new=addnew, user=current_user)
        else:
            return render_template('index.html', accounts=accs_info, user=current_user)
    else:
        token = request.form.get('token')
        a_api = ada_api(token, only_read=True)
        if a_api.account is not None:
            acc_info = a_api.get_account_info()
            return render_template('index.html', accounts=accs_info, new_acc_info=acc_info, user=current_user)
        else:
            return render_template('index.html', accounts=accs_info, new_acc_info={'None': token}, user=current_user)


@app.route('/api/acc/add', methods=['POST', 'GET'])
@login_required
def add_acc():
    if request.method == 'GET':
        return redirect('/') 
    token = request.form.get('token')
    a_api = ada_api(token)
    acc_info = a_api.get_account_info()
    user = User(current_user)
    user.add_acc(acc_info['uid'])
    cache.delete('user_accs_{}'.format(user.username))
    return redirect(url_for('index', addnew=acc_info['nickName']))


@app.route('/analyze/refresh', methods=['POST', 'GET'])
@login_required
def refresh_ada():
    if request.method == 'GET':
        return redirect('/') 
    token = request.form.get('token')
    a_api = ada_api(token)
    return redirect('/')


@app.route('/analyze/refresh/force', methods=['POST', 'GET'])
@login_required
def refresh_force_ada():
    if request.method == 'GET':
        return redirect('/') 
    token = request.form.get('token')
    a_api = ada_api(token, force_refresh=True)
    return redirect('/')


@app.route('/analyze', methods=['POST', 'GET'])
@login_required
def analyze_results():
    if request.method == 'GET':
        return redirect('/') 
    token = request.form.get('token')

    accs_info = get_user_accs()
    a_api = ada_api(token, only_read=True)
    a_info = a_api.get_all_info()
    return render_template('analysis.html', info=a_info, accounts=accs_info, user=current_user)


@app.route('/analyze/pool', methods=['POST', 'GET'])
@login_required
def analyze_pool_results():
    if request.method == 'GET':
        return redirect('/')
    token = request.form.get('token')
    pool = request.form.get('pool')

    accs_info = get_user_accs()
    a_api = ada_api(token, only_read=True)
    a_info = {
        'acc_info': a_api.get_account_info(),
        'osr_info': a_api.get_pool_osr_info(pool)
    }
    return render_template('analysis_pool.html', info=a_info, accounts=accs_info, user=current_user)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/robots.txt')
def robots():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'robots.txt')

@app.route('/statistics', methods=['POST', 'GET'])
@login_required
def statistics():
    accs_info = get_user_accs()
    statistics_info = cache.get('statistics')
    if not statistics_info:
      statistics_info = api.data.get_statistics()
      cache.set('statistics', statistics_info, timeout=3600)
    return render_template('statistics.html', accounts=accs_info, user=current_user, info=statistics_info)


@app.route('/statistics/pool', methods=['POST', 'GET'])
@login_required
def statistics_pool():
    if request.method == 'GET':
        return redirect('/')
    pool = request.form.get('pool')
    accs_info = get_user_accs()
    
    statistics_info = cache.get('statistics_pool_{}'.format(pool))
    if not statistics_info:
      statistics_info = api.data.get_pool_statistics(pool)
      cache.set('statistics_pool_{}'.format(pool), statistics_info, timeout=3600)
    return render_template('statistics_pool.html', accounts=accs_info, user=current_user, info=statistics_info)


@app.route('/settings')
@login_required
def user_settings():
    accs_info = get_user_accs()
    settings_info = get_user_settings_info()
    return render_template('settings.html', accounts=accs_info, user=current_user, settings=settings_info)


@app.route('/settings/modify', methods=['GET', 'POST'])
@login_required
def user_settings_modify():
    if request.method == 'GET':
        return redirect(url_for('user_settings'))
    a_user_settings = User(current_user).get_settings()

    is_statistics = request.form.get('statistics')
    is_lucky_rank = request.form.get('lucky_rank')
    is_display_name = request.form.get('display_name')
    is_display_full = request.form.get('display_full')
    private_qq = request.form.get('private_qq')
    nickname = request.form.get('nickname')
    is_display_nick = request.form.get('display_nick')
    if is_statistics:
        if is_statistics == 'true':
            a_user_settings.is_statistics = True
        elif is_statistics == 'false':
            a_user_settings.is_statistics = False
    elif is_lucky_rank:
        if is_lucky_rank == 'true':
            a_user_settings.is_lucky_rank = True
        elif is_lucky_rank == 'false':
            a_user_settings.is_lucky_rank = False
    elif is_display_name:
        if is_display_name == 'true':
            a_user_settings.is_display_name = True
        elif is_display_name == 'false':
            a_user_settings.is_display_name = False
    elif is_display_full:
        if is_display_full == 'true':
            a_user_settings.is_display_full = True
        elif is_display_full == 'false':
            a_user_settings.is_display_full = False
    elif private_qq:
        if private_qq.isdigit() and 5 < len(private_qq) < 20:
            a_user_settings.private_qq = private_qq
    elif nickname:
        if not has_bad_char(nickname) and 0 < len(nickname) < 20:
            o_nickname = UserSettings.select().filter(nickname=nickname)
            if len(o_nickname) == 0:
                a_user_settings.nickname = nickname
    elif is_display_nick:
        if is_display_nick == 'true':
            a_user_settings.is_display_nick = True
        elif is_display_nick == 'false':
            a_user_settings.is_display_nick = False

    a_user_settings.save()
    return redirect(url_for('user_settings'))


@app.route('/luckyrank', methods=['GET', 'POST'])
@login_required
def lucky_rank():
    accs_info = get_user_accs()
    lucky_info = cache.get('luckyrank')
    if not lucky_info:
      lucky_info = api.data.get_lucky_rank()
      cache.set('luckyrank', lucky_info, timeout=3600)
    return render_template('lucky_rank.html', accounts=accs_info, user=current_user, info=lucky_info)


@app.route('/diamond', methods=['POST', 'GET'])
@login_required
def diamond_record():
    if request.method == 'GET':
        return redirect('/') 
    token = request.form.get('token')

    accs_info = get_user_accs()
    a_api = ada_api(token, only_read=True)
    a_info = a_api.get_diamond_record()
    return render_template('diamond.html', info=a_info, accounts=accs_info, user=current_user)


@app.route('/author', methods=['GET'])
@login_required
def author_page():
    accs_info = get_user_accs()
    return render_template('author.html', accounts=accs_info, user=current_user)


def get_user_accs():
    user = User(current_user)
    accs_info = cache.get('user_accs_{}'.format(user.username))
    
    if not accs_info:
      accs_token = user.get_accs_token()
      accs_info = []
      for acc_token in accs_token:
        a_api = ada_api(acc_token, only_read=True)
        acc_info = a_api.get_account_info()
        accs_info.append(acc_info)
      cache.set('user_accs_{}'.format(user.username), accs_info, timeout=600)

    return accs_info


def get_user_settings_info():
    a_user_settings = User(current_user).get_settings()
    settings_info = {
        'is_statistics': '开启' if a_user_settings.is_statistics else '关闭',
        'is_lucky_rank': '开启' if a_user_settings.is_lucky_rank else '关闭',
        'is_display_name': '开启' if a_user_settings.is_display_name else '关闭',
        'is_display_full': '开启' if a_user_settings.is_display_full and a_user_settings.is_display_name else '关闭',
        'private_qq': api.data.f_hide_mid(a_user_settings.private_qq) if a_user_settings.private_qq is not None else '',
        'is_display_nick': '开启' if a_user_settings.is_display_nick else '关闭',
        'nickname': a_user_settings.get_nickname(),
    }
    return settings_info


def has_bad_char(info):
    bad_char = ["'", '~', '!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '+', '-', '/', '\\', '<', '>', '''"''', '{',
                '}', '[', ']', '.', ',', ' ']
    for i in info:
        if i in bad_char:
            return True
    return False


if __name__ == '__main__':
    web_config = ada_config().config.get('web')
    debug = web_config.get('debug')
    port = web_config.get('port')
    host = web_config.get('host')
    if debug:
        host = "127.0.0.1"

    if not os.path.isfile('templates/activity.html'):
        file = open('templates/activity.html', 'w')
        file.close()

    app.run(debug=debug, port=port, host=host)
