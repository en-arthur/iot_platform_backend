"""initial schema

Revision ID: 001
Revises: 
Create Date: 2026-03-12

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('apps',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('owner_id', UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('is_active', sa.Boolean(), default=True),
    )
    op.create_index('idx_apps_project_id', 'apps', ['project_id'])
    op.create_index('idx_apps_owner_id', 'apps', ['owner_id'])

    op.create_table('users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('app_id', UUID(as_uuid=True), sa.ForeignKey('apps.id', ondelete='CASCADE'), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('is_active', sa.Boolean(), default=True),
    )
    op.create_unique_constraint('uq_app_email', 'users', ['app_id', 'email'])
    op.create_index('idx_users_app_id', 'users', ['app_id'])
    op.create_index('idx_users_email', 'users', ['email'])

    op.create_table('refresh_tokens',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token_hash', sa.String(255), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('last_used_at', sa.DateTime(timezone=True)),
    )
    op.create_index('idx_refresh_tokens_user_id', 'refresh_tokens', ['user_id'])

    op.create_table('storage',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('app_id', UUID(as_uuid=True), sa.ForeignKey('apps.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('collection', sa.String(255), nullable=False),
        sa.Column('data', JSONB, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_storage_app_user_collection', 'storage', ['app_id', 'user_id', 'collection'])
    op.create_index('idx_storage_collection', 'storage', ['collection'])

    op.create_table('files',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('app_id', UUID(as_uuid=True), sa.ForeignKey('apps.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('r2_key', sa.String(500), nullable=False),
        sa.Column('mime_type', sa.String(100)),
        sa.Column('size_bytes', sa.BigInteger()),
        sa.Column('url', sa.String(500)),
        sa.Column('metadata', JSONB),        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_files_app_user', 'files', ['app_id', 'user_id'])


def downgrade() -> None:
    op.drop_table('files')
    op.drop_table('storage')
    op.drop_table('refresh_tokens')
    op.drop_table('users')
    op.drop_table('apps')
