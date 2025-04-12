from pathlib import Path
import yaml

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from dotenv import dotenv_values


env = dotenv_values()

__location__ = Path(__file__).resolve().parent
with open(__location__ / 'config/config.yaml') as file:
    db_config = yaml.safe_load(file)['database']

user = env['POSTGRES_USER']
password = env['POSTGRES_PASSWORD']
host = db_config['host']
port = db_config['port']
database = db_config['database']

_engine = create_async_engine(
    f'postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}',
    echo=True
)

SessionFactory = async_sessionmaker(
    bind=_engine, expire_on_commit=False
)

def get_session():
    return SessionFactory()
