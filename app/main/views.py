import gc
import threading
import os
import sys

from flask import abort, current_app, redirect, render_template, session, url_for
from flask_login import login_required, current_user

from . import main
from .. import db

from .forms import NameForm
from .charts import *

PROJECT_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@main.route('/index')
def minimal_index():

    return render_template('/minimal/index.html')


@main.route('/dashboard')
@login_required
def minimal_dashboard():

    last_update_time = "2019-02-21"

    summary = {}
    summary['sections'] = [{
        "section_name":
        "累计数据",
        "rows": [[{
            "data_name": "累计申请件数",
            "data_value": 12345,
            'color': 'redbrown'
        }, {
            "data_name": "累计放款金额(万)",
            "data_value": 1002333,
            'color': 'blue'
        }, {
            "data_name": "目前在库金额(亿)",
            "data_value": 801234,
            'color': 'greensea'
        }, {
            "data_name": "累计放款时收入(万)",
            "data_value": 23456,
            'color': 'slategray'
        }]]
    }, {
        "section_name":
        "实时数据",
        "rows": [[{
            "data_name": "当日申请件数",
            "data_value": 123,
            'color': 'redbrown',
            "href": '/day_report#day_apply'
        }, {
            "data_name": "当日放款金额(万)",
            "data_value": 3000,
            'color': 'blue',
            "href": '/day_report#day_loan_amount'
        }, {
            "data_name": "当日放款件均(万)",
            "data_value": 15,
            'color': 'greensea',
            "href": '/day_report#day_loan_average'
        }, {
            "data_name": "当日放款时收入(万)",
            "data_value": 100,
            'color': 'slategray',
            "href": '/day_report#day_income'
        }, {
            "data_name": "当日审批通过率",
            "data_value": "79%",
            'color': 'redbrown',
            "href": '/day_report#day_review'
        }, {
            "data_name": "当日签约率",
            "data_value": "74%",
            'color': 'orange',
            "href": '/day_report#day_sign'
        }], [{
            "data_name": "当月申请件数",
            "data_value": 2333,
            'color': 'redbrown',
            'href': '#bar_apply_month_bill'
        }, {
            "data_name": "当月放款金额(万)",
            "data_value": 2333,
            'color': 'blue',
            'href': '#bar_loan_month_amount'
        }, {
            "data_name": "当月放款件均(万)",
            "data_value": 12.3,
            'color': 'greensea',
            'href': '#bar_loan_month_amount_average'
        }, {
            "data_name": "当月放款时收入(万)",
            "data_value": 2000,
            'color': 'slategray',
            'href': '#bar_loan_month_income'
        }, {
            "data_name": "当月审批通过率",
            "data_value": "80%",
            'color': 'redbrown',
            'href': '#bar_review_month_pass_rate'
        }, {
            "data_name": "当月签约率",
            "data_value": "75%",
            'color': 'orange',
            'href': '#bar_review_month_sign_rate'
        }]]
    }]

    dashboard_charts = []

    return render_template(
        '/minimal/dashboard.html',
        collection=summary,
        charts=dashboard_charts,
        last_update_time=last_update_time)


@main.errorhandler(404)
def page_not_found(e):
    return render_template('/minimal/page404.html'), 404


@main.errorhandler(500)
def internal_server_error(e):
    return render_template('/minimal/page500.html'), 500


@main.route('/day_report')
@login_required
def minimal_day_report():

    last_update_time = "2019-02-21"

    summary = {}
    summary['sections'] = [{
        "section_name":
        "当日数据",
        "rows": [[{
            "data_name": "当日申请件数",
            "data_value": 123,
            'color': 'redbrown',
            "href": '#day_apply'
        }, {
            "data_name": "当日放款金额(万)",
            "data_value": 3000,
            'color': 'blue',
            "href": '#day_loan_amount'
        }, {
            "data_name": "当日放款件均(万)",
            "data_value": 15,
            'color': 'greensea',
            "href": '#day_loan_average'
        }, {
            "data_name": "当日放款时收入(万)",
            "data_value": 100,
            'color': 'slategray',
            "href": '#day_income'
        }, {
            "data_name": "当日审批通过率",
            "data_value": "79%",
            'color': 'redbrown',
            "href": '#day_review'
        }, {
            "data_name": "当日签约率",
            "data_value": "74%",
            'color': 'orange',
            "href": '#day_sign'
        }]]
    }]

    day_charts = [{
        "name":
        "申请数据",
        "id":
        'day_apply',
        "charts": [{
            "width": 12,
            "offset": 0,
            "content": day_apply_bill().render_embed(),
            "id": 'day_apply_bill'
        }]
    }, {
        "name":
        "放款数据",
        "id":
        'day_loan',
        "charts": [{
            "width": 6,
            "offset": 0,
            "content": day_loan_amount().render_embed(),
            "id": 'day_loan_amount'
        }, {
            "width": 6,
            "offset": 0,
            "content": day_loan_average().render_embed(),
            "id": 'day_loan_average'
        }]
    }, {
        "name":
        "收入数据",
        "id":
        'day_income',
        "charts": [{
            "width": 6,
            "offset": 0,
            "content": day_loan_income().render_embed(),
            "id": 'day_loan_income'
        }]
    }, {
        "name":
        "审批数据",
        "id":
        'day_review',
        "charts": [{
            "width": 6,
            "offset": 0,
            "content": day_review().render_embed(),
            "id": 'day_loan_income'
        }]
    }, {
        "name":
        "签约数据",
        "id":
        'day_sign',
        "charts": [{
            "width": 6,
            "offset": 0,
            "content": day_sign().render_embed(),
            "id": 'day_loan_income'
        }]
    }]

    return render_template(
        '/minimal/report/day_report.html',
        report_kind="当日",
        last_update_time=last_update_time,
        collection=summary,
        charts=day_charts)


@main.route('/month_report')
@login_required
def minimal_month_report():

    last_update_time = "2019-02-21"
    month = "2019-02"

    summary = {}
    summary['sections'] = [{
        "section_name":
        "当月数据",
        "rows": [[{
            "data_name": "当月申请件数",
            "data_value": 2333,
            'color': 'redbrown',
            'href': '#bar_apply_month_bill'
        }, {
            "data_name": "当月放款金额(万)",
            "data_value": 2333,
            'color': 'blue',
            'href': '#bar_loan_month_amount'
        }, {
            "data_name": "当月放款件均(万)",
            "data_value": 12.3,
            'color': 'greensea',
            'href': '#bar_loan_month_amount_average'
        }, {
            "data_name": "当月放款时收入(万)",
            "data_value": 2000,
            'color': 'slategray',
            'href': '#bar_loan_month_income'
        }, {
            "data_name": "当月审批通过率",
            "data_value": "80%",
            'color': 'redbrown',
            'href': '#bar_review_month_pass_rate'
        }, {
            "data_name": "当月签约率",
            "data_value": "75%",
            'color': 'orange',
            'href': '#bar_review_month_sign_rate'
        }]]
    }]

    month_charts = []

    return render_template(
        '/minimal/report/day_report.html',
        report_kind="每月",
        last_update_time=last_update_time,
        select_month=month,
        collection=summary,
        charts=month_charts)
