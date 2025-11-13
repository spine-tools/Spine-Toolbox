import sys
from sqlalchemy import create_engine, text
from spinedb_api import DatabaseMapping

url = sys.argv[1]
real_url = DatabaseMapping(url).db_url
engine = create_engine(real_url)
with engine.connect() as connection:
    entity_ids = {row.id for row in connection.execute(text("select id from entity"))}
    value_entity_ids = {row.entity_id for row in connection.execute(text("select entity_id from parameter_value"))}
    print(value_entity_ids)
    assert value_entity_ids.issubset(entity_ids)
