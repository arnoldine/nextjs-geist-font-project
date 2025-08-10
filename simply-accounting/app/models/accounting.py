"""
Accounting models for financial management.
"""

from sqlalchemy import Column, String, Text, Boolean, ForeignKey, Numeric, Integer, DateTime, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from app.models.base import BaseModel, TenantMixin


class AccountType(PyEnum):
    """Enumeration for account types."""
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSE = "expense"


class AccountSubType(PyEnum):
    """Enumeration for account subtypes."""
    # Assets
    CURRENT_ASSET = "current_asset"
    FIXED_ASSET = "fixed_asset"
    INVENTORY = "inventory"
    ACCOUNTS_RECEIVABLE = "accounts_receivable"
    CASH = "cash"
    BANK = "bank"
    
    # Liabilities
    CURRENT_LIABILITY = "current_liability"
    LONG_TERM_LIABILITY = "long_term_liability"
    ACCOUNTS_PAYABLE = "accounts_payable"
    CREDIT_CARD = "credit_card"
    
    # Equity
    OWNERS_EQUITY = "owners_equity"
    RETAINED_EARNINGS = "retained_earnings"
    
    # Revenue
    SALES_REVENUE = "sales_revenue"
    SERVICE_REVENUE = "service_revenue"
    OTHER_REVENUE = "other_revenue"
    
    # Expenses
    COST_OF_GOODS_SOLD = "cost_of_goods_sold"
    OPERATING_EXPENSE = "operating_expense"
    OTHER_EXPENSE = "other_expense"


class TransactionType(PyEnum):
    """Enumeration for transaction types."""
    SALE = "sale"
    PURCHASE = "purchase"
    PAYMENT = "payment"
    RECEIPT = "receipt"
    JOURNAL_ENTRY = "journal_entry"
    ADJUSTMENT = "adjustment"
    OPENING_BALANCE = "opening_balance"
    CLOSING_ENTRY = "closing_entry"


class Account(BaseModel, TenantMixin):
    """
    Chart of accounts model for financial tracking.
    """
    __tablename__ = "accounts"
    
    # Account Information
    account_number = Column(String(20), nullable=False, index=True)
    account_name = Column(String(255), nullable=False, index=True)
    account_type = Column(Enum(AccountType), nullable=False, index=True)
    account_subtype = Column(Enum(AccountSubType), nullable=True, index=True)
    
    # Hierarchy
    parent_account_id = Column(ForeignKey("accounts.id"), nullable=True, index=True)
    
    # Account Details
    description = Column(Text, nullable=True)
    is_system_account = Column(Boolean, default=False, nullable=False)  # System-created accounts
    is_header_account = Column(Boolean, default=False, nullable=False)  # Header/summary accounts
    
    # Balance Information
    current_balance = Column(Numeric(15, 2), default=0, nullable=False)
    opening_balance = Column(Numeric(15, 2), default=0, nullable=False)
    
    # Settings
    allow_manual_entries = Column(Boolean, default=True, nullable=False)
    require_reconciliation = Column(Boolean, default=False, nullable=False)
    
    # Tax Information
    is_tax_account = Column(Boolean, default=False, nullable=False)
    tax_rate = Column(Numeric(5, 4), nullable=True)
    
    # Additional Information
    bank_account_number = Column(String(100), nullable=True)  # For bank accounts
    bank_routing_number = Column(String(50), nullable=True)
    credit_limit = Column(Numeric(15, 2), nullable=True)  # For credit accounts
    
    # Relationships
    tenant = relationship("Tenant", back_populates="accounts")
    parent_account = relationship("Account", remote_side="Account.id", back_populates="child_accounts")
    child_accounts = relationship("Account", back_populates="parent_account", cascade="all, delete-orphan")
    transaction_entries = relationship("TransactionEntry", back_populates="account")
    
    def __repr__(self):
        return f"<Account(id={self.id}, number='{self.account_number}', name='{self.account_name}')>"
    
    @property
    def full_name(self):
        """Get full account name with parent hierarchy."""
        if self.parent_account:
            return f"{self.parent_account.full_name} > {self.account_name}"
        return self.account_name
    
    @property
    def is_debit_account(self):
        """Check if account increases with debits."""
        return self.account_type in [AccountType.ASSET, AccountType.EXPENSE]
    
    @property
    def is_credit_account(self):
        """Check if account increases with credits."""
        return self.account_type in [AccountType.LIABILITY, AccountType.EQUITY, AccountType.REVENUE]
    
    def get_balance(self, as_of_date: DateTime = None):
        """Get account balance as of a specific date."""
        if as_of_date is None:
            return self.current_balance
        
        # Calculate balance from transaction entries up to the date
        # This would need to be implemented with proper query
        return self.current_balance
    
    def update_balance(self, amount: float, is_debit: bool):
        """Update account balance based on transaction."""
        if self.is_debit_account:
            if is_debit:
                self.current_balance += amount
            else:
                self.current_balance -= amount
        else:  # Credit account
            if is_debit:
                self.current_balance -= amount
            else:
                self.current_balance += amount
    
    def get_children_recursive(self):
        """Get all descendant accounts."""
        children = []
        for child in self.child_accounts:
            if child.is_active and not child.is_deleted:
                children.append(child)
                children.extend(child.get_children_recursive())
        return children
    
    def can_be_deleted(self):
        """Check if account can be deleted."""
        if self.is_system_account:
            return False
        
        # Check if account has transactions
        if len(self.transaction_entries) > 0:
            return False
        
        # Check if account has child accounts
        if len(self.child_accounts) > 0:
            return False
        
        return True


