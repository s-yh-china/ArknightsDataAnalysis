from flask import Blueprint, request, redirect, url_for, render_template
from flask_login import current_user, login_required

disclaimers_blue = Blueprint('disclaimers', __name__, url_prefix='/disclaimers')


@disclaimers_blue.before_app_request
def not_disclaimers():
    if current_user.is_authenticated and not current_user.accept_disclaimers:
        if request.path not in ['/disclaimers/', '/logout']:
            return redirect(url_for('disclaimers.disclaimers'))


@disclaimers_blue.route('/', methods=['POST', 'GET'])
@login_required
def disclaimers():
    if request.method == 'POST':
        if request.form.get('accept'):
            current_user.accept_disclaimers = True
            current_user.save()
            return redirect(url_for('index'))

    return render_template('disclaimers.html', user=current_user)
