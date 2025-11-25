import unittest
from flask import json
from app import create_app
from models import db, Catalog, Entities, EntitiesSources, EntitiesSourceMap


class EntitiesRoutesTestCase(unittest.TestCase):
    """
    测试entities_routes模块中的API端点
    """

    def setUp(self):
        """
        测试前的设置工作
        """
        # 创建测试应用
        self.app = create_app('testing')
        self.client = self.app.test_client()
        
        # 创建测试上下文
        with self.app.app_context():
            # 创建测试数据库表
            db.create_all()
            
            # 添加测试数据
            self._add_test_data()
    
    def tearDown(self):
        """
        测试后的清理工作
        """
        with self.app.app_context():
            # 删除测试数据库表
            db.drop_all()
    
    def _add_test_data(self):
        """
        添加测试数据到数据库
        """
        # 创建一些测试实体数据
        entities_data = [
            Entities(entity_id=1, entity_name="实体1", description="第一个实体"),
            Entities(entity_id=2, entity_name="实体2", description="第二个实体"),
            Entities(entity_id=3, entity_name="实体3", description="第三个实体"),
            Entities(entity_id=4, entity_name="实体4", description="第四个实体"),
            Entities(entity_id=5, entity_name="实体5", description="第五个实体"),
            Entities(entity_id=6, entity_name="实体6", description="第六个实体"),
            Entities(entity_id=7, entity_name="实体7", description="第七个实体"),
            Entities(entity_id=8, entity_name="实体8", description="第八个实体"),
            Entities(entity_id=9, entity_name="实体9", description="第九个实体"),
            Entities(entity_id=10, entity_name="实体10", description="第十个实体"),
            Entities(entity_id=11, entity_name="实体11", description="第十一个实体"),
            Entities(entity_id=12, entity_name="实体12", description="第十二个实体"),
            Entities(entity_id=13, entity_name="实体13", description="第十三个实体"),
            Entities(entity_id=14, entity_name="实体14", description="第十四个实体"),
            Entities(entity_id=15, entity_name="实体15", description="第十五个实体"),
        ]
        
        # 创建一些测试数据，包含复杂路径用于测试树形结构
        catalog_data = [
            # 简单路径测试
            Catalog(entity_id=1, path="通信/无线通信", domain="通信", sub_domain="无线通信"),
            Catalog(entity_id=2, path="通信/光纤通信", domain="通信", sub_domain="光纤通信"),
            Catalog(entity_id=3, path="计算机/硬件", domain="计算机", sub_domain="硬件"),
            Catalog(entity_id=4, path="计算机/软件", domain="计算机", sub_domain="软件"),
            Catalog(entity_id=5, path="人工智能/机器学习", domain="人工智能", sub_domain="机器学习"),
            Catalog(entity_id=6, path="人工智能/深度学习", domain="人工智能", sub_domain="深度学习"),
            Catalog(entity_id=7, path="数据科学", domain="数据科学", sub_domain=None),
            
            # 复杂路径测试 - 用于测试entities-tree API
            Catalog(entity_id=8, path="通信/无线通信/5G", domain="通信", sub_domain="无线通信"),
            Catalog(entity_id=9, path="通信/无线通信/WiFi", domain="通信", sub_domain="无线通信"),
            Catalog(entity_id=10, path="通信/无线通信/5G/毫米波", domain="通信", sub_domain="无线通信"),
            Catalog(entity_id=11, path="通信/无线通信/5G/大规模MIMO", domain="通信", sub_domain="无线通信"),
            Catalog(entity_id=12, path="计算机/软件/操作系统", domain="计算机", sub_domain="软件"),
            Catalog(entity_id=13, path="计算机/软件/编程语言", domain="计算机", sub_domain="软件"),
            Catalog(entity_id=14, path="计算机/软件/编程语言/Python", domain="计算机", sub_domain="软件"),
            Catalog(entity_id=15, path="计算机/软件/编程语言/Java", domain="计算机", sub_domain="软件"),
        ]
        
        # 创建一些测试数据源
        sources_data = [
            EntitiesSources(source_id=1, source_type="数据库"),
            EntitiesSources(source_id=2, source_type="API接口"),
            EntitiesSources(source_id=3, source_type="文件系统"),
            EntitiesSources(source_id=4, source_type="数据库"),
            EntitiesSources(source_id=5, source_type="API接口"),
        ]
        
        # 创建实体与数据源的映射关系
        source_map_data = [
            EntitiesSourceMap(source_id=1, entity_id=1),
            EntitiesSourceMap(source_id=1, entity_id=2),
            EntitiesSourceMap(source_id=2, entity_id=3),
            EntitiesSourceMap(source_id=2, entity_id=4),
            EntitiesSourceMap(source_id=3, entity_id=5),
            EntitiesSourceMap(source_id=4, entity_id=6),
            EntitiesSourceMap(source_id=4, entity_id=7),
            EntitiesSourceMap(source_id=5, entity_id=8),
            EntitiesSourceMap(source_id=5, entity_id=9),
            EntitiesSourceMap(source_id=1, entity_id=10),
        ]
        
        # 添加所有测试数据到数据库
        db.session.add_all(entities_data)
        db.session.add_all(catalog_data)
        db.session.add_all(sources_data)
        db.session.add_all(source_map_data)
        db.session.commit()
    
    def test_get_domains_tree(self):
        """
        测试获取domain和sub_domain树形结构的API端点
        """
        # 发送GET请求
        response = self.client.get('/api/entities/domains-tree')
        
        # 检查响应状态码
        self.assertEqual(response.status_code, 200)
        
        # 检查响应数据
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
        
        # 检查是否包含所有预期的domain
        domains = [item['key'] for item in data]
        expected_domains = ['通信', '计算机', '人工智能', '数据科学']
        for domain in expected_domains:
            self.assertIn(domain, domains)
        
        # 检查特定domain的子节点
        communication_node = next((item for item in data if item['key'] == '通信'), None)
        self.assertIsNotNone(communication_node)
        self.assertIn('children', communication_node)
        self.assertEqual(len(communication_node['children']), 2)
        
        # 检查子节点的key格式是否正确
        sub_domain_keys = [child['key'] for child in communication_node['children']]
        expected_subdomain_keys = ['通信:无线通信', '通信:光纤通信']
        for key in expected_subdomain_keys:
            self.assertIn(key, sub_domain_keys)
    
    def test_get_domains_tree_with_refresh(self):
        """
        测试使用refresh参数强制刷新缓存
        """
        # 发送带有refresh参数的GET请求
        response = self.client.get('/api/entities/domains-tree?refresh=true')
        
        # 检查响应状态码
        self.assertEqual(response.status_code, 200)
        
        # 验证响应数据是否为列表格式
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
    
    def test_domain_without_subdomain(self):
        """
        测试没有sub_domain的domain
        """
        response = self.client.get('/api/entities/domains-tree')
        data = json.loads(response.data)
        
        # 查找'data science'节点
        data_science_node = next((item for item in data if item['key'] == '数据科学'), None)
        self.assertIsNotNone(data_science_node)
        
        # 验证没有子节点
        self.assertIn('children', data_science_node)
        self.assertEqual(len(data_science_node['children']), 0)
    
    def test_get_entities_tree(self):
        """
        测试根据domain和sub_domain获取实体树结构的API端点
        """
        # 发送GET请求，获取通信/无线通信下的实体树
        response = self.client.get('/api/entities-tree?domain=通信&sub_domain=无线通信')
        
        # 检查响应状态码
        self.assertEqual(response.status_code, 200)
        
        # 检查响应数据
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
        
        # 检查是否有顶层节点
        self.assertTrue(len(data) > 0)
        
        # 检查顶层节点的格式
        for node in data:
            self.assertIn('key', node)
            self.assertIn('title', node)
            self.assertIn('isLeaf', node)
            self.assertIn('children', node)
            self.assertIn('entity_id', node)
        
        # 检查是否包含5G节点
        five_g_node = next((item for item in data if item['title'] == '5G'), None)
        self.assertIsNotNone(five_g_node)
        self.assertFalse(five_g_node['isLeaf'])  # 不是叶子节点，因为有子节点
        
        # 检查5G节点是否有子节点
        self.assertTrue(len(five_g_node['children']) > 0)
        
        # 检查毫米波节点
        mmwave_node = next(
            (item for item in five_g_node['children'] if item['title'] == '毫米波'),
            None
        )
        self.assertIsNotNone(mmwave_node)
        self.assertTrue(mmwave_node['isLeaf'])  # 是叶子节点
        self.assertEqual(mmwave_node['entity_id'], 10)  # 检查实体ID
    
    def test_get_entities_tree_missing_params(self):
        """
        测试缺少参数时的错误处理
        """
        # 测试缺少domain参数
        response = self.client.get('/api/entities-tree?sub_domain=无线通信')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        
        # 测试缺少sub_domain参数
        response = self.client.get('/api/entities-tree?domain=通信')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        
        # 测试两个参数都缺少
        response = self.client.get('/api/entities-tree')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_get_entities_tree_with_refresh(self):
        """
        测试使用refresh参数强制刷新缓存
        """
        # 发送带有refresh参数的GET请求
        response = self.client.get('/api/entities-tree?domain=通信&sub_domain=无线通信&refresh=true')
        
        # 检查响应状态码
        self.assertEqual(response.status_code, 200)
        
        # 验证响应数据是否为列表格式
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
    
    def test_get_entities_count_by_source_type(self):
        """
        测试统计Entities Source表中不同source_type对应的实体数量的API端点
        """
        # 发送GET请求
        response = self.client.get('/api/entities/count-by-source-type')
        
        # 检查响应状态码
        self.assertEqual(response.status_code, 200)
        
        # 检查响应数据
        data = json.loads(response.data)
        self.assertIsInstance(data, dict)
        
        # 验证返回的数据是否符合预期
        # 根据我们的测试数据：
        # 数据库类型应该有4个实体 (source_id=1关联了entity_id=1,2,10; source_id=4关联了entity_id=6,7)
        # API接口类型应该有3个实体 (source_id=2关联了entity_id=3,4; source_id=5关联了entity_id=8,9)
        # 文件系统类型应该有1个实体 (source_id=3关联了entity_id=5)
        expected_counts = {
            "数据库": 4,
            "API接口": 3,
            "文件系统": 1
        }
        
        # 验证每种source_type的数量是否正确
        for source_type, expected_count in expected_counts.items():
            self.assertIn(source_type, data)
            self.assertEqual(data[source_type], expected_count, 
                           f"{source_type}的数量应该是{expected_count}，但实际是{data[source_type]}")
        
        # 验证只返回了这三种source_type，没有其他类型
        self.assertEqual(len(data), len(expected_counts))
    
    def test_get_entities_count_by_source_type_empty_database(self):
        """
        测试当数据库中没有数据时，统计API的行为
        """
        with self.app.app_context():
            # 清空数据源映射表
            EntitiesSourceMap.query.delete()
            # 清空数据源表
            EntitiesSources.query.delete()
            # 提交更改
            db.session.commit()
        
        # 发送GET请求
        response = self.client.get('/api/entities/count-by-source-type')
        
        # 检查响应状态码
        self.assertEqual(response.status_code, 200)
        
        # 检查响应数据应该是空字典
        data = json.loads(response.data)
        self.assertIsInstance(data, dict)
        self.assertEqual(len(data), 0)


if __name__ == '__main__':
    unittest.main()
