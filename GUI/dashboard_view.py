from collections import defaultdict

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QGraphicsDropShadowEffect,
    QProgressBar, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from Kernel.product_service import ProductService
from Kernel.inventory_service import InventoryService


# ---------------------------------------------------------------------------
# Reusable visual primitives
# ---------------------------------------------------------------------------

def apply_shadow(widget: QWidget, blur: int = 22, y_offset: int = 6, alpha: int = 70):
    """Attaches a soft drop shadow to any widget — used for the card / panel feel."""
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur)
    shadow.setOffset(0, y_offset)
    shadow.setColor(QColor(0, 0, 0, alpha))
    widget.setGraphicsEffect(shadow)


class StatCard(QFrame):
    """KPI card with icon glyph, big value, label, and a slim progress/accent bar."""

    def __init__(self, title: str, value: str, color: str, icon: str = "📦", subtitle: str = ""):
        super().__init__()
        self._color = color
        self.setMinimumHeight(120)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #2a3142;
                border-radius: 16px;
            }}
        """)
        apply_shadow(self, blur=24, y_offset=8, alpha=60)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 18, 20, 16)
        outer.setSpacing(10)

        top_row = QHBoxLayout()
        icon_badge = QLabel(icon)
        icon_badge.setFixedSize(42, 42)
        icon_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_badge.setStyleSheet(f"""
            background-color: {color}26;
            border-radius: 12px;
            font-size: 20px;
        """)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #9aa5b1; font-size: 12px; font-weight: 600;")

        top_row.addWidget(icon_badge)
        top_row.addSpacing(10)
        title_box = QVBoxLayout()
        title_box.addWidget(title_label)
        top_row.addLayout(title_box)
        top_row.addStretch()
        outer.addLayout(top_row)

        self.value_label = QLabel(value)
        self.value_label.setFont(QFont("Segoe UI", 26, QFont.Weight.Bold))
        self.value_label.setStyleSheet("color: #ffffff;")
        outer.addWidget(self.value_label)

        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setStyleSheet("color: #6b7280; font-size: 11px;")
        outer.addWidget(self.subtitle_label)

        self.accent_bar = QFrame()
        self.accent_bar.setFixedHeight(4)
        self.accent_bar.setStyleSheet(f"background-color: {color}; border-radius: 2px;")
        outer.addWidget(self.accent_bar)

    def set_value(self, value: str):
        self.value_label.setText(value)

    def set_subtitle(self, text: str):
        self.subtitle_label.setText(text)


class SectionPanel(QFrame):
    """A rounded card container used to wrap charts / tables with a header."""

    def __init__(self, title: str, accent: str = "#3b82f6"):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                background-color: #2a3142;
                border-radius: 16px;
            }
        """)
        apply_shadow(self, blur=20, y_offset=6, alpha=55)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 18, 20, 18)
        self.layout.setSpacing(12)

        header_row = QHBoxLayout()
        bar = QFrame()
        bar.setFixedSize(4, 18)
        bar.setStyleSheet(f"background-color: {accent}; border-radius: 2px;")
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 14px;")
        header_row.addWidget(bar)
        header_row.addSpacing(8)
        header_row.addWidget(title_label)
        header_row.addStretch()

        self.layout.addLayout(header_row)

    def add_widget(self, widget: QWidget):
        self.layout.addWidget(widget)


