"""
historial_vivo.py — UI4: línea de tiempo de la REALIDAD (CSV del monitor)

Lee (y sigue en vivo) los archivos PLC/historial/historial_*.csv que escribe
monitor_247.py. Cada fila del CSV es un instante con Ga/Al/In/As/N en
ABIERTA|CERRADA — la misma información que tu amigo usará en la tabla SQL
de monitoreo (ver README.md).

Contraste:
  UI2 (main.py TimelineWidget) = PLAN de la receta JSON
  UI4 (este archivo)           = REALIDAD medida/logueada en el CSV

Lanzar:
  cd PLC && ../.venv/bin/python historial_vivo.py
  # opcional: pasar ruta a un CSV como argv[1]
"""
import csv
import glob
import os
import sys

from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QFont
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QFrame, QMessageBox,
)

from styles import MAIN_STYLE_SHEET

CELLS = ["Ga", "Al", "In", "As", "N"]
CELL_COLORS = {
    "Ga": QColor(50, 120, 220),
    "Al": QColor(40, 170, 90),
    "In": QColor(255, 150, 40),
    "As": QColor(220, 50, 50),
    "N":  QColor(150, 50, 220),
}


def historial_dir():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "historial")


def latest_csv_path():
    folder = historial_dir()
    if not os.path.isdir(folder):
        return None
    files = glob.glob(os.path.join(folder, "historial_*.csv"))
    if not files:
        return None
    return max(files, key=os.path.getmtime)


def parse_open(value):
    return str(value).strip().upper().startswith("ABIERT")


class RealityTimelineWidget(QWidget):
    """Horizontal bars: for each cell, segments where the CSV says ABIERTA."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(320)
        # list of (t_seconds: float, open_by_cell: dict[str,bool])
        self.samples = []

    def set_samples(self, samples):
        self.samples = samples
        self.update()

    def format_time_label(self, seconds, total):
        if total < 120:
            return f"{seconds:.1f}s"
        if total < 7200:
            return f"{seconds / 60:.1f}m"
        return f"{seconds / 3600:.1f}h"

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        p.fillRect(rect, QColor(245, 245, 245))

        left, right = 90, rect.width() - 40
        top, bottom = 40, rect.height() - 40
        width = max(1, right - left)
        draw_h = max(1, bottom - top)

        p.setPen(QPen(Qt.GlobalColor.black, 2))
        p.drawRect(left, top, width, draw_h)

        if len(self.samples) < 1:
            p.setPen(QPen(QColor("#7f8c8d")))
            p.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            p.drawText(
                QRectF(left, top, width, draw_h),
                Qt.AlignmentFlag.AlignCenter,
                "UI4: Esperando CSV del monitor…\n"
                "Inicia un crecimiento o abre un historial_*.csv",
            )
            return

        t0 = self.samples[0][0]
        t_end = self.samples[-1][0]
        total = max(0.1, t_end - t0)

        # time grid
        p.setPen(QPen(QColor(200, 200, 200), 1, Qt.PenStyle.DashLine))
        for i in range(6):
            x = left + (i / 5) * width
            t_val = t0 + (i / 5) * total
            p.drawLine(int(x), top, int(x), bottom)
            p.setPen(QPen(Qt.GlobalColor.black))
            p.setFont(QFont("Arial", 9))
            p.drawText(
                int(x) - 24, bottom + 12, 48, 16,
                Qt.AlignmentFlag.AlignCenter,
                self.format_time_label(t_val - t0, total),
            )
            p.setPen(QPen(QColor(200, 200, 200), 1, Qt.PenStyle.DashLine))

        row_h = draw_h / len(CELLS)
        y = top
        for cell in CELLS:
            color = CELL_COLORS[cell]
            p.setPen(QPen(Qt.GlobalColor.black))
            p.setFont(QFont("Arial", 11, QFont.Weight.Bold))
            p.drawText(15, int(y + row_h / 2 + 5), f"Celda {cell}")

            bar_y = y + row_h * 0.3
            bar_h = row_h * 0.4

            seg_start = None
            for t, states in self.samples:
                is_open = states.get(cell, False)
                if is_open and seg_start is None:
                    seg_start = t
                elif not is_open and seg_start is not None:
                    x1 = left + ((seg_start - t0) / total) * width
                    x2 = left + ((t - t0) / total) * width
                    w = max(1.0, x2 - x1)
                    p.fillRect(QRectF(x1, bar_y, w, bar_h), color)
                    p.setPen(Qt.GlobalColor.black)
                    p.drawRect(QRectF(x1, bar_y, w, bar_h))
                    seg_start = None
            if seg_start is not None:
                x1 = left + ((seg_start - t0) / total) * width
                x2 = left + ((t_end - t0) / total) * width
                w = max(1.0, x2 - x1)
                p.fillRect(QRectF(x1, bar_y, w, bar_h), color)
                p.setPen(Qt.GlobalColor.black)
                p.drawRect(QRectF(x1, bar_y, w, bar_h))

            p.setPen(QPen(QColor(200, 200, 200)))
            p.drawLine(left, int(y + row_h), right, int(y + row_h))
            y += row_h

        # playhead at latest sample
        play_x = left + ((t_end - t0) / total) * width
        p.setPen(QPen(Qt.GlobalColor.red, 2, Qt.PenStyle.DashLine))
        p.drawLine(int(play_x), top - 10, int(play_x), bottom + 10)
        p.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        p.drawText(int(play_x) - 20, top - 15, "Ahora")


class HistorialVivoWindow(QMainWindow):
    def __init__(self, csv_path=None):
        super().__init__()
        self.setWindowTitle("MBE Control — UI4 Historial vivo (realidad CSV)")
        self.resize(1200, 700)
        self.setStyleSheet(MAIN_STYLE_SHEET)

        self.csv_path = csv_path
        self.file_pos = 0
        self.header = None
        self.samples = []  # (t, {cell: bool})
        self._line_buf = ""

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)

        header_row = QHBoxLayout()
        title = QLabel("UI4 — Línea de tiempo de la REALIDAD (CSV del monitor)")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #0d2a52;")
        header_row.addWidget(title)
        header_row.addStretch()

        self.btn_latest = QPushButton("CSV mas reciente")
        self.btn_latest.clicked.connect(self.attach_latest)
        self.btn_open = QPushButton("Abrir CSV...")
        self.btn_open.clicked.connect(self.pick_csv)
        self.btn_follow = QPushButton("Seguir automatico: ON")
        self.btn_follow.setCheckable(True)
        self.btn_follow.setChecked(True)
        self.btn_follow.clicked.connect(self._toggle_follow)
        self.btn_clear = QPushButton("Limpiar vista")
        self.btn_clear.clicked.connect(self.clear_view)
        for b in (self.btn_latest, self.btn_open, self.btn_follow, self.btn_clear):
            b.setStyleSheet(
                "QPushButton { background: #0d2a52; color: white; border: none; "
                "border-radius: 6px; padding: 8px 14px; font-weight: bold; }"
                "QPushButton:hover { background: #204a87; }"
                "QPushButton:checked { background: #27ae60; }"
            )
            header_row.addWidget(b)
        layout.addLayout(header_row)

        self.auto_follow = True

        self.lbl_file = QLabel("Sin archivo")
        self.lbl_file.setStyleSheet("color: #34495e; font-size: 13px;")
        layout.addWidget(self.lbl_file)

        self.lbl_stats = QLabel("Muestras: 0  |  t = 0.0 s")
        self.lbl_stats.setStyleSheet("color: #0d2a52; font-weight: bold;")
        layout.addWidget(self.lbl_stats)

        frame = QFrame()
        frame.setStyleSheet("QFrame { background: white; border: 1px solid #a0a0a0; border-radius: 8px; }")
        fl = QVBoxLayout(frame)
        self.timeline = RealityTimelineWidget()
        fl.addWidget(self.timeline)
        layout.addWidget(frame, stretch=1)

        hint = QLabel(
            "Esto dibuja lo que monitor_247.py está escribiendo en historial/*.csv "
            "(realidad). UI2 en main.py dibuja el plan de la receta JSON."
        )
        hint.setStyleSheet("color: #7f8c8d; font-size: 12px; font-style: italic;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.poll = QTimer(self)
        self.poll.setInterval(200)  # match sensor poll / live feel
        self.poll.timeout.connect(self.read_new_rows)
        self.poll.start()

        if self.csv_path and os.path.exists(self.csv_path):
            self.attach_file(self.csv_path)
        else:
            self.attach_latest()

    def _toggle_follow(self):
        self.auto_follow = self.btn_follow.isChecked()
        self.btn_follow.setText(
            "Seguir automatico: ON" if self.auto_follow else "Seguir automatico: OFF"
        )

    def clear_view(self):
        self.samples = []
        self.file_pos = 0
        self.header = None
        self._line_buf = ""
        self.timeline.set_samples([])
        self.lbl_stats.setText("Muestras: 0  |  t = 0.0 s")

    def attach_latest(self):
        path = latest_csv_path()
        if not path:
            self.lbl_file.setText("No hay archivos en historial/ todavía")
            return
        self.attach_file(path)

    def pick_csv(self):
        self.auto_follow = False
        self.btn_follow.setChecked(False)
        self.btn_follow.setText("Seguir automatico: OFF")
        folder = historial_dir()
        os.makedirs(folder, exist_ok=True)
        path, _ = QFileDialog.getOpenFileName(
            self, "Abrir historial CSV", folder, "CSV (*.csv)"
        )
        if path:
            self.attach_file(path)

    def attach_file(self, path):
        self.csv_path = path
        self.file_pos = 0
        self.header = None
        self._line_buf = ""
        self.samples = []
        self.lbl_file.setText(f"Leyendo: {path}")
        self.read_new_rows()

    def read_new_rows(self):
        # Auto-follow newest historial_*.csv while a growth is running
        if self.auto_follow:
            newest = latest_csv_path()
            if newest and newest != self.csv_path:
                self.attach_file(newest)
                return

        if not self.csv_path or not os.path.exists(self.csv_path):
            newest = latest_csv_path()
            if newest:
                self.attach_file(newest)
            return

        try:
            size = os.path.getsize(self.csv_path)
            if size < self.file_pos:
                self.file_pos = 0
                self.header = None
                self._line_buf = ""
                self.samples = []

            with open(self.csv_path, "r", encoding="utf-8", newline="") as f:
                f.seek(self.file_pos)
                chunk = f.read()
                self.file_pos = f.tell()

            if not chunk:
                return

            data = self._line_buf + chunk
            if "\n" in data:
                *complete, self._line_buf = data.split("\n")
            else:
                self._line_buf = data
                return

            new = False
            for line in complete:
                line = line.strip("\r")
                if not line:
                    continue
                row = next(csv.reader([line]))
                if self.header is None:
                    self.header = row
                    continue
                if not row or len(row) < 2:
                    continue
                try:
                    if len(self.header) == len(row):
                        mapped = dict(zip(self.header, row))
                        t = float(mapped.get("Tiempo_Global(s)", row[0]))
                        states = {c: parse_open(mapped.get(c, "CERRADA")) for c in CELLS}
                    else:
                        t = float(row[0])
                        states = {
                            "Ga": parse_open(row[1]) if len(row) > 1 else False,
                            "Al": parse_open(row[2]) if len(row) > 2 else False,
                            "In": parse_open(row[3]) if len(row) > 3 else False,
                            "As": parse_open(row[4]) if len(row) > 4 else False,
                            "N": parse_open(row[5]) if len(row) > 5 else False,
                        }
                except ValueError:
                    continue
                self.samples.append((t, states))
                new = True

            if new:
                if len(self.samples) > 50000:
                    self.samples = self.samples[-50000:]
                self.timeline.set_samples(self.samples)
                t_last = self.samples[-1][0] if self.samples else 0.0
                self.lbl_stats.setText(
                    f"Muestras: {len(self.samples)}  |  t = {t_last:.1f} s"
                )
        except OSError as e:
            self.lbl_file.setText(f"Error leyendo CSV: {e}")


def main():
    app = QApplication(sys.argv)
    path = sys.argv[1] if len(sys.argv) > 1 else None
    win = HistorialVivoWindow(path)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