class Transaction(BaseModel, TenantMixin):
    """
    Financial transaction model for double-entry bookkeeping.
    """
    __tablename__ = "transactions"
    
    # Transaction Information
    transaction_number = Column(String(50), unique=True, nullable=False, index=True)
    transaction_type = Column(Enum(TransactionType), nullable=False, index=True)
    transaction_date = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Reference Information
    reference_type = Column(String(50), nullable=True)  # sale, purchase_order, payment, etc.
    reference_id = Column(Integer, nullable=True)  # ID of the related record
    reference_number = Column(String(100), nullable=True, index=True)  # Human-readable reference
    
    # Transaction Details
    description = Column(Text, nullable=False)
    notes = Column(Text, nullable=True)
    
    # Status
    status = Column(String(20), default="posted", nullable=False)  # draft, posted, reversed
    is_reconciled = Column(Boolean, default=False, nullable=False)
    
    # Amounts
    total_debit = Column(Numeric(15, 2), default=0, nullable=False)
    total_credit = Column(Numeric(15, 2), default=0, nullable=False)
    
    # Audit Information
    posted_by_user_id = Column(ForeignKey("users.id"), nullable=True, index=True)
    posted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Reversal Information
    reversed_by_transaction_id = Column(ForeignKey("transactions.id"), nullable=True)
    reversal_reason = Column(Text, nullable=True)
    
    # Additional Data
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    tenant = relationship("Tenant")
    posted_by = relationship("User")
    reversed_by_transaction = relationship("Transaction", remote_side="Transaction.id")
    entries = relationship("TransactionEntry", back_populates="transaction", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, number='{self.transaction_number}', type='{self.transaction_type}')>"
    
    @property
    def is_balanced(self):
        """Check if transaction is balanced (debits = credits)."""
        return abs(self.total_debit - self.total_credit) < 0.01  # Allow for rounding differences
    
    @property
    def can_be_reversed(self):
        """Check if transaction can be reversed."""
        return (self.status == "posted" and 
                not self.reversed_by_transaction_id and 
                not self.is_reconciled)
    
    def calculate_totals(self):
        """Calculate total debits and credits."""
        self.total_debit = sum(entry.debit_amount for entry in self.entries)
        self.total_credit = sum(entry.credit_amount for entry in self.entries)
    
    def add_entry(self, account_id: int, debit_amount: float = 0, credit_amount: float = 0, 
                  description: str = None):
        """Add an entry to the transaction."""
        entry = TransactionEntry(
            transaction_id=self.id,
            account_id=account_id,
            debit_amount=debit_amount,
            credit_amount=credit_amount,
            description=description or self.description
        )
        self.entries.append(entry)
        self.calculate_totals()
        return entry
    
    def post(self, user_id: int = None):
        """Post the transaction and update account balances."""
        if self.status != "draft":
            raise ValueError("Only draft transactions can be posted")
        
        if not self.is_balanced:
            raise ValueError("Transaction must be balanced before posting")
        
        # Update account balances
        for entry in self.entries:
            if entry.debit_amount > 0:
                entry.account.update_balance(float(entry.debit_amount), True)
            if entry.credit_amount > 0:
                entry.account.update_balance(float(entry.credit_amount), False)
        
        self.status = "posted"
        self.posted_by_user_id = user_id
        self.posted_at = func.now()
    
    def reverse(self, reason: str, user_id: int = None):
        """Create a reversal transaction."""
        if not self.can_be_reversed:
            raise ValueError("Transaction cannot be reversed")
        
        # Create reversal transaction
        reversal = Transaction(
            tenant_id=self.tenant_id,
            transaction_type=self.transaction_type,
            transaction_date=func.now(),
            reference_type=self.reference_type,
            reference_id=self.reference_id,
            reference_number=f"REV-{self.reference_number}",
            description=f"Reversal of {self.transaction_number}: {reason}",
            notes=f"Reversal of transaction {self.transaction_number}",
            posted_by_user_id=user_id
        )
        
        # Create reversal entries (swap debits and credits)
        for entry in self.entries:
            reversal.add_entry(
                account_id=entry.account_id,
                debit_amount=float(entry.credit_amount),
                credit_amount=float(entry.debit_amount),
                description=f"Reversal: {entry.description}"
            )
        
        # Mark original transaction as reversed
        self.reversed_by_transaction_id = reversal.id
        self.reversal_reason = reason
        
        return reversal


