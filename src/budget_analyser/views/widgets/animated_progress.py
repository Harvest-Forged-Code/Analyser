"""Animated progress bar widget.

Provides smooth value transitions for progress indicators.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QProgressBar
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, Property

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

# Animation duration for progress value changes
PROGRESS_ANIMATION_DURATION = 300


class AnimatedProgressBar(QProgressBar):
    """Progress bar with animated value transitions.

    Smoothly animates between values instead of jumping directly,
    providing a more polished user experience.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize animated progress bar.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self._animation: QPropertyAnimation | None = None
        self._target_value = 0

    def setValueAnimated(
        self,
        value: int,
        *,
        duration: int = PROGRESS_ANIMATION_DURATION,
    ) -> None:
        """Set progress value with smooth animation.

        Args:
            value: Target progress value (0-100)
            duration: Animation duration in milliseconds
        """
        # Clamp value to valid range
        value = max(self.minimum(), min(value, self.maximum()))

        # Skip animation if value hasn't changed
        if value == self._target_value and value == self.value():
            return

        self._target_value = value

        # Stop any existing animation
        if self._animation is not None:
            self._animation.stop()

        # Create and start new animation
        self._animation = QPropertyAnimation(self, b"value")
        self._animation.setDuration(duration)
        self._animation.setStartValue(self.value())
        self._animation.setEndValue(value)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._animation.start()

    def setValueInstant(self, value: int) -> None:
        """Set progress value immediately without animation.

        Args:
            value: Progress value (0-100)
        """
        # Stop any running animation
        if self._animation is not None:
            self._animation.stop()

        self._target_value = value
        self.setValue(value)

    def targetValue(self) -> int:
        """Get the target value (may differ from current during animation).

        Returns:
            Target progress value
        """
        return self._target_value


class AnimatedPercentageBar(AnimatedProgressBar):
    """Animated progress bar optimized for percentage display.

    Pre-configured with 0-100 range and percentage formatting.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize percentage progress bar.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setMinimum(0)
        self.setMaximum(100)
        self.setTextVisible(False)  # Hide default text, use custom label

    def setPercentage(self, percentage: float, *, animated: bool = True) -> None:
        """Set progress as a percentage.

        Args:
            percentage: Percentage value (0.0 - 100.0+)
            animated: Whether to animate the transition
        """
        # Cap at 100 for display but track actual value
        display_value = min(int(percentage), 100)

        if animated:
            self.setValueAnimated(display_value)
        else:
            self.setValueInstant(display_value)
