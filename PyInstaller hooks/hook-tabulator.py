from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files("tabulator")
datas += collect_data_files("tabulator", subdir="loaders", include_py_files=True)
datas += collect_data_files("tabulator", subdir="parsers", include_py_files=True)
