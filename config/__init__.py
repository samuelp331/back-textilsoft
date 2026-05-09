try:
    import pymysql

    pymysql.install_as_MySQLdb()
except ModuleNotFoundError:
    # El proyecto usa Postgres (Supabase) por defecto.
    pass
