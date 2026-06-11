FROM python:3.13-slim

WORKDIR /app

COPY docker/libs/sql_limit_enforcer/ ./libs/sql_limit_enforcer/
RUN pip install --no-cache-dir ./libs/sql_limit_enforcer/ && rm -rf /app/libs

COPY docker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY docker/src/ ./src/

ENTRYPOINT ["python", "-m", "src.http_static_server"]
