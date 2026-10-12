# Native ArangoDB Export Result

Target: `quakewatch_test` only. The guarded pre-export probe confirmed test mode, endpoint `http://arangodb:8529`, and database list `_system,quakewatch,quakewatch_test`.

Command executed in the ArangoDB service container, using its environment-provided root password without printing it:

```sh
docker compose exec -T arangodb sh -c 'test ! -e /tmp/qw-review2-20261011-native && arangodump --server.username root --server.password "$ARANGO_ROOT_PASSWORD" --server.database quakewatch_test --output-directory /tmp/qw-review2-20261011-native'
```

Actual dump result (ArangoDB 3.12.5): connected to `tcp://127.0.0.1:8529`, database `quakewatch_test`; processed 31 collections from 1 database; retrieved 955.4 KB; wrote 32.8 KB compressed. Dump command exit code: 0.

The dump was copied to [native_arangodump_2026-10-11](native_arangodump_2026-10-11). Host verification found 65 non-empty files totaling 159,002 bytes. `dump.json` parsed successfully and all 31 `.data.json.gz` payloads decompressed successfully. The test database was subsequently dropped via the guarded project helper; the dump was retained as evidence. No restore validation was run.

Harness notes: the first host-side wrapper had a Python quoting syntax error before executing any command. The corrected dump succeeded. A subsequent `find -printf` listing failed because the container uses BusyBox; the listing was repeated with supported `find -exec ls`, then copy and integrity checks passed. See [native_arangodump_command.log](native_arangodump_command.log) for command and output details.
