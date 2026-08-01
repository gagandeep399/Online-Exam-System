#   ONLINE EXAM SYSTEM
#   Technologies: Python, Tkinter, SQLite3, PIL (Pillow)
import tkinter as tk
from tkinter import ttk, messagebox, font
import sqlite3
import hashlib
import os
import time
import threading
from datetime import datetime
from result_downloader import ResultDownloader



try:
    from PIL import Image, ImageTk, ImageDraw, ImageFilter
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


DB_NAME = "exam_system.db"

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
    "hover":        "#1F2937",
    "purple":       "#BC8CFF",
    "gradient1":    "#1C2D40",
    "gradient2":    "#0D2137",
}

FONTS = {
    "title":    ("Segoe UI", 28, "bold"),
    "heading":  ("Segoe UI", 18, "bold"),
    "subhead":  ("Segoe UI", 14, "bold"),
    "body":     ("Segoe UI", 11),
    "body_b":   ("Segoe UI", 11, "bold"),
    "small":    ("Segoe UI", 9),
    "mono":     ("Consolas", 11),
    "big":      ("Segoe UI", 48, "bold"),
    "timer":    ("Consolas", 22, "bold"),
}



class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self._create_tables()
        self._seed_data()

    def _create_tables(self):
        self.cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            email       TEXT    UNIQUE NOT NULL,
            username    TEXT    UNIQUE NOT NULL,
            password    TEXT    NOT NULL,
            role        TEXT    DEFAULT 'student',
            created_at  TEXT    DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS subjects (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL UNIQUE,
            description TEXT,
            total_marks INTEGER DEFAULT 100,
            duration    INTEGER DEFAULT 30
        );

        CREATE TABLE IF NOT EXISTS questions (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id     INTEGER NOT NULL,
            question_text  TEXT    NOT NULL,
            option_a       TEXT    NOT NULL,
            option_b       TEXT    NOT NULL,
            option_c       TEXT    NOT NULL,
            option_d       TEXT    NOT NULL,
            correct_option TEXT    NOT NULL,
            marks          INTEGER DEFAULT 1,
            FOREIGN KEY (subject_id) REFERENCES subjects(id)
        );

        CREATE TABLE IF NOT EXISTS exam_results (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       INTEGER NOT NULL,
            subject_id    INTEGER NOT NULL,
            score         INTEGER DEFAULT 0,
            total_marks   INTEGER DEFAULT 0,
            percentage    REAL    DEFAULT 0.0,
            grade         TEXT    DEFAULT 'F',
            status        TEXT    DEFAULT 'FAIL',
            time_taken    INTEGER DEFAULT 0,
            attempt_date  TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (user_id)    REFERENCES users(id),
            FOREIGN KEY (subject_id) REFERENCES subjects(id)
        );
        """)
        self.conn.commit()

    def _seed_data(self):
        # Admin account
        admin_pw = self._hash("admin123")
        self.cursor.execute(
            "INSERT OR IGNORE INTO users (name,email,username,password,role) VALUES (?,?,?,?,?)",
            ("Administrator", "admin@exam.com", "admin", admin_pw, "admin")
        )
        # Subjects
        subjects = [
            ("Python Programming",  "Test your Python coding knowledge",         10, 15),
            ("Mathematics",         "Algebra, Geometry and Arithmetic problems",  10, 15),
            ("General Knowledge",   "Current affairs and world knowledge",         10, 15),
            ("Computer Science",    "OS, Networking and Database concepts",         10, 15),
        ]
        self.cursor.executemany(
            "INSERT OR IGNORE INTO subjects (name,description,total_marks,duration) VALUES (?,?,?,?)",
            subjects
        )
        self.conn.commit()

        # Questions
        questions_data = [
            # Python (subject_id=1)
            (1,"What is the output of print(type([]))?","<class 'list'>","<class 'tuple'>","<class 'dict'>","<class 'set'>","A",1),
            (1,"Which keyword defines a function in Python?","function","def","func","define","B",1),
            (1,'What does len("Hello") return?',"4","5","6","Error","B",1),
            (1,"Which is a mutable data type?","tuple","string","list","int","C",1),
            (1,"Symbol for single-line comments in Python?","//","#","/*","--","B",1),
            (1,"How to create a dictionary in Python?","dict=[]","dict=()","dict={}","dict=<>","C",1),
            (1,"Method to add item to a list?","add()","insert()","append()","push()","C",1),
            (1,'What does "self" represent in a class?',"Class method","Current instance","Static variable","None","B",1),
            (1,"Module for regular expressions?","re","regex","regexp","pattern","A",1),
            (1,'Open a file in read mode?','open("f","w")','open("f","r")','open("f","a")','open("f","x")',"B",1),
            # Math (subject_id=2)
            (2,"What is √144?","11","12","13","14","B",1),
            (2,"If 2x + 5 = 15, x = ?","4","5","6","7","B",1),
            (2,"15% of 200 = ?","25","30","35","40","B",1),
            (2,"Area of circle, r=7 (π=22/7)?","144","154","164","174","B",1),
            (2,"LCM of 4 and 6?","10","12","18","24","B",1),
            (2,"2^10 = ?","512","1024","2048","256","B",1),
            (2,"Sum of angles in a triangle?","90°","180°","270°","360°","B",1),
            (2,"log10(1000) = ?","2","3","4","5","B",1),
            (2,"Hypotenuse if a=3, b=4?","4","5","6","7","B",1),
            (2,"Perimeter of rectangle L=8, W=5?","24","26","28","30","B",1),
            # GK (subject_id=3)
            (3,"Capital of France?","Berlin","Madrid","Paris","Rome","C",1),
            (3,"Who invented the telephone?","Thomas Edison","Alexander Graham Bell","Nikola Tesla","Isaac Newton","B",1),
            (3,"Which planet is called the Red Planet?","Venus","Jupiter","Mars","Saturn","C",1),
            (3,"Largest ocean on Earth?","Atlantic","Indian","Arctic","Pacific","D",1),
            (3,"How many continents are there?","5","6","7","8","C",1),
            (3,"Who wrote Romeo and Juliet?","Charles Dickens","William Shakespeare","Jane Austen","Mark Twain","B",1),
            (3,"Chemical symbol for Gold?","Go","Gd","Au","Ag","C",1),
            (3,"Year World War II ended?","1943","1944","1945","1946","C",1),
            (3,"Land of the Rising Sun?","China","South Korea","Japan","Thailand","C",1),
            (3,"Fastest land animal?","Lion","Cheetah","Leopard","Horse","B",1),
            # CS (subject_id=4)
            (4,"CPU stands for?","Central Processing Unit","Computer Processing Unit","Central Program Unit","Core Processing Unit","A",1),
            (4,"RAM stands for?","Read Access Memory","Random Access Memory","Rapid Access Memory","Remote Access Memory","B",1),
            (4,"Which is NOT an operating system?","Windows","Linux","Oracle","macOS","C",1),
            (4,"Full form of HTML?","HyperText Markup Language","HyperText Machine Language","HighText Markup Language","Hyper Transfer Markup Language","A",1),
            (4,"Data structure using LIFO?","Queue","Stack","Array","Tree","B",1),
            (4,"Binary of decimal 10?","1010","1100","1001","0110","A",1),
            (4,"Protocol used to send emails?","FTP","HTTP","SMTP","POP3","C",1),
            (4,"SQL stands for?","Structured Query Language","Simple Query Language","Standard Query Logic","Sequential Query Language","A",1),
            (4,"Best average-case sorting algorithm?","Bubble Sort","Selection Sort","Quick Sort","Insertion Sort","C",1),
            (4,"Purpose of an IP address?","Identify a device on a network","Store files","Run programs","Display graphics","A",1),
        ]
        self.cursor.executemany(
            "INSERT OR IGNORE INTO questions (subject_id,question_text,option_a,option_b,option_c,option_d,correct_option,marks) VALUES (?,?,?,?,?,?,?,?)",
            questions_data
        )
        self.conn.commit()

    @staticmethod
    def _hash(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def login(self, username: str, password: str):
        pw = self._hash(password)
        self.cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=?", (username, pw)
        )
        return self.cursor.fetchone()

    def register(self, name, email, username, password):
        try:
            pw = self._hash(password)
            self.cursor.execute(
                "INSERT INTO users (name,email,username,password) VALUES (?,?,?,?)",
                (name, email, username, pw)
            )
            self.conn.commit()
            return True, "Registration successful!"
        except sqlite3.IntegrityError as e:
            if "email" in str(e):
                return False, "Email already exists!"
            return False, "Username already taken!"

    def get_subjects(self):
        self.cursor.execute("SELECT * FROM subjects")
        return self.cursor.fetchall()

    def get_questions(self, subject_id):
        self.cursor.execute(
            "SELECT * FROM questions WHERE subject_id=? ORDER BY RANDOM()",
            (subject_id,)
        )
        return self.cursor.fetchall()

    def save_result(self, user_id, subject_id, score, total, time_taken):
        percentage = round((score / total) * 100, 2) if total else 0
        grade = self._get_grade(percentage)
        status = "PASS" if percentage >= 40 else "FAIL"
        self.cursor.execute(
            """INSERT INTO exam_results
               (user_id,subject_id,score,total_marks,percentage,grade,status,time_taken)
               VALUES (?,?,?,?,?,?,?,?)""",
            (user_id, subject_id, score, total, percentage, grade, status, time_taken)
        )
        self.conn.commit()
        return percentage, grade, status

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
        self.cursor.execute("SELECT * FROM users WHERE role='student' ORDER BY created_at DESC")
        return self.cursor.fetchall()

    @staticmethod
    def _get_grade(percentage):
        if percentage >= 90: return "A+"
        if percentage >= 80: return "A"
        if percentage >= 70: return "B"
        if percentage >= 60: return "C"
        if percentage >= 50: return "D"
        return "F"

    def close(self):
        self.conn.close()

def make_icon_label(parent, icon, size=32, **kw):
    """Create a canvas-drawn icon (no external image needed)."""
    c = tk.Canvas(parent, width=size, height=size,
                  bg=kw.get("bg", COLORS["bg_card"]),
                  highlightthickness=0)
    icons = {
        "user":   lambda: [c.create_oval(8,4,24,20,fill=COLORS["accent"],outline=""),
                            c.create_arc(2,18,30,38,start=0,extent=180,fill=COLORS["accent"],outline="")],
        "lock":   lambda: [c.create_rectangle(8,14,24,28,fill=COLORS["accent"],outline="",width=0),
                            c.create_arc(8,5,24,18,start=0,extent=180,outline=COLORS["accent"],width=3,style="arc")],
        "exam":   lambda: [c.create_rectangle(6,4,26,28,fill=COLORS["accent"],outline=""),
                            c.create_line(10,10,22,10,fill="white",width=2),
                            c.create_line(10,15,22,15,fill="white",width=2),
                            c.create_line(10,20,18,20,fill="white",width=2)],
        "chart":  lambda: [c.create_rectangle(4,20,10,28,fill=COLORS["accent2"],outline=""),
                            c.create_rectangle(13,12,19,28,fill=COLORS["accent"],outline=""),
                            c.create_rectangle(22,6,28,28,fill=COLORS["purple"],outline="")],
        "trophy": lambda: [c.create_arc(6,4,26,22,start=0,extent=180,fill=COLORS["warning"],outline=""),
                            c.create_rectangle(13,20,19,28,fill=COLORS["warning"],outline=""),
                            c.create_line(9,28,23,28,fill=COLORS["warning"],width=3)],
        "home":   lambda: [c.create_polygon(16,4,28,16,28,28,4,28,4,16,fill=COLORS["accent"],outline=""),
                            c.create_rectangle(12,20,20,28,fill=COLORS["bg_card"],outline="")],
        "logout": lambda: [c.create_rectangle(4,8,20,24,fill=COLORS["accent3"],outline=""),
                            c.create_line(18,16,28,16,fill=COLORS["accent3"],width=2,arrow="last")],
    }
    if icon in icons:
        icons[icon]()
    return c


def rounded_frame(parent, **kw):
    """A frame styled as a card."""
    f = tk.Frame(parent, bg=kw.get("bg", COLORS["bg_card"]),
                 highlightbackground=kw.get("border", COLORS["border"]),
                 highlightthickness=1)
    return f


# ============================================================
#   MAIN APPLICATION
# ============================================================
class OnlineExamApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.current_user = None

        self.title("🎓 Online Exam System")
        self.geometry("1100x720")
        self.minsize(900, 600)
        self.configure(bg=COLORS["bg_dark"])
        self.resizable(True, True)

        # Center window
        self.update_idletasks()
        w, h = 1100, 720
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

        self.container = tk.Frame(self, bg=COLORS["bg_dark"])
        self.container.pack(fill="both", expand=True)

        self.frames = {}
        self._show_login()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        self.db.close()
        self.destroy()

    def _clear(self):
        for w in self.container.winfo_children():
            w.destroy()

    def _show_login(self):
        self._clear()
        LoginPage(self.container, self).pack(fill="both", expand=True)

    def _show_register(self):
        self._clear()
        RegisterPage(self.container, self).pack(fill="both", expand=True)

    def _show_dashboard(self):
        self._clear()
        if self.current_user["role"] == "admin":
            AdminDashboard(self.container, self).pack(fill="both", expand=True)
        else:
            StudentDashboard(self.container, self).pack(fill="both", expand=True)

    def _show_exam(self, subject):
        self._clear()
        ExamPage(self.container, self, subject).pack(fill="both", expand=True)

    def _show_results(self):
        self._clear()
        ResultsPage(self.container, self).pack(fill="both", expand=True)


# ============================================================
#   REUSABLE UI COMPONENTS
# ============================================================
class StyledEntry(tk.Frame):
    """A styled entry widget with label and optional icon."""
    def __init__(self, parent, label, show="", **kw):
        super().__init__(parent, bg=kw.get("bg", COLORS["bg_card"]))
        self.bg_color = kw.get("bg", COLORS["bg_card"])

        tk.Label(self, text=label, font=FONTS["small"],
                 bg=self.bg_color, fg=COLORS["text_muted"]).pack(anchor="w", pady=(0,3))

        entry_frame = tk.Frame(self, bg=COLORS["bg_input"],
                               highlightbackground=COLORS["border"],
                               highlightthickness=1)
        entry_frame.pack(fill="x")

        self.var = tk.StringVar()
        self.entry = tk.Entry(entry_frame, textvariable=self.var, show=show,
                              font=FONTS["body"], bg=COLORS["bg_input"],
                              fg=COLORS["text_primary"], insertbackground=COLORS["accent"],
                              relief="flat", bd=8)
        self.entry.pack(fill="x")

        entry_frame.bind("<Enter>", lambda e: entry_frame.config(highlightbackground=COLORS["accent"]))
        entry_frame.bind("<Leave>", lambda e: entry_frame.config(highlightbackground=COLORS["border"]))

    def get(self): return self.var.get()
    def set(self, v): self.var.set(v)


class FancyButton(tk.Button):
    def __init__(self, parent, text, command=None, style="primary", **kw):
        colors = {
            "primary": (COLORS["accent"],    "#1C3D5A", COLORS["text_primary"]),
            "success": (COLORS["accent2"],   "#1A3A24", COLORS["text_primary"]),
            "danger":  (COLORS["accent3"],   "#3A1A1A", COLORS["text_primary"]),
            "warning": (COLORS["warning"],   "#3A2E1A", COLORS["bg_dark"]),
            "ghost":   (COLORS["border"],    COLORS["bg_input"], COLORS["text_muted"]),
        }
        bg, hover_bg, fg = colors.get(style, colors["primary"])
        self._bg = bg
        self._hover = hover_bg

        super().__init__(parent, text=text, command=command,
                         bg=bg, fg=fg, activebackground=hover_bg,
                         activeforeground=fg, font=kw.get("font", FONTS["body_b"]),
                         relief="flat", bd=0, cursor="hand2",
                         padx=kw.get("padx", 20), pady=kw.get("pady", 10),
                         **{k:v for k,v in kw.items() if k not in ("font","padx","pady")})

        self.bind("<Enter>", lambda e: self.config(bg=hover_bg))
        self.bind("<Leave>", lambda e: self.config(bg=bg))


# ============================================================
#   LOGIN PAGE
# ============================================================
class LoginPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS["bg_dark"])
        self.app = app
        self._build()

    def _build(self):
        # Left panel - decorative
        left = tk.Frame(self, bg=COLORS["gradient2"], width=400)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)
        self._draw_left_panel(left)

        # Right panel - login form
        right = tk.Frame(self, bg=COLORS["bg_dark"])
        right.pack(side="right", fill="both", expand=True)

        form = tk.Frame(right, bg=COLORS["bg_dark"])
        form.place(relx=0.5, rely=0.5, anchor="center")

        # Logo
        logo_frame = tk.Frame(form, bg=COLORS["bg_dark"])
        logo_frame.pack(pady=(0, 30))

        if PIL_AVAILABLE:
            self._draw_logo(logo_frame)
        else:
            tk.Label(logo_frame, text="🎓", font=("Segoe UI", 52),
                     bg=COLORS["bg_dark"]).pack()

        tk.Label(form, text="Welcome Back", font=FONTS["title"],
                 bg=COLORS["bg_dark"], fg=COLORS["text_primary"]).pack()
        tk.Label(form, text="Sign in to your exam portal",
                 font=FONTS["body"], bg=COLORS["bg_dark"],
                 fg=COLORS["text_muted"]).pack(pady=(4,28))

        # Form card
        card = rounded_frame(form, bg=COLORS["bg_card"])
        card.pack(ipadx=30, ipady=30)

        self.username_entry = StyledEntry(card, "USERNAME", bg=COLORS["bg_card"])
        self.username_entry.pack(fill="x", pady=(0,14))

        self.password_entry = StyledEntry(card, "PASSWORD", show="•", bg=COLORS["bg_card"])
        self.password_entry.pack(fill="x", pady=(0,20))

        FancyButton(card, "SIGN IN →", self._login, style="primary",
                    font=FONTS["subhead"], padx=0, pady=12).pack(fill="x")

        # Divider
        div = tk.Frame(card, bg=COLORS["border"], height=1)
        div.pack(fill="x", pady=16)

        reg_frame = tk.Frame(card, bg=COLORS["bg_card"])
        reg_frame.pack()
        tk.Label(reg_frame, text="Don't have an account?",
                 font=FONTS["small"], bg=COLORS["bg_card"],
                 fg=COLORS["text_muted"]).pack(side="left")

        reg_btn = tk.Label(reg_frame, text="  Register here",
                           font=("Segoe UI", 9, "underline"),
                           bg=COLORS["bg_card"], fg=COLORS["accent"],
                           cursor="hand2")
        reg_btn.pack(side="left")
        reg_btn.bind("<Button-1>", lambda e: self.app._show_register())

        # Demo hint
        tk.Label(form, text="Admin: admin / admin123",
                 font=FONTS["small"], bg=COLORS["bg_dark"],
                 fg=COLORS["text_muted"]).pack(pady=(16,0))

        # Bind Enter key
        self.password_entry.entry.bind("<Return>", lambda e: self._login())
        self.username_entry.entry.bind("<Return>", lambda e: self._login())
        self.username_entry.entry.focus()

    def _draw_left_panel(self, parent):
        tk.Frame(parent, bg=COLORS["gradient2"]).pack(expand=True)

        content = tk.Frame(parent, bg=COLORS["gradient2"])
        content.pack(expand=True, fill="both", padx=40)

        # Title
        tk.Label(content, text="📚", font=("Segoe UI", 60),
                 bg=COLORS["gradient2"]).pack(pady=(0, 16))

        tk.Label(content, text="Online\nExam System",
                 font=("Segoe UI", 30, "bold"),
                 bg=COLORS["gradient2"], fg=COLORS["text_primary"],
                 justify="center").pack()

        tk.Label(content, text="Test Your Knowledge\nAnytime. Anywhere.",
                 font=FONTS["body"], bg=COLORS["gradient2"],
                 fg=COLORS["text_muted"], justify="center").pack(pady=12)

        # Feature bullets
        features = [
            ("✦", "Multiple Subjects"),
            ("✦", "Timed Assessments"),
            ("✦", "Instant Results"),
            ("✦", "Progress Tracking"),
        ]
        feat_frame = tk.Frame(content, bg=COLORS["gradient2"])
        feat_frame.pack(pady=20)
        for icon, text in features:
            row = tk.Frame(feat_frame, bg=COLORS["gradient2"])
            row.pack(anchor="w", pady=4)
            tk.Label(row, text=icon, font=FONTS["body"],
                     bg=COLORS["gradient2"], fg=COLORS["accent"]).pack(side="left", padx=(0,8))
            tk.Label(row, text=text, font=FONTS["body"],
                     bg=COLORS["gradient2"], fg=COLORS["text_primary"]).pack(side="left")

        tk.Frame(parent, bg=COLORS["gradient2"]).pack(expand=True)

    def _draw_logo(self, parent):
        if not PIL_AVAILABLE:
            return
        size = 80
        img = Image.new("RGBA", (size, size), (0,0,0,0))
        draw = ImageDraw.Draw(img)
        draw.ellipse([0,0,size,size], fill=(88,166,255,200))
        photo = ImageTk.PhotoImage(img)
        lbl = tk.Label(parent, image=photo, bg=COLORS["bg_dark"])
        lbl.image = photo
        lbl.pack()
        tk.Label(parent, text="EXS", font=("Segoe UI", 16, "bold"),
                 bg=COLORS["bg_dark"], fg="white").place(relx=0.5, rely=0.5, anchor="center")

    def _login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if not username or not password:
            messagebox.showwarning("Input Required", "Please enter username and password.")
            return
        user = self.app.db.login(username, password)
        if user:
            self.app.current_user = dict(user)
            self.app._show_dashboard()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")
            self.password_entry.set("")


# ============================================================
#   REGISTER PAGE
# ============================================================
class RegisterPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS["bg_dark"])
        self.app = app
        self._build()

    def _build(self):
        outer = tk.Frame(self, bg=COLORS["bg_dark"])
        outer.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(outer, text="🎓 Create Account", font=FONTS["title"],
                 bg=COLORS["bg_dark"], fg=COLORS["text_primary"]).pack(pady=(0,4))
        tk.Label(outer, text="Join the exam portal today",
                 font=FONTS["body"], bg=COLORS["bg_dark"],
                 fg=COLORS["text_muted"]).pack(pady=(0,24))

        card = rounded_frame(outer, bg=COLORS["bg_card"])
        card.pack(ipadx=36, ipady=30)

        row1 = tk.Frame(card, bg=COLORS["bg_card"])
        row1.pack(fill="x", pady=(0,14))

        self.name_e  = StyledEntry(row1, "FULL NAME",  bg=COLORS["bg_card"])
        self.email_e = StyledEntry(row1, "EMAIL ADDRESS", bg=COLORS["bg_card"])
        self.name_e.pack(side="left", fill="x", expand=True, padx=(0,10))
        self.email_e.pack(side="left", fill="x", expand=True)

        self.user_e = StyledEntry(card, "USERNAME", bg=COLORS["bg_card"])
        self.user_e.pack(fill="x", pady=(0,14))

        row2 = tk.Frame(card, bg=COLORS["bg_card"])
        row2.pack(fill="x", pady=(0,20))
        self.pass_e  = StyledEntry(row2, "PASSWORD",        show="•", bg=COLORS["bg_card"])
        self.cpass_e = StyledEntry(row2, "CONFIRM PASSWORD", show="•", bg=COLORS["bg_card"])
        self.pass_e.pack(side="left", fill="x", expand=True, padx=(0,10))
        self.cpass_e.pack(side="left", fill="x", expand=True)

        FancyButton(card, "CREATE ACCOUNT →", self._register,
                    style="success", font=FONTS["subhead"],
                    padx=0, pady=12).pack(fill="x")

        div = tk.Frame(card, bg=COLORS["border"], height=1)
        div.pack(fill="x", pady=14)

        back_frame = tk.Frame(card, bg=COLORS["bg_card"])
        back_frame.pack()
        tk.Label(back_frame, text="Already have an account?",
                 font=FONTS["small"], bg=COLORS["bg_card"],
                 fg=COLORS["text_muted"]).pack(side="left")
        lnk = tk.Label(back_frame, text="  Login here",
                        font=("Segoe UI",9,"underline"),
                        bg=COLORS["bg_card"], fg=COLORS["accent"], cursor="hand2")
        lnk.pack(side="left")
        lnk.bind("<Button-1>", lambda e: self.app._show_login())

    def _register(self):
        name  = self.name_e.get().strip()
        email = self.email_e.get().strip()
        user  = self.user_e.get().strip()
        pw    = self.pass_e.get()
        cpw   = self.cpass_e.get()

        if not all([name, email, user, pw, cpw]):
            messagebox.showwarning("Missing Fields", "Please fill in all fields.")
            return
        if pw != cpw:
            messagebox.showerror("Password Mismatch", "Passwords do not match.")
            return
        if len(pw) < 6:
            messagebox.showwarning("Weak Password", "Password must be at least 6 characters.")
            return

        ok, msg = self.app.db.register(name, email, user, pw)
        if ok:
            messagebox.showinfo("Success! 🎉", msg + "\nPlease login.")
            self.app._show_login()
        else:
            messagebox.showerror("Registration Failed", msg)


# ============================================================
#   STUDENT DASHBOARD
# ============================================================
class StudentDashboard(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS["bg_dark"])
        self.app = app
        self.user = app.current_user
        self._build()

    def _build(self):
        self._build_sidebar()
        self._build_main()

    def _build_sidebar(self):
        sidebar = tk.Frame(self, bg=COLORS["bg_card"], width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # Header
        hdr = tk.Frame(sidebar, bg=COLORS["gradient2"], height=90)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        tk.Label(hdr, text="🎓", font=("Segoe UI",28),
                 bg=COLORS["gradient2"]).pack(pady=(14,0))
        tk.Label(hdr, text="EXS Portal",
                 font=("Segoe UI",11,"bold"),
                 bg=COLORS["gradient2"], fg=COLORS["text_primary"]).pack()

        # User info
        info = tk.Frame(sidebar, bg=COLORS["bg_card"])
        info.pack(fill="x", padx=12, pady=14)

        av = tk.Label(info, text=self.user["name"][0].upper(),
                      font=("Segoe UI",18,"bold"), width=3, height=1,
                      bg=COLORS["accent"], fg="white")
        av.pack(pady=(0,6))

        tk.Label(info, text=self.user["name"],
                 font=FONTS["body_b"], bg=COLORS["bg_card"],
                 fg=COLORS["text_primary"], wraplength=170).pack()
        tk.Label(info, text="Student",
                 font=FONTS["small"], bg=COLORS["bg_card"],
                 fg=COLORS["accent"]).pack()

        tk.Frame(sidebar, bg=COLORS["border"], height=1).pack(fill="x", padx=12, pady=8)

        # Nav items
        nav_items = [
            ("🏠  Dashboard",  self._show_home_tab),
            ("📝  Take Exam",   self._show_exam_tab),
            ("📊  My Results",  self._show_results_tab),
        ]
        self.nav_frames = {}
        for label, cmd in nav_items:
            btn = tk.Button(sidebar, text=label, font=FONTS["body"],
                            bg=COLORS["bg_card"], fg=COLORS["text_primary"],
                            activebackground=COLORS["hover"],
                            activeforeground=COLORS["accent"],
                            relief="flat", bd=0, cursor="hand2",
                            anchor="w", padx=18, pady=10, command=cmd)
            btn.pack(fill="x")
            btn.bind("<Enter>", lambda e,b=btn: b.config(bg=COLORS["hover"]))
            btn.bind("<Leave>", lambda e,b=btn: b.config(bg=COLORS["bg_card"]))

        # Logout at bottom
        tk.Frame(sidebar, bg=COLORS["bg_card"]).pack(expand=True)
        tk.Frame(sidebar, bg=COLORS["border"], height=1).pack(fill="x", padx=12)
        FancyButton(sidebar, "⏻  Logout", self._logout,
                    style="danger", font=FONTS["small"],
                    padx=0, pady=8).pack(fill="x", padx=12, pady=10)

    def _build_main(self):
        self.main = tk.Frame(self, bg=COLORS["bg_dark"])
        self.main.pack(side="right", fill="both", expand=True)
        self._show_home_tab()

    def _clear_main(self):
        for w in self.main.winfo_children():
            w.destroy()

    def _topbar(self, title, subtitle=""):
        bar = tk.Frame(self.main, bg=COLORS["bg_card"], height=64)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        inner = tk.Frame(bar, bg=COLORS["bg_card"])
        inner.place(relx=0, rely=0.5, anchor="w", x=24)
        tk.Label(inner, text=title, font=FONTS["heading"],
                 bg=COLORS["bg_card"], fg=COLORS["text_primary"]).pack(anchor="w")
        if subtitle:
            tk.Label(inner, text=subtitle, font=FONTS["small"],
                     bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(anchor="w")
        tk.Frame(self.main, bg=COLORS["border"], height=1).pack(fill="x")

    # ── Tabs ─────────────────────────────────────────────────
    def _show_home_tab(self):
        self._clear_main()
        self._topbar(f"Welcome, {self.user['name']} 👋",
                     f"Today is {datetime.now().strftime('%A, %d %B %Y')}")

        scroll = tk.Frame(self.main, bg=COLORS["bg_dark"])
        scroll.pack(fill="both", expand=True, padx=24, pady=20)

        # Stats row
        results = self.app.db.get_results(self.user["id"])
        total   = len(results)
        passed  = sum(1 for r in results if r["status"] == "PASS")
        avg     = round(sum(r["percentage"] for r in results) / total, 1) if total else 0

        stats = [
            ("📝", "Exams Taken",   str(total),          COLORS["accent"]),
            ("✅", "Exams Passed",  str(passed),          COLORS["accent2"]),
            ("❌", "Exams Failed",  str(total - passed),  COLORS["accent3"]),
            ("📈", "Average Score", f"{avg}%",            COLORS["warning"]),
        ]
        stat_row = tk.Frame(scroll, bg=COLORS["bg_dark"])
        stat_row.pack(fill="x", pady=(0,20))

        for icon, label, val, color in stats:
            card = rounded_frame(stat_row, bg=COLORS["bg_card"])
            card.pack(side="left", fill="x", expand=True, padx=(0,12))
            tk.Label(card, text=icon, font=("Segoe UI",24),
                     bg=COLORS["bg_card"]).pack(padx=16, pady=(12,4), anchor="w")
            tk.Label(card, text=val, font=("Segoe UI",28,"bold"),
                     bg=COLORS["bg_card"], fg=color).pack(padx=16, anchor="w")
            tk.Label(card, text=label, font=FONTS["small"],
                     bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(padx=16,pady=(2,12),anchor="w")

        # Subject cards
        tk.Label(scroll, text="Available Subjects",
                 font=FONTS["subhead"], bg=COLORS["bg_dark"],
                 fg=COLORS["text_primary"]).pack(anchor="w", pady=(0,10))

        subjects = self.app.db.get_subjects()
        subj_row = tk.Frame(scroll, bg=COLORS["bg_dark"])
        subj_row.pack(fill="x")

        icons_s = ["🐍","🔢","🌍","💻"]
        colors_s = [COLORS["accent"], COLORS["accent2"], COLORS["warning"], COLORS["purple"]]
        for i, subj in enumerate(subjects):
            card = rounded_frame(subj_row, bg=COLORS["bg_card"])
            card.pack(side="left", fill="x", expand=True, padx=(0,12))
            tk.Label(card, text=icons_s[i%4], font=("Segoe UI",28),
                     bg=COLORS["bg_card"]).pack(padx=16, pady=(14,4), anchor="w")
            tk.Label(card, text=subj["name"],
                     font=FONTS["body_b"], bg=COLORS["bg_card"],
                     fg=colors_s[i%4], wraplength=140).pack(padx=16, anchor="w")
            tk.Label(card, text=f"⏱ {subj['duration']} min  •  {subj['total_marks']} marks",
                     font=FONTS["small"], bg=COLORS["bg_card"],
                     fg=COLORS["text_muted"]).pack(padx=16, pady=(2,8), anchor="w")
            FancyButton(card, "Start Exam",
                        lambda s=subj: self.app._show_exam(dict(s)),
                        style="primary", font=FONTS["small"],
                        padx=10, pady=6).pack(padx=16, pady=(0,14), anchor="w")

    def _show_exam_tab(self):
        self._clear_main()
        self._topbar("📝 Select Exam Subject", "Choose a subject to begin your exam")

        body = tk.Frame(self.main, bg=COLORS["bg_dark"])
        body.pack(fill="both", expand=True, padx=40, pady=30)

        subjects = self.app.db.get_subjects()
        icons_s  = ["🐍","🔢","🌍","💻"]

        for i, subj in enumerate(subjects):
            card = rounded_frame(body, bg=COLORS["bg_card"])
            card.pack(fill="x", pady=8)

            inner = tk.Frame(card, bg=COLORS["bg_card"])
            inner.pack(fill="x", padx=20, pady=16)

            lft = tk.Frame(inner, bg=COLORS["bg_card"])
            lft.pack(side="left")
            tk.Label(lft, text=icons_s[i%4], font=("Segoe UI",30),
                     bg=COLORS["bg_card"]).pack(side="left", padx=(0,16))

            info = tk.Frame(lft, bg=COLORS["bg_card"])
            info.pack(side="left")
            tk.Label(info, text=subj["name"], font=FONTS["subhead"],
                     bg=COLORS["bg_card"], fg=COLORS["text_primary"]).pack(anchor="w")
            tk.Label(info, text=subj["description"], font=FONTS["small"],
                     bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(anchor="w")
            tk.Label(info, text=f"⏱ {subj['duration']} min   •   📋 {subj['total_marks']} marks",
                     font=FONTS["small"], bg=COLORS["bg_card"],
                     fg=COLORS["text_muted"]).pack(anchor="w", pady=(4,0))

            FancyButton(inner, "Start Exam ▶",
                        lambda s=subj: self.app._show_exam(dict(s)),
                        style="primary").pack(side="right")

    def _show_results_tab(self):
        self._clear_main()
        self._topbar("📊 My Results", "Your exam history and performance")
        ResultsPage(self.main, self.app, embedded=True).pack(fill="both", expand=True)

    def _logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.app.current_user = None
            self.app._show_login()


# ============================================================
#   EXAM PAGE
# ============================================================
class ExamPage(tk.Frame):
    def __init__(self, parent, app, subject):
        super().__init__(parent, bg=COLORS["bg_dark"])
        self.app = app
        self.subject = subject
        self.questions = app.db.get_questions(subject["id"])
        self.current_q = 0
        self.answers = {}
        self.selected_var = tk.StringVar()
        self.start_time = time.time()
        self.duration = subject["duration"] * 60  # seconds
        self.timer_running = True
        self._build()
        self._start_timer()

    def _build(self):
        # Top bar
        top = tk.Frame(self, bg=COLORS["bg_card"], height=64)
        top.pack(fill="x")
        top.pack_propagate(False)

        tk.Label(top, text=f"📝  {self.subject['name']}",
                 font=FONTS["heading"], bg=COLORS["bg_card"],
                 fg=COLORS["text_primary"]).place(relx=0.02, rely=0.5, anchor="w")

        timer_frame = tk.Frame(top, bg=COLORS["bg_input"],
                               highlightbackground=COLORS["accent3"],
                               highlightthickness=1)
        timer_frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(timer_frame, text="⏱ Time Left:",
                 font=FONTS["small"], bg=COLORS["bg_input"],
                 fg=COLORS["text_muted"]).pack(side="left", padx=(8,4), pady=6)
        self.timer_lbl = tk.Label(timer_frame, text="00:00",
                                   font=FONTS["timer"], bg=COLORS["bg_input"],
                                   fg=COLORS["accent3"])
        self.timer_lbl.pack(side="left", padx=(0,8))

        # Progress
        self.prog_lbl = tk.Label(top, text="", font=FONTS["small"],
                                  bg=COLORS["bg_card"], fg=COLORS["text_muted"])
        self.prog_lbl.place(relx=0.98, rely=0.5, anchor="e")

        tk.Frame(self, bg=COLORS["border"], height=1).pack(fill="x")

        # Body
        body = tk.Frame(self, bg=COLORS["bg_dark"])
        body.pack(fill="both", expand=True, padx=50, pady=30)

        # Question panel
        q_card = rounded_frame(body, bg=COLORS["bg_card"])
        q_card.pack(fill="x", pady=(0,16))

        self.q_num = tk.Label(q_card, text="", font=FONTS["small"],
                               bg=COLORS["bg_card"], fg=COLORS["accent"])
        self.q_num.pack(anchor="w", padx=20, pady=(16,4))

        self.q_text = tk.Label(q_card, text="", font=("Segoe UI",14),
                                bg=COLORS["bg_card"], fg=COLORS["text_primary"],
                                wraplength=800, justify="left")
        self.q_text.pack(anchor="w", padx=20, pady=(0,16))

        # Options
        self.opt_frame = tk.Frame(body, bg=COLORS["bg_dark"])
        self.opt_frame.pack(fill="x")

        self.opt_btns = []
        option_labels = ["A", "B", "C", "D"]
        for i in range(4):
            row = tk.Frame(self.opt_frame, bg=COLORS["bg_card"],
                           highlightbackground=COLORS["border"],
                           highlightthickness=1, cursor="hand2")
            row.pack(fill="x", pady=5)

            badge = tk.Label(row, text=option_labels[i],
                             font=FONTS["body_b"], width=3, height=1,
                             bg=COLORS["border"], fg=COLORS["text_muted"])
            badge.pack(side="left", padx=(12,0), pady=12)

            lbl = tk.Label(row, text="", font=FONTS["body"],
                           bg=COLORS["bg_card"], fg=COLORS["text_primary"],
                           wraplength=750, justify="left")
            lbl.pack(side="left", padx=12, pady=12, fill="x", expand=True)

            row.bind("<Button-1>", lambda e, v=option_labels[i]: self._select_option(v))
            lbl.bind("<Button-1>", lambda e, v=option_labels[i]: self._select_option(v))
            badge.bind("<Button-1>", lambda e, v=option_labels[i]: self._select_option(v))
            row.bind("<Enter>", lambda e, r=row: r.config(bg=COLORS["hover"]))
            row.bind("<Leave>", lambda e, r=row, b=badge: self._on_leave(r, b))

            self.opt_btns.append((row, badge, lbl))

        # Navigation
        nav = tk.Frame(body, bg=COLORS["bg_dark"])
        nav.pack(fill="x", pady=20)

        self.prev_btn = FancyButton(nav, "← Previous", self._prev_q,
                                    style="ghost")
        self.prev_btn.pack(side="left")

        # Question palette
        self.palette_frame = tk.Frame(nav, bg=COLORS["bg_dark"])
        self.palette_frame.pack(side="left", expand=True)

        self.next_btn = FancyButton(nav, "Next →", self._next_q, style="primary")
        self.next_btn.pack(side="right")

        self.submit_btn = FancyButton(nav, "Submit Exam ✓", self._submit,
                                       style="success")
        self.submit_btn.pack(side="right", padx=(0,8))

        self._load_question()

    def _load_question(self):
        if not self.questions:
            messagebox.showerror("No Questions", "No questions available for this subject.")
            self.app._show_dashboard()
            return

        q = self.questions[self.current_q]
        total = len(self.questions)

        self.q_num.config(text=f"Question {self.current_q + 1} of {total}")
        self.q_text.config(text=q["question_text"])
        self.prog_lbl.config(text=f"Answered: {len(self.answers)} / {total}")

        options = [q["option_a"], q["option_b"], q["option_c"], q["option_d"]]
        opt_keys = ["A","B","C","D"]

        saved = self.answers.get(self.current_q)

        for i, (row, badge, lbl) in enumerate(self.opt_btns):
            lbl.config(text=options[i])
            if saved == opt_keys[i]:
                row.config(bg=COLORS["gradient1"],
                            highlightbackground=COLORS["accent"])
                badge.config(bg=COLORS["accent"], fg="white")
            else:
                row.config(bg=COLORS["bg_card"],
                            highlightbackground=COLORS["border"])
                badge.config(bg=COLORS["border"], fg=COLORS["text_muted"])

        self.prev_btn.config(state="normal" if self.current_q > 0 else "disabled")

        # Update palette
        for w in self.palette_frame.winfo_children():
            w.destroy()
        for i in range(min(total, 10)):
            bg = COLORS["accent2"] if i in self.answers else COLORS["bg_input"]
            fg = "white" if i in self.answers else COLORS["text_muted"]
            brd = COLORS["accent"] if i == self.current_q else COLORS["border"]
            btn = tk.Button(self.palette_frame, text=str(i+1),
                            font=FONTS["small"], width=2, height=1,
                            bg=bg, fg=fg, relief="flat", bd=0,
                            highlightbackground=brd, highlightthickness=1,
                            cursor="hand2",
                            command=lambda n=i: self._goto(n))
            btn.pack(side="left", padx=2)

    def _on_leave(self, row, badge):
        q = self.questions[self.current_q]
        saved = self.answers.get(self.current_q)
        opt_keys = ["A","B","C","D"]
        idx = self.opt_btns.index(
            next(x for x in self.opt_btns if x[0] == row)
        )
        if saved == opt_keys[idx]:
            row.config(bg=COLORS["gradient1"])
        else:
            row.config(bg=COLORS["bg_card"])

    def _select_option(self, value):
        self.answers[self.current_q] = value
        self._load_question()

    def _next_q(self):
        if self.current_q < len(self.questions) - 1:
            self.current_q += 1
            self._load_question()

    def _prev_q(self):
        if self.current_q > 0:
            self.current_q -= 1
            self._load_question()

    def _goto(self, n):
        self.current_q = n
        self._load_question()

    def _start_timer(self):
        def tick():
            while self.timer_running:
                elapsed = int(time.time() - self.start_time)
                remaining = max(0, self.duration - elapsed)
                m, s = divmod(remaining, 60)
                try:
                    color = COLORS["accent3"] if remaining < 60 else (
                            COLORS["warning"] if remaining < 180 else COLORS["accent2"])
                    self.timer_lbl.config(text=f"{m:02d}:{s:02d}", fg=color)
                except:
                    break
                if remaining == 0:
                    try:
                        self.timer_lbl.config(text="00:00", fg=COLORS["accent3"])
                        self._submit(timeout=True)
                    except:
                        pass
                    break
                time.sleep(1)
        t = threading.Thread(target=tick, daemon=True)
        t.start()

    def _submit(self, timeout=False):
        self.timer_running = False
        total_q = len(self.questions)
        if not timeout:
            unanswered = total_q - len(self.answers)
            if unanswered > 0:
                if not messagebox.askyesno("Unanswered Questions",
                        f"You have {unanswered} unanswered question(s).\nSubmit anyway?"):
                    self.timer_running = True
                    threading.Thread(target=lambda: None, daemon=True).start()
                    self._start_timer()
                    return

        score = 0
        for i, q in enumerate(self.questions):
            if self.answers.get(i) == q["correct_option"]:
                score += q["marks"]

        time_taken = int(time.time() - self.start_time)
        percentage, grade, status = self.app.db.save_result(
            self.app.current_user["id"],
            self.subject["id"],
            score,
            total_q,
            time_taken
        )
        self._show_result_dialog(score, total_q, percentage, grade, status, time_taken)

    def _show_result_dialog(self, score, total, pct, grade, status, time_taken):
        dlg = tk.Toplevel(self)
        dlg.title("Exam Result")
        dlg.geometry("520x560")
        dlg.configure(bg=COLORS["bg_dark"])
        dlg.resizable(False, False)
        dlg.transient(self)
        dlg.grab_set()

        # Center dialog
        dlg.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - 520) // 2
        y = self.winfo_rooty() + (self.winfo_height() - 560) // 2
        dlg.geometry(f"+{x}+{y}")

        # Banner
        banner_color = COLORS["accent2"] if status == "PASS" else COLORS["accent3"]
        banner = tk.Frame(dlg, bg=banner_color, height=120)
        banner.pack(fill="x")
        emoji = "🎉" if status == "PASS" else "📚"
        tk.Label(banner, text=emoji, font=("Segoe UI",40),
                 bg=banner_color).pack(pady=(16,4))
        tk.Label(banner, text=status, font=("Segoe UI",20,"bold"),
                 bg=banner_color, fg="white").pack()

        body = tk.Frame(dlg, bg=COLORS["bg_dark"])
        body.pack(fill="both", expand=True, padx=30, pady=20)

        # Grade circle
        grade_lbl = tk.Label(body, text=grade, font=("Segoe UI",48,"bold"),
                              bg=COLORS["bg_dark"], fg=banner_color)
        grade_lbl.pack()
        tk.Label(body, text="Grade", font=FONTS["small"],
                 bg=COLORS["bg_dark"], fg=COLORS["text_muted"]).pack()

        # Stats
        stats_frame = tk.Frame(body, bg=COLORS["bg_card"],
                                highlightbackground=COLORS["border"],
                                highlightthickness=1)
        stats_frame.pack(fill="x", pady=16)

        data = [
            ("Score",      f"{score} / {total}"),
            ("Percentage", f"{pct}%"),
            ("Time Taken", f"{time_taken//60}m {time_taken%60}s"),
            ("Subject",    self.subject["name"]),
        ]
        for label, val in data:
            row = tk.Frame(stats_frame, bg=COLORS["bg_card"])
            row.pack(fill="x", padx=16, pady=5)
            tk.Label(row, text=label, font=FONTS["small"],
                     bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(side="left")
            tk.Label(row, text=val, font=FONTS["body_b"],
                     bg=COLORS["bg_card"], fg=COLORS["text_primary"]).pack(side="right")

        def go_dash():
            dlg.destroy()
            self.app._show_dashboard()

        FancyButton(body, "Back to Dashboard",
                    go_dash, style="primary",
                    padx=0, pady=10).pack(fill="x", pady=8)
        FancyButton(body, "View All Results",
                    lambda: (dlg.destroy(), self.app._show_results()),
                    style="ghost", pady=10).pack(fill="x")

        dlg.protocol("WM_DELETE_WINDOW", go_dash)


# ============================================================
#   RESULTS PAGE
# ============================================================
class ResultsPage(tk.Frame):
    def __init__(self, parent, app, embedded=False):
        super().__init__(parent, bg=COLORS["bg_dark"])
        self.app = app
        self.embedded = embedded
        self._build()

    def _build(self):
        if not self.embedded:
            # Top bar with back button
            bar = tk.Frame(self, bg=COLORS["bg_card"], height=64)
            bar.pack(fill="x")
            bar.pack_propagate(False)
            tk.Label(bar, text="📊 My Results",
                     font=FONTS["heading"], bg=COLORS["bg_card"],
                     fg=COLORS["text_primary"]).place(relx=0.02, rely=0.5, anchor="w")
            FancyButton(bar, "← Back",
                        self.app._show_dashboard,
                        style="ghost", pady=6).place(relx=0.98, rely=0.5, anchor="e", x=-12)
            tk.Frame(self, bg=COLORS["border"], height=1).pack(fill="x")

        body = tk.Frame(self, bg=COLORS["bg_dark"])
        body.pack(fill="both", expand=True, padx=24, pady=16)

        results = self.app.db.get_results(self.app.current_user["id"])

        if not results:
            tk.Label(body, text="📭", font=("Segoe UI",48),
                     bg=COLORS["bg_dark"]).pack(expand=True)
            tk.Label(body, text="No results yet.",
                     font=FONTS["subhead"], bg=COLORS["bg_dark"],
                     fg=COLORS["text_muted"]).pack()
            tk.Label(body, text="Take an exam to see your results here.",
                     font=FONTS["body"], bg=COLORS["bg_dark"],
                     fg=COLORS["text_muted"]).pack(pady=6)
            return

        # Table
        cols = ("Subject","Score","Percentage","Grade","Status","Time","Date")
        tree_frame = tk.Frame(body, bg=COLORS["bg_dark"])
        tree_frame.pack(fill="both", expand=True)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
                         background=COLORS["bg_card"],
                         foreground=COLORS["text_primary"],
                         fieldbackground=COLORS["bg_card"],
                         rowheight=36,
                         font=FONTS["body"])
        style.configure("Treeview.Heading",
                         background=COLORS["gradient2"],
                         foreground=COLORS["accent"],
                         font=FONTS["body_b"],
                         relief="flat")
        style.map("Treeview", background=[("selected", COLORS["gradient1"])])

        tree = ttk.Treeview(tree_frame, columns=cols, show="headings",
                             style="Treeview")
        sb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)

        col_widths = [180, 80, 100, 70, 80, 90, 160]
        for col, width in zip(cols, col_widths):
            tree.heading(col, text=col)
            tree.column(col, width=width, anchor="center")

        for r in results:
            mins, secs = divmod(r["time_taken"], 60)
            tree.insert("", "end", values=(
                r["subject_name"],
                f"{r['score']} / {r['total_marks']}",
                f"{r['percentage']}%",
                r["grade"],
                r["status"],
                f"{mins}m {secs}s",
                r["attempt_date"][:16]
            ), tags=(r["status"],))

        tree.tag_configure("PASS", foreground=COLORS["accent2"])
        tree.tag_configure("FAIL", foreground=COLORS["accent3"])

        tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")


# ============================================================
#   ADMIN DASHBOARD
# ============================================================
class AdminDashboard(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS["bg_dark"])
        self.app = app
        self._build()

    def _build(self):
        # Sidebar
        sidebar = tk.Frame(self, bg=COLORS["bg_card"], width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        hdr = tk.Frame(sidebar, bg=COLORS["gradient2"], height=90)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="⚙️", font=("Segoe UI",26),
                 bg=COLORS["gradient2"]).pack(pady=(14,0))
        tk.Label(hdr, text="Admin Panel", font=("Segoe UI",11,"bold"),
                 bg=COLORS["gradient2"], fg=COLORS["text_primary"]).pack()

        info = tk.Frame(sidebar, bg=COLORS["bg_card"])
        info.pack(fill="x", padx=12, pady=14)
        tk.Label(info, text="A", font=("Segoe UI",18,"bold"),
                 width=3, height=1, bg=COLORS["warning"], fg="white").pack(pady=(0,6))
        tk.Label(info, text="Administrator", font=FONTS["body_b"],
                 bg=COLORS["bg_card"], fg=COLORS["text_primary"]).pack()
        tk.Label(info, text="Admin", font=FONTS["small"],
                 bg=COLORS["bg_card"], fg=COLORS["warning"]).pack()

        tk.Frame(sidebar, bg=COLORS["border"], height=1).pack(fill="x", padx=12, pady=8)

        nav_items = [
            ("📊  Overview",    self._show_overview),
            ("👥  Students",    self._show_students),
            ("📋  All Results", self._show_all_results),
        ]
        for label, cmd in nav_items:
            btn = tk.Button(sidebar, text=label, font=FONTS["body"],
                            bg=COLORS["bg_card"], fg=COLORS["text_primary"],
                            activebackground=COLORS["hover"],
                            activeforeground=COLORS["accent"],
                            relief="flat", bd=0, cursor="hand2",
                            anchor="w", padx=18, pady=10, command=cmd)
            btn.pack(fill="x")
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=COLORS["hover"]))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=COLORS["bg_card"]))

        tk.Frame(sidebar, bg=COLORS["bg_card"]).pack(expand=True)
        tk.Frame(sidebar, bg=COLORS["border"], height=1).pack(fill="x", padx=12)
        FancyButton(sidebar, "⏻  Logout", self._logout,
                    style="danger", font=FONTS["small"],
                    padx=0, pady=8).pack(fill="x", padx=12, pady=10)

        # Main
        self.main = tk.Frame(self, bg=COLORS["bg_dark"])
        self.main.pack(side="right", fill="both", expand=True)
        self._show_overview()

    def _clear_main(self):
        for w in self.main.winfo_children():
            w.destroy()

    def _topbar(self, title, subtitle=""):
        bar = tk.Frame(self.main, bg=COLORS["bg_card"], height=64)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        inner = tk.Frame(bar, bg=COLORS["bg_card"])
        inner.place(relx=0, rely=0.5, anchor="w", x=24)
        tk.Label(inner, text=title, font=FONTS["heading"],
                 bg=COLORS["bg_card"], fg=COLORS["text_primary"]).pack(anchor="w")
        if subtitle:
            tk.Label(inner, text=subtitle, font=FONTS["small"],
                     bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(anchor="w")
        tk.Frame(self.main, bg=COLORS["border"], height=1).pack(fill="x")

    def _show_overview(self):
        self._clear_main()
        self._topbar("📊 System Overview",
                     f"As of {datetime.now().strftime('%A, %d %B %Y')}")

        body = tk.Frame(self.main, bg=COLORS["bg_dark"])
        body.pack(fill="both", expand=True, padx=24, pady=20)

        students = self.app.db.get_all_students()
        results  = self.app.db.get_all_results()
        passed   = sum(1 for r in results if r["status"] == "PASS")

        stats = [
            ("👥", "Total Students", str(len(students)),         COLORS["accent"]),
            ("📝", "Total Exams",    str(len(results)),           COLORS["purple"]),
            ("✅", "Passed",         str(passed),                  COLORS["accent2"]),
            ("❌", "Failed",         str(len(results) - passed),   COLORS["accent3"]),
        ]
        row = tk.Frame(body, bg=COLORS["bg_dark"])
        row.pack(fill="x", pady=(0,24))
        for icon, label, val, color in stats:
            card = rounded_frame(row, bg=COLORS["bg_card"])
            card.pack(side="left", fill="x", expand=True, padx=(0,12))
            tk.Label(card, text=icon, font=("Segoe UI",26),
                     bg=COLORS["bg_card"]).pack(padx=16, pady=(14,4), anchor="w")
            tk.Label(card, text=val, font=("Segoe UI",30,"bold"),
                     bg=COLORS["bg_card"], fg=color).pack(padx=16, anchor="w")
            tk.Label(card, text=label, font=FONTS["small"],
                     bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(padx=16,pady=(2,14),anchor="w")

        # Recent results
        tk.Label(body, text="Recent Exam Results",
                 font=FONTS["subhead"], bg=COLORS["bg_dark"],
                 fg=COLORS["text_primary"]).pack(anchor="w", pady=(0,10))

        cols = ("Student","Subject","Score","Grade","Status","Date")
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
                         background=COLORS["bg_card"],
                         foreground=COLORS["text_primary"],
                         fieldbackground=COLORS["bg_card"],
                         rowheight=34, font=FONTS["body"])
        style.configure("Treeview.Heading",
                         background=COLORS["gradient2"],
                         foreground=COLORS["accent"],
                         font=FONTS["body_b"], relief="flat")
        style.map("Treeview", background=[("selected", COLORS["gradient1"])])

        tree = ttk.Treeview(body, columns=cols, show="headings",
                             style="Treeview", height=8)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=140, anchor="center")

        for r in results[:20]:
            tree.insert("", "end", values=(
                r["student_name"], r["subject_name"],
                f"{r['score']}/{r['total_marks']}",
                r["grade"], r["status"],
                r["attempt_date"][:16]
            ), tags=(r["status"],))

        tree.tag_configure("PASS", foreground=COLORS["accent2"])
        tree.tag_configure("FAIL", foreground=COLORS["accent3"])
        tree.pack(fill="x")

    def _show_students(self):
        self._clear_main()
        self._topbar("👥 Registered Students")
        body = tk.Frame(self.main, bg=COLORS["bg_dark"])
        body.pack(fill="both", expand=True, padx=24, pady=20)

        students = self.app.db.get_all_students()
        cols = ("ID","Name","Email","Username","Joined")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
                         background=COLORS["bg_card"],
                         foreground=COLORS["text_primary"],
                         fieldbackground=COLORS["bg_card"],
                         rowheight=36, font=FONTS["body"])
        style.configure("Treeview.Heading",
                         background=COLORS["gradient2"],
                         foreground=COLORS["accent"],
                         font=FONTS["body_b"], relief="flat")
        style.map("Treeview", background=[("selected", COLORS["gradient1"])])

        tree = ttk.Treeview(body, columns=cols, show="headings",
                             style="Treeview")
        sb = ttk.Scrollbar(body, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)

        widths = [50, 180, 220, 140, 160]
        for col, w in zip(cols, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="center")

        for s in students:
            tree.insert("", "end", values=(
                s["id"], s["name"], s["email"],
                s["username"], s["created_at"][:16]
            ))

        tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    def _show_all_results(self):
        self._clear_main()
        self._topbar("📋 All Exam Results")
        body = tk.Frame(self.main, bg=COLORS["bg_dark"])
        body.pack(fill="both", expand=True, padx=24, pady=20)

        results = self.app.db.get_all_results()
        cols = ("Student","Subject","Score","Percentage","Grade","Status","Date")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
                         background=COLORS["bg_card"],
                         foreground=COLORS["text_primary"],
                         fieldbackground=COLORS["bg_card"],
                         rowheight=36, font=FONTS["body"])
        style.configure("Treeview.Heading",
                         background=COLORS["gradient2"],
                         foreground=COLORS["accent"],
                         font=FONTS["body_b"], relief="flat")
        style.map("Treeview", background=[("selected", COLORS["gradient1"])])

        tree = ttk.Treeview(body, columns=cols, show="headings", style="Treeview")
        sb = ttk.Scrollbar(body, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)

        widths = [160, 160, 80, 100, 70, 80, 150]
        for col, w in zip(cols, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="center")

        for r in results:
            tree.insert("", "end", values=(
                r["student_name"], r["subject_name"],
                f"{r['score']}/{r['total_marks']}",
                f"{r['percentage']}%",
                r["grade"], r["status"],
                r["attempt_date"][:16]
            ), tags=(r["status"],))

        tree.tag_configure("PASS", foreground=COLORS["accent2"])
        tree.tag_configure("FAIL", foreground=COLORS["accent3"])
        tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    def _logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.app.current_user = None
            self.app._show_login()


# ============================================================
#   ENTRY POINT
# ============================================================
if __name__ == "__main__":
    app = OnlineExamApp()
    app.mainloop()