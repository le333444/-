"""
股票数据中心 - 东方财富API
"""
from flask import Flask, render_template, request, jsonify
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 股票列表 (只用A股)
A_STOCKS = [
    {'symbol': '600519', 'name': '贵州茅台'},
    {'symbol': '600036', 'name': '招商银行'},
    {'symbol': '601318', 'name': '中国平安'},
    {'symbol': '000001', 'name': '平安银行'},
    {'symbol': '002594', 'name': '比亚迪'},
    {'symbol': '300750', 'name': '宁德时代'},
    {'symbol': '601888', 'name': '中国中免'},
    {'symbol': '600276', 'name': '恒瑞医药'}
]

HK_STOCKS = [
    {'symbol': '00700', 'name': '腾讯控股'},
    {'symbol': '00981', 'name': '小米集团'},
    {'symbol': '03690', 'name': '美团'}
]

US_STOCKS = [
    {'symbol': 'AAPL', 'name': '苹果'},
    {'symbol': 'MSFT', 'name': '微软'},
    {'symbol': 'NVDA', 'name': '英伟达'}
]


def get_stock(symbol):
    """获取股票数据"""
    try:
        # 判断市场
        if symbol.isdigit():
            # 纯数字: A股或港股
            if len(symbol) == 5 and int(symbol) < 90000:
                # 港股 00700
                secid = f"116.{symbol}"
            else:
                # A股
                if symbol.startswith('6'):
                    secid = f"1.{symbol}"
                else:
                    secid = f"0.{symbol}"
        else:
            # 美股等
            secid = f"1.{symbol}"
        
        url = f'https://push2.eastmoney.com/api/qt/stock/get?secid={secid}&fields=f43,f44,f45,f46,f47,f48,f58'
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('data'):
                stock = data['data']
                name = stock.get('f58', symbol)
                
                # 港股价格除以1000，A股除以100
                is_hk = secid.startswith('116.')
                divisor = 1000 if is_hk else 100
                
                current_price = (stock.get('f43', 0) or 0) / divisor
                close_price = (stock.get('f44', 0) or 0) / divisor
                open_price = (stock.get('f45', 0) or 0) / divisor
                high_price = (stock.get('f46', 0) or 0) / divisor
                low_price = (stock.get('f47', 0) or 0) / divisor
                volume = stock.get('f48', 0)
                
                change = current_price - close_price
                change_pct = (change / close_price * 100) if close_price else 0
                
                return {
                    'symbol': symbol,
                    'name': name,
                    'price': round(current_price, 2),
                    'change': round(change, 2),
                    'change_pct': round(change_pct, 2),
                    'open': round(open_price, 2),
                    'close': round(close_price, 2),
                    'high': round(high_price, 2),
                    'low': round(low_price, 2),
                    'volume': format_volume(volume)
                }
    except Exception as e:
        logger.error(f"获取失败 {symbol}: {e}")
    return None


def get_index():
    """获取大盘指数"""
    indices_data = [
        ('1.000001', '000001', '上证指数'),
        ('0.399001', '399001', '深证成指')
    ]
    
    result = []
    for secid, code, name in indices_data:
        try:
            url = f'https://push2.eastmoney.com/api/qt/stock/get?secid={secid}&fields=f43,f44,f45,f46,f47,f48,f58'
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('data'):
                    stock = data['data']
                    current_price = (stock.get('f43', 0) or 0) / 100
                    close_price = (stock.get('f44', 0) or 0) / 100
                    
                    change = current_price - close_price
                    change_pct = (change / close_price * 100) if close_price else 0
                    
                    result.append({
                        'symbol': code,
                        'name': name,
                        'price': round(current_price, 2),
                        'change': round(change, 2),
                        'change_pct': round(change_pct, 2)
                    })
        except Exception as e:
            logger.error(f"获取指数失败 {name}: {e}")
    
    return result


def format_volume(volume):
    if volume >= 100000000:
        return f"{volume/100000000:.2f}亿"
    elif volume >= 10000:
        return f"{volume/10000:.2f}万"
    return str(volume)


@app.route('/')
def index():
    indices = get_index()
    return render_template('index.html',
                         indices=indices,
                         a_stocks=A_STOCKS,
                         hk_stocks=HK_STOCKS,
                         us_stocks=US_STOCKS)


@app.route('/quote/<symbol>')
def quote(symbol):
    stock_data = get_stock(symbol)
    
    if stock_data is None:
        return render_template('error.html', message=f"无法获取 {symbol} 数据"), 404
    
    return render_template('quote.html', stock=stock_data)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
