#############################################################################
# Copyright (C) 2017 - 2018 VTT Technical Research Centre of Finland
#
# This file is part of Spine Toolbox.
#
# Spine Toolbox is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#############################################################################

"""
Functions to import and export from excel to spine database.

:author: P. Vennström (VTT)
:date:   21.8.2018
"""

# TODO: Remove blank lines inside functions
# TODO: Add docstrings to all functions
# TODO: PEP8: Do not use bare except. Too broad exception clause

from collections import namedtuple
from itertools import groupby
import json
from openpyxl import Workbook, load_workbook
from openpyxl.utils import get_column_letter
from spinedatabase_api import SpineDBAPIError
import logging


SheetData = namedtuple("SheetData",["sheet_name","class_name","object_classes",
                                    "parameters","parameter_values","objects",
                                    "class_type"])


def import_xlsx_to_db(db, filepath):
    """reads excel file in 'filepath' and insert into database in mapping 'db'.
    Returns two list, one with succesful writes to database, one with errors
    when trying to write to database.

    Args:
        db (spinedatabase_api.DatabaseMapping): database mapping for database to write to
        filepath (str): str with filepath to excel file to read from

    Returns:
        (List, List) Returns two lists, first contains all imported data,
        second one contains error information on all failed writes
    """

    insert_log = []
    error_log = []

    obj_data, rel_data, error_log_temp = read_spine_xlsx(filepath)
    error_log = error_log + error_log_temp

    insert_log_temp, error_log_temp = export_object_classes_to_spine_db(db, obj_data)
    insert_log = insert_log + insert_log_temp
    error_log = error_log + error_log_temp

    insert_log_temp, error_log_temp = export_object_parameters_spine_db(db, obj_data)
    insert_log = insert_log + insert_log_temp
    error_log = error_log + error_log_temp

    insert_log_temp, error_log_temp = export_object_to_spine_db(db, obj_data)
    insert_log = insert_log + insert_log_temp
    error_log = error_log + error_log_temp

    insert_log_temp, error_log_temp = export_object_parameter_values(db, obj_data)
    insert_log = insert_log + insert_log_temp
    error_log = error_log + error_log_temp

    insert_log_temp, error_log_temp = export_relationship_class_to_spine_db(db, rel_data)
    insert_log = insert_log + insert_log_temp
    error_log = error_log + error_log_temp

    insert_log_temp, error_log_temp = export_relationships_parameters_to_spine_db(db, rel_data)
    insert_log = insert_log + insert_log_temp
    error_log = error_log + error_log_temp

    insert_log_temp, error_log_temp = export_relationships_to_spine_db(db, rel_data)
    insert_log = insert_log + insert_log_temp
    error_log = error_log + error_log_temp

    insert_log_temp, error_log_temp = export_relationships_parameter_value_to_spine_db(db, rel_data)
    insert_log = insert_log + insert_log_temp
    error_log = error_log + error_log_temp

    return insert_log, error_log


def get_objects_and_parameters(db):
    """Exports all object data from spine database into unstacked list of lists

    Args:
        db (spinedatabase_api.DatabaseMapping): database mapping for database

    Returns:
        (List, List) First list contains parameter data, second one json data
    """

    # get all objects
    obj = db.object_list().add_column(db.ObjectClass.name.label('class_name')).\
        filter(db.ObjectClass.id == db.Object.class_id).all()

    # get all object classes
    obj_class = db.object_class_list().all()

    # get all parameter values
    pval = db.session.query(
                            db.ObjectClass.name,
                            db.Object.name,
                            db.Parameter.name,
                            db.ParameterValue.value,
                            db.ParameterValue.json).\
                        filter(db.ParameterValue.object_id == db.Object.id,
                               db.ObjectClass.id == db.Object.class_id,
                               db.ParameterValue.parameter_id == db.Parameter.id).\
                        all()

    # get all parameter definitions
    par = db.session.query(db.ObjectClass.name, db.Parameter.name).\
        filter(db.ObjectClass.id == db.Parameter.object_class_id).all()

    # make all in same format
    par = [(p[0], None, p[1], None, None) for p in par]
    obj = [(p.class_name, p.name, None, None, None) for p in obj]
    obj_class = [(p.name, None, None, None, None) for p in obj_class]

    object_and_par = pval + par + obj + obj_class

    object_par = [v[:-1] for v in object_and_par]
    object_json = [v[:-2] + (v[4],) for v in object_and_par if v[4] is not None]

    return object_par, object_json


def get_relationships_and_parameters(db):
    """Exports all relationship data from spine database into unstacked list of lists

    Args:
        db (spinedatabase_api.DatabaseMapping): database mapping for database

    Returns:
        (List, List) First list contains parameter data, second one json data
    """

    rel_class = db.wide_relationship_class_list().all()
    rel = db.wide_relationship_list().all()
    rel_par = db.relationship_parameter_list().all()
    rel_par_value = db.relationship_parameter_value_list().all()

    rel_class_id_2_name = {rc.id: rc.name for rc in rel_class}

    out_data = [[r.relationship_class_name,
                 r.object_name_list,
                 r.parameter_name,
                 r.value, r.json] for r in rel_par_value]

    rel_with_par = set(r.object_name_list for r in rel_par_value)
    rel_without_par = [[rel_class_id_2_name[r.class_id], r.object_name_list, None, None, None]
                       for r in rel if r.object_name_list not in rel_with_par]

    rel_class_par = [[r.relationship_class_name, None, r.parameter_name, None, None]
                     for r in rel_par]

    rel_class_with_par = [r.relationship_class_name for r in rel_par]
    rel_class_without_par = [[r.name, None, None, None, None]
                             for r in rel_class if r.name not in rel_class_with_par]

    rel_data = out_data + rel_without_par + rel_class_par + rel_class_without_par

    rel_par = [v[:-1] for v in rel_data]
    rel_json = [v[:-2] + [v[4]] for v in rel_data if v[4] is not None]

    return rel_par, rel_json, rel_class


