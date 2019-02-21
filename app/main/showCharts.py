# coding=utf-8
import copy
import numpy as np
import pandas as pd
from flask import Flask, render_template
import os
import sys

# # 修改第三方库的属性
# import pyecharts.conf as conf
# # 'C:\\Users\\JR1\\WJH\\获取系统数据\\templates\\pyecharts'
# conf.configure(echarts_template_dir=os.path.join(os.getcwd(),'templates','pyecharts'))
# from pyecharts import engine
# engine.CHART_CONFIG_FORMATTER = """
# window.onload = function() {{
#     setTimeout(function() {{
#         var myChart_{chart_id} = echarts.init(document.getElementById('{chart_id}'), '{theme}', {{renderer: '{renderer}'}});
#         {custom_function}
#         var option_{chart_id} = {options};
#         myChart_{chart_id}.setOption(option_{chart_id});
#         window.onresize = function() {{
#             myChart_{chart_id}.resize();
#         }};
#     }}, 1000);
# }};
# """
# engine.CHART_EVENT_FORMATTER = """"""

# 因timeline、grid无法使用use_theme，故更改此库的configure的默认全局主题
import pyecharts.conf as conf

from sys import getsizeof, getrefcount


def configure(
        jshost=None,
        hosted_on_github=None,
        echarts_template_dir=None,
        force_js_embed=None,
        output_image=None,
        global_theme="dark",
):
    """
    Config all items for pyecharts when use chart.render() or page.render().

    :param jshost: the host for echarts related javascript libraries
    :param echarts_template_dir: the directory for custom html templates
    :param force_js_embed: embed javascript in html file or not
    :param output_image: Non None value asks pyecharts to use
                         pyecharts-snapshots to render as image directly.
                         Values such as 'svg', 'jpeg', 'png' changes
                         chart presentation in jupyter notebook to those image
                         formats, instead of 'html' format.
    """
    if jshost:
        CURRENT_CONFIG.jshost = jshost
    elif hosted_on_github is True:
        CURRENT_CONFIG.hosted_on_github = True
    if echarts_template_dir:
        CURRENT_CONFIG.echarts_template_dir = echarts_template_dir
    if force_js_embed is not None:
        CURRENT_CONFIG.force_js_embed = force_js_embed
    if output_image in constants.JUPYTER_PRESENTATIONS:
        CURRENT_CONFIG.jupyter_presentation = output_image
    if global_theme in constants.ALL_THEMES:
        CURRENT_CONFIG.theme = global_theme


conf.configure = configure

from pyecharts.chart import Chart
from pyecharts.base import Base
import pyecharts.constants as constants
import pyecharts
from pyecharts import Bar, Line, Pie, Overlap, EffectScatter, Scatter, Grid, Timeline, Kline

import random
import threading
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time
from json.decoder import JSONDecodeError

PROJECT_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(PROJECT_DIR, "data/webData/"))
from webConfig import SettingConfig

sys.path.append(PROJECT_DIR)
# # cookies(从浏览器中获取)
from myUtils import getCookieFromChrome
from myUtils.decorator import singleton

from webConfig import SettingConfig

IS_BUG = False
NONE_PT = -1
NORMAL_PT = 1


# 装饰器
def create_chart_time(func):
    def newFunc(*args, **args2):
        if IS_BUG:
            t0 = time.time()
            print("@%s, {%s} start" % (time.strftime("%X", time.localtime()),
                                       func.__name__))
        back = func(*args, **args2)
        if IS_BUG:
            print("@%s, {%s} end" % (time.strftime("%X", time.localtime()),
                                     func.__name__))
            print("@%.3fs taken for {%s}" % (time.time() - t0, func.__name__))
        return back

    return newFunc


