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

"""Contains a notification widget."""
from PySide6.QtWidgets import QFrame, QLabel, QHBoxLayout, QGraphicsOpacityEffect, QLayout, QSizePolicy, QPushButton
from PySide6.QtCore import Qt, Slot, QTimer, QPropertyAnimation, Property, QObject
from PySide6.QtGui import QFont, QColor
from spinetoolbox.helpers import color_from_index


class Notification(QFrame):
    """Custom pop-up notification widget with fade-in and fade-out effect."""

    _FADE_IN_OUT_DURATION = 500

    def __init__(
        self, parent, txt, anim_duration=_FADE_IN_OUT_DURATION, life_span=None, word_wrap=True, corner=Qt.TopRightCorner
    ):
        """

        Args:
            parent (QWidget): Parent widget
            txt (str): Text to display in notification
            anim_duration (int): Duration of the animation in msecs
            life_span (int): How long does the notification stays in place in msecs
            word_wrap (bool)
            corner (Qt.Corner)
        """
        super().__init__()
        if life_span is None:
            word_count = len(txt.split(" "))
            mspw = 60000 / 140  # Assume people can read ~140 words per minute
            life_span = mspw * word_count
        self.setFocusPolicy(Qt.NoFocus)
        self.setWindowFlags(Qt.WindowType.Popup)
        self.setParent(parent)
        self._parent = parent
        self._corner = corner
        self.label = QLabel(txt)
        self.label.setMaximumSize(parent.size())
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setWordWrap(word_wrap)
        self.label.setMargin(8)
        self.label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        font = QFont()
        font.setBold(True)
        self.label.setFont(font)
        layout = QHBoxLayout()
        layout.addWidget(self.label)
        layout.setSizeConstraint(QLayout.SetMinimumSize)
        layout.setContentsMargins(3, 3, 3, 3)
        self.setLayout(layout)
        self.adjustSize()
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setObjectName("Notification")
        self._background_color = "#e6ffc2b3"
        ss = (
            "QFrame#Notification{"
            f"background-color: {self._background_color};"
            "border-width: 2px;"
            "border-color: #ffebe6;"
            "border-style: groove; border-radius: 8px;}"
        )
        self.setStyleSheet(ss)
        self.setAcceptDrops(True)
        self.effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.effect)
        self.effect.setOpacity(0.0)
        self._opacity = 0.0
        self.timer = QTimer(self)
        self.timer.setInterval(life_span)
        self.timer.timeout.connect(self.start_self_destruction)
        # Fade in animation
        self.fade_in_anim = QPropertyAnimation(self, b"opacity")
        self.fade_in_anim.setDuration(anim_duration)
        self.fade_in_anim.setStartValue(0.0)
        self.fade_in_anim.setEndValue(1.0)
        self.fade_in_anim.valueChanged.connect(self.update_opacity)
        self.fade_in_anim.finished.connect(self.timer.start)
        # Fade out animation
        self.fade_out_anim = QPropertyAnimation(self, b"opacity")
        self.fade_out_anim.setDuration(anim_duration)
        self.fade_out_anim.setStartValue(1.0)
        self.fade_out_anim.setEndValue(0)
        self.fade_out_anim.valueChanged.connect(self.update_opacity)
        self.fade_out_anim.finished.connect(self.close)
        # Start fade in animation
        self.fade_in_anim.start(QPropertyAnimation.DeleteWhenStopped)

    def show(self):
        """Shows widget and moves it to the selected corner of the parent widget."""
        super().show()
        if self._corner in (Qt.TopRightCorner, Qt.BottomRightCorner):
            x = self._parent.size().width() - self.width() - 2
        else:
            x = self.pos().x()
        if self._corner in (Qt.BottomLeftCorner, Qt.BottomRightCorner):
            y = self._parent.size().height() - self.height() - 2
        else:
            y = self.pos().y()
        self.move(x, y)

    def get_opacity(self):
        """opacity getter."""
        return self._opacity

    def set_opacity(self, op):
        """opacity setter."""
        self._opacity = op

    @Slot(float)
    def update_opacity(self, value):
        """Updates graphics effect opacity."""
        self.effect.setOpacity(value)

    def start_self_destruction(self):
        """Starts fade-out animation and closing of the notification."""
        self.fade_out_anim.start(QPropertyAnimation.DeleteWhenStopped)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def enterEvent(self, e):
        """Pauses timer as the mouse hovers the notification."""
        super().enterEvent(e)
        if self.remaining_time():
            self.timer.stop()

    def leaveEvent(self, e):
        """Starts self destruction after the mouse leaves the notification."""
        super().leaveEvent(e)
        self.start_self_destruction()

    def remaining_time(self):
        if self.timer.isActive():
            return self.timer.remainingTime()
        if self.fade_out_anim.state() == QPropertyAnimation.Running:
            return 0
        return self.timer.interval()

    opacity = Property(float, get_opacity, set_opacity)