def unstack_list_of_tuples(data, headers, key_cols, value_name_col, value_col):
    """Unstacks list of lists or list of tuples and creates a list of namedtuples
    whit unstacked data (pivoted data)

    Args:
        data (List[List]): List of lists with data to unstack
        headers (List[str]): List of header names for data
        key_cols (List[Int]): List of index for column that are keys, columns to not unstack
        value_name_col (Int): index to column containing name of data to unstack
        value_col (Int): index to column containg value to value_name_col

    Returns:
        (List[namedtuple]): List of namedtuples whit fields given by headers
        and unqiue names in value_name_col column
    """

    key_names = [headers[n] for n in key_cols]

    # find unique rows for key names.
    unique_keys = []
    values = []
    keyfunc = lambda x: [x[k] for k in key_cols]

    # value names with invalid key_cols
    value_names = [x[value_name_col] for x in data if None in keyfunc(x)]

    # remove data with invalid key cols
    data = [x for x in data if None not in keyfunc(x)]
    data = sorted(data, key=keyfunc)
    for k, g in groupby(data, key=keyfunc):
        if not None in k:
            unique_keys.append(k)
        vn = {gv[value_name_col]: gv[value_col] for gv in g if gv[value_name_col] is not None}
        values.append(vn)
        value_names = value_names + list(vn.keys())

    # names of values to create pivoted values for
    value_names = list(set([v for v in value_names if v is not None]))

    # pivot/unstack data
    PivotedData = namedtuple("Data", key_names+value_names)

    data_list_out = []
    for k, value_dict in zip(unique_keys, values):
        value_list = []
        for key in value_names:
            if key in value_dict:
                value_list.append(value_dict[key])
            else:
                value_list.append(None)
        data_list_out.append(PivotedData._make(k+value_list))

    return data_list_out


def stack_list_of_tuples(data, headers, key_cols, value_cols):
    """Stacks list of lists or list of tuples and creates a list of namedtuples
    with stacked data (unpivoted data)

    Args:
        data (List[List]): List of lists with data to unstack
        headers (List[str]): List of header names for data
        key_cols (List[Int]): List of index for columns that are keys
        value_cols (List[Int]): List of index for columns containing values to stack

    Returns:
        (List[namedtuple]): List of namedtuples whit fields given by headers
        and 'parameter' and 'value' which contains stacked values
    """

    value_names = [headers[n] for n in value_cols]
    key_names = [headers[n] for n in key_cols]

    new_tuple_names = key_names + ["parameter", "value"]

    NewDataTuple = namedtuple("Data", new_tuple_names)
    # TODO: Comment needed
    # takes unstacked data and duplicates columns in key_cols and then zips
    # them with values in value_cols
    new_data_list = [list(
          map(NewDataTuple._make,
              [a+[b]+[c] for a, b, c in
                   zip([[dl[k] for k in key_cols]]*len(value_cols),
                       value_names,
                       [dl[vk] for vk in value_cols]
                       )
                   ]
              )
        )
    for dl in data]

    new_data_list = [item for sublist in new_data_list for item in sublist]

    return new_data_list


def unpack_json_parameters(data, json_index):
    out_data = []
    for data_row in data:
        json_data = json.loads(data_row[json_index].replace("\n", ""))

        if json_index == 0:
            key_cols = [list(data_row[json_index+1:])]*len(json_data)
        else:
            key_cols = [list(data_row[:json_index]) +
                        list(data_row[json_index+1:])]*len(json_data)

        out_data += [a + [b] + [c] for a, b, c in
                     zip(key_cols, range(0, len(json_data), 1), json_data)]

    return out_data


def pack_json_parameters(data, key_cols, value_col, index_col=None):

    out_data = []
    # group by keys cols
    keyfunc = lambda x: [x[k] for k in key_cols]
    data = sorted(data, key=keyfunc)
    for key, grouped in groupby(data, key=keyfunc):
        # sort if index is given.
        if index_col is not None:
            grouped = sorted(grouped, key=lambda x: x[index_col])

        # pack values into json
        values = [g[value_col] for g in grouped]
        json_val = json.dumps(values)
        out_data.append(key + [json_val])
    return out_data


def get_unstacked_relationships(db):
    """Gets all data for relationships in a unstacked list of list

    Args:
        db (spinedatabase_api.DatabaseMapping): database mapping for database

    Returns:
        (List, List): Two list of data for relationship, one with parameter values
        and the second one with json values
    """
    data, data_json, rel_class = get_relationships_and_parameters(db)

    class_2_obj_list = {rc.name: rc.object_class_name_list.split(',') for rc in rel_class}

    keyfunc = lambda x: x[0]
    data_json = sorted(data_json, key=keyfunc)
    parsed_json = []
    # json data, split by relationship class
    for k,v in groupby(data_json, key=keyfunc):
        json_vals  = []
        for row in v:
            rel_list = row[1].split(',')
            parameter = row[2]
            try:
                val = json.loads(row[3].replace("\n", ""))
                json_vals.append([rel_list+[parameter], val])
            except:
                logging.debug("error parsing json value for parameter: {} for relationship {}".format(parameter, row[1]))
        if json_vals:
            object_classes = class_2_obj_list[k]
            parsed_json.append([k, object_classes, json_vals])

    # parameter data, split by relationship class
    stacked_rels = []
    data = sorted(data, key=keyfunc)
    for k, v in groupby(data, key=keyfunc):
        values = list(v)
        rel = unstack_list_of_tuples(values, ["relationship_class", "relationship", "parameter", "value"], [0, 1], 2, 3)
        if len(rel) > 0:
            parameters = list(rel[0]._fields[2:])
        else:
            parameters = list(set([p[2] for p in values]))
        rel = [r.relationship.split(',') + list(r[2:]) for r in rel]
        object_classes = class_2_obj_list[k]
        stacked_rels.append([k, rel, object_classes, parameters])
    return stacked_rels, parsed_json


