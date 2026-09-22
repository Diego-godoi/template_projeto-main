"""Seed default roles

Revision ID: 59d84a75a862
Revises: 65b0751bba60
Create Date: 2026-09-22 14:01:33.729768

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '59d84a75a862'
down_revision = '65b0751bba60'
branch_labels = None
depends_on = None


def upgrade() -> None:
    from datetime import datetime, timezone
    import uuid
    
    op.bulk_insert(
        sa.table('roles',
            sa.column('id', sa.UUID(as_uuid=True)),
            sa.column('name', sa.String(45)),
            sa.column('description', sa.String(250)),
            sa.column('is_system', sa.Boolean()),
            sa.column('created_at', sa.DateTime(timezone=True)),
            sa.column('updated_at', sa.DateTime(timezone=True))
        ),
        [
            {'id': uuid.uuid4(), 'name': 'User', 'description': 'Usuário comum do sistema.', 'is_system': True, 'created_at': datetime.now(timezone.utc), 'updated_at': datetime.now(timezone.utc)},
            {'id': uuid.uuid4(), 'name': 'Manager', 'description': 'Gestor do sistema.', 'is_system': True, 'created_at': datetime.now(timezone.utc), 'updated_at': datetime.now(timezone.utc)},
            {'id': uuid.uuid4(), 'name': 'Admin', 'description': 'Administrador do sistema.', 'is_system': True, 'created_at': datetime.now(timezone.utc), 'updated_at': datetime.now(timezone.utc)}
        ]
    )


def downgrade() -> None:
    op.execute("DELETE FROM roles WHERE name IN ('User', 'Manager', 'Admin')")
