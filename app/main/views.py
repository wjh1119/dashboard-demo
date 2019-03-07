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


@main.route('/home')
def minimal_home():

    return render_template('/minimal/index.html')

@main.route('/')
@login_required
def minimal_root():

    return redirect(
        url_for('main.minimal_home'))


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
            'color': 'redbrown',
            "href": '/month_report#monthly_apply_bill'
        }, {
            "data_name": "累计放款金额(万)",
            "data_value": 1002333,
            'color': 'blue',
            "href": '/month_report#monthly_loan_amount'
        }, {
            "data_name": "累计放款时收入(万)",
            "data_value": 23456,
            'color': 'slategray',
            "href": '/day_report#day_apply'
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
            'href': '/month_report#month_apply_bill'
        }, {
            "data_name": "当月放款金额(万)",
            "data_value": 2333,
            'color': 'blue',
            'href': '/month_report#month_loan_amount'
        }, {
            "data_name": "当月放款件均(万)",
            "data_value": 12.3,
            'color': 'greensea',
            'href': '/month_report#month_loan_average'
        }, {
            "data_name": "当月放款时收入(万)",
            "data_value": 2000,
            'color': 'slategray',
            'href': '/month_report#month_loan_income'
        }, {
            "data_name": "当月审批通过率",
            "data_value": "80%",
            'color': 'redbrown',
            'href': '/month_report#month_review'
        }, {
            "data_name": "当月签约率",
            "data_value": "75%",
            'color': 'orange',
            'href': '/month_report#month_sign'
        }]]
    }]

    dashboard_charts = [{
        "name":
        "总体情况",
        "id":
        'day_apply',
        "charts": [{
            "width": 12,
            "offset": 0,
            "content": dashboard_loan_amount().render_embed(),
            "id": 'dashboard_loan_amount'
        }]
    }]

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
            'href': '#month_apply_bill'
        }, {
            "data_name": "当月放款金额(万)",
            "data_value": 2333,
            'color': 'blue',
            'href': '#month_loan_amount'
        }, {
            "data_name": "当月放款件均(万)",
            "data_value": 12.3,
            'color': 'greensea',
            'href': '#month_loan_average'
        }, {
            "data_name": "当月放款时收入(万)",
            "data_value": 2000,
            'color': 'slategray',
            'href': '#month_loan_income'
        }, {
            "data_name": "当月审批通过率",
            "data_value": "80%",
            'color': 'redbrown',
            'href': '#month_review'
        }, {
            "data_name": "当月签约率",
            "data_value": "75%",
            'color': 'orange',
            'href': '#month_sign'
        }]]
    }]

    month_charts = [{
        "name":
        "本月数据",
        "id":
        'month',
        "charts": [{
            "width": 6,
            "offset": 0,
            "content": month_apply_bill().render_embed(),
            "id": 'month_apply_bill'
        },{
            "width": 6,
            "offset": 0,
            "content": month_loan_amount().render_embed(),
            "id": 'month_loan_amount'
        },{
            "width": 6,
            "offset": 0,
            "content": month_loan_average().render_embed(),
            "id": 'month_loan_average'
        },{
            "width": 6,
            "offset": 0,
            "content": month_loan_income().render_embed(),
            "id": 'month_loan_income'
        },{
            "width": 6,
            "offset": 0,
            "content": month_review().render_embed(),
            "id": 'month_review'
        },{
            "width": 6,
            "offset": 0,
            "content": month_sign().render_embed(),
            "id": 'month_sign'
        }]
    }, {
        "name":
        "每月数据",
        "id":
        'monthly',
        "charts": [{
            "width": 6,
            "offset": 0,
            "content": monthly_apply_bill().render_embed(),
            "id": 'monthly_apply_bill'
        },{
            "width": 6,
            "offset": 0,
            "content": monthly_loan_amount().render_embed(),
            "id": 'monthly_loan_amount'
        },{
            "width": 6,
            "offset": 0,
            "content": monthly_loan_average().render_embed(),
            "id": 'monthly_loan_average'
        },{
            "width": 6,
            "offset": 0,
            "content": monthly_loan_income().render_embed(),
            "id": 'monthly_loan_income'
        },{
            "width": 6,
            "offset": 0,
            "content": monthly_review().render_embed(),
            "id": 'monthly_review'
        },{
            "width": 6,
            "offset": 0,
            "content": monthly_sign().render_embed(),
            "id": 'monthly_sign'
        }]
    }]

    return render_template(
        '/minimal/report/day_report.html',
        report_kind="每月",
        last_update_time=last_update_time,
        select_month=month,
        collection=summary,
        charts=month_charts)