@singleton
class Charts():
    def __init__(self):

        print("初始化Charts类")

        self.n_show_days_short = 5
        self.n_show_days_long = 20
        self.start_date = "2018/09/01"
        self.end_date = "2018/09/30"

        setting_config = SettingConfig()
        self.show_month = setting_config.get_option_config("web", "show_month")
        self.show_months_list = setting_config.get_option_config(
            "web", "show_months").split(",")
        self.show_week = setting_config.get_option_config("web", "show_week")
        self.select_month = None
        self.select_week_start = None
        self.select_week_end = None

        self.option(show_month=self.show_month, show_week=self.show_week)

        print("月报表显示%s月份" % self.select_month)
        print("周报表显示%s----%s" % (self.select_week_start, self.select_week_end))

        self._sub_title_range_dict = {
            "M": "本月",
            "W": "本周",
            "ALL": "历史",
            "A": "历史"
        }
        self._sub_title_frq_dict = {"M": "每月", "W": "每周", "D": "每日"}

        self.chart = {}

    def set_charts_data(self, data_dict):

        for data_name in data_dict:
            setattr(self, data_name, data_dict[data_name])
            print("Charts类载入%s数据" % data_name)

        self.data_names = data_dict.keys()

        return self

    def set_holidays(self, holidays):

        self.holidays = holidays

        return self

    def set_date_range(self, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date

    def set_data(self, data_dict):
        print("更新Charts类的data")

        for data_name in data_dict:
            setattr(self, data_name, data_dict[data_name])
            print("Charts类载入%s数据" % data_name)

    def delete_cache(self):
        '''清楚储存在类属性里的数据'''
        print("删除Charts类的data")

        for data_name in self.data_names:
            # print("%s的引用计数为%d"%(data_name,getrefcount(getattr(self, data_name))))
            setattr(self, data_name, None)
            # print("删除Charts类的%s数据" % data_name)
        print('删除Charts类属性里的数据之后,类大小为%d' % getsizeof(self))

    def __sizeof__(self):

        size_all = 0
        for name, value in vars(self).items():
            size_all += getsizeof(value)
        return size_all

    def option(self,
               n_show_days_short=None,
               start_date=None,
               end_date=None,
               holidays=None,
               show_month=None,
               show_week=None):

        if n_show_days_short:
            self.n_show_days_short = n_show_days_short
        if start_date:
            self.start_date = start_date
        if end_date:
            self.end_date = end_date
        if holidays:
            self.holidays = holidays

        # 处理月份显示属性
        if show_month:
            self.show_month = show_month
            if show_month == "now":
                self.select_month = datetime.now().strftime("%Y-%m")
            elif show_month == "last":
                self.select_month = (datetime.now() + relativedelta(months=-1)
                                     ).strftime("%Y-%m")
            elif type(show_month) == int:
                self.select_month = (
                    datetime.now() +
                    relativedelta(months=show_month)).strftime("%Y-%m")
            else:
                self.show_month = "now"
                self.select_month = datetime.now().strftime("%Y-%m")
                print("属性show_month设置失败，回复默认值“now”")

        # 处理周显示属性
        if show_week:
            self.show_week = show_week
            if show_week == "now":
                tmp_week = 0
            elif show_week == "last":
                tmp_week = -1
            elif type(show_week) == int:
                tmp_week = show_month
            else:
                self.show_month = "now"
                tmp_week = 0
                print("属性show_week设置失败，回复默认值“now”")

            # 计算show_week_start,show_week_end

            self.select_week_start = (
                datetime.now() - timedelta(days=datetime.now().weekday()) +
                timedelta(days=tmp_week * 7)).strftime("%Y-%m-%d")
            self.select_week_end = (
                datetime.now() + timedelta(days=6 - datetime.now().weekday()) +
                timedelta(days=tmp_week * 7)).strftime("%Y-%m-%d")

    def get_select_month(self):
        if self.select_month:
            return self.select_month
        else:
            return "显示月份出错，请联系管理员"

    def get_select_week(self):
        if self.select_week_start and self.select_week_end:
            return self.select_week_start, self.select_week_end
        else:
            return "出错", "出错"

    def get_collect_data(self):
        ''' 
            获取汇总数据
        '''

        def get_collect_data_by_pivot_table_name(self, pivot_table_name,
                                                 condition):
            '''
            获取汇总表中的数据

            Arguments：
                pivot_table_name:数据透视表的名称
                condition：筛选条件
            returns：
                如果找不到，返回“暂无数据”
            '''

            if condition == "day":
                condition = datetime.now().strftime("%Y/%m/%d")
            elif condition == "week":
                condition = self.get_select_week(
                )[0] + "/" + self.get_select_week()[1]
            elif condition == "month":
                condition = self.get_select_month()

            pt = getattr(self, pivot_table_name)()['pt']

            if check_pt(pt) == NONE_PT:
                return "暂无数据"

            select_pt = pt[pt.index == condition]
            if len(select_pt) == 1:
                pt_sum = select_pt.sum().sum()
                if int(pt_sum) == pt_sum:
                    return "%d" % int(pt_sum)
                else:
                    return "%.2f" % pt_sum
            else:
                return "暂无数据"

        self.collection = {}

        self.collection['all'] = {}
        # 获取累计申请件数，每日累计放款金额，累计放款时收入，在库金额
        self.collection['all'][
            'apply_bill'] = "%d" % self.apply_data.customer_name.count()
        self.collection['all'][
            'loan_amount'] = "%.2f" % self.loan_data.bidding_money.sum()
        self.collection['all'][
            'loan_income'] = "%.2f" % self.loan_data.assets_income.sum()
        self.collection['all'][
            'instock_amount'] = "%.2f" % self.instock_data.sy_bj.sum()
        # self.collection['all']['pass_rate'] = "%.2f%%" % (
        #     self.review_data.loc[self.review_data['终审结果'] == '通过', ['终审结果']].
        #     shape[0] / self.review_data.loc[self.review_data['终审结果'].isin(
        #         ['通过', '拒绝']), ['终审结果']].shape[0])
        # self.collection['all']['sign_rate'] = "%.2f%%" % (
        #     self.review_data.loc[(self.review_data['终审结果'] == '通过') & (
        #         self.review_data['是否上标'] == 1), ['终审结果', '是否上标']].shape[
        #             0] / self.review_data.loc[self.review_data['终审结果'] ==
        #                                       '通过', ['终审结果']].shape[0])

        self.collection['day'] = {}
        # 获取每日申请件数，每日放款金额，每日件均，每月收入
        for collect_data_name, pivot_table_name in zip([
                'apply_bill', 'loan_amount', 'loan_amount_average',
                'loan_income', 'pass_rate', 'sign_rate'
        ], [
                'get_bar_apply_all_bill',
                'get_bar_loan_all_amount',
                'get_bar_loan_all_amount_average',
                'get_bar_loan_all_income_each_prd',
                'get_bar_review_all_pass_rate',
                'get_line_review_all_sign_rate',
        ]):
            self.collection['day'][
                collect_data_name] = get_collect_data_by_pivot_table_name(
                    self, pivot_table_name=pivot_table_name, condition='day')

        self.collection['week'] = {}

        # 获取每周申请件数，每日放款金额，每日件均，每月收入
        for collect_data_name, pivot_table_name in zip([
                'apply_bill', 'loan_amount', 'loan_amount_average',
                'loan_income', 'pass_rate', 'sign_rate'
        ], [
                'get_bar_apply_weekly_bill',
                'get_bar_loan_weekly_amount',
                'get_bar_loan_weekly_amount_average',
                'get_bar_loan_weekly_income',
                'get_bar_review_weekly_pass_rate',
                'get_bar_review_weekly_sign_rate',
        ]):
            self.collection['week'][
                collect_data_name] = get_collect_data_by_pivot_table_name(
                    self, pivot_table_name, 'week')

        # 获取每月申请件数，每日放款金额，每日件均，每月收入
        for condition in self.show_months_list:
            self.collection[condition] = {}

            for collect_data_name, pivot_table_name in zip([
                    'apply_bill', 'loan_amount', 'loan_amount_average',
                    'loan_income', "pass_rate", "sign_rate"
            ], [
                    'get_bar_apply_monthly_bill',
                    'get_bar_loan_monthly_amount',
                    'get_bar_loan_monthly_amount_average',
                    'get_bar_loan_monthly_income',
                    'get_bar_review_monthly_pass_rate',
                    'get_bar_review_monthly_sign_rate',
            ]):
                self.collection[condition][
                    collect_data_name] = get_collect_data_by_pivot_table_name(
                        self, pivot_table_name, condition)

        # 在库数据 (正常、逾期、坏账)
        self.collection['instock'] = {}
        self.collection['instock']['all'] = "%.2f" % (
            self.instock_data.sy_bj.sum() / 10000)
        self.collection['instock']['overdue'] = "%.2f" % (
            self.instock_data[(self.instock_data.overdue_days <= 180) & (
                self.instock_data.overdue_days > 0)].sy_bj.sum() / 10000)
        self.collection['instock']['normal'] = "%.2f" % (self.instock_data[
            self.instock_data.overdue_days == 0].sy_bj.sum() / 10000)
        self.collection['instock']['bad_debt'] = "%.2f" % (self.instock_data[
            self.instock_data.overdue_days > 180].sy_bj.sum() / 10000)
        # 等额本息、先息后本
        for repayment_mode in ['等额本息', '先息后本']:

            self.collection['instock'][repayment_mode] = {}
            self.collection['instock'][repayment_mode]['all'] = "%.2f" % (
                self.instock_data[(self.instock_data.repayment_mode ==
                                   repayment_mode)].sy_bj.sum() / 10000)
            self.collection['instock'][repayment_mode]['overdue'] = "%.2f" % (
                self.instock_data[(self.instock_data.overdue_days <= 180)
                                  & (self.instock_data.overdue_days > 0) &
                                  (self.instock_data.repayment_mode ==
                                   repayment_mode)].sy_bj.sum() / 10000)
            self.collection['instock'][repayment_mode]['normal'] = "%.2f" % (
                self.instock_data[(self.instock_data.overdue_days == 0)
                                  & (self.instock_data.repayment_mode ==
                                     repayment_mode)].sy_bj.sum() / 10000)
            self.collection['instock'][repayment_mode]['bad_debt'] = "%.2f" % (
                self.instock_data[(self.instock_data.overdue_days > 180)
                                  & (self.instock_data.repayment_mode ==
                                     repayment_mode)].sy_bj.sum() / 10000)

    def update(self):
        '''
            更新所有图表并保存至类属性中
        '''

        time_start = time.time()
        print("*" * 40)
        print("正在更新图表...........")

        # 总体情况

        self.chart['bar_apply_all_bill'] = self.get_bar_apply_all_bill()[
            'chart_render']
        self.chart['bar_loan_all_amount'] = self.get_bar_loan_all_amount()[
            'chart_render']
        self.chart[
            'bar_loan_all_period_average'] = self.get_bar_loan_all_period_average(
            )['chart_render']
        self.chart[
            'bar_loan_all_amount_average'] = self.get_bar_loan_all_amount_average(
            )['chart_render']
        self.chart[
            'bar_review_all_pass_rate'] = self.get_bar_review_all_pass_rate()[
                'chart_render']

        # 各产品申请件数、放款金额对比
        self.chart[
            'bar_apply_all_bill_each_prd'] = self.get_bar_apply_all_bill_each_prd(
            )['chart_render']
        self.chart[
            'bar_loan_all_amount_each_prd'] = self.get_bar_loan_all_amount_each_prd(
            )['chart_render']
        self.chart[
            'bar_apply_all_bill_each_prd_per'] = self.get_bar_apply_all_bill_each_prd_per(
            )['chart_render']
        self.chart[
            'bar_loan_all_amount_each_prd_per'] = self.get_bar_loan_all_amount_each_prd_per(
            )['chart_render']
        self.chart[
            'bar_apply_all_bill_each_prd_overlap'] = self.get_bar_apply_all_bill_each_prd_overlap(
            )['chart_render']
        self.chart['bar_apply_all_bill_dw'] = self.get_bar_apply_all_bill_dw()[
            'chart_render']
        self.chart['bar_loan_all_amount_dw'] = self.get_bar_loan_all_amount_dw(
        )['chart_render']
        self.chart['bar_apply_all_bill_ge'] = self.get_bar_apply_all_bill_ge()[
            'chart_render']
        self.chart['bar_loan_all_amount_ge'] = self.get_bar_loan_all_amount_ge(
        )['chart_render']

        # 审批通过率
        self.chart[
            'bar_review_all_pass_rate_each_prd'] = self.get_bar_review_all_pass_rate_each_prd(
            )['chart_render']

        # 签约率
        self.chart[
            'line_review_all_sign_rate'] = self.get_line_review_all_sign_rate(
            )['chart_render']
        self.chart[
            'line_review_all_sign_rate_each_prd'] = self.get_line_review_all_sign_rate_each_prd(
            )['chart_render']
        self.chart[
            'line_review_all_sign_rate_each_loan_amount_distribution'] = self.get_line_review_all_sign_rate_each_loan_amount_distribution(
            )['chart_render']

        # 逾期率
        self.chart[
            'bar_instock_all_overdue_rate'] = self.get_bar_instock_all_overdue_rate(
            )['chart_render']
        self.chart[
            'bar_instock_all_overdue_amount'] = self.get_bar_instock_all_overdue_amount(
            )['chart_render']
        self.chart[
            'bar_instock_all_overdue_rate_per_prd'] = self.get_bar_instock_all_overdue_rate_per_prd(
            )['chart_render']
        self.chart[
            'bar_instock_all_overdue_amount_per_prd'] = self.get_bar_instock_all_overdue_amount_per_prd(
            )['chart_render']

        # 借款人成本
        self.chart[
            'scatter_borrower_cost_all_per_prd'] = self.get_scatter_borrower_cost_all_per_prd(
            )['chart_render']
        self.chart[
            'bar_borrower_cost_all_average_rate_each_prd'] = self.get_bar_borrower_cost_all_average_rate_each_prd(
            )['chart_render']

        # 各期限对比图表
        self.chart[
            'bar_apply_all_bill_each_period'] = self.get_bar_apply_all_bill_each_period(
            )['chart_render']
        self.chart[
            'bar_loan_all_amount_each_period'] = self.get_bar_loan_all_amount_each_period(
            )['chart_render']
        self.chart[
            'bar_apply_all_bill_each_period_per'] = self.get_bar_apply_all_bill_each_period_per(
            )['chart_render']
        self.chart[
            'bar_loan_all_amount_each_period_per'] = self.get_bar_loan_all_amount_each_period_per(
            )['chart_render']

        # 各还款方式对比图表
        self.chart[
            'bar_apply_all_bill_each_repay'] = self.get_bar_apply_all_bill_each_repay(
            )['chart_render']
        self.chart[
            'bar_loan_all_amount_each_repay'] = self.get_bar_loan_all_amount_each_repay(
            )['chart_render']
        self.chart[
            'bar_apply_all_bill_each_repay_per'] = self.get_bar_apply_all_bill_each_repay_per(
            )['chart_render']
        self.chart[
            'bar_loan_all_amount_each_repay_per'] = self.get_bar_loan_all_amount_each_repay_per(
            )['chart_render']

        # 收入图表
        self.chart[
            'bar_loan_all_income_each_prd'] = self.get_bar_loan_all_income_each_prd(
            )['chart_render']
        self.chart['bar_loan_all_income_dw'] = self.get_bar_loan_all_income_dw(
        )['chart_render']
        self.chart['bar_loan_all_income_ge'] = self.get_bar_loan_all_income_ge(
        )['chart_render']
        # 地区数据图表
        self.chart[
            'bar_loan_all_amount_each_province_per'] = self.get_bar_loan_all_amount_each_province_per(
            )['chart_render']
        # self.chart[
        #     'bar_loan_all_amount_each_province_grid'] = self.get_bar_loan_all_amount_each_province_grid(
        #     )['chart_render']
        # 年龄数据图表
        self.chart[
            'bar_loan_all_amount_each_age_range'] = self.get_bar_loan_all_amount_each_age_range(
            )['chart_render']

        # 遍历show_months_list中每个月份
        for month in self.show_months_list:

            print("正在更新%s的图表" % month)

            self.chart[month] = {}

            # 月汇总信息
            # 各产品对比
            self.chart[month][
                'pie_apply_month_bill_each_prd'] = self.get_pie_apply_month_bill_each_prd(
                    month=month)['chart_render']
            self.chart[month][
                'pie_loan_month_amount_each_prd'] = self.get_pie_loan_month_amount_each_prd(
                    month=month)['chart_render']
            self.chart[month][
                'bar_loan_month_amount_average_each_prd'] = self.get_bar_loan_month_amount_average_each_prd(
                    month=month)['chart_render']
            self.chart[month][
                'bar_loan_month_period_average_each_prd'] = self.get_bar_loan_month_period_average_each_prd(
                    month=month)['chart_render']
            self.chart[month][
                'bar_review_month_pass_rate_each_prd'] = self.get_bar_review_month_pass_rate_each_prd(
                    month=month)['chart_render']
            self.chart[month][
                'bar_borrower_cost_month_average_rate_each_prd'] = self.get_bar_borrower_cost_month_average_rate_each_prd(
                    month=month)['chart_render']
            self.chart[month][
                'pie_loan_month_income_each_prd'] = self.get_pie_loan_month_income_each_prd(
                    month=month)['chart_render']
            self.chart[month][
                'pie_instock_month_income_each_prd'] = self.get_pie_instock_month_income_each_prd(
                    month=month)['chart_render']
            self.chart[month][
                'pie_loan_month_amount_distribution'] = self.get_pie_loan_month_amount_distribution(
                    month=month)['chart_render']  # 放款金额分布
            self.chart[month][
                'bar_review_month_sign_rate_each_loan_amount_distribution'] = self.get_bar_review_month_sign_rate_each_loan_amount_distribution(
                    month=month)['chart_render']

            # 本月每日走势
            self.chart[month][
                'bar_apply_month_bill'] = self.get_bar_apply_month_bill(
                    month=month)['chart_render']
            self.chart[month][
                'bar_apply_month_bill_mom'] = self.get_bar_apply_month_bill(
                    month=month)["mom_chart"]
            self.chart[month][
                'bar_loan_month_amount'] = self.get_bar_loan_month_amount(
                    month=month)['chart_render']
            self.chart[month][
                'bar_loan_month_amount_mom'] = self.get_bar_loan_month_amount(
                    month=month)["mom_chart"]
            self.chart[month][
                'bar_loan_month_amount_average'] = self.get_bar_loan_month_amount_average(
                    month=month)['chart_render']  # 件均
            self.chart[month][
                'bar_loan_month_amount_average_mom'] = self.get_bar_loan_month_amount_average(
                    month=month)["mom_chart"]  # 件均 环比
            self.chart[month][
                'bar_loan_month_period_average'] = self.get_bar_loan_month_period_average(
                    month=month)['chart_render']  # 期均
            self.chart[month][
                'bar_loan_month_period_average_mom'] = self.get_bar_loan_month_period_average(
                    month=month)["mom_chart"]  # 期均 环比
            self.chart[month][
                'bar_review_month_pass_rate'] = self.get_bar_review_month_pass_rate(
                    month=month)['chart_render']
            self.chart[month][
                'bar_review_month_pass_rate_mom'] = self.get_bar_review_month_pass_rate(
                    month=month)["mom_chart"]
            self.chart[month][
                'bar_loan_month_income'] = self.get_bar_loan_month_income(
                    month=month)['chart_render']  # 放款时收入
            self.chart[month][
                'bar_loan_month_income_mom'] = self.get_bar_loan_month_income(
                    month=month)["mom_chart"]  # 放款时收入 环比
            self.chart[month][
                'bar_review_month_sign_rate'] = self.get_bar_review_month_sign_rate(
                    month=month)['chart_render']  # 签约率

            # 每月走势
            self.chart[month][
                'bar_apply_monthly_bill'] = self.get_bar_apply_monthly_bill()[
                    'chart_render']
            self.chart[month][
                'bar_apply_monthly_bill_mom'] = self.get_bar_apply_monthly_bill(
                )["mom_chart"]
            self.chart[month][
                'bar_loan_monthly_amount'] = self.get_bar_loan_monthly_amount(
                )['chart_render']
            self.chart[month][
                'bar_loan_monthly_amount_mom'] = self.get_bar_loan_monthly_amount(
                )["mom_chart"]
            self.chart[month][
                'bar_loan_monthly_amount_average'] = self.get_bar_loan_monthly_amount_average(
                )['chart_render']  # 件均
            self.chart[month][
                'bar_loan_monthly_amount_average_mom'] = self.get_bar_loan_monthly_amount_average(
                )["mom_chart"]  # 件均 环比
            self.chart[month][
                'bar_loan_monthly_period_average'] = self.get_bar_loan_monthly_period_average(
                )['chart_render']  # 期均
            self.chart[month][
                'bar_loan_monthly_period_average_mom'] = self.get_bar_loan_monthly_period_average(
                )["mom_chart"]  # 期均 环比
            self.chart[month][
                'bar_review_monthly_pass_rate'] = self.get_bar_review_monthly_pass_rate(
                )['chart_render']
            self.chart[month][
                'bar_review_monthly_pass_rate_mom'] = self.get_bar_review_monthly_pass_rate(
                )["mom_chart"]
            self.chart[month][
                'bar_loan_monthly_income'] = self.get_bar_loan_monthly_income(
                )['chart_render']  # 放款时收入
            self.chart[month][
                'bar_loan_monthly_income_mom'] = self.get_bar_loan_monthly_income(
                )["mom_chart"]  # 放款时收入 环比
            self.chart[month][
                'bar_instock_monthly_income'] = self.get_bar_instock_monthly_income(
                )["chart_render"]  # 存量收入
            self.chart[month][
                'bar_instock_monthly_income_mom'] = self.get_bar_instock_monthly_income(
                )["mom_chart"]  # 存量收入
            self.chart[month][
                'bar_review_monthly_sign_rate'] = self.get_bar_review_monthly_sign_rate(
                    month=month)['chart_render']  # 签约率

            # 逾期数据
            self.chart[month][
                'bar_instock_all_overdue_rate2'] = self.get_bar_instock_all_overdue_rate(
                )['chart_render']
            self.chart[month][
                'bar_instock_all_overdue_rate_per_prd2'] = self.get_bar_instock_all_overdue_rate_per_prd(
                )['chart_render']

            print("成功更新%s的图表" % month)

        # 周汇总信息
        # 各产品对比
        self.chart[
            'pie_apply_week_bill_each_prd'] = self.get_pie_apply_week_bill_each_prd(
            )['chart_render']
        self.chart[
            'pie_loan_week_amount_each_prd'] = self.get_pie_loan_week_amount_each_prd(
            )['chart_render']
        self.chart[
            'bar_loan_week_amount_average_each_prd'] = self.get_bar_loan_week_amount_average_each_prd(
            )['chart_render']
        self.chart[
            'bar_loan_week_period_average_each_prd'] = self.get_bar_loan_week_period_average_each_prd(
            )['chart_render']
        self.chart[
            'bar_review_week_pass_rate_each_prd'] = self.get_bar_review_week_pass_rate_each_prd(
            )['chart_render']
        self.chart[
            'bar_borrower_cost_week_average_rate_each_prd'] = self.get_bar_borrower_cost_week_average_rate_each_prd(
            )['chart_render']
        self.chart[
            'pie_loan_week_income_each_prd'] = self.get_pie_loan_week_income_each_prd(
            )['chart_render']
        self.chart[
            'pie_instock_week_income_each_prd'] = self.get_pie_instock_week_income_each_prd(
            )['chart_render']
        self.chart[
            'pie_loan_week_amount_distribution'] = self.get_pie_loan_week_amount_distribution(
            )['chart_render']  # 放款金额分布
        self.chart[
            'bar_review_week_sign_rate_each_loan_amount_distribution'] = self.get_bar_review_week_sign_rate_each_loan_amount_distribution(
            )['chart_render']

        # 本周每日走势
        self.chart['bar_apply_week_bill'] = self.get_bar_apply_week_bill()[
            'chart_render']
        self.chart['bar_apply_week_bill_mom'] = self.get_bar_apply_week_bill()[
            "mom_chart"]
        self.chart['bar_loan_week_amount'] = self.get_bar_loan_week_amount()[
            'chart_render']
        self.chart['bar_loan_week_amount_mom'] = self.get_bar_loan_week_amount(
        )["mom_chart"]
        self.chart[
            'bar_loan_week_amount_average'] = self.get_bar_loan_week_amount_average(
            )['chart_render']  # 件均
        self.chart[
            'bar_loan_week_amount_average_mom'] = self.get_bar_loan_week_amount_average(
            )["mom_chart"]  # 件均 环比
        self.chart[
            'bar_loan_week_period_average'] = self.get_bar_loan_week_period_average(
            )['chart_render']  # 期均
        self.chart[
            'bar_loan_week_period_average_mom'] = self.get_bar_loan_week_period_average(
            )["mom_chart"]  # 期均 环比
        self.chart[
            'bar_review_week_pass_rate'] = self.get_bar_review_week_pass_rate(
            )['chart_render']
        self.chart[
            'bar_review_week_pass_rate_mom'] = self.get_bar_review_week_pass_rate(
            )["mom_chart"]
        self.chart['bar_loan_week_income'] = self.get_bar_loan_week_income()[
            'chart_render']  # 放款时收入
        self.chart['bar_loan_week_income_mom'] = self.get_bar_loan_week_income(
        )["mom_chart"]  # 放款时收入 环比
        self.chart[
            'bar_review_week_sign_rate'] = self.get_bar_review_week_sign_rate(
            )['chart_render']  # 签约率

        # 每周走势
        self.chart['bar_apply_weekly_bill'] = self.get_bar_apply_weekly_bill()[
            'chart_render']
        self.chart[
            'bar_apply_weekly_bill_mom'] = self.get_bar_apply_weekly_bill()[
                "mom_chart"]
        self.chart['bar_loan_weekly_amount'] = self.get_bar_loan_weekly_amount(
        )['chart_render']
        self.chart[
            'bar_loan_weekly_amount_mom'] = self.get_bar_loan_weekly_amount()[
                "mom_chart"]
        self.chart[
            'bar_loan_weekly_amount_average'] = self.get_bar_loan_weekly_amount_average(
            )['chart_render']  # 件均
        self.chart[
            'bar_loan_weekly_amount_average_mom'] = self.get_bar_loan_weekly_amount_average(
            )["mom_chart"]  # 件均 环比
        self.chart[
            'bar_loan_weekly_period_average'] = self.get_bar_loan_weekly_period_average(
            )['chart_render']  # 期均
        self.chart[
            'bar_loan_weekly_period_average_mom'] = self.get_bar_loan_weekly_period_average(
            )["mom_chart"]  # 期均 环比
        self.chart[
            'bar_review_weekly_pass_rate'] = self.get_bar_review_weekly_pass_rate(
            )['chart_render']
        self.chart[
            'bar_review_weekly_pass_rate_mom'] = self.get_bar_review_weekly_pass_rate(
            )["mom_chart"]
        self.chart['bar_loan_weekly_income'] = self.get_bar_loan_weekly_income(
        )['chart_render']  # 放款时收入
        self.chart[
            'bar_loan_weekly_income_mom'] = self.get_bar_loan_weekly_income()[
                "mom_chart"]  # 放款时收入 环比
        self.chart[
            'bar_review_weekly_sign_rate'] = self.get_bar_review_weekly_sign_rate(
            )['chart_render']  # 签约率

        # 逾期数据
        self.chart[
            'bar_instock_all_overdue_rate3'] = self.get_bar_instock_all_overdue_rate(
            )['chart_render']
        self.chart[
            'bar_instock_all_overdue_rate_per_prd3'] = self.get_bar_instock_all_overdue_rate_per_prd(
            )['chart_render']

        # 贷后报表

        for chart_name in [
                'get_line_instock_all_amount',
                'get_line_instock_monthly_amount', 'get_line_paid_all_bill',
                'get_line_paid_monthly_bill', 'get_line_paid_all_income',
                'get_line_paid_monthly_income',
                'get_line_repay_all_income_perdict',
                'get_line_repay_monthly_income_perdict',
                'get_bar_instock_all_status_amount_per_prd_percent',
                "get_bar_instock_all_status_amount_per_prd",
                "get_bar_instock_all_status_amount_per_repayment_mode_percent",
                "get_bar_instock_all_status_amount_per_repayment_mode",
                "get_bar_instock_all_status_amount_per_province_percent",
                "get_bar_instock_all_status_amount_per_province",
                "get_bar_instock_all_status_amount_per_age_range_percent",
                "get_bar_instock_all_status_amount_per_age_range",
                "get_bar_instock_all_status_amount_per_period_percent",
                "get_bar_instock_all_status_amount_per_period",
                'get_bar_instock_all_prd_amount_per_status_percent',
                "get_bar_instock_all_prd_amount_per_status",
                "get_bar_instock_all_repayment_mode_amount_per_status_percent",
                "get_bar_instock_all_repayment_mode_amount_per_status",
                "get_bar_instock_all_province_amount_per_status_percent",
                "get_bar_instock_all_province_amount_per_status",
                "get_bar_instock_all_age_range_amount_per_status_percent",
                "get_bar_instock_all_age_range_amount_per_status",
                "get_bar_instock_all_period_amount_per_status_percent",
                "get_bar_instock_all_period_amount_per_status"
        ]:
            self.chart[chart_name[4:]] = getattr(self,
                                                 chart_name)()['chart_render']

        time_end = time.time()
        print("更新图表完毕，一共使用%.2f秒" % (time_end - time_start))

        time_collect = time.time()
        self.get_collect_data()
        print("更新汇总数据完毕，一共使用%.2f秒" % (time.time() - time_collect))

        #删除数据
        self.delete_cache()

        return self

    def get_chart(self, chart_name="ALL"):
        '''
            根据图表名称提取图表
        
        Args：
            chart_name:图表名称或“ALL”

        Return：
            如果是图表名称，则返回type:pyecharts.Chart
            如果是“ALL”，则返回dict
        '''
        if chart_name == "ALL" and self.chart:
            return self.chart

        elif type(self.chart) == dict and type(
                chart_name
        ) == str and chart_name in self.chart and self.chart[chart_name]:
            return self.chart[chart_name]
        else:
            print("获取图表失败，参数为%s" % chart_name)
        return None

    # 总体情况 每日申请
    @create_chart_time
    def get_bar_apply_all_bill(self):
        '''
            申请件数每日走势图
        '''

        pt = extract_data_by_date(
            self.apply_data,
            index=['时间（-）'],
            values='customer_name',
            aggfunc=np.count_nonzero,
            margins=None,
            holidays=self.holidays)

        pt = proc_pt(pt, n_show_days=20, columns_name=pd.Index(['申请件数']))

        chart = render_echarts_by_lists(
            pt,
            "每日申请件数",
            "近20工作日申请件数每日走势图",
            chart_kind="line",
            dropna=True,
            xaxis_rotate=90,
            xaxis_interval=0,
            label_text_size=15,
            is_label_show=True,
            mark_line=["average"],
            is_smooth=True,
            is_fill=True,
            area_opacity=0.3,
            is_more_utils=True)

        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else ""
        }

    @create_chart_time
    def get_bar_loan_all_amount(self):

        pt = extract_data_by_date(
            self.loan_data,
            index=['full_scale_time'],
            values='bidding_money',
            aggfunc=np.sum,
            margins=None,
            holidays=self.holidays)

        pt = proc_pt(pt, n_show_days=20, is_round=1, columns_name=['放款金额（万）'])

        chart = render_echarts_by_lists(
            pt,
            "每日放款金额",
            "近20工作日放款金额（万）每日走势图",
            chart_kind="line",
            dropna=True,
            xaxis_rotate=90,
            xaxis_interval=0,
            label_text_size=15,
            is_label_show=True,
            mark_line=["average"],
            is_smooth=True,
            is_fill=True,
            area_opacity=0.3,
            is_more_utils=True)
        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else ""
        }

    # 各产品申请件数
    @create_chart_time
    def get_bar_apply_all_bill_each_prd(self):

        pt = extract_data_by_date(
            self.apply_data,
            index=['时间（-）'],
            columns=['loan_product'],
            values='customer_name',
            aggfunc=np.count_nonzero,
            margins=None,
            holidays=self.holidays)

        pt = proc_pt(
            pt, n_show_days=self.n_show_days_short, is_change_index='column')

        chart = render_echarts_by_lists(
            pt,
            "各产品申请件数",
            "近5工作日各产品申请件数",
            dropna=True,
            xaxis_rotate=0,
            xaxis_interval=0,
            label_text_size=12,
            is_label_show=True,
            is_more_utils=True,
        )
        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else "",
            'chart': chart
        }

    @create_chart_time
    def get_bar_loan_all_amount_each_prd(self):

        pt = extract_data_by_date(
            self.loan_data,
            index=['full_scale_time'],
            columns=['loan_product_ch'],
            values='bidding_money',
            aggfunc=np.sum,
            margins=None,
            holidays=self.holidays)

        pt = proc_pt(
            pt,
            n_show_days=self.n_show_days_short,
            is_round=1,
            is_change_index='column')

        chart = render_echarts_by_lists(
            pt,
            "各产品放款金额",
            "近5工作日各产品放款金额（万）",
            dropna=True,
            xaxis_rotate=0,
            xaxis_interval=0,
            label_show_percent=True,
            is_label_show=True)
        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else ""
        }

    @create_chart_time
    def get_bar_apply_all_bill_each_prd_per(self):

        pt = extract_data_by_date(
            self.apply_data,
            index=['时间（-）'],
            columns=['loan_product'],
            values='customer_name',
            aggfunc=np.count_nonzero,
            margins=None,
            holidays=self.holidays)

        pt = proc_pt(
            pt, n_show_days=self.n_show_days_short, change_to_percent=2)

        chart = render_echarts_by_lists(
            pt,
            "各产品申请件数",
            "近5工作日各产品申请件数占比（%）",
            chart_kind='line',
            dropna=True,
            xaxis_rotate=0,
            xaxis_interval=0,
            yaxis_formatter="%",
            label_formatter="{c}%",
            label_text_size=12,
            is_label_show=True)

        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else "",
            'chart': chart
        }

    @create_chart_time
    def get_bar_loan_all_amount_each_prd_per(self):

        pt = extract_data_by_date(
            self.loan_data,
            index=['full_scale_time'],
            columns=['loan_product_ch'],
            values='bidding_money',
            aggfunc=np.sum,
            margins=None,
            holidays=self.holidays)

        pt = proc_pt(
            pt, n_show_days=self.n_show_days_short, change_to_percent=2)

        chart = render_echarts_by_lists(
            pt,
            "各产品放款金额",
            "近5工作日各产品放款金额占比（%）",
            chart_kind='line',
            dropna=True,
            xaxis_rotate=0,
            xaxis_interval=0,
            yaxis_formatter="%",
            label_formatter="{c}%",
            label_text_size=12,
            is_label_show=True)

        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else ""
        }

    @create_chart_time
    def get_bar_apply_all_bill_each_prd_overlap(self):

        bar_apply_all_bill_each_prd = self.get_bar_apply_all_bill_each_prd()[
            'chart']

        bar_apply_all_bill_each_prd_per = self.get_bar_apply_all_bill_each_prd_per(
        )['chart']

        chart = Overlap()
        chart.add(bar_apply_all_bill_each_prd)
        chart.add(
            bar_apply_all_bill_each_prd_per, yaxis_index=1, is_add_yaxis=True)
        return {'chart_render': chart.render_embed() if chart else ""}

    @create_chart_time
    def get_bar_apply_all_bill_dw(self):

        pt = extract_data_by_date(
            self.apply_data,
            index=['时间（-）'],
            columns=['loan_product', 'apply_period'],
            values='customer_name',
            aggfunc=np.count_nonzero,
            margins=None,
            holidays=self.holidays)

        pt = proc_pt(
            pt['别等贷'],
            n_show_days=self.n_show_days_short,
            is_change_index='column')

        chart = render_echarts_by_lists(
            pt,
            "别等贷各期限申请件数对比",
            "近5日别等贷各期限申请件数",
            dropna=True,
            xaxis_rotate=0,
            xaxis_interval=0,
            label_text_size=12,
            is_label_show=True,
            is_more_utils=True)

        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else ""
        }

    @create_chart_time
    def get_bar_loan_all_amount_dw(self):

        pt = extract_data_by_date(
            self.loan_data,
            index=['full_scale_time'],
            columns=['loan_product_ch', 'loan_period', 'month_rate'],
            values='bidding_money',
            aggfunc=np.sum,
            margins=None,
            holidays=self.holidays)

        pt = proc_pt(
            pt['别等贷'],
            n_show_days=self.n_show_days_short,
            is_round=1,
            is_change_index="column")

        chart = render_echarts_by_lists(
            pt,
            "别等贷各期限放款金额对比",
            "近5日别等贷各期限放款金额（万）",
            dropna=True,
            xaxis_rotate=0,
            xaxis_interval=0,
            label_text_size=12,
            is_label_show=True)

        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else ""
        }

    @create_chart_time
    def get_bar_apply_all_bill_ge(self):

        pt = extract_data_by_date(
            self.apply_data,
            index=['时间（-）'],
            columns=['loan_product', 'apply_period'],
            values='customer_name',
            aggfunc=np.count_nonzero,
            margins=None,
            holidays=self.holidays)

        pt = proc_pt(
            pt['好期贷'],
            n_show_days=self.n_show_days_short,
            is_change_index='column')

        pt = pt[['1个月', '3个月', '6个月', '12个月']]

        chart = render_echarts_by_lists(
            pt,
            "好期贷各期限申请件数对比",
            "近5日好期贷各期限申请件数",
            dropna=True,
            xaxis_rotate=0,
            xaxis_interval=0,
            label_text_size=12,
            is_label_show=True,
            is_more_utils=True)

        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else ""
        }

    @create_chart_time
    def get_bar_loan_all_amount_ge(self):

        pt = extract_data_by_date(
            self.loan_data,
            index=['full_scale_time'],
            columns=['loan_product_ch', 'loan_period', 'month_rate'],
            values='bidding_money',
            aggfunc=np.sum,
            margins=None,
            holidays=self.holidays)

        pt = proc_pt(
            pt['好期贷'],
            n_show_days=self.n_show_days_short,
            is_round=1,
            is_change_index="column")

        chart = render_echarts_by_lists(
            pt,
            "好期贷各期限放款金额对比",
            "近5日好期贷各期限放款金额（万）",
            dropna=True,
            xaxis_rotate=0,
            xaxis_interval=0,
            label_text_size=12,
            is_label_show=True)

        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else ""
        }

    # 审批数据对比
    @create_chart_time
    def get_bar_review_all_pass_rate_each_prd(self):

        pt = extract_data_by_date(
            self.review_data,
            index=['第一次提交初审日期'],
            columns=['终审审核结果', '借款类型'],
            values='借款单ID',
            aggfunc=np.count_nonzero,
            margins=None,
            holidays=self.holidays)

        if check_pt(pt) == NONE_PT:
            return {"pt": pt, 'chart_render': "无数据"}

        for i in ['通过', '拒绝']:
            if i not in pt.columns:
                pt[i] = 0

        pt = pt["通过"] / (pt["通过"] + pt["拒绝"]) * 100

        pt = proc_pt(pt, n_show_days=5, is_round=1, columns_name=['审批通过率'])

        pt_min = pt.min().min()

        chart = render_echarts_by_lists(
            pt,
            "各产品审批通过率",
            "近5工作日各产品审批通过率",
            chart_kind="line",
            dropna=True,
            xaxis_rotate=90,
            xaxis_interval=0,
            yaxis_min=pt_min,
            yaxis_max="dataMax",
            yaxis_formatter="%",
            label_formatter="{c}%",
            label_text_size=12,
            is_label_show=True,
            mark_line=["average"],
            is_smooth=True,
            is_fill=True,
            area_opacity=0.1,
            is_more_utils=True)
        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else ""
        }

    @create_chart_time
    def get_bar_review_all_pass_rate(self):

        pt = extract_data_by_date(
            self.review_data,
            index=['第一次提交初审日期'],
            columns=['终审审核结果'],
            values='借款单ID',
            aggfunc=np.count_nonzero,
            margins=None,
            holidays=self.holidays)

        if check_pt(pt) == NONE_PT:
            return {"pt": pt, 'chart_render': "无数据"}

        for i in ['通过', '拒绝']:
            if i not in pt.columns:
                pt[i] = 0

        pt.loc[:, '审批通过率'] = pt["通过"] / (pt["通过"] + pt["拒绝"]) * 100
        pt = pt[['审批通过率']]
        pt = proc_pt(pt, n_show_days=20, is_round=1, columns_name=['审批通过率'])

        pt_min = pt.min().min()

        chart = render_echarts_by_lists(
            pt,
            "每日审批通过率",
            "近20工作日审批通过率（%）",
            chart_kind="line",
            dropna=True,
            xaxis_rotate=90,
            xaxis_interval=0,
            yaxis_min=pt_min,
            yaxis_max="dataMax",
            yaxis_formatter="%",
            label_formatter="{c}%",
            label_text_size=15,
            is_label_show=True,
            mark_line=["average"],
            is_smooth=True,
            is_fill=True,
            area_opacity=0.1,
            is_more_utils=True)
        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else ""
        }

    @create_chart_time
    def get_chart_sign_rate(self,
                            groupby=None,
                            date_range="A",
                            index=None,
                            month=None,
                            show_restrict=True):

        # range data
        range_data = self.get_range_data(
            self.review_data, date_range=date_range, specify=month)

        if not type(range_data) == pd.DataFrame:
            return {"pt": None, 'chart_render': "range_data无数据"}

        sub_title_range = self._sub_title_range_dict.get(date_range, "错误")
        sub_title_frq = self._sub_title_frq_dict.get(groupby, "错误")

        # decide what kind of chart? trend or summary
        if not groupby or groupby == date_range:
            # summary chart, use bar or pie

            pt = extract_data_by_date(
                range_data,
                index=index,
                values=['借款单ID', '是否上标'],
                aggfunc=np.count_nonzero,
                margins=None,
                holidays=self.holidays)

            if check_pt(pt) == NONE_PT:
                return {"pt": pt, 'chart_render': "pivot_table无数据"}

            # Calculate the sign rate
            average_sign_rate = pt['是否上标'].sum() / pt['借款单ID'].sum()
            pt = pt.apply(
                lambda x: 0 if x['是否上标'] == 0 else x['是否上标'] / x['借款单ID'],
                axis=1)

            # Change them to proportion
            pt = pt.map(lambda x: round(x * 100, 2))

            # Sort index
            row_name_sorted = [
                '3万以下', '3万(含)-5万(含)', '5万-10万(含)', '10万-15万(含)', '15万-20万(含)',
                '20万-25万(含)', '25万-30万(含)', '30万以上'
            ]

            pt = pt.loc[[
                row_name for row_name in row_name_sorted
                if row_name in pt.index
            ]]

            chart = render_echarts_by_lists(
                pt,
                "各金额区间签约率",
                "%s平均签约率%.2f%%" % (sub_title_range, average_sign_rate * 100),
                dropna=True,
                chart_kind="bar",
                xaxis_rotate=30,
                xaxis_interval=0,
                legend_pos='75%',
                legend_orient='vertical',
                legend_top='center',
                label_formatter="{c}%",
                yaxis_formatter="%",
                is_legend_show=False,
                is_label_show=True,
                bar_category_gap=50)

        else:
            # trend chart, use line

            pt = extract_data_by_date(
                range_data,
                index=['index'],
                columns=index,
                values=['借款单ID', '是否上标'],
                aggfunc=np.count_nonzero,
                margins=None,
                groupby=groupby,
                holidays=self.holidays)

            if check_pt(pt) == NONE_PT:
                return {"pt": pt, 'chart_render': "pivot_table无数据"}

            # Calculate the sign rate
            pt = pt['是否上标'] / pt['借款单ID']
            pt.fillna(0, inplace=True)

            # Change them to proportion
            if type(pt) == pd.DataFrame:
                pt = pt.applymap(lambda x: round(x * 100, 2))
            elif type(pt) == pd.Series:
                pt = pt.map(lambda x: round(x * 100, 2))

            if show_restrict:
                pt = proc_pt(
                    pt,
                    n_show_days=self.n_show_days_long,
                    is_round=1,
                    columns_name=['签约率'])
            else:
                pt = proc_pt(
                    pt, n_show_days=None, is_round=1, columns_name=['签约率'])

            feature_name = ""
            if index:
                if index[0] == "借款类型":
                    feature_name = "各产品"
                else:
                    feature_name = "各" + str(index[0])

            chart = render_echarts_by_lists(
                pt,
                "%s%s签约率%s走势" % (feature_name, sub_title_range, sub_title_frq),
                "",
                chart_kind="line",
                dropna=True,
                label_formatter="{c}%",
                yaxis_formatter="%",
                xaxis_rotate=90,
                xaxis_interval=0,
                label_text_size=12,
                is_label_show=True,
                mark_line=["average"],
                is_smooth=True,
                is_fill=True,
                area_opacity=0.3,
                is_more_utils=True)

        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else ""
        }

    @create_chart_time
    def get_bar_loan_all_period_average(self):

        pt = extract_data_by_date(
            self.loan_data,
            index=['full_scale_time'],
            values='loan_period',
            aggfunc=np.average,
            margins=None,
            holidays=self.holidays)

        pt = proc_pt(pt, n_show_days=20, is_round=1, columns_name=['平均期限'])

        chart = render_echarts_by_lists(
            pt,
            "每日放款平均期限",
            "近20工作日放款平均期限（月）",
            chart_kind="line",
            dropna=True,
            xaxis_rotate=90,
            xaxis_interval=0,
            yaxis_min=round(pt.min().min() / 1.1, 2),
            label_text_size=12,
            is_label_show=True,
            mark_line=["average"],
            is_smooth=True,
            is_fill=True,
            area_opacity=0.3,
            is_more_utils=True)
        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else ""
        }

    # 放款期均、件均数据
    @create_chart_time
    def get_bar_loan_all_amount_average(self):

        pt = extract_data_by_date(
            self.loan_data,
            index=['full_scale_time'],
            values='bidding_money',
            aggfunc=np.average,
            margins=None,
            holidays=self.holidays)

        pt = proc_pt(pt, n_show_days=20, is_round=1, columns_name=['放款件均'])

        chart = render_echarts_by_lists(
            pt,
            "每日放款件均",
            "近20工作日借款单平均放款金额（万）",
            chart_kind="line",
            dropna=True,
            xaxis_rotate=90,
            xaxis_interval=0,
            yaxis_min=round(pt.min().min() / 1.1, 2),
            label_text_size=12,
            is_label_show=True,
            mark_line=["average"],
            is_smooth=True,
            is_fill=True,
            area_opacity=0.3,
            is_more_utils=True)
        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else ""
        }

    # 逾期数据对比
    @create_chart_time
    def get_bar_instock_all_overdue_rate(self):

        instock_amount = self.instock_data.sy_bj.sum()

        pt = extract_data_by_date(
            self.instock_data,
            columns='overdue_state',
            values='sy_bj',
            aggfunc=np.sum,
            margins=None,
            holidays=self.holidays)

        pt = proc_pt(
            pt, is_round=1, change_to_percent=2, columns_name=['正常', '逾期'])
        pt.index = ['逾期']
        pt = pt[['M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M6+']]

        pt.fillna(0, inplace=True)
        pt.loc[:, '产品逾期率'] = pt.M1 + pt.M2 + pt.M3 + pt.M4 + pt.M5 + pt.M6
        pt.loc[:, '产品逾期率'] = pt['产品逾期率'].map(lambda x: round(x, 2))
        pt = pt[['M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M6+', '产品逾期率']]
        pt = pt.sort_values(by='产品逾期率', ascending=False)

        chart = render_echarts_by_lists(
            pt,
            "逾期状态分布",
            "截止至目前，逾期状态分布（%%），在库金额为%.2f万" % instock_amount,
            chart_kind="bar",
            dropna=True,
            xaxis_interval=0,
            yaxis_formatter="%",
            label_formatter="{c}%\n{a}",
            label_text_size=12,
            is_label_show=True,
            is_more_utils=True)
        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else ""
        }

    @create_chart_time
    def get_bar_instock_all_overdue_amount(self):

        instock_amount = self.instock_data.sy_bj.sum()

        pt = extract_data_by_date(
            self.instock_data,
            columns='overdue_state',
            values='sy_bj',
            aggfunc=np.sum,
            margins=None,
            holidays=self.holidays)

        pt = proc_pt(pt, is_round=1)
        pt.index = ['逾期金额']
        pt = pt[['M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M6+']]

        pt.fillna(0, inplace=True)
        pt.loc[:, '产品总逾期'] = pt.M1 + pt.M2 + pt.M3 + pt.M4 + pt.M5 + pt.M6
        pt.loc[:, '产品总逾期'] = pt['产品总逾期'].map(lambda x: round(x, 2))
        pt = pt[['M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M6+', '产品总逾期']]
        pt = pt.sort_values(by='产品总逾期', ascending=False)

        chart = render_echarts_by_lists(
            pt,
            "各逾期状态逾期金额",
            "截止至目前，各逾期状态逾期金额（万），在库金额为%.2f万" % instock_amount,
            chart_kind="bar",
            dropna=True,
            xaxis_interval=0,
            yaxis_formatter="万",
            label_formatter="{c}\n{a}",
            label_text_size=12,
            is_label_show=True,
            is_more_utils=True)
        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else ""
        }

    @create_chart_time
    def get_bar_instock_all_overdue_rate_per_prd(self):

        pt = extract_data_by_date(
            self.instock_data,
            index=['loan_product'],
            columns='overdue_state',
            values='sy_bj',
            aggfunc=np.sum,
            margins=None,
            holidays=self.holidays)

        pt = proc_pt(
            pt, is_round=1, change_to_percent=2, columns_name=['正常', '逾期'])
        pt = pt[['M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M6+']]

        pt.fillna(0, inplace=True)
        pt.loc[:, '产品逾期率'] = pt.M1 + pt.M2 + pt.M3 + pt.M4 + pt.M5 + pt.M6
        pt.loc[:, '产品逾期率'] = pt['产品逾期率'].map(lambda x: round(x, 2))
        pt = pt[['M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M6+', '产品逾期率']]
        pt = pt.sort_values(by='产品逾期率', ascending=False)

        chart = render_echarts_by_lists(
            pt,
            "各产品逾期率对比",
            "截止至目前为止，各产品各逾期状态逾期率",
            chart_kind="bar",
            dropna=True,
            xaxis_interval=0,
            yaxis_formatter="%",
            label_formatter="{c}%\n{a}",
            width='100%',
            height=800,
            label_text_size=12,
            is_label_show=True,
            is_more_utils=True)
        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else ""
        }

    @create_chart_time
    def get_bar_instock_all_overdue_amount_per_prd(self):

        pt = extract_data_by_date(
            self.instock_data,
            index=['loan_product'],
            columns='overdue_state',
            values='sy_bj',
            aggfunc=np.sum,
            margins=None,
            holidays=self.holidays)

        pt = proc_pt(pt, is_round=1)
        pt = pt[['M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M6+']]

        pt.fillna(0, inplace=True)
        pt.loc[:, '产品总逾期'] = pt.M1 + pt.M2 + pt.M3 + pt.M4 + pt.M5 + pt.M6
        pt.loc[:, '产品总逾期'] = pt['产品总逾期'].map(lambda x: round(x, 2))
        pt = pt[['M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M6+', '产品总逾期']]
        pt = pt.sort_values(by='产品总逾期', ascending=False)

        chart = render_echarts_by_lists(
            pt,
            "各产品逾期金额对比",
            "截止至目前为止，各产品各逾期状态逾期金额",
            chart_kind="bar",
            dropna=True,
            xaxis_interval=0,
            yaxis_formatter="万",
            label_formatter="{c}万\n{a}",
            width='100%',
            height=800,
            label_text_size=12,
            is_label_show=True,
            is_more_utils=True)
        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else ""
        }

    # 借款人成本数据对比
    @create_chart_time
    def get_scatter_borrower_cost_all_per_prd(self):
        '''借款人成本数据'''

        borrower_cost_data = copy.deepcopy(self.borrower_cost_data)

        # 时间轮播
        timeline = Timeline(is_auto_play=True, timeline_bottom=0, width="100%")
        timeline.use_theme("dark")

        day_list = list(
            borrower_cost_data.sort_values(
                by="full_scale_time", ascending=False).drop_duplicates(
                    subset='full_scale_time', keep='first')['full_scale_time'])

        # 获取最近N天的数据
        for cur_day in day_list[self.n_show_days_short::-1]:

            # 筛选当天的数据
            df = borrower_cost_data[borrower_cost_data[
                'full_scale_time'] == cur_day][[
                    'bidding_money', 'borrower_cost_rate', 'business_type',
                    'loan_period'
                ]]
            # 将上标金额设为index，除去原上标金额列
            df.index = df.bidding_money
            df = df.drop('bidding_money', axis=1)

            #处理数据
            scatter_data = None
            # 遍历产品
            for i in set(df['business_type']):
                # 遍历审批期限
                for period in set(df[df['business_type'] == i]['loan_period']):
                    # 如果是好期待、别等待，则按期限拆分
                    if i in ['别等贷', '好期贷']:
                        cur_data = df[(df['business_type'] == i)
                                      & (df['loan_period'] == period)]
                        cur_data = cur_data[['borrower_cost_rate']]
                        cur_data.columns = [
                            i + "-" + "%02d" % period,
                        ]
                    else:
                        cur_data = df[df['business_type'] == i]
                        cur_data = cur_data[['borrower_cost_rate']]
                        cur_data.columns = [
                            i,
                        ]
                    if type(scatter_data) == pd.DataFrame:
                        scatter_data = scatter_data.append(cur_data)
                    else:
                        scatter_data = cur_data

            # 将比例乘100，保留两位小数
            scatter_data = scatter_data.applymap(lambda x: round(x * 100, 2))

            chart = render_echarts_by_lists(
                scatter_data,
                "借款人成本（年化）",
                "借款人成本（年化）散点图（横坐标为借款金额，纵坐标为借款人成本（年化））",
                chart_kind="scatter",
                dropna=True,
                xaxis_rotate=0,
                xaxis_interval=0,
                label_text_size=12,
                label_formatter=" ",
                yaxis_formatter="%",
                tooltip_formatter="{c}%",
                effect_scale=0,
                is_label_show=False,
                legend_top="80%",
                is_more_utils=False)

            # 留出空间防止legend及timeline
            grid = Grid(width="100%")
            grid.add(chart, grid_bottom='30%')
            grid

            # 往timeline中添加当前图表
            timeline.add(grid, cur_day)

        return {'chart_render': timeline.render_embed()}

    @create_chart_time
    def get_bar_borrower_cost_all_average_rate_each_prd(self):

        borrower_cost_data = copy.deepcopy(self.borrower_cost_data)

        # 时间轮播
        timeline = Timeline(is_auto_play=True, timeline_bottom=0, width="100%")
        timeline.use_theme("dark")

        ext_df = None

        day_list = list(
            borrower_cost_data.sort_values(
                by="full_scale_time", ascending=False).drop_duplicates(
                    subset='full_scale_time', keep='first')['full_scale_time'])

        for cur_day in day_list[self.n_show_days_short::-1]:
            df = borrower_cost_data[cur_day][[
                'bidding_money', 'borrower_cost_fee', 'business_type',
                'loan_period'
            ]]
            df_dict = {}
            for i in set(df['business_type']):
                for period in set(df[df['business_type'] == i]['loan_period']):
                    if i in ['别等贷', '好期贷']:
                        cur_data = df[(df['business_type'] == i)
                                      & (df['loan_period'] == period)]
                        cur_data = cur_data[[
                            'borrower_cost_fee', 'bidding_money'
                        ]]
                        cur_data = cur_data.sum()
                        df_dict[
                            i + "-" + "%02d" %
                            period] = cur_data.borrower_cost_fee / cur_data.bidding_money / period * 12

            cur_day_df = pd.DataFrame(df_dict, index=[cur_day])

            if type(ext_df) == pd.DataFrame:
                ext_df = ext_df.append(cur_day_df)
            else:
                ext_df = cur_day_df

            pt = cur_day_df.applymap(lambda x: round(x * 100, 2))

            chart = render_echarts_by_lists(
                pt,
                "各产品平均借款人成本（年化）",
                "近5工作日各产品平均借款人成本（年化）",
                dropna=True,
                xaxis_rotate=0,
                xaxis_interval=0,
                label_formatter="{c}%",
                yaxis_formatter="%",
                tooltip_formatter="{c}%",
                legend_top="80%",
                is_label_show=True)

            # 留出空间防止legend及timeline
            grid = Grid(width="100%")
            grid.use_theme("dark")
            grid.add(chart, grid_bottom='30%')

            timeline.add(grid, cur_day)

        return {'chart_render': timeline.render_embed()}

    # 收入数据对比
    @create_chart_time
    def get_bar_loan_all_income_each_prd(self):

        pt = extract_data_by_date(
            self.loan_data,
            index=['full_scale_time'],
            columns=['loan_product_ch'],
            values='assets_income',
            aggfunc=np.sum,
            margins=None,
            holidays=self.holidays)

        pt = proc_pt(
            pt,
            n_show_days=self.n_show_days_short,
            is_round=1,
            is_change_index='column')

        chart = render_echarts_by_lists(
            pt,
            "各产品放款时收入",
            "近5工作日各产品每日放款时收入（万）",
            dropna=True,
            xaxis_rotate=0,
            xaxis_interval=0,
            is_label_show=True)
        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else ""
        }

    @create_chart_time
    def get_bar_loan_all_income_dw(self):

        pt = extract_data_by_date(
            self.loan_data,
            index=['full_scale_time'],
            columns=['loan_product_ch', 'loan_period', 'month_rate'],
            values='assets_income',
            aggfunc=np.sum,
            margins=None,
            holidays=self.holidays)

        pt = proc_pt(
            pt['别等贷'],
            n_show_days=self.n_show_days_short,
            is_round=1,
            is_change_index="column")

        chart = render_echarts_by_lists(
            pt,
            "别等贷各期限放款时收入",
            "近5工作日别等贷各期限每日放款时收入",
            dropna=True,
            xaxis_rotate=0,
            xaxis_interval=0,
            label_text_size=12,
            is_label_show=True)

        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else ""
        }

    @create_chart_time
    def get_bar_loan_all_income_ge(self):

        pt = extract_data_by_date(
            self.loan_data,
            index=['full_scale_time'],
            columns=['loan_product_ch', 'loan_period', 'month_rate'],
            values='assets_income',
            aggfunc=np.sum,
            margins=None,
            holidays=self.holidays)

        pt = proc_pt(
            pt['好期贷'],
            n_show_days=self.n_show_days_short,
            is_round=1,
            is_change_index="column")

        chart = render_echarts_by_lists(
            pt,
            "好期贷各期限放款时收入",
            "近5工作日好期待各期限每日放款时收入",
            dropna=True,
            xaxis_rotate=0,
            xaxis_interval=0,
            label_text_size=12,
            is_label_show=True)

        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else ""
        }

    # 各期限对比
    @create_chart_time
    def get_bar_apply_all_bill_each_period(self):

        pt = extract_data_by_date(
            self.apply_data,
            index=['时间（-）'],
            columns=['loan_period'],
            values='customer_name',
            aggfunc=np.count_nonzero,
            margins=None,
            holidays=self.holidays)

        pt = proc_pt(
            pt, n_show_days=self.n_show_days_short, is_change_index='column')

        chart = render_echarts_by_lists(
            pt,
            "各期限申请件数",
            "近5工作日各期限申请件数",
            dropna=True,
            xaxis_rotate=0,
            xaxis_interval=0,
            label_text_size=12,
            is_label_show=True)

        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else ""
        }

    @create_chart_time
    def get_bar_loan_all_amount_each_period(self):

        pt = extract_data_by_date(
            self.loan_data,
            index=['full_scale_time'],
            columns=['loan_period'],
            values='bidding_money',
            aggfunc=np.sum,
            margins=None,
            holidays=self.holidays)

        pt = proc_pt(
            pt,
            n_show_days=self.n_show_days_short,
            is_round=1,
            is_change_index='column')

        chart = render_echarts_by_lists(
            pt,
            "各期限放款金额",
            "近5工作日各期限放款金额（万）",
            dropna=True,
            is_label_show=True,
        )

        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else ""
        }

    @create_chart_time
    def get_bar_apply_all_bill_each_period_per(self):

        pt = extract_data_by_date(
            self.apply_data,
            index=['时间（-）'],
            columns=['loan_period'],
            values='customer_name',
            aggfunc=np.count_nonzero,
            margins=None,
            holidays=self.holidays)

        pt = proc_pt(
            pt,
            n_show_days=self.n_show_days_short,
            is_change_index='column',
            change_to_percent=2)

        chart = render_echarts_by_lists(
            pt,
            "各期限申请件数",
            "近5工作日各期限申请件数占比（%）",
            dropna=True,
            xaxis_rotate=0,
            xaxis_interval=0,
            yaxis_formatter="%",
            label_formatter="{c}%",
            label_text_size=12,
            is_label_show=True)

        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else ""
        }

    @create_chart_time
    def get_bar_loan_all_amount_each_period_per(self):

        pt = extract_data_by_date(
            self.loan_data,
            index=['full_scale_time'],
            columns=['loan_period'],
            values='bidding_money',
            aggfunc=np.sum,
            margins=None,
            holidays=self.holidays)

        pt = proc_pt(
            pt,
            n_show_days=self.n_show_days_short,
            is_round=1,
            is_change_index='column',
            change_to_percent=2)

        chart = render_echarts_by_lists(
            pt,
            "各期限放款金额",
            "近5工作日各期限放款金额占比（%）",
            dropna=True,
            yaxis_formatter="%",
            label_formatter="{c}%",
            label_text_size=12,
            is_label_show=True)

        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else ""
        }

    # 还款方式对比
    @create_chart_time
    def get_bar_apply_all_bill_each_repay(self):

        pt = extract_data_by_date(
            self.apply_data,
            index=['时间（-）'],
            columns=['repayment_mode'],
            values='customer_name',
            aggfunc=np.count_nonzero,
            margins=None,
            holidays=self.holidays)

        pt = proc_pt(
            pt, n_show_days=self.n_show_days_short, is_change_index='column')

        chart = render_echarts_by_lists(
            pt,
            "各还款方式申请件数",
            "近5工作日各还款方式申请件数",
            dropna=True,
            xaxis_rotate=0,
            xaxis_interval=0,
            label_text_size=12,
            is_label_show=True)

        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else ""
        }

    @create_chart_time
    def get_bar_loan_all_amount_each_repay(self):

        pt = extract_data_by_date(
            self.loan_data,
            index=['full_scale_time'],
            columns=['repayment_mode_ch'],
            values='bidding_money',
            aggfunc=np.sum,
            margins=None,
            holidays=self.holidays)

        pt = proc_pt(
            pt,
            n_show_days=self.n_show_days_short,
            is_round=1,
            is_change_index='column')

        chart = render_echarts_by_lists(
            pt,
            "各还款方式放款金额",
            "近5工作日各还款方式还款金额（万）",
            dropna=True,
            is_label_show=True,
        )

        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else ""
        }

    @create_chart_time
    def get_bar_apply_all_bill_each_repay_per(self):

        pt = extract_data_by_date(
            self.apply_data,
            index=['时间（-）'],
            columns=['repayment_mode'],
            values='customer_name',
            aggfunc=np.count_nonzero,
            margins=None,
            holidays=self.holidays)

        pt = proc_pt(
            pt,
            n_show_days=self.n_show_days_short,
            is_change_index='column',
            change_to_percent=2)

        chart = render_echarts_by_lists(
            pt,
            "各还款方式申请件数",
            "近5工作日各还款方式申请件数占比（%）",
            dropna=True,
            xaxis_rotate=0,
            xaxis_interval=0,
            yaxis_formatter="%",
            label_formatter="{c}%",
            label_text_size=12,
            is_label_show=True)

        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else ""
        }

    @create_chart_time
    def get_bar_loan_all_amount_each_repay_per(self):

        pt = extract_data_by_date(
            self.loan_data,
            index=['full_scale_time'],
            columns=['repayment_mode_ch'],
            values='bidding_money',
            aggfunc=np.sum,
            margins=None,
            holidays=self.holidays)

        pt = proc_pt(
            pt,
            n_show_days=self.n_show_days_short,
            is_round=1,
            is_change_index='column',
            change_to_percent=2)

        chart = render_echarts_by_lists(
            pt,
            "各还款方式放款金额",
            "近5工作日各还款方式放款金额占比（%）",
            dropna=True,
            yaxis_formatter="%",
            label_formatter="{c}%",
            label_text_size=12,
            is_label_show=True)

        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else ""
        }

    # 区域数据对比
    @create_chart_time
    def get_bar_loan_all_amount_each_province_ge(self):
        '''区域放款数据对比（占比）'''

        loan_data_temp = self.loan_data.loc[
            self.loan_data.full_scale_time.isin(
                getEveryDay(
                    self.start_date.replace("-", "/"),
                    self.end_date.replace("-", "/"))), :]

        pt = extract_data_by_date(
            loan_data_temp[(loan_data_temp["loan_product_ch"] == '好期贷')],
            index=['org_province'],
            columns='loan_product_ch',
            values='bidding_money',
            aggfunc=np.sum,
            margins=None,
            holidays=self.holidays)

        pt = proc_pt(pt, n_show_days=0, is_round=1)
        pt.sort_values(by='好期贷', inplace=True, ascending=True)

        chart = render_echarts_by_lists(
            pt,
            "好期贷放款金额排名",
            "各省份好期贷放款金额（万）排名（%s-%s）" % (self.start_date, self.end_date),
            chart_kind="bar",
            dropna=True,
            xaxis_rotate=90,
            xaxis_interval=0,
            is_label_show=True,
            label_text_size=10,
            mark_line=["average"],
            width='100%',
            height=800,
            tooltip_axispointer_type="cross",
            grid_left=20)

        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else "",
            'chart': chart
        }

    @create_chart_time
    def get_bar_loan_all_amount_each_province_dw(self):
        '''区域放款数据对比（占比）'''

        loan_data_temp = self.loan_data.loc[
            self.loan_data.full_scale_time.isin(
                getEveryDay(
                    self.start_date.replace("-", "/"),
                    self.end_date.replace("-", "/"))), :]

        pt = extract_data_by_date(
            loan_data_temp[(loan_data_temp["loan_product_ch"] == '别等贷')],
            index=['org_province'],
            columns='loan_product_ch',
            values='bidding_money',
            aggfunc=np.sum,
            margins=None,
            holidays=self.holidays)

        pt = proc_pt(pt, n_show_days=0, is_round=1)
        pt.sort_values(by='别等贷', inplace=True, ascending=True)

        chart = render_echarts_by_lists(
            pt,
            "别等贷放款金额排名",
            "各省份别等贷放款金额（万）排名（%s-%s）" % (self.start_date, self.end_date),
            chart_kind="bar",
            dropna=True,
            xaxis_rotate=90,
            xaxis_interval=0,
            is_label_show=True,
            label_text_size=10,
            mark_line=["average"],
            width='100%',
            height=800,
            tooltip_axispointer_type="cross",
            grid_left=20)

        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else "",
            'chart': chart
        }

    @create_chart_time
    def get_bar_loan_all_amount_each_province_per(self):
        '''区域放款数据对比'''
        return self.get_bar_distribution(
            data_name="loan_data",
            column=None,
            column_show_name="",
            index="org_province",
            index_show_name="省份",
            value="bidding_money",
            value_show_name="放款金额",
            sort_by="bidding_money",
            label_formatter="{c}",
            xaxis_rotate=45,
            is_legend_show=False)

    # 年龄数据
    @create_chart_time
    def get_bar_loan_all_amount_each_age_range(self):
        '''放款数据各年龄段分布'''
        return self.get_bar_distribution(
            data_name="loan_data",
            column=None,
            column_show_name="",
            index="age_range",
            index_show_name="年龄段",
            value="bidding_money",
            value_show_name="放款金额",
            sort_by="bidding_money",
            label_formatter="{b},{d}%,{c}万",
            xaxis_rotate=45,
            is_legend_show=False,
            chart_kind='pie')

    # 月度汇总信息

    # 本月各产品对比
    # 各产品申请件数
    @create_chart_time
    def get_pie_apply_bill_each_prd(self, date_range=None, month=None):

        if date_range == "M":
            if month and type(month) == str:
                range_apply_data = self.apply_data[month]
            else:
                # 日期范围为本月
                range_apply_data = self.apply_data[self.select_month]
        elif date_range == "W":
            # 日期范围为星期
            range_apply_data = self.apply_data[self.select_week_start:
                                               self.select_week_end]
        else:
            range_apply_data = self.apply_data

        sub_title_range = self._sub_title_range_dict.get(date_range, "错误")

        pt = extract_data_by_date(
            range_apply_data,
            index=['loan_product'],
            values='customer_name',
            aggfunc=np.count_nonzero,
            margins=None,
            holidays=self.holidays)

        if check_pt(pt) == NONE_PT:
            return {"pt": pt, 'chart_render': "无数据"}

        pt = proc_pt(pt, n_show_days=None, columns_name=['申请件数'])

        chart = render_echarts_by_lists(
            pt,
            "各产品申请件数",
            "%s总申请%d件" % (sub_title_range, pt.sum().sum()),
            dropna=True,
            chart_kind="pie",
            xaxis_rotate=90,
            xaxis_interval=0,
            label_text_size=12,
            label_formatter="{b},{d}%",
            is_label_show=True,
            is_more_utils=True,
        )
        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else ""
        }

    @create_chart_time
    def get_pie_loan_amount_each_prd(self, date_range=None, month=None):

        if date_range == "M":
            if month and type(month) == str:
                range_loan_data = self.loan_data[month]
            else:
                # 日期范围为本月
                range_loan_data = self.loan_data[self.select_month]
        elif date_range == "W":
            # 日期范围为星期
            range_loan_data = self.loan_data[self.select_week_start:
                                             self.select_week_end]
        else:
            range_loan_data = self.loan_data

        sub_title_range = self._sub_title_range_dict.get(date_range, "错误")

        pt = extract_data_by_date(
            range_loan_data,
            index=['loan_product_ch'],
            values='bidding_money',
            aggfunc=np.sum,
            margins=None,
            holidays=self.holidays)

        if check_pt(pt) == NONE_PT:
            return {"pt": pt, 'chart_render': "无数据"}

        pt = proc_pt(pt, n_show_days=None, is_round=1, columns_name=['放款金额'])

        chart = render_echarts_by_lists(
            pt,
            "各产品放款金额",
            "%s总放款金额%.1f万" % (sub_title_range, pt.sum().sum()),
            dropna=True,
            chart_kind="pie",
            xaxis_rotate=90,
            xaxis_interval=0,
            label_formatter="{b},{d}%",
            is_label_show=True)
        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else ""
        }

    @create_chart_time
    def get_bar_loan_amount_average_each_prd(self, date_range=None,
                                             month=None):
        '''
            本月各产品件均对比
        '''

        if date_range == "M":
            if month and type(month) == str:
                range_loan_data = self.loan_data[month]
            else:
                # 日期范围为本月
                range_loan_data = self.loan_data[self.select_month]
        elif date_range == "W":
            # 日期范围为星期
            range_loan_data = self.loan_data[self.select_week_start:
                                             self.select_week_end]
        else:
            range_loan_data = self.loan_data

        sub_title_range = self._sub_title_range_dict.get(date_range, "错误")

        pt = extract_data_by_date(
            range_loan_data,
            index=['loan_product_ch'],
            values='bidding_money',
            aggfunc=np.average,
            margins=None,
            holidays=self.holidays)

        if check_pt(pt) == NONE_PT:
            return {"pt": pt, 'chart_render': "无数据"}

        pt = proc_pt(
            pt, n_show_days=None, is_round=1, columns_name=['放款件均(万)'])
        pt.sort_values(by='放款件均(万)', inplace=True, ascending=True)

        chart = render_echarts_by_lists(
            pt,
            "各产品放款件均",
            "%s平均放款件均%.2f万" % (sub_title_range,
                               range_loan_data['bidding_money'].mean()),
            dropna=True,
            chart_kind="line",
            xaxis_interval=0,
            yaxis_min=round(pt.min().min() / 1.2, 2),
            yaxis_max=round(pt.max().max() * 1.1, 2),
            label_text_size=12,
            is_label_show=True,
            is_more_utils=True)

        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else ""
        }

    @create_chart_time
    def get_bar_loan_period_average_each_prd(self, date_range=None,
                                             month=None):
        '''
            本月各产品期均对比
        '''

        if date_range == "M":
            if month and type(month) == str:
                range_loan_data = self.loan_data[month]
            else:
                # 日期范围为本月
                range_loan_data = self.loan_data[self.select_month]
        elif date_range == "W":
            # 日期范围为星期
            range_loan_data = self.loan_data[self.select_week_start:
                                             self.select_week_end]
        else:
            range_loan_data = self.loan_data

        sub_title_range = self._sub_title_range_dict.get(date_range, "错误")

        pt = extract_data_by_date(
            range_loan_data,
            index=['loan_product_ch'],
            values='loan_period',
            aggfunc=np.average,
            margins=None,
            holidays=self.holidays)

        if check_pt(pt) == NONE_PT:
            return {"pt": pt, 'chart_render': "无数据"}

        pt = proc_pt(
            pt, n_show_days=None, is_round=1, columns_name=['放款期均（月）'])
        pt.sort_values(by='放款期均（月）', inplace=True, ascending=True)

        chart = render_echarts_by_lists(
            pt,
            "各产品平均放款期限",
            "%s平均放款期限%.2f月" % (sub_title_range,
                               range_loan_data['loan_period'].mean()),
            dropna=True,
            chart_kind="line",
            xaxis_interval=0,
            yaxis_min=round(pt.min().min() / 1.2, 2),
            yaxis_max=round(pt.max().max() * 1.1, 2),
            label_text_size=12,
            is_label_show=True,
            is_more_utils=True)

        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else ""
        }

    @create_chart_time
    def get_bar_review_pass_rate_each_prd(self, date_range="M", month=None):
        '''
            本月各产品审批通过率对比
        '''

        if date_range == "M":
            if month and type(month) == str:
                range_review_data = self.review_data[month]
            else:
                # 日期范围为本月
                range_review_data = self.review_data[self.select_month]
        elif date_range == "W":
            # 日期范围为星期
            range_review_data = self.review_data[self.select_week_start:
                                                 self.select_week_end]
        else:
            range_review_data = self.review_data

        sub_title_range = self._sub_title_range_dict.get(date_range, "错误")

        pt = extract_data_by_date(
            range_review_data,
            index=['借款类型'],
            columns=['终审审核结果'],
            values='借款单ID',
            aggfunc=np.count_nonzero,
            margins=None,
            holidays=self.holidays)

        if check_pt(pt) == NONE_PT:
            return {"pt": pt, 'chart_render': "无数据"}

        for i in ['通过', '拒绝']:
            if i not in pt.columns:
                pt[i] = 0

        pass_rate_average = pt["通过"].sum() / (pt["拒绝"].sum() + pt["通过"].sum())
        pt['审批通过率'] = pt["通过"] / (pt["通过"] + pt["拒绝"]) * 100
        pt = pt[['审批通过率']]
        pt = proc_pt(pt, n_show_days=None, is_round=1, columns_name=['审批通过率'])
        pt.sort_values(by='审批通过率', inplace=True, ascending=True)

        chart = render_echarts_by_lists(
            pt,
            "各产品审批通过率",
            "%s总审批通过率为%.2f%%" % (sub_title_range, (pass_rate_average * 100)),
            dropna=True,
            chart_kind="line",
            xaxis_interval=0,
            yaxis_min=round(pt.min().min() / 1.1, 2),
            yaxis_max=pt.max().max(),
            yaxis_formatter="%",
            label_formatter="{c}%",
            label_text_size=12,
            is_label_show=True,
            is_more_utils=True)

        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else ""
        }

    @create_chart_time
    def get_bar_borrower_cost_average_rate_each_prd(self,
                                                    date_range="M",
                                                    month=None):
        '''
            本月各产品借款人成本对比
        '''

        if date_range == "M":
            if month and type(month) == str:
                range_borrower_cost_data = self.borrower_cost_data[month]
            else:
                # 日期范围为本月
                range_borrower_cost_data = self.borrower_cost_data[
                    self.select_month]
        elif date_range == "W":
            # 日期范围为星期
            range_borrower_cost_data = self.borrower_cost_data[
                self.select_week_start:self.select_week_end]
        else:
            range_borrower_cost_data = self.borrower_cost_data

        sub_title_range = self._sub_title_range_dict.get(date_range, "错误")

        df = range_borrower_cost_data[[
            'bidding_money', 'borrower_cost_fee', 'business_type',
            'loan_period'
        ]]
        df_dict = {}
        for i in set(df['business_type']):
            for period in set(df[df['business_type'] == i]['loan_period']):
                if i in ['别等贷', '好期贷']:
                    cur_data = df[(df['business_type'] == i)
                                  & (df['loan_period'] == period)]
                    cur_data = cur_data[['borrower_cost_fee', 'bidding_money']]
                    cur_data = cur_data.sum()
                    df_dict[
                        i + "-" + "%02d" %
                        period] = cur_data.borrower_cost_fee / cur_data.bidding_money / period * 12

        cur_df = pd.DataFrame(df_dict, index=['借款人成本'])

        pt = cur_df.applymap(lambda x: round(x * 100, 2))

        chart = render_echarts_by_lists(
            pt,
            "%s各产品平均借款人成本" % sub_title_range,
            "",
            dropna=True,
            xaxis_rotate=0,
            xaxis_interval=0,
            label_formatter="{c}%",
            yaxis_formatter="%",
            tooltip_formatter="{c}%",
            legend_top="bottom",
            is_label_show=True)

        # 留出空间防止legend及timeline
        grid = Grid(width="100%")
        grid.use_theme("dark")
        grid.add(chart, grid_bottom='20%')

        return {'chart_render': grid.render_embed()}

    @create_chart_time
    def get_pie_loan_income_each_prd(self, date_range=None, month=None):
        '''各产品放款时收入'''

        if date_range == "M":
            if month and type(month) == str:
                range_loan_data = self.loan_data[month]
            else:
                # 日期范围为本月
                range_loan_data = self.loan_data[self.select_month]
        elif date_range == "W":
            # 日期范围为星期
            range_loan_data = self.loan_data[self.select_week_start:
                                             self.select_week_end]
        else:
            range_loan_data = self.loan_data

        sub_title_range = self._sub_title_range_dict.get(date_range, "错误")

        pt = extract_data_by_date(
            range_loan_data,
            index=['loan_product_ch'],
            values='assets_income',
            aggfunc=np.sum,
            margins=None,
            holidays=self.holidays)

        if check_pt(pt) == NONE_PT:
            return {"pt": pt, 'chart_render': "无数据"}

        pt = proc_pt(pt, n_show_days=None, is_round=1)

        chart = render_echarts_by_lists(
            pt,
            "各产品放款时收入",
            "%s总放款时收入%.1f万" % (sub_title_range, pt.sum().sum()),
            dropna=True,
            chart_kind="pie",
            xaxis_rotate=90,
            xaxis_interval=0,
            label_formatter="{b},{d}%",
            is_label_show=True)
        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else ""
        }

    @create_chart_time
    def get_pie_instock_income_each_prd(self, date_range=None, month=None):
        '''产品存量收入'''

        if date_range == "M":
            if month and type(month) == str:
                range_instock_income_data = self.instock_income_data[month]
            else:
                # 日期范围为本月
                range_instock_income_data = self.instock_income_data[
                    self.select_month]
        elif date_range == "W":
            # 日期范围为星期
            range_instock_income_data = self.instock_income_data[
                self.select_week_start:self.select_week_end]
        else:
            range_instock_income_data = self.instock_income_data

        range_instock_income_data = range_instock_income_data[
            range_instock_income_data.is_paid == '已还']

        sub_title_range = self._sub_title_range_dict.get(date_range, "错误")

        pt = extract_data_by_date(
            range_instock_income_data,
            index=['loan_product'],
            values='month_assets_income',
            aggfunc=np.sum,
            margins=None,
            holidays=self.holidays)

        if check_pt(pt) == NONE_PT:
            return {"pt": pt, 'chart_render': "无数据"}

        pt = proc_pt(pt, n_show_days=None, is_round=1)

        chart = render_echarts_by_lists(
            pt,
            "各产品存量收入",
            "%s总存量收入%.1f万" % (sub_title_range, pt.sum().sum()),
            dropna=True,
            chart_kind="pie",
            xaxis_rotate=90,
            xaxis_interval=0,
            label_formatter="{b},{d}%",
            is_label_show=True)
        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else ""
        }

    @create_chart_time
    def get_pie_loan_amount_distribution(self, date_range=None, month=None):

        if date_range == "M":
            if month and type(month) == str:
                range_loan_data = self.loan_data[month]
            else:
                # 日期范围为本月
                range_loan_data = self.loan_data[self.select_month]
        elif date_range == "W":
            # 日期范围为星期
            range_loan_data = self.loan_data[self.select_week_start:
                                             self.select_week_end]
        else:
            range_loan_data = self.loan_data

        sub_title_range = self._sub_title_range_dict.get(date_range, "错误")

        pt = extract_data_by_date(
            range_loan_data,
            index=['loan_amount_distribution'],
            values='bidding_money',
            aggfunc=np.count_nonzero,
            margins=None,
            holidays=self.holidays)

        if check_pt(pt) == NONE_PT:
            return {"pt": pt, 'chart_render': "无数据"}

        pt = proc_pt(pt, n_show_days=None, is_round=1, columns_name=['放款金额'])

        chart = render_echarts_by_lists(
            pt,
            "放款金额分布",
            "%s总放款%.1f件" % (sub_title_range, pt.sum().sum()),
            dropna=True,
            chart_kind="pie",
            xaxis_rotate=90,
            xaxis_interval=0,
            label_formatter="{b},{c}笔,{d}%",
            is_label_show=True)
        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else ""
        }

    @create_chart_time
    def get_bar_apply_bill(self, groupby="D", date_range="M", month=None):
        '''
            申请件数本月每日走势
        '''
        if date_range == "M":
            if month and type(month) == str:
                range_apply_data = self.apply_data[month]
            else:
                # 日期范围为本月
                range_apply_data = self.apply_data[self.select_month]
        elif date_range == "W":
            # 日期范围为星期
            range_apply_data = self.apply_data[self.select_week_start:
                                               self.select_week_end]
        else:
            range_apply_data = self.apply_data

        sub_title_range = self._sub_title_range_dict.get(date_range, "错误")
        sub_title_frq = self._sub_title_frq_dict.get(groupby, "错误")

        pt = extract_data_by_date(
            range_apply_data,
            index=['create_time'],
            values='customer_name',
            aggfunc=np.count_nonzero,
            margins=None,
            groupby=groupby,
            holidays=self.holidays)

        if check_pt(pt) == NONE_PT:
            return {
                "pt": pt,
                'chart_render': "无数据",
                "mom_pt": pt,
                "mom_chart": "无数据"
            }

        pt = proc_pt(pt, n_show_days=None, is_round=1, columns_name=['申请件数'])

        chart = render_echarts_by_lists(
            pt,
            "%s申请件数%s走势" % (sub_title_range, sub_title_frq),
            "",
            chart_kind="line",
            dropna=True,
            xaxis_rotate=90,
            xaxis_interval=0,
            label_text_size=12,
            is_label_show=True,
            mark_line=["average"],
            is_smooth=True,
            is_fill=True,
            area_opacity=0.3,
            is_more_utils=True)

        # 计算环比数据透视表
        mom_pt = (pt / pt.shift(1) - 1) * 100
        mom_pt = proc_pt(mom_pt, is_round=2, n_show_days=None)

        mom_chart = render_echarts_by_lists(
            mom_pt,
            "",
            "环比",
            height=200,
            chart_kind="line",
            dropna=True,
            xaxis_rotate=90,
            xaxis_interval=0,
            label_text_size=12,
            yaxis_formatter="%",
            label_formatter="{c}%",
            is_label_show=True,
            mark_line=["average"],
            is_smooth=True,
            is_fill=True,
            area_opacity=0.3,
            is_more_utils=False)

        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else "",
            "mom_pt": mom_pt,
            "mom_chart": mom_chart.render_embed()
        }

    @create_chart_time
    def get_bar_loan_amount(self, groupby="D", date_range="M", month=None):
        '''
            放款金额本月每日走势
        '''

        if date_range == "M":
            if month and type(month) == str:
                range_loan_data = self.loan_data[month]
            else:
                # 日期范围为本月
                range_loan_data = self.loan_data[self.select_month]
        elif date_range == "W":
            # 日期范围为星期
            range_loan_data = self.loan_data[self.select_week_start:
                                             self.select_week_end]
        else:
            range_loan_data = self.loan_data

        sub_title_range = self._sub_title_range_dict.get(date_range, "错误")
        sub_title_frq = self._sub_title_frq_dict.get(groupby, "错误")

        pt = extract_data_by_date(
            range_loan_data,
            index=['time'],
            values='bidding_money',
            aggfunc=np.sum,
            margins=None,
            groupby=groupby,
            holidays=self.holidays)

        if check_pt(pt) == NONE_PT:
            return {
                "pt": pt,
                'chart_render': "无数据",
                "mom_pt": pt,
                "mom_chart": "无数据"
            }

        pt = proc_pt(pt, n_show_days=25, is_round=1, columns_name=['放款金额（万）'])

        chart = render_echarts_by_lists(
            pt,
            "%s放款金额（万）%s走势" % (sub_title_range, sub_title_frq),
            "",
            chart_kind="line",
            dropna=True,
            xaxis_rotate=90,
            xaxis_interval=0,
            label_text_size=12,
            is_label_show=True,
            mark_line=["average"],
            is_smooth=True,
            is_fill=True,
            area_opacity=0.3,
            is_more_utils=True)

        # 计算环比数据透视表
        mom_pt = (pt / pt.shift(1) - 1) * 100
        mom_pt = proc_pt(mom_pt, is_round=2, n_show_days=None)

        mom_chart = render_echarts_by_lists(
            mom_pt,
            "",
            "环比",
            height=200,
            chart_kind="line",
            dropna=True,
            xaxis_rotate=90,
            xaxis_interval=0,
            label_text_size=12,
            yaxis_formatter="%",
            label_formatter="{c}%",
            is_label_show=True,
            mark_line=["average"],
            is_smooth=True,
            is_fill=True,
            area_opacity=0.3,
            is_more_utils=False)

        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else "",
            "mom_pt": mom_pt,
            "mom_chart": mom_chart.render_embed()
        }

    @create_chart_time
    def get_bar_loan_amount_average(self,
                                    groupby="D",
                                    date_range="M",
                                    month=None):
        '''
            放款件均本月每日走势
        '''

        if date_range == "M":
            if month and type(month) == str:
                range_loan_data = self.loan_data[month]
            else:
                # 日期范围为本月
                range_loan_data = self.loan_data[self.select_month]
        elif date_range == "W":
            # 日期范围为星期
            range_loan_data = self.loan_data[self.select_week_start:
                                             self.select_week_end]
        else:
            range_loan_data = self.loan_data

        sub_title_range = self._sub_title_range_dict.get(date_range, "错误")

        sub_title_frq = self._sub_title_frq_dict.get(groupby, "错误")

        pt = extract_data_by_date(
            range_loan_data,
            index=['index'],
            values='bidding_money',
            aggfunc=np.average,
            margins=None,
            groupby=groupby,
            how="mean",
            holidays=self.holidays)

        if check_pt(pt) == NONE_PT:
            return {
                "pt": pt,
                'chart_render': "无数据",
                "mom_pt": pt,
                "mom_chart": "无数据"
            }

        pt = proc_pt(pt, n_show_days=25, is_round=1, columns_name=['放款件均'])

        chart = render_echarts_by_lists(
            pt,
            "%s放款件均%s走势" % (sub_title_range, sub_title_frq),
            "",
            chart_kind="line",
            dropna=True,
            xaxis_rotate=90,
            xaxis_interval=0,
            label_text_size=12,
            is_label_show=True,
            mark_line=["average"],
            is_smooth=True,
            is_fill=True,
            area_opacity=0.3,
            is_more_utils=True)

        # 计算环比数据透视表
        mom_pt = (pt / pt.shift(1) - 1) * 100
        mom_pt = proc_pt(mom_pt, is_round=2, n_show_days=None)

        mom_chart = render_echarts_by_lists(
            mom_pt,
            "",
            "环比",
            height=200,
            chart_kind="line",
            dropna=True,
            xaxis_rotate=90,
            xaxis_interval=0,
            label_text_size=12,
            yaxis_formatter="%",
            label_formatter="{c}%",
            is_label_show=True,
            mark_line=["average"],
            is_smooth=True,
            is_fill=True,
            area_opacity=0.3,
            is_more_utils=False)

        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else "",
            "mom_pt": mom_pt,
            "mom_chart": mom_chart.render_embed()
        }

    @create_chart_time
    def get_bar_loan_period_average(self,
                                    groupby="D",
                                    date_range="M",
                                    month=None):
        '''
            放款期均本月每日走势
        '''

        if date_range == "M":
            if month and type(month) == str:
                range_loan_data = self.loan_data[month]
            else:
                # 日期范围为本月
                range_loan_data = self.loan_data[self.select_month]
        elif date_range == "W":
            # 日期范围为星期
            range_loan_data = self.loan_data[self.select_week_start:
                                             self.select_week_end]
        else:
            range_loan_data = self.loan_data

        sub_title_range = self._sub_title_range_dict.get(date_range, "错误")
        sub_title_frq = self._sub_title_frq_dict.get(groupby, "每月")

        pt = extract_data_by_date(
            range_loan_data,
            index=['time'],
            values='loan_period',
            aggfunc=np.average,
            margins=None,
            groupby=groupby,
            how="mean",
            holidays=self.holidays)

        if check_pt(pt) == NONE_PT:
            return {
                "pt": pt,
                'chart_render': "无数据",
                "mom_pt": pt,
                "mom_chart": "无数据"
            }

        pt = proc_pt(pt, n_show_days=25, is_round=1, columns_name=['放款期均'])

        chart = render_echarts_by_lists(
            pt,
            "%s平均放款期限%s走势" % (sub_title_range, sub_title_frq),
            "",
            chart_kind="line",
            dropna=True,
            xaxis_rotate=90,
            xaxis_interval=0,
            label_text_size=12,
            is_label_show=True,
            mark_line=["average"],
            is_smooth=True,
            is_fill=True,
            area_opacity=0.3,
            is_more_utils=True)

        # 计算环比数据透视表
        mom_pt = (pt / pt.shift(1) - 1) * 100
        mom_pt = proc_pt(mom_pt, is_round=2, n_show_days=None)

        mom_chart = render_echarts_by_lists(
            mom_pt,
            "",
            "环比",
            height=200,
            chart_kind="line",
            dropna=True,
            xaxis_rotate=90,
            xaxis_interval=0,
            label_text_size=12,
            yaxis_formatter="%",
            label_formatter="{c}%",
            is_label_show=True,
            mark_line=["average"],
            is_smooth=True,
            is_fill=True,
            area_opacity=0.3,
            is_more_utils=False)

        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else "",
            "mom_pt": mom_pt,
            "mom_chart": mom_chart.render_embed()
        }

    @create_chart_time
    def get_bar_review_pass_rate(self, groupby="D", date_range="M",
                                 month=None):
        '''
            审批通过率本月每日走势
        '''

        if date_range == "M":
            if month and type(month) == str:
                range_review_data = self.review_data[month]
            else:
                # 日期范围为本月
                range_review_data = self.review_data[self.select_month]
        elif date_range == "W":
            # 日期范围为星期
            range_review_data = self.review_data[self.select_week_start:
                                                 self.select_week_end]
        else:
            range_review_data = self.review_data

        sub_title_range = self._sub_title_range_dict.get(date_range, "错误")
        sub_title_frq = self._sub_title_frq_dict.get(groupby, "每月")

        pt = extract_data_by_date(
            range_review_data,
            index=['第一次提交初审时间'],
            columns=['终审审核结果'],
            values='借款单ID',
            aggfunc=np.count_nonzero,
            margins=None,
            groupby=groupby,
            holidays=self.holidays)

        if check_pt(pt) == NONE_PT:
            return {
                "pt": pt,
                'chart_render': "无数据",
                "mom_pt": pt,
                "mom_chart": "无数据"
            }

        for i in ['通过', '拒绝']:
            if i not in pt.columns:
                pt[i] = 0

        pt.loc[:, '审批通过率'] = pt["通过"] / (pt["通过"] + pt["拒绝"]) * 100
        pt = pt[['审批通过率']]
        pt = proc_pt(pt, n_show_days=25, is_round=1, columns_name=['审批通过率'])

        pt_min = pt.min().min()

        chart = render_echarts_by_lists(
            pt,
            "%s审批通过率%s走势" % (sub_title_range, sub_title_frq),
            "",
            chart_kind="line",
            dropna=True,
            xaxis_rotate=90,
            xaxis_interval=0,
            yaxis_min=pt_min,
            yaxis_max="dataMax",
            yaxis_formatter="%",
            label_formatter="{c}%",
            label_text_size=12,
            is_label_show=True,
            mark_line=["average"],
            is_smooth=True,
            is_fill=True,
            area_opacity=0.1,
            is_more_utils=True)

        # 计算环比数据透视表
        mom_pt = (pt / pt.shift(1) - 1) * 100
        mom_pt = proc_pt(mom_pt, is_round=2, n_show_days=None)

        mom_chart = render_echarts_by_lists(
            mom_pt,
            "",
            "环比",
            height=200,
            chart_kind="line",
            dropna=True,
            xaxis_rotate=90,
            xaxis_interval=0,
            label_text_size=12,
            yaxis_formatter="%",
            label_formatter="{c}%",
            is_label_show=True,
            mark_line=["average"],
            is_smooth=True,
            is_fill=True,
            area_opacity=0.3,
            is_more_utils=False)

        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else "",
            "mom_pt": mom_pt,
            "mom_chart": mom_chart.render_embed()
        }

    @create_chart_time
    def get_bar_loan_income(self, groupby="D", date_range="M", month=None):
        '''
            放款时收入本月每日走势
        '''

        if date_range == "M":
            if month and type(month) == str:
                range_loan_data = self.loan_data[month]
            else:
                # 日期范围为本月
                range_loan_data = self.loan_data[self.select_month]
        elif date_range == "W":
            # 日期范围为星期
            range_loan_data = self.loan_data[self.select_week_start:
                                             self.select_week_end]
        else:
            range_loan_data = self.loan_data

        sub_title_range = self._sub_title_range_dict.get(date_range, "错误")
        sub_title_frq = self._sub_title_frq_dict.get(groupby, "每月")

        pt = extract_data_by_date(
            range_loan_data,
            index=['time'],
            values='assets_income',
            aggfunc=np.sum,
            margins=None,
            groupby=groupby,
            holidays=self.holidays)

        if check_pt(pt) == NONE_PT:
            return {
                "pt": pt,
                'chart_render': "无数据",
                "mom_pt": pt,
                "mom_chart": "无数据"
            }

        pt = proc_pt(pt, n_show_days=25, is_round=1, columns_name=['放款时收入（万）'])

        chart = render_echarts_by_lists(
            pt,
            "%s放款时收入（万）%s走势" % (sub_title_range, sub_title_frq),
            "",
            chart_kind="line",
            dropna=True,
            xaxis_rotate=90,
            xaxis_interval=0,
            label_text_size=12,
            is_label_show=True,
            mark_line=["average"],
            is_smooth=True,
            is_fill=True,
            area_opacity=0.3,
            is_more_utils=True)

        # 计算环比数据透视表
        mom_pt = (pt / pt.shift(1) - 1) * 100
        mom_pt = proc_pt(mom_pt, is_round=2, n_show_days=None)

        mom_chart = render_echarts_by_lists(
            mom_pt,
            "",
            "环比",
            height=200,
            chart_kind="line",
            dropna=True,
            xaxis_rotate=90,
            xaxis_interval=0,
            label_text_size=12,
            yaxis_formatter="%",
            label_formatter="{c}%",
            is_label_show=True,
            mark_line=["average"],
            is_smooth=True,
            is_fill=True,
            area_opacity=0.3,
            is_more_utils=False)

        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else "",
            "mom_pt": mom_pt,
            "mom_chart": mom_chart.render_embed()
        }

    @create_chart_time
    def get_bar_instock_income(self, groupby="D", date_range="M", month=None):
        '''
            存量收入走势图
        '''

        if date_range == "M":
            if month and type(month) == str:
                range_instock_income_data = self.instock_income_data[month]
            else:
                # 日期范围为本月
                range_instock_income_data = self.instock_income_data[
                    self.select_month]
        elif date_range == "W":
            # 日期范围为星期
            range_instock_income_data = self.instock_income_data[
                self.select_week_start:self.select_week_end]
        else:
            range_instock_income_data = self.instock_income_data

        sub_title_range = self._sub_title_range_dict.get(date_range, "错误")
        sub_title_frq = self._sub_title_frq_dict.get(groupby, "每月")

        range_instock_income_data.sort_values(by='due_date', inplace=True)

        pt = pd.pivot_table(
            range_instock_income_data,
            index='due_date',
            columns='is_paid',
            values='month_assets_income',
            aggfunc=np.sum)

        if check_pt(pt) == NONE_PT:
            return {
                "pt": pt,
                'chart_render': "无数据",
                "mom_pt": pt,
                "mom_chart": "无数据"
            }

        pt.index = pd.to_datetime(pt.index)

        if groupby == "M":

            pt = getattr(pt.resample(groupby, kind="period"), "sum")()

            next_month = (
                datetime.now() + relativedelta(months=1)).strftime("%Y-%m")
            pt = pt[:next_month]
            pt = proc_pt(pt, n_show_days=5, is_round=1)

        chart = render_echarts_by_lists(
            pt,
            "%s在库收入（万）%s走势" % (sub_title_range, sub_title_frq),
            "",
            chart_kind="line",
            dropna=True,
            xaxis_interval=0,
            label_text_size=12,
            is_label_show=True,
            mark_line=["average"],
            is_smooth=True,
            is_fill=True,
            area_opacity=0.3,
            is_more_utils=True)

        # 计算环比数据透视表
        pt_paid = pt[['已还']]
        mom_pt = (pt_paid / pt_paid.shift(1) - 1) * 100
        mom_pt = proc_pt(mom_pt, is_round=2, n_show_days=None)

        mom_chart = render_echarts_by_lists(
            mom_pt,
            "",
            "环比",
            height=200,
            chart_kind="line",
            dropna=True,
            xaxis_rotate=90,
            xaxis_interval=0,
            label_text_size=12,
            yaxis_formatter="%",
            label_formatter="{c}%",
            is_label_show=True,
            mark_line=["average"],
            is_smooth=True,
            is_fill=True,
            area_opacity=0.3,
            is_more_utils=False)

        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else "",
            "mom_pt": mom_pt,
            "mom_chart": mom_chart.render_embed()
        }

    def get_line_paid_bill(self,
                           groupby="D",
                           date_range="ALL",
                           month=None,
                           show_restrict=True):
        '''
            还款件数统计
        '''
        if date_range == "M":
            if month and type(month) == str:
                range_paid_data = self.paid_data[month]
            else:
                # 日期范围为本月
                range_paid_data = self.paid_data[self.select_month]
        elif date_range == "W":
            # 日期范围为星期
            range_paid_data = self.paid_data[self.select_week_start:
                                             self.select_week_end]
        else:
            range_paid_data = self.paid_data

        sub_title_range = self._sub_title_range_dict.get(date_range, "错误")
        sub_title_frq = self._sub_title_frq_dict.get(groupby, "错误")

        pt = extract_data_by_date(
            range_paid_data,
            index=['index'],
            values='refund_actual_id',
            aggfunc=np.count_nonzero,
            margins=None,
            groupby=groupby,
            holidays=self.holidays)

        if check_pt(pt) == NONE_PT:
            return {
                "pt": pt,
                'chart_render': "无数据",
                "mom_pt": pt,
                "mom_chart": "无数据"
            }
        if show_restrict:
            pt = proc_pt(
                pt,
                n_show_days=self.n_show_days_long,
                is_round=1,
                columns_name=['还款件数'])
        else:
            pt = proc_pt(
                pt, n_show_days=None, is_round=1, columns_name=['还款件数'])

        chart = render_echarts_by_lists(
            pt,
            "%s还款件数%s走势" % (sub_title_range, sub_title_frq),
            "",
            chart_kind="line",
            dropna=True,
            xaxis_rotate=90,
            xaxis_interval=0,
            label_text_size=12,
            is_label_show=True,
            mark_line=["average"],
            is_smooth=True,
            is_fill=True,
            area_opacity=0.3,
            is_more_utils=True)

        # 计算环比数据透视表
        mom_pt = (pt / pt.shift(1) - 1) * 100
        mom_pt = proc_pt(mom_pt, is_round=2, n_show_days=None)

        mom_chart = render_echarts_by_lists(
            mom_pt,
            "",
            "环比",
            height=200,
            chart_kind="line",
            dropna=True,
            xaxis_rotate=90,
            xaxis_interval=0,
            label_text_size=12,
            yaxis_formatter="%",
            label_formatter="{c}%",
            is_label_show=True,
            mark_line=["average"],
            is_smooth=True,
            is_fill=True,
            area_opacity=0.3,
            is_more_utils=False)

        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else "",
            "mom_pt": mom_pt,
            "mom_chart": mom_chart.render_embed(),
            "chart": chart
        }

    def get_line_paid_income(self,
                             groupby="D",
                             date_range="ALL",
                             month=None,
                             show_restrict=True):
        '''
            还款金额（月服务费）
        '''
        if date_range == "M":
            if month and type(month) == str:
                range_paid_data = self.paid_data[month]
            else:
                # 日期范围为本月
                range_paid_data = self.paid_data[self.select_month]
        elif date_range == "W":
            # 日期范围为星期
            range_paid_data = self.paid_data[self.select_week_start:
                                             self.select_week_end]
        else:
            range_paid_data = self.paid_data

        sub_title_range = self._sub_title_range_dict.get(date_range, "错误")
        sub_title_frq = self._sub_title_frq_dict.get(groupby, "错误")

        pt = extract_data_by_date(
            range_paid_data,
            index=['index'],
            values='month_assets_income',
            aggfunc=np.sum,
            margins=None,
            groupby=groupby,
            holidays=self.holidays)

        if check_pt(pt) == NONE_PT:
            return {
                "pt": pt,
                'chart_render': "无数据",
                "mom_pt": pt,
                "mom_chart": "无数据"
            }

        pt = pt / 10000  #单位转换成W

        if show_restrict:
            pt = proc_pt(
                pt,
                n_show_days=self.n_show_days_long,
                is_round=1,
                columns_name=['还款件数'])
        else:
            pt = proc_pt(
                pt, n_show_days=None, is_round=1, columns_name=['还款件数'])

        chart = render_echarts_by_lists(
            pt,
            "%s还款金额（月服务费W）%s走势" % (sub_title_range, sub_title_frq),
            "",
            chart_kind="line",
            dropna=True,
            xaxis_rotate=90,
            xaxis_interval=0,
            label_text_size=12,
            is_label_show=True,
            mark_line=["average"],
            is_smooth=True,
            is_fill=True,
            area_opacity=0.3,
            is_more_utils=True)

        # 计算环比数据透视表
        mom_pt = (pt / pt.shift(1) - 1) * 100
        mom_pt = proc_pt(mom_pt, is_round=2, n_show_days=None)

        mom_chart = render_echarts_by_lists(
            mom_pt,
            "",
            "环比",
            height=200,
            chart_kind="line",
            dropna=True,
            xaxis_rotate=90,
            xaxis_interval=0,
            label_text_size=12,
            yaxis_formatter="%",
            label_formatter="{c}%",
            is_label_show=True,
            mark_line=["average"],
            is_smooth=True,
            is_fill=True,
            area_opacity=0.3,
            is_more_utils=False)

        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else "",
            "mom_pt": mom_pt,
            "mom_chart": mom_chart.render_embed(),
            "chart": chart
        }

    def get_line_instock_amount(self,
                                groupby="D",
                                date_range="ALL",
                                month=None,
                                show_restrict=True):
        '''
            在库金额
        '''
        if date_range == "M":
            if month and type(month) == str:
                range_instock_collection_data = self.instock_collection_data[
                    month]
            else:
                # 日期范围为本月
                range_instock_collection_data = self.instock_collection_data[
                    self.select_month]
        elif date_range == "W":
            # 日期范围为星期
            range_instock_collection_data = self.instock_collection_data[
                self.select_week_start:self.select_week_end]
        else:
            range_instock_collection_data = self.instock_collection_data

        sub_title_range = self._sub_title_range_dict.get(date_range, "错误")
        sub_title_frq = self._sub_title_frq_dict.get(groupby, "错误")

        pt = extract_data_by_date(
            range_instock_collection_data,
            index=['index'],
            values='sy_bj',
            aggfunc=np.sum,
            margins=None,
            groupby=groupby,
            how="max",
            holidays=self.holidays)

        if check_pt(pt) == NONE_PT:
            return {
                "pt": pt,
                'chart_render': "无数据",
                "mom_pt": pt,
                "mom_chart": "无数据"
            }

        pt = pt / 100000000  #单位转换成亿

        if show_restrict:
            pt = proc_pt(
                pt,
                n_show_days=self.n_show_days_long,
                is_round=2,
                columns_name=['在库金额'])
        else:
            pt = proc_pt(
                pt, n_show_days=None, is_round=2, columns_name=['在库金额(亿)'])

        chart = render_echarts_by_lists(
            pt,
            "%s在库金额（亿）%s走势" % (sub_title_range, sub_title_frq),
            "",
            chart_kind="line",
            legend_name=["在库金额"],
            dropna=True,
            xaxis_rotate=90,
            xaxis_interval=0,
            yaxis_min=pt.min().min(),
            label_text_size=12,
            is_label_show=True,
            mark_line=["average"],
            is_smooth=True,
            is_fill=True,
            area_opacity=0.3,
            is_more_utils=True)

        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else "",
            "chart": chart
        }

    def get_line_repay_income_perdict(self,
                                      groupby="D",
                                      date_range="ALL",
                                      month=None,
                                      show_restrict=False):
        '''
            还款件数本月每日走势
        '''
        if date_range == "M":
            if month and type(month) == str:
                range_repay_collection_data = self.repay_collection_data[month]
            else:
                # 日期范围为本月
                range_repay_collection_data = self.repay_collection_data[
                    self.select_month]
        elif date_range == "W":
            # 日期范围为星期
            range_repay_collection_data = self.repay_collection_data[
                self.select_week_start:self.select_week_end]
        elif date_range == "ALL":
            if groupby == "D":
                range_repay_collection_data = self.repay_collection_data[
                    datetime.now():]
            elif groupby == "M":
                range_repay_collection_data = self.repay_collection_data[
                    self.select_month:]
        else:
            range_repay_collection_data = self.repay_collection_data

        sub_title_range = self._sub_title_range_dict.get(date_range, "错误")
        sub_title_frq = self._sub_title_frq_dict.get(groupby, "错误")

        pt = extract_data_by_date(
            range_repay_collection_data,
            index=['index'],
            values='month_assets_income',
            aggfunc=np.sum,
            margins=None,
            groupby=groupby,
            holidays=self.holidays)

        if check_pt(pt) == NONE_PT:
            return {
                "pt": pt,
                'chart_render': "无数据",
                "mom_pt": pt,
                "mom_chart": "无数据"
            }

        pt = pt / 10000  #单位转换成万

        if show_restrict:
            pt = proc_pt(
                pt,
                n_show_days=self.n_show_days_long,
                is_round=2,
                columns_name=['月服务费还款金额'])
        else:
            pt = proc_pt(
                pt, n_show_days=None, is_round=1, columns_name=['月服务费还款金额'])

        if groupby == "D":
            datazoom_range = [0, 3]
        elif groupby == "M":
            datazoom_range = [0, 20]
        else:
            datazoom_range = [0, 50]
        chart = render_echarts_by_lists(
            pt,
            "预测未来月服务费还款金额（万）%s走势" % (sub_title_frq),
            "还款无逾期的情况下",
            chart_kind="line",
            legend_name=["月服务费还款金额"],
            dropna=True,
            xaxis_rotate=90,
            xaxis_interval=0,
            yaxis_min=pt.min().min(),
            label_text_size=12,
            is_label_show=True,
            mark_line=["average"],
            is_datazoom_show=True,
            datazoom_range=datazoom_range,
            is_smooth=True,
            is_fill=True,
            area_opacity=0.3,
            is_more_utils=True)

        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else "",
            "chart": chart
        }

    # 每日报表
    # 签约信息
    # 签约率
    @create_chart_time
    def get_line_review_all_sign_rate(self):
        return self.get_chart_sign_rate(
            date_range="A", groupby="D", show_restrict=True)

    def get_line_review_all_sign_rate_each_prd(self):
        return self.get_chart_sign_rate(
            date_range="A", groupby="D", show_restrict=True, index=['借款类型'])

    def get_line_review_all_sign_rate_each_loan_amount_distribution(self):
        return self.get_chart_sign_rate(
            date_range="A", groupby="D", show_restrict=True, index=['初审金额分布'])

    # 月汇总信息

    @create_chart_time
    def get_pie_apply_month_bill_each_prd(self, month=None):
        return self.get_pie_apply_bill_each_prd(date_range="M", month=month)

    @create_chart_time
    def get_pie_loan_month_amount_each_prd(self, month=None):
        return self.get_pie_loan_amount_each_prd(date_range="M", month=month)

    @create_chart_time
    def get_bar_loan_month_amount_average_each_prd(self, month=None):
        return self.get_bar_loan_amount_average_each_prd(
            date_range="M", month=month)

    @create_chart_time
    def get_bar_loan_month_period_average_each_prd(self, month=None):
        return self.get_bar_loan_period_average_each_prd(
            date_range="M", month=month)

    @create_chart_time
    def get_bar_review_month_pass_rate_each_prd(self, month=None):
        return self.get_bar_review_pass_rate_each_prd(
            date_range="M", month=month)

    @create_chart_time
    def get_bar_borrower_cost_month_average_rate_each_prd(self, month=None):
        return self.get_bar_borrower_cost_average_rate_each_prd(
            date_range="M", month=month)

    @create_chart_time
    def get_pie_loan_month_income_each_prd(self, month=None):
        return self.get_pie_loan_income_each_prd(date_range="M", month=month)

    @create_chart_time
    def get_pie_instock_month_income_each_prd(self, month=None):
        return self.get_pie_instock_income_each_prd(
            date_range="M", month=month)

    @create_chart_time
    def get_pie_loan_month_amount_distribution(self, month=None):
        return self.get_pie_loan_amount_distribution(
            date_range="M", month=month)

    @create_chart_time
    def get_bar_review_month_sign_rate_each_loan_amount_distribution(
            self, month=None):
        return self.get_chart_sign_rate(
            date_range="M", groupby="M", index=['初审金额分布'], month=month)

    # 本月每日数据

    def get_bar_apply_month_bill(self, month=None):
        return self.get_bar_apply_bill(
            groupby="D", date_range="M", month=month)

    def get_bar_loan_month_amount(self, month=None):
        return self.get_bar_loan_amount(
            groupby="D", date_range="M", month=month)

    def get_bar_loan_month_amount_average(self, month=None):
        return self.get_bar_loan_amount_average(
            groupby="D", date_range="M", month=month)

    def get_bar_loan_month_period_average(self, month=None):
        return self.get_bar_loan_period_average(
            groupby="D", date_range="M", month=month)

    def get_bar_review_month_pass_rate(self, month=None):
        return self.get_bar_review_pass_rate(
            groupby="D", date_range="M", month=month)

    def get_bar_loan_month_income(self, month=None):
        return self.get_bar_loan_income(
            groupby="D", date_range="M", month=month)

    def get_bar_instock_month_income(self, month=None):
        return self.get_bar_instock_income(
            groupby="D", date_range="M", month=month)

    def get_bar_review_month_sign_rate(self, month=None):
        return self.get_chart_sign_rate(
            date_range="M", groupby="D", month=month)

    # 每月数据

    def get_bar_apply_monthly_bill(self):
        return self.get_bar_apply_bill(groupby="M", date_range="ALL")

    def get_bar_loan_monthly_amount(self):
        return self.get_bar_loan_amount(groupby="M", date_range="ALL")

    def get_bar_loan_monthly_amount_average(self):
        return self.get_bar_loan_amount_average(groupby="M", date_range="ALL")

    def get_bar_loan_monthly_period_average(self):
        return self.get_bar_loan_period_average(groupby="M", date_range="ALL")

    def get_bar_review_monthly_pass_rate(self):
        return self.get_bar_review_pass_rate(groupby="M", date_range="ALL")

    def get_bar_loan_monthly_income(self):
        return self.get_bar_loan_income(groupby="M", date_range="ALL")

    def get_bar_instock_monthly_income(self):
        return self.get_bar_instock_income(groupby="M", date_range="ALL")

    def get_bar_review_monthly_sign_rate(self, month=None):
        return self.get_chart_sign_rate(date_range="A", groupby="M")

    # 周汇总信息

    @create_chart_time
    def get_pie_apply_week_bill_each_prd(self):
        return self.get_pie_apply_bill_each_prd(date_range="W")

    @create_chart_time
    def get_pie_loan_week_amount_each_prd(self):
        return self.get_pie_loan_amount_each_prd(date_range="W")

    @create_chart_time
    def get_bar_loan_week_amount_average_each_prd(self):
        return self.get_bar_loan_amount_average_each_prd(date_range="W")

    @create_chart_time
    def get_bar_loan_week_period_average_each_prd(self):
        return self.get_bar_loan_period_average_each_prd(date_range="W")

    @create_chart_time
    def get_bar_review_week_pass_rate_each_prd(self):
        return self.get_bar_review_pass_rate_each_prd(date_range="W")

    @create_chart_time
    def get_bar_borrower_cost_week_average_rate_each_prd(self):
        return self.get_bar_borrower_cost_average_rate_each_prd(date_range="W")

    @create_chart_time
    def get_pie_loan_week_income_each_prd(self):
        return self.get_pie_loan_income_each_prd(date_range="W")

    @create_chart_time
    def get_pie_instock_week_income_each_prd(self):
        return self.get_pie_instock_income_each_prd(date_range="W")

    @create_chart_time
    def get_pie_loan_week_amount_distribution(self):
        return self.get_pie_loan_amount_distribution(date_range="W")

    @create_chart_time
    def get_bar_review_week_sign_rate_each_loan_amount_distribution(self):
        return self.get_chart_sign_rate(
            date_range="W", groupby="W", index=['初审金额分布'])

    # 本周每日数据

    @create_chart_time
    def get_bar_apply_week_bill(self):
        return self.get_bar_apply_bill(groupby="D", date_range="W")

    @create_chart_time
    def get_bar_loan_week_amount(self):
        return self.get_bar_loan_amount(groupby="D", date_range="W")

    @create_chart_time
    def get_bar_loan_week_amount_average(self):
        return self.get_bar_loan_amount_average(groupby="D", date_range="W")

    @create_chart_time
    def get_bar_loan_week_period_average(self):
        return self.get_bar_loan_period_average(groupby="D", date_range="W")

    @create_chart_time
    def get_bar_review_week_pass_rate(self):
        return self.get_bar_review_pass_rate(groupby="D", date_range="W")

    @create_chart_time
    def get_bar_loan_week_income(self):
        return self.get_bar_loan_income(groupby="D", date_range="W")

    def get_bar_review_week_sign_rate(self, month=None):
        return self.get_chart_sign_rate(date_range="W", groupby="D")

    # 每周数据

    def get_bar_apply_weekly_bill(self):
        return self.get_bar_apply_bill(groupby="W", date_range="ALL")

    def get_bar_loan_weekly_amount(self):
        return self.get_bar_loan_amount(groupby="W", date_range="ALL")

    def get_bar_loan_weekly_amount_average(self):
        return self.get_bar_loan_amount_average(groupby="W", date_range="ALL")

    def get_bar_loan_weekly_period_average(self):
        return self.get_bar_loan_period_average(groupby="W", date_range="ALL")

    def get_bar_review_weekly_pass_rate(self):
        return self.get_bar_review_pass_rate(groupby="W", date_range="ALL")

    def get_bar_loan_weekly_income(self):
        return self.get_bar_loan_income(groupby="W", date_range="ALL")

    def get_bar_review_weekly_sign_rate(self):
        return self.get_chart_sign_rate(groupby="W", date_range="ALL")

    # 贷后图表

    def get_line_paid_all_bill(self):
        return self.get_line_paid_bill(
            groupby="D", date_range="ALL", show_restrict=True)

    def get_line_paid_monthly_bill(self):
        return self.get_line_paid_bill(groupby="M", date_range="ALL")

    def get_line_paid_all_income(self):
        return self.get_line_paid_income(
            groupby="D", date_range="ALL", show_restrict=True)

    def get_line_paid_monthly_income(self):
        return self.get_line_paid_income(groupby="M", date_range="ALL")

    def get_line_repay_all_income_perdict(self):
        return self.get_line_repay_income_perdict(
            groupby="D", date_range="ALL")

    def get_line_repay_monthly_income_perdict(self):
        return self.get_line_repay_income_perdict(
            groupby="M", date_range="ALL")

    def get_kline_instock_monthly_amount(self, chart_kind="kline"):
        '''
            在库金额每月走势
        '''
        from pandas.tseries.offsets import MonthEnd
        first_date_df = self.instock_collection_data.resample("MS").fillna(
            'ffill')
        first_date_df.index = first_date_df.index.map(lambda x: x + MonthEnd())
        first_date_df.columns = ['open']
        first_date_df
        last_date_df = self.instock_collection_data.resample("M").fillna(
            'ffill')
        last_date_df.columns = ['close']

        max_df = self.instock_collection_data.resample("M").max()
        max_df.columns = ['lowest']

        min_df = self.instock_collection_data.resample("M").min()
        min_df.columns = ['highest']

        pt = first_date_df.join([last_date_df, max_df, min_df])
        if check_pt(pt) == NONE_PT:
            return {
                "pt": pt,
                'chart_render': "无数据",
                "mom_pt": pt,
                "mom_chart": "无数据"
            }

        pt = pt / 100000000  #单位转换成亿
        pt.index = pt.index.map(lambda x: x.strftime("%Y-%m"))

        pt = proc_pt(pt, n_show_days=None, is_round=2)

        if chart_kind == "kline":  #如果图表类型是kline
            chart = render_echarts_by_lists(
                pt,
                "在库金额（亿）每月走势",
                "",
                chart_kind="kline",
                legend_name=["在库金额"],
                dropna=True,
                xaxis_rotate=90,
                xaxis_interval=0,
                label_text_size=12,
                is_label_show=True,
                yaxis_formatter="亿",
                label_formatter="{c}亿",
                mark_line=["average"],
                is_smooth=True,
                is_fill=True,
                area_opacity=0.3,
                is_more_utils=True)
        else:  #如果图表类型是line或其他
            chart = render_echarts_by_lists(
                pt['close'],
                "在库金额（亿）每月走势",
                "图表数据为每月最后一天的在库金额",
                chart_kind="line",
                legend_name=["在库金额"],
                dropna=True,
                xaxis_rotate=90,
                xaxis_interval=0,
                label_text_size=12,
                is_label_show=True,
                yaxis_formatter="亿",
                label_formatter="{c}亿",
                mark_line=["average"],
                is_smooth=True,
                is_fill=True,
                area_opacity=0.3,
                is_more_utils=True)

        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else "",
            "chart": chart
        }

    def get_line_instock_monthly_amount(self):
        return self.get_kline_instock_monthly_amount(chart_kind="line")

    def get_line_instock_all_amount(self):
        return self.get_line_instock_amount(
            groupby="D", date_range="ALL", show_restrict=True)

    def get_bar_instock_all_status_amount_per_prd_percent(self):
        return self.get_bar_distribution(
            data_name="instock_data",
            column="instock_status",
            column_show_name="在库状态",
            index="loan_product",
            index_show_name="产品",
            value="sy_bj",
            value_show_name="在库金额",
            sort_by="正常",
            unit="",
            change_to_percent='index')

    def get_bar_instock_all_status_amount_per_prd(self):
        return self.get_bar_distribution(
            data_name="instock_data",
            column="instock_status",
            column_show_name="在库状态",
            index="loan_product",
            index_show_name="产品",
            value="sy_bj",
            value_show_name="在库金额",
            sort_by="正常",
            unit="万",
            change_to_percent=None)

    def get_bar_instock_all_prd_amount_per_status_percent(self):
        return self.get_bar_distribution(
            data_name="instock_data",
            index="instock_status",
            index_show_name="在库状态",
            column="loan_product",
            column_show_name="产品",
            value="sy_bj",
            value_show_name="在库金额",
            sort_by="正常",
            unit="",
            change_to_percent='index')

    def get_bar_instock_all_prd_amount_per_status(self):
        return self.get_bar_distribution(
            data_name="instock_data",
            index="instock_status",
            index_show_name="在库状态",
            column="loan_product",
            column_show_name="产品",
            value="sy_bj",
            value_show_name="在库金额",
            sort_by="正常",
            unit="万",
            change_to_percent=None)

    # def get_bar_instock_all_status_amount_per_prd(self):
    #     overlap = Overlap(width="100%", height=400)
    #     overlap.use_theme("dark")
    #     overlap.add(
    #         self.get_bar_distribution(
    #             data_name="instock_data",
    #             column="instock_status",
    #             column_show_name="在库状态",
    #             index="loan_product",
    #             index_show_name="产品",
    #             value="sy_bj",
    #             value_show_name="在库金额",
    #             sort_by="index",
    #             unit="万",
    #             change_to_percent=None)["chart"])
    #     overlap.add(
    #         self.get_bar_distribution(
    #             data_name="instock_data",
    #             column="instock_status",
    #             column_show_name="在库状态",
    #             index="loan_product",
    #             index_show_name="产品",
    #             value="sy_bj",
    #             value_show_name="在库金额",
    #             sort_by="index",
    #             unit="",
    #             change_to_percent='index',
    #             is_stack=True)["chart"],
    #         yaxis_index=1,
    #         is_add_yaxis=True)
    #     return {"chart_render": overlap.render_embed(), "chart": overlap}

    def get_bar_instock_all_status_amount_per_repayment_mode_percent(self):
        return self.get_bar_distribution(
            data_name="instock_data",
            column="instock_status",
            column_show_name="在库状态",
            index="repayment_mode",
            index_show_name="还款方式",
            value="sy_bj",
            value_show_name="在库金额",
            sort_by="正常",
            unit="",
            change_to_percent='index')

    def get_bar_instock_all_status_amount_per_repayment_mode(self):
        return self.get_bar_distribution(
            data_name="instock_data",
            column="instock_status",
            column_show_name="在库状态",
            index="repayment_mode",
            index_show_name="还款方式",
            value="sy_bj",
            value_show_name="在库金额",
            sort_by="正常",
            unit="万",
            change_to_percent=None)

    def get_bar_instock_all_repayment_mode_amount_per_status_percent(self):
        return self.get_bar_distribution(
            data_name="instock_data",
            index="instock_status",
            index_show_name="在库状态",
            column="repayment_mode",
            column_show_name="还款方式",
            value="sy_bj",
            value_show_name="在库金额",
            sort_by="正常",
            unit="",
            change_to_percent='index')

    def get_bar_instock_all_repayment_mode_amount_per_status(self):
        return self.get_bar_distribution(
            data_name="instock_data",
            index="instock_status",
            index_show_name="在库状态",
            column="repayment_mode",
            column_show_name="还款方式",
            value="sy_bj",
            value_show_name="在库金额",
            sort_by="正常",
            unit="万",
            change_to_percent=None)

    def get_bar_instock_all_status_amount_per_province_percent(self):
        return self.get_bar_distribution(
            data_name="instock_data",
            column="instock_status",
            column_show_name="在库状态",
            index="org_province",
            index_show_name="地区",
            value="sy_bj",
            value_show_name="在库金额",
            sort_by="正常",
            unit="",
            is_datazoom_show=True,
            datazoom_range=[0, 40],
            change_to_percent='index')

    def get_bar_instock_all_status_amount_per_province(self):
        return self.get_bar_distribution(
            data_name="instock_data",
            column="instock_status",
            column_show_name="在库状态",
            index="org_province",
            index_show_name="地区",
            value="sy_bj",
            value_show_name="在库金额",
            sort_by="正常",
            unit="万",
            is_datazoom_show=True,
            datazoom_range=[0, 40],
            change_to_percent=None)

    def get_bar_instock_all_province_amount_per_status_percent(self):
        return self.get_bar_distribution(
            data_name="instock_data",
            index="instock_status",
            index_show_name="在库状态",
            column="org_province",
            column_show_name="地区",
            value="sy_bj",
            value_show_name="在库金额",
            sort_by="正常",
            unit="",
            is_datazoom_show=True,
            datazoom_range=[0, 40],
            change_to_percent='index')

    def get_bar_instock_all_province_amount_per_status(self):
        return self.get_bar_distribution(
            data_name="instock_data",
            index="instock_status",
            index_show_name="在库状态",
            column="org_province",
            column_show_name="地区",
            value="sy_bj",
            value_show_name="在库金额",
            sort_by="正常",
            unit="万",
            is_datazoom_show=True,
            datazoom_range=[0, 40],
            change_to_percent=None)

    def get_bar_instock_all_status_amount_per_age_range_percent(self):
        return self.get_bar_distribution(
            data_name="instock_data",
            index="instock_status",
            index_show_name="在库状态",
            column="age_range",
            column_show_name="年龄段",
            value="sy_bj",
            value_show_name="在库金额",
            sort_by="正常",
            unit="",
            change_to_percent='index')

    def get_bar_instock_all_status_amount_per_age_range(self):
        return self.get_bar_distribution(
            data_name="instock_data",
            index="instock_status",
            index_show_name="在库状态",
            column="age_range",
            column_show_name="年龄段",
            value="sy_bj",
            value_show_name="在库金额",
            sort_by="正常",
            unit="万",
            change_to_percent=None)

    def get_bar_instock_all_age_range_amount_per_status_percent(self):
        return self.get_bar_distribution(
            data_name="instock_data",
            index="instock_status",
            index_show_name="在库状态",
            column="age_range",
            column_show_name="年龄段",
            value="sy_bj",
            value_show_name="在库金额",
            sort_by="正常",
            unit="",
            change_to_percent='index')

    def get_bar_instock_all_age_range_amount_per_status(self):
        return self.get_bar_distribution(
            data_name="instock_data",
            index="instock_status",
            index_show_name="在库状态",
            column="age_range",
            column_show_name="年龄段",
            value="sy_bj",
            value_show_name="在库金额",
            sort_by="正常",
            unit="万",
            change_to_percent=None)

    def get_bar_instock_all_status_amount_per_period_percent(self):
        return self.get_bar_distribution(
            data_name="instock_data",
            index="instock_status",
            index_show_name="在库状态",
            column="loan_period",
            column_show_name="期限",
            value="sy_bj",
            value_show_name="在库金额",
            sort_by="正常",
            unit="",
            change_to_percent='index')

    def get_bar_instock_all_status_amount_per_period(self):
        return self.get_bar_distribution(
            data_name="instock_data",
            index="instock_status",
            index_show_name="在库状态",
            column="loan_period",
            column_show_name="期限",
            value="sy_bj",
            value_show_name="在库金额",
            sort_by="正常",
            unit="万",
            change_to_percent=None)

    def get_bar_instock_all_period_amount_per_status_percent(self):
        return self.get_bar_distribution(
            data_name="instock_data",
            index="instock_status",
            index_show_name="在库状态",
            column="loan_period",
            column_show_name="期限",
            value="sy_bj",
            value_show_name="在库金额",
            sort_by="正常",
            unit="",
            change_to_percent='index')

    def get_bar_instock_all_period_amount_per_status(self):
        return self.get_bar_distribution(
            data_name="instock_data",
            index="instock_status",
            index_show_name="在库状态",
            column="loan_period",
            column_show_name="期限",
            value="sy_bj",
            value_show_name="在库金额",
            sort_by="正常",
            unit="万",
            change_to_percent=None)

    def get_bar_distribution(self,
                             index,
                             index_show_name,
                             column,
                             column_show_name,
                             value,
                             value_show_name,
                             unit="",
                             data_name="",
                             date_range='A',
                             specify=None,
                             aggfunc=np.sum,
                             sort_by=None,
                             ascending=False,
                             change_to_percent=None,
                             **kwargs):
        '''获取某指标的分布图表
        
        Parameters
        --------------------------
        index: str
            细分特征在数据库中的名称
        index_show_name: str
            细分特征展示在报表中的名称
        column: str
            类别特征在数据库中的名称
        column_show_name: str
            类别特征展示在报表中的名称
        value: str
            要分析的指标在数据库中的名称
        value_show_name: str
            要分析的指标在报表中的名称
        data_name: str
            要分析的数据来源的表
        date_range: str
            要分析的数据的时间范围
        specify: str or None
            要分析的数据的时间范围的辅助筛选条件
        short_by: str
            是否要按照某一列或行特征的值进行排序
        ascending: boolean
            升降序
        change_to_percent: None,int
            如果为None,不需要将数据转化成百分比形式
            如果为int,则将数据转化成不含%(即各项加起来为100),保留了该参数位小数的数。

        Returns
        --------------------------
        pt: pd.DataFrame
            格式为pandas的DataFrame的表格,包含该图表数据的数据透视表
        chart_render: str
            转化成html代码的图表
        chart: pyecharts.Chart
            图表对象
        '''

        # range data
        range_data = self.get_range_data(
            getattr(self, data_name), date_range=date_range, specify=specify)

        # 获取指标的汇总数据
        summary = range_data[value].sum()

        pt = extract_data_by_date(
            range_data,
            columns=column,
            index=index,
            values=value,
            aggfunc=aggfunc,
            margins=None,
            holidays=self.holidays)

        pt = proc_pt(
            pt,
            is_round=1,
            change_to_percent=change_to_percent
            # columns_name=['剩余本金']
        )

        pt.index.name = "index"

        if sort_by:
            axis = 1 if sort_by in pt.index else 0 if sort_by in pt.columns else -1
            if axis != -1:
                pt = pt.sort_values(by=sort_by, axis=axis, ascending=False)

        default_chart_kwargs = {
            "chart_kind": "bar",
            "dropna": True,
            "xaxis_interval": 0,
            "label_text_size": 12,
            "yaxis_max": round(pt.max().max() * 1.2, -1),
            "is_label_show": True,
            "is_more_utils": True,
            "yaxis_formatter": "%s" % unit,
            "label_formatter": "{c}%s\n{a}" % unit
        }
        default_chart_kwargs.update(kwargs)

        title_note = "(金额)"

        if change_to_percent:
            default_chart_kwargs.update({
                "yaxis_formatter": "%",
                "label_formatter": "{c}%\n{a}",
            })
            title_note = ""

        # 显示名称
        if column_show_name:
            column_show_name = "各" + column_show_name
            index_show_name = "各" + index_show_name
        else:
            column_show_name = "各" + index_show_name
            index_show_name = ""

        chart = render_echarts_by_lists(
            pt, "%s%s%s分布%s" % (index_show_name, value_show_name,
                                column_show_name, title_note),
            "截止至目前的%s%s%s分布，总%s为%.2f万" % (index_show_name, value_show_name,
                                          column_show_name, value_show_name,
                                          summary), **default_chart_kwargs)
        return {
            "pt": pt,
            'chart_render': chart.render_embed() if chart else "",
            'chart': chart
        }

    def get_range_data(self, df, date_range="A", specify=None):
        '''获取范围数据

        Parameters
        ------------------------
        df: pd.DataFrame
            还未筛选的数据
        date_range: {"M","W","A"}
            时间范围,M为月;W为周;A,ALL,All为所有
        specify: str
            其他筛选条件

        Returns
        -----------------------
        df: pd.DataFrame
            筛选后的数据
        '''

        if date_range == "M":
            if specify and type(specify) == str:
                return df[specify]
            else:
                # 日期范围为本月
                return df[self.select_month]
        elif date_range == "W":
            # 日期范围为星期
            return df[self.select_week_start:self.select_week_end]
        elif date_range in ["A", "ALL", "All"]:
            return df
        else:
            return None


