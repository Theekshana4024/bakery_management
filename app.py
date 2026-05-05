from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from sqlalchemy import func, extract
from models import db, Item, StockIn, Sale, Waste

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/bakery_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

# ==================== PAGE ROUTES ====================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add-stock')
def add_stock_page():
    return render_template('add_stock.html')

@app.route('/add-sales')
def add_sales_page():
    return render_template('add_sales.html')

@app.route('/add-waste')
def add_waste_page():
    return render_template('add_waste.html')

@app.route('/daily-report')
def daily_report_page():
    return render_template('daily_report.html')

@app.route('/monthly-report')
def monthly_report_page():
    return render_template('monthly_report.html')

# ==================== API ENDPOINTS ====================

@app.route('/api/items', methods=['GET'])
def get_items():
    """Get all items with current stock"""
    items = Item.query.all()
    return jsonify([item.to_dict() for item in items])

@app.route('/api/stock', methods=['POST'])
def add_stock():
    """Add stock to an item (creates item if doesn't exist)"""
    data = request.get_json()
    
    if not data or not all(k in data for k in ('name', 'quantity', 'cost_price')):
        return jsonify({'error': 'Missing required fields: name, quantity, cost_price'}), 400
    
    try:
        quantity = int(data['quantity'])
        cost_price = float(data['cost_price'])
        
        if quantity <= 0 or cost_price <= 0:
            return jsonify({'error': 'Quantity and cost price must be positive'}), 400
        
        # Find or create item
        item = Item.query.filter_by(name=data['name']).first()
        if item:
            # Update existing item
            item.quantity_available += quantity
            item.cost_price = cost_price  # Update to latest cost price
            item.updated_at = datetime.utcnow()
        else:
            # Create new item
            item = Item(
                name=data['name'],
                quantity_available=quantity,
                cost_price=cost_price
            )
            db.session.add(item)
            db.session.flush()  # Get item ID
        
        # Record stock in transaction
        stock_in = StockIn(
            item_id=item.id,
            quantity=quantity,
            cost_price=cost_price,
            added_date=datetime.utcnow().date()
        )
        db.session.add(stock_in)
        db.session.commit()
        
        return jsonify({
            'message': 'Stock added successfully',
            'item': item.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/sales', methods=['POST'])
def add_sale():
    """Record a sale and reduce stock"""
    data = request.get_json()
    
    if not data or not all(k in data for k in ('item_id', 'quantity', 'selling_price')):
        return jsonify({'error': 'Missing required fields: item_id, quantity, selling_price'}), 400
    
    try:
        item_id = int(data['item_id'])
        quantity = int(data['quantity'])
        selling_price = float(data['selling_price'])
        
        if quantity <= 0 or selling_price <= 0:
            return jsonify({'error': 'Quantity and selling price must be positive'}), 400
        
        item = Item.query.get(item_id)
        if not item:
            return jsonify({'error': 'Item not found'}), 404
        
        if item.quantity_available < quantity:
            return jsonify({'error': f'Insufficient stock. Available: {item.quantity_available}'}), 400
        
        # Record sale with current cost price
        sale = Sale(
            item_id=item_id,
            quantity=quantity,
            selling_price=selling_price,
            cost_price=item.cost_price,
            sale_date=datetime.utcnow().date()
        )
        
        # Reduce stock
        item.quantity_available -= quantity
        item.updated_at = datetime.utcnow()
        
        db.session.add(sale)
        db.session.commit()
        
        return jsonify({
            'message': 'Sale recorded successfully',
            'sale': sale.to_dict(),
            'remaining_stock': item.quantity_available
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/waste', methods=['POST'])
def add_waste():
    """Record wasted/damaged stock"""
    data = request.get_json()
    
    if not data or not all(k in data for k in ('item_id', 'quantity')):
        return jsonify({'error': 'Missing required fields: item_id, quantity'}), 400
    
    try:
        item_id = int(data['item_id'])
        quantity = int(data['quantity'])
        
        if quantity <= 0:
            return jsonify({'error': 'Quantity must be positive'}), 400
        
        item = Item.query.get(item_id)
        if not item:
            return jsonify({'error': 'Item not found'}), 404
        
        if item.quantity_available < quantity:
            return jsonify({'error': f'Insufficient stock to record waste. Available: {item.quantity_available}'}), 400
        
        # Record waste with current cost price
        waste = Waste(
            item_id=item_id,
            quantity=quantity,
            cost_price=item.cost_price,
            waste_date=datetime.utcnow().date()
        )
        
        # Reduce stock
        item.quantity_available -= quantity
        item.updated_at = datetime.utcnow()
        
        db.session.add(waste)
        db.session.commit()
        
        return jsonify({
            'message': 'Waste recorded successfully',
            'waste': waste.to_dict(),
            'loss_value': float(waste.loss_value),
            'remaining_stock': item.quantity_available
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard_stats():
    """Get dashboard statistics for today and overall"""
    today = datetime.utcnow().date()
    
    # Today's sales
    today_sales = Sale.query.filter(Sale.sale_date == today).all()
    today_revenue = sum(s.total_revenue for s in today_sales)
    today_profit = sum(s.profit for s in today_sales)
    
    # Today's waste loss
    today_waste = Waste.query.filter(Waste.waste_date == today).all()
    today_loss = sum(w.loss_value for w in today_waste)
    
    # Stock summary
    items = Item.query.all()
    total_stock_value = sum(i.quantity_available * i.cost_price for i in items)
    low_stock_items = [i for i in items if i.quantity_available < 10]  # Threshold 10 units
    
    # Recent transactions
    recent_sales = Sale.query.order_by(Sale.sale_date.desc(), Sale.created_at.desc()).limit(5).all()
    recent_waste = Waste.query.order_by(Waste.waste_date.desc(), Waste.created_at.desc()).limit(5).all()
    
    return jsonify({
        'today': {
            'revenue': float(today_revenue),
            'profit': float(today_profit),
            'loss': float(today_loss),
            'net': float(today_profit - today_loss)
        },
        'inventory': {
            'total_items': len(items),
            'total_stock_value': float(total_stock_value),
            'low_stock_count': len(low_stock_items),
            'low_stock_items': [{'name': i.name, 'quantity': i.quantity_available} for i in low_stock_items]
        },
        'recent_sales': [s.to_dict() for s in recent_sales],
        'recent_waste': [w.to_dict() for w in recent_waste],
        'all_items': [item.to_dict() for item in items]
    })

@app.route('/api/daily-report', methods=['GET'])
def get_daily_report():
    """Get report for a specific date"""
    date_str = request.args.get('date', datetime.utcnow().date().isoformat())
    
    try:
        report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    
    # Sales for the day
    sales = Sale.query.filter(Sale.sale_date == report_date).all()
    total_revenue = sum(s.total_revenue for s in sales)
    total_profit = sum(s.profit for s in sales)
    
    # Waste for the day
    waste = Waste.query.filter(Waste.waste_date == report_date).all()
    total_loss = sum(w.loss_value for w in waste)
    
    # Stock added on that day
    stock_added = StockIn.query.filter(StockIn.added_date == report_date).all()
    
    return jsonify({
        'date': report_date.isoformat(),
        'sales': {
            'transactions': [s.to_dict() for s in sales],
            'total_revenue': float(total_revenue),
            'total_profit': float(total_profit)
        },
        'waste': {
            'transactions': [w.to_dict() for w in waste],
            'total_loss': float(total_loss)
        },
        'stock_added': [s.to_dict() for s in stock_added],
        'summary': {
            'net_result': float(total_profit - total_loss),
            'total_transactions': len(sales) + len(waste)
        }
    })

@app.route('/api/monthly-report', methods=['GET'])
def get_monthly_report():
    """Get report for a specific month and current stock summary"""
    year = request.args.get('year', datetime.utcnow().year, type=int)
    month = request.args.get('month', datetime.utcnow().month, type=int)
    
    # Validate month
    if month < 1 or month > 12:
        return jsonify({'error': 'Month must be between 1 and 12'}), 400
    
    # Date range for the month
    start_date = datetime(year, month, 1).date()
    if month == 12:
        end_date = datetime(year + 1, 1, 1).date()
    else:
        end_date = datetime(year, month + 1, 1).date()
    
    # Monthly sales
    sales = Sale.query.filter(Sale.sale_date >= start_date, Sale.sale_date < end_date).all()
    total_revenue = sum(s.total_revenue for s in sales)
    total_profit = sum(s.profit for s in sales)
    
    # Monthly waste
    waste = Waste.query.filter(Waste.waste_date >= start_date, Waste.waste_date < end_date).all()
    total_loss = sum(w.loss_value for w in waste)
    
    # Sales by item
    sales_by_item = {}
    for sale in sales:
        item_name = sale.item.name
        if item_name not in sales_by_item:
            sales_by_item[item_name] = {
                'quantity_sold': 0,
                'revenue': 0,
                'profit': 0
            }
        sales_by_item[item_name]['quantity_sold'] += sale.quantity
        sales_by_item[item_name]['revenue'] += float(sale.total_revenue)
        sales_by_item[item_name]['profit'] += float(sale.profit)
    
    # Waste by item
    waste_by_item = {}
    for w in waste:
        item_name = w.item.name
        if item_name not in waste_by_item:
            waste_by_item[item_name] = {
                'quantity_wasted': 0,
                'loss_value': 0
            }
        waste_by_item[item_name]['quantity_wasted'] += w.quantity
        waste_by_item[item_name]['loss_value'] += float(w.loss_value)
    
    # Current stock summary (remaining stock per item)
    items = Item.query.all()
    stock_summary = [{
        'name': item.name,
        'quantity_available': item.quantity_available,
        'cost_price': float(item.cost_price),
        'stock_value': float(item.quantity_available * item.cost_price)
    } for item in items]
    
    return jsonify({
        'year': year,
        'month': month,
        'period': f"{start_date} to {end_date}",
        'summary': {
            'total_revenue': float(total_revenue),
            'total_profit': float(total_profit),
            'total_loss': float(total_loss),
            'net_profit': float(total_profit - total_loss)
        },
        'sales_by_item': sales_by_item,
        'waste_by_item': waste_by_item,
        'stock_summary': stock_summary,
        'total_stock_value': float(sum(item.quantity_available * item.cost_price for item in items))
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true')