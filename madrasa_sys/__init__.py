"""Project package — enable PyMySQL as MySQLdb for PythonAnywhere / Windows lab."""

try:
    import pymysql

    pymysql.install_as_MySQLdb()
except ImportError:  # pragma: no cover - optional until pip install
    pass
