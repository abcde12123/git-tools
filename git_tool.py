import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import os
import threading
import shutil
import time

# 隐藏 CMD 窗口
CREATE_NO_WINDOW = 0x08000000
CONFIG_FILE = os.path.join(os.getenv('APPDATA'), "git_tool_path_config.txt")

def _hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def _rgb_to_hex(rgb):
    return "#{:02X}{:02X}{:02X}".format(*rgb)

def _blend(a, b, t):
    ar, ag, ab = _hex_to_rgb(a)
    br, bg, bb = _hex_to_rgb(b)
    r = int(ar + (br - ar) * t)
    g = int(ag + (bg - ag) * t)
    b2 = int(ab + (bb - ab) * t)
    return _rgb_to_hex((r, g, b2))

class RoundedButton(tk.Canvas):
    def __init__(self, master, text, command=None, width=200, height=40, radius=14, bg="#2C3E50", fg="#FFFFFF", hover_bg=None, active_bg=None, border="#DDE7E7", hover_border=None, active_border=None, canvas_bg=None, font=("微软雅黑", 10, "bold")):
        super().__init__(master, width=width, height=height, highlightthickness=0, bd=0, bg=canvas_bg if canvas_bg is not None else master.cget("bg"))
        self._text = text
        self._command = command
        self._width = width
        self._height = height
        self._radius = radius
        self._bg = bg
        self._fg = fg
        self._hover_bg = hover_bg if hover_bg is not None else _blend(bg, "#FFFFFF", 0.08)
        self._active_bg = active_bg if active_bg is not None else _blend(bg, "#000000", 0.08)
        self._border = border
        self._hover_border = hover_border if hover_border is not None else _blend(border, "#FFFFFF", 0.35)
        self._active_border = active_border if active_border is not None else _blend(self._hover_border, "#000000", 0.18)
        self._font = font
        self._enabled = True
        self._pressed = False
        self._hovering = False
        self._shape_ids = []
        self._text_id = None

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_down)
        self.bind("<ButtonRelease-1>", self._on_up)
        self.configure(cursor="hand2")
        self._draw(self._bg, self._fg, self._border, shadow_level=0)

    def set_enabled(self, enabled):
        self._enabled = bool(enabled)
        if self._enabled:
            self.configure(cursor="hand2")
            self._draw(self._bg, self._fg, self._border, shadow_level=0)
        else:
            self.configure(cursor="")
            disabled_bg = _blend(self._bg, self.cget("bg"), 0.55)
            disabled_fg = _blend(self._fg, self.cget("bg"), 0.55)
            self._draw(disabled_bg, disabled_fg, _blend(self._border, self.cget("bg"), 0.55), shadow_level=0)

    def _rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [
            x1 + r, y1,
            x2 - r, y1,
            x2, y1,
            x2, y1 + r,
            x2, y2 - r,
            x2, y2,
            x2 - r, y2,
            x1 + r, y2,
            x1, y2,
            x1, y2 - r,
            x1, y1 + r,
            x1, y1,
        ]
        return self.create_polygon(points, smooth=True, splinesteps=36, **kwargs)

    def _draw(self, fill, text_color, border_color, shadow_level):
        for _id in self._shape_ids:
            try:
                self.delete(_id)
            except Exception:
                pass
        self._shape_ids.clear()
        if self._text_id is not None:
            try:
                self.delete(self._text_id)
            except Exception:
                pass
            self._text_id = None

        bg = self.cget("bg")
        shadow_far = _blend("#000000", bg, 0.90)
        shadow_near = _blend("#000000", bg, 0.84)

        if shadow_level == 0:
            s1, s2 = (4, 5), (3, 4)
        elif shadow_level == 1:
            s1, s2 = (3, 4), (2, 3)
        else:
            s1, s2 = (2, 3), (1, 2)

        w = self._width
        h = self._height
        r = self._radius
        self._shape_ids.append(self._rounded_rect(s1[0], s1[1], w - 1, h - 1, r, fill=shadow_far, outline=""))
        self._shape_ids.append(self._rounded_rect(s2[0], s2[1], w - 2, h - 2, r, fill=shadow_near, outline=""))

        base_x1, base_y1, base_x2, base_y2 = 1, 1, w - 6, h - 6
        if base_x2 <= base_x1 + 10 or base_y2 <= base_y1 + 10:
            base_x2, base_y2 = w - 2, h - 2
        self._shape_ids.append(self._rounded_rect(base_x1, base_y1, base_x2, base_y2, r, fill=fill, outline=border_color, width=1))

        highlight = _blend(fill, "#FFFFFF", 0.10)
        mid = fill
        self._shape_ids.append(self._rounded_rect(base_x1 + 2, base_y1 + 2, base_x2 - 2, base_y2 - 2, max(8, r - 2), fill=highlight, outline=""))
        self._shape_ids.append(self._rounded_rect(base_x1 + 3, base_y1 + 3, base_x2 - 3, base_y2 - 3, max(7, r - 3), fill=mid, outline=""))

        self._text_id = self.create_text(w / 2, h / 2 - 1, text=self._text, fill=text_color, font=self._font)

    def _on_enter(self, _):
        if not self._enabled or self._pressed:
            return
        self._hovering = True
        self._draw(self._hover_bg, self._fg, self._hover_border, shadow_level=1)

    def _on_leave(self, _):
        if not self._enabled:
            return
        self._pressed = False
        self._hovering = False
        self._draw(self._bg, self._fg, self._border, shadow_level=0)

    def _on_down(self, _):
        if not self._enabled:
            return
        self._pressed = True
        self._draw(self._active_bg, self._fg, self._active_border, shadow_level=2)

    def _on_up(self, event):
        if not self._enabled:
            return
        was_pressed = self._pressed
        self._pressed = False
        inside = 0 <= event.x <= self._width and 0 <= event.y <= self._height
        if inside and self._hovering:
            self._draw(self._hover_bg, self._fg, self._hover_border, shadow_level=1)
        else:
            self._draw(self._bg, self._fg, self._border, shadow_level=0)
        if was_pressed and inside and callable(self._command):
            self._command()

class GitTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Git 自动化工具 v2.6 ")
        self.root.geometry("680x750")
        self.colors = {
            "primary": "#2C3E50",
            "secondary": "#A8E6CF",
            "accent": "#FDFFAB",
            "background": "#F4F9F9",
            "cancel": "#FF6B6B",
            "card": "#FFFFFF",
            "border": "#DDE7E7",
        }
        self.root.configure(bg=self.colors["background"])
        
        # 设置全局样式
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TButton', font=('微软雅黑', 10), padding=6, background=self.colors["secondary"], foreground=self.colors["primary"])
        self.style.map('TButton', background=[('active', self.colors["accent"])], foreground=[('active', self.colors["primary"])])
        self.style.configure('TLabel', background=self.colors["background"], foreground=self.colors["primary"], font=('微软雅黑', 10))
        self.style.configure('Header.TLabel', font=('微软雅黑', 12, 'bold'), foreground=self.colors["primary"], background=self.colors["card"])
        self.style.configure('Summer.Horizontal.TProgressbar', troughcolor=self.colors["background"], background=self.colors["secondary"], bordercolor=self.colors["background"], lightcolor=self.colors["secondary"], darkcolor=self.colors["secondary"])

        # 布局核心：响应式居中
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=4)
        self.root.grid_columnconfigure(2, weight=1)

        self.log_lines = []
        self.log_window = None
        self.log_text = None
        self.cancel_requested = False
        self.current_process = None

        self.setup_ui()
        self.load_last_path()

    def create_front_button(self, parent, text, kind, command, width=520, height=44):
        if kind == "mint":
            bg = self.colors["secondary"]
            fg = self.colors["primary"]
            hover = _blend(bg, self.colors["accent"], 0.35)
            active = _blend(bg, "#000000", 0.08)
            hover_border = self.colors["accent"]
        elif kind == "dark":
            bg = self.colors["primary"]
            fg = self.colors["background"]
            hover = _blend(bg, "#FFFFFF", 0.10)
            active = _blend(bg, "#000000", 0.10)
            hover_border = self.colors["secondary"]
        elif kind == "accent":
            bg = self.colors["accent"]
            fg = self.colors["primary"]
            hover = _blend(bg, self.colors["secondary"], 0.55)
            active = _blend(bg, "#000000", 0.08)
            hover_border = self.colors["secondary"]
        elif kind == "danger":
            bg = self.colors["cancel"]
            fg = self.colors["card"]
            hover = _blend(bg, "#FFFFFF", 0.10)
            active = _blend(bg, "#000000", 0.10)
            hover_border = self.colors["accent"]
        else:
            bg = self.colors["secondary"]
            fg = self.colors["primary"]
            hover = _blend(bg, self.colors["accent"], 0.35)
            active = _blend(bg, "#000000", 0.08)
            hover_border = self.colors["accent"]

        active_border = _blend(hover_border, self.colors["primary"], 0.25)

        return RoundedButton(
            parent,
            text=text,
            command=command,
            width=width,
            height=height,
            radius=14,
            bg=bg,
            fg=fg,
            hover_bg=hover,
            active_bg=active,
            border=self.colors["border"],
            hover_border=hover_border,
            active_border=active_border,
            canvas_bg=parent.cget("bg"),
            font=("微软雅黑", 10, "bold"),
        )

    def setup_ui(self):
        # --- 顶部：项目路径选择 ---
        frame_path = tk.Frame(self.root, bg=self.colors["background"])
        frame_path.grid(row=0, column=0, columnspan=3, pady=(20, 10), padx=20, sticky="ew")
        frame_path.grid_columnconfigure(1, weight=1)

        ttk.Label(frame_path, text="📁 项目路径:").grid(row=0, column=0, sticky="e", padx=5)
        self.entry_path = ttk.Entry(frame_path, font=('微软雅黑', 10))
        self.entry_path.grid(row=0, column=1, sticky="ew", padx=5)
        self.btn_browse = self.create_front_button(frame_path, "浏览", "dark", self.select_path, width=92, height=34)
        self.btn_browse.grid(row=0, column=2, sticky="w")

        ttk.Separator(self.root, orient='horizontal').grid(row=1, column=0, columnspan=3, sticky="ew", padx=20, pady=5)

        # --- 主操作区 ---
        frame_ops = tk.Frame(self.root, bg=self.colors["card"], highlightbackground=self.colors["border"], highlightthickness=1, bd=0)
        frame_ops.grid(row=2, column=1, pady=10, sticky="nsew")
        frame_ops.grid_columnconfigure(0, weight=1)

        ttk.Label(frame_ops, text="📌 日常工作流", style='Header.TLabel', background=self.colors["card"]).grid(row=0, column=0, pady=(15, 10))

        self.btn_pull = self.create_front_button(frame_ops, "⬇️ 1. 从远程更新 (Git Pull)", "mint", lambda: self.run_thread(self.git_pull), width=540, height=46)
        self.btn_pull.grid(row=1, column=0, pady=6)

        self.btn_add = self.create_front_button(frame_ops, "➕ 2. 暂存所有更改 (Git Add)", "dark", lambda: self.run_thread(self.git_add), width=540, height=46)
        self.btn_add.grid(row=2, column=0, pady=6)

        f_commit = tk.Frame(frame_ops, bg=self.colors["card"])
        f_commit.grid(row=3, column=0, pady=6)
        ttk.Label(f_commit, text="📝 描述:", background=self.colors["card"]).pack(side="left")
        self.entry_msg = ttk.Entry(f_commit, width=28, font=('微软雅黑', 10))
        self.entry_msg.pack(side="left", padx=5)
        self.btn_commit = self.create_front_button(f_commit, "提交", "accent", lambda: self.run_thread(self.git_commit), width=88, height=34)
        self.btn_commit.pack(side="left")

        self.btn_push = self.create_front_button(frame_ops, "⬆️ 3. 推送至云端 (Git Push)", "mint", lambda: self.run_thread(self.git_push), width=540, height=46)
        self.btn_push.grid(row=4, column=0, pady=(10, 15))

        # --- 高级管理区 ---
        frame_adv = tk.Frame(self.root, bg=self.colors["card"], highlightbackground=self.colors["border"], highlightthickness=1, bd=0)
        frame_adv.grid(row=3, column=1, pady=10, sticky="nsew")
        frame_adv.grid_columnconfigure(0, weight=1)
        frame_adv.grid_columnconfigure(1, weight=1)

        ttk.Label(frame_adv, text="⚙️ 仓库配置与修复", style='Header.TLabel', background=self.colors["card"]).grid(row=0, column=0, columnspan=2, pady=(15, 10))

        self.btn_init = self.create_front_button(frame_adv, "🆕 初始化新仓库", "mint", self.open_init_window, width=220, height=40)
        self.btn_init.grid(row=1, column=0, padx=10, pady=(5, 15), sticky="e")

        self.btn_force = self.create_front_button(frame_adv, "🔧 强制联通云端", "danger", lambda: self.run_thread(self.git_pull_force), width=220, height=40)
        self.btn_force.grid(row=1, column=1, padx=10, pady=(5, 15), sticky="w")

        # --- 状态与进度条 ---
        frame_status = tk.Frame(self.root, bg=self.colors["background"])
        frame_status.grid(row=5, column=0, columnspan=3, pady=(10, 0), sticky="ew")
        frame_status.grid_columnconfigure(0, weight=1)

        self.status_var = tk.StringVar(value="状态: 准备就绪")
        self.status_label = tk.Label(frame_status, textvariable=self.status_var, fg=self.colors["primary"], bg=self.colors["background"], font=("微软雅黑", 9, "bold"))
        self.status_label.grid(row=0, column=0, pady=(0, 5))

        self.progress = ttk.Progressbar(frame_status, orient="horizontal", mode="indeterminate", style="Summer.Horizontal.TProgressbar")
        # 修复进度条初始显示问题：默认隐藏
        self.progress.grid_remove()

        frame_status_btns = tk.Frame(frame_status, bg=self.colors["background"])
        frame_status_btns.grid(row=2, column=0, pady=(6, 0))

        self.btn_view_log = self.create_front_button(frame_status_btns, "查看日志", "dark", self.open_log_window, width=110, height=36)
        self.btn_view_log.pack(side="left", padx=(0, 10))

        self.btn_cancel = self.create_front_button(frame_status_btns, "打断", "danger", self.interrupt_current, width=90, height=36)
        self.btn_cancel.pack(side="left")

        # --- 网络设置区 ---
        frame_net = tk.Frame(self.root, bg=self.colors["card"], highlightbackground=self.colors["border"], highlightthickness=1, bd=0)
        frame_net.grid(row=4, column=1, pady=10, sticky="nsew")
        frame_net.grid_columnconfigure(0, weight=1)

        ttk.Label(frame_net, text="🌐 网络", style='Header.TLabel', background=self.colors["card"]).grid(row=0, column=0, columnspan=3, pady=(12, 10))

        frame_net_row = tk.Frame(frame_net, bg=self.colors["card"])
        frame_net_row.grid(row=1, column=0, columnspan=3, pady=(0, 12))

        ttk.Label(frame_net_row, text="代理端口:", background=self.colors["card"]).pack(side="left", padx=(0, 6))
        self.entry_proxy_port = ttk.Entry(frame_net_row, font=('微软雅黑', 10), width=12)
        self.entry_proxy_port.pack(side="left", padx=(0, 10))
        self.btn_set_proxy = self.create_front_button(frame_net_row, "启用代理", "mint", lambda: self.run_thread_no_path(self.git_set_proxy), width=110, height=34)
        self.btn_set_proxy.pack(side="left", padx=(0, 10))

        self.btn_unset_proxy = self.create_front_button(frame_net_row, "取消代理", "dark", lambda: self.run_thread_no_path(self.git_unset_proxy), width=110, height=34)
        self.btn_unset_proxy.pack(side="left")

    # --- 线程与 UI 状态管理 ---
    def set_buttons_state(self, state):
        enabled = bool(state)
        self.btn_pull.set_enabled(enabled)
        self.btn_add.set_enabled(enabled)
        self.btn_commit.set_enabled(enabled)
        self.btn_push.set_enabled(enabled)
        self.btn_init.set_enabled(enabled)
        self.btn_force.set_enabled(enabled)
        self.btn_set_proxy.set_enabled(enabled)
        self.btn_unset_proxy.set_enabled(enabled)
        self.btn_browse.set_enabled(enabled)
        self.btn_view_log.set_enabled(True)
        self.btn_cancel.set_enabled(True)

    def run_thread(self, func):
        if not self.get_path():
            messagebox.showwarning("提示", "请先选择有效的项目路径！")
            return
        self.cancel_requested = False
        self.set_buttons_state(False)
        # 显示进度条并开始滚动
        self.progress.grid(row=1, column=0, sticky="ew", padx=40)
        self.progress.start(15)
        self.update_status("正在执行中，请稍候...", "#007bff")
        
        def thread_target():
            try:
                # 设置网络环境，防止大文件中断
                os.environ['GIT_HTTP_LOW_SPEED_LIMIT'] = '1000'
                os.environ['GIT_HTTP_LOW_SPEED_TIME'] = '60'
                func()
            except Exception as e:
                self.root.after(0, self.update_status, f"系统错误: {str(e)}", "red")
            finally:
                self.root.after(0, self.progress.stop)
                # 隐藏进度条
                self.root.after(0, self.progress.grid_remove)
                self.root.after(0, self.set_buttons_state, True)
                self.current_process = None

        threading.Thread(target=thread_target, daemon=True).start()

    def run_thread_no_path(self, func):
        self.cancel_requested = False
        self.set_buttons_state(False)
        self.progress.grid(row=1, column=0, sticky="ew", padx=40)
        self.progress.start(15)
        self.update_status("正在执行中，请稍候...", "#007bff")

        def thread_target():
            try:
                os.environ['GIT_HTTP_LOW_SPEED_LIMIT'] = '1000'
                os.environ['GIT_HTTP_LOW_SPEED_TIME'] = '60'
                func()
            except Exception as e:
                self.root.after(0, self.update_status, f"系统错误: {str(e)}", "red")
            finally:
                self.root.after(0, self.progress.stop)
                self.root.after(0, self.progress.grid_remove)
                self.root.after(0, self.set_buttons_state, True)
                self.current_process = None

        threading.Thread(target=thread_target, daemon=True).start()

    def update_status(self, msg, color="#28a745"):
        self.status_var.set(f"状态: {msg}")
        self.status_label.config(fg=color)

    def log(self, msg):
        self.root.after(0, self._append_log, msg)

    def _append_log(self, msg):
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {msg}"
        self.log_lines.append(line)
        if len(self.log_lines) > 2000:
            self.log_lines = self.log_lines[-2000:]

        if self.log_text is not None:
            try:
                self.log_text.config(state=tk.NORMAL)
                self.log_text.insert(tk.END, line + "\n")
                self.log_text.see(tk.END)
                self.log_text.config(state=tk.DISABLED)
            except Exception:
                pass

    def open_log_window(self):
        if self.log_window is not None:
            try:
                if self.log_window.winfo_exists():
                    self.log_window.lift()
                    self.log_window.focus_force()
                    return
            except Exception:
                pass

        win = tk.Toplevel(self.root)
        win.title("运行日志")
        win.geometry("760x420")
        win.configure(bg=self.colors["background"])

        container = tk.Frame(win, bg=self.colors["card"], highlightbackground=self.colors["border"], highlightthickness=1, bd=0)
        container.pack(fill="both", expand=True, padx=12, pady=12)

        sb = ttk.Scrollbar(container, orient="vertical")
        sb.pack(side="right", fill="y")
        txt = tk.Text(container, yscrollcommand=sb.set, wrap="word", font=("微软雅黑", 9), bg=self.colors["card"], fg=self.colors["primary"], relief="flat", insertbackground=self.colors["primary"], selectbackground=self.colors["secondary"], selectforeground=self.colors["primary"])
        txt.pack(side="left", fill="both", expand=True)
        sb.config(command=txt.yview)

        content = "\n".join(self.log_lines) + ("\n" if self.log_lines else "")
        txt.insert("1.0", content)
        txt.config(state=tk.DISABLED)

        def on_close():
            self.log_text = None
            self.log_window = None
            win.destroy()

        win.protocol("WM_DELETE_WINDOW", on_close)
        self.log_window = win
        self.log_text = txt

    def interrupt_current(self):
        p = self.current_process
        if p is None:
            self.root.after(0, self.update_status, "⚠️ 当前没有可打断的任务", "#ffc107")
            return
        self.cancel_requested = True
        self.log("已请求打断当前操作")
        self.root.after(0, self.update_status, "⚠️ 已请求打断", "#ffc107")
        try:
            p.terminate()
            try:
                p.wait(timeout=2)
            except Exception:
                p.kill()
        except Exception:
            pass

    # --- 带有重试机制的网络操作封装 ---
    def run_git_with_retry(self, cmd_list, max_retries=3, timeout_sec=50):
        """执行涉及网络的Git命令，如果失败自动重试"""
        last_err = ""
        for attempt in range(1, max_retries + 1):
            if self.cancel_requested:
                last_err = "已打断操作"
                self.log(last_err)
                return False, last_err
            self.root.after(0, self.update_status, f"正在连接服务器... (尝试 {attempt}/{max_retries})", "#007bff")
            self.log(f"执行命令: {' '.join(cmd_list)} (尝试 {attempt}/{max_retries})")
            env = os.environ.copy()
            env["GIT_TERMINAL_PROMPT"] = "0"
            env["GCM_INTERACTIVE"] = "never"
            try:
                p = subprocess.Popen(
                    cmd_list,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    creationflags=CREATE_NO_WINDOW,
                    env=env,
                )
                self.current_process = p
                stdout, stderr = p.communicate(timeout=timeout_sec)
                self.current_process = None
                if p.returncode == 0:
                    if stdout and stdout.strip():
                        self.log(f"执行成功，输出: {stdout.strip()}")
                    return True, stdout
                last_err = (stderr or stdout or "").strip()
                if last_err:
                    self.log(f"执行失败，返回码 {p.returncode}，信息: {last_err}")
            except subprocess.TimeoutExpired:
                try:
                    if self.current_process is not None:
                        self.current_process.terminate()
                        try:
                            self.current_process.wait(timeout=2)
                        except Exception:
                            self.current_process.kill()
                except Exception:
                    pass
                self.current_process = None
                last_err = f"命令执行超时（超过 {timeout_sec} 秒），可能是代理端口不可用或网络被阻塞。"
                self.log(last_err)
            time.sleep(2) # 失败后稍微等2秒再试
        return False, last_err

    # --- 功能函数 ---
    def git_pull(self):
        success, err = self.run_git_with_retry(["git", "pull", "origin", "main"])
        if success: 
            self.root.after(0, self.update_status, "✅ 同步成功")
        else: 
            self.root.after(0, self.update_status, "❌ 同步失败 (网络超时)", "red")
            self.root.after(0, messagebox.showerror, "错误", f"多次尝试后依然失败，请检查网络或加速器。\n\n详细信息:\n{err}")

    def git_add(self):
        res = subprocess.run(["git", "add", "."], capture_output=True, text=True, creationflags=CREATE_NO_WINDOW)
        if res.returncode == 0:
            self.root.after(0, self.update_status, "✅ 已全部添加到暂存区")
        else:
            self.root.after(0, self.update_status, "❌ 暂存失败", "red")

    def git_commit(self):
        msg = self.entry_msg.get().strip()
        if not msg: 
            self.root.after(0, self.update_status, "⚠️ 描述不能为空", "#ffc107")
            return
        
        res = subprocess.run(["git", "commit", "-m", msg], capture_output=True, text=True, creationflags=CREATE_NO_WINDOW)
        if res.returncode == 0:
            self.root.after(0, self.update_status, "✅ 本地提交完成")
            self.root.after(0, lambda: self.entry_msg.delete(0, tk.END))
        else: 
            self.root.after(0, self.update_status, "⚠️ 没有需要提交的更改", "#ffc107")

    def git_push(self):
        # 使用重试机制解决网络波动问题
        success, err = self.run_git_with_retry(["git", "push", "origin", "main"])
        if success: 
            self.root.after(0, self.update_status, "✅ 推送成功！")
            self.root.after(0, messagebox.showinfo, "成功", "代码已成功同步至云端。")
        else: 
            self.root.after(0, self.update_status, "❌ 推送失败", "red")
            self.root.after(0, messagebox.showerror, "错误", f"多次推送失败，请检查网络环境。\n\n详细信息:\n{err}")

    def git_pull_force(self):
        success, err = self.run_git_with_retry(["git", "pull", "origin", "main", "--allow-unrelated-histories", "--no-edit"])
        if success: 
            self.root.after(0, self.update_status, "✅ 强制联通成功")
            self.root.after(0, messagebox.showinfo, "完成", "已强行接通历史，解决无关历史报错。")
        else: 
            self.root.after(0, self.update_status, "❌ 联通失败", "red")
            self.root.after(0, messagebox.showerror, "错误", err)

    def git_set_proxy(self):
        port = self.entry_proxy_port.get().strip()
        if not port.isdigit():
            self.root.after(0, self.update_status, "⚠️ 请输入正确端口号", "#ffc107")
            return
        port_int = int(port)
        if port_int < 1 or port_int > 65535:
            self.root.after(0, self.update_status, "⚠️ 端口号范围 1-65535", "#ffc107")
            return
        self.root.after(0, self.save_config)

        proxy_url = f"http://127.0.0.1:{port_int}"
        self.log(f"设置代理: http.proxy={proxy_url} / https.proxy={proxy_url}")
        res1 = subprocess.run(["git", "config", "--global", "http.proxy", proxy_url], capture_output=True, text=True, creationflags=CREATE_NO_WINDOW)
        res2 = subprocess.run(["git", "config", "--global", "https.proxy", proxy_url], capture_output=True, text=True, creationflags=CREATE_NO_WINDOW)
        if res1.returncode == 0 and res2.returncode == 0:
            self.root.after(0, self.update_status, f"✅ 已启用代理: 127.0.0.1:{port_int}")
        else:
            err = (res1.stderr or res1.stdout or "") + "\n" + (res2.stderr or res2.stdout or "")
            if err.strip():
                self.log(f"代理设置失败: {err.strip()}")
            self.root.after(0, self.update_status, "❌ 代理设置失败", "red")
            self.root.after(0, messagebox.showerror, "错误", err.strip() or "未知错误")

    def git_unset_proxy(self):
        self.log("取消代理: unset http.proxy / https.proxy")
        res1 = subprocess.run(["git", "config", "--global", "--unset", "http.proxy"], capture_output=True, text=True, creationflags=CREATE_NO_WINDOW)
        res2 = subprocess.run(["git", "config", "--global", "--unset", "https.proxy"], capture_output=True, text=True, creationflags=CREATE_NO_WINDOW)
        if res1.returncode == 0 and res2.returncode == 0:
            self.root.after(0, self.update_status, "✅ 已取消代理")
            return

        stderr_all = ((res1.stderr or res1.stdout or "") + "\n" + (res2.stderr or res2.stdout or "")).strip()
        if "unset" in stderr_all.lower() or "not found" in stderr_all.lower():
            self.root.after(0, self.update_status, "✅ 已取消代理")
        else:
            if stderr_all:
                self.log(f"取消代理失败: {stderr_all}")
            self.root.after(0, self.update_status, "❌ 取消代理失败", "red")
            self.root.after(0, messagebox.showerror, "错误", stderr_all or "未知错误")

    # --- 初始化窗口 ---
    def open_init_window(self):
        i_win = tk.Toplevel(self.root)
        i_win.title("仓库初始化向导")
        i_win.geometry("600x320")
        i_win.configure(bg=self.colors["background"])
        i_win.grab_set()

        i_win.grid_columnconfigure(1, weight=1)

        ttk.Label(i_win, text="填写云端信息", style='Header.TLabel').grid(row=0, column=0, columnspan=3, pady=(20, 15))

        # 远程URL
        ttk.Label(i_win, text="GitHub URL:").grid(row=1, column=0, padx=15, pady=10, sticky="e")
        e_url = ttk.Entry(i_win, font=('微软雅黑', 10))
        e_url.grid(row=1, column=1, columnspan=2, sticky="ew", padx=(0, 15))

        # GitIgnore
        ttk.Label(i_win, text=".gitignore 源:").grid(row=2, column=0, padx=15, pady=10, sticky="e")
        e_ignore = ttk.Entry(i_win, font=('微软雅黑', 10))
        e_ignore.grid(row=2, column=1, sticky="ew", padx=(0, 5))
        ttk.Button(i_win, text="浏览", command=lambda: self.select_file(e_ignore)).grid(row=2, column=2, padx=(0, 15), sticky="w")

        # GitAttributes
        ttk.Label(i_win, text=".gitattributes 源:").grid(row=3, column=0, padx=15, pady=10, sticky="e")
        e_attr = ttk.Entry(i_win, font=('微软雅黑', 10))
        e_attr.grid(row=3, column=1, sticky="ew", padx=(0, 5))
        ttk.Button(i_win, text="浏览", command=lambda: self.select_file(e_attr)).grid(row=3, column=2, padx=(0, 15), sticky="w")

        def start_init():
            url = e_url.get().strip()
            path = self.entry_path.get().strip()
            if not url or not path: 
                messagebox.showwarning("提示", "请填写完整的项目路径和远程 URL！")
                return
            if not os.path.exists(path):
                messagebox.showerror("错误", "项目路径不存在！")
                return

            try:
                os.chdir(path)
                subprocess.run(["git", "init"], creationflags=CREATE_NO_WINDOW, check=True)
                if e_ignore.get(): shutil.copy(e_ignore.get(), os.path.join(path, ".gitignore"))
                if e_attr.get(): shutil.copy(e_attr.get(), os.path.join(path, ".gitattributes"))
                subprocess.run(["git", "remote", "add", "origin", url], creationflags=CREATE_NO_WINDOW)
                subprocess.run(["git", "branch", "-M", "main"], creationflags=CREATE_NO_WINDOW)
                messagebox.showinfo("成功", "🎉 初始化完成！")
                i_win.destroy()
            except Exception as e: 
                messagebox.showerror("错误", f"初始化失败: {str(e)}")

        btn_init_run = self.create_front_button(i_win, "🚀 立即执行初始化", "mint", start_init, width=260, height=44)
        btn_init_run.grid(row=4, column=0, columnspan=3, pady=(25, 0))

    # --- 工具函数 ---
    def select_file(self, entry):
        p = filedialog.askopenfilename()
        if p: 
            entry.delete(0, tk.END)
            entry.insert(0, p)

    def get_path(self):
        p = self.entry_path.get().strip()
        if not p or not os.path.exists(p): return None
        try:
            os.chdir(p)
            return p
        except Exception:
            return None

    def select_path(self):
        p = filedialog.askdirectory()
        if p:
            self.entry_path.delete(0, tk.END)
            self.entry_path.insert(0, p)
            self.save_config()

    def load_last_path(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    lines = f.read().splitlines()
                    p = lines[0].strip() if len(lines) > 0 else ""
                    port = lines[1].strip() if len(lines) > 1 else ""
                    if os.path.exists(p):
                        self.entry_path.insert(0, p)
                    if port and hasattr(self, "entry_proxy_port"):
                        self.entry_proxy_port.insert(0, port)
            except Exception:
                pass

    def save_config(self):
        p = self.entry_path.get().strip()
        port = ""
        if hasattr(self, "entry_proxy_port"):
            port = self.entry_proxy_port.get().strip()
        try:
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                f.write(p + "\n" + port)
        except Exception:
            pass

if __name__ == "__main__":
    root = tk.Tk()
    app = GitTool(root)
    root.mainloop()
