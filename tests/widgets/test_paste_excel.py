######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# Copyright Spine Toolbox contributors
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################
import unittest
from spinedb_api import DateTime, to_database
from spinedb_api.parameter_value import join_value_and_type
from spinetoolbox.widgets.paste_excel import clipboard_excel_as_table


class Test(unittest.TestCase):
    def test_single_empty_cell_gives_empty_table(self):
        data = b'<?xml version="1.0"?>\r\n\
<?mso-application progid="Excel.Sheet"?>\r\n\
<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"\r\n\
 xmlns:o="urn:schemas-microsoft-com:office:office"\r\n\
 xmlns:x="urn:schemas-microsoft-com:office:excel"\r\n\
 xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet"\r\n\
 xmlns:html="http://www.w3.org/TR/REC-html40">\r\n\
 <Styles>\r\n\
  <Style ss:ID="Default" ss:Name="Normal">\r\n\
   <Alignment ss:Vertical="Bottom"/>\r\n\
   <Borders/>\r\n\
   <Font ss:FontName="Calibri" x:Family="Swiss" ss:Size="11" ss:Color="#000000"/>\r\n\
   <Interior/>\r\n\
   <NumberFormat/>\r\n\
   <Protection/>\r\n\
  </Style>\r\n\
 </Styles>\r\n\
 <Worksheet ss:Name="Sheet1">\r\n\
  <Table ss:ExpandedColumnCount="1" ss:ExpandedRowCount="1"\r\n\
   ss:DefaultRowHeight="15">\r\n\
  </Table>\r\n\
 </Worksheet>\r\n\
</Workbook>\r\n\
\x00'
        self.assertEqual(clipboard_excel_as_table(data), [])

    def test_convert_single_boolean_cell(self):
        data = b'<?xml version="1.0"?>\r\n\
<?mso-application progid="Excel.Sheet"?>\r\n\
<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"\r\n\
 xmlns:o="urn:schemas-microsoft-com:office:office"\r\n\
 xmlns:x="urn:schemas-microsoft-com:office:excel"\r\n\
 xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet"\r\n\
 xmlns:html="http://www.w3.org/TR/REC-html40">\r\n\
 <Styles>\r\n\
  <Style ss:ID="Default" ss:Name="Normal">\r\n\
   <Alignment ss:Vertical="Bottom"/>\r\n\
   <Borders/>\r\n\
   <Font ss:FontName="Calibri" x:Family="Swiss" ss:Size="11" ss:Color="#000000"/>\r\n\
   <Interior/>\r\n\
   <NumberFormat/>\r\n\
   <Protection/>\r\n\
  </Style>\r\n\
 </Styles>\r\n\
 <Worksheet ss:Name="Sheet1">\r\n\
  <Table ss:ExpandedColumnCount="1" ss:ExpandedRowCount="1"\r\n\
   ss:DefaultRowHeight="15">\r\n\
   <Row>\r\n\
    <Cell><Data ss:Type="Boolean">1</Data></Cell>\r\n\
   </Row>\r\n\
  </Table>\r\n\
 </Worksheet>\r\n\
</Workbook>\r\n\
\x00'
        value, _ = to_database(True)
        self.assertEqual(clipboard_excel_as_table(data), [[value]])

    def test_convert_single_number_cell(self):
        data = b'<?xml version="1.0"?>\r\n\
<?mso-application progid="Excel.Sheet"?>\r\n\
<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"\r\n\
 xmlns:o="urn:schemas-microsoft-com:office:office"\r\n\
 xmlns:x="urn:schemas-microsoft-com:office:excel"\r\n\
 xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet"\r\n\
 xmlns:html="http://www.w3.org/TR/REC-html40">\r\n\
 <Styles>\r\n\
  <Style ss:ID="Default" ss:Name="Normal">\r\n\
   <Alignment ss:Vertical="Bottom"/>\r\n\
   <Borders/>\r\n\
   <Font ss:FontName="Calibri" x:Family="Swiss" ss:Size="11" ss:Color="#000000"/>\r\n\
   <Interior/>\r\n\
   <NumberFormat/>\r\n\
   <Protection/>\r\n\
  </Style>\r\n\
  <Style ss:ID="s63">\r\n\
   <NumberFormat/>\r\n\
  </Style>\r\n\
 </Styles>\r\n\
 <Worksheet ss:Name="Sheet1">\r\n\
  <Table ss:ExpandedColumnCount="1" ss:ExpandedRowCount="1"\r\n\
   ss:DefaultRowHeight="15">\r\n\
   <Row>\r\n\
    <Cell ss:StyleID="s63"><Data ss:Type="Number">2.2999999999999998</Data></Cell>\r\n\
   </Row>\r\n\
  </Table>\r\n\
 </Worksheet>\r\n\
</Workbook>\r\n\
\x00'
        self.assertEqual(clipboard_excel_as_table(data), [[2.3]])

    def test_convert_single_string_cell(self):
        data = b'<?xml version="1.0"?>\r\n\
<?mso-application progid="Excel.Sheet"?>\r\n\
<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"\r\n\
 xmlns:o="urn:schemas-microsoft-com:office:office"\r\n\
 xmlns:x="urn:schemas-microsoft-com:office:excel"\r\n\
 xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet"\r\n\
 xmlns:html="http://www.w3.org/TR/REC-html40">\r\n\
 <Styles>\r\n\
  <Style ss:ID="Default" ss:Name="Normal">\r\n\
   <Alignment ss:Vertical="Bottom"/>\r\n\
   <Borders/>\r\n\
   <Font ss:FontName="Calibri" x:Family="Swiss" ss:Size="11" ss:Color="#000000"/>\r\n\
   <Interior/>\r\n\
   <NumberFormat/>\r\n\
   <Protection/>\r\n\
  </Style>\r\n\
 </Styles>\r\n\
 <Worksheet ss:Name="Sheet1">\r\n\
  <Table ss:ExpandedColumnCount="1" ss:ExpandedRowCount="1"\r\n\
   ss:DefaultRowHeight="15">\r\n\
   <Row>\r\n\
    <Cell><Data ss:Type="String">this is text</Data></Cell>\r\n\
   </Row>\r\n\
  </Table>\r\n\
 </Worksheet>\r\n\
</Workbook>\r\n\
\x00'
        self.assertEqual(clipboard_excel_as_table(data), [["this is text"]])

    def test_convert_single_date_time_cell(self):
        data = b'<?xml version="1.0"?>\r\n\
<?mso-application progid="Excel.Sheet"?>\r\n\
<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"\r\n\
 xmlns:o="urn:schemas-microsoft-com:office:office"\r\n\
 xmlns:x="urn:schemas-microsoft-com:office:excel"\r\n\
 xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet"\r\n\
 xmlns:html="http://www.w3.org/TR/REC-html40">\r\n\
 <Styles>\r\n\
  <Style ss:ID="Default" ss:Name="Normal">\r\n\
   <Alignment ss:Vertical="Bottom"/>\r\n\
   <Borders/>\r\n\
   <Font ss:FontName="Calibri" x:Family="Swiss" ss:Size="11" ss:Color="#000000"/>\r\n\
   <Interior/>\r\n\
   <NumberFormat/>\r\n\
   <Protection/>\r\n\
  </Style>\r\n\
  <Style ss:ID="s64">\r\n\
   <NumberFormat ss:Format="General Date"/>\r\n\
  </Style>\r\n\
 </Styles>\r\n\
 <Worksheet ss:Name="Sheet1">\r\n\
  <Table ss:ExpandedColumnCount="1" ss:ExpandedRowCount="1"\r\n\
   ss:DefaultRowHeight="15">\r\n\
   <Column ss:AutoFitWidth="0" ss:Width="109.5"/>\r\n\
   <Row>\r\n\
    <Cell ss:StyleID="s64"><Data ss:Type="DateTime">2024-08-14T14:41:44.000</Data></Cell>\r\n\
   </Row>\r\n\
  </Table>\r\n\
 </Worksheet>\r\n\
</Workbook>\r\n\
\x00'
        value = bytes(join_value_and_type(*to_database(DateTime("2024-08-14T14:41:44"))), encoding="utf-8")
        self.assertEqual(clipboard_excel_as_table(data), [[value]])

    def test_small_table(self):
        data = b'<?xml version="1.0"?>\r\n\
<?mso-application progid="Excel.Sheet"?>\r\n\
<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"\r\n\
 xmlns:o="urn:schemas-microsoft-com:office:office"\r\n\
 xmlns:x="urn:schemas-microsoft-com:office:excel"\r\n\
 xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet"\r\n\
 xmlns:html="http://www.w3.org/TR/REC-html40">\r\n\
 <Styles>\r\n\
  <Style ss:ID="Default" ss:Name="Normal">\r\n\
   <Alignment ss:Vertical="Bottom"/>\r\n\
   <Borders/>\r\n\
   <Font ss:FontName="Calibri" x:Family="Swiss" ss:Size="11" ss:Color="#000000"/>\r\n\
   <Interior/>\r\n\
   <NumberFormat/>\r\n\
   <Protection/>\r\n\
  </Style>\r\n\
  <Style ss:ID="s63">\r\n\
   <NumberFormat/>\r\n\
  </Style>\r\n\
  <Style ss:ID="s64">\r\n\
   <NumberFormat ss:Format="General Date"/>\r\n\
  </Style>\r\n\
 </Styles>\r\n\
 <Worksheet ss:Name="Sheet1">\r\n\
  <Table ss:ExpandedColumnCount="3" ss:ExpandedRowCount="2"\r\n\
   ss:DefaultRowHeight="15">\r\n\
   <Column ss:Index="3" ss:AutoFitWidth="0" ss:Width="109.5"/>\r\n\
   <Row>\r\n\
    <Cell ss:StyleID="s63"><Data ss:Type="Number">2.2999999999999998</Data></Cell>\r\n\
    <Cell><Data ss:Type="Boolean">1</Data></Cell>\r\n\
    <Cell ss:StyleID="s64"><Data ss:Type="DateTime">2024-08-14T14:41:44.000</Data></Cell>\r\n\
   </Row>\r\n\
   <Row>\r\n\
    <Cell><Data ss:Type="String">this is text</Data></Cell>\r\n\
   </Row>\r\n\
  </Table>\r\n\
 </Worksheet>\r\n\
</Workbook>\r\n\
\x00'
        bool_value, _ = to_database(True)
        date_time_value = bytes(join_value_and_type(*to_database(DateTime("2024-08-14T14:41:44"))), encoding="utf-8")
        self.assertEqual(
            clipboard_excel_as_table(data), [[2.3, bool_value, date_time_value], ["this is text", None, None]]
        )

    def test_table_with_holes_in_columns(self):
        data = b'<?xml version="1.0"?>\r\n\
<?mso-application progid="Excel.Sheet"?>\r\n\
<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"\r\n\
 xmlns:o="urn:schemas-microsoft-com:office:office"\r\n\
 xmlns:x="urn:schemas-microsoft-com:office:excel"\r\n\
 xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet"\r\n\
 xmlns:html="http://www.w3.org/TR/REC-html40">\r\n\
 <Styles>\r\n\
  <Style ss:ID="Default" ss:Name="Normal">\r\n\
   <Alignment ss:Vertical="Bottom"/>\r\n\
   <Borders/>\r\n\
   <Font ss:FontName="Calibri" x:Family="Swiss" ss:Size="11" ss:Color="#000000"/>\r\n\
   <Interior/>\r\n\
   <NumberFormat/>\r\n\
   <Protection/>\r\n\
  </Style>\r\n\
 </Styles>\r\n\
 <Worksheet ss:Name="Sheet1">\r\n\
  <Table ss:ExpandedColumnCount="3" ss:ExpandedRowCount="3"\r\n\
  ss:DefaultRowHeight="15">\r\n\
  <Row>\r\n\
   <Cell><Data ss:Type="Number">2.2999999999999998</Data></Cell>\r\n\
   <Cell><Data ss:Type="Number">2.4</Data></Cell>\r\n\
  </Row>\r\n\
  <Row>\r\n\
   <Cell><Data ss:Type="Number">2.5</Data></Cell>\r\n\
   <Cell ss:Index="3"><Data ss:Type="Number">2.6</Data></Cell>\r\n\
  </Row>\r\n\
  <Row>\r\n\
   <Cell ss:Index="2"><Data ss:Type="Number">2.7</Data></Cell>\r\n\
   <Cell><Data ss:Type="Number">2.8</Data></Cell>\r\n\
  </Row>\r\n\
  </Table>\r\n\
 </Worksheet>\r\n\
</Workbook>\r\n\
\x00'
        self.assertEqual(clipboard_excel_as_table(data), [[2.3, 2.4, None], [2.5, None, 2.6], [None, 2.7, 2.8]])

    def test_table_with_holes_in_rows(self):
        data = b'<?xml version="1.0"?>\r\n\
<?mso-application progid="Excel.Sheet"?>\r\n\
<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"\r\n\
 xmlns:o="urn:schemas-microsoft-com:office:office"\r\n\
 xmlns:x="urn:schemas-microsoft-com:office:excel"\r\n\
 xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet"\r\n\
 xmlns:html="http://www.w3.org/TR/REC-html40">\r\n\
 <Styles>\r\n\
  <Style ss:ID="Default" ss:Name="Normal">\r\n\
   <Alignment ss:Vertical="Bottom"/>\r\n\
   <Borders/>\r\n\
   <Font ss:FontName="Calibri" x:Family="Swiss" ss:Size="11" ss:Color="#000000"/>\r\n\
   <Interior/>\r\n\
   <NumberFormat/>\r\n\
   <Protection/>\r\n\
  </Style>\r\n\
 </Styles>\r\n\
 <Worksheet ss:Name="Sheet1">\r\n\
  <Table ss:ExpandedColumnCount="2" ss:ExpandedRowCount="3"\r\n\
   ss:DefaultRowHeight="15">\r\n\
   <Row>\r\n\
    <Cell><Data ss:Type="Number">2.2999999999999998</Data></Cell>\r\n\
    <Cell><Data ss:Type="Number">2.4</Data></Cell>\r\n\
   </Row>\r\n\
   <Row ss:Index="3">\r\n\
    <Cell><Data ss:Type="Number">2.5</Data></Cell>\r\n\
    <Cell><Data ss:Type="Number">2.6</Data></Cell>\r\n\
   </Row>\r\n\
  </Table>\r\n\
 </Worksheet>\r\n\
</Workbook>\r\n\
\x00'
        self.assertEqual(clipboard_excel_as_table(data), [[2.3, 2.4], [None, None], [2.5, 2.6]])


if __name__ == "__main__":
    unittest.main()
