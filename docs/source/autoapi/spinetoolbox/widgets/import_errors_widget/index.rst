:mod:`spinetoolbox.widgets.import_errors_widget`
================================================

.. py:module:: spinetoolbox.widgets.import_errors_widget

.. autoapi-nested-parse::

   Contains ImportErrorWidget class.

   :author: P. Vennström (VTT)
   :date:   1.6.2019



Module Contents
---------------

.. py:class:: ImportErrorWidget(parent=None)

   Bases: :class:`PySide2.QtWidgets.QWidget`

   Widget to display errors while importing and ask user for action.

   .. method:: set_import_state(self, num_imported, errors)


      Sets state of error widget.

      :param num_imported {int} -- number of successfully imported items:
      :param errors {list} -- list of errors.:



