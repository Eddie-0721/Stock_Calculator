"""
@Author      :   Eddie 
@Time        :   2024/04/02 12:48:35
@Description :   这是一个股票计算器
"""
from flask import Flask, render_template, request, jsonify, abort
import os

app = Flask(__name__)

# 使用环境变量来配置应用
COMMISSION_RATE = float(os.getenv('COMMISSION_RATE', '0.0003'))  # 佣金率
MIN_COMMISSION = float(os.getenv('MIN_COMMISSION', '5'))  # 最低佣金费用
TRANSFER_FEE_RATE_SH = float(os.getenv('TRANSFER_FEE_RATE_SH', '0.00002'))  # 上海股市过户费率
STAMP_TAX_RATE = float(os.getenv('STAMP_TAX_RATE', '0.001'))  # 印花税率

@app.route("/")
def index():
    """
    首页路由处理函数，当用户访问网站根URL时调用。
    渲染并返回index.html模板。  
    """
    return render_template("index.html")

@app.route("/calculate_stock_profit", methods=["POST"])
def calculate_stock_profit():
    """
    股票盈利计算路由处理函数，处理POST请求。
    从请求中获取初始买入价格、当前价格和股票数量，
    计算并返回股票交易的总成本、总收益、盈利以及百分比增益。
    """
    # 接收JSON数据，并计算股票盈利
    data = request.get_json()
    try:
        # 尝试提取所需数据，如果数据不合法将返回错误
        initial_price = float(data['initial_price'])  # 初始买入价格
        current_price = float(data['current_price'])  # 当前价格
        shares = int(data['shares'])  # 持有的股票数量
        if initial_price <= 0 or current_price <= 0 or shares <= 0:
            abort(400, description="Invalid input data: Values must be positive")
    except (ValueError, KeyError):
        abort(400, description="Invalid input data")
    market_type = data.get('market_type', 'sh')  # 股票市场类型，默认上海

    # 计算买入成本
    gross_cost = initial_price * shares  # 成交金额 = 初始价格 × 股票数量
    commission_buy = max(gross_cost * COMMISSION_RATE, MIN_COMMISSION)  # 佣金 = 成交金额 × 佣金率，不低于最小佣金
    transfer_fee_buy = gross_cost * TRANSFER_FEE_RATE_SH if market_type == 'sh' else 0  # 过户费（仅限上海股市）= 成交金额 × 过户费率
    total_cost = gross_cost + commission_buy + transfer_fee_buy  # 总成本 = 成交金额 + 佣金 + 过户费

    # 计算卖出收益
    gross_income = current_price * shares  # 成交金额 = 当前价格 × 股票数量
    commission_sell = max(gross_income * COMMISSION_RATE, MIN_COMMISSION)  # 佣金 = 成交金额 × 佣金率，不低于最小佣金
    transfer_fee_sell = gross_income * TRANSFER_FEE_RATE_SH if market_type == 'sh' else 0  # 过户费（仅限上海股市）= 成交金额 × 过户费率
    stamp_tax = gross_income * STAMP_TAX_RATE  # 印花税 = 成交金额 × 印花税率
    total_income = gross_income - commission_sell - transfer_fee_sell - stamp_tax  # 总收益 = 成交金额 - 佣金 - 过户费 - 印花税

    # 盈利
    profit = total_income - total_cost  # 利润 = 总收益 - 总成本
    percentage_gain = (profit / total_cost) * 100  # 百分比增益 =（利润 / 总成本）× 100

    # 计算保本价格
    breakeven_price = total_cost / shares  # 保本价格 = 总成本 / 股票数量

    # 结果保留两位小数
    total_cost = round(total_cost, 2)
    total_income = round(total_income, 2)
    profit = round(profit, 2)
    percentage_gain = round(percentage_gain, 2)
    breakeven_price = round(breakeven_price, 2)

    return jsonify({
        'initial_price': initial_price,
        'current_price': current_price,
        'shares': shares,
        'total_cost': total_cost,
        'total_income': total_income,
        'profit': profit,
        'percentage_gain': percentage_gain,
        'breakeven_price': breakeven_price,  # 返回保本价格
        'commission_sell': commission_sell,
        'transfer_fee_sell': transfer_fee_sell,
        'stamp_tax': stamp_tax
    })

