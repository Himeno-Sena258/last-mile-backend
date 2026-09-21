"""Add vehicle liveness and reliable dispatch commands."""
from alembic import op
import sqlalchemy as sa

revision = "d19f7a6c2e40"
down_revision = ("8db92c8e4110", "b8c3e1f04a2d")
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    car_columns = {column["name"] for column in inspector.get_columns("cars")}
    if "connected_at" not in car_columns:
        op.add_column("cars", sa.Column("connected_at", sa.DateTime(), nullable=True))
    if "last_seen_at" not in car_columns:
        op.add_column("cars", sa.Column("last_seen_at", sa.DateTime(), nullable=True))
    if not inspector.has_table("dispatch_commands"):
        op.create_table(
            "dispatch_commands",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("command_id", sa.String(36), nullable=False, unique=True),
            sa.Column("car_id", sa.Integer(), sa.ForeignKey("cars.id"), nullable=False),
            sa.Column("task_id", sa.Integer(), sa.ForeignKey("tasks.id"), nullable=False, unique=True),
            sa.Column("status", sa.String(20), nullable=False),
            sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("last_sent_at", sa.DateTime(), nullable=True),
            sa.Column("acknowledged_at", sa.DateTime(), nullable=True),
            sa.Column("interrupted_at", sa.DateTime(), nullable=True),
            sa.Column("failed_at", sa.DateTime(), nullable=True),
            sa.Column("failure_reason", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        )


def downgrade():
    op.drop_table("dispatch_commands")
    op.drop_column("cars", "last_seen_at")
    op.drop_column("cars", "connected_at")
