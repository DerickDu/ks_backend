from flask import Blueprint, jsonify, request, current_app
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel, Field, field_validator
import logging

from models import Entities, EntitiesSources, Catalog, EntitiesSourceMap, db
from utils.error_handlers import handle_db_error
from utils.validators import validate_query_params

# 获取日志记录器
logger = logging.getLogger(__name__)


class EntityIdValidator(BaseModel):
    """
    实体ID参数验证器
    用于验证entity_detail相关API中的entity_id参数
    """
    entity_id: int = Field(..., ge=1, description="实体ID，必须是正整数")
    
    @field_validator('entity_id')
    def validate_entity_id(cls, v):
        """验证实体ID的合理性"""
        if v < 1:
            raise ValueError("实体ID必须大于0")
        return v

# 创建entity_detail蓝图实例
entity_detail_bp = Blueprint('entity_detail', __name__, url_prefix='/api/entity-detail')


@entity_detail_bp.route('/entity', methods=['GET'])
@validate_query_params(validator_class=EntityIdValidator)
def get_entity_by_id():
    """
    通过entity_id获取Entity表中的完整记录
    
    查询参数：
    - entity_id: 实体ID（必需，整数类型）
    
    响应格式：
    - 成功: {"entity": {"id": <id>, "name": <name>, "description": <description>, ...}}
    - 失败: {"error": "错误信息"}
    
    HTTP状态码：
    - 200: 成功获取实体信息
    - 400: 参数错误
    - 404: 实体不存在
    - 500: 服务器内部错误
    """
    try:
        # 从请求上下文获取验证后的参数
        # 注意：这里使用request.validated_params而不是直接获取参数
        # validate_query_params装饰器已经验证了entity_id的格式和有效性
        entity_id = request.validated_params.get('entity_id')
        
        # 查询实体
        entity = Entities.query.filter_by(id=entity_id).first()
        
        if not entity:
            return jsonify({"error": f"实体不存在: entity_id={entity_id}"}), 404
        
        # 构造响应数据
        entity_data = {
            "id": entity.id,
            "name": entity.name,
            "description": entity.description,
            "created_at": entity.created_at.isoformat() if entity.created_at else None,
            "updated_at": entity.updated_at.isoformat() if entity.updated_at else None
        }
        
        return jsonify({"entity": entity_data}), 200
        
    except ValueError as e:
        # 参数格式错误
        return jsonify({"error": "参数错误", "details": str(e)}), 400
    except SQLAlchemyError as e:
        # 数据库错误
        # 使用统一的错误处理函数处理数据库错误
        return handle_db_error(e)
    except Exception as e:
        # 捕获其他所有未预期的错误
        # 注意：在生产环境中，通常不应该暴露详细的错误信息给客户端
        # 但在开发环境中，可以提供更多调试信息
        return jsonify({"error": "服务器内部错误", "details": str(e)}), 500