@app.route("/calculate_increase", methods=["POST"])
def calculate_increase():
    """
    价格预期涨幅计算路由处理函数，处理POST请求。
    从请求中获取当前价格和预期涨幅的百分比，
    计算并返回涨幅后的价格。
    """
    # 接收JSON数据，并计算价格预期涨幅后的值
    data = request.get_json()
    try:
        # 尝试提取所需数据，如果数据不合法将返回错误
        current_price = float(data['current_price'])  # 当前价格
        percentage_increase = float(data['percentage_increase'])  # 预期涨幅百分比
        if current_price <= 0 or percentage_increase <= 0:
            abort(400, description="Invalid input data: Values must be positive")
    except (ValueError, KeyError):
        abort(400, description="Invalid input data")
    increased_price = round(current_price * (1 + percentage_increase / 100), 2)  # 计算涨幅后价格 = 当前价格 × (1 + 百分比涨幅)

    return jsonify({
        'current_price': current_price,
        'percentage_increase': percentage_increase,
        'increased_price': increased_price
    })

@app.route("/calculate_breakeven_price", methods=["POST"])
def calculate_breakeven_price():
    """
    保本价格计算路由处理函数，处理POST请求。
    从请求中获取初始价格和股票数量，计算并返回每股的保本价格，
    保本价格是指在考虑所有交易费用后卖出股票时不会产生亏损的价格。
    """
    # 接收JSON数据，并计算保本价格
    data = request.get_json()
    try:
        # 尝试提取所需数据，如果数据不合法将返回错误
        initial_price = float(data['initial_price'])  # 初始价格
        shares = int(data['shares'])  # 股票数量
        market_type = data.get('market_type', 'sh')  # 股票市场类型，默认上海
        if initial_price <= 0 or shares <= 0:
            abort(400, description="Invalid input data: Values must be positive")

        # 计算买入成本
        gross_cost = initial_price * shares  # 成交金额 = 初始价格 × 股票数量
        commission_buy = max(gross_cost * COMMISSION_RATE, MIN_COMMISSION)  # 买入佣金 = 成交金额 × 佣金率，不低于最小佣金
        transfer_fee_buy = gross_cost * TRANSFER_FEE_RATE_SH if market_type == 'sh' else 0  # 买入过户费（仅限上海股市） = 成交金额 × 过户费率

        # 预计卖出时的费用
        commission_sell = max(gross_cost * COMMISSION_RATE, MIN_COMMISSION)  # 预计卖出佣金 = 成交金额 × 佣金率，不低于最小佣金
        transfer_fee_sell = gross_cost * TRANSFER_FEE_RATE_SH if market_type == 'sh' else 0  # 预计卖出过户费（仅限上海股市） = 成交金额 × 过户费率
        stamp_tax = gross_cost * STAMP_TAX_RATE  # 预计印花税 = 成交金额 × 印花税率

        # 保本价格
        total_cost_with_future_sell = gross_cost \
                                    + commission_buy \
                                    + transfer_fee_buy \
                                    + commission_sell \
                                    + transfer_fee_sell \
                                    + stamp_tax  # 总成本计 = 买入成本 + 预计卖出时的总费用
        breakeven_price = total_cost_with_future_sell / shares  # 保本价格 = 总成本 / 股票数量

        # 保留两位小数
        breakeven_price = round(breakeven_price, 2)

    except (ValueError, KeyError):
        abort(400, description="Invalid input data")
    
    return jsonify({
        'initial_price': initial_price,
        'shares': shares,
        'breakeven_price': breakeven_price
    })

if __name__ == "__main__":
    app.run(port=8080, debug=True)  # 启动Flask应用并设置监听的端口