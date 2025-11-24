import unittest
from sqlalchemy import text
from app import create_app
from models import db


class DatabaseSchemaTestCase(unittest.TestCase):
    """
    测试数据库连接和schema设置
    """

    def setUp(self):
        """
        测试前的设置工作
        """
        # 创建测试应用
        self.app = create_app('development')
        self.client = self.app.test_client()
        
        # 创建测试上下文
        self.app_context = self.app.app_context()
        self.app_context.push()
    
    def tearDown(self):
        """
        测试后的清理工作
        """
        self.app_context.pop()
    
    def test_database_connection(self):
        """
        测试数据库连接是否正常
        """
        try:
            with db.engine.connect() as conn:
                result = conn.execute(text('SELECT 1'))
                value = result.scalar()
                self.assertEqual(value, 1)
                print("✓ 数据库连接测试通过")
        except Exception as e:
            self.fail(f"数据库连接测试失败: {str(e)}")
    
    def test_ks_schema_exists(self):
        """
        测试ks schema是否存在
        """
        try:
            with db.engine.connect() as conn:
                result = conn.execute(text("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'ks'"))
                exists = result.fetchone() is not None
                self.assertTrue(exists, "ks schema不存在")
                print("✓ ks schema存在测试通过")
        except Exception as e:
            self.fail(f"ks schema检查失败: {str(e)}")
    
    def test_search_path_includes_ks(self):
        """
        测试数据库连接的search_path是否包含ks schema
        """
        try:
            with db.engine.connect() as conn:
                result = conn.execute(text("SHOW search_path"))
                search_path = result.scalar()
                self.assertIn('ks', search_path, f"search_path不包含ks: {search_path}")
                print(f"✓ search_path测试通过: {search_path}")
        except Exception as e:
            self.fail(f"search_path检查失败: {str(e)}")
    
    def test_schema_in_model_metadata(self):
        """
        测试模型元数据中是否正确设置了schema
        """
        from models import Entities, Catalog, EntitiesSourceMap, EntitiesSources
        
        # 检查所有模型是否都设置了schema='ks'
        for model in [Entities, Catalog, EntitiesSourceMap, EntitiesSources]:
            self.assertEqual(model.__table_args__['schema'], 'ks', 
                            f"模型 {model.__name__} 未设置schema='ks'")
            print(f"✓ 模型 {model.__name__} schema设置正确")
    
    def test_tables_in_ks_schema(self):
        """
        测试ks schema下是否存在所有需要的表
        """
        from models import Entities, Catalog, EntitiesSourceMap, EntitiesSources
        
        expected_tables = [
            model.__tablename__ for model in 
            [Entities, Catalog, EntitiesSourceMap, EntitiesSources]
        ]
        
        try:
            with db.engine.connect() as conn:
                for table_name in expected_tables:
                    # 检查表是否存在于ks schema下
                    result = conn.execute(text(
                        f"SELECT EXISTS ("
                        f"    SELECT FROM information_schema.tables "
                        f"    WHERE table_schema = 'ks' AND table_name = '{table_name}'"
                        f")"
                    ))
                    exists = result.scalar()
                    self.assertTrue(exists, f"表 {table_name} 不存在于ks schema下")
                    print(f"✓ 表 {table_name} 在ks schema下存在")
        except Exception as e:
            self.fail(f"表检查失败: {str(e)}")
    
    def test_health_endpoint_schema_check(self):
        """
        测试健康检查端点是否正确检查了schema
        """
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        # 检查数据库状态是否包含schema信息
        self.assertIn('db_status', data)
        if 'ks schema available' in data['db_status']:
            print("✓ 健康检查端点正确检测到ks schema")
        else:
            print(f"⚠️  健康检查端点schema状态: {data['db_status']}")


if __name__ == '__main__':
    unittest.main()
