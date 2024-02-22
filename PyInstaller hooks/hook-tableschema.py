from PyInstaller.utils.hooks import collect_data_files

package = "tableschema"

datas = collect_data_files(package)
datas += collect_data_files(package, subdir="profiles")
