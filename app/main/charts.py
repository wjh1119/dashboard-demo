from pyecharts import Bar, Pie, Line, Timeline
import pandas as pd
import numpy as np

LABEL_COLOR = [
    "#dd6b66", "#759aa0", "#e69d87", "#8dc1a9", "#ea7e53", "#eedd78",
    "#73a373", "#73b9bc", "#7289ab", "#91ca8c", "#f49f42"
]
BACKGROUND_COLOR = "rgba(0,0,0,0)"

DEFAULT_KWARGS = {
    'tooltip_axispointer_type':
    'shadow',
    'label_color': [
        "#dd6b66", "#759aa0", "#e69d87", "#8dc1a9", "#ea7e53", "#eedd78",
        "#73a373", "#73b9bc", "#7289ab", "#91ca8c", "#f49f42"
    ],
    'legend_pos':
    "right",
    'line_width':
    3,
    "is_label_show":
    True,
}

dates = [date.strftime("%Y-%m-%d") for date in pd.date_range('2/1/2019', '2/28/2019')]
months = [date.strftime("%Y-%m") for date in pd.date_range('3/1/2018', '2/28/2019', freq="M")]

def day_apply_bill():
    '''生成日申请件数图表'''

    # X轴label
    attr = ["1月", "3月", "6月", "12月", "24月", "36月"]

    # 图表数据
    v1 = [5, 20, 36, 10, 75, 90]
    v2 = [10, 25, 8, 60, 20, 80]

    # 生成图表实例
    chart = Bar("今日各产品申请件数", background_color=BACKGROUND_COLOR, width="100%")

    # 使用暗色主题
    chart.use_theme('dark')

    # 载入默认设置并差异化更新
    chart_kwargs = DEFAULT_KWARGS
    chart_kwargs.update({
        "bar_category_gap": 50,
    })

    # 添加数据
    chart.add("产品A", attr, v1, **chart_kwargs)
    chart.add("产品B", attr, v2, **chart_kwargs)
    return chart


def day_loan_amount():
    '''生成日放款金额图表'''

    # X轴label
    attr = ["1月", "3月", "6月", "12月", "24月", "36月"]

    # 图表数据
    v1 = list(np.random.randint(5000, 10000, 6) / 10)
    v2 = list(np.random.randint(3000, 8000, 6) / 10)

    # 生成图表实例
    chart = Bar("今日各产品放款金额", background_color=BACKGROUND_COLOR, width="100%")

    # 使用暗色主题
    chart.use_theme('dark')

    # 载入默认设置并差异化更新
    chart_kwargs = DEFAULT_KWARGS
    chart_kwargs.update({
        "bar_category_gap": 50,
    })

    # 添加数据
    chart.add("产品A", attr, v1, is_stack=True, **chart_kwargs)
    chart.add("产品B", attr, v2, is_stack=True, **chart_kwargs)
    return chart


def day_loan_average():
    '''生成日放款件均图表'''

    # X轴label
    attr = ["1月", "3月", "6月", "12月", "24月", "36月"]

    # 图表数据
    v1 = list(np.random.randint(1000, 1100, 6) / 100)
    v2 = list(np.random.randint(900, 1000, 6) / 100)

    # 生成图表实例
    chart = Bar("今日放款件均", background_color=BACKGROUND_COLOR, width="100%")

    # 使用暗色主题
    chart.use_theme('dark')

    # 载入默认设置并差异化更新
    chart_kwargs = DEFAULT_KWARGS
    chart_kwargs.update({"bar_category_gap": 50, "yaxis_min": "dataMin"})

    # 添加数据
    chart.add("产品A", attr, v1, **chart_kwargs)
    chart.add("产品B", attr, v2, **chart_kwargs)
    return chart


def day_loan_income():
    '''生成日放款收入图表'''

    # X轴label
    attr = ["产品A", "产品B", "产品C", "产品D", "产品E", "产品F"]

    # 图表数据
    v1 = list(np.random.randint(200, 1000, 6) / 10)

    # 生成图表实例
    chart = Pie(
        "今日收入(单位:万)",
        "今日总收入为%f万" % np.sum(v1),
        background_color=BACKGROUND_COLOR,
        width="100%")

    # 使用暗色主题
    chart.use_theme('dark')

    # 载入默认设置并差异化更新
    chart_kwargs = DEFAULT_KWARGS
    chart_kwargs.update({})

    # 添加数据
    chart.add("收入", attr, v1, **chart_kwargs)

    return chart


