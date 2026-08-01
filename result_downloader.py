import csv
import os
import sqlite3
from datetime import datetime
from tkinter import filedialog, messagebox
import tkinter as tk
from tkinter import ttk

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors as rl_colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle,
        Paragraph, Spacer, HRFlowable
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


# ============================================================
#   THEME (matches main app)
# ============================================================
COLORS = {
    "bg_dark":      "#0D1117",
    "bg_card":      "#161B22",
    "bg_input":     "#21262D",
    "accent":       "#58A6FF",
    "accent2":      "#3FB950",
    "accent3":      "#F78166",
    "warning":      "#E3B341",
    "text_primary": "#E6EDF3",
    "text_muted":   "#8B949E",
    "border":       "#30363D",
    "gradient2":    "#0D2137",
}

FONTS = {
    "heading":  ("Segoe UI", 18, "bold"),
    "subhead":  ("Segoe UI", 13, "bold"),
    "body":     ("Segoe UI", 11),
    "body_b":   ("Segoe UI", 11, "bold"),
    "small":    ("Segoe UI", 9),
}


# ============================================================
#   MAIN CLASS
# ============================================================
class ResultDownloader:
    """
    Standalone result download module for Online Exam System.

    Usage inside online_exam_system.py:
    ─────────────────────────────────────────────────────────
    from result_downloader import ResultDownloader

    # Inside ResultsPage or StudentDashboard:
    ResultDownloader.show_download_dialog(
        parent    = self,          # tkinter parent widget
        db        = self.app.db,   # Database instance
        user      = self.app.current_user,  # dict with id, name, role
    )
    ─────────────────────────────────────────────────────────
    """

    # ── Public entry point ──────────────────────────────────
    @staticmethod
    def show_download_dialog(parent, db, user):
        """Open the styled download dialog window."""
        _DownloadDialog(parent, db, user)

    # ── PDF Export ──────────────────────────────────────────
    @staticmethod
    def export_pdf(filepath: str, results: list, user: dict, is_admin: bool = False):
        if not REPORTLAB_AVAILABLE:
            messagebox.showerror(
                "Library Missing",
                "reportlab is not installed.\n\nRun:  pip install reportlab"
            )
            return False

        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            leftMargin=2*cm, rightMargin=2*cm,
            topMargin=2*cm,  bottomMargin=2*cm,
        )

        styles = getSampleStyleSheet()
        story  = []

        # ── Colour helpers ──────────────────────────────────
        BLUE   = rl_colors.HexColor("#58A6FF")
        GREEN  = rl_colors.HexColor("#3FB950")
        RED    = rl_colors.HexColor("#F78166")
        YELLOW = rl_colors.HexColor("#E3B341")
        DARK   = rl_colors.HexColor("#0D1117")
        CARD   = rl_colors.HexColor("#161B22")
        MUTED  = rl_colors.HexColor("#8B949E")
        WHITE  = rl_colors.white

        # ── Title ───────────────────────────────────────────
        title_style = ParagraphStyle(
            "Title",
            fontName="Helvetica-Bold",
            fontSize=22, textColor=WHITE,
            backColor=DARK, alignment=TA_CENTER,
            spaceAfter=4, spaceBefore=4,
            leading=28, borderPad=10,
        )
        sub_style = ParagraphStyle(
            "Sub",
            fontName="Helvetica",
            fontSize=10, textColor=MUTED,
            alignment=TA_CENTER, spaceAfter=2,
        )
        label_style = ParagraphStyle(
            "Label",
            fontName="Helvetica-Bold",
            fontSize=9, textColor=MUTED,
        )
        value_style = ParagraphStyle(
            "Value",
            fontName="Helvetica-Bold",
            fontSize=12, textColor=WHITE,
        )

        story.append(Paragraph("🎓  Online Exam System", title_style))
        story.append(Paragraph("Official Examination Result Report", sub_style))
        story.append(Spacer(1, 0.3*cm))
        story.append(HRFlowable(width="100%", thickness=1, color=BLUE))
        story.append(Spacer(1, 0.4*cm))

        # ── User info box ────────────────────────────────────
        generated = datetime.now().strftime("%d %B %Y, %I:%M %p")
        if is_admin:
            info_data = [
                ["Report Type", "All Students — Admin Export"],
                ["Generated On", generated],
                ["Total Records", str(len(results))],
            ]
        else:
            passed  = sum(1 for r in results if r["status"] == "PASS")
            failed  = len(results) - passed
            avg_pct = round(sum(r["percentage"] for r in results) / len(results), 1) if results else 0
            info_data = [
                ["Student Name",   user.get("name", "—")],
                ["Username",       user.get("username", "—")],
                ["Total Attempts", str(len(results))],
                ["Passed",         str(passed)],
                ["Failed",         str(failed)],
                ["Average Score",  f"{avg_pct}%"],
                ["Generated On",   generated],
            ]

        info_table = Table(
            [[Paragraph(k, label_style), Paragraph(v, value_style)] for k, v in info_data],
            colWidths=[5*cm, 11*cm]
        )
        info_table.setStyle(TableStyle([
            ("BACKGROUND",   (0,0), (-1,-1), CARD),
            ("TEXTCOLOR",    (0,0), (-1,-1), WHITE),
            ("ROWBACKGROUNDS",(0,0),(-1,-1),[CARD, rl_colors.HexColor("#1C2532")]),
            ("GRID",         (0,0), (-1,-1), 0.3, rl_colors.HexColor("#30363D")),
            ("LEFTPADDING",  (0,0), (-1,-1), 10),
            ("RIGHTPADDING", (0,0), (-1,-1), 10),
            ("TOPPADDING",   (0,0), (-1,-1), 6),
            ("BOTTOMPADDING",(0,0), (-1,-1), 6),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.5*cm))
        story.append(HRFlowable(width="100%", thickness=0.5, color=rl_colors.HexColor("#30363D")))
        story.append(Spacer(1, 0.4*cm))

        # ── Results table ────────────────────────────────────
        hdr_style = ParagraphStyle("Hdr", fontName="Helvetica-Bold",
                                   fontSize=8, textColor=BLUE, alignment=TA_CENTER)
        cell_style = ParagraphStyle("Cell", fontName="Helvetica",
                                    fontSize=8, textColor=WHITE, alignment=TA_CENTER)

        if is_admin:
            headers = ["#", "Student", "Subject", "Score", "Percentage", "Grade", "Status", "Date"]
            col_w   = [0.8*cm, 4*cm, 3.5*cm, 2*cm, 2.5*cm, 1.5*cm, 1.8*cm, 3.2*cm]
            rows = [[Paragraph(h, hdr_style) for h in headers]]
            for i, r in enumerate(results, 1):
                status_color = GREEN if r["status"] == "PASS" else RED
                s_style = ParagraphStyle("S", fontName="Helvetica-Bold",
                                         fontSize=8, textColor=status_color,
                                         alignment=TA_CENTER)
                rows.append([
                    Paragraph(str(i), cell_style),
                    Paragraph(str(r["student_name"]), cell_style),
                    Paragraph(str(r["subject_name"]), cell_style),
                    Paragraph(f"{r['score']}/{r['total_marks']}", cell_style),
                    Paragraph(f"{r['percentage']}%", cell_style),
                    Paragraph(str(r["grade"]), cell_style),
                    Paragraph(str(r["status"]), s_style),
                    Paragraph(str(r["attempt_date"])[:10], cell_style),
                ])
        else:
            headers = ["#", "Subject", "Score", "Percentage", "Grade", "Status", "Time", "Date"]
            col_w   = [0.8*cm, 4.5*cm, 2*cm, 2.5*cm, 1.5*cm, 1.8*cm, 2*cm, 3.2*cm]
            rows = [[Paragraph(h, hdr_style) for h in headers]]
            for i, r in enumerate(results, 1):
                status_color = GREEN if r["status"] == "PASS" else RED
                s_style = ParagraphStyle("S", fontName="Helvetica-Bold",
                                         fontSize=8, textColor=status_color,
                                         alignment=TA_CENTER)
                mins, secs = divmod(r["time_taken"], 60)
                rows.append([
                    Paragraph(str(i), cell_style),
                    Paragraph(str(r["subject_name"]), cell_style),
                    Paragraph(f"{r['score']}/{r['total_marks']}", cell_style),
                    Paragraph(f"{r['percentage']}%", cell_style),
                    Paragraph(str(r["grade"]), cell_style),
                    Paragraph(str(r["status"]), s_style),
                    Paragraph(f"{mins}m {secs}s", cell_style),
                    Paragraph(str(r["attempt_date"])[:10], cell_style),
                ])

        res_table = Table(rows, colWidths=col_w, repeatRows=1)
        res_table.setStyle(TableStyle([
            # Header row
            ("BACKGROUND",    (0,0), (-1,0),  rl_colors.HexColor("#0D2137")),
            ("TEXTCOLOR",     (0,0), (-1,0),  BLUE),
            ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
            ("FONTSIZE",      (0,0), (-1,0),  8),
            ("BOTTOMPADDING", (0,0), (-1,0),  8),
            ("TOPPADDING",    (0,0), (-1,0),  8),
            # Data rows
            ("ROWBACKGROUNDS",(0,1), (-1,-1), [CARD, rl_colors.HexColor("#1A2030")]),
            ("GRID",          (0,0), (-1,-1), 0.3, rl_colors.HexColor("#30363D")),
            ("TOPPADDING",    (0,1), (-1,-1), 5),
            ("BOTTOMPADDING", (0,1), (-1,-1), 5),
            ("ALIGN",         (0,0), (-1,-1), "CENTER"),
            ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ]))
        story.append(res_table)
        story.append(Spacer(1, 0.6*cm))

        # ── Footer ───────────────────────────────────────────
        footer_style = ParagraphStyle(
            "Footer", fontName="Helvetica",
            fontSize=8, textColor=MUTED, alignment=TA_CENTER,
        )
        story.append(HRFlowable(width="100%", thickness=0.5,
                                color=rl_colors.HexColor("#30363D")))
        story.append(Spacer(1, 0.2*cm))
        story.append(Paragraph(
            f"Generated by Online Exam System  •  {generated}  •  Confidential",
            footer_style
        ))

        # ── Build PDF ────────────────────────────────────────
        doc.build(story)
        return True

    # ── CSV Export ──────────────────────────────────────────
    @staticmethod
    def export_csv(filepath: str, results: list, is_admin: bool = False):
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            if is_admin:
                writer.writerow([
                    "No.", "Student Name", "Subject", "Score",
                    "Total Marks", "Percentage", "Grade",
                    "Status", "Time Taken (sec)", "Date"
                ])
                for i, r in enumerate(results, 1):
                    writer.writerow([
                        i,
                        r["student_name"],
                        r["subject_name"],
                        r["score"],
                        r["total_marks"],
                        f"{r['percentage']}%",
                        r["grade"],
                        r["status"],
                        r["time_taken"],
                        r["attempt_date"]
                    ])
            else:
                writer.writerow([
                    "No.", "Subject", "Score", "Total Marks",
                    "Percentage", "Grade", "Status",
                    "Time Taken (sec)", "Date"
                ])
                for i, r in enumerate(results, 1):
                    writer.writerow([
                        i,
                        r["subject_name"],
                        r["score"],
                        r["total_marks"],
                        f"{r['percentage']}%",
                        r["grade"],
                        r["status"],
                        r["time_taken"],
                        r["attempt_date"]
                    ])
        return True

    # ── TXT Export ──────────────────────────────────────────
    @staticmethod
    def export_txt(filepath: str, results: list, user: dict, is_admin: bool = False):
        line  = "=" * 65
        tline = "-" * 65
        now   = datetime.now().strftime("%d %B %Y, %I:%M %p")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"{line}\n")
            f.write(f"         ONLINE EXAM SYSTEM — RESULT REPORT\n")
            f.write(f"{line}\n\n")

            if is_admin:
                f.write(f"  Report Type  : All Students (Admin Export)\n")
                f.write(f"  Total Records: {len(results)}\n")
            else:
                passed  = sum(1 for r in results if r["status"] == "PASS")
                failed  = len(results) - passed
                avg     = round(sum(r["percentage"] for r in results) / len(results), 1) if results else 0
                f.write(f"  Student Name : {user.get('name','')}\n")
                f.write(f"  Username     : {user.get('username','')}\n")
                f.write(f"  Attempts     : {len(results)}  (Passed: {passed}  Failed: {failed})\n")
                f.write(f"  Avg Score    : {avg}%\n")

            f.write(f"  Generated    : {now}\n")
            f.write(f"\n{line}\n")

            if is_admin:
                f.write(f"  {'#':<4} {'Student':<18} {'Subject':<20} {'Score':<8} {'%':<7} {'Grade':<6} {'Status'}\n")
            else:
                f.write(f"  {'#':<4} {'Subject':<22} {'Score':<8} {'%':<7} {'Grade':<6} {'Status':<6} {'Date'}\n")
            f.write(f"  {tline}\n")

            for i, r in enumerate(results, 1):
                if is_admin:
                    f.write(
                        f"  {i:<4} {r['student_name'][:17]:<18} "
                        f"{r['subject_name'][:19]:<20} "
                        f"{r['score']}/{r['total_marks']:<4} "
                        f"{r['percentage']:<7} {r['grade']:<6} {r['status']}\n"
                    )
                else:
                    mins, secs = divmod(r["time_taken"], 60)
                    f.write(
                        f"  {i:<4} {r['subject_name'][:21]:<22} "
                        f"{r['score']}/{r['total_marks']:<4} "
                        f"{r['percentage']:<7} {r['grade']:<6} "
                        f"{r['status']:<6} {r['attempt_date'][:10]}\n"
                    )

            f.write(f"\n{line}\n")
            f.write(f"  End of Report — Online Exam System\n")
            f.write(f"{line}\n")
        return True


