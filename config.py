import os
from dotenv import load_dotenv

# 加载.env文件中的环境变量（如果存在）
load_dotenv()

class Config:
    # 飞书应用配置
    FEISHU_APP_ID = os.getenv("FEISHU_APP_ID", "cli_a74947d158fbd00e")
    FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET", "ba3ugcQrfLuAcX10CyZbYdPZSz2GkIL5")
    
    # 多维表格配置
    BASE_ID = os.getenv("BASE_ID", "RIt3bjzYZaAm0MsR9DBc7qzRnAb")
    TABLE_ID = os.getenv("TABLE_ID", "tbli9iBxwTXoiLkp")
    
    # Flask应用配置
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    
    # 缓存配置
    CACHE_TYPE = "SimpleCache"
    CACHE_DEFAULT_TIMEOUT = 300  # 缓存过期时间（秒）