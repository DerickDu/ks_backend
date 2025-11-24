import unittest
from flask import json
from app import create_app
from models import db, Catalog


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
        # 创建一些测试数据，包含复杂路径用于测试树形结构
        test_data = [
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
        
        db.session.add_all(test_data)
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


if __name__ == '__main__':
    unittest.main()
