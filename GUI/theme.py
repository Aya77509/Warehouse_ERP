"""
Unified design system for the Warehouse ERP.
Every view imports tokens, factories and helpers from this module so the
visual language stays 100% consistent across the whole application.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QColor, QIcon
from PyQt6.QtWidgets import (
    QApplication, QStyle, QPushButton, QLabel, QFrame, QTableWidget,
    QHeaderView, QGraphicsDropShadowEffect, QWidget,
)


# ============================================================ #
#                       DESIGN TOKENS                          #
# ============================================================ #

# --- Color palette (professional enterprise light theme) ----- #
BG          = "#f4f6fa"   # app background
SURFACE     = "#ffffff"   # cards / panels
SURFACE_2   = "#f8fafc"   # nested surface (table headers, chips)
SURFACE_3   = "#eef2f7"   # hover / subtle fill
BORDER      = "#e2e8f0"   # slate-200
BORDER_STR  = "#cbd5e1"   # slate-300 (stronger)

TEXT        = "#0f172a"   # slate-900 (headings)
TEXT_BODY   = "#1e293b"   # slate-800 (body)
TEXT_MUTED  = "#64748b"   # slate-500 (subtitles)
TEXT_FAINT  = "#94a3b8"   # slate-400 (placeholders)

PRIMARY     = "#2563eb"   # blue-600 (single brand color)
PRIMARY_DK  = "#1d4ed8"   # blue-700 (hover)
PRIMARY_SOFT = "#dbeafe"  # blue-100 (chips / selection)

SUCCESS     = "#16a34a"   # green-600
SUCCESS_DK  = "#15803d"
SUCCESS_SOFT = "#dcfce7"

WARNING     = "#d97706"   # amber-600
WARNING_DK  = "#ce6b20"
WARNING_SOFT = "#fef3c7"

DANGER      = "#dc2626"   # red-600
DANGER_DK   = "#b62121b1"
DANGER_SOFT = "#fee2e2"

INFO        = "#0284c7"   # sky-600
INFO_SOFT   = "#e0f2fe"

CHART_PALETTE = [PRIMARY, SUCCESS, WARNING, INFO, "#cfe0f5", DANGER]

# --- Typography ---------------------------------------------- #
FONT_FAMILY = "Helvetica"
FS_PAGE_TITLE = 23
FS_SECTION    = 15
FS_BODY       = 14
FS_SMALL      = 12
FS_MICRO      = 12

# --- Spacing & radius --------------------------------------- #
RADIUS_SM = 6
RADIUS_MD = 8
RADIUS_LG = 12
RADIUS_XL = 14

PAD_PAGE = 24
GAP_LG   = 18
GAP_MD   = 14
GAP_SM   = 10

# --- Icon sizes --------------------------------------------- #
ICON_SM = 14
ICON_MD = 16
ICON_LG = 18
ICON_XL = 22


# ============================================================ #
#                       ICON SYSTEM                            #
# ============================================================ #
# One canonical name -> one StandardPixmap, used everywhere.
# This guarantees the same icon style/weight across the app.

class Icons:
    SP = QStyle.StandardPixmap

    # Navigation
    DASHBOARD = SP.SP_ComputerIcon
    PRODUCTS  = SP.SP_FileDialogContentsView
    INVENTORY = SP.SP_DriveHDIcon
    SUPPLIERS = SP.SP_FileDialogDetailedView
    REPORTS   = SP.SP_FileIcon

    # Actions
    ADD       = SP.SP_FileDialogNewFolder
    EDIT      = SP.SP_FileDialogDetailedView
    DELETE    = SP.SP_TrashIcon
    SAVE      = SP.SP_DialogSaveButton
    EXPORT    = SP.SP_ArrowDown  # download metaphor
    SEARCH    = SP.SP_FileDialogContentsView
    VIEW      = SP.SP_FileDialogInfoView
    LOGIN     = SP.SP_DialogOkButton
    LOGOUT    = SP.SP_DialogCloseButton

    # Stock movement
    STOCK_IN  = SP.SP_ArrowUp
    STOCK_OUT = SP.SP_ArrowDown
    HISTORY   = SP.SP_FileDialogContentsView

    # Status / alerts
    OK        = SP.SP_DialogApplyButton
    WARNING   = SP.SP_MessageBoxWarning
    DANGER    = SP.SP_MessageBoxCritical
    INFO      = SP.SP_MessageBoxInformation

    # KPI / misc
    BOX       = SP.SP_DirIcon
    STOCK     = SP.SP_DriveHDIcon
    USER      = SP.SP_DirHomeIcon
    BRAND     = SP.SP_ComputerIcon


def qicon(sp) -> QIcon:
    """Return a QIcon for any StandardPixmap value."""
    return QApplication.instance().style().standardIcon(sp)


def icon_label(sp, size: int = ICON_LG) -> QLabel:
    lbl = QLabel()
    lbl.setPixmap(qicon(sp).pixmap(QSize(size, size)))
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setStyleSheet("background: transparent;")
    return lbl


# ============================================================ #
#                       FONT HELPERS                           #
# ============================================================ #

def page_title_font() -> QFont:
    return QFont(FONT_FAMILY, FS_PAGE_TITLE, QFont.Weight.Bold)

def section_font() -> QFont:
    return QFont(FONT_FAMILY, FS_SECTION, QFont.Weight.DemiBold)


# ============================================================ #
#                    GLOBAL STYLESHEET                         #
# ============================================================ #
# Apply once on the QApplication so EVERY widget inherits the
# same baseline (fonts, scrollbars, tooltips, message boxes…).

def global_stylesheet() -> str:
    return f"""
        * {{ font-family: "{FONT_FAMILY}"; font-size: {FS_BODY}px; color: {TEXT_BODY}; }}
        QWidget        {{ background-color: {BG}; }}
        QToolTip       {{ background-color: {TEXT}; color: white;
                          border: 1px solid {TEXT}; padding: 6px 8px;
                          border-radius: {RADIUS_SM}px; font-size: {FS_SMALL}px; }}
        QScrollBar:vertical, QScrollBar:horizontal {{
            background: transparent; border: none; width: 10px; height: 10px; margin: 2px;
        }}
        QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
            background: {BORDER_STR}; border-radius: 5px; min-height: 30px; min-width: 30px;
        }}
        QScrollBar::handle:hover {{ background: {TEXT_MUTED}; }}
        QScrollBar::add-line, QScrollBar::sub-line {{ background: none; border: none; height: 0; width: 0; }}
        QMessageBox    {{ background-color: {SURFACE}; }}
        QMessageBox QLabel {{ color: {TEXT_BODY}; font-size: {FS_BODY}px; }}
        QMenu          {{ background-color: {SURFACE}; border: 1px solid {BORDER};
                          border-radius: {RADIUS_MD}px; padding: 4px; }}
        QMenu::item    {{ padding: 6px 14px; border-radius: {RADIUS_SM}px; }}
        QMenu::item:selected {{ background-color: {PRIMARY_SOFT}; color: {PRIMARY_DK}; }}
    """


# ============================================================ #
#                    WIDGET FACTORIES                          #
# ============================================================ #

def primary_button(text: str, sp=None, variant: str = "primary") -> QPushButton:
    """
    Standard button — all CTAs in the app go through this.
    variant: primary | success | danger | warning | ghost | secondary
    """
    palette = {
        "primary":   (PRIMARY,   PRIMARY_DK,  "white"),
        "success":   (SUCCESS,   SUCCESS_DK,  "white"),
        "danger":    (DANGER,    DANGER_DK,   "white"),
        "warning":   (WARNING,   WARNING_DK,  "white"),
        "secondary": (SURFACE,   SURFACE_3,   TEXT_BODY),
        "ghost":     ("transparent", SURFACE_3, TEXT_MUTED),
    }
    bg, hover, fg = palette.get(variant, palette["primary"])
    border = f"1px solid {BORDER}" if variant in ("secondary", "ghost") else "none"

    btn = QPushButton(("  " + text) if sp is not None else text)
    if sp is not None:
        btn.setIcon(qicon(sp))
        btn.setIconSize(QSize(ICON_MD, ICON_MD))
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setMinimumHeight(36)
    btn.setStyleSheet(f"""
        QPushButton {{
            background-color: {bg}; color: {fg};
            border: {border}; border-radius: {RADIUS_MD}px;
            padding: 8px 16px; font-weight: 600; font-size: {FS_BODY}px;
        }}
        QPushButton:hover    {{ background-color: {hover}; }}
        QPushButton:disabled {{ background-color: {SURFACE_3}; color: {TEXT_FAINT}; }}
    """)
    return btn


def input_style() -> str:
    """Shared style for QLineEdit / QComboBox / QSpinBox / QDateEdit."""
    return f"""
        QLineEdit, QComboBox, QSpinBox, QDateEdit {{
            background-color: {SURFACE};
            color: {TEXT_BODY};
            border: 1px solid {BORDER};
            border-radius: {RADIUS_MD}px;
            padding: 9px 12px;
            font-size: {FS_BODY}px;
            min-height: 18px;
        }}
        QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDateEdit:focus {{
            border: 1.5px solid {PRIMARY};
            background-color: {SURFACE};
        }}
        QLineEdit::placeholder {{ color: {TEXT_FAINT}; }}
        QComboBox::drop-down {{ border: none; width: 22px; }}
        QComboBox QAbstractItemView {{
            background: {SURFACE}; color: {TEXT_BODY};
            border: 1px solid {BORDER}; border-radius: {RADIUS_MD}px;
            selection-background-color: {PRIMARY_SOFT};
            selection-color: {PRIMARY_DK};
            padding: 4px;
        }}
    """


def card_frame(padding: int = 18) -> QFrame:
    """A unified surface card with soft shadow + rounded corners."""
    f = QFrame()
    f.setObjectName("Card")
    f.setStyleSheet(f"""
        QFrame#Card {{
            background-color: {SURFACE};
            border: 1px solid {BORDER};
            border-radius: {RADIUS_XL}px;
        }}
    """)
    shadow = QGraphicsDropShadowEffect(f)
    shadow.setBlurRadius(18); shadow.setOffset(0, 2)
    shadow.setColor(QColor(15, 23, 42, 18))
    f.setGraphicsEffect(shadow)
    f.setContentsMargins(padding, padding, padding, padding)
    return f


def style_table(table: QTableWidget):
    """Single consistent style + behavior for every table in the app."""
    table.setStyleSheet(f"""
        QTableWidget {{
            background-color: {SURFACE};
            color: {TEXT_BODY};
            border: 1px solid {BORDER};
            border-radius: {RADIUS_LG}px;
            gridline-color: transparent;
            selection-background-color: {PRIMARY_SOFT};
            selection-color: {TEXT};
            font-size: {FS_BODY}px;
        }}
        QHeaderView::section {{
            background-color: {SURFACE_2};
            color: {TEXT_MUTED};
            padding: 10px 12px;
            border: none;
            border-bottom: 1px solid {BORDER};
            font-weight: 700;
            font-size: {FS_MICRO}px;
            text-transform: uppercase;
            letter-spacing: 0.6px;
        }}
        QTableWidget::item {{
            padding: 10px 12px;
            border-bottom: 1px solid {BORDER};
        }}
        QTableWidget::item:selected {{
            background-color: {PRIMARY_SOFT}; color: {TEXT};
        }}
    """)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    table.horizontalHeader().setHighlightSections(False)
    table.verticalHeader().setVisible(False)
    table.setShowGrid(False)
    table.setAlternatingRowColors(False)
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    table.verticalHeader().setDefaultSectionSize(42)


def status_badge(text: str, variant: str = "info") -> QLabel:
    """Pill-shaped status badge — use it everywhere instead of colored text."""
    palette = {
        "success": (SUCCESS_SOFT, SUCCESS_DK),
        "warning": (WARNING_SOFT, WARNING_DK),
        "danger":  (DANGER_SOFT,  DANGER_DK),
        "info":    (INFO_SOFT,    INFO),
        "neutral": (SURFACE_3,    TEXT_MUTED),
        "primary": (PRIMARY_SOFT, PRIMARY_DK),
    }
    bg, fg = palette.get(variant, palette["info"])
    lbl = QLabel(text)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setStyleSheet(f"""
        background-color: {bg};
        color: {fg};
        border-radius: 10px;
        padding: 3px 10px;
        font-size: {FS_MICRO}px;
        font-weight: 700;
        letter-spacing: 0.4px;
    """)
    return lbl


def page_header(title: str, subtitle: str = "") -> QWidget:
    """Standard page header used by every view."""
    from PyQt6.QtWidgets import QVBoxLayout
    w = QWidget()
    w.setStyleSheet("background: transparent;")
    lay = QVBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(2)
    t = QLabel(title); t.setFont(page_title_font())
    t.setStyleSheet(f"color: {TEXT}; background: transparent;")
    lay.addWidget(t)
    if subtitle:
        s = QLabel(subtitle)
        s.setStyleSheet(f"color: {TEXT_MUTED}; font-size: {FS_SMALL}px; background: transparent;")
        lay.addWidget(s)
    return w