class DonutChart(FigureCanvas):
    """Embedded matplotlib donut chart themed to match the dark ERP palette."""

    PALETTE = ["#3b82f6", "#22c55e", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4", "#ec4899"]

    def __init__(self, parent=None):
        fig = Figure(figsize=(4, 3.4), dpi=100)
        fig.patch.set_alpha(0)
        super().__init__(fig)
        self.setParent(parent)
        self.setStyleSheet("background: transparent;")
        self.ax = fig.add_subplot(111)

    def plot(self, labels: list[str], values: list[int], center_text: str = ""):
        self.ax.clear()
        self.ax.set_facecolor("none")

        if not values or sum(values) == 0:
            self.ax.text(
                0.5, 0.5, "No data yet", ha="center", va="center",
                color="#6b7280", fontsize=11, transform=self.ax.transAxes
            )
            self.ax.axis("off")
            self.draw()
            return

        colors = [self.PALETTE[i % len(self.PALETTE)] for i in range(len(values))]
        wedges, _ = self.ax.pie(
            values,
            colors=colors,
            startangle=90,
            wedgeprops=dict(width=0.42, edgecolor="#2a3142", linewidth=2),
        )

        self.ax.text(
            0, 0, center_text, ha="center", va="center",
            color="#ffffff", fontsize=13, fontweight="bold"
        )

        legend = self.ax.legend(
            wedges, labels,
            loc="center left",
            bbox_to_anchor=(1.0, 0.5),
            frameon=False,
            fontsize=8,
            labelcolor="#cbd5e1",
        )

        self.ax.set_aspect("equal")
        self.figure.tight_layout()
        self.draw()


class RankRow(QWidget):
    """A single ranked row: name, slim progress bar, and quantity value."""

    def __init__(self, name: str, value: int, max_value: int, color: str):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(4)

        top = QHBoxLayout()
        name_label = QLabel(name)
        name_label.setStyleSheet("color: #e5e7eb; font-size: 12px;")
        value_label = QLabel(str(value))
        value_label.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: bold;")
        top.addWidget(name_label)
        top.addStretch()
        top.addWidget(value_label)
        layout.addLayout(top)

        bar = QProgressBar()
        bar.setFixedHeight(8)
        bar.setTextVisible(False)
        bar.setRange(0, max(max_value, 1))
        bar.setValue(value)
        bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #1e2530;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 4px;
            }}
        """)
        layout.addWidget(bar)


# ---------------------------------------------------------------------------
# Main dashboard view
# ---------------------------------------------------------------------------

class DashboardView(QWidget):
    """Dashboard tab: KPI cards, donut charts for stock movement, and rankings."""

    def __init__(self, product_service: ProductService, inventory_service: InventoryService):
        super().__init__()
        self.product_service = product_service
        self.inventory_service = inventory_service
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        self.setStyleSheet("background-color: #1e2530;")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(20)

        header = QLabel("Dashboard")
        header.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        header.setStyleSheet("color: #ffffff;")
        outer.addWidget(header)

        subheader = QLabel("Live overview of inventory health and stock movement")
        subheader.setStyleSheet("color: #6b7280; font-size: 12px;")
        outer.addWidget(subheader)

        # --- KPI cards row ---
        cards_row = QHBoxLayout()
        cards_row.setSpacing(16)
        self.total_products_card = StatCard("Total Products", "0", "#3b82f6", icon="📦", subtitle="Active SKUs")
        self.total_stock_card = StatCard("Total Stock", "0", "#22c55e", icon="🧮", subtitle="Units on hand")
        self.low_stock_card = StatCard("Low Stock Alerts", "0", "#ef4444", icon="⚠️", subtitle="Need reorder")
        cards_row.addWidget(self.total_products_card)
        cards_row.addWidget(self.total_stock_card)
        cards_row.addWidget(self.low_stock_card)
        outer.addLayout(cards_row)

        # --- Charts row: stocked-out donut | stocked-in donut ---
        charts_row = QHBoxLayout()
        charts_row.setSpacing(16)

        self.out_panel = SectionPanel("Most Stocked-OUT Products", accent="#ef4444")
        self.out_chart = DonutChart(self.out_panel)
        self.out_panel.add_widget(self.out_chart)

        self.in_panel = SectionPanel("Most Stocked-IN Products", accent="#22c55e")
        self.in_chart = DonutChart(self.in_panel)
        self.in_panel.add_widget(self.in_chart)

        charts_row.addWidget(self.out_panel)
        charts_row.addWidget(self.in_panel)
        outer.addLayout(charts_row, stretch=3)

        # --- Bottom row: low stock list | recent movements ---
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(16)

        self.low_stock_panel = SectionPanel("Low Stock Products", accent="#f59e0b")
        self.low_stock_table = QTableWidget(0, 3)
        self.low_stock_table.setHorizontalHeaderLabels(["ID", "Name", "Quantity"])
        self._style_table(self.low_stock_table)
        self.low_stock_panel.add_widget(self.low_stock_table)

        self.recent_panel = SectionPanel("Recent Movements", accent="#3b82f6")
        self.recent_table = QTableWidget(0, 4)
        self.recent_table.setHorizontalHeaderLabels(["Date", "Product", "Type", "Quantity"])
        self._style_table(self.recent_table)
        self.recent_panel.add_widget(self.recent_table)

        bottom_row.addWidget(self.low_stock_panel)
        bottom_row.addWidget(self.recent_panel)
        outer.addLayout(bottom_row, stretch=3)

        # --- Ranking panel: top movers as progress bars ---
        self.ranking_panel = SectionPanel("Top Movement Activity", accent="#8b5cf6")
        self.ranking_container = QVBoxLayout()
        self.ranking_container.setSpacing(8)
        ranking_wrapper = QWidget()
        ranking_wrapper.setLayout(self.ranking_container)
        self.ranking_panel.add_widget(ranking_wrapper)
        outer.addWidget(self.ranking_panel, stretch=2)

    @staticmethod
    def _style_table(table: QTableWidget):
        table.setStyleSheet("""
            QTableWidget {
                background-color: #1e2530;
                color: #e5e7eb;
                border: none;
                border-radius: 10px;
                gridline-color: #2a3142;
            }
            QHeaderView::section {
                background-color: #161b26;
                color: #9aa5b1;
                padding: 6px;
                border: none;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 6px;
            }
        """)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)

    # ------------------------------------------------------------------
    # Data refresh
    # ------------------------------------------------------------------

    def refresh(self):
        """Reload all dashboard data from services. No business logic changed —
        this only re-reads existing service/repository data and redraws widgets."""
        try:
            total_products = self.product_service.get_total_products()
            total_stock = self.product_service.get_total_stock()
            low_stock_products = self.product_service.get_low_stock_products()
            recent_movements = self.inventory_service.get_recent_movements(10)
            full_history = self.inventory_service.get_history()

            # KPI cards
            self.total_products_card.set_value(str(total_products))
            self.total_stock_card.set_value(str(total_stock))
            self.low_stock_card.set_value(str(len(low_stock_products)))
            self.low_stock_card.set_subtitle(
                "All good" if len(low_stock_products) == 0 else "Action needed"
            )

            # Low stock table
            self.low_stock_table.setRowCount(0)
            for p in low_stock_products:
                row = self.low_stock_table.rowCount()
                self.low_stock_table.insertRow(row)
                self.low_stock_table.setItem(row, 0, QTableWidgetItem(str(p.id)))
                self.low_stock_table.setItem(row, 1, QTableWidgetItem(p.name))
                qty_item = QTableWidgetItem(str(p.quantity))
                qty_item.setForeground(Qt.GlobalColor.red)
                self.low_stock_table.setItem(row, 2, qty_item)

            # Recent movements table
            self.recent_table.setRowCount(0)
            for m in recent_movements:
                row = self.recent_table.rowCount()
                self.recent_table.insertRow(row)
                self.recent_table.setItem(row, 0, QTableWidgetItem(m.date))
                self.recent_table.setItem(row, 1, QTableWidgetItem(m.product_name))
                type_item = QTableWidgetItem(m.movement_type.value)
                type_item.setForeground(
                    Qt.GlobalColor.green if m.movement_type.value == "IN" else Qt.GlobalColor.red
                )
                self.recent_table.setItem(row, 2, type_item)
                self.recent_table.setItem(row, 3, QTableWidgetItem(str(m.quantity)))

            # Aggregate IN vs OUT quantities per product from full history
            out_totals: dict[str, int] = defaultdict(int)
            in_totals: dict[str, int] = defaultdict(int)
            for m in full_history:
                if m.movement_type.value == "OUT":
                    out_totals[m.product_name] += m.quantity
                else:
                    in_totals[m.product_name] += m.quantity

            top_out = sorted(out_totals.items(), key=lambda x: x[1], reverse=True)[:5]
            top_in = sorted(in_totals.items(), key=lambda x: x[1], reverse=True)[:5]

            self.out_chart.plot(
                labels=[name for name, _ in top_out],
                values=[qty for _, qty in top_out],
                center_text=f"{sum(qty for _, qty in top_out)}\nunits"
            )
            self.in_chart.plot(
                labels=[name for name, _ in top_in],
                values=[qty for _, qty in top_in],
                center_text=f"{sum(qty for _, qty in top_in)}\nunits"
            )

            # Ranking panel: combine top movers (by total activity) as progress bars
            self._refresh_ranking(out_totals, in_totals)

        except Exception as e:
            print(f"Dashboard refresh error: {e}")

    def _refresh_ranking(self, out_totals: dict, in_totals: dict):
        # Clear existing rows
        while self.ranking_container.count():
            item = self.ranking_container.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        combined: dict[str, int] = defaultdict(int)
        for name, qty in out_totals.items():
            combined[name] += qty
        for name, qty in in_totals.items():
            combined[name] += qty

        if not combined:
            empty_label = QLabel("No stock movement recorded yet.")
            empty_label.setStyleSheet("color: #6b7280; font-size: 12px;")
            self.ranking_container.addWidget(empty_label)
            return

        top_combined = sorted(combined.items(), key=lambda x: x[1], reverse=True)[:6]
        max_value = top_combined[0][1] if top_combined else 1
        colors = ["#3b82f6", "#22c55e", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4"]

        for i, (name, qty) in enumerate(top_combined):
            row = RankRow(name, qty, max_value, colors[i % len(colors)])
            self.ranking_container.addWidget(row)