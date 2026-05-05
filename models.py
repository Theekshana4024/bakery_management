from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Item(db.Model):
    __tablename__ = 'item'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    quantity_available = db.Column(db.Integer, default=0, nullable=False)
    cost_price = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    stock_ins = db.relationship('StockIn', backref='item', lazy=True, cascade='all, delete-orphan')
    sales = db.relationship('Sale', backref='item', lazy=True, cascade='all, delete-orphan')
    wastes = db.relationship('Waste', backref='item', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'quantity_available': self.quantity_available,
            'cost_price': float(self.cost_price),
            'stock_value': float(self.quantity_available * self.cost_price)
        }

class StockIn(db.Model):
    __tablename__ = 'stock_in'
    
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    cost_price = db.Column(db.Numeric(10, 2), nullable=False)
    added_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'item_name': self.item.name,
            'quantity': self.quantity,
            'cost_price': float(self.cost_price),
            'added_date': self.added_date.isoformat()
        }

class Sale(db.Model):
    __tablename__ = 'sale'
    
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    selling_price = db.Column(db.Numeric(10, 2), nullable=False)
    cost_price = db.Column(db.Numeric(10, 2), nullable=False)
    sale_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def total_revenue(self):
        return self.selling_price * self.quantity
    
    @property
    def total_cost(self):
        return self.cost_price * self.quantity
    
    @property
    def profit(self):
        return (self.selling_price - self.cost_price) * self.quantity
    
    def to_dict(self):
        return {
            'id': self.id,
            'item_name': self.item.name,
            'quantity': self.quantity,
            'selling_price': float(self.selling_price),
            'cost_price': float(self.cost_price),
            'total_revenue': float(self.total_revenue),
            'profit': float(self.profit),
            'sale_date': self.sale_date.isoformat()
        }

class Waste(db.Model):
    __tablename__ = 'waste'
    
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    cost_price = db.Column(db.Numeric(10, 2), nullable=False)
    waste_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def loss_value(self):
        return self.quantity * self.cost_price
    
    def to_dict(self):
        return {
            'id': self.id,
            'item_name': self.item.name,
            'quantity': self.quantity,
            'cost_price': float(self.cost_price),
            'loss_value': float(self.loss_value),
            'waste_date': self.waste_date.isoformat()
        }