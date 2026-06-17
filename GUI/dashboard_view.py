"""
Modern, professional Dashboard view for the warehouse app.

Drop-in replacement for the previous DashboardView. Same public API:
    DashboardView(product_service, inventory_service)
    .refresh()

Enhancements:
- Professional palette (deep navy / slate / blue accents, green & orange status).
- KPI cards with icon, value, label, and trend delta vs. previous snapshot.
- Charts (PyQt6.QtCharts):
    * Stock movement line chart (IN vs OUT over recent days)
    * Stock by category donut chart
    * Top products bar chart
- Alerts panel with severity-coded rows (low stock + expiring).
- Recent movements + low stock tables, restyled.
- Live status pill in the header.
- Graceful fallback if PyQt6-Charts isn't installed (charts replaced by
  clean placeholder panels — the rest of the dashboard still works).
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Iterable

from PyQt6.QtCore import Qt, QTimer, QMargins, QDateTime
from PyQt6.QtGui import QFont, QColor, QPainter, QPalette
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QSizePolicy,
    QScrollArea, QProgressBar,
)

# Optional charts — degrade gracefully if PyQt6-Charts isn't installed.
try:
    from PyQt6.QtCharts import (
        QChart, QChartView, QLineSeries, QValueAxis, QDateTimeAxis,
        QPieSeries, QBarSeries, QBarSet, QBarCategoryAxis,
    )
    _CHARTS_OK = True
except Exception:  # pragma: no cover
    _CHARTS_OK = False

from Kernel.product_service import ProductService
from Kernel.inventory_service import InventoryService


# ----------------------------- Design tokens ----------------------------- #
BG          = "#0f172a"   # app background (slate-900)
SURFACE     = "#1e293b"   # card background (slate-800)
SURFACE_2   = "#273449"   # nested surface
BORDER      = "#334155"   # slate-700
TEXT        = "#f1f5f9"   # slate-100
TEXT_MUTED  = "#94a3b8"   # slate-400
PRIMARY     = "#3b82f6"   # blue-500
PRIMARY_2   = "#60a5fa"   # blue-400
SUCCESS     = "#22c55e"
WARNING     = "#f59e0b"
DANGER      = "#ef4444"
INFO        = "#06b6d4"
PURPLE      = "#8b5cf6"

CHART_PALETTE = [PRIMARY, SUCCESS, WARNING, DANGER, PURPLE, INFO]


# ------------------------------- Widgets -------------------------------- #
class KpiCard(QFrame):
    """Modern KPI card: icon chip, big value, label, and trend delta."""

    def __init__(self, title: str, icon: str, accent: str):
        super().__init__()
        self.accent = accent
        self.setObjectName("KpiCard")
        self.setStyleSheet(f"""
            QFrame#KpiCard {{
                background-color: {SURFACE};
                border: 1px solid {BORDER};
                border-radius: 14px;
            }}
        """)
        self.setMinimumHeight(120)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(8)

        top = QHBoxLayout()
        top.setSpacing(10)

        chip = QLabel(icon)
        chip.setFixedSize(36, 36)
        chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chip.setStyleSheet(f"""
            background-color: {accent}22;
            color: {accent};
            border-radius: 10px;
            font-size: 18px;
        """)
        top.addWidget(chip)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; letter-spacing: 0.5px;")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        top.addWidget(title_lbl, 1)

        self.trend_lbl = QLabel("")
        self.trend_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; font-weight: 600;")
        top.addWidget(self.trend_lbl, 0, Qt.AlignmentFlag.AlignRight)
        root.addLayout(top)

        self.value_lbl = QLabel("0")
        self.value_lbl.setFont(QFont("Segoe UI", 26, QFont.Weight.Bold))
        self.value_lbl.setStyleSheet(f"color: {TEXT};")
        root.addWidget(self.value_lbl)

        self.sub_lbl = QLabel("")
        self.sub_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        root.addWidget(self.sub_lbl)

        self._prev_value: float | None = None

    def set_value(self, value, subtitle: str = ""):
        try:
            num = float(value)
        except (TypeError, ValueError):
            num = None

        self.value_lbl.setText(str(value))
        self.sub_lbl.setText(subtitle)

        if num is not None and self._prev_value is not None and self._prev_value != 0:
            delta = num - self._prev_value
            pct = (delta / self._prev_value) * 100
            arrow = "▲" if delta > 0 else ("▼" if delta < 0 else "■")
            color = SUCCESS if delta > 0 else (DANGER if delta < 0 else TEXT_MUTED)
            self.trend_lbl.setText(f"{arrow} {abs(pct):.1f}%")
            self.trend_lbl.setStyleSheet(f"color: {color}; font-size: 11px; font-weight: 600;")
        if num is not None:
            self._prev_value = num


class SectionCard(QFrame):
    """Reusable titled card container."""

    def __init__(self, title: str, subtitle: str = ""):
        super().__init__()
        self.setObjectName("SectionCard")
        self.setStyleSheet(f"""
            QFrame#SectionCard {{
                background-color: {SURFACE};
                border: 1px solid {BORDER};
                border-radius: 14px;
            }}
        """)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(18, 16, 18, 16)
        self._root.setSpacing(10)

        header = QVBoxLayout()
        header.setSpacing(2)
        t = QLabel(title)
        t.setStyleSheet(f"color: {TEXT}; font-size: 14px; font-weight: 700;")
        header.addWidget(t)
        if subtitle:
            s = QLabel(subtitle)
            s.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
            header.addWidget(s)
        self._root.addLayout(header)

    def body(self) -> QVBoxLayout:
        return self._root


class AlertRow(QFrame):
    """Color-coded alert row."""

    def __init__(self, icon: str, title: str, detail: str, severity: str = "warning"):
        super().__init__()
        color = {"danger": DANGER, "warning": WARNING, "info": INFO, "success": SUCCESS}.get(severity, WARNING)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {color}14;
                border-left: 3px solid {color};
                border-radius: 8px;
            }}
            QLabel {{ background: transparent; }}
        """)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(10)

        ic = QLabel(icon)
        ic.setStyleSheet(f"color: {color}; font-size: 16px;")
        lay.addWidget(ic)

        box = QVBoxLayout()
        box.setSpacing(2)
        t = QLabel(title)
        t.setStyleSheet(f"color: {TEXT}; font-size: 12px; font-weight: 600;")
        d = QLabel(detail)
        d.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        box.addWidget(t)
        box.addWidget(d)
        lay.addLayout(box, 1)


