:mod:`spinetoolbox.project_items.shared.import_export_animation`
================================================================

.. py:module:: spinetoolbox.project_items.shared.import_export_animation

.. autoapi-nested-parse::

   Animation class for the Exporter and Importer items.

   :authors: M. Marin (KTH)
   :date:   12.11.2019



Module Contents
---------------

.. py:class:: ImportExportAnimation(parent_item, src_item, dst_item, duration=2000)

   Initializes animation stuff.

   :param parent_item: The item on top of which the animation should play.
   :type parent_item: QGraphicsItem
   :param src_item: The source item.
   :type src_item: QGraphicsItem
   :param dst_item: The destination item.
   :type dst_item: QGraphicsItem
   :param duration: The desired duration of each loop in milliseconds, defaults to 1000.
   :type duration: int. optional

   .. method:: _handle_timer_value_changed(self, value)



   .. method:: start(self)


      Starts the animation.


   .. method:: stop(self)


      Stops the animation



