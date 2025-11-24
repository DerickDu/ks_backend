from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError

from models import Catalog, Entities, db
from utils.error_handlers import handle_db_error
from utils.validators import QueryParamsValidator, validate_query_params

# 简单的内存缓存，用于存储domain树结构
_domain_tree_cache = None
_cache_timestamp = 0
# 新增缓存，用于存储基于sub_domain的实体树结构
_subdomain_entity_cache = {}
_subdomain_entity_timestamp = {}
CACHE_DURATION = 300  # 缓存持续时间（秒）
import time

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


def _convert_to_tree_format(domain_subdomain_pairs):
    """
    将domain和sub_domain对转换为Ant Design Tree组件所需的树形结构
    
    Args:
        domain_subdomain_pairs: 包含(domain, sub_domain)的列表
    
    Returns:
        符合Ant Design Tree组件格式的树形结构列表
    """
    # 创建domain到sub_domains的映射
    domain_map = {}
    
    for domain, sub_domain in domain_subdomain_pairs:
        if domain not in domain_map:
            # 为每个唯一的domain创建一个父节点
            domain_map[domain] = {
                'key': domain,
                'title': domain,
                'children': []
            }
        
        # 如果有sub_domain，且不为空，则添加为子节点
        if sub_domain and sub_domain.strip():
            # 检查是否已经添加过相同的sub_domain
            if not any(child['key'] == sub_domain for child in domain_map[domain]['children']):
                domain_map[domain]['children'].append({
                    'key': f"{domain}:{sub_domain}",
                    'title': sub_domain
                })
    
    # 转换为列表并返回
    return list(domain_map.values())


def _is_cache_valid():
    """
    检查缓存是否有效
    """
    global _cache_timestamp
    if _cache_timestamp == 0:
        return False
    return (time.time() - _cache_timestamp) < CACHE_DURATION


def _refresh_domain_tree_cache():
    """
    刷新domain树结构缓存
    """
    global _domain_tree_cache, _cache_timestamp
    
    try:
        # 查询所有唯一的domain和对应的sub_domain对
        query = db.session.query(
            Catalog.domain,
            Catalog.sub_domain
        ).distinct()
        
        # 执行查询
        result = query.all()
        
        # 转换为Ant Design Tree格式
        _domain_tree_cache = _convert_to_tree_format(result)
        _cache_timestamp = time.time()
        
        return _domain_tree_cache
    except Exception as e:
        # 缓存刷新失败时，保留旧缓存（如果存在）
        print(f"缓存刷新失败: {str(e)}")
        return _domain_tree_cache


def _build_path_tree(domain, sub_domain, catalogs):
    """
    根据domain、sub_domain和catalog数据构建Ant Design Tree格式的树形结构
    
    Args:
        domain: 领域名称
        sub_domain: 子领域名称
        catalogs: 目录数据列表
    
    Returns:
        符合Ant Design Tree格式的树形结构列表
    """
    # 构建路径映射结构
    path_map = {}
    
    # 处理每个路径
    for catalog in catalogs:
        # 按/分割路径
        path_parts = catalog.path.split("/")
        
        # 跳过domain和subDomain部分（前两项）
        relative_path_parts = path_parts[2:] if len(path_parts) > 2 else []
        
        # 如果没有足够的层级（至少还需要一级），跳过
        if len(relative_path_parts) < 1:
            continue
        
        current_path = ""
        
        # 构建路径层级
        for i in range(len(relative_path_parts)):
            part = relative_path_parts[i]
            is_last = i == len(relative_path_parts) - 1
            
            # 构建当前路径标识
            current_path = f"{current_path}/{part}" if current_path else part
            full_key = f"{domain}/{sub_domain}/{current_path}"
            
            # 如果该路径节点不存在，则创建
            if full_key not in path_map:
                path_map[full_key] = {
                    "title": part,
                    "isLeaf": False,  # 默认为非叶子节点，除非是最后一级且有entity_id
                    "children": [],
                    "entity_id": None
                }
            
            # 如果是最后一级且有entity_id，则关联实体信息
            if is_last and catalog.entity_id:
                path_map[full_key]["isLeaf"] = True
                path_map[full_key]["entity_id"] = catalog.entity_id
    
    # 构建树结构
    root_nodes = []
    node_map = {}
    
    # 先创建所有节点
    for key, value in path_map.items():
        node = {
            "title": value["title"],
            "key": key,
            "isLeaf": value["isLeaf"],
            "children": [],
            "entity_id": value["entity_id"]
        }
        
        node_map[key] = node
        
        # 找出根节点（即直接在domain/subDomain下的节点）
        path_parts = key.split("/")
        if len(path_parts) == 3:
            # domain/subDomain/node
            root_nodes.append(node)
    
    # 构建父子关系
    for key, node in node_map.items():
        path_parts = key.split("/")
        
        # 如果不是顶层节点，找到父节点并添加到其子节点中
        if len(path_parts) > 3:
            parent_key = "/".join(path_parts[:-1])
            if parent_key in node_map:
                node_map[parent_key]["children"].append(node)
    
    return root_nodes


def _is_subdomain_cache_valid(domain, sub_domain):
    """
    检查基于sub_domain的实体树缓存是否有效
    """
    cache_key = f"{domain}:{sub_domain}"
    return (cache_key in _subdomain_entity_timestamp and 
            (time.time() - _subdomain_entity_timestamp[cache_key]) < CACHE_DURATION)