def get_unstacked_objects(db):
    """Gets all data for objects in a unstacked list of list

    Args:
        db (spinedatabase_api.DatabaseMapping): database mapping for database

    Returns:
        (List, List): Two list of data for objects, one with parameter values
        and the second one with json values
    """
    data, data_json = get_objects_and_parameters(db)

    keyfunc = lambda x: x[0]

    parsed_json = []
    data_json = sorted(data_json, key=keyfunc)
    for k, v in groupby(data_json, key=keyfunc):
        json_vals  = []
        for row in v:
            obj = row[1]
            parameter = row[2]
            try:
                val = json.loads(row[3].replace("\n", ""))
                json_vals.append([[obj,parameter], val])
            except:
                logging.debug("error parsing json value for parameter: {} for object {}".format(parameter, obj))
        if json_vals:
            parsed_json.append([k, [k], json_vals])

    stacked_obj = []
    data = sorted(data, key = keyfunc)
    for k,v in groupby(data, key = keyfunc):
        values = list(v)
        obj = unstack_list_of_tuples(values, ["object_class", "object", "parameter", "value"], [0, 1], 2, 3)
        if len(obj) > 0:
            parameters = list(obj[0]._fields[2:])
        else:
            parameters = list(set([p[2] for p in values]))
        obj = [[o[1]] + list(o[2:]) for o in obj]
        object_classes = [k]
        stacked_obj.append([k, obj, object_classes, parameters])
    return stacked_obj, parsed_json


def write_relationships_to_xlsx(wb, relationship_data):
    """Writes Classes, parameter and parameter values for relationships.
    Writes one sheet per relationship class.

    Args:
        wb (openpyxl.workbook): excel workbook to write too.
        relationship_data (List[List]): List of lists containing relationship data give by function get_unstacked_relationships
    """
    for rel in relationship_data:
        ws = wb.create_sheet()

        # try setting the sheetname to relationship class name
        # sheet name can only be 31 chars log
        title = "rel_" + rel[0]
        if len(title) < 32:
            ws.title = title

        ws['A1'] = "Sheet type"
        ws['A2'] = "relationship"
        ws['B1'] = "Data type"
        ws['B2'] = "Parameter"
        ws['C1'] = "relationship class name"
        ws['C2'] = rel[0]
        ws['D1'] = "Number of relationship dimensions"
        ws['D2'] = len(rel[2])
        ws['E1'] = "Number of pivoted relationship dimensions"
        ws['E2'] = 0

        for c, val in enumerate(rel[2]):
            ws.cell(row=4, column=c+1).value = val

        for c, val in enumerate(rel[3]):
            ws.cell(row=4, column=len(rel[2]) + 1 + c).value = val

        start_row = 5
        start_col = 1
        for r, line in enumerate(rel[1]):
            for c, val in enumerate(line):
                ws.cell(row=start_row + r, column=start_col + c).value = val


def write_json_array_to_xlsx(wb, data, sheet_type):
    """Writes json array data for object classes and relationship classes.
    Writes one sheet per relationship/object class.

    Args:
        wb (openpyxl.workbook): excel workbook to write too.
        data (List[List]): List of lists containing json data give by function get_unstacked_objects and get_unstacked_relationships
        sheet_type (str): str with value "relationship" or "object" telling if data is for a relationship or object
    """

    for d in data:
        ws = wb.create_sheet()

        if sheet_type == "relationship":
            sheet_title = "json_"
        elif sheet_type == "object":
            sheet_title = "json_"
        else:
            pass

        # sheet name can only be 31 chars log
        title = sheet_title + d[0]
        if len(title) < 32:
            ws.title = title

        ws['A1'] = "Sheet type"
        ws['A2'] = sheet_type
        ws['B1'] = "Data type"
        ws['B2'] = "json array"
        ws['C1'] = sheet_type + " class name"
        ws['C2'] = d[0]

        if sheet_type == "relationship":
            ws['D1'] = "Number of relationship dimensions"
            ws['D2'] = len(d[1])

        title_rows = d[1]+["json parameter"]
        for c, val in enumerate(title_rows):
            ws.cell(row = 4+c, column = 1).value = val

        start_row = 4 + len(title_rows)
        for col, obj_list in enumerate(d[2]):
            for obj_iter, obj in enumerate(obj_list[0]):
                ws.cell(row=4 + obj_iter, column=2 + col).value = obj

            for row_iter, json_val in enumerate(obj_list[1]):
                ws.cell(row=start_row + row_iter, column=2 + col).value = json_val


def write_objects_to_xlsx(wb, object_data):
    """Writes Classes, parameter and parameter values for objects.
    Writes one sheet per relationship/object class.

    Args:
        wb (openpyxl.workbook): excel workbook to write too.
        object_data (List[List]): List of lists containing relationship data give by function get_unstacked_objects
    """

    for obj in object_data:
        ws = wb.create_sheet()

        # try setting the sheetname to object class name
        # sheet name can only be 31 chars log
        title = "obj_" + obj[0]
        if len(title) < 32:
            ws.title = title

        ws['A1'] = "Sheet type"
        ws['A2'] = "object"
        ws['B1'] = "Data type"
        ws['B2'] = "Parameter"
        ws['C1'] = "object class name"
        ws['C2'] = obj[0]

        for c, val in enumerate(obj[2]):
            ws.cell(row=4, column=c+1).value = val

        for c, val in enumerate(obj[3]):
            ws.cell(row=4, column=len(obj[2]) + 1 + c).value = val

        start_row = 5
        start_col = 1
        for r, line in enumerate(obj[1]):
            for c, val in enumerate(line):
                ws.cell(row=start_row + r, column=start_col + c).value = val


def export_spine_database_to_xlsx(db, filepath):
    """Writes all data in a spine database into an excel file.

    Args:
        db (spinedatabase_api.DatabaseMapping): database mapping for database.
        filepath (str): str with filepath to save excel file to.
    """

    obj_data, obj_json_data = get_unstacked_objects(db)
    rel_data, rel_json_data = get_unstacked_relationships(db)

    wb = Workbook()

    write_relationships_to_xlsx(wb, rel_data)
    write_objects_to_xlsx(wb, obj_data)
    write_json_array_to_xlsx(wb, obj_json_data, "object")
    write_json_array_to_xlsx(wb, rel_json_data, "relationship")

    wb.save(filepath)
    wb.close()