@entity_detail_bp.route('/complete-info', methods=['GET'])
@validate_query_params(validator_class=EntityIdValidator)
def get_entity_complete_info():
    """
    获取实体完整信息API
    
    根据提供的entity_id参数，同时从Entity、Catalog和EntitiesSource表中查询并获取对应数据
    
    查询参数：
    - entity_id: 实体ID（必需，整数类型）
    
    响应格式：
    - 成功: {"status": "success", "message": "查询成功", "data": {"entity": entity_info, "paths": catalog_info, "source": source_info}}
    - 失败: {"status": "error", "message": "错误信息", "error_code": "错误代码"}
    
    HTTP状态码：
    - 200: 成功获取实体完整信息
    - 400: 参数错误
    - 404: 实体不存在
    - 500: 服务器内部错误
    """
    try:
        # 记录API调用日志
        logger.info("调用获取实体完整信息API，entity_id: %s", request.validated_params.get('entity_id'))
        
        # 获取验证后的参数
        entity_id = request.validated_params.get('entity_id')
        
        # 1. 查询Entity表数据
        entity = Entities.query.filter_by(entity_id=entity_id).first()
        
        if not entity:
            logger.warning("未找到实体数据，entity_id: %s", entity_id)
            return jsonify({
                "status": "error",
                "message": f"实体不存在: entity_id={entity_id}",
                "error_code": "ENTITY_NOT_FOUND"
            }), 404
        
        # 构建entity_info数据
        entity_info = {
            "entity_id": entity.entity_id,
            "entity_name": entity.entity_name,
            "description": entity.description,
            "validity_result": entity.validity_result,
            "validity_method": entity.validity_method,
            "created_at": entity.created_at.isoformat() if entity.created_at else None,
            "updated_at": entity.updated_at.isoformat() if entity.updated_at else None
        }
        
        # 2. 查询Catalog表数据
        catalogs = Catalog.query.filter_by(entity_id=entity_id).all()
        catalog_info = [
            {
                "entity_id": catalog.entity_id,
                "path": catalog.path,
                "domain": catalog.domain,
                "sub_domain": catalog.sub_domain
            }
            for catalog in catalogs
        ]
        
        # 3. 查询EntitiesSourceMap和EntitiesSources表数据
        # 通过JOIN查询获取实体的所有数据源信息
        sources = db.session.query(EntitiesSources).join(
            EntitiesSourceMap, 
            EntitiesSources.source_id == EntitiesSourceMap.source_id
        ).filter(
            EntitiesSourceMap.entity_id == entity_id
        ).all()
        
        source_info = [
            {
                "source_id": source.source_id,
                "source_type": source.source_type,
                "source_ref": source.source_ref,
                "created_at": source.created_at.isoformat() if source.created_at else None
            }
            for source in sources
        ]
        
        # 组合响应数据
        response_data = {
            "entity": entity_info,
            "paths": catalog_info,
            "source": source_info
        }
        
        logger.info("成功获取实体完整信息，entity_id: %s", entity_id)
        
        # 返回统一格式的成功响应
        return jsonify({
            "status": "success",
            "message": "查询成功",
            "data": response_data
        }), 200
        
    except ValueError as e:
        # 参数验证错误
        logger.error("参数验证错误: %s", str(e))
        return jsonify({
            "status": "error",
            "message": f"参数错误: {str(e)}",
            "error_code": "INVALID_PARAMETER"
        }), 400
    except SQLAlchemyError as e:
        # 数据库错误
        logger.error("数据库操作错误: %s", str(e))
        # 使用统一的错误处理函数处理数据库错误
        error_response, status_code = handle_db_error(e)
        # 确保返回统一格式
        if not isinstance(error_response.get("status"), str):
            return jsonify({
                "status": "error",
                "message": error_response.get("error", "数据库操作错误"),
                "error_code": "DATABASE_ERROR"
            }), status_code
        return error_response, status_code
    except Exception as e:
        # 未预期的错误
        logger.error("未预期的服务器错误: %s", str(e), exc_info=True)
        return jsonify({
            "status": "error",
            "message": "服务器内部错误",
            "error_code": "INTERNAL_ERROR"
        }), 500





@entity_detail_bp.route('/entity-sources', methods=['GET'])
@validate_query_params(validator_class=EntityIdValidator)
def get_entity_sources_by_id():
    """
    通过entity_id获取EntitiesSources表中的完整记录
    
    查询参数：
    - entity_id: 实体ID（必需，整数类型）
    
    响应格式：
    - 成功: {"sources": [{"id": <id>, "entity_id": <entity_id>, "source_url": <source_url>, ...}, ...]}
    - 失败: {"error": "错误信息"}
    
    HTTP状态码：
    - 200: 成功获取实体源信息
    - 400: 参数错误
    - 500: 服务器内部错误
    """
    try:
        # 从请求上下文获取验证后的参数
        entity_id = request.validated_params.get('entity_id')
        
        # 查询实体源数据
        sources = EntitiesSources.query.filter_by(entity_id=entity_id).all()
        
        # 构造响应数据
        sources_data = []
        for source in sources:
            sources_data.append({
                "id": source.id,
                "entity_id": source.entity_id,
                "source_url": source.source_url,
                "source_type": source.source_type,
                "created_at": source.created_at.isoformat() if source.created_at else None,
                "updated_at": source.updated_at.isoformat() if source.updated_at else None
            })
        
        # 即使没有找到源数据，也返回空数组而不是404
        return jsonify({"sources": sources_data}), 200
        
    except ValueError as e:
        # 参数格式错误
        return jsonify({"error": "参数错误", "details": str(e)}), 400
    except SQLAlchemyError as e:
        # 数据库错误
        # 使用统一的错误处理函数处理数据库错误
        return handle_db_error(e)
    except Exception as e:
        # 捕获其他所有未预期的错误
        # 注意：在生产环境中，通常不应该暴露详细的错误信息给客户端
        # 但在开发环境中，可以提供更多调试信息
        return jsonify({"error": "服务器内部错误", "details": str(e)}), 500
