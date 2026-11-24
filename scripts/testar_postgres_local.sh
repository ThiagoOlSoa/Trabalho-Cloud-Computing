#!/usr/bin/env bash
# Cluster próprio, acessível apenas por socket Unix.
set -euo pipefail
pg_bin="${PG_BIN_DIR:-$(pg_config --bindir)}"
tmp_root="$(mktemp -d "${RUNNER_TEMP:-/tmp}/observatorio-ci.XXXXXX")"
stop_cluster() {
    "$pg_bin/pg_ctl" -D "$tmp_root/pgdata" stop -m fast >/dev/null 2>&1 || true
    rm -rf -- "$tmp_root"
}
trap stop_cluster EXIT
mkdir "$tmp_root/socket"
"$pg_bin/initdb" -D "$tmp_root/pgdata" --username=observatorio_ci --locale=C.UTF-8 \
    --auth-local=trust --auth-host=scram-sha-256 > "$tmp_root/init.log"
"$pg_bin/pg_ctl" -D "$tmp_root/pgdata" -l "$tmp_root/postgres.log" \
    -o "-k $tmp_root/socket -c listen_addresses= -p 5432" start

unset PGHOSTADDR PGSERVICE PGPASSWORD PGOPTIONS
export PGHOST="$tmp_root/socket" PGPORT=5432 PGUSER=observatorio_ci PGDATABASE=referencia
export PGSSLMODE=disable
"$pg_bin/createdb" "$PGDATABASE"
"$pg_bin/psql" -X -v ON_ERROR_STOP=1 -f sql/schema.sql > "$tmp_root/schema.log"

for nome in censo_2024_area1 enade_2023_area1; do
    gzip -dc "data/processed/$nome.csv.gz" > "$tmp_root/$nome.csv"
done
export DB_HOST="$PGHOST" DB_PORT="$PGPORT" DB_USER="$PGUSER" DB_NAME="$PGDATABASE"
export DB_PASSWORD=fixture-local DB_SSLMODE=disable
python -m src.load --csv "$tmp_root/censo_2024_area1.csv"
python -m src.load_enade --csv "$tmp_root/enade_2023_area1.csv"
"$pg_bin/createdb" --template "$PGDATABASE" legado
"$pg_bin/psql" -X -v ON_ERROR_STOP=1 -f sql/views.sql
PGDATABASE=legado "$pg_bin/psql" -X -v ON_ERROR_STOP=1 -f tests/fixtures/grafana_legado.sql
PGDATABASE=legado "$pg_bin/psql" -X -v ON_ERROR_STOP=1 <<'SQL'
CREATE ROLE grafana_direto LOGIN;
ALTER ROLE grafana_direto SET default_transaction_read_only TO on;
ANALYZE;
SQL
PGDATABASE=legado "$pg_bin/psql" -X -v ON_ERROR_STOP=1 -f tests/fixtures/grafana_permissoes.sql
export ETL_TEST_PG_SOCKET="$PGHOST" ETL_TEST_PSQL="$pg_bin/psql" ETL_TEST_PG_USER="$PGUSER"
export ETL_TEST_DB_NAME="$PGDATABASE" ETL_TEST_CSV_DIR="$tmp_root"
export GRAFANA_TEST_LEGACY_DB_NAME=legado GRAFANA_TEST_LEGACY_USER=grafana_direto
python -m unittest discover -s tests -v
PGDATABASE=legado PGUSER=grafana_direto python -m scripts.validar_indicadores

if [[ "${MEDIR_GRAFANA:-0}" == 1 ]]; then
    PGDATABASE=legado PGUSER=grafana_direto python -m scripts.medir_grafana_local
fi
