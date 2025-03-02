import requests
import json
import datetime
from flask import Flask, render_template, request, redirect, url_for, abort
from flask_caching import Cache
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# 初始化缓存
cache = Cache(app)

# 飞书API相关函数
def get_tenant_access_token():
    """获取飞书tenant_access_token"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    headers = {"Content-Type": "application/json"}
    data = {
        "app_id": app.config["FEISHU_APP_ID"],
        "app_secret": app.config["FEISHU_APP_SECRET"]
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        result = response.json()
        if result.get("code") == 0:
            return result.get("tenant_access_token")
    return None

@cache.cached(timeout=3600, key_prefix="feishu_data")
def get_bitable_data():
    """从飞书多维表格获取数据"""
    token = get_tenant_access_token()
    if not token:
        return []
    
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app.config['BASE_ID']}/tables/{app.config['TABLE_ID']}/records"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    # 添加参数以获取所有记录
    params = {
        "page_size": 100  # 设置较大的页面大小以获取更多记录
    }
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        result = response.json()
        if result.get("code") == 0:
            return result.get("data", {}).get("items", [])
    return []

# 处理JSON格式的文本内容
def process_json_text(raw_text):
    """处理可能是JSON格式的文本，提取所有文本内容并连接"""
    if not isinstance(raw_text, str):
        return raw_text
    
    # 处理空字符串
    if not raw_text.strip():
        return raw_text
    
    # 处理字符串形式的JSON数组，如："[{'text': '内容', 'type': 'text'}]"
    # 这种情况下，字符串中使用的是单引号而不是双引号，无法直接用json.loads解析
    if raw_text.startswith("[") and "'text'" in raw_text and "'type'" in raw_text:
        try:
            # 尝试将单引号替换为双引号以便解析
            # 注意：这是一个简化处理，可能不适用于所有情况
            normalized_text = raw_text.replace("'", '"')
            text_data = json.loads(normalized_text)
            
            extracted_texts = []
            for item in text_data:
                if isinstance(item, dict) and 'text' in item:
                    extracted_texts.append(item['text'])
            
            if extracted_texts:
                return ' '.join(extracted_texts)
            return raw_text
        except (json.JSONDecodeError, TypeError):
            pass  # 如果解析失败，继续尝试其他方法
        
    # 尝试处理标准JSON格式的文本
    try:
        # 检查是否可能是JSON格式
        if (raw_text.startswith('[') and raw_text.endswith(']')) or \
           (raw_text.startswith('{') and raw_text.endswith('}')):
            text_data = json.loads(raw_text)
            
            # 处理列表类型的JSON
            if isinstance(text_data, list):
                extracted_texts = []
                for item in text_data:
                    # 处理特定格式：[{"text": "内容", "type": "text"}]
                    if isinstance(item, dict) and 'text' in item and 'type' in item and item.get('type') == 'text':
                        extracted_texts.append(item['text'])
                    # 如果是字典且包含text字段
                    elif isinstance(item, dict) and 'text' in item:
                        extracted_texts.append(item['text'])
                    # 如果是字典但没有text字段，尝试获取其他可能的文本字段
                    elif isinstance(item, dict):
                        for key, value in item.items():
                            if isinstance(value, str):
                                extracted_texts.append(value)
                                break
                    # 如果是字符串，直接添加
                    elif isinstance(item, str):
                        extracted_texts.append(item)
                
                # 如果成功提取了文本，则返回连接后的文本
                if extracted_texts:
                    return ' '.join(extracted_texts)
            
            # 处理字典类型的JSON
            elif isinstance(text_data, dict):
                # 处理特定格式：{"text": "内容", "type": "text"}
                if 'text' in text_data and 'type' in text_data and text_data.get('type') == 'text':
                    return text_data['text']
                # 如果字典中有text字段
                elif 'text' in text_data:
                    return text_data['text']
                # 尝试获取字典中的第一个字符串值
                for key, value in text_data.items():
                    if isinstance(value, str):
                        return value
                        
        # 如果不是有效的JSON或无法提取文本，返回原始文本
        return raw_text
    except (json.JSONDecodeError, TypeError):
        return raw_text

# 路由设置
@app.route('/')
def index():
    articles = get_bitable_data()
    processed_articles = []
    
    for article in articles:
        fields = article.get("fields", {})
        # 获取原始内容
        raw_title = fields.get("标题", "")
        raw_quote = fields.get("金句输出", "")
        raw_comment = fields.get("黄叔点评", "")
        raw_content = fields.get("概要内容输出", "")
        
        # 处理可能的JSON格式内容
        processed_article = {
            "id": article.get("record_id"),
            "title": process_json_text(raw_title),
            "quote": process_json_text(raw_quote),
            "comment": process_json_text(raw_comment),
            "content": process_json_text(raw_content)
        }
        processed_articles.append(processed_article)
    
    current_year = datetime.datetime.now().year
    return render_template('index.html', articles=processed_articles, current_year=current_year)

@app.route('/article/<article_id>')
def article_detail(article_id):
    articles = get_bitable_data()
    article = None
    
    for item in articles:
        if item.get("record_id") == article_id:
            fields = item.get("fields", {})
            # 获取原始内容
            raw_title = fields.get("标题", "")
            raw_quote = fields.get("金句输出", "")
            raw_comment = fields.get("黄叔点评", "")
            raw_content = fields.get("概要内容输出", "")
            
            # 处理可能的JSON格式内容并创建文章对象
            article = {
                "id": item.get("record_id"),
                "title": process_json_text(raw_title),
                "quote": process_json_text(raw_quote),
                "comment": process_json_text(raw_comment),
                "content": process_json_text(raw_content)
            }
            break
    
    if not article:
        abort(404)
        
    current_year = datetime.datetime.now().year
    return render_template('detail.html', article=article, current_year=current_year)

@app.errorhandler(404)
def page_not_found(e):
    current_year = datetime.datetime.now().year
    return render_template('404.html', current_year=current_year), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=app.config['DEBUG'])