def day_review():
    '''生成日审批通过率图表'''

    # X轴label
    attr = ["产品A", "产品B", "产品C", "产品D", "产品E", "产品F"]

    # 图表数据
    v1 = list(np.random.randint(800, 900, 6) / 10)

    # 生成图表实例
    chart = Bar("今日各产品审批率", background_color=BACKGROUND_COLOR, width="100%")

    # 使用暗色主题
    chart.use_theme('dark')

    # 载入默认设置并差异化更新
    chart_kwargs = DEFAULT_KWARGS
    chart_kwargs.update({
        "bar_category_gap": 50,
        "yaxis_min": "dataMin",
        "yaxis_formatter": "%",
        "label_formatter": "{c}%",
    })

    # 添加数据
    chart.add("审批率", attr, v1, **chart_kwargs)

    return chart


def day_sign():
    '''生成日签约率图表'''

    # X轴label
    attr = ["产品A", "产品B", "产品C", "产品D", "产品E", "产品F"]

    # 图表数据
    v1 = list(np.random.randint(750, 850, 6) / 10)

    # 生成图表实例
    chart = Bar("今日各产品签约率", background_color=BACKGROUND_COLOR, width="100%")

    # 使用暗色主题
    chart.use_theme('dark')

    # 载入默认设置并差异化更新
    chart_kwargs = DEFAULT_KWARGS
    chart_kwargs.update({
        "bar_category_gap": 50,
        "yaxis_min": "dataMin",
        "yaxis_formatter": "%",
        "label_formatter": "{c}%",
    })

    # 添加数据
    chart.add("签约率", attr, v1, **chart_kwargs)

    return chart


def month_apply_bill():
    '''生成本月申请件数图表'''

    # X轴label
    attr = dates

    # 图表数据
    v1 = list(np.random.randint(20, 100, len(dates)))

    # 生成图表实例
    chart = Line("本月申请件数趋势", background_color=BACKGROUND_COLOR, width="100%")

    # 使用暗色主题
    chart.use_theme('dark')

    # 载入默认设置并差异化更新
    chart_kwargs = DEFAULT_KWARGS
    chart_kwargs.update({
        "xaxis_interval":0,
        "mark_line": ["average"],
        "is_smooth": True,
        "is_fill": True,
        "area_opacity": 0.3,
        "xaxis_rotate":90,
    })

    # 添加数据
    chart.add("申请件数", attr, v1, **chart_kwargs)

    return chart


def month_loan_amount():
    '''生成本月放款金额图表'''

    # X轴label
    attr = dates

    # 图表数据
    v1 = list(np.random.randint(2000, 10000, len(dates)) / 10)

    # 生成图表实例
    chart = Line("本月放款金额趋势", background_color=BACKGROUND_COLOR, width="100%")

    # 使用暗色主题
    chart.use_theme('dark')

    # 载入默认设置并差异化更新
    chart_kwargs = DEFAULT_KWARGS
    chart_kwargs.update({
        "xaxis_interval":0,
        "mark_line": ["average"],
        "is_smooth": True,
        "is_fill": True,
        "area_opacity": 0.3,
        "xaxis_rotate":90,
    })

    # 添加数据
    chart.add("放款金额", attr, v1, **chart_kwargs)

    return chart

def month_loan_average():
    '''生成本月放款件均图表'''

    # X轴label
    attr = dates

    # 图表数据
    v1 = list(np.random.randint(95, 105, len(dates)) / 10)

    # 生成图表实例
    chart = Line("本月放款件均趋势(单位:万)", background_color=BACKGROUND_COLOR, width="100%")

    # 使用暗色主题
    chart.use_theme('dark')

    # 载入默认设置并差异化更新
    chart_kwargs = DEFAULT_KWARGS
    chart_kwargs.update({
        "xaxis_interval":0,
        "mark_line": ["average"],
        "is_smooth": True,
        "is_fill": True,
        "area_opacity": 0.3,
        "yaxis_min": "dataMin",
        "xaxis_rotate":90,
    })

    # 添加数据
    chart.add("放款件均", attr, v1, **chart_kwargs)

    return chart