def _refresh_subdomain_entity_cache(domain, sub_domain):
    """
    刷新基于sub_domain的实体树缓存
    """
    cache_key = f"{domain}:{sub_domain}"
    
    try:
        # 查询指定domain和sub_domain下的所有catalog记录，包括关联的entity信息
        catalogs = Catalog.query.filter_by(
            domain=domain,
            sub_domain=sub_domain
        ).all()
        
        # 构建树形结构
        tree_data = _build_path_tree(domain, sub_domain, catalogs)
        
        # 更新缓存
        _subdomain_entity_cache[cache_key] = tree_data
        _subdomain_entity_timestamp[cache_key] = time.time()
        
        return tree_data
    except Exception as e:
        # 缓存刷新失败时，保留旧缓存（如果存在）
        print(f"subdomain实体树缓存刷新失败: {str(e)}")
        return _subdomain_entity_cache.get(cache_key, [])


@entities_bp.route('/domains-tree', methods=['GET'])
@validate_query_params()
def get_domains_tree():
    """
    获取所有唯一的domain和sub_domain，并转换为Ant Design Tree组件所需的树形结构
    
    该端点查询Catalog表，获取所有唯一的domain和sub_domain对，并将其组织成
    符合Ant Design Tree组件要求的层级结构（domain为父节点，sub_domain为子节点）。
    
    响应格式：
    - 成功: [{"key": "domain1", "title": "domain1", "children": [{"key": "sub_domain1", "title": "sub_domain1"}, ...]}, ...]
    - 失败: {"error": "错误信息"}
    
    HTTP状态码：
    - 200: 成功获取树形结构数据
    - 500: 服务器内部错误，包括数据库连接错误或查询错误
    
    缓存策略：
    - 实现了简单的内存缓存，缓存持续时间为5分钟
    - 缓存可以通过添加refresh参数来强制刷新
    
    示例请求：
    GET /api/entities/domains-tree
    GET /api/entities/domains-tree?refresh=true  # 强制刷新缓存
    
    示例响应：
    [
        {
            "key": "通信",
            "title": "通信",
            "children": [
                {"key": "通信:无线通信", "title": "无线通信"},
                {"key": "通信:光纤通信", "title": "光纤通信"}
            ]
        },
        {
            "key": "计算机",
            "title": "计算机",
            "children": [
                {"key": "计算机:硬件", "title": "硬件"},
                {"key": "计算机:软件", "title": "软件"}
            ]
        }
    ]
    """
    try:
        # 检查是否需要强制刷新缓存
        refresh_cache = request.args.get('refresh', 'false').lower() == 'true'
        
        # 如果缓存有效且不需要强制刷新，则使用缓存
        if _is_cache_valid() and not refresh_cache:
            return jsonify(_domain_tree_cache), 200
        
        # 刷新缓存并返回结果
        domain_tree = _refresh_domain_tree_cache()
        
        if domain_tree is not None:
            return jsonify(domain_tree), 200
        else:
            # 如果缓存和查询都失败
            return jsonify({"error": "获取domain树结构失败"}), 500
            
    except SQLAlchemyError as e:
        # 捕获并处理SQLAlchemy相关错误
        return handle_db_error(e)
    except Exception as e:
        # 捕获其他未预期的错误
        return jsonify({"error": f"服务器内部错误: {str(e)}"}), 500


@entities_bp.route('/entities-tree', methods=['GET'])
@validate_query_params()
def get_entities_tree():
    """
    根据指定的domain和sub_domain获取实体和目录的树形结构
    
    该端点查询Catalog表，获取指定domain和sub_domain下的所有目录和关联实体，并将其
    组织成符合Ant Design Tree组件要求的层级结构。每个叶子节点会包含对应的实体ID。
    
    查询参数：
    - domain: 领域名称（必需）
    - sub_domain: 子领域名称（必需）
    - refresh: 强制刷新缓存（可选，布尔值）
    
    响应格式：
    - 成功: [{"key": "path1", "title": "path1", "isLeaf": false, "children": [...], "entity_id": null}, ...]
    - 失败: {"error": "错误信息"}
    
    HTTP状态码：
    - 200: 成功获取实体树结构数据
    - 400: 参数错误
    - 500: 服务器内部错误，包括数据库连接错误或查询错误
    
    缓存策略：
    - 实现了基于domain和sub_domain的内存缓存，缓存持续时间为5分钟
    - 缓存可以通过添加refresh=true参数来强制刷新
    """
    try:
        # 获取请求参数
        domain = request.args.get('domain')
        sub_domain = request.args.get('sub_domain')
        refresh = request.args.get('refresh', 'false').lower() == 'true'
        
        # 参数验证
        if not domain or not sub_domain:
            return jsonify({"error": "缺少必需参数: domain 和 sub_domain"}), 400
        
        # 检查缓存是否有效
        if not refresh and _is_subdomain_cache_valid(domain, sub_domain):
            cache_key = f"{domain}:{sub_domain}"
            return jsonify(_subdomain_entity_cache.get(cache_key, [])), 200
        
        # 缓存无效或强制刷新时，刷新缓存
        tree_data = _refresh_subdomain_entity_cache(domain, sub_domain)
        return jsonify(tree_data), 200
    
    except ValueError as e:
        # 参数格式错误
        return jsonify({"error": f"参数错误: {str(e)}"}), 400
    except SQLAlchemyError as e:
        # 捕获并处理SQLAlchemy相关错误
        return handle_db_error(e)
    except Exception as e:
        # 捕获其他未预期的错误
        return jsonify({"error": f"服务器内部错误: {str(e)}"}), 500