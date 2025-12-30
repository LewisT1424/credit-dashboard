"""Initial migration: users, portfolios, loans, default_rates, rating_history, audit_logs

Revision ID: 001
Revises: 
Create Date: 2025-12-30 07:19:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('role', sa.Enum('admin', 'portfolio_manager', name='userrole'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    
    # Create portfolios table
    op.create_table('portfolios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_portfolios_owner_id'), 'portfolios', ['owner_id'], unique=False)
    
    # Create default_rates table
    op.create_table('default_rates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('credit_rating', sa.String(length=10), nullable=False),
        sa.Column('default_probability', sa.Float(), nullable=False),
        sa.Column('recovery_rate', sa.Float(), nullable=False),
        sa.Column('risk_weight', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_default_rates_credit_rating'), 'default_rates', ['credit_rating'], unique=True)
    
    # Create loans table
    op.create_table('loans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('loan_id', sa.String(length=50), nullable=False),
        sa.Column('portfolio_id', sa.Integer(), nullable=False),
        sa.Column('borrower', sa.String(length=255), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('rate', sa.Float(), nullable=False),
        sa.Column('sector', sa.String(length=100), nullable=False),
        sa.Column('maturity_date', sa.Date(), nullable=False),
        sa.Column('credit_rating', sa.String(length=10), nullable=False),
        sa.Column('status', sa.Enum('performing', 'watch_list', 'non_performing', 'defaulted', name='loanstatus'), nullable=False),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('debt_to_equity', sa.Float(), nullable=True),
        sa.Column('interest_coverage', sa.Float(), nullable=True),
        sa.Column('leverage_ratio', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['portfolio_id'], ['portfolios.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_loans_loan_id'), 'loans', ['loan_id'], unique=True)
    op.create_index(op.f('ix_loans_portfolio_id'), 'loans', ['portfolio_id'], unique=False)
    op.create_index(op.f('ix_loans_credit_rating'), 'loans', ['credit_rating'], unique=False)
    op.create_index(op.f('ix_loans_sector'), 'loans', ['sector'], unique=False)
    op.create_index(op.f('ix_loans_country'), 'loans', ['country'], unique=False)
    op.create_index(op.f('ix_loans_status'), 'loans', ['status'], unique=False)
    
    # Create rating_history table
    op.create_table('rating_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('loan_id', sa.Integer(), nullable=False),
        sa.Column('snapshot_date', sa.Date(), nullable=False),
        sa.Column('credit_rating', sa.String(length=10), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['loan_id'], ['loans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_rating_history_loan_id'), 'rating_history', ['loan_id'], unique=False)
    # Unique constraint for loan_id + snapshot_date
    op.create_index('ix_rating_history_unique', 'rating_history', ['loan_id', 'snapshot_date'], unique=True)
    
    # Create audit_logs table
    op.create_table('audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.Enum('CREATE', 'UPDATE', 'DELETE', 'LOGIN', name='auditaction'), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=True),
        sa.Column('changes', postgresql.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_entity'), 'audit_logs', ['entity_type', 'entity_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_created_at'), 'audit_logs', ['created_at'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('audit_logs')
    op.drop_table('rating_history')
    op.drop_table('loans')
    op.drop_table('default_rates')
    op.drop_table('portfolios')
    op.drop_table('users')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS userrole')
    op.execute('DROP TYPE IF EXISTS loanstatus')
    op.execute('DROP TYPE IF EXISTS auditaction')