# ============================================================
#   DOWNLOAD DIALOG WINDOW
# ============================================================
class _DownloadDialog(tk.Toplevel):
    def __init__(self, parent, db, user):
        super().__init__(parent)
        self.db       = db
        self.user     = user
        self.is_admin = user.get("role") == "admin"

        self.title("Download Results")
        self.geometry("520x540")
        self.resizable(False, False)
        self.configure(bg=COLORS["bg_dark"])
        self.transient(parent)
        self.grab_set()

        # Center over parent
        self.update_idletasks()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        x  = px + (pw - 520) // 2
        y  = py + (ph - 540) // 2
        self.geometry(f"+{x}+{y}")

        self._build()
        self._load_preview()

    # ── Build UI ────────────────────────────────────────────
    def _build(self):
        # ── Header ──────────────────────────────────────────
        hdr = tk.Frame(self, bg=COLORS["gradient2"], height=72)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        tk.Label(hdr, text="⬇  Download Results",
                 font=FONTS["heading"],
                 bg=COLORS["gradient2"],
                 fg=COLORS["text_primary"]).place(relx=0.04, rely=0.5, anchor="w")

        tk.Frame(self, bg=COLORS["border"], height=1).pack(fill="x")

        # ── Body ────────────────────────────────────────────
        body = tk.Frame(self, bg=COLORS["bg_dark"])
        body.pack(fill="both", expand=True, padx=24, pady=20)

        # Preview stats
        preview_card = tk.Frame(body, bg=COLORS["bg_card"],
                                highlightbackground=COLORS["border"],
                                highlightthickness=1)
        preview_card.pack(fill="x", pady=(0, 18))

        tk.Label(preview_card, text="📋  Result Summary",
                 font=FONTS["body_b"],
                 bg=COLORS["bg_card"],
                 fg=COLORS["accent"]).pack(anchor="w", padx=14, pady=(10,4))

        self.preview_frame = tk.Frame(preview_card, bg=COLORS["bg_card"])
        self.preview_frame.pack(fill="x", padx=14, pady=(0,10))

        # Format selector
        tk.Label(body, text="Select Export Format",
                 font=FONTS["body_b"],
                 bg=COLORS["bg_dark"],
                 fg=COLORS["text_primary"]).pack(anchor="w", pady=(0,8))

        fmt_frame = tk.Frame(body, bg=COLORS["bg_dark"])
        fmt_frame.pack(fill="x", pady=(0,16))

        self.fmt_var = tk.StringVar(value="pdf")
        formats = [
            ("pdf", "📄 PDF Report",   "Professional formatted report", COLORS["accent"]),
            ("csv", "📊 CSV Spreadsheet", "Open in Excel / Google Sheets", COLORS["accent2"]),
            ("txt", "📝 Text File",    "Simple plain-text report",      COLORS["warning"]),
        ]

        self.fmt_cards = {}
        for val, label, desc, color in formats:
            card = tk.Frame(fmt_frame, bg=COLORS["bg_card"],
                            highlightbackground=COLORS["border"],
                            highlightthickness=1, cursor="hand2")
            card.pack(fill="x", pady=4)

            inner = tk.Frame(card, bg=COLORS["bg_card"])
            inner.pack(fill="x", padx=12, pady=8)

            rb = tk.Radiobutton(inner, variable=self.fmt_var, value=val,
                                bg=COLORS["bg_card"],
                                activebackground=COLORS["bg_card"],
                                selectcolor=COLORS["bg_input"],
                                fg=color, font=FONTS["body_b"],
                                text=label,
                                command=lambda c=card, v=val: self._on_fmt_select(v))
            rb.pack(side="left")

            tk.Label(inner, text=desc,
                     font=FONTS["small"],
                     bg=COLORS["bg_card"],
                     fg=COLORS["text_muted"]).pack(side="right")

            card.bind("<Button-1>", lambda e, v=val: self._select_fmt_card(v))
            self.fmt_cards[val] = card

        self._on_fmt_select("pdf")

        # Scope selector (admin only)
        if self.is_admin:
            tk.Frame(body, bg=COLORS["border"], height=1).pack(fill="x", pady=(0,12))
            scope_row = tk.Frame(body, bg=COLORS["bg_dark"])
            scope_row.pack(fill="x", pady=(0,4))
            tk.Label(scope_row, text="Export Scope:",
                     font=FONTS["body_b"],
                     bg=COLORS["bg_dark"],
                     fg=COLORS["text_primary"]).pack(side="left")
            self.scope_var = tk.StringVar(value="all")
            tk.Radiobutton(scope_row, text="All Students",
                           variable=self.scope_var, value="all",
                           bg=COLORS["bg_dark"], fg=COLORS["text_primary"],
                           selectcolor=COLORS["bg_input"],
                           font=FONTS["body"]).pack(side="left", padx=12)
        else:
            self.scope_var = None

        # ── Download button ──────────────────────────────────
        btn_frame = tk.Frame(self, bg=COLORS["bg_dark"])
        btn_frame.pack(fill="x", padx=24, pady=(0,16))

        pdf_note = "" if REPORTLAB_AVAILABLE else "  (pip install reportlab for PDF)"
        self.dl_btn = tk.Button(
            btn_frame,
            text=f"⬇  Download{pdf_note}",
            font=FONTS["body_b"],
            bg=COLORS["accent"],
            fg="white",
            activebackground=COLORS["gradient2"],
            activeforeground="white",
            relief="flat", bd=0, cursor="hand2",
            pady=12,
            command=self._download
        )
        self.dl_btn.pack(fill="x")
        self.dl_btn.bind("<Enter>", lambda e: self.dl_btn.config(bg=COLORS["gradient2"]))
        self.dl_btn.bind("<Leave>", lambda e: self.dl_btn.config(bg=COLORS["accent"]))

        tk.Button(
            btn_frame, text="Cancel",
            font=FONTS["small"],
            bg=COLORS["bg_input"],
            fg=COLORS["text_muted"],
            activebackground=COLORS["border"],
            relief="flat", bd=0, cursor="hand2",
            pady=8,
            command=self.destroy
        ).pack(fill="x", pady=(6,0))

    # ── Load preview stats ───────────────────────────────────
    def _load_preview(self):
        for w in self.preview_frame.winfo_children():
            w.destroy()

        if self.is_admin:
            results = self.db.get_all_results()
            students = self.db.get_all_students()
            passed   = sum(1 for r in results if r["status"] == "PASS")
            stats = [
                ("Total Students",  str(len(students)),        COLORS["accent"]),
                ("Total Exams",     str(len(results)),          COLORS["purple"]),
                ("Passed",          str(passed),                COLORS["accent2"]),
                ("Failed",          str(len(results) - passed), COLORS["accent3"]),
            ]
        else:
            results = self.db.get_results(self.user["id"])
            passed  = sum(1 for r in results if r["status"] == "PASS")
            avg     = round(sum(r["percentage"] for r in results) / len(results), 1) if results else 0
            stats = [
                ("Total Exams",  str(len(results)),          COLORS["accent"]),
                ("Passed",       str(passed),                 COLORS["accent2"]),
                ("Failed",       str(len(results) - passed),  COLORS["accent3"]),
                ("Average",      f"{avg}%",                   COLORS["warning"]),
            ]

        for label, val, color in stats:
            col = tk.Frame(self.preview_frame, bg=COLORS["bg_card"])
            col.pack(side="left", expand=True)
            tk.Label(col, text=val,
                     font=("Segoe UI", 18, "bold"),
                     bg=COLORS["bg_card"], fg=color).pack()
            tk.Label(col, text=label,
                     font=FONTS["small"],
                     bg=COLORS["bg_card"],
                     fg=COLORS["text_muted"]).pack()

    # ── Format card selection ───
    def _on_fmt_select(self, val):
        self.fmt_var.set(val)
        for v, card in self.fmt_cards.items():
            if v == val:
                card.config(highlightbackground=COLORS["accent"])
            else:
                card.config(highlightbackground=COLORS["border"])

    def _select_fmt_card(self, val):
        self._on_fmt_select(val)

    # ── Download action ──────────────────────────────────────
    def _download(self):
        fmt = self.fmt_var.get()

        # Collect results
        if self.is_admin:
            results = self.db.get_all_results()
            results = [dict(r) for r in results]
        else:
            results = self.db.get_results(self.user["id"])
            results = [dict(r) for r in results]

        if not results:
            messagebox.showinfo("No Data", "No results found to download.")
            return

        # File type extensions and filters
        ext_map = {"pdf": ".pdf", "csv": ".csv", "txt": ".txt"}
        type_map = {
            "pdf": [("PDF files", "*.pdf")],
            "csv": [("CSV files", "*.csv")],
            "txt": [("Text files", "*.txt")],
        }

        # Suggest default filename
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        who = "all_students" if self.is_admin else self.user.get("username","user")
        default_name = f"exam_results_{who}_{now}{ext_map[fmt]}"

        filepath = filedialog.asksaveasfilename(
            defaultextension=ext_map[fmt],
            filetypes=type_map[fmt],
            initialfile=default_name,
            title="Save Results As"
        )
        if not filepath:
            return  # user cancelled

        # ── Export ──────────────────────────────────────────
        try:
            self.dl_btn.config(text="⏳ Generating...", state="disabled")
            self.update()

            success = False
            if fmt == "pdf":
                success = ResultDownloader.export_pdf(
                    filepath, results, self.user, self.is_admin
                )
            elif fmt == "csv":
                success = ResultDownloader.export_csv(
                    filepath, results, self.is_admin
                )
            elif fmt == "txt":
                success = ResultDownloader.export_txt(
                    filepath, results, self.user, self.is_admin
                )

            if success:
                self.dl_btn.config(text="✅ Downloaded!", bg=COLORS["accent2"])
                messagebox.showinfo(
                    "Download Complete",
                    f"Results saved successfully!\n\n📁 {filepath}"
                )
                self.destroy()
            else:
                self.dl_btn.config(
                    text="⬇  Download", state="normal",
                    bg=COLORS["accent"]
                )

        except Exception as ex:
            self.dl_btn.config(
                text="⬇  Download", state="normal",
                bg=COLORS["accent"]
            )
            messagebox.showerror("Export Error", f"Failed to save file:\n{ex}")


