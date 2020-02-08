#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
import importlib
from datetime import datetime

from flask import Flask, request, render_template, flash, redirect, url_for
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
from util.douban import KEY_TEMPLATE, resources, fetch_data
from util.torrent import build_dir_tree
from util.utils import fetch_trackers

app = Flask(__name__)
app.config.from_object(Config)

db_client = Torrent()
cache = Cache(app)
bootstrap = Bootstrap(app)

scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()


class SearchForm(FlaskForm):
    query = StringField('Query',
                        validators=[DataRequired(message='输入关键词。'),
                                    Length(1, 100, message='长度请限制在100字符内。')])
    category = SelectField('Category', choices=[('', '全部')] + categories)
    submit = SubmitField('GO')


scheduler.add_job(id='fetch trackers', func=lambda: fetch_trackers(cache), trigger='cron', day='*', jitter=60 * 60, next_run_time=datetime.now())
scheduler.add_job(id='fetch douban', func=lambda: fetch_data(cache), trigger='cron', day='*', jitter=60 * 60, next_run_time=datetime.now())

render_kwargs = {'import': importlib.import_module, 'resources': resources}


@app.route('/', methods=['GET', 'POST'])
def index():
    searchForm = SearchForm()
    if searchForm.validate_on_submit():
        return redirect('/search?query=%s&category=%s&limit=20' % (searchForm.query.data, searchForm.category.data))
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
        return redirect('/search?query=%s&category=%s&limit=20' % (searchForm.query.data, searchForm.category.data))

    data = cache.get(KEY_TEMPLATE % (type, tag))
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
        return redirect('/search?query=%s&category=%s&limit=20' % (query, category))

    kwargs = {}
    if category and len(category) > 0:
        kwargs['category'] = category

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
        return redirect('/search?query=%s&category=%s&limit=20' % (query, category))

    if not infohash or len(infohash) != 40:
        flash('infohash参数错误', category='error')

        return render_template('index.html', form=searchForm)

    data = db_client.get_by_infohash(infohash)
    if len(data) == 0:
        return render_template('not_exist.html', form=searchForm, infohash=infohash, **render_kwargs)

    data = data[0]

    data['dir'] = build_dir_tree(data['metainfo']).json()

    data['keywords'] = extract_keywords(data['metainfo'])

    trackers = cache.get('best_trackers')
    if trackers is None:
        trackers = []
    magnet_url = '&'.join(['magnet:?xt=urn:btih:' + data['infohash']] + trackers)

    return render_template('magnet.html', form=searchForm, data=data, magnet=magnet_url, **render_kwargs)


if __name__ == '__main__':
    app.run(port=5000, debug=True)
