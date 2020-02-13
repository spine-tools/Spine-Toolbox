:mod:`spinetoolbox.widgets.notification`
========================================

.. py:module:: spinetoolbox.widgets.notification

.. autoapi-nested-parse::

   Contains a notification widget.

   :author: P. Savolainen (VTT)
   :date: 12.12.2019



Module Contents
---------------

.. py:class:: Notification(parent, txt, anim_duration=500, life_span=2000)

   Bases: :class:`PySide2.QtWidgets.QWidget`

   Custom pop-up notification widget with fade-in and fade-out effect.

   :param parent: Parent widget
   :type parent: QWidget
   :param txt: Text to display in notification
   :type txt: str
   :param anim_duration: Duration of the animation in msecs
   :type anim_duration: int
   :param life_span: How long does the notification stays in place in msecs
   :type life_span: int

   .. attribute:: opacity
      

      

   .. method:: show(self)



   .. method:: get_opacity(self)


      opacity getter.


   .. method:: set_opacity(self, op)


      opacity setter.


   .. method:: update_opacity(self, value)


      Updates graphics effect opacity.


   .. method:: start_self_destruction(self)


      Starts fade-out animation and closing of the notification.


   .. method:: enterEvent(self, e)



   .. method:: remaining_time(self)




.. py:class:: NotificationStack(parent, anim_duration=500, life_span=2000)

   Bases: :class:`PySide2.QtCore.QObject`

   .. method:: push(self, txt)


      Pushes a notification to the stack with the given text.


   .. method:: handle_notification_destroyed(self, notification, height)


      Removes from the stack the given notification and move up
      subsequent ones.