def extract_data_by_date(df,
                         index=None,
                         columns=None,
                         values=None,
                         aggfunc=np.sum,
                         margins=None,
                         groupby=None,
                         how="sum",
                         holidays=None):
    '''获取数据透视表,并删除非工作日'''

    pt = pd.pivot_table(
        df,
        index=index,
        columns=columns,
        values=values,
        aggfunc=aggfunc,
        margins=margins)

    if len(pt) == 0:
        return None

    # print(pt.index)

    if groupby == "D":
        pt = getattr(pt.resample(groupby, kind="period"), how)()
        # 数据透视表排除假期
        pt.index = [
            datetime.strptime(str(i), "%Y-%m-%d").strftime("%Y/%m/%d")
            for i in pt.index
        ]
        for holiday in holidays:
            if holiday in pt.index:
                pt.drop(holiday, inplace=True)
    elif groupby == "W":
        pt = getattr(pt.resample(groupby, kind="period"), how)()

    elif groupby == "M":

        pt = getattr(pt.resample(groupby, kind="period"), how)()
        # print(pt.index)

    # 向后兼容
    elif not groupby:
        for holiday in holidays:
            if holiday in pt.index:
                pt.drop(holiday, inplace=True)
    else:
        print("参数groupby出错")

    return pt


def render_echarts_by_lists(
        df,
        chart_title="图表一",
        chart_introduce="",
        chart_kind="bar",
        legend_name=None,
        theme='dark',
        dropna=None,
        width="100%",  # div的width，如果为int或float则自动添加px
        height=400,
        tooltip_axispointer_type="cross",
        label_show_percent=False,
        **kwargs):
    '''根据df或Series数据渲染图表'''

    # 图标样式（黑底）
    title_color = "#eeeeee"
    subtitle_color = "#aaaaaa"
    background_color = "rgba(0,0,0,0)"
    title_text_size = 21
    subtitle_text_size = 15

    label_color = [
        "#dd6b66", "#759aa0", "#e69d87", "#8dc1a9", "#ea7e53", "#eedd78",
        "#73a373", "#73b9bc", "#7289ab", "#91ca8c", "#f49f42"
    ]

    legend_pos = "right"
    legend_text_color = '#eeeeee'
    tooltip_text_color = "#eeeeee"
    line_width = 3

    # 图标类型
    if chart_kind == "line":
        chart = Line(
            chart_title,
            chart_introduce,
            width=width,
            height=height,
            title_color=title_color,
            subtitle_color=subtitle_color,
            background_color=background_color,
            title_text_size=title_text_size,
            subtitle_text_size=subtitle_text_size)

    elif chart_kind == "pie":
        chart = Pie(
            chart_title,
            chart_introduce,
            width=width,
            height=height,
            title_color=title_color,
            subtitle_color=subtitle_color,
            background_color=background_color,
            title_text_size=title_text_size,
            subtitle_text_size=subtitle_text_size)

    elif chart_kind == "effectScatter":
        chart = EffectScatter(
            chart_title,
            chart_introduce,
            width=width,
            height=height,
            title_color=title_color,
            subtitle_color=subtitle_color,
            background_color=background_color,
            title_text_size=title_text_size,
            subtitle_text_size=subtitle_text_size)

    elif chart_kind == "scatter":
        chart = Scatter(
            chart_title,
            chart_introduce,
            width=width,
            height=height,
            title_color=title_color,
            subtitle_color=subtitle_color,
            background_color=background_color,
            title_text_size=title_text_size,
            subtitle_text_size=subtitle_text_size)

    elif chart_kind == "kline":
        chart = Kline(
            chart_title,
            chart_introduce,
            width=width,
            height=height,
            title_color=title_color,
            subtitle_color=subtitle_color,
            background_color=background_color,
            title_text_size=title_text_size,
            subtitle_text_size=subtitle_text_size)

    else:
        chart = Bar(
            chart_title,
            chart_introduce,
            width=width,
            height=height,
            title_color=title_color,
            subtitle_color=subtitle_color,
            background_color=background_color,
            title_text_size=title_text_size,
            subtitle_text_size=subtitle_text_size)

    # 更改图表主题
    chart.use_theme(theme)

    default_kwargs = {
        'tooltip_axispointer_type': tooltip_axispointer_type,
        'label_color': label_color,
        'legend_pos': legend_pos,
        'legend_text_color': legend_text_color,
        'tooltip_text_color': tooltip_text_color,
        'line_width': line_width
    }

    default_kwargs.update(kwargs)

    # 如果传入数据类型为Series
    if type(df) == pd.core.series.Series:

        if chart_kind == "kline":
            print("kline类型不支持Series数据")
            print("创建失败")
            return

        # 删除缺失数据
        if dropna:
            df.dropna(inplace=True)

        # 添加X轴
        chart_index = list(df.index)

        # 添加数据
        val = list(df)
        chart.add(chart_title, chart_index, val, **default_kwargs)
        return chart

    # 如果传入的数据类型为Dataframe
    elif type(df) == pd.core.frame.DataFrame:

        # 将列名改成str
        df.columns = [str(i) if type(i) != str else i for i in df.columns]

        # 删除缺失数据
        if dropna:
            df.dropna(axis=0, how="all", thresh=None, inplace=True)

        # 添加X轴
        chart_index = list(df.index)

        values = []
        value_names = []
        if chart_kind == "kline":

            if (df.columns == ['open', 'close', 'lowest', 'highest']).all():
                kline_values = []
                for index, row_value in df.iterrows():
                    kline_values.append([i for i in row_value])
                values.append(kline_values)
                value_names = legend_name if legend_name else ""
            else:
                print("生成kline的数据的列必须为['open','close','lowest','highest']")
                print('而传入的df的columns为%s' % (df.columns))
                print('创建失败')
                return
        else:
            values = [list(df[col_name]) for col_name in df.columns]
            value_names = list(df.columns)

        if len(value_names) != len(values):
            print("系列数量跟系列名称的数量不一致，请检查")
            print("value_names is %s,长度为%d;values is %s,长度为%d" %
                  (value_names, len(value_names), values, len(values)))
            print("创建失败")
            return

        for val, col_name in zip(values, value_names):

            chart.add(col_name, chart_index, val, **default_kwargs)

        return chart
    else:
        raise ValueError("传入数据的数据类型错误，目前仅支持Series和dataframe")


