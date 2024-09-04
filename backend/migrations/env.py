from logging.config import fileConfig

from app import models
from app.database import SYNC_DB_API, get_connection_url

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# this will overwrite the ini-file sqlalchemy.url path
connection_url = get_connection_url(db_api=SYNC_DB_API)
connection_string = connection_url.render_as_string(hide_password=False)
# Don't use '%' in password: https://stackoverflow.com/a/40837579/25741288
config.set_main_option("sqlalchemy.url", connection_string)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
# See: https://pytest-alembic.readthedocs.io/en/latest/setup.html#caplog-issues for
# more info on fileConfig for `pytest-alembic`.
if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=True)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = models.Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    For `pytest-alembic`, the connection is provided by `pytest-alembic` at runtime.
    Thus, we create a check to see if `connectable` already exists. This allows the same
    `env.py` to be used for both `pytest-alembic` and regular migrations.

    """
    connectable = context.config.attributes.get("connection", None)

    if connectable is None:
        connectable = engine_from_config(
            config.get_section(config.config_ini_section, {}),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