# ============================================================
#   STANDALONE TEST (run this file directly to test)
# ============================================================
if __name__ == "__main__":
    import sqlite3

    # ── Create a tiny test DB ────────────────────────────────
    TEST_DB = "exam_system.db"

    class MockDB:
        """Reads from the real exam_system.db for testing."""
        def __init__(self):
            self.conn = sqlite3.connect(TEST_DB)
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()

        def get_results(self, user_id):
            self.cursor.execute(
                """SELECT r.*, s.name AS subject_name
                   FROM exam_results r
                   JOIN subjects s ON r.subject_id = s.id
                   WHERE r.user_id=?
                   ORDER BY r.attempt_date DESC""",
                (user_id,)
            )
            return self.cursor.fetchall()

        def get_all_results(self):
            self.cursor.execute(
                """SELECT r.*, u.name AS student_name, s.name AS subject_name
                   FROM exam_results r
                   JOIN users u ON r.user_id = u.id
                   JOIN subjects s ON r.subject_id = s.id
                   ORDER BY r.attempt_date DESC"""
            )
            return self.cursor.fetchall()

        def get_all_students(self):
            self.cursor.execute("SELECT * FROM users WHERE role='student'")
            return self.cursor.fetchall()

    root = tk.Tk()
    root.geometry("400x300")
    root.configure(bg=COLORS["bg_dark"])
    root.title("Test Result Downloader")

    mock_db   = MockDB()
    mock_user = {"id": 1, "name": "Test Student", "username": "admin", "role": "admin"}

    tk.Label(root, text="Result Downloader Test",
             font=FONTS["heading"],
             bg=COLORS["bg_dark"], fg=COLORS["text_primary"]).pack(pady=40)

    tk.Button(
        root, text="Open Download Dialog",
        font=FONTS["body_b"],
        bg=COLORS["accent"], fg="white",
        relief="flat", pady=10, padx=20,
        cursor="hand2",
        command=lambda: ResultDownloader.show_download_dialog(root, mock_db, mock_user)
    ).pack()

    root.mainloop()