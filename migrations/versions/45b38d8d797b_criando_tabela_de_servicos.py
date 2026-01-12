"""criando tabela de servicos

Revision ID: 45b38d8d797b
Revises: d5604025f23b
Create Date: 2026-01-12 09:59:12.394899

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '45b38d8d797b'
down_revision = 'd5604025f23b'
branch_labels = None
depends_on = None

def upgrade():
    # REMOVIDO: audit_logs, resource e user (Pois já existem no banco)
    
    # 1. CRIAR AS TABELAS QUE REALMENTE FALTAM
    op.create_table('patient_profile',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('cpf', sa.String(length=14), nullable=True),
    sa.Column('birth_date', sa.Date(), nullable=True),
    sa.Column('phone', sa.String(length=20), nullable=True),
    sa.Column('medical_notes', sa.Text(), nullable=True),
    sa.Column('insurance_plan', sa.String(length=50), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name=op.f('fk_patient_profile_user_id_user')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_patient_profile')),
    sa.UniqueConstraint('cpf', name=op.f('uq_patient_profile_cpf')),
    sa.UniqueConstraint('user_id', name=op.f('uq_patient_profile_user_id'))
    )

    op.create_table('service',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('image_url', sa.String(length=255), nullable=True),
    sa.Column('duration_minutes', sa.Integer(), nullable=False),
    sa.Column('price_cents', sa.Integer(), nullable=False),
    sa.Column('category', sa.String(length=50), nullable=False),
    sa.Column('content', sa.Text(), nullable=True),
    sa.Column('benefits', sa.Text(), nullable=True),
    sa.Column('indications', sa.Text(), nullable=True),
    sa.Column('contraindications', sa.Text(), nullable=True),
    sa.Column('active', sa.Boolean(), nullable=True),
    sa.Column('resource_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['resource_id'], ['resource.id'], name=op.f('fk_service_resource_id_resource')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_service'))
    )

    with op.batch_alter_table('service', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_service_active'), ['active'], unique=False)

    op.create_table('staff_profile',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('professional_reg', sa.String(length=50), nullable=True),
    sa.Column('specialty', sa.String(length=100), nullable=True),
    sa.Column('bio', sa.Text(), nullable=True),
    sa.Column('work_hours', sa.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name=op.f('fk_staff_profile_user_id_user')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_staff_profile')),
    sa.UniqueConstraint('user_id', name=op.f('uq_staff_profile_user_id'))
    )

    op.create_table('appointment',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('service_id', sa.Integer(), nullable=False),
    sa.Column('resource_id', sa.Integer(), nullable=True),
    sa.Column('start_datetime', sa.DateTime(), nullable=False),
    sa.Column('actual_start', sa.DateTime(), nullable=True),
    sa.Column('end_datetime', sa.DateTime(), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('payment_status', sa.String(length=20), nullable=True),
    sa.Column('phone', sa.String(length=20), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['resource_id'], ['resource.id'], name=op.f('fk_appointment_resource_id_resource')),
    sa.ForeignKeyConstraint(['service_id'], ['service.id'], name=op.f('fk_appointment_service_id_service')),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name=op.f('fk_appointment_user_id_user')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_appointment'))
    )

    with op.batch_alter_table('appointment', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_appointment_start_datetime'), ['start_datetime'], unique=False)

def downgrade():
    with op.batch_alter_table('appointment', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_appointment_start_datetime'))
    op.drop_table('appointment')
    op.drop_table('staff_profile')
    with op.batch_alter_table('service', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_service_active'))
    op.drop_table('service')
    op.drop_table('patient_profile')