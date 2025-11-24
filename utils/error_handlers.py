from flask import jsonify
from sqlalchemy.exc import (
    SQLAlchemyError,
    IntegrityError,
    ProgrammingError,
    OperationalError,
    DataError,
    InvalidRequestError
)

def handle_db_error(error):
    """
    统一处理数据库相关错误
    
    根据不同类型的数据库错误返回相应的错误消息和状态码
    
    参数:
        error: SQLAlchemyError实例或其子类实例
    
    返回:
        tuple: (JSON响应对象, HTTP状态码)
    """
    error_message = str(error)
    
    # 根据错误类型提供更具体的错误信息
    if isinstance(error, OperationalError):
        # 连接错误、表不存在等操作错误
        return jsonify({"error": "数据库连接错误或操作失败", "details": error_message}), 500
    elif isinstance(error, IntegrityError):
        # 完整性约束错误（如外键约束、唯一约束）
        return jsonify({"error": "数据完整性错误", "details": error_message}), 400
    elif isinstance(error, ProgrammingError):
        # SQL语法错误、未知列等
        return jsonify({"error": "数据库查询语法错误", "details": error_message}), 500
    elif isinstance(error, DataError):
        # 数据类型不匹配、值过大等
        return jsonify({"error": "数据类型错误或值超出范围", "details": error_message}), 400
    elif isinstance(error, InvalidRequestError):
        # SQLAlchemy使用错误
        return jsonify({"error": "无效的数据库请求", "details": error_message}), 400
    else:
        # 其他未预期的数据库错误
        return jsonify({"error": "数据库操作失败", "details": error_message}), 500