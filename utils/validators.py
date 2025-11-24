from typing import Optional
from pydantic import BaseModel, Field, field_validator
from flask import request, jsonify


class QueryParamsValidator(BaseModel):
    """
    通用查询参数验证器
    
    用于验证API请求中的查询参数，支持分页、排序等常见参数
    """
    page: Optional[int] = Field(default=1, ge=1, description="页码，从1开始")
    per_page: Optional[int] = Field(default=10, ge=1, le=1000, description="每页记录数，最大1000")
    sort_by: Optional[str] = Field(default=None, description="排序字段")
    order: Optional[str] = Field(default="asc", pattern="^(asc|desc)$", description="排序方向，可选值：asc、desc")
    
    @field_validator('per_page')
    def validate_per_page(cls, v):
        """验证每页记录数的合理性"""
        if v > 1000:
            raise ValueError("每页记录数不能超过1000")
        return v


def validate_query_params(validator_class=QueryParamsValidator):
    """
    验证查询参数的装饰器
    
    用于装饰API路由函数，自动验证查询参数并将验证后的值注入请求上下文
    
    参数:
        validator_class: 用于验证的Pydantic模型类
    
    返回:
        装饰后的路由函数
    """
    def decorator(f):
        def wrapper(*args, **kwargs):
            try:
                # 从请求中获取查询参数
                params = request.args.to_dict()
                
                # 类型转换 - 将字符串转换为适当的类型
                if 'page' in params:
                    params['page'] = int(params['page'])
                if 'per_page' in params:
                    params['per_page'] = int(params['per_page'])
                
                # 使用Pydantic验证器验证参数
                validated_params = validator_class(**params)
                
                # 将验证后的参数存储在请求上下文中
                request.validated_params = validated_params.model_dump()
                
                # 继续执行原路由函数
                return f(*args, **kwargs)
                
            except ValueError as e:
                # 处理类型转换错误
                return jsonify({"error": "参数类型错误", "details": str(e)}), 400
            except Exception as e:
                # 处理验证错误
                return jsonify({"error": "参数验证失败", "details": str(e)}), 400
        
        # 保留原函数的元数据
        wrapper.__name__ = f.__name__
        wrapper.__doc__ = f.__doc__
        wrapper.__module__ = f.__module__
        
        return wrapper
    
    return decorator


def validate_request_data(validator_class):
    """
    验证请求体数据的装饰器
    
    用于装饰API路由函数，自动验证请求体JSON数据并将验证后的值注入请求上下文
    
    参数:
        validator_class: 用于验证的Pydantic模型类
    
    返回:
        装饰后的路由函数
    """
    def decorator(f):
        def wrapper(*args, **kwargs):
            try:
                # 尝试从请求体获取JSON数据
                data = request.get_json()
                
                if data is None:
                    return jsonify({"error": "请求体必须是有效的JSON格式"}), 400
                
                # 使用Pydantic验证器验证数据
                validated_data = validator_class(**data)
                
                # 将验证后的数据存储在请求上下文中
                request.validated_data = validated_data.model_dump()
                
                # 继续执行原路由函数
                return f(*args, **kwargs)
                
            except ValueError as e:
                # 处理JSON解析错误
                return jsonify({"error": "JSON解析错误", "details": str(e)}), 400
            except Exception as e:
                # 处理验证错误
                return jsonify({"error": "请求数据验证失败", "details": str(e)}), 400
        
        # 保留原函数的元数据
        wrapper.__name__ = f.__name__
        wrapper.__doc__ = f.__doc__
        wrapper.__module__ = f.__module__
        
        return wrapper
    
    return decorator