def read_spine_xlsx(filepath):
    """reads all data from a excel file where the sheets are in valid spine data format

    Args:
        filepath (str): str with filepath to excel file to read from.
    """
    wb = load_workbook(filepath)
    sheets = wb.sheetnames

    obj_data = []
    rel_data = []
    obj_json_data = []
    rel_json_data = []

    # read all sheets
    for s in sheets:
        ws = wb[s]

        # check if valid
        if not validate_sheet(ws):
            continue

        sheet_type = ws['A2'].value.lower()
        sheet_data = ws['B2'].value.lower()

        if sheet_data == "parameter":
            # read sheet with data type: 'parameter'
            try:
                data = read_parameter_sheet(ws)
                if sheet_type == "relationship":
                    rel_data.append(data)
                else:
                    obj_data.append(data)
            except:
                print(s)
        elif sheet_data == "json array":
            # read sheet with data type: 'json array'
            try:
                data = read_json_sheet(ws, sheet_type)
                if sheet_type == "relationship":
                    rel_json_data.append(data)
                else:
                    obj_json_data.append(data)
            except:
                print(s)
    wb.close()

    # merge sheets that have the same class.
    error_log = []
    obj_data, el = merge_spine_xlsx_data(obj_data + obj_json_data)
    error_log = error_log + el

    rel_data, el = merge_spine_xlsx_data(rel_data + rel_json_data)
    error_log = error_log + el

    return (obj_data, rel_data, error_log)


def merge_spine_xlsx_data(data):
    """Merge data from different sheets with same object class or
    relationship class.

    Args:
        data (List(SheetData)): list of SheetData

    Returns:
        (List[SheetData]): List of SheetData with only one relationship/object class per item
    """
    error_log = []
    new_data = []
    data = sorted(data, key=lambda x: x.class_name)
    for class_name, values in groupby(data, key=lambda x: x.class_name):
        values = list(values)
        if len(values) < 2:
            if len(values) > 0:
                #only one sheet
                new_data.append(values[0])
            continue
        else:
            # if more than one SheetData with same class_name
            sheet_name = values[0].sheet_name
            object_classes = values[0].object_classes
            parameters = values[0].parameters
            parameter_values = values[0].parameter_values
            objects = values[0].objects
            class_type = values[0].class_type

            iter_values = iter(values)
            next(iter_values)
            for v in iter_values:
                # make sure that the new sheet has same object_classes that first
                if v.object_classes != object_classes:
                    error_log.append["sheet",v.sheet_name,"sheet {} as different object_classes than sheet {} for class {}".format(v.sheet_name, sheet_name, class_name)]
                    continue
                parameters = parameters + v.parameters
                objects = objects + v.objects
                parameter_values = parameter_values + v.parameter_values

            # make unique again
            parameters = list(set(parameters))

            if len(object_classes) > 1:
                keyfunc = lambda x: [x[i] for i,_ in enumerate(object_classes)]
                objects = sorted(objects, key=keyfunc)
                objects = list(k for k,_ in groupby(objects, key=keyfunc))
            else:
                objects = list(set(objects))

            new_data.append(SheetData(sheet_name=sheet_name,
                                      class_name=class_name,
                                      object_classes=object_classes,
                                      parameters=parameters,
                                      parameter_values=parameter_values,
                                      objects=objects,
                                      class_type=class_type))

    return new_data, error_log


def validate_sheet(ws):
    """Checks if supplied sheet is a valid import sheet for spine.

    Args:
        ws (openpyxl.workbook.worksheet): worksheet to validate

    Returns:
        (bool): True if sheet is valid, False otherwise
    """
    sheet_type = ws['A2'].value
    sheet_data = ws['B2'].value

    if not isinstance(sheet_type, str):
        return False
    if not isinstance(sheet_data, str):
        return False
    if sheet_type.lower() not in ["relationship", "object"]:
        return False
    if sheet_data.lower() not in ["parameter", "json array"]:
        return False

    if sheet_type.lower() == "relationship":
        rel_dimension = ws['D2'].value
        rel_name = ws['C2'].value
        if not isinstance(rel_name, str):
            return False
        if not rel_name:
            return False
        if not isinstance(rel_dimension, int):
            return False
        if not rel_dimension > 1:
            return False
        rel_row = read_2d(ws, 4, 4, 1, rel_dimension)
        if None in rel_row:
            return False
    elif sheet_type.lower() == "object":
        obj_name = ws['C2'].value
        if not isinstance(obj_name, str):
            return False
        if not obj_name:
            return False
    return True


def read_json_sheet(ws, sheet_type):
    """Reads a sheet containg json array data for objects and relationships

    Args:
        ws (openpyxl.workbook.worksheet): worksheet to read from
        sheet_type (str): str with value "relationship" or "object" telling if sheet is a relationship or object sheet

    Returns:
        (List[SheetData])
    """
    if sheet_type == "relationship":
        dim = ws['D2'].value
    else:
        dim = 1

    path = ["object" + str(i) for i in range(dim)]

    class_name = ws['C2'].value

    object_classes = []
    for i in range(4, 4 + dim, 1):
        object_classes.append(ws["A" + str(i)].value)

    # search row for until first empty cell
    read_cols = []
    for c, cell in enumerate(ws[4]):
        if c > 0:
            if cell.value is None:
                break
            else:
                read_cols.append(c+1)

    Data = namedtuple("Data", ["parameter_type"] + path + ["parameter", "value"])

    unique_parameters = []
    json_data = []
    # red columnwise from second column.
    for c in read_cols:
        obj_path = []
        parameter = []
        json_vals = []
        for r, cell in enumerate(ws[get_column_letter(c)]):
            if r > 2 and r < 3+dim:
                # get object path
                obj_path.append(cell.value)
            elif r == 3+dim:
                # get parameter name
                parameter = [cell.value]
            elif r > 3+dim:
                # get values until first empty cell
                if cell.value is None:
                    break
                else:
                    json_vals.append(cell.value)

        if json_vals and parameter and None not in obj_path:
            # save values if there is json data, a parameter name
            # and the obj_path doesn't contain None.
            unique_parameters.append(parameter[0])
            packed_json = json.dumps(json_vals)
            json_data.append(Data._make(["json"] + obj_path+parameter+[packed_json]))

    return SheetData(sheet_name=ws.title,
                     class_name=class_name,
                     object_classes=object_classes,
                     parameters=list(set(unique_parameters)),
                     parameter_values=json_data,
                     objects=[],
                     class_type=sheet_type)


