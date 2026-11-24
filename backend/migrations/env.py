from logging.config import fileConfig

from alembic import context

from backend.accounts import models as accounts_models  # noqa: F401
from backend.characters import models as characters_models  # noqa: F401
from backend.db import Base, engine
from backend.moderation import models as moderation_models  # noqa: F401
from backend.servers import models as servers_models  # noqa: F401
from backend.stories import models as stories_models  # noqa: F401

if context.config.config_file_name is not None:
    fileConfig(context.config.config_file_name)

with engine.connect() as connection:
    context.configure(connection=connection, target_metadata=Base.metadata)
    with context.begin_transaction():
        context.run_migrations()
