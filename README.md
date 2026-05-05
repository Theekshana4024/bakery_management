# Bakery Management System

A lightweight web application for tracking stock, sales, waste, profit, and loss in a bakery.

## Features

- **Stock Management**: Add daily stock with item name, quantity, and cost price
- **Sales Recording**: Record sales with quantity and selling price
- **Automatic Stock Calculation**: Remaining stock = total stock - sold stock - wasted stock
- **Profit Calculation**: (selling price - cost price) × sold quantity
- **Loss Tracking**: Record wasted/damaged stock with automatic loss value calculation
- **Daily Reports**: View profit, loss, and transactions for any date
- **Monthly Reports**: View monthly profit, loss, and remaining stock per item
- **Dashboard**: Real-time overview of today's performance and inventory status

## Technology Stack

- **Backend**: Python Flask
- **Database**: PostgreSQL
- **Frontend**: HTML5, Bootstrap 5, JavaScript (Fetch API)
- **ORM**: SQLAlchemy

## Installation & Setup

### Option 1: Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd bakery_management