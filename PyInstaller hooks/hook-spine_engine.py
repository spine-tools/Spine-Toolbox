from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files(
    "spine_engine", subdir="execution_managers", includes=("spine_repl.*",), include_py_files=True
)