# ------------------------------ Main view ------------------------------- #
class DashboardView(QWidget):
    """Modern dashboard: KPIs, charts, alerts, low stock, recent movements."""

    def __init__(self, product_service: ProductService, inventory_service: InventoryService):
        super().__init__()
        self.product_service = product_service
        self.inventory_service = inventory_service
        self._alert_shown_this_session = False

        self.setStyleSheet(f"background-color: {BG};")
        self._build_ui()
        self.refresh()

        # Auto-refresh every 30s (lightweight; safe to remove).
        self._timer = QTimer(self)
        self._timer.setInterval(30_000)
        self._timer.timeout.connect(self.refresh)
        self._timer.start()

    # ---------- UI ---------- #
    def _build_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")

        container = QWidget()
        container.setStyleSheet(f"background-color: {BG};")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        scroll.setWidget(container)

        root = QVBoxLayout(container)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(18)

        # ---- Header ----
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        h = QLabel("Warehouse Dashboard")
        h.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        h.setStyleSheet(f"color: {TEXT};")
        sub = QLabel("Real-time overview of stock, movements, and alerts")
        sub.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        title_box.addWidget(h)
        title_box.addWidget(sub)
        header.addLayout(title_box, 1)

        live = QLabel("●  LIVE")
        live.setStyleSheet(f"""
            color: {SUCCESS};
            background-color: {SUCCESS}1f;
            border: 1px solid {SUCCESS}55;
            border-radius: 999px;
            padding: 6px 12px;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 1px;
        """)
        header.addWidget(live, 0, Qt.AlignmentFlag.AlignTop)

        self.updated_lbl = QLabel("")
        self.updated_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; padding-left: 10px;")
        header.addWidget(self.updated_lbl, 0, Qt.AlignmentFlag.AlignTop)
        root.addLayout(header)

        # ---- KPI cards ----
        kpis = QGridLayout()
        kpis.setSpacing(14)
        self.card_products  = KpiCard("Total Products", "📦", PRIMARY)
        self.card_stock     = KpiCard("Total Stock Units", "🏷", SUCCESS)
        self.card_low       = KpiCard("Low Stock Alerts", "⚠", WARNING)
        self.card_expiring  = KpiCard("Expiring Soon", "⏳", DANGER)
        for i, c in enumerate((self.card_products, self.card_stock, self.card_low, self.card_expiring)):
            kpis.addWidget(c, 0, i)
            kpis.setColumnStretch(i, 1)
        root.addLayout(kpis)

        # ---- Charts row ----
        charts_row = QGridLayout()
        charts_row.setSpacing(14)

        # Movement trend
        self.movement_card = SectionCard("Stock Movements", "Incoming vs outgoing — last 7 days")
        self.movement_chart_host = QVBoxLayout()
        self.movement_card.body().addLayout(self.movement_chart_host)

        # Category donut
        self.category_card = SectionCard("Stock by Category", "Distribution across product categories")
        self.category_chart_host = QVBoxLayout()
        self.category_card.body().addLayout(self.category_chart_host)

        charts_row.addWidget(self.movement_card, 0, 0)
        charts_row.addWidget(self.category_card, 0, 1)
        charts_row.setColumnStretch(0, 2)
        charts_row.setColumnStretch(1, 1)
        root.addLayout(charts_row)

        # ---- Top products bar + Alerts ----
        mid_row = QGridLayout()
        mid_row.setSpacing(14)

        self.top_card = SectionCard("Top Products by Stock", "Highest quantity on hand")
        self.top_chart_host = QVBoxLayout()
        self.top_card.body().addLayout(self.top_chart_host)

        self.alerts_card = SectionCard("Alerts & Notifications", "Items needing attention")
        self.alerts_host = QVBoxLayout()
        self.alerts_host.setSpacing(8)
        self.alerts_card.body().addLayout(self.alerts_host)
        self.alerts_card.body().addStretch(1)

        mid_row.addWidget(self.top_card, 0, 0)
        mid_row.addWidget(self.alerts_card, 0, 1)
        mid_row.setColumnStretch(0, 2)
        mid_row.setColumnStretch(1, 1)
        root.addLayout(mid_row)

        # ---- Tables row ----
        tables_row = QGridLayout()
        tables_row.setSpacing(14)

        low_card = SectionCard("Low Stock Products", "Items below their threshold")
        self.low_stock_table = QTableWidget(0, 3)
        self.low_stock_table.setHorizontalHeaderLabels(["ID", "Product", "Qty"])
        self._style_table(self.low_stock_table)
        low_card.body().addWidget(self.low_stock_table)

        rec_card = SectionCard("Recent Movements", "Latest inventory activity")
        self.recent_table = QTableWidget(0, 4)
        self.recent_table.setHorizontalHeaderLabels(["Date", "Product", "Type", "Qty"])
        self._style_table(self.recent_table)
        rec_card.body().addWidget(self.recent_table)

        tables_row.addWidget(low_card, 0, 0)
        tables_row.addWidget(rec_card, 0, 1)
        tables_row.setColumnStretch(0, 1)
        tables_row.setColumnStretch(1, 1)
        root.addLayout(tables_row)

        root.addStretch(1)

    @staticmethod
    def _style_table(table: QTableWidget):
        table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {SURFACE_2};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 10px;
                gridline-color: {BORDER};
                selection-background-color: {PRIMARY}33;
            }}
            QHeaderView::section {{
                background-color: {SURFACE};
                color: {TEXT_MUTED};
                padding: 8px;
                border: none;
                border-bottom: 1px solid {BORDER};
                font-weight: 600;
                font-size: 11px;
                letter-spacing: 0.5px;
            }}
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {BORDER};
            }}
        """)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
        table.setAlternatingRowColors(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        table.setMinimumHeight(240)

    # ---------- Chart builders ---------- #
    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

    def _placeholder(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; padding: 30px;")
        lbl.setMinimumHeight(220)
        return lbl

    def _new_chart(self, title: str = "") -> "QChart":
        chart = QChart()
        chart.setTitle(title)
        chart.setBackgroundBrush(QColor(SURFACE))
        chart.setPlotAreaBackgroundBrush(QColor(SURFACE))
        chart.setPlotAreaBackgroundVisible(True)
        chart.setBackgroundRoundness(0)
        chart.setMargins(QMargins(0, 0, 0, 0))
        chart.legend().setLabelColor(QColor(TEXT_MUTED))
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        chart.setTitleBrush(QColor(TEXT))
        return chart

    def _chart_view(self, chart) -> "QChartView":
        view = QChartView(chart)
        view.setRenderHint(QPainter.RenderHint.Antialiasing)
        view.setStyleSheet(f"background-color: {SURFACE}; border: none;")
        view.setMinimumHeight(260)
        return view

    def _build_movement_chart(self, movements: Iterable):
        self._clear_layout(self.movement_chart_host)
        if not _CHARTS_OK:
            self.movement_chart_host.addWidget(self._placeholder("Install PyQt6-Charts to see movement trends"))
            return

        # Aggregate IN/OUT by day for last 7 days.
        today = datetime.now().date()
        days = [today - timedelta(days=i) for i in range(6, -1, -1)]
        in_by_day = defaultdict(int)
        out_by_day = defaultdict(int)
        for m in movements:
            d = self._parse_date(getattr(m, "date", None))
            if d is None or d < days[0] or d > days[-1]:
                continue
            qty = int(getattr(m, "quantity", 0) or 0)
            mtype = getattr(getattr(m, "movement_type", None), "value", "")
            if mtype == "IN":
                in_by_day[d] += qty
            elif mtype == "OUT":
                out_by_day[d] += qty

        series_in = QLineSeries(); series_in.setName("Incoming")
        series_out = QLineSeries(); series_out.setName("Outgoing")
        max_y = 1
        for d in days:
            ts = QDateTime(d.year, d.month, d.day, 0, 0).toMSecsSinceEpoch()
            series_in.append(ts, in_by_day[d])
            series_out.append(ts, out_by_day[d])
            max_y = max(max_y, in_by_day[d], out_by_day[d])

        pen_in = series_in.pen(); pen_in.setColor(QColor(SUCCESS)); pen_in.setWidth(3); series_in.setPen(pen_in)
        pen_out = series_out.pen(); pen_out.setColor(QColor(DANGER)); pen_out.setWidth(3); series_out.setPen(pen_out)

        chart = self._new_chart()
        chart.addSeries(series_in)
        chart.addSeries(series_out)

        axis_x = QDateTimeAxis()
        axis_x.setFormat("MMM dd")
        axis_x.setTickCount(7)
        axis_x.setLabelsColor(QColor(TEXT_MUTED))
        axis_x.setGridLineColor(QColor(BORDER))
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series_in.attachAxis(axis_x); series_out.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setRange(0, max_y * 1.2)
        axis_y.setLabelFormat("%d")
        axis_y.setLabelsColor(QColor(TEXT_MUTED))
        axis_y.setGridLineColor(QColor(BORDER))
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series_in.attachAxis(axis_y); series_out.attachAxis(axis_y)

        self.movement_chart_host.addWidget(self._chart_view(chart))

    def _build_category_chart(self, products):
        self._clear_layout(self.category_chart_host)
        if not _CHARTS_OK:
            self.category_chart_host.addWidget(self._placeholder("Install PyQt6-Charts to see category breakdown"))
            return

        totals = Counter()
        for p in products:
            cat = getattr(p, "category", None) or "Uncategorized"
            qty = int(getattr(p, "quantity", 0) or 0)
            totals[cat] += qty

        if not totals:
            self.category_chart_host.addWidget(self._placeholder("No category data available"))
            return

        series = QPieSeries()
        series.setHoleSize(0.55)
        for i, (cat, qty) in enumerate(totals.most_common(6)):
            slc = series.append(f"{cat} ({qty})", qty)
            slc.setBrush(QColor(CHART_PALETTE[i % len(CHART_PALETTE)]))
            slc.setBorderColor(QColor(SURFACE))
            slc.setBorderWidth(2)
            slc.setLabelColor(QColor(TEXT_MUTED))

        chart = self._new_chart()
        chart.addSeries(series)
        self.category_chart_host.addWidget(self._chart_view(chart))

    def _build_top_products_chart(self, products):
        self._clear_layout(self.top_chart_host)
        if not _CHARTS_OK:
            self.top_chart_host.addWidget(self._placeholder("Install PyQt6-Charts to see top products"))
            return

        top = sorted(products, key=lambda p: getattr(p, "quantity", 0) or 0, reverse=True)[:6]
        if not top:
            self.top_chart_host.addWidget(self._placeholder("No products to display"))
            return

        bar_set = QBarSet("Quantity")
        bar_set.setColor(QColor(PRIMARY))
        bar_set.setBorderColor(QColor(PRIMARY))
        categories = []
        for p in top:
            bar_set.append(int(getattr(p, "quantity", 0) or 0))
            name = getattr(p, "name", "?")
            categories.append(name if len(name) <= 14 else name[:13] + "…")

        series = QBarSeries()
        series.append(bar_set)
        series.setLabelsVisible(False)

        chart = self._new_chart()
        chart.addSeries(series)
        chart.legend().setVisible(False)

        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        axis_x.setLabelsColor(QColor(TEXT_MUTED))
        axis_x.setGridLineColor(QColor(BORDER))
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setLabelFormat("%d")
        axis_y.setLabelsColor(QColor(TEXT_MUTED))
        axis_y.setGridLineColor(QColor(BORDER))
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)

        self.top_chart_host.addWidget(self._chart_view(chart))

    # ---------- Alerts panel ---------- #
    def _build_alerts(self, low_stock, expiring):
        self._clear_layout(self.alerts_host)

        if not low_stock and not expiring:
            ok = AlertRow("✓", "All clear", "No critical alerts right now.", "success")
            self.alerts_host.addWidget(ok)
            return

        for p in low_stock[:4]:
            self.alerts_host.addWidget(AlertRow(
                "⚠", f"Low stock: {getattr(p, 'name', '?')}",
                f"Only {getattr(p, 'quantity', 0)} units left",
                "warning",
            ))
        if len(low_stock) > 4:
            self.alerts_host.addWidget(AlertRow(
                "•", f"+{len(low_stock) - 4} more low-stock products",
                "Check the low stock table below.", "info",
            ))

        for p in expiring[:3]:
            days = None
            try:
                days = p.days_until_expiration()
            except Exception:
                pass
            status = "Expired" if days is not None and days < 0 else (
                f"Expires in {days} day(s)" if days is not None else "Expiring soon"
            )
            sev = "danger" if days is not None and days < 0 else "warning"
            self.alerts_host.addWidget(AlertRow(
                "⏳", f"{getattr(p, 'name', '?')}",
                f"{status} — {getattr(p, 'expiration_date', '')}",
                sev,
            ))

    # ---------- Data refresh ---------- #
    def refresh(self):
        try:
            total_products = self.product_service.get_total_products()
            total_stock = self.product_service.get_total_stock()
            low_stock_products = self.product_service.get_low_stock_products()
            expiring_products = self.product_service.get_expiring_soon_products()
            recent_movements = self.inventory_service.get_recent_movements(10)

            # Try to fetch all products for charts; fall back gracefully.
            all_products = []
            for attr in ("get_all_products", "list_products", "get_products"):
                fn = getattr(self.product_service, attr, None)
                if callable(fn):
                    try:
                        all_products = list(fn() or [])
                        break
                    except Exception:
                        continue

            # KPI cards
            self.card_products.set_value(total_products, "items in catalog")
            self.card_stock.set_value(total_stock, "units across warehouse")
            self.card_low.set_value(len(low_stock_products), "below threshold")
            self.card_expiring.set_value(len(expiring_products), "within alert window")

            # Charts (try to use a longer window for the trend if available)
            trend_movements = recent_movements
            try:
                trend_movements = self.inventory_service.get_recent_movements(200)
            except Exception:
                pass
            self._build_movement_chart(trend_movements)
            self._build_category_chart(all_products or low_stock_products)
            self._build_top_products_chart(all_products or low_stock_products)

            # Alerts
            self._build_alerts(low_stock_products, expiring_products)

            # Low stock table
            self.low_stock_table.setRowCount(0)
            for p in low_stock_products:
                row = self.low_stock_table.rowCount()
                self.low_stock_table.insertRow(row)
                self.low_stock_table.setItem(row, 0, QTableWidgetItem(str(p.id)))
                self.low_stock_table.setItem(row, 1, QTableWidgetItem(p.name))
                qty_item = QTableWidgetItem(str(p.quantity))
                qty_item.setForeground(QColor(DANGER))
                qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.low_stock_table.setItem(row, 2, qty_item)

            # Recent movements table
            self.recent_table.setRowCount(0)
            for m in recent_movements:
                row = self.recent_table.rowCount()
                self.recent_table.insertRow(row)
                self.recent_table.setItem(row, 0, QTableWidgetItem(str(m.date)))
                self.recent_table.setItem(row, 1, QTableWidgetItem(m.product_name))
                mtype = m.movement_type.value
                type_item = QTableWidgetItem(("▲ " if mtype == "IN" else "▼ ") + mtype)
                type_item.setForeground(QColor(SUCCESS if mtype == "IN" else DANGER))
                self.recent_table.setItem(row, 2, type_item)
                qty_item = QTableWidgetItem(str(m.quantity))
                qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.recent_table.setItem(row, 3, qty_item)

            self.updated_lbl.setText("Updated " + datetime.now().strftime("%H:%M:%S"))

            if not self._alert_shown_this_session:
                self._alert_shown_this_session = True
                self._show_startup_alert(low_stock_products, expiring_products)
        except Exception as e:
            print(f"Dashboard refresh error: {e}")

    # ---------- Helpers ---------- #
    @staticmethod
    def _parse_date(value):
        if value is None:
            return None
        if hasattr(value, "year") and hasattr(value, "month"):
            try:
                return value.date() if hasattr(value, "date") else value
            except Exception:
                return None
        s = str(value)
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
            try:
                return datetime.strptime(s[:len(fmt) + 2], fmt).date()
            except Exception:
                continue
        try:
            return datetime.fromisoformat(s).date()
        except Exception:
            return None

    def _show_startup_alert(self, low_stock_products, expiring_products):
        if not low_stock_products and not expiring_products:
            return
        lines = []
        if low_stock_products:
            lines.append(f"⚠ {len(low_stock_products)} product(s) are low on stock:")
            for p in low_stock_products[:5]:
                lines.append(f"   • {p.name} (qty: {p.quantity})")
            if len(low_stock_products) > 5:
                lines.append(f"   ...and {len(low_stock_products) - 5} more")
        if expiring_products:
            if lines:
                lines.append("")
            lines.append(f"⏳ {len(expiring_products)} product(s) are expired or expiring soon:")
            for p in expiring_products[:5]:
                days = None
                try:
                    days = p.days_until_expiration()
                except Exception:
                    pass
                status = "EXPIRED" if days is not None and days < 0 else (
                    f"in {days} day(s)" if days is not None else "soon"
                )
                lines.append(f"   • {p.name} — {status} ({p.expiration_date})")
            if len(expiring_products) > 5:
                lines.append(f"   ...and {len(expiring_products) - 5} more")
        QMessageBox.warning(self, "Inventory Alerts", "\n".join(lines))