def read_parameter_sheet(ws):
    """Reads a sheet containg parameter data for objects and relationships

    Args:
        ws (openpyxl.workbook.worksheet): worksheet to read from

    Returns:
        (List[SheetData])
    """
    sheet_type = ws['A2'].value.lower()
    class_name = ws['C2'].value

    if sheet_type == "object":
        dim = 1
    elif sheet_type == "relationship":
        dim = ws['D2'].value

    # object classes
    object_classes = read_2d(ws, 4, 4, 1, dim)[0]

    # read all columns to the right of the number of cells in dim. Read until
    # encounters a empty cell.
    parameters = []
    for c, cell in enumerate(ws[4]):
        if cell.value is None:
            break
        elif c >= dim:
            parameters.append(cell.value)

    #get data
    data = read_2d(ws, 5, len(ws['A']), 1, dim + len(parameters))

    keyfunc = lambda x: [x[i] for i,_  in enumerate(object_classes)]

    #remove data where not all dimensions exists
    data = [d for d in data if not None in keyfunc(d)]

    data_parameter = []
    if len(parameters) > 0:
        # add that parameter type type should be "value"
        data = [["value"] + d for d in data]
        keyfunc = lambda x: [x[i+1] for i, _ in enumerate(object_classes)]
        key_cols = list(range(0, dim+1, 1))
        val_cols = list(range(dim+1, dim+len(parameters)+1))
        headers = ["parameter_type"] + ["object" + str(x) for x in range(dim)] + parameters
        data_parameter = stack_list_of_tuples(data, headers, key_cols, val_cols)
        data_parameter = [d for d in data_parameter if d.value is not None]

    # find unique relationships from data
    data = sorted(data, key = keyfunc)
    objects = list(k for k,_ in groupby(data, key = keyfunc))
    if dim == 1:
        # flattern list if only one object per row
        objects = [item for sublist in objects for item in sublist]

    return SheetData(sheet_name=ws.title,
                     class_name=class_name,
                     object_classes=object_classes,
                     parameters=parameters,
                     parameter_values=data_parameter,
                     objects=objects,
                     class_type=sheet_type)


def read_2d(ws,start_row = 1,end_row = 1,start_col = 1,end_col = 1):
    """Reads a 2d area from worksheet into a list of lists where each line is
    the inner list.

    Args:
        ws (openpyxl.workbook.worksheet): Worksheet to look in
        start_row (Integer): start row to read, 1-indexed (as excel)
        end_row (Integer): row to read to, 1-indexed (as excel)
        start_col (Integer): start column to read, 1-indexed (as excel)
        end_col (Integer): end column to read to, 1-indexed (as excel)

    Returns:
        (List) List of all lines read.
    """
    end_col = get_column_letter(end_col)
    start_col = get_column_letter(start_col)
    xl_index = '{}{}:{}{}'.format(start_col, start_row, end_col, end_row)
    values = [[inner.value for inner in outer] for outer in ws[xl_index]]
    return values


def max_col_in_row(ws, row=1):
    """Finds max col index for given row. If no data exists on row, returns 1.

    Args:
        ws (openpyxl.workbook.worksheet): Worksheet to look in
        row (Integer): index for row to search, 1-indexed (as excel)

    Returns:
        (Integer) column index of last cell with value.
    """
    for cell in reversed(ws[row]):
        if cell.value is not None:
            break
    return cell.col_idx


def export_object_classes_to_spine_db(db, data):
    """Tries to insert object classes into given database mapping.
    Filters out duplicates before inserting.

    Args:
        db (spinedatabase_api.DatabaseMapping): mapping for database to insert into
        data (List[SheetData]): data to insert

    Returns:
        (List, List) Tuple of two lists, first one a list of successful inserts.
        Second one a list of failed inserts.
    """
    obj_classes = list(set([o.class_name for o in data]))

    existing_classes = db.object_class_list().all()

    # filter classes that don't already exist in db
    new_classes = [o for o in obj_classes if o not in [e.name for e in existing_classes]]

    error_log = []
    import_log = []
    for nc in new_classes:
        try:
            db.add_object_class(name=nc)
            import_log.append(["object_class", nc])
        except SpineDBAPIError as e:
            error_log.append(["object_class", nc, e.msg])
            continue
    return import_log, error_log


def export_object_parameters_spine_db(db, data):
    """Tries to insert object class parameter into given database mapping.
    Filters out duplicates before inserting. Filters if class exists.

    Args:
        db (spinedatabase_api.DatabaseMapping): mapping for database to insert into
        data (List[SheetData]): data to insert

    Returns:
        (List, List) Tuple of two lists, first one a list of successful inserts.
        Second one a list of failed inserts.
    """
    parameters = [[[object_list.class_name, p] for p in object_list.parameters]
                  for object_list in data]
    parameters = [item for sublist in parameters for item in sublist]
    object_classes = set([c[0] for c in parameters])

    # existing object classes
    db_classes = db.object_class_list().\
        filter(db.ObjectClass.name.in_(object_classes)).all()
    obj_class_name_2_id = {o.name: o.id for o in db_classes}

    # check if the parameters object class exists in db.
    error_log = [["object_parameter", p[1],
                  "object_class '{}' did not exist in database".format(p[0])]
                for p in parameters if p[0] not in obj_class_name_2_id.keys()]

    parameters = [[obj_class_name_2_id[p[0]], p[0], p[1]] for p in parameters
                  if p[0] in obj_class_name_2_id.keys()]

    # existing parameters in database
    db_parameters = db.object_parameter_list().\
        filter(db.Parameter.name.in_([p[2] for p in parameters])).all()
    db_parameters = [[d.object_class_name, d.parameter_name]
                     for d in db_parameters]

    # remove already existing parameters
    parameters = [p for p in parameters if [p[1], p[2]] not in db_parameters]

    import_log = []
    for p in parameters:
        try:
            db.add_parameter(name=p[2], object_class_id=p[0])
            import_log.append(["object_parameter", p[2]])
        except SpineDBAPIError as e:
            error_log.append(["object_parameter", p[2], e.msg])
            continue

    return import_log, error_log


