from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError
from models import db, Entities, Catalog
from utils.error_handlers import handle_db_error
from utils.validators import validate_query_params, QueryParamsValidator

# 创建蓝图实例
entities_bp = Blueprint('entities', __name__, url_prefix='/api/entities')


@entities_bp.route('/count', methods=['GET'])
@validate_query_params()
def get_total_entities_count():
    """
    获取Entities表中的总记录数
    
    该端点返回Entities表中的实体总数量，以JSON格式响应。
    
    响应格式：
    - 成功: {"total_entities": <数值>}
    - 失败: {"error": "错误信息"}
    
    HTTP状态码：
    - 200: 成功获取总记录数
    - 500: 服务器内部错误，包括数据库连接错误或查询错误
    
    示例请求：
    GET /api/entities/count
    
    示例响应：
    {
        "total_entities": 123
    }
    """
    try:
        # 查询Entities表中的总记录数
        total_count = Entities.query.count()
        
        # 返回结果
        return jsonify({"total_entities": total_count}), 200
        
    except SQLAlchemyError as e:
        # 捕获并处理SQLAlchemy相关错误
        return handle_db_error(e)
    except Exception as e:
        # 捕获其他未预期的错误
        return jsonify({"error": f"服务器内部错误: {str(e)}"}), 500


@entities_bp.route('/count-by-domain', methods=['GET'])
@validate_query_params()
def get_entities_count_by_domain():
    """
    按Domain分组统计Entities表中的实体数量
    
    该端点查询Catalog表，按domain字段分组统计实体数量，并以JSON格式响应。
    
    响应格式：
    - 成功: {"domain1": count1, "domain2": count2, ...}
    - 失败: {"error": "错误信息"}
    
    HTTP状态码：
    - 200: 成功获取按Domain分组的统计数据
    - 500: 服务器内部错误，包括数据库连接错误或查询错误
    
    示例请求：
    GET /api/entities/count-by-domain
    
    示例响应：
    {
        "通信": 15,
        "计算机": 23,
        "人工智能": 42
    }
    """
    try:
        # 优化查询：直接使用已建立的索引，避免不必要的连接
        # 查询仅包含必要字段，并利用idx_catalog_domain索引加速查询
        query = db.session.query(
            Catalog.domain,
            db.func.count(Catalog.entity_id).label('count')
        ).group_by(Catalog.domain)
        
        # 执行查询并获取结果
        result = query.all()
        
        # 将查询结果高效转换为字典格式
        domain_counts = {domain: count for domain, count in result}
        
        # 返回结果
        return jsonify(domain_counts), 200
        
    except SQLAlchemyError as e:
        # 捕获并处理SQLAlchemy相关错误
        return handle_db_error(e)
    except Exception as e:
        # 捕获其他未预期的错误
        return jsonify({"error": f"服务器内部错误: {str(e)}"}), 500