def change_index(df, how="column"):
    '''将多维的index转变为1维的

    how:"columns"转变的index为column index
        "row"转变的index为row index
    return:返回已经改变index的df
    '''

    if type(df) == pd.core.series.Series:
        return df

    if not (type(df.columns) == pd.core.indexes.multi.MultiIndex
            or type(df.index) == pd.core.indexes.multi.MultiIndex):
        return df

    # 深拷贝
    df = copy.deepcopy(df)

    # 读取levels和labels
    if how == "column":
        levels = df.columns.levels
        labels = df.columns.labels
    elif how == "row":
        levels = df.index.levels
        labels = df.index.labels
    else:
        raise ValueError("参数how错误")

    dimension = len(labels)
    label_len = len(labels[0])

    mod_index = []
    for i in range(label_len):
        name = None
        for d in range(dimension):
            short_label = levels[d][labels[d][i]]
            short_label = str(
                short_label) if type(short_label) != str else short_label

            # 添加label
            if name is None:
                name = short_label
            else:
                name = name + '-' + short_label
        mod_index.append(name)

    # 读取levels和labels
    if how == "column":
        df.columns = mod_index
    elif how == "row":
        df.index = mod_index

    return df


def proc_pt(pt,
            n_show_days=20,
            columns_name=[],
            is_change_index=False,
            is_round=False,
            change_to_percent=False):
    '''处理数据透视表

    Parameters
    ---------------------------
    pt: pd.DataFrame or pd.Series
        数据透视表
    n_show_days: int
        数据透视表显示的行数, 从末尾开始保留
    columns_name: list
        如有则用该参数替换列名
    is_change_index: boolean
        如果为True则将多维的index转换成一维的
    is_round: False or int
        如果为int则将所有的值进行四舍五入的处理, 并保留该参数位小数
    change_to_percent: ['column','index', False]
        如果为column, 则将所有值转换成该值在列中的占比
        如果为index, 则将所有值转换成该值在行中的占比

    Returns
    --------------------------
    pt:pd.DataFrame or pd.Series
        经过处理之后的数据透视表        
    '''

    if n_show_days:
        pt = pt[-n_show_days:]

    if hasattr(pt, "columns") and len(columns_name) == len(pt.columns):
        pt.columns = pd.Index(columns_name)
    else:
        pass
        # print("修改columns名字失败，长度不符")

    if is_change_index:
        if is_change_index not in ["row", "column"]:
            raise ValueError("is_change_index is wrong")
        else:
            pt = change_index(pt)

    if is_round:
        if hasattr(pt, "applymap"):
            pt = pt.applymap(lambda x: round(x, is_round))
        elif hasattr(pt, "map"):
            pt = pt.map(lambda x: round(x, is_round))
        else:
            print("四舍五入失败")

    if change_to_percent:

        if change_to_percent == "column":
            pt = pt / np.sum(pt)
        else:
            pt = pt.T / np.sum(pt.T)
            pt = pt.T

        # 转换成百分比
        def mul_100_and_round(value, pre=2):
            if value > 0:
                return round(value * 100, pre)
            else:
                return value

        if hasattr(pt, "applymap"):
            pt = pt.applymap(mul_100_and_round)
        elif hasattr(pt, "map"):
            pt = pt.map(mul_100_and_round)
        else:
            print("转化成百分比失败")

    # 将index转变为str
    pt.index = pt.index.map(lambda x: str(x) if type(x) != str else x)

    return pt


def check_pt(pt):
    # 如果pt不存在，则直接返回
    if pt is None or (type(pt) != pd.core.frame.DataFrame
                      and type(pt) != pd.core.series.Series) or len(pt) == 0:
        print("数据透视表无数据，直接返回pt")
        return NONE_PT
    else:
        return NORMAL_PT


def getEveryDay(begin_date, end_date, link="/"):
    '''生成日期列表'''

    date_list = []
    begin_date = datetime.strptime(begin_date,
                                   "%Y" + link + "%m" + link + "%d")
    end_date = datetime.strptime(end_date, "%Y" + link + "%m" + link + "%d")

    while begin_date <= end_date:
        date_str = begin_date.strftime("%Y" + link + "%m" + link + "%d")
        date_list.append(date_str)
        begin_date += timedelta(days=1)

    return date_list
