from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files("spinedb_api", subdir="alembic", include_py_files=True)
