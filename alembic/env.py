from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from app import core
from app.db.base_class import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support

target_metadata = Base.metadata


def include_object(obj, name, type_, reflected, compare_to):
    """Ignora objetos que existem no banco mas não nos models.

    Evita que o autogenerate tente apagar tabelas de extensões
    (PostGIS: spatial_ref_sys; Tiger geocoder: edges, faces, county...;
    topology: topology, layer).
    """
    if type_ == "table" and reflected and name not in target_metadata.tables:
        return False
    if (
        type_ == "index"
        and reflected
        and obj.table.name not in target_metadata.tables
    ):
        return False
    return True


def run_migrations_offline():
    url = core.settings.get_db_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    url = core.settings.get_db_url()

    config_session = config.get_section(config.config_ini_section)
    config_session["sqlalchemy.url"] = url
    connectable = engine_from_config(
        config_session,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        isolation_level="AUTOCOMMIT",
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
