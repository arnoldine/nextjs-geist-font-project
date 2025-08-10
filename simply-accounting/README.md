# Simply Accounting

A comprehensive POS and accounting system for small businesses, built with Python FastAPI and modern web technologies.

## Features

### 🏪 Point of Sale (POS)
- **Product Catalog**: Manage products with SKUs, variants, barcodes, and pricing
- **Sales Transactions**: Process sales with multiple payment methods
- **Receipt Generation**: PDF receipts with customizable templates
- **Customer Management**: Track customer information and loyalty points
- **Shift Management**: X/Z reports and cash management

### 📦 Inventory Management
- **Stock Tracking**: Real-time inventory across multiple stores
- **Low Stock Alerts**: Automated reorder notifications
- **Supplier Management**: Vendor information and purchase orders
- **Stock Transfers**: Move inventory between locations
- **Batch/Lot Tracking**: Track expiry dates and batch numbers

### 💰 Accounting (QuickBooks-like)
- **Chart of Accounts**: Flexible account structure
- **Double-Entry Bookkeeping**: Automated journal entries
- **Invoicing**: Professional invoices and credit notes
- **Expense Tracking**: Categorized expense management
- **Financial Reports**: P&L, Balance Sheet, Cash Flow
- **Tax Management**: Multi-rate tax calculations

### 🏢 Multi-Tenant & Multi-Store
- **Tenant Isolation**: Complete data separation between businesses
- **Multi-Store Support**: Manage multiple locations
- **Role-Based Access**: Granular permissions (Admin, Manager, Supervisor, Cashier, Auditor)

## Technology Stack

- **Backend**: Python 3.11+ with FastAPI
- **Database**: MySQL with SQLAlchemy ORM
- **Authentication**: JWT tokens with role-based permissions
- **API Documentation**: OpenAPI/Swagger
- **Database Migrations**: Alembic
- **PDF Generation**: ReportLab/WeasyPrint
- **Background Tasks**: Celery with Redis

## Quick Start

### Prerequisites

- Python 3.11 or higher
- MySQL 8.0 or higher
- Redis (for background tasks)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd simply-accounting
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your database and other settings
   ```

5. **Set up database**
   ```bash
   # Create database
   mysql -u root -p -e "CREATE DATABASE simply_accounting;"
   
   # Run migrations
   alembic upgrade head
   ```

6. **Start the application**
   ```bash
   python -m app.main
   # Or use uvicorn directly:
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

7. **Access the application**
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

## Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```env
# Database
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/simply_accounting

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application
APP_NAME=Simply Accounting
DEBUG=True
ENVIRONMENT=development

# Redis
REDIS_URL=redis://localhost:6379/0
```

### Database Setup

1. **Create MySQL database**
   ```sql
   CREATE DATABASE simply_accounting CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

2. **Create database user (optional)**
   ```sql
   CREATE USER 'simply_user'@'localhost' IDENTIFIED BY 'your_password';
   GRANT ALL PRIVILEGES ON simply_accounting.* TO 'simply_user'@'localhost';
   FLUSH PRIVILEGES;
   ```

3. **Run migrations**
   ```bash
   alembic upgrade head
   ```

## API Documentation

The API is fully documented with OpenAPI/Swagger. When running in development mode, you can access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/api/v1/openapi.json

### Authentication

The API uses JWT tokens for authentication. To get started:

1. **Register a new user** (POST `/api/v1/auth/register`)
2. **Login** (POST `/api/v1/auth/login`) to get access token
3. **Use the token** in the Authorization header: `Bearer <your-token>`

### Key Endpoints

- **Authentication**: `/api/v1/auth/`
- **Users**: `/api/v1/users/`
- **Tenants**: `/api/v1/tenants/`
- **Stores**: `/api/v1/stores/`
- **Products**: `/api/v1/products/`
- **Inventory**: `/api/v1/inventory/`
- **Customers**: `/api/v1/customers/`
- **Suppliers**: `/api/v1/suppliers/`
- **Sales**: `/api/v1/sales/`
- **Purchases**: `/api/v1/purchases/`
- **Accounting**: `/api/v1/accounting/`
- **Reports**: `/api/v1/reports/`

## Development

### Project Structure

```
simply-accounting/
├── app/
│   ├── api/v1/endpoints/     # API endpoints
│   ├── core/                 # Core functionality (config, database, security)
│   ├── models/               # SQLAlchemy models
│   ├── schemas/              # Pydantic schemas
│   ├── services/             # Business logic
│   └── main.py              # FastAPI application
├── alembic/                 # Database migrations
├── tests/                   # Test files
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
└── README.md               # This file
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Code Quality

```bash
# Format code
black app/

# Sort imports
isort app/

# Lint code
flake8 app/
```

## User Roles & Permissions

### Admin
- Full system access
- User management
- System configuration
- All business operations

### Manager
- Store management
- Product and inventory management
- Sales and customer management
- Financial reports
- User management (limited)

### Supervisor
- Product management (limited)
- Sales processing
- Customer management
- Basic reports

### Cashier
- Sales processing
- Basic product lookup
- Customer information (read/update)

### Auditor
- Read-only access to all data
- Full reporting access
- No modification permissions

## Business Workflows

### Sales Process
1. Create sale transaction
2. Add products to cart
3. Apply discounts/taxes
4. Process payment(s)
5. Generate receipt
6. Update inventory
7. Create accounting entries

### Purchase Process
1. Create purchase order
2. Send to supplier
3. Receive goods
4. Update inventory
5. Create accounting entries
6. Process supplier payment

### Inventory Management
1. Stock movements tracked automatically
2. Low stock alerts generated
3. Reorder points managed
4. Stock transfers between stores
5. Periodic stock adjustments

## Deployment

### Production Setup

1. **Set environment to production**
   ```env
   ENVIRONMENT=production
   DEBUG=False
   ```

2. **Use production database**
   ```env
   DATABASE_URL=mysql+pymysql://user:pass@prod-server:3306/simply_accounting
   ```

3. **Configure reverse proxy** (nginx example)
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

4. **Use process manager** (systemd example)
   ```ini
   [Unit]
   Description=Simply Accounting API
   After=network.target
   
   [Service]
   User=www-data
   Group=www-data
   WorkingDirectory=/path/to/simply-accounting
   ExecStart=/path/to/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   ```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Check the API documentation at `/docs`
- Review the code examples in the `examples/` directory

## Roadmap

- [ ] Web frontend (React/Next.js)
- [ ] Mobile app (React Native)
- [ ] Advanced reporting and analytics
- [ ] Integration with payment processors
- [ ] Multi-currency support
- [ ] Advanced inventory features (kitting, assemblies)
- [ ] CRM features
- [ ] E-commerce integration
- [ ] API rate limiting
- [ ] Audit logging
- [ ] Data export/import tools
