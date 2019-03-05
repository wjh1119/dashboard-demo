from pyecharts import Bar, Pie
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


def day_apply_bill():
    attr = ["1月", "3月", "6月", "12月", "24月", "36月"]
    v1 = [5, 20, 36, 10, 75, 90]
    v2 = [10, 25, 8, 60, 20, 80]
    chart = Bar("今日各产品申请件数", background_color=BACKGROUND_COLOR, width="100%")
    chart.use_theme('dark')

    chart_kwargs = DEFAULT_KWARGS
    chart_kwargs.update({
        "bar_category_gap": 50,
    })

    chart.add("产品A", attr, v1, **chart_kwargs)
    chart.add("产品B", attr, v2, **chart_kwargs)
    return chart


def day_loan_amount():
    #示例图表 今日各产品放款金额
    attr = ["1月", "3月", "6月", "12月", "24月", "36月"]
    v1 = list(np.random.randint(5000, 10000, 6) / 10)
    v2 = list(np.random.randint(3000, 8000, 6) / 10)
    chart = Bar("今日各产品放款金额", background_color=BACKGROUND_COLOR, width="100%")
    chart.use_theme('dark')

    chart_kwargs = DEFAULT_KWARGS
    chart_kwargs.update({
        "bar_category_gap": 50,
    })

    chart.add("产品A", attr, v1, is_stack=True, **chart_kwargs)
    chart.add("产品B", attr, v2, is_stack=True, **chart_kwargs)
    return chart


def day_loan_average():
    attr = ["1月", "3月", "6月", "12月", "24月", "36月"]
    v1 = list(np.random.randint(1000, 1100, 6) / 100)
    v2 = list(np.random.randint(900, 1000, 6) / 100)
    chart = Bar("今日放款件均", background_color=BACKGROUND_COLOR, width="100%")
    chart.use_theme('dark')

    chart_kwargs = DEFAULT_KWARGS
    chart_kwargs.update({"bar_category_gap": 50, "yaxis_min": "dataMin"})

    chart.add("产品A", attr, v1, **chart_kwargs)
    chart.add("产品B", attr, v2, **chart_kwargs)
    return chart


def day_loan_income():
    attr = ["产品A", "产品B", "产品C", "产品D", "产品E", "产品F"]
    v1 = list(np.random.randint(200, 1000, 6) / 10)
    chart = Pie(
        "今日收入(单位:万)",
        "今日总收入为%f万" % np.sum(v1),
        background_color=BACKGROUND_COLOR,
        width="100%")
    chart.use_theme('dark')

    chart_kwargs = DEFAULT_KWARGS
    chart_kwargs.update({})

    chart.add("收入", attr, v1, **chart_kwargs)
    return chart


def day_review():
    attr = ["产品A", "产品B", "产品C", "产品D", "产品E", "产品F"]
    v1 = list(np.random.randint(800, 900, 6) / 10)
    chart = Bar("今日各产品审批率", background_color=BACKGROUND_COLOR, width="100%")
    chart.use_theme('dark')

    chart_kwargs = DEFAULT_KWARGS
    chart_kwargs.update({
        "bar_category_gap": 50,
        "yaxis_min": "dataMin",
        "yaxis_formatter": "%",
        "label_formatter": "{c}%",
    })

    chart.add("审批率", attr, v1, **chart_kwargs)

    return chart


def day_sign():
    attr = ["产品A", "产品B", "产品C", "产品D", "产品E", "产品F"]
    v1 = list(np.random.randint(750, 850, 6) / 10)
    chart = Bar("今日各产品签约率", background_color=BACKGROUND_COLOR, width="100%")
    chart.use_theme('dark')

    chart_kwargs = DEFAULT_KWARGS
    chart_kwargs.update({
        "bar_category_gap": 50,
        "yaxis_min": "dataMin",
        "yaxis_formatter": "%",
        "label_formatter": "{c}%",
    })


    chart.add("签约率", attr, v1, **chart_kwargs)

    return chart