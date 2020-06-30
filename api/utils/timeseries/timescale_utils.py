import os
from datetime import datetime, timedelta
import pytz
import asyncpg
from typing import List
from utils.schemas.dataflow_schemas import TickSchema
from utils.schemas.request_schemas import DataRequestSchema


DEFAULT_DBNAME = 'livewater'


async def pool_context(app):
    app['TIMESCALE_POOL'] = pool = await get_pool(DEFAULT_DBNAME)
    yield
    await pool.close()


def get_url():
    url = os.environ.get('TIMESCALEDB_URL')
    assert url, "Time-series DB URL must be specified in TIMESCALEDB_URL environment variable"
    return url


async def init_connection(dbname):
    return await asyncpg.connect(f"{get_url()}{dbname}")


async def reset_db(dbname):
    conn = await asyncpg.connect(f"{get_url()}template1")
    await conn.execute(f"DROP DATABASE IF EXISTS {dbname};")
    await conn.execute(f"CREATE DATABASE {dbname};")
    await conn.close()
    conn = await init_connection(dbname)
    await init_ticks_table(conn)


async def init_ticks_table(conn):
    TICKS_TABLE_SCHEMA = """ticks (
        timestamp TIMESTAMPTZ NOT NULL,
        source_id VARCHAR(70), -- third-party tick ID
        session_id INTEGER, -- session id associated with the tick
        data_type INTEGER, -- type of data (primary_ticks = 1, secondary_ticks = 2 etc)
        label VARCHAR(50), -- asset name or other string identifier if N/A
        price DOUBLE PRECISION,
        volume DOUBLE PRECISION,
        funds DOUBLE PRECISION
    )"""
    await conn.execute(f"CREATE TABLE IF NOT EXISTS {TICKS_TABLE_SCHEMA};")
    try:
        await conn.execute("SELECT create_hypertable('ticks', 'timestamp');")
        print('created hypertable')
    except asyncpg.exceptions.UnknownPostgresError:
        pass

    await conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS unique_ticks \
        ON ticks(timestamp, source_id, session_id, data_type, label, funds);")


async def init_db(dbname=DEFAULT_DBNAME):
    conn = await asyncpg.connect(f"{get_url()}template1")
    try:
        await conn.execute(f"CREATE DATABASE {dbname};")
    except asyncpg.exceptions.DuplicateDatabaseError:
        pass
    await conn.close()
    conn = await init_connection(dbname)
    await init_ticks_table(conn)


async def get_pool(dbname=DEFAULT_DBNAME) -> asyncpg.pool.Pool:
    await init_db(dbname)
    try:
        return await asyncpg.create_pool(
            f"{get_url()}{dbname}",
            max_inactive_connection_lifetime=10
        )
    except Exception as e:
        print('Failed to start up connection pool')
        raise e


async def get_terminal_data(session_id, request_params: DataRequestSchema, request):
    pool = request.app['TIMESCALE_POOL']
    if not request_params.to_datetime:
        request_params.to_datetime = datetime.now()
    period = timedelta(minutes=request_params.period)
    async with pool.acquire() as conn:
        query = """
        SELECT
            time_bucket($1, timestamp) AS time,
            first(price, timestamp) as open,
            max(price) as high,
            min(price) as low,
            last(price, timestamp) as close,
            sum(volume) as volume
        FROM ticks
        WHERE session_id = $2
        and label = $3
        and data_type = $4
        and timestamp BETWEEN $5 and $6
        GROUP BY time
        ORDER BY time ASC;
        """
        params = (
            period,
            session_id,
            request_params.label,
            request_params.data_type,
            request_params.from_datetime,
            request_params.to_datetime
        )
        # params = (period, session_id)
        return list(await conn.fetch(query, *params))


async def write_ticks(session_id, data_type, label, ticks: List[TickSchema], pool):
    prepared_ticks = []
    for tick in ticks:
        timestamp = tick.timestamp.replace(tzinfo=pytz.UTC)
        values = (
            timestamp,
            session_id,
            data_type,
            label,
            tick.price,
            tick.volume,
            tick.funds
        )
        prepared_ticks.append(values)

    async with pool.acquire() as conn:
        try:
            await conn.executemany('''
                INSERT INTO ticks(timestamp, session_id, data_type, label, price, volume, funds)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (timestamp, source_id, session_id, data_type, label, funds) DO UPDATE
                SET price=EXCLUDED.price,
                    volume=EXCLUDED.volume;
            ''', prepared_ticks)
        except asyncpg.exceptions.UniqueViolationError:
            pass
