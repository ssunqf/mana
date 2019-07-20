#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
import asyncio
from flask_bootstrap import Bootstrap
from flask import Flask, jsonify, request, render_template, flash, redirect, Markup
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length

from app.config import Config
from flask_sqlalchemy import SQLAlchemy
from database import Torrent
from categories import categories

app = Flask(__name__)
app.config.from_object(Config)

bootstrap = Bootstrap(app)
db = SQLAlchemy(app)


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
    query = request.args.get('q', '')
    searchForm = SearchForm()
    if searchForm.validate_on_submit():
        print('search for {}'.format(searchForm.query.data))
        return redirect('/search?q=%s' % searchForm.query.data)

    results = loop.run_until_complete(db_client.search(query.lower()))


    return render_template('search.html', form=searchForm, results=results)


if __name__ == '__main__':
    app.run(port=5000, debug=True)