def export_object_to_spine_db(db, data):
    """Tries to insert objects into given database mapping.
    Filters out duplicates before inserting. Filters if class exists.

    Args:
        db (spinedatabase_api.DatabaseMapping): mapping for database to insert into
        data (List[SheetData]): data to insert into

    Returns:
        (List, List) Tuple of two lists, first one a list of successful inserts.
        Second one a list of failed inserts.
    """
    objects = [[[object_list.class_name, o] for o in object_list.objects]
               for object_list in data]
    objects = [item for sublist in objects for item in sublist]
    object_classes = set([c[0] for c in objects])

    # existing object_classes.
    db_classes = db.object_class_list().filter(db.ObjectClass.name.in_(object_classes)).all()
    obj_class_name_2_id = {o.name: o.id for o in db_classes}

    # remove objects where the object_class does not exist in db.
    error_log = [["object", o[1],
                  "object_class '{}' did not exist in database".format(o[0])]
                 for o in objects if o[0] not in obj_class_name_2_id.keys()]

    objects = [[obj_class_name_2_id[o[0]], o[0], o[1]] for o in objects
               if o[0] in obj_class_name_2_id.keys()]

    # existsing objects
    db_objects = db.object_list().all()
    db_objects = [[d.class_id, d.name] for d in db_objects]

    # remove already existing objects
    objects = [o for o in objects if [o[0], o[2]] not in db_objects]

    # export to db
    import_log = []
    for o in objects:
        try:
            db.add_object(name=o[2], class_id=o[0])
            import_log.append(["object", o[2]])
        except SpineDBAPIError as e:
            error_log.append(["object", o[2], e.msg])
            continue

    return import_log, error_log


def export_object_parameter_values(db, data):
    """Tries to insert objects parameter values into given database mapping.

    Args:
        db (spinedatabase_api.DatabaseMapping): mapping for database to insert into
        data (List[SheetData]): data to insert into

    Returns:
        (List, List) Tuple of two lists, first one a list of successful inserts.
        Second one a list of failed inserts.
    """
    parameter_values = [[[object_list.class_name, p] for p in object_list.parameter_values]
                        for object_list in data]
    parameter_values = [item for sublist in parameter_values for item in sublist]
    parameters = set([c[1].parameter for c in parameter_values])
    object_classes = set([c[0] for c in parameter_values])

    # existing objects.
    db_objects = db.object_list().all()
    obj_name_2_id = {o.name: o.id for o in db_objects}

    # existing parameters.
    db_parameters = db.parameter_list().\
        filter(db.Parameter.name.in_(parameters)).all()
    parameter_name_2_id = {o.name: o.id for o in db_parameters}

    # existing object_classes.
    db_classes = db.object_class_list().\
        filter(db.ObjectClass.name.in_(object_classes)).all()
    obj_class_name_2_id = {o.name: o.id for o in db_classes}

    # existing values
    db_parameter_values = db.object_parameter_value_list().all()
    db_parameter_values_dict = {'_'.join([d.object_class_name,
                                          d.object_name,
                                          d.parameter_name]): d
                                for d in db_parameter_values}

    object_class_parameter = [[dp.object_class_id, dp.id] for dp in db_parameters]
    object_class_object = [[dp.class_id, dp.id] for dp in db_objects]

    error_log = []
    update_parameters = []
    insert_parameters = []
    ParVal = namedtuple("ParVal",["id", "object_id", "parameter_id",
                                  "name", "value", "key", "parameter_type"])
    for p in parameter_values:
        # check if parameter value object class doesn't exists in db
        if p[0] not in obj_class_name_2_id.keys():
            error_log.append(["object_parameter_value",
                              p[1].parameter,
                              "object_class '{}' did not exist in database".format(p[0])])
            continue

        # check if object exists in database
        if p[1].object0 not in obj_name_2_id.keys():
            error_log.append(["object_parameter_value",
                              p[1].parameter,
                              "object_class '{}' did not exist in database".format(p[0])])
            continue

        # check if parameter exists in database
        if p[1].parameter not in parameter_name_2_id.keys():
            error_log.append(["object_parameter_value",
                              p[1].parameter,
                              "parameter '{}' did not exist in database".format(p[0])])
            continue

        obj_id = obj_name_2_id[p[1].object0]
        obj_class_id = obj_class_name_2_id[p[0]]
        par_id = parameter_name_2_id[p[1].parameter]

        key = '_'.join([p[0], p[1].object0, p[1].parameter])

        if key in db_parameter_values_dict.keys():
            # parameter value exists, see if value needs updating.
            if p[1].parameter_type == "value":
                compare_with = str(db_parameter_values_dict[key].value)
            else:
                compare_with = db_parameter_values_dict[key].json

            if str(p[1].value) != compare_with:
                # parameter value is different from db
                new_p = ParVal(db_parameter_values_dict[key].parameter_value_id,
                               obj_id, par_id, p[1].parameter, p[1].value, key,
                               p[1].parameter_type)
                update_parameters.append(new_p)
        else:
            # parameter value doesn't exists
            # check if object_class for parameter matches db
            if [obj_class_id, obj_id] not in object_class_object:
                error_log.append(["object_parameter_value",
                                  p[1].parameter,
                                  "parameter object did not match object class in database"])
                continue
            # check if object_class for parameter matches db
            if [obj_class_id, par_id] not in object_class_parameter:
                error_log.append(["object_parameter_value",
                                  p[1].parameter,
                                  "parameter object class did not match parameter object class in database"])
                continue

            insert_parameters.append(ParVal(None, obj_id, par_id,
                                            p[1].parameter, p[1].value,
                                            key, p[1].parameter_type))

    # update parameter values
    import_log = []
    for p in update_parameters:
        try:
            db.update_parameter_value(id=p.id,
                                      field_name=p.parameter_type,
                                      new_value=p.value)
            import_log.append(["object_parameter_value_update", p.key])
        except SpineDBAPIError as e:
            error_log.append(["object_parameter_value", p.key, e.msg])
            continue

    # insert new parameter values
    for p in insert_parameters:
        try:
            input_args = {"object_id": p.object_id,
                          "parameter_id": p.parameter_id,
                          p.parameter_type: p.value}
            db.add_parameter_value(**input_args)
            import_log.append(["object_parameter_value_insert", p.key])
        except SpineDBAPIError as e:
            error_log.append(["object_parameter_value", p.key, e.msg])
            continue

    return import_log, error_log


