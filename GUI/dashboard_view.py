"""Dashboard — unified theme & icons. Logic untouched."""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Iterable

from PyQt6.QtCore import Qt, QTimer, QMargins, QDateTime, QSize
from PyQt6.QtGui import QFont, QColor, QPainter
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QSizePolicy,
    QScrollArea,
)

try:
    from PyQt6.QtCharts import (
        QChart, QChartView, QLineSeries, QValueAxis, QDateTimeAxis,
        QPieSeries, QBarSeries, QBarSet, QBarCategoryAxis,
    )
    _CHARTS_OK = True
except Exception:
    _CHARTS_OK = False

from Kernel.product_service import ProductService
from Kernel.inventory_service import InventoryService
from Kernel.category_service import CategoryService

from GUI.theme import (
    BG, SURFACE, SURFACE_2, BORDER, TEXT, TEXT_MUTED,
    PRIMARY, SUCCESS, WARNING, DANGER, INFO,
    FS_SECTION, FS_BODY, FS_SMALL, FS_MICRO, RADIUS_XL, CHART_PALETTE,
    Icons, qicon, icon_label, page_header, style_table, status_badge,
)


# ---------- Pastel helpers (low-opacity tints over white) ----------
# Soft, easy-on-the-eyes pastels for the "attention" widgets.
PASTEL_WARNING_BG     = "#fff6e5"   # pastel amber
PASTEL_WARNING_BORDER = "#fde7b3"
PASTEL_DANGER_BG      = "#fdecec"   # pastel red
PASTEL_DANGER_BORDER  = "#f6c9c9"


# ----------------------------- Widgets ----------------------------- #
class KpiCard(QFrame):
    def __init__(self, title: str, std_icon, accent: str, pastel_bg: str | None = None,
                 pastel_border: str | None = None):
        super().__init__()
        self.accent = accent
        self.setObjectName("KpiCard")
        bg = pastel_bg or SURFACE
        bd = pastel_border or BORDER
        self.setStyleSheet(f"""
            QFrame#KpiCard {{
                background-color: {bg};
                border: 1px solid {bd};
                border-radius: {RADIUS_XL}px;
            }}
            QLabel {{ background: transparent; }}
        """)
        self.setMinimumHeight(122)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18); root.setSpacing(8)

        top = QHBoxLayout(); top.setSpacing(12)
        chip = QFrame(); chip.setFixedSize(42, 42)
        chip.setStyleSheet(f"background-color: {accent}22; border-radius: 11px;")
        chip_lay = QVBoxLayout(chip); chip_lay.setContentsMargins(0, 0, 0, 0)
        chip_lay.addWidget(icon_label(std_icon, 20))
        top.addWidget(chip)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: {FS_MICRO}px; "
            f"font-weight: 700; letter-spacing: 0.8px; text-transform: uppercase;"
        )
        top.addWidget(title_lbl, 1)

        self.trend_lbl = QLabel("")
        self.trend_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: {FS_MICRO}px; font-weight: 700;")
        top.addWidget(self.trend_lbl, 0, Qt.AlignmentFlag.AlignRight)
        root.addLayout(top)

        self.value_lbl = QLabel("0")
        self.value_lbl.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        self.value_lbl.setStyleSheet(f"color: {TEXT};")
        root.addWidget(self.value_lbl)

        self.sub_lbl = QLabel("")
        self.sub_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: {FS_MICRO}px;")
        root.addWidget(self.sub_lbl)

        self._prev_value: float | None = None

    def set_value(self, value, subtitle: str = ""):
        try: num = float(value)
        except (TypeError, ValueError): num = None
        self.value_lbl.setText(str(value))
        self.sub_lbl.setText(subtitle)
        if num is not None and self._prev_value is not None and self._prev_value != 0:
            delta = num - self._prev_value
            pct = (delta / self._prev_value) * 100
            arrow = "▲" if delta > 0 else ("▼" if delta < 0 else "■")
            color = SUCCESS if delta > 0 else (DANGER if delta < 0 else TEXT_MUTED)
            self.trend_lbl.setText(f"{arrow} {abs(pct):.1f}%")
            self.trend_lbl.setStyleSheet(f"color: {color}; font-size: {FS_MICRO}px; font-weight: 700;")
        if num is not None:
            self._prev_value = num


