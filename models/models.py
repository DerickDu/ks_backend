from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import PrimaryKeyConstraint, ForeignKey, Index
from sqlalchemy.orm import relationship

# 初始化SQLAlchemy实例
db = SQLAlchemy()


class Entities(db.Model):
    """
    实体信息表模型
    
    字段说明：
    - entity_id: 主键，实体ID
    - entity_name: 实体名称，唯一且非空
    - description: 实体描述
    - validity_result: 有效性验证结果
    - validity_method: 有效性验证方法
    - created_at: 创建时间
    - updated_at: 更新时间
    """
    __tablename__ = 'entities'
    
    entity_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    entity_name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    validity_result = db.Column(db.Boolean)
    validity_method = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系定义
    catalogs = relationship('Catalog', back_populates='entity', cascade='all, delete-orphan')
    entity_source_maps = relationship('EntitiesSourceMap', back_populates='entity', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Entities {self.entity_id}: {self.entity_name}>'


class Catalog(db.Model):
    """
    实体分类目录表模型
    
    字段说明：
    - entity_id: 外键，关联Entities表的entity_id
    - path: 挂接目录路径，例如："通信/通信技术/无线传输"
    - domain: 最大的父节点，例如："通信"
    - sub_domain: 第二级节点
    """
    __tablename__ = 'catalog'
    
    entity_id = db.Column(db.BigInteger, ForeignKey('entities.entity_id'), primary_key=True)
    path = db.Column(db.String(255), nullable=False)
    domain = db.Column(db.String(100), nullable=False, index=True)  # 添加索引以优化按domain查询
    sub_domain = db.Column(db.String(100))
    
    # 关系定义
    entity = relationship('Entities', back_populates='catalogs')
    
    # 添加索引以优化性能
    __table_args__ = (
        Index('idx_catalog_domain', 'domain'),
    )
    
    def __repr__(self):
        return f'<Catalog entity_id={self.entity_id}, domain={self.domain}>'


class EntitiesSourceMap(db.Model):
    """
    实体与数据源映射表模型
    
    字段说明：
    - source_id: 联合主键，关联EntitiesSources表的source_id
    - entity_id: 联合主键，关联Entities表的entity_id
    """
    __tablename__ = 'entities_source_map'
    
    source_id = db.Column(db.BigInteger, ForeignKey('entities_sources.source_id'), primary_key=True)
    entity_id = db.Column(db.BigInteger, ForeignKey('entities.entity_id'), primary_key=True)
    
    # 关系定义
    source = relationship('EntitiesSources', back_populates='entity_source_maps')
    entity = relationship('Entities', back_populates='entity_source_maps')
    
    def __repr__(self):
        return f'<EntitiesSourceMap source_id={self.source_id}, entity_id={self.entity_id}>'


class EntitiesSources(db.Model):
    """
    数据源信息表模型
    
    字段说明：
    - source_id: 主键，数据源ID
    - source_type: 数据源类型，非空
    - source_ref: 数据源引用
    - created_at: 创建时间
    """
    __tablename__ = 'entities_sources'
    
    source_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    source_type = db.Column(db.String(100), nullable=False, index=True)
    source_ref = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系定义
    entity_source_maps = relationship('EntitiesSourceMap', back_populates='source', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<EntitiesSources {self.source_id}: {self.source_type}>'