class TransactionEntry(BaseModel):
    """
    Individual entries within a transaction (journal entries).
    """
    __tablename__ = "transaction_entries"
    
    transaction_id = Column(ForeignKey("transactions.id"), nullable=False, index=True)
    account_id = Column(ForeignKey("accounts.id"), nullable=False, index=True)
    
    # Entry Amounts
    debit_amount = Column(Numeric(15, 2), default=0, nullable=False)
    credit_amount = Column(Numeric(15, 2), default=0, nullable=False)
    
    # Entry Details
    description = Column(Text, nullable=True)
    reference = Column(String(100), nullable=True)
    
    # Reconciliation
    is_reconciled = Column(Boolean, default=False, nullable=False)
    reconciled_at = Column(DateTime(timezone=True), nullable=True)
    reconciled_by_user_id = Column(ForeignKey("users.id"), nullable=True)
    
    # Additional Information
    memo = Column(Text, nullable=True)
    
    # Relationships
    transaction = relationship("Transaction", back_populates="entries")
    account = relationship("Account", back_populates="transaction_entries")
    reconciled_by = relationship("User")
    
    def __repr__(self):
        return f"<TransactionEntry(id={self.id}, account_id={self.account_id}, debit={self.debit_amount}, credit={self.credit_amount})>"
    
    @property
    def amount(self):
        """Get the non-zero amount (debit or credit)."""
        return self.debit_amount if self.debit_amount > 0 else self.credit_amount
    
    @property
    def is_debit(self):
        """Check if entry is a debit."""
        return self.debit_amount > 0
    
    @property
    def is_credit(self):
        """Check if entry is a credit."""
        return self.credit_amount > 0
    
    def reconcile(self, user_id: int = None):
        """Mark entry as reconciled."""
        self.is_reconciled = True
        self.reconciled_at = func.now()
        self.reconciled_by_user_id = user_id
    
    def unreconcile(self):
        """Mark entry as unreconciled."""
        self.is_reconciled = False
        self.reconciled_at = None
        self.reconciled_by_user_id = None


class Invoice(BaseModel, TenantMixin):
    """
    Invoice model for accounts receivable.
    """
    __tablename__ = "invoices"
    
    # Invoice Information
    invoice_number = Column(String(50), unique=True, nullable=False, index=True)
    customer_id = Column(ForeignKey("customers.id"), nullable=False, index=True)
    
    # Invoice Details
    invoice_date = Column(DateTime(timezone=True), nullable=False, index=True)
    due_date = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Status
    status = Column(String(20), default="draft", nullable=False)  # draft, sent, paid, overdue, cancelled
    
    # Amounts
    subtotal = Column(Numeric(10, 2), default=0, nullable=False)
    tax_amount = Column(Numeric(10, 2), default=0, nullable=False)
    discount_amount = Column(Numeric(10, 2), default=0, nullable=False)
    total_amount = Column(Numeric(10, 2), default=0, nullable=False)
    paid_amount = Column(Numeric(10, 2), default=0, nullable=False)
    balance_due = Column(Numeric(10, 2), default=0, nullable=False)
    
    # Payment Terms
    payment_terms = Column(String(100), nullable=True)
    
    # Additional Information
    notes = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)
    
    # Relationships
    tenant = relationship("Tenant")
    customer = relationship("Customer")
    invoice_items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Invoice(id={self.id}, number='{self.invoice_number}', total={self.total_amount}, status='{self.status}')>"
    
    @property
    def is_paid(self):
        """Check if invoice is fully paid."""
        return self.balance_due <= 0
    
    @property
    def is_overdue(self):
        """Check if invoice is overdue."""
        from datetime import datetime
        return (self.status not in ["paid", "cancelled"] and 
                self.due_date < datetime.utcnow())
    
    @property
    def days_overdue(self):
        """Get number of days overdue."""
        if not self.is_overdue:
            return 0
        
        from datetime import datetime
        return (datetime.utcnow() - self.due_date).days


class InvoiceItem(BaseModel):
    """
    Individual items within an invoice.
    """
    __tablename__ = "invoice_items"
    
    invoice_id = Column(ForeignKey("invoices.id"), nullable=False, index=True)
    product_id = Column(ForeignKey("products.id"), nullable=True, index=True)
    
    # Item Details
    description = Column(Text, nullable=False)
    quantity = Column(Numeric(10, 3), default=1, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    line_total = Column(Numeric(10, 2), nullable=False)
    
    # Tax Information
    tax_rate = Column(Numeric(5, 4), nullable=True)
    tax_amount = Column(Numeric(10, 2), default=0, nullable=False)
    
    # Relationships
    invoice = relationship("Invoice", back_populates="invoice_items")
    product = relationship("Product")
    
    def __repr__(self):
        return f"<InvoiceItem(id={self.id}, description='{self.description}', total={self.line_total})>"
    
    def calculate_line_total(self):
        """Calculate line total including tax."""
        base_amount = float(self.quantity) * float(self.unit_price)
        
        if self.tax_rate:
            self.tax_amount = base_amount * float(self.tax_rate)
            self.line_total = base_amount + float(self.tax_amount)
        else:
            self.tax_amount = 0
            self.line_total = base_amount
