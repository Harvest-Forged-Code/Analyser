"""Animation utilities for the views layer.

Provides consistent animation helpers for UI transitions and effects.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import (
    QPropertyAnimation,
    QEasingCurve,
    QObject,
    Property,
    QParallelAnimationGroup,
    QSequentialAnimationGroup,
)
from PySide6.QtWidgets import QGraphicsOpacityEffect, QGraphicsDropShadowEffect
from PySide6.QtGui import QColor

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget


# Animation timing constants (in milliseconds)
DURATION_INSTANT = 50
DURATION_FAST = 150
DURATION_NORMAL = 250
DURATION_SLOW = 400
DURATION_PROGRESS = 300

# Easing curves
EASE_OUT_CUBIC = QEasingCurve.Type.OutCubic
EASE_IN_OUT_CUBIC = QEasingCurve.Type.InOutCubic
EASE_OUT_QUAD = QEasingCurve.Type.OutQuad
EASE_OUT_EXPO = QEasingCurve.Type.OutExpo


class AnimationHelper:
    """Helper class for creating common animations."""

    @staticmethod
    def fade_in(
        widget: QWidget,
        *,
        duration: int = DURATION_NORMAL,
        start_opacity: float = 0.0,
        end_opacity: float = 1.0,
    ) -> QPropertyAnimation:
        """Create a fade-in animation for a widget.

        Args:
            widget: Widget to animate
            duration: Animation duration in milliseconds
            start_opacity: Starting opacity (0.0 - 1.0)
            end_opacity: Ending opacity (0.0 - 1.0)

        Returns:
            QPropertyAnimation instance (call start() to run)
        """
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)

        animation = QPropertyAnimation(effect, b"opacity")
        animation.setDuration(duration)
        animation.setStartValue(start_opacity)
        animation.setEndValue(end_opacity)
        animation.setEasingCurve(EASE_OUT_CUBIC)

        return animation

    @staticmethod
    def fade_out(
        widget: QWidget,
        *,
        duration: int = DURATION_NORMAL,
    ) -> QPropertyAnimation:
        """Create a fade-out animation for a widget.

        Args:
            widget: Widget to animate
            duration: Animation duration in milliseconds

        Returns:
            QPropertyAnimation instance (call start() to run)
        """
        return AnimationHelper.fade_in(
            widget,
            duration=duration,
            start_opacity=1.0,
            end_opacity=0.0,
        )

    @staticmethod
    def pulse(
        widget: QWidget,
        *,
        duration: int = DURATION_SLOW,
        min_opacity: float = 0.7,
        max_opacity: float = 1.0,
    ) -> QSequentialAnimationGroup:
        """Create a pulse animation (fade in/out loop).

        Args:
            widget: Widget to animate
            duration: Total duration for one pulse cycle
            min_opacity: Minimum opacity
            max_opacity: Maximum opacity

        Returns:
            QSequentialAnimationGroup instance (call start() to run)
        """
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)

        half_duration = duration // 2

        fade_out = QPropertyAnimation(effect, b"opacity")
        fade_out.setDuration(half_duration)
        fade_out.setStartValue(max_opacity)
        fade_out.setEndValue(min_opacity)
        fade_out.setEasingCurve(EASE_IN_OUT_CUBIC)

        fade_in = QPropertyAnimation(effect, b"opacity")
        fade_in.setDuration(half_duration)
        fade_in.setStartValue(min_opacity)
        fade_in.setEndValue(max_opacity)
        fade_in.setEasingCurve(EASE_IN_OUT_CUBIC)

        group = QSequentialAnimationGroup()
        group.addAnimation(fade_out)
        group.addAnimation(fade_in)

        return group


class ShadowAnimator(QObject):
    """Animator for QGraphicsDropShadowEffect properties.

    Enables smooth shadow transitions for hover effects.
    """

    def __init__(
        self,
        shadow_effect: QGraphicsDropShadowEffect,
        parent: QObject | None = None,
    ) -> None:
        """Initialize shadow animator.

        Args:
            shadow_effect: The shadow effect to animate
            parent: Parent QObject
        """
        super().__init__(parent)
        self._shadow = shadow_effect
        self._blur_radius = shadow_effect.blurRadius()
        self._y_offset = shadow_effect.yOffset()

    def _get_blur_radius(self) -> float:
        return self._blur_radius

    def _set_blur_radius(self, value: float) -> None:
        self._blur_radius = value
        self._shadow.setBlurRadius(value)

    def _get_y_offset(self) -> float:
        return self._y_offset

    def _set_y_offset(self, value: float) -> None:
        self._y_offset = value
        self._shadow.setYOffset(value)

    blur_radius = Property(float, _get_blur_radius, _set_blur_radius)
    y_offset = Property(float, _get_y_offset, _set_y_offset)

    def animate_hover_enter(
        self,
        *,
        target_blur: float = 28.0,
        target_offset: float = 8.0,
        duration: int = DURATION_FAST,
    ) -> QParallelAnimationGroup:
        """Create hover enter animation (elevate shadow).

        Args:
            target_blur: Target blur radius
            target_offset: Target Y offset
            duration: Animation duration

        Returns:
            QParallelAnimationGroup instance
        """
        blur_anim = QPropertyAnimation(self, b"blur_radius")
        blur_anim.setDuration(duration)
        blur_anim.setEndValue(target_blur)
        blur_anim.setEasingCurve(EASE_OUT_CUBIC)

        offset_anim = QPropertyAnimation(self, b"y_offset")
        offset_anim.setDuration(duration)
        offset_anim.setEndValue(target_offset)
        offset_anim.setEasingCurve(EASE_OUT_CUBIC)

        group = QParallelAnimationGroup()
        group.addAnimation(blur_anim)
        group.addAnimation(offset_anim)

        return group

    def animate_hover_leave(
        self,
        *,
        target_blur: float = 20.0,
        target_offset: float = 4.0,
        duration: int = DURATION_FAST,
    ) -> QParallelAnimationGroup:
        """Create hover leave animation (lower shadow).

        Args:
            target_blur: Target blur radius
            target_offset: Target Y offset
            duration: Animation duration

        Returns:
            QParallelAnimationGroup instance
        """
        return self.animate_hover_enter(
            target_blur=target_blur,
            target_offset=target_offset,
            duration=duration,
        )


def create_card_shadow(
    *,
    blur_radius: float = 20.0,
    x_offset: float = 0.0,
    y_offset: float = 4.0,
    color: str = "rgba(0, 0, 0, 0.15)",
) -> QGraphicsDropShadowEffect:
    """Create a standard card shadow effect.

    Args:
        blur_radius: Shadow blur radius
        x_offset: Horizontal shadow offset
        y_offset: Vertical shadow offset
        color: Shadow color (supports rgba)

    Returns:
        Configured QGraphicsDropShadowEffect
    """
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur_radius)
    shadow.setXOffset(x_offset)
    shadow.setYOffset(y_offset)

    # Parse color
    if color.startswith("rgba"):
        # Parse rgba(r, g, b, a) format
        parts = color.replace("rgba(", "").replace(")", "").split(",")
        if len(parts) == 4:
            r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
            a = int(float(parts[3].strip()) * 255)
            shadow.setColor(QColor(r, g, b, a))
    else:
        shadow.setColor(QColor(color))

    return shadow