class SectionCard(QFrame):
    def __init__(self, title: str, subtitle: str = "",
                 bg: str | None = None, border: str | None = None):
        super().__init__()
        self.setObjectName("SectionCard")
        _bg = bg or SURFACE
        _bd = border or BORDER
        self.setStyleSheet(f"""
            QFrame#SectionCard {{
                background-color: {_bg};
                border: 1px solid {_bd};
                border-radius: {RADIUS_XL}px;
            }}
            QLabel {{ background: transparent; }}
        """)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(20, 18, 20, 18); self._root.setSpacing(12)
        head = QVBoxLayout(); head.setSpacing(2)
        t = QLabel(title)
        t.setStyleSheet(f"color: {TEXT}; font-size: {FS_SECTION}px; font-weight: 700;")
        head.addWidget(t)
        if subtitle:
            s = QLabel(subtitle)
            s.setStyleSheet(f"color: {TEXT_MUTED}; font-size: {FS_MICRO}px;")
            head.addWidget(s)
        self._root.addLayout(head)

    def body(self) -> QVBoxLayout: return self._root


class AlertRow(QFrame):
    def __init__(self, std_icon, title: str, detail: str, severity: str = "warning"):
        super().__init__()
        # Pastel, low-opacity row styling so text stays perfectly readable.
        palette = {
            "danger":  ("#fdecec", "#f4c2c2", DANGER),
            "warning": ("#fff6e5", "#fde0a8", WARNING),
            "info":    ("#e8f1fb", "#cfe0f5", INFO),
            "success": ("#e9f7ee", "#c6e9d2", SUCCESS),
        }
        bg, bd, accent = palette.get(severity, palette["warning"])
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                border: 1px solid {bd};
                border-left: 3px solid {accent};
                border-radius: 8px;
            }}
            QLabel {{ background: transparent; }}
        """)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10); lay.setSpacing(10)
        lay.addWidget(icon_label(std_icon, 18), 0, Qt.AlignmentFlag.AlignTop)
        box = QVBoxLayout(); box.setSpacing(2)
        t = QLabel(title); t.setStyleSheet(f"color: {TEXT}; font-size: {FS_SMALL}px; font-weight: 600;")
        d = QLabel(detail); d.setStyleSheet(f"color: {TEXT_MUTED}; font-size: {FS_MICRO}px;"); d.setWordWrap(True)
        box.addWidget(t); box.addWidget(d)
        lay.addLayout(box, 1)


# ----------------------------- Main view ----------------------------- #
class DashboardView(QWidget):
    def __init__(self, product_service: ProductService, inventory_service: InventoryService,
                 category_service: CategoryService | None = None):
        super().__init__()
        self.product_service = product_service
        self.inventory_service = inventory_service
        self.category_service = category_service
        self._alert_shown_this_session = False
        self.setStyleSheet(f"background-color: {BG};")
        self._build_ui()
        self.refresh()
        self._timer = QTimer(self); self._timer.setInterval(30_000)
        self._timer.timeout.connect(self.refresh); self._timer.start()

    def _build_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        container = QWidget()
        container.setStyleSheet(f"background-color: {BG};")
        outer = QVBoxLayout(self); outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll); scroll.setWidget(container)

        root = QVBoxLayout(container)
        root.setContentsMargins(28, 24, 28, 24); root.setSpacing(20)

        # Header
        header = QHBoxLayout()
        header.addWidget(page_header("Dashboard", "Real-time overview of stock, movements, and alerts"), 1)

        live = QLabel("●  LIVE")
        live.setStyleSheet(f"""
            color: {SUCCESS};
            background-color: {SUCCESS}1f;
            border: 1px solid {SUCCESS}55;
            border-radius: 999px;
            padding: 6px 12px;
            font-size: {FS_MICRO}px;
            font-weight: 700; letter-spacing: 1px;
        """)
        header.addWidget(live, 0, Qt.AlignmentFlag.AlignTop)

        self.updated_lbl = QLabel("")
        self.updated_lbl.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: {FS_MICRO}px; padding-left: 10px; background: transparent;"
        )
        header.addWidget(self.updated_lbl, 0, Qt.AlignmentFlag.AlignTop)
        root.addLayout(header)

        # KPI grid — Low Stock & Expiring Soon use pastel low-opacity cards
        kpis = QGridLayout(); kpis.setSpacing(16)
        self.card_products = KpiCard("Total Products",    Icons.BOX,     PRIMARY)
        self.card_stock    = KpiCard("Stock Units",       Icons.STOCK,   SUCCESS)
        self.card_low      = KpiCard("Low Stock Alerts",  Icons.WARNING, WARNING,
                                     pastel_bg=PASTEL_WARNING_BG, pastel_border=PASTEL_WARNING_BORDER)
        self.card_expiring = KpiCard("Expiring Soon",     Icons.DANGER,  DANGER,
                                     pastel_bg=PASTEL_DANGER_BG, pastel_border=PASTEL_DANGER_BORDER)
        for i, c in enumerate((self.card_products, self.card_stock, self.card_low, self.card_expiring)):
            kpis.addWidget(c, 0, i); kpis.setColumnStretch(i, 1)
        root.addLayout(kpis)

        # Charts row
        charts = QGridLayout(); charts.setSpacing(16)
        self.movement_card = SectionCard("Stock Movements", "Incoming vs outgoing — last 7 days")
        self.movement_chart_host = QVBoxLayout(); self.movement_card.body().addLayout(self.movement_chart_host)
        self.category_card = SectionCard("Stock by Category", "Distribution across product categories")
        self.category_chart_host = QVBoxLayout(); self.category_card.body().addLayout(self.category_chart_host)
        charts.addWidget(self.movement_card, 0, 0); charts.addWidget(self.category_card, 0, 1)
        charts.setColumnStretch(0, 2); charts.setColumnStretch(1, 1)
        root.addLayout(charts)

        # Top + Alerts (Alerts panel uses pastel red background)
        mid = QGridLayout(); mid.setSpacing(16)
        self.top_card = SectionCard("Top Products by Stock", "Highest quantity on hand")
        self.top_chart_host = QVBoxLayout(); self.top_card.body().addLayout(self.top_chart_host)
        self.alerts_card = SectionCard(
            "Alerts & Notifications", "Items needing attention",
            bg=PASTEL_DANGER_BG, border=PASTEL_DANGER_BORDER,
        )
        self.alerts_host = QVBoxLayout(); self.alerts_host.setSpacing(8)
        self.alerts_card.body().addLayout(self.alerts_host)
        self.alerts_card.body().addStretch(1)
        mid.addWidget(self.top_card, 0, 0); mid.addWidget(self.alerts_card, 0, 1)
        mid.setColumnStretch(0, 2); mid.setColumnStretch(1, 1)
        root.addLayout(mid)

        # (Removed: Low Stock Products & Recent Movements tables)
        root.addStretch(1)

    # ---------- Chart helpers ---------- #
    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w is not None: w.deleteLater()

    def _placeholder(self, text: str) -> QLabel:
        lbl = QLabel(text); lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: {FS_SMALL}px; padding: 30px; background: transparent;")
        lbl.setMinimumHeight(220); return lbl

    def _new_chart(self, title: str = ""):
        chart = QChart(); chart.setTitle(title)
        chart.setBackgroundBrush(QColor(SURFACE))
        chart.setPlotAreaBackgroundBrush(QColor(SURFACE))
        chart.setPlotAreaBackgroundVisible(True)
        chart.setBackgroundRoundness(0)
        chart.setMargins(QMargins(0, 0, 0, 0))
        chart.legend().setLabelColor(QColor(TEXT_MUTED))
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        chart.setTitleBrush(QColor(TEXT))
        return chart

    def _chart_view(self, chart):
        view = QChartView(chart); view.setRenderHint(QPainter.RenderHint.Antialiasing)
        view.setStyleSheet(f"background-color: {SURFACE}; border: none;")
        view.setMinimumHeight(270); return view

    def _build_movement_chart(self, movements: Iterable):
        self._clear_layout(self.movement_chart_host)
        if not _CHARTS_OK:
            self.movement_chart_host.addWidget(self._placeholder("Install PyQt6-Charts to see movement trends")); return
        today = datetime.now().date()
        days = [today - timedelta(days=i) for i in range(6, -1, -1)]
        in_by_day, out_by_day = defaultdict(int), defaultdict(int)
        for m in movements:
            d = self._parse_date(getattr(m, "date", None))
            if d is None or d < days[0] or d > days[-1]: continue
            qty = int(getattr(m, "quantity", 0) or 0)
            mtype = getattr(getattr(m, "movement_type", None), "value", "")
            if mtype == "IN": in_by_day[d] += qty
            elif mtype == "OUT": out_by_day[d] += qty

        s_in = QLineSeries(); s_in.setName("Incoming")
        s_out = QLineSeries(); s_out.setName("Outgoing")
        max_y = 1
        for d in days:
            ts = QDateTime(d.year, d.month, d.day, 0, 0).toMSecsSinceEpoch()
            s_in.append(ts, in_by_day[d]); s_out.append(ts, out_by_day[d])
            max_y = max(max_y, in_by_day[d], out_by_day[d])

        p1 = s_in.pen();  p1.setColor(QColor(SUCCESS)); p1.setWidth(3); s_in.setPen(p1)
        p2 = s_out.pen(); p2.setColor(QColor(DANGER));  p2.setWidth(3); s_out.setPen(p2)

        chart = self._new_chart(); chart.addSeries(s_in); chart.addSeries(s_out)
        ax_x = QDateTimeAxis(); ax_x.setFormat("MMM dd"); ax_x.setTickCount(7)
        ax_x.setLabelsColor(QColor(TEXT_MUTED)); ax_x.setGridLineColor(QColor(BORDER))
        chart.addAxis(ax_x, Qt.AlignmentFlag.AlignBottom)
        s_in.attachAxis(ax_x); s_out.attachAxis(ax_x)
        ax_y = QValueAxis(); ax_y.setRange(0, max_y * 1.2); ax_y.setLabelFormat("%d")
        ax_y.setLabelsColor(QColor(TEXT_MUTED)); ax_y.setGridLineColor(QColor(BORDER))
        chart.addAxis(ax_y, Qt.AlignmentFlag.AlignLeft)
        s_in.attachAxis(ax_y); s_out.attachAxis(ax_y)
        self.movement_chart_host.addWidget(self._chart_view(chart))

    def _build_category_chart(self, products):
        self._clear_layout(self.category_chart_host)
        if not _CHARTS_OK:
            self.category_chart_host.addWidget(self._placeholder("Install PyQt6-Charts to see category breakdown")); return
        category_names = {}
        if self.category_service is not None:
            try:
                category_names = {c.id: c.name for c in self.category_service.list_categories()}
            except Exception:
                category_names = {}
        totals = Counter()
        for p in products:
            cat_id = getattr(p, "category_id", None)
            cat = category_names.get(cat_id, "Uncategorized") if cat_id is not None else "Uncategorized"
            totals[cat] += int(getattr(p, "quantity", 0) or 0)
        if not totals:
            self.category_chart_host.addWidget(self._placeholder("No category data available")); return
        series = QPieSeries(); series.setHoleSize(0.58)
        for i, (cat, qty) in enumerate(totals.most_common(6)):
            slc = series.append(f"{cat} ({qty})", qty)
            slc.setBrush(QColor(CHART_PALETTE[i % len(CHART_PALETTE)]))
            slc.setBorderColor(QColor(SURFACE)); slc.setBorderWidth(2)
            slc.setLabelColor(QColor(TEXT_MUTED))
        chart = self._new_chart(); chart.addSeries(series)
        self.category_chart_host.addWidget(self._chart_view(chart))

    def _build_top_products_chart(self, products):
        self._clear_layout(self.top_chart_host)
        if not _CHARTS_OK:
            self.top_chart_host.addWidget(self._placeholder("Install PyQt6-Charts to see top products")); return
        top = sorted(products, key=lambda p: getattr(p, "quantity", 0) or 0, reverse=True)[:6]
        if not top:
            self.top_chart_host.addWidget(self._placeholder("No products to display")); return

        total_top = sum(int(getattr(p, "quantity", 0) or 0) for p in top) or 1

        bar = QBarSet("Quantity"); bar.setColor(QColor(PRIMARY)); bar.setBorderColor(QColor(PRIMARY))
        categories = []
        for p in top:
            qty = int(getattr(p, "quantity", 0) or 0)
            bar.append(qty)
            name = getattr(p, "name", "?")
            short = name if len(name) <= 14 else name[:13] + "…"
            pct = (qty / total_top) * 100
            # More detailed numbers: name + qty + share of top-N
            categories.append(f"{short}\n{qty:,} u • {pct:.1f}%")

        series = QBarSeries(); series.append(bar)
        # Show value on top of each bar
        series.setLabelsVisible(True)
        series.setLabelsFormat("@value")
        try:
            series.setLabelsPosition(QBarSeries.LabelsPosition.LabelsOutsideEnd)
        except Exception:
            pass

        chart = self._new_chart(); chart.addSeries(series); chart.legend().setVisible(False)
        ax_x = QBarCategoryAxis(); ax_x.append(categories)
        ax_x.setLabelsColor(QColor(TEXT_MUTED)); ax_x.setGridLineColor(QColor(BORDER))
        chart.addAxis(ax_x, Qt.AlignmentFlag.AlignBottom); series.attachAxis(ax_x)

        max_q = max((int(getattr(p, "quantity", 0) or 0) for p in top), default=1)
        ax_y = QValueAxis(); ax_y.setLabelFormat("%d")
        ax_y.setRange(0, max(1, int(max_q * 1.2)))
        ax_y.setLabelsColor(QColor(TEXT_MUTED)); ax_y.setGridLineColor(QColor(BORDER))
        chart.addAxis(ax_y, Qt.AlignmentFlag.AlignLeft); series.attachAxis(ax_y)
        self.top_chart_host.addWidget(self._chart_view(chart))

    # ---------- Alerts ---------- #
    def _build_alerts(self, low_stock, expiring):
        self._clear_layout(self.alerts_host)
        if not low_stock and not expiring:
            self.alerts_host.addWidget(AlertRow(Icons.OK, "All clear",
                                                "No critical alerts right now.", "success"))
            return
        for p in low_stock[:4]:
            self.alerts_host.addWidget(AlertRow(
                Icons.WARNING, f"Low stock: {getattr(p, 'name', '?')}",
                f"Only {getattr(p, 'quantity', 0)} units left", "warning"))
        if len(low_stock) > 4:
            self.alerts_host.addWidget(AlertRow(
                Icons.INFO, f"+{len(low_stock) - 4} more low-stock products",
                "See the Low Stock Alerts KPI above.", "info"))
        for p in expiring[:3]:
            days = None
            try: days = p.days_until_expiration()
            except Exception: pass
            status = "Expired" if days is not None and days < 0 else (
                f"Expires in {days} day(s)" if days is not None else "Expiring soon")
            sev = "danger" if days is not None and days < 0 else "warning"
            self.alerts_host.addWidget(AlertRow(
                Icons.DANGER, f"{getattr(p, 'name', '?')}",
                f"{status} — {getattr(p, 'expiration_date', '')}", sev))

    # ---------- Refresh ---------- #
    def refresh(self):
        try:
            total_products = self.product_service.get_total_products()
            total_stock = self.product_service.get_total_stock()
            low_stock_products = self.product_service.get_low_stock_products()
            expiring_products = self.product_service.get_expiring_soon_products()
            recent_movements = self.inventory_service.get_recent_movements(10)

            all_products = []
            for attr in ("get_all_products", "list_products", "get_products"):
                fn = getattr(self.product_service, attr, None)
                if callable(fn):
                    try: all_products = list(fn() or []); break
                    except Exception: continue

            self.card_products.set_value(total_products, "items in catalog")
            self.card_stock.set_value(total_stock, "units across warehouse")
            self.card_low.set_value(len(low_stock_products), "below threshold")
            self.card_expiring.set_value(len(expiring_products), "within alert window")

            trend = recent_movements
            try: trend = self.inventory_service.get_recent_movements(200)
            except Exception: pass
            self._build_movement_chart(trend)
            self._build_category_chart(all_products or low_stock_products)
            self._build_top_products_chart(all_products or low_stock_products)
            self._build_alerts(low_stock_products, expiring_products)

            self.updated_lbl.setText("Updated " + datetime.now().strftime("%H:%M:%S"))

            if not self._alert_shown_this_session:
                self._alert_shown_this_session = True
                self._show_startup_alert(low_stock_products, expiring_products)
        except Exception as e:
            print(f"Dashboard refresh error: {e}")

    @staticmethod
    def _parse_date(value):
        if value is None: return None
        if hasattr(value, "year") and hasattr(value, "month"):
            try: return value.date() if hasattr(value, "date") else value
            except Exception: return None
        s = str(value)
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
            try: return datetime.strptime(s[:len(fmt) + 2], fmt).date()
            except Exception: continue
        try: return datetime.fromisoformat(s).date()
        except Exception: return None

    def _show_startup_alert(self, low_stock_products, expiring_products):
        if not low_stock_products and not expiring_products: return
        lines = []
        if low_stock_products:
            lines.append(f"{len(low_stock_products)} product(s) are low on stock:")
            for p in low_stock_products[:5]:
                lines.append(f"   - {p.name} (qty: {p.quantity})")
            if len(low_stock_products) > 5:
                lines.append(f"   ...and {len(low_stock_products) - 5} more")
        if expiring_products:
            if lines: lines.append("")
            lines.append(f"{len(expiring_products)} product(s) are expired or expiring soon:")
            for p in expiring_products[:5]:
                days = None
                try: days = p.days_until_expiration()
                except Exception: pass
                status = "EXPIRED" if days is not None and days < 0 else (
                    f"in {days} day(s)" if days is not None else "soon")
                lines.append(f"   - {p.name} — {status} ({p.expiration_date})")
            if len(expiring_products) > 5:
                lines.append(f"   ...and {len(expiring_products) - 5} more")
        QMessageBox.warning(self, "Inventory Alerts", "\n".join(lines))
