from flask import Flask, jsonify
from flask_cors import CORS
from models import db
from routes import entities_bp
from config import get_config
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def create_app(config_name=None):
    """
    创建并配置Flask应用实例
    
    参数:
        config_name: 配置名称，可选值为 'development', 'testing', 'production'
    
    返回:
        Flask: 配置好的Flask应用实例
    """
    # 创建Flask应用实例
    app = Flask(__name__)
    
    # 加载配置
    config = get_config(config_name)
    app.config.from_object(config)
    
    # 初始化数据库连接
    db.init_app(app)
    
    # 配置CORS
    CORS(app, origins=config.CORS_ORIGINS)
    
    # 注册蓝图
    app.register_blueprint(entities_bp)
    
    # 全局错误处理器
    @app.errorhandler(404)
    def not_found_error(error):
        """处理404错误"""
        return jsonify({"error": "请求的资源不存在"}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """处理500错误"""
        # 确保在开发环境下不会暴露敏感信息
        if app.config['DEBUG']:
            return jsonify({"error": "服务器内部错误", "details": str(error)}), 500
        return jsonify({"error": "服务器内部错误"}), 500
    
    @app.errorhandler(400)
    def bad_request_error(error):
        """处理400错误"""
        return jsonify({"error": "请求参数错误"}), 400
    
    # 根路径路由，返回API信息
    @app.route('/')
    def index():
        """API根路径，返回API基本信息"""
        return jsonify({
            "name": app.config['APP_NAME'],
            "version": app.config['APP_VERSION'],
            "description": "实体管理API服务，提供实体统计相关功能",
            "endpoints": {
                "total_entities": "/api/entities/count",
                "entities_by_domain": "/api/entities/count-by-domain"
            }
        })
    
    # 健康检查端点
    @app.route('/health')
    def health_check():
        """
        健康检查端点，用于监控系统状态
        """
        try:
            # 尝试执行一个简单的数据库查询，验证数据库连接和schema设置
            from sqlalchemy import text
            with db.engine.connect() as conn:
                # 检查ks schema是否存在并且可访问
                result = conn.execute(text("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'ks'"))
                schema_exists = result.fetchone() is not None
                
                if schema_exists:
                    # 在ks schema中执行简单查询
                    conn.execute(text('SELECT 1'))
                    db_status = "connected (ks schema available)"
                else:
                    db_status = "connected (ks schema not found)"
        except Exception as e:
            db_status = f"error: {str(e)}"
        
        return jsonify({
            "status": "healthy",
            "app_name": app.config['APP_NAME'],
            "db_status": db_status
        })
    
    # 创建数据库表（仅在开发环境使用）
    with app.app_context():
        if app.config['DEBUG']:
            try:
                db.create_all()
                print("数据库表创建成功")
            except Exception as e:
                print(f"数据库表创建失败: {e}")
    
    return app


# 当直接运行此文件时启动应用
if __name__ == '__main__':
    # 获取环境配置
    config_name = os.environ.get('FLASK_ENV', 'development')
    app = create_app(config_name)
    
    # 启动应用服务器
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    
    print(f"启动 {app.config['APP_NAME']} v{app.config['APP_VERSION']}")
    print(f"环境: {config_name}")
    print(f"访问地址: http://{host}:{port}")
    
    app.run(host=host, port=port, debug=app.config['DEBUG'])