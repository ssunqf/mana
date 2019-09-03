#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
import importlib

from flask import Flask, request, render_template, flash, redirect
from flask_apscheduler import APScheduler
from flask_bootstrap import Bootstrap
from flask_caching import Cache
from flask_paginate import Pagination, get_page_args
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length

from parser.parse import extract_keywords
from service.config import Config
from util.categories import categories
from util.database2 import Torrent
from util.resource import resources, fetch_data
from util.torrent import build_dir_tree
from util.utils import best_trackers, fetch_trackers

db_client = Torrent(host='207.148.124.42')

app = Flask(__name__)

'''
SELF = "'self'"
talisman = Talisman(
    app,
    content_security_policy={
        'default-src': SELF,
        'img-src': [
            SELF,
            '*.doubanio.com',
            'img.icons8.com'
        ],
        'script-src': [
            SELF,
            'cdn.jsdelivr.net',
        ],
        'style-src': [
            SELF,
            'www.jqueryscript.net',
            'fonts.googleapis.com',
            'netdna.bootstrapcdn.com'
        ],
    },
    content_security_policy_nonce_in=['script-src'],
    feature_policy={
        'geolocation': '\'none\'',
    }
)
'''

# Talisman(app, content_security_policy=GOOGLE_CSP_POLICY)

app.config.from_object(Config)

scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

bootstrap = Bootstrap(app)


class SearchForm(FlaskForm):
    query = StringField('Query',
                        validators=[DataRequired(message='输入关键词。'),
                                    Length(1, 100, message='长度请限制在100字符内。')])
    category = SelectField('Category', choices= [('', '全部')] + categories)
    submit = SubmitField('GO')


scheduler.add_job(id='fetch trackers', func=fetch_trackers, trigger='cron', day='*', jitter=60 * 60)
scheduler.add_job(id='fetch douban', func=fetch_data, trigger='cron', day='*', jitter=60 * 60)

render_kwargs = { 'import' : importlib.import_module , 'resources': resources}


@app.route('/', methods=['GET', 'POST'])
def index():
    searchForm = SearchForm()
    if searchForm.validate_on_submit():
        return redirect('/search?query=%s&category=%s' % (searchForm.query.data, searchForm.category.data))
    return render_template('index.html', form=searchForm, **render_kwargs)


@app.route('/resource', methods=['GET', 'POST'])
def resource():
    type = request.values.get('type', 'hot')
    tag = request.values.get('tag', None)
    page = int(request.values.get('page', '1'))
    if tag is None:
        tag = resources[type][0].name
    searchForm = SearchForm()
    if searchForm.validate_on_submit():
        return redirect('/search?query=%s&category=%s' % (searchForm.query.data, searchForm.category.data))

    data = resources[type][tag].data
    return render_template('resource.html', form=searchForm, type=type, tag=tag, page=page, data=data, **render_kwargs)


@app.route('/search', methods=['GET', 'POST'])
def search():
    query = request.values.get('query', None)
    category = request.values.get('category', None)
    adult = request.values.get('adult', None)

    page, limit, offset = get_page_args(page_parameter='page', per_page_parameter='limit')

    searchForm = SearchForm()
    searchForm.query.data = query
    searchForm.category.data = category

    if query is None:
        return redirect('/')
    if searchForm.validate_on_submit():
        query = request.form.get('query')
        category = request.form.get('category')
        return redirect('/search?query=%s&category=%s' % (query, category))

    kwargs = {}
    if category and len(category) > 0:
        kwargs['category']=category

    if adult and len(adult):
        kwargs['adult'] = adult

    results = db_client.search(query, offset=offset, limit=limit, **kwargs)

    pagination = Pagination(page=page,
                            per_page=limit if limit else 20,
                            total=results[0]['total'] if len(results) > 0 else 0,
                            display_msg='''显示<b>{start}</b>到<b>{end}</b>的{record_name}，最多显示<b>{total}个</b>''',
                            record_name='磁力信息',
                            css_framework='bootstrap4')

    return render_template('search.html',
                           form=searchForm, results=results, pagination=pagination, **render_kwargs)


@app.route('/magnet', methods=['GET', 'POST'])
def magnet():
    infohash = request.values.get('infohash', None)

    searchForm = SearchForm()
    if searchForm.validate_on_submit():
        query = request.form.get('query')
        category = request.form.get('category')
        return redirect('/search?query=%s&category=%s' % (query, category))

    if not infohash or len(infohash) != 40:
        flash('infohash参数错误', category='error')

        return render_template('index.html', form=searchForm)

    data = db_client.get_by_infohash(infohash)
    if len(data) == 0:
        return render_template('not_exist.html', form=searchForm, infohash=infohash)

    data = data[0]

    data['dir'] = build_dir_tree(data['metainfo']).json()

    data['keywords'] = extract_keywords(data['metainfo'])

    magnet_url = '&'.join(['magnet:?xt=urn:btih:' + data['infohash']] + best_trackers)

    return render_template('magnet.html', form=searchForm, data=data, magnet=magnet_url, **render_kwargs)


if __name__ == '__main__':
    app.run(port=5000, debug=True)