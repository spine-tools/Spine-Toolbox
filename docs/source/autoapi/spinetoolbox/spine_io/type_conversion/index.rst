:mod:`spinetoolbox.spine_io.type_conversion`
============================================

.. py:module:: spinetoolbox.spine_io.type_conversion


Module Contents
---------------

.. py:class:: NewIntegerSequenceDateTimeConvertSpecDialog(*args, **kwargs)

   Bases: :class:`PySide2.QtWidgets.QDialog`

   .. method:: _validate(self)



   .. method:: get_spec(self)




.. function:: value_to_convert_spec(value)


.. py:class:: ConvertSpec

   .. attribute:: DISPLAY_NAME
      :annotation: = 

      

   .. attribute:: RETURN_TYPE
      

      

   .. method:: convert_function(self)



   .. method:: to_json_value(self)




.. py:class:: DateTimeConvertSpec

   Bases: :class:`spinetoolbox.spine_io.type_conversion.ConvertSpec`

   .. attribute:: DISPLAY_NAME
      :annotation: = datetime

      

   .. attribute:: RETURN_TYPE
      

      


.. py:class:: DurationConvertSpec

   Bases: :class:`spinetoolbox.spine_io.type_conversion.ConvertSpec`

   .. attribute:: DISPLAY_NAME
      :annotation: = duration

      

   .. attribute:: RETURN_TYPE
      

      


.. py:class:: FloatConvertSpec

   Bases: :class:`spinetoolbox.spine_io.type_conversion.ConvertSpec`

   .. attribute:: DISPLAY_NAME
      :annotation: = float

      

   .. attribute:: RETURN_TYPE
      

      


.. py:class:: StringConvertSpec

   Bases: :class:`spinetoolbox.spine_io.type_conversion.ConvertSpec`

   .. attribute:: DISPLAY_NAME
      :annotation: = string

      

   .. attribute:: RETURN_TYPE
      

      


.. py:class:: IntegerSequenceDateTimeConvertSpec(start_datetime, start_int, duration)

   Bases: :class:`spinetoolbox.spine_io.type_conversion.ConvertSpec`

   .. attribute:: DISPLAY_NAME
      :annotation: = integer sequence datetime

      

   .. attribute:: RETURN_TYPE
      

      

   .. method:: convert_function(self)



   .. method:: to_json_value(self)




