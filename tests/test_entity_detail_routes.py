import unittest
import json
from datetime import datetime
from app import app, db
from models import Entities, EntitiesSources, Catalog, EntitiesSourceMap


class EntityDetailRoutesTestCase(unittest.TestCase):
    """entity_detail API路由测试用例"""
    
    def setUp(self):
        """测试前的准备工作"""
        # 设置测试配置
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://test_user:test_password@localhost:5432/test_db?search_path=ks'
        
        # 创建测试客户端
        self.client = app.test_client()
        
        # 创建测试数据库表
        with app.app_context():
            db.create_all()
            
            # 创建测试数据
            self._create_test_data()
    
    def tearDown(self):
        """测试后的清理工作"""
        # 删除测试数据
        with app.app_context():
            db.session.remove()
            db.drop_all()
    
    def _create_test_data(self):
        """创建测试数据"""
        # 创建实体 - 使用正确的字段名
        entity1 = Entities(
            entity_id=1,
            entity_name="测试实体1",
            description="这是第一个测试实体",
            validity_result=True,
            validity_method="method1",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        entity2 = Entities(
            entity_id=2,
            entity_name="测试实体2",
            description="这是第二个测试实体",
            validity_result=False,
            validity_method="method2",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # 创建目录数据
        catalog1 = Catalog(
            entity_id=1,
            path="通信/通信技术/无线传输",
            domain="通信",
            sub_domain="通信技术"
        )
        
        catalog2 = Catalog(
            entity_id=1,
            path="电子/电子设备/通信设备",
            domain="电子",
            sub_domain="电子设备"
        )
        
        # 创建实体源数据
        source1 = EntitiesSources(
            source_id=1,
            source_type="webpage",
            source_ref="https://example.com/source1",
            created_at=datetime.utcnow()
        )
        
        source2 = EntitiesSources(
            source_id=2,
            source_type="document",
            source_ref="https://example.com/source2",
            created_at=datetime.utcnow()
        )
        
        # 创建实体与源映射
        source_map1 = EntitiesSourceMap(
            source_id=1,
            entity_id=1
        )
        
        source_map2 = EntitiesSourceMap(
            source_id=2,
            entity_id=1
        )
        
        # 添加到数据库
        db.session.add_all([
            entity1, entity2, 
            catalog1, catalog2,
            source1, source2,
            source_map1, source_map2
        ])
        db.session.commit()
    
    def test_get_entity_by_id_success(self):
        """测试成功获取实体详情"""
        response = self.client.get('/api/entity-detail/entity?entity_id=1')
        
        # 验证响应状态码
        self.assertEqual(response.status_code, 200)
        
        # 验证响应内容
        data = json.loads(response.data)
        self.assertIn('entity', data)
        self.assertEqual(data['entity']['entity_id'], 1)
        self.assertEqual(data['entity']['entity_name'], "测试实体1")
        self.assertEqual(data['entity']['description'], "这是第一个测试实体")
    
    def test_get_entity_by_id_not_found(self):
        """测试获取不存在的实体"""
        response = self.client.get('/api/entity-detail/entity?entity_id=999')
        
        # 验证响应状态码
        self.assertEqual(response.status_code, 404)
        
        # 验证响应内容
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_get_entity_complete_info_success(self):
        """测试成功获取实体完整信息"""
        response = self.client.get('/api/entity-detail/complete-info?entity_id=1')
        
        # 验证响应状态码
        self.assertEqual(response.status_code, 200)
        
        # 验证响应内容
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['message'], '查询成功')
        
        # 验证数据结构
        self.assertIn('data', data)
        self.assertIn('entity', data['data'])
        self.assertIn('paths', data['data'])
        self.assertIn('source', data['data'])
        
        # 验证entity信息
        entity_info = data['data']['entity']
        self.assertEqual(entity_info['entity_id'], 1)
        self.assertEqual(entity_info['entity_name'], '测试实体1')
        self.assertEqual(entity_info['description'], '这是第一个测试实体')
        
        # 验证paths信息
        paths = data['data']['paths']
        self.assertEqual(len(paths), 2)
        self.assertEqual(paths[0]['domain'], '通信')
        self.assertEqual(paths[1]['domain'], '电子')
        
        # 验证source信息
        sources = data['data']['source']
        self.assertEqual(len(sources), 2)
        self.assertEqual(sources[0]['source_type'], 'webpage')
        self.assertEqual(sources[1]['source_type'], 'document')
    
    def test_get_entity_complete_info_not_found(self):
        """测试获取不存在的实体完整信息"""
        response = self.client.get('/api/entity-detail/complete-info?entity_id=999')
        
        # 验证响应状态码
        self.assertEqual(response.status_code, 404)
        
        # 验证响应内容
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['error_code'], 'ENTITY_NOT_FOUND')
    
    def test_get_entity_complete_info_missing_param(self):
        """测试缺少entity_id参数的情况"""
        response = self.client.get('/api/entity-detail/complete-info')
        
        # 验证响应状态码
        self.assertEqual(response.status_code, 400)
        
        # 验证响应内容
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')
    
    def test_get_entity_complete_info_invalid_param(self):
        """测试无效的entity_id参数"""
        response = self.client.get('/api/entity-detail/complete-info?entity_id=-1')
        
        # 验证响应状态码
        self.assertEqual(response.status_code, 400)
        
        # 验证响应内容
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['error_code'], 'INVALID_PARAMETER')
    
    def test_get_entity_by_id_missing_param(self):
        """测试缺少entity_id参数"""
        response = self.client.get('/api/entity-detail/entity')
        
        # 验证响应状态码
        self.assertEqual(response.status_code, 400)
        
        # 验证响应内容
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_get_entity_by_id_invalid_param(self):
        """测试entity_id参数格式错误"""
        response = self.client.get('/api/entity-detail/entity?entity_id=invalid')
        
        # 验证响应状态码
        self.assertEqual(response.status_code, 400)
        
        # 验证响应内容
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_get_entity_sources_by_id_success(self):
        """测试成功获取实体源数据"""
        response = self.client.get('/api/entity-detail/entity-sources?entity_id=1')
        
        # 验证响应状态码
        self.assertEqual(response.status_code, 200)
        
        # 验证响应内容
        data = json.loads(response.data)
        self.assertIn('sources', data)
        self.assertEqual(len(data['sources']), 2)
        self.assertEqual(data['sources'][0]['entity_id'], 1)
        self.assertEqual(data['sources'][1]['entity_id'], 1)
    
    def test_get_entity_sources_by_id_empty(self):
        """测试获取没有源数据的实体"""
        # 实体2没有关联的源数据
        response = self.client.get('/api/entity-detail/entity-sources?entity_id=2')
        
        # 验证响应状态码
        self.assertEqual(response.status_code, 200)  # 没有找到源数据返回200而不是404
        
        # 验证响应内容
        data = json.loads(response.data)
        self.assertIn('sources', data)
        self.assertEqual(len(data['sources']), 0)
    
    def test_get_entity_sources_by_id_missing_param(self):
        """测试缺少entity_id参数"""
        response = self.client.get('/api/entity-detail/entity-sources')
        
        # 验证响应状态码
        self.assertEqual(response.status_code, 400)
        
        # 验证响应内容
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_get_entity_sources_by_id_invalid_param(self):
        """测试entity_id参数格式错误"""
        response = self.client.get('/api/entity-detail/entity-sources?entity_id=invalid')
        
        # 验证响应状态码
        self.assertEqual(response.status_code, 400)
        
        # 验证响应内容
        data = json.loads(response.data)
        self.assertIn('error', data)


if __name__ == '__main__':
    unittest.main()
