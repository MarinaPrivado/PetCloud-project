"""create_concurso_table

Revision ID: add_concurso_table
Revises: c765baa94781
Create Date: 2025-12-07 08:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'add_concurso_table'
down_revision = 'c765baa94781'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'concursos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pet_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('imagem_url', sa.String(length=500), nullable=False),
        sa.Column('descricao', sa.Text(), nullable=True),
        sa.Column('votos', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('data_envio', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['pet_id'], ['pets.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_concursos_id'), 'concursos', ['id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_concursos_id'), table_name='concursos')
    op.drop_table('concursos')
