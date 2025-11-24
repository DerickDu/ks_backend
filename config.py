import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Config:
    """
    应用配置基类
    
    包含所有环境下共有的配置项
    """
    # Flask应用基本配置
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    APP_NAME = os.environ.get('APP_NAME', 'Entity Management API')
    APP_VERSION = os.environ.get('APP_VERSION', '1.0.0')
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # 禁用修改跟踪以提高性能
    SQLALCHEMY_ECHO = False  # 在生产环境中关闭SQL查询日志
    
    # CORS配置
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    
    # 错误处理配置
    ERROR_404_HELP = False  # 在生产环境中禁用详细的404错误帮助


class DevelopmentConfig(Config):
    """
    开发环境配置
    
    适用于本地开发和测试的配置项
    """
    DEBUG = True
    SQLALCHEMY_ECHO = True  # 在开发环境中启用SQL查询日志，便于调试


class TestingConfig(Config):
    """
    测试环境配置
    
    适用于自动化测试的配置项
    """
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL', 'sqlite:///:memory:')
    WTF_CSRF_ENABLED = False  # 在测试环境中禁用CSRF保护


class ProductionConfig(Config):
    """
    生产环境配置
    
    适用于生产部署的配置项
    """
    DEBUG = False
    TESTING = False
    
    # 确保在生产环境中有强密钥
    if not os.environ.get('SECRET_KEY'):
        import secrets
        SECRET_KEY = secrets.token_hex(32)


# 配置映射，用于根据环境变量选择不同的配置类
config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config(env=None):
    """
    根据环境获取对应的配置类
    
    参数:
        env: 环境名称，可选值为 'development', 'testing', 'production'
    
    返回:
        Config子类: 对应的配置类
    """
    if env is None:
        env = os.environ.get('FLASK_ENV', 'default')
    return config_by_name.get(env, config_by_name['default'])