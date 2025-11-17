"""add_vaccines_table

Revision ID: c765baa94781
Revises: cda56a112bee
Create Date: 2025-11-09 17:02:11.288122

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c765baa94781'
down_revision = 'cda56a112bee'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Criar tabela vaccines
    op.create_table(
        'vaccines',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('scheduled_date', sa.Date(), nullable=False),
        sa.Column('veterinarian', sa.String(), nullable=True),
        sa.Column('pet_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['pet_id'], ['pets.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vaccines_id'), 'vaccines', ['id'], unique=False)


def downgrade() -> None:
    # Remover tabela vaccines
    op.drop_index(op.f('ix_vaccines_id'), table_name='vaccines')
    op.drop_table('vaccines')