def export_relationship_class_to_spine_db(db, data):
    """Tries to insert realtionship classes into given database mapping.

    Args:
        db (spinedatabase_api.DatabaseMapping): mapping for database to insert into
        data (List[SheetData]): data to insert into

    Returns:
        (List, List) Tuple of two lists, first one a list of successful inserts.
        Second one a list of failed inserts.
    """
    rel_classes = [[o.class_name, o.object_classes] for o in data]

    existing_classes = db.relationship_class_list().all()
    existing_classes = list(set([ec.name for ec in existing_classes]))

    rel_classes = [o for o in rel_classes if o[0] not in existing_classes]

    object_classes = [o[1] for o in rel_classes]
    object_classes = set(item for sublist in object_classes for item in sublist)

    # existing object_classes.
    db_classes = db.object_class_list().\
        filter(db.ObjectClass.name.in_(object_classes)).all()
    obj_class_name_2_id = {o.name: o.id for o in db_classes}

    # find ids for object_class name and make sure they are valid
    error_log = []
    valid_rel_classes = []
    for r in rel_classes:
        if set(r[1]).issubset(obj_class_name_2_id.keys()):
            rd = {'name': r[0],
                  'object_class_id_list': [obj_class_name_2_id[o] for o in r[1]]}
            valid_rel_classes.append(rd)
        else:
            error_log.append(["relationship_class", r[0],
                              "relationship class contains invalid object_classes"])

    # insert relationship classes
    import_log = []
    for r in valid_rel_classes:
        try:
            db.add_wide_relationship_class(**r)
            import_log.append(["relationship_class", r['name']])
        except SpineDBAPIError as e:
            error_log.append(["relationship_class", r['name'], e.msg])
            continue

    return import_log, error_log


def export_relationships_to_spine_db(db, data):
    """Tries to insert realtionships into given database mapping.

    Args:
        db (spinedatabase_api.DatabaseMapping): mapping for database to insert into
        data (List[SheetData]): data to insert into

    Returns:
        (List, List) Tuple of two lists, first one a list of successful inserts.
        Second one a list of failed inserts.
    """
    rels = [list(zip([o.class_name]*len(o.objects),
                     [o.object_classes]*len(o.objects),
                     o.objects)) for o in data]

    rels = [item for sublist in rels for item in sublist]

    rel_class = set([r.class_name for r in data])

    object_classes = [o.object_classes for o in data]
    object_classes = set(item for sublist in object_classes for item in sublist)

    # existing relationship classes
    db_rel_classes = db.relationship_class_list().\
        filter(db.RelationshipClass.name.in_(rel_class)).\
        order_by(db.RelationshipClass.name, db.RelationshipClass.dimension).all()

    # existing objects.
    db_objects = db.object_list().all()
    obj_name_2_id = {o.name: o.id for o in db_objects}
    obj_name_2_class = {o.name: o.class_id for o in db_objects}

    # existing object_classes.
    db_classes = db.object_class_list().\
        filter(db.ObjectClass.name.in_(object_classes)).all()
    obj_class_name_2_id = {o.name: o.id for o in db_classes}

    # existing relationships.
    db_relationships = db.wide_relationship_list().all()
    db_relationships = [[r.class_id, r.object_name_list]
                        for r in db_relationships]

    # pivot db data
    dbRelClass = namedtuple("dbRelClass", ["name", "id", "object_classes"])
    db_rel_class_dict = {}
    for key, val in groupby(db_rel_classes, key=lambda x: x.name):
        val = sorted(val, key=lambda x: x.dimension)
        db_rel_class_dict[key] = dbRelClass(key,
                                            val[0].id,
                                            [v.object_class_id for v in val])

    error_log = []
    valid_relationships = []
    for r in rels:
        key = "_".join(r[2])
        # check if relationship class exist in db
        if r[0] not in db_rel_class_dict.keys():
            error_log.append(["relationship",
                              key,
                              "relationship class does not exist in db"])
            continue

        db_rel_class = db_rel_class_dict[r[0]]
        obj_name_list_str = ",".join(r[2])

        # check if a relationship for class with same objects exist
        if [db_rel_class.id, obj_name_list_str] in db_relationships:
            continue
        # check that object classes and objects exits in db
        if not set(r[1]).issubset(obj_class_name_2_id.keys()):
            error_log.append(["relationship",
                              key,
                              "all object class names doesn't exist in db"])
            continue
        if not set(r[2]).issubset(obj_name_2_id.keys()):
            error_log.append(["relationship",
                              key,
                              "all object names doesn't exist in db"])
            continue

        # convert names to ids
        r_classes = [obj_class_name_2_id[item] for item in r[1]]
        r_ids = [obj_name_2_id[item] for item in r[2]]
        r_id_2_class = [obj_name_2_class[item] for item in r[2]]

        # check that object classes are in order and same as db
        if not r_classes == db_rel_class.object_classes:
            error_log.append(["relationship",
                              key,
                              "object class name does not match object class names for relationship class in db"])
            continue
        # check that objects are right class
        if not r_id_2_class == db_rel_class.object_classes:
            error_log.append(["relationship",
                              key,
                              "objects does not match object class for relationship class in db"])
            continue

        valid_relationships.append({'name': key,
                                    'class_id': db_rel_class.id,
                                    'object_id_list': r_ids,
                                    'key': key})

    # insert relationship classes
    import_log = []
    for r in valid_relationships:
        try:
            db.add_wide_relationship(**r)
            import_log.append(["relationship", r['key']])
        except SpineDBAPIError as e:
            error_log.append(["relationship", r['key'], e.msg])
            continue

    return import_log, error_log


def export_relationships_parameters_to_spine_db(db, data):
    """Tries to insert realtionship parameters into given database mapping.

    Args:
        db (spinedatabase_api.DatabaseMapping): mapping for database to insert into
        data (List[SheetData]): data to insert into

    Returns:
        (List, List) Tuple of two lists, first one a list of successful inserts.
        Second one a list of failed inserts.
    """
    rels = [list(zip([o.class_name]*len(o.parameters), o.parameters)) for o in data]
    rels = [item for sublist in rels for item in sublist]

    rel_class = set([r[0] for r in rels])

    # existing relationship classes
    db_rel_classes = db.relationship_class_list().\
        filter(db.RelationshipClass.name.in_(rel_class)).\
        order_by(db.RelationshipClass.name, db.RelationshipClass.dimension).all()

    # pivot db data
    dbRelClass = namedtuple("dbRelClass", ["name", "id", "object_classes"])
    db_rel_class_dict = {}
    for key, val in groupby(db_rel_classes, key=lambda x: x.name):
        val = sorted(val, key=lambda x: x.dimension)
        db_rel_class_dict[key] = dbRelClass(key,
                                            val[0].id,
                                            [v.object_class_id for v in val])

    db_parameters = db.relationship_parameter_list().all()
    db_parameters = [[d.relationship_class_name, d.parameter_name] for d in db_parameters]

    error_log = []
    valid_relationships_parameters = []
    for r in rels:
        # check relationship class exists
        if r[0] not in db_rel_class_dict.keys():
            error_log.append(["relationship_parameter", r[1],
                              "relationship class does not exist in db"])
            continue
        # if a parameter with same class exists don't add
        if list(r) in db_parameters:
            continue
        valid_relationships_parameters.append({'relationship_class_id': db_rel_class_dict[r[0]].id, 'name': r[1]})

    # insert relationship classes
    import_log = []
    for r in valid_relationships_parameters:
        try:
            db.add_parameter(**r)
            import_log.append(["relationship_parameter", r['name']])
        except SpineDBAPIError as e:
            error_log.append(["relationship_parameter", r['name'], e.msg])
            continue

    return import_log, error_log


def export_relationships_parameter_value_to_spine_db(db, data):
    """Tries to insert realtionships parameter values into given database mapping.

    Args:
        db (spinedatabase_api.DatabaseMapping): mapping for database to insert into
        data (List[SheetData]): data to insert into

    Returns:
        (List, List) Tuple of two lists, first one a list of successful inserts.
        Second one a list of failed inserts.
    """

    rels = [list(zip([o.class_name]*len(o.parameter_values),
                     [o.object_classes]*len(o.parameter_values),
                     o.parameter_values)) for o in data]

    rels = [item for sublist in rels for item in sublist]

    rel_class = set([r.class_name for r in data])

    # existing relationship classes
    db_rel_classes = db.relationship_class_list().\
        filter(db.RelationshipClass.name.in_(rel_class)).\
        order_by(db.RelationshipClass.name, db.RelationshipClass.dimension).all()

    # existing relationships.
    db_relationships = db.wide_relationship_list().all()
    db_rel_2_id = {str(r.class_id) + ',' + r.object_name_list: r.id
                   for r in db_relationships}

    # existing values
    db_rel_par = db.relationship_parameter_value_list().all()
    db_rel_par = {','.join([p.relationship_class_name, p.object_name_list, p.parameter_name]):
                  p for p in db_rel_par}

    # pivot db data
    dbRelClass = namedtuple("dbRelClass", ["name", "id", "object_classes"])
    db_rel_class_dict = {}
    for key, val in groupby(db_rel_classes, key=lambda x: x.name):
        val = sorted(val, key=lambda x: x.dimension)
        db_rel_class_dict[key] = dbRelClass(key,
                                            val[0].id,
                                            [v.object_class_id for v in val])

    # existing relationship parameters.
    db_parameters = db.relationship_parameter_list().all()
    db_parameters = {p.parameter_name: (p.relationship_class_name,
                                        p.id) for p in db_parameters}

    error_log = []
    update_par = []
    insert_par = []
    for r in rels:
        key = "_".join(r[2][1:-1])
        # check if relationship class exists in db
        if r[0] not in db_rel_class_dict.keys():
            error_log.append(["relationship_parameter_value", key,
                              "relationship class does not exist in db"])
            continue

        db_rel_class = db_rel_class_dict[r[0]]
        class_obj_name_list_str = str(db_rel_class.id) + ',' + ",".join(r[2][1:-2])
        class_name_obj_name_list_par_str = ','.join([r[0], ",".join(r[2][1:-2]), r[2].parameter])

        # check if a relationship for class with same objects exits
        if class_obj_name_list_str not in db_rel_2_id.keys():
            error_log.append(["relationship_parameter_value", key,
                              "relationship does not exist in db"])
            continue

        # check if parameter exists in db
        if r[2].parameter not in db_parameters.keys():
            error_log.append(["relationship_parameter_value", key,
                              "parameter does not exist in db"])
            continue

        # check if parameter relationship class matches given class
        if db_parameters[r[2].parameter][0] != r[0]:
            error_log.append(["relationship_parameter_value", key,
                              "parameter relationship class does not match the class in db"])
            continue

        par_id = db_parameters[r[2].parameter][1]
        rel_id = db_rel_2_id[class_obj_name_list_str]
        value = r[2].value

        # spit data into update and insert lists
        if class_name_obj_name_list_par_str in db_rel_par.keys():
            # parameter value exists.
            if r[2].parameter_type == "value":
                compare_with = str(db_rel_par[class_name_obj_name_list_par_str].value)
            else:
                compare_with = db_rel_par[class_name_obj_name_list_par_str].json

            if value != compare_with:
                # parameter does not match existing value, update value
                update_par.append([{'id': db_rel_par[class_name_obj_name_list_par_str].parameter_value_id,
                                    'field_name': r[2].parameter_type,
                                    'new_value': value}, key])
        else:
            # parameter value does not exist, insert new
            insert_par.append([{'parameter_id': par_id,
                                'relationship_id': rel_id,
                                r[2].parameter_type: value,
                                }, key])

    # insert relationship classes
    import_log = []
    for r in insert_par:
        try:
            db.add_parameter_value(**r[0])
            import_log.append(["relationship_parameter_value", r[1]])
        except SpineDBAPIError as e:
            error_log.append(["relationship_parameter_value", r[1], e.msg])
            continue

    # update parameters
    for r in update_par:
        try:
            db.update_parameter_value(**r[0])
            import_log.append(["relationship_parameter_value", r[1]])
        except SpineDBAPIError as e:
            error_log.append(["relationship_parameter_value", r[1], e.msg])
            continue

    return import_log, error_log
