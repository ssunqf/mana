#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
import asyncio
from flask_bootstrap import Bootstrap
from flask import Flask, request, render_template, flash, redirect
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length

from app.config import Config
from util.database import Torrent
from util.categories import categories

app = Flask(__name__)
app.config.from_object(Config)

bootstrap = Bootstrap(app)

class SearchForm(FlaskForm):
    query = StringField('Query',
                        validators=[DataRequired(message='输入关键词。'),
                                    Length(1, 100, message='长度请限制在100字符内。')])
    category = SelectField('Category', choices= [('', '')] + list(zip(categories, categories)))
    submit = SubmitField('GO')


db_client = Torrent()
loop = asyncio.get_event_loop()


@app.route('/', methods=['GET', 'POST'])
def index():
    searchForm = SearchForm()
    if searchForm.validate_on_submit():
        return redirect('/search?q=%s' % searchForm.query.data)
    return render_template('index.html', form=searchForm)


@app.route('/search', methods=['GET', 'POST'])
def search():
    query = request.args.get('q', None)
    category = request.args.get('category', None)
    print(query, category)
    searchForm = SearchForm()

    if query is None:
        return redirect('/')
    if searchForm.validate_on_submit():
        print('search for {}, {}'.format(searchForm.query.data, searchForm.category.data))
        return redirect('/search?q=%s&category=%s' % (searchForm.query.data, searchForm.category.data))

    if category and len(category) > 0:
        results = loop.run_until_complete(db_client.search(query.lower(), category=category))
    else:
        results = loop.run_until_complete(db_client.search(query.lower()))

    return render_template('search.html', form=searchForm, results=results)


@app.route('/magnet', methods=['GET', 'POST'])
def magnet():
    infohash = request.args.get('infohash', None)

    searchForm = SearchForm()
    if searchForm.validate_on_submit():
        return redirect('/search?q=%s' % searchForm.query.data)

    if not infohash or len(infohash) != 40:
        flash('infohash参数错误', category='error')

        return render_template('index.html', form=searchForm)

    data = loop.run_until_complete(db_client.get_by_infohash(infohash))

    return render_template(
        'magnet.html',
        data=data)

if __name__ == '__main__':
    app.run(port=5000, debug=True)