## Docker Installation  
1. Edit `docker-compose.yml` if you change to change defaults such as ports or credentials
2. Build the Docker image: `docker build -t threatkb .`
3. Execute docker-compose: `docker-compose up`
4. Open your browser to htp://127.0.0.1:5000/#!/login

**Example output:**
```
$ docker-compose up
Starting threatkb_db_1 ... done
Starting threatkb_redis_1          ... done
Starting threatkb_threatkb_agent_1 ... done
Starting threatkb_threatkb_1       ... done
Attaching to threatkb_db_1, threatkb_redis_1, threatkb_threatkb_1, threatkb_threatkb_agent_1
...snip...
threatkb_1        | WSGI app 0 (mountpoint='') ready in 2 seconds on interpreter 0x55ed5c094c50 pid: 94 (default app)
threatkb_1        | *** uWSGI is running in multiple interpreter mode ***
threatkb_1        | spawned uWSGI master process (pid: 94)
threatkb_1        | spawned uWSGI worker 1 (pid: 98, cores: 1)
threatkb_1        | spawned uWSGI worker 2 (pid: 99, cores: 1)
threatkb_1        | spawned uWSGI worker 3 (pid: 100, cores: 1)
threatkb_1        | spawned uWSGI worker 4 (pid: 102, cores: 1)
threatkb_1        | spawned uWSGI worker 5 (pid: 104, cores: 1)
threatkb_1        | Python auto-reloader enabled
threatkb_1        | spawned uWSGI worker 6 (pid: 105, cores: 1)
threatkb_1        | spawned uWSGI worker 7 (pid: 108, cores: 1)
threatkb_1        | spawned uWSGI worker 8 (pid: 110, cores: 1)
threatkb_1        | spawned uWSGI worker 9 (pid: 112, cores: 1)
threatkb_1        | spawned uWSGI worker 10 (pid: 115, cores: 1)
threatkb_1        | spawned uWSGI http 1 (pid: 117)
```

### Troubleshooting

Initial DB migration may fail in mysql has not finished initialization on first time launch... 

Example:
```
threatkb_1        |   File "/usr/local/lib/python2.7/dist-packages/flask_script/__init__.py", line 383, in handle
threatkb_1        |     res = handle(*args, **config)
threatkb_1        |   File "/usr/local/lib/python2.7/dist-packages/flask_script/commands.py", line 216, in __call__
threatkb_1        |     return self.run(*args, **kwargs)
threatkb_1        |   File "/usr/local/lib/python2.7/dist-packages/flask_migrate/__init__.py", line 259, in upgrade
threatkb_1        |     command.upgrade(config, revision, sql=sql, tag=tag)
threatkb_1        |   File "/usr/local/lib/python2.7/dist-packages/alembic/command.py", line 254, in upgrade
threatkb_1        |     script.run_env()
threatkb_1        |   File "/usr/local/lib/python2.7/dist-packages/alembic/script/base.py", line 425, in run_env
threatkb_1        |     util.load_python_file(self.dir, 'env.py')
threatkb_1        |   File "/usr/local/lib/python2.7/dist-packages/alembic/util/pyfiles.py", line 93, in load_python_file
threatkb_1        |     module = load_module_py(module_id, path)
threatkb_1        |   File "/usr/local/lib/python2.7/dist-packages/alembic/util/compat.py", line 75, in load_module_py
threatkb_1        |     mod = imp.load_source(module_id, path, fp)
threatkb_1        |   File "migrations/env.py", line 88, in <module>
threatkb_1        |     run_migrations_online()
threatkb_1        |   File "migrations/env.py", line 72, in run_migrations_online
threatkb_1        |     connection = engine.connect()
threatkb_1        |   File "/usr/local/lib/python2.7/dist-packages/sqlalchemy/engine/base.py", line 1649, in connect
threatkb_1        |     return self._connection_cls(self, **kwargs)
threatkb_1        |   File "/usr/local/lib/python2.7/dist-packages/sqlalchemy/engine/base.py", line 59, in __init__
threatkb_1        |     self.__connection = connection or engine.raw_connection()
threatkb_1        |   File "/usr/local/lib/python2.7/dist-packages/sqlalchemy/engine/base.py", line 1707, in raw_connection
threatkb_1        |     return self.pool.unique_connection()
threatkb_1        |   File "/usr/local/lib/python2.7/dist-packages/sqlalchemy/pool.py", line 220, in unique_connection
threatkb_1        |     return _ConnectionFairy(self).checkout()
threatkb_1        |   File "/usr/local/lib/python2.7/dist-packages/sqlalchemy/pool.py", line 425, in __init__
threatkb_1        |     rec = self._connection_record = pool._do_get()
threatkb_1        |   File "/usr/local/lib/python2.7/dist-packages/sqlalchemy/pool.py", line 855, in _do_get
threatkb_1        |     return self._create_connection()
threatkb_1        |   File "/usr/local/lib/python2.7/dist-packages/sqlalchemy/pool.py", line 225, in _create_connection
threatkb_1        |     return _ConnectionRecord(self)
threatkb_1        |   File "/usr/local/lib/python2.7/dist-packages/sqlalchemy/pool.py", line 318, in __init__
threatkb_1        |     self.connection = self.__connect()
threatkb_1        |   File "/usr/local/lib/python2.7/dist-packages/sqlalchemy/pool.py", line 368, in __connect
threatkb_1        |     connection = self.__pool._creator()
threatkb_1        |   File "/usr/local/lib/python2.7/dist-packages/sqlalchemy/engine/strategies.py", line 80, in connect
threatkb_1        |     return dialect.connect(*cargs, **cparams)
threatkb_1        |   File "/usr/local/lib/python2.7/dist-packages/sqlalchemy/engine/default.py", line 279, in connect
threatkb_1        |     return self.dbapi.connect(*cargs, **cparams)
threatkb_1        |   File "/usr/local/lib/python2.7/dist-packages/MySQLdb/__init__.py", line 81, in Connect
threatkb_1        |     return Connection(*args, **kwargs)
threatkb_1        |   File "/usr/local/lib/python2.7/dist-packages/MySQLdb/connections.py", line 193, in __init__
threatkb_1        |     super(Connection, self).__init__(*args, **kwargs2)
threatkb_1        | sqlalchemy.exc.OperationalError: (OperationalError) (2003, "Can't connect to MySQL server on 'db' (111)") None None
...snip...
db_1              | MySQL init process done. Ready for start up.
```

Just `CTRL+C` and run `docker-compose up` again.