def month_loan_income():
    '''生成本月放款收入图表'''

    # X轴label
    attr = dates

    # 图表数据
    v1 = list(np.random.randint(2000, 6000, len(dates)) / 10)

    # 生成图表实例
    chart = Line("本月放款收入趋势(单位:万)", background_color=BACKGROUND_COLOR, width="100%")

    # 使用暗色主题
    chart.use_theme('dark')

    # 载入默认设置并差异化更新
    chart_kwargs = DEFAULT_KWARGS
    chart_kwargs.update({
        "xaxis_interval":0,
        "mark_line": ["average"],
        "is_smooth": True,
        "is_fill": True,
        "area_opacity": 0.3,
        "yaxis_min": "dataMin",
        "xaxis_rotate":90,
    })

    # 添加数据
    chart.add("放款收入", attr, v1, **chart_kwargs)

    return chart

def month_review():
    '''生成本月审批通过率图表'''

    # X轴label
    attr = dates

    # 图表数据
    v1 = list(np.random.randint(750, 850, len(dates)) / 10)

    # 生成图表实例
    chart = Line("本月审批通过率趋势", background_color=BACKGROUND_COLOR, width="100%")

    # 使用暗色主题
    chart.use_theme('dark')

    # 载入默认设置并差异化更新
    chart_kwargs = DEFAULT_KWARGS
    chart_kwargs.update({
        "xaxis_interval":0,
        "mark_line": ["average"],
        "is_smooth": True,
        "is_fill": True,
        "area_opacity": 0.3,
        "yaxis_min": "dataMin",
        "yaxis_formatter": "%",
        "label_formatter": "{c}%",
        "xaxis_rotate":90,
    })

    # 添加数据
    chart.add("审批通过率", attr, v1, **chart_kwargs)

    return chart

def month_sign():
    '''生成本月签约率图表'''

    # X轴label
    attr = dates

    # 图表数据
    v1 = list(np.random.randint(700, 800, len(dates)) / 10)

    # 生成图表实例
    chart = Line("本月签约率趋势", background_color=BACKGROUND_COLOR, width="100%")

    # 使用暗色主题
    chart.use_theme('dark')

    # 载入默认设置并差异化更新
    chart_kwargs = DEFAULT_KWARGS
    chart_kwargs.update({
        "xaxis_interval":0,
        "mark_line": ["average"],
        "is_smooth": True,
        "is_fill": True,
        "area_opacity": 0.3,
        "yaxis_min": "dataMin",
        "yaxis_formatter": "%",
        "label_formatter": "{c}%",
        "xaxis_rotate":90,
    })

    # 添加数据
    chart.add("签约率", attr, v1, **chart_kwargs)

    return chart

def monthly_apply_bill():
    '''生成每月申请件数图表'''

    # X轴label
    attr = months

    # 图表数据
    v1 = list(np.random.randint(600, 3000, len(months)))

    # 生成图表实例
    chart = Line("每月申请件数趋势", background_color=BACKGROUND_COLOR, width="100%")

    # 使用暗色主题
    chart.use_theme('dark')

    # 载入默认设置并差异化更新
    chart_kwargs = DEFAULT_KWARGS
    chart_kwargs.update({
        "xaxis_interval":0,
        "mark_line": ["average"],
        "is_smooth": True,
        "is_fill": True,
        "area_opacity": 0.3,
        "xaxis_rotate":90,
    })

    # 添加数据
    chart.add("申请件数", attr, v1, **chart_kwargs)

    return chart


def monthly_loan_amount():
    '''生成每月放款金额图表'''

    # X轴label
    attr = months

    # 图表数据
    v1 = list(np.random.randint(60000, 300000, len(months)) / 10)

    # 生成图表实例
    chart = Line("每月放款金额趋势", background_color=BACKGROUND_COLOR, width="100%")

    # 使用暗色主题
    chart.use_theme('dark')

    # 载入默认设置并差异化更新
    chart_kwargs = DEFAULT_KWARGS
    chart_kwargs.update({
        "xaxis_interval":0,
        "mark_line": ["average"],
        "is_smooth": True,
        "is_fill": True,
        "area_opacity": 0.3,
        "xaxis_rotate":90,
    })

    # 添加数据
    chart.add("放款金额", attr, v1, **chart_kwargs)

    return chart

