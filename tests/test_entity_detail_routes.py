import unittest
import json
from datetime import datetime
from app import app, db
from models import Entities, EntitiesSources


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
        # 创建实体
        entity1 = Entities(
            id=1,
            name="测试实体1",
            description="这是第一个测试实体",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        entity2 = Entities(
            id=2,
            name="测试实体2",
            description="这是第二个测试实体",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # 创建实体源数据
        source1 = EntitiesSources(
            id=1,
            entity_id=1,
            source_url="https://example.com/source1",
            source_type="webpage",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        source2 = EntitiesSources(
            id=2,
            entity_id=1,
            source_url="https://example.com/source2",
            source_type="document",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # 添加到数据库
        db.session.add_all([entity1, entity2, source1, source2])
        db.session.commit()
    
    def test_get_entity_by_id_success(self):
        """测试成功获取实体详情"""
        response = self.client.get('/api/entity-detail/entity?entity_id=1')
        
        # 验证响应状态码
        self.assertEqual(response.status_code, 200)
        
        # 验证响应内容
        data = json.loads(response.data)
        self.assertIn('entity', data)
        self.assertEqual(data['entity']['id'], 1)
        self.assertEqual(data['entity']['name'], "测试实体1")
        self.assertEqual(data['entity']['description'], "这是第一个测试实体")
    
    def test_get_entity_by_id_not_found(self):
        """测试获取不存在的实体"""
        response = self.client.get('/api/entity-detail/entity?entity_id=999')
        
        # 验证响应状态码
        self.assertEqual(response.status_code, 404)
        
        # 验证响应内容
        data = json.loads(response.data)
        self.assertIn('error', data)
    
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