class ButtonNotification(Notification):
    """A notification with a button."""

    def __init__(self, *args, button_text="", button_slot=None, **kwargs):
        super().__init__(*args, **kwargs)
        button = QPushButton(button_text, self)
        self.layout().addWidget(button)
        button.clicked.connect(button_slot)
        button.clicked.connect(self.start_self_destruction)
        # Style button: We try hard to programmatically find good contrasting colors
        label_bg_color = QColor(self._background_color)
        base_hue = label_bg_color.hsvHueF()
        saturation = label_bg_color.hsvSaturationF()
        bg_color = color_from_index(1, 2, base_hue=base_hue, saturation=saturation)
        pressed_bg_color = bg_color.darker(110)
        hover_bg_color = bg_color.lighter(110)
        border_color = QColor("#F0F0F0")
        pressed_border_color = border_color.darker(110)
        ss = (
            "QPushButton{"
            f"background-color: {bg_color.name()}; color: #0F0F0F; "
            f"border: 2px solid {border_color.name()}; border-style: groove; border-radius: 4px;}}"
            f"QPushButton:hover{{background-color: {hover_bg_color.name()};}}"
            f"QPushButton:pressed{{background-color: {pressed_bg_color.name()};"
            f"border: 2px solid {pressed_border_color.name()};}}"
        )
        button.setStyleSheet(ss)
        font = QFont()
        font.setBold(True)
        button.setFont(font)


class LinkNotification(Notification):
    """A notification that may have a link."""

    def __init__(self, *args, open_link=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        if open_link is None:
            self.label.setOpenExternalLinks(True)
        else:
            self.label.linkActivated.connect(open_link)


class ChangeNotifier(QObject):
    _ANIMATION_LIFE_SPAN = 5000

    def __init__(self, parent, undo_stack, settings, settings_key, corner=Qt.BottomRightCorner):
        """
        Args:
            parent (QWidget)
            undo_stack (QUndoStack)
            settings (QSettings)
            settings_key (str)
            corner (int)
        """
        super().__init__(undo_stack)
        self._undo_stack = undo_stack
        self._settings = settings
        self._settings_key = settings_key
        self._parent = parent
        self._corner = corner
        self._notification = None
        self._undo_stack.indexChanged.connect(self._push_notification)
        self._notified_commands = set()

    @Slot(int)
    def _push_notification(self, index):
        if self._settings.value(self._settings_key, defaultValue="2") != "2":
            return
        if self._notification is not None:
            try:
                self._notification.start_self_destruction()
            except RuntimeError:
                # Already destroyed
                pass
        try:
            cmd = self._undo_stack.command(index)
        except RuntimeError:
            return
        if cmd is not None or index == 0:
            return
        cmd = self._undo_stack.command(index - 1)
        if cmd in self._notified_commands:
            return
        self._notified_commands.add(cmd)
        notification_text = cmd.actionText() + " successful"
        button_text = "undo"
        button_slot = self._undo_stack.undo
        self._notification = ButtonNotification(
            self._parent,
            notification_text,
            life_span=self._ANIMATION_LIFE_SPAN,
            word_wrap=False,
            corner=self._corner,
            button_text=button_text,
            button_slot=button_slot,
        )
        self._notification.show()

    def tear_down(self):
        """Tears down the notifier."""
        self._undo_stack.indexChanged.disconnect(self._push_notification)