def monthly_loan_average():
    '''生成每月放款件均图表'''

    # X轴label
    attr = months

    # 图表数据
    v1 = list(np.random.randint(95, 105, len(months)) / 10)

    # 生成图表实例
    chart = Line("每月放款件均趋势(单位:万)", background_color=BACKGROUND_COLOR, width="100%")

    # 使用暗色主题
    chart.use_theme('dark')

    # 载入默认设置并差异化更新
    chart_kwargs = DEFAULT_KWARGS
    chart_kwargs.update({
        "xaxis_interval":0,
        "mark_line": ["average"],
        "is_smooth": True,
        "is_fill": True,
        "area_opacity": 0.3,
        "yaxis_min": "dataMin",
        "xaxis_rotate":90,
    })

    # 添加数据
    chart.add("放款件均", attr, v1, **chart_kwargs)

    return chart

def monthly_loan_income():
    '''生成每月放款收入图表'''

    # X轴label
    attr = months

    # 图表数据
    v1 = list(np.random.randint(60000, 180000, len(months)) / 10)

    # 生成图表实例
    chart = Line("每月放款收入趋势(单位:万)", background_color=BACKGROUND_COLOR, width="100%")

    # 使用暗色主题
    chart.use_theme('dark')

    # 载入默认设置并差异化更新
    chart_kwargs = DEFAULT_KWARGS
    chart_kwargs.update({
        "xaxis_interval":0,
        "mark_line": ["average"],
        "is_smooth": True,
        "is_fill": True,
        "area_opacity": 0.3,
        "yaxis_min": "dataMin",
        "xaxis_rotate":90,
    })

    # 添加数据
    chart.add("放款收入", attr, v1, **chart_kwargs)

    return chart

def monthly_review():
    '''生成每月审批通过率图表'''

    # X轴label
    attr = months

    # 图表数据
    v1 = list(np.random.randint(750, 850, len(months)) / 10)

    # 生成图表实例
    chart = Line("每月审批通过率趋势", background_color=BACKGROUND_COLOR, width="100%")

    # 使用暗色主题
    chart.use_theme('dark')

    # 载入默认设置并差异化更新
    chart_kwargs = DEFAULT_KWARGS
    chart_kwargs.update({
        "xaxis_interval":0,
        "mark_line": ["average"],
        "is_smooth": True,
        "is_fill": True,
        "area_opacity": 0.3,
        "yaxis_min": "dataMin",
        "yaxis_formatter": "%",
        "label_formatter": "{c}%",
        "xaxis_rotate":90,
    })

    # 添加数据
    chart.add("审批通过率", attr, v1, **chart_kwargs)

    return chart

def monthly_sign():
    '''生成每月签约率图表'''

    # X轴label
    attr = months

    # 图表数据
    v1 = list(np.random.randint(700, 800, len(months)) / 10)

    # 生成图表实例
    chart = Line("每月签约率趋势", background_color=BACKGROUND_COLOR, width="100%")

    # 使用暗色主题
    chart.use_theme('dark')

    # 载入默认设置并差异化更新
    chart_kwargs = DEFAULT_KWARGS
    chart_kwargs.update({
        "xaxis_interval":0,
        "mark_line": ["average"],
        "is_smooth": True,
        "is_fill": True,
        "area_opacity": 0.3,
        "yaxis_min": "dataMin",
        "yaxis_formatter": "%",
        "label_formatter": "{c}%",
        "xaxis_rotate":90,
    })

    # 添加数据
    chart.add("签约率", attr, v1, **chart_kwargs)

    return chart

def dashboard_loan_amount():
    '''添加放款金额轮播图表'''

    # 生成图表实例
    timeline = Timeline(is_auto_play=True, timeline_bottom=0, width="100%")

    # 使用暗色主题
    timeline.use_theme('dark')

    # 生成每个月份的图表
    for month in months:
        
        # X轴label
        n_day_in_month = pd.Period(month+"-01").days_in_month
        attr = list(range(1,n_day_in_month+1))

        # 图表数据
        v1 = list(np.random.randint(2000, 10000, n_day_in_month) / 10)

        # 生成图表实例
        chart = Line("%s月放款金额走势图" %month,"当月放款总金额为%.2f万" %np.sum(v1), background_color=BACKGROUND_COLOR, width="100%")

        # 使用暗色主题
        chart.use_theme('dark')

        # 载入默认设置并差异化更新
        chart_kwargs = DEFAULT_KWARGS
        chart_kwargs.update({
            "xaxis_interval":0,
            "mark_line": ["average"],
            "is_smooth": True,
            "is_fill": True,
            "area_opacity": 0.3,
        })

        # 添加数据
        chart.add("放款金额", attr, v1, **chart_kwargs)

        timeline.add(chart,month)
    
    return timeline

