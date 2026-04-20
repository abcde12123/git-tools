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

class GitTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Git 自动化工具 v2.6 ")
        self.root.geometry("680x620")
        self.root.configure(bg="#f8f9fa")
        
        # 设置全局样式
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TButton', font=('微软雅黑', 10), padding=5)
        self.style.configure('Action.TButton', font=('微软雅黑', 10, 'bold'), foreground='white')
        self.style.configure('TLabel', background="#f8f9fa", font=('微软雅黑', 10))
        self.style.configure('Header.TLabel', font=('微软雅黑', 12, 'bold'), foreground='#343a40')

        # 布局核心：响应式居中
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=4)
        self.root.grid_columnconfigure(2, weight=1)

        self.setup_ui()
        self.load_last_path()

    def setup_ui(self):
        # --- 顶部：项目路径选择 ---
        frame_path = tk.Frame(self.root, bg="#f8f9fa")
        frame_path.grid(row=0, column=0, columnspan=3, pady=(20, 10), padx=20, sticky="ew")
        frame_path.grid_columnconfigure(1, weight=1)

        ttk.Label(frame_path, text="📁 项目路径:").grid(row=0, column=0, sticky="e", padx=5)
        self.entry_path = ttk.Entry(frame_path, font=('微软雅黑', 10))
        self.entry_path.grid(row=0, column=1, sticky="ew", padx=5)
        ttk.Button(frame_path, text="浏览", command=self.select_path, width=8).grid(row=0, column=2, sticky="w")

        ttk.Separator(self.root, orient='horizontal').grid(row=1, column=0, columnspan=3, sticky="ew", padx=20, pady=5)

        # --- 主操作区 ---
        frame_ops = tk.Frame(self.root, bg="white", highlightbackground="#dee2e6", highlightthickness=1, bd=0)
        frame_ops.grid(row=2, column=1, pady=10, sticky="nsew")
        frame_ops.grid_columnconfigure(0, weight=1)

        ttk.Label(frame_ops, text="📌 日常工作流", style='Header.TLabel', background="white").grid(row=0, column=0, pady=(15, 10))

        btn_w = 40
        self.btn_pull = tk.Button(frame_ops, text="⬇️ 1. 从远程更新 (Git Pull)", width=btn_w, bg="#17a2b8", fg="white", font=('微软雅黑', 10, 'bold'), relief="flat", cursor="hand2", command=lambda: self.run_thread(self.git_pull))
        self.btn_pull.grid(row=1, column=0, pady=6)

        self.btn_add = tk.Button(frame_ops, text="➕ 2. 暂存所有更改 (Git Add)", width=btn_w, bg="#6c757d", fg="white", font=('微软雅黑', 10, 'bold'), relief="flat", cursor="hand2", command=lambda: self.run_thread(self.git_add))
        self.btn_add.grid(row=2, column=0, pady=6)

        f_commit = tk.Frame(frame_ops, bg="white")
        f_commit.grid(row=3, column=0, pady=6)
        ttk.Label(f_commit, text="📝 描述:", background="white").pack(side="left")
        self.entry_msg = ttk.Entry(f_commit, width=28, font=('微软雅黑', 10))
        self.entry_msg.pack(side="left", padx=5)
        self.btn_commit = tk.Button(f_commit, text="提交", bg="#ffc107", fg="#343a40", font=('微软雅黑', 9, 'bold'), relief="flat", cursor="hand2", command=lambda: self.run_thread(self.git_commit))
        self.btn_commit.pack(side="left")

        self.btn_push = tk.Button(frame_ops, text="⬆️ 3. 推送至云端 (Git Push)", width=btn_w, bg="#28a745", fg="white", font=('微软雅黑', 10, 'bold'), relief="flat", cursor="hand2", command=lambda: self.run_thread(self.git_push))
        self.btn_push.grid(row=4, column=0, pady=(10, 15))

        # --- 高级管理区 ---
        frame_adv = tk.Frame(self.root, bg="white", highlightbackground="#dee2e6", highlightthickness=1, bd=0)
        frame_adv.grid(row=3, column=1, pady=10, sticky="nsew")
        frame_adv.grid_columnconfigure(0, weight=1)
        frame_adv.grid_columnconfigure(1, weight=1)

        ttk.Label(frame_adv, text="⚙️ 仓库配置与修复", style='Header.TLabel', background="white").grid(row=0, column=0, columnspan=2, pady=(15, 10))

        self.btn_init = tk.Button(frame_adv, text="🆕 初始化新仓库", width=18, bg="#007bff", fg="white", font=('微软雅黑', 9, 'bold'), relief="flat", cursor="hand2", command=self.open_init_window)
        self.btn_init.grid(row=1, column=0, padx=10, pady=(5, 15), sticky="e")

        self.btn_force = tk.Button(frame_adv, text="🔧 强制联通云端", width=18, bg="#dc3545", fg="white", font=('微软雅黑', 9, 'bold'), relief="flat", cursor="hand2", command=lambda: self.run_thread(self.git_pull_force))
        self.btn_force.grid(row=1, column=1, padx=10, pady=(5, 15), sticky="w")

        # --- 状态与进度条 ---
        frame_status = tk.Frame(self.root, bg="#f8f9fa")
        frame_status.grid(row=4, column=0, columnspan=3, pady=(10, 0), sticky="ew")
        frame_status.grid_columnconfigure(0, weight=1)

        self.status_var = tk.StringVar(value="状态: 准备就绪")
        self.status_label = tk.Label(frame_status, textvariable=self.status_var, fg="#495057", bg="#f8f9fa", font=("微软雅黑", 9, "bold"))
        self.status_label.grid(row=0, column=0, pady=(0, 5))

        self.progress = ttk.Progressbar(frame_status, orient="horizontal", mode="indeterminate")
        # 修复进度条初始显示问题：默认隐藏
        self.progress.grid_remove()

    # --- 线程与 UI 状态管理 ---
    def set_buttons_state(self, state):
        state_str = tk.NORMAL if state else tk.DISABLED
        self.btn_pull.config(state=state_str)
        self.btn_add.config(state=state_str)
        self.btn_commit.config(state=state_str)
        self.btn_push.config(state=state_str)
        self.btn_init.config(state=state_str)
        self.btn_force.config(state=state_str)

    def run_thread(self, func):
        if not self.get_path():
            messagebox.showwarning("提示", "请先选择有效的项目路径！")
            return
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

        threading.Thread(target=thread_target, daemon=True).start()

    def update_status(self, msg, color="#28a745"):
        self.status_var.set(f"状态: {msg}")
        self.status_label.config(fg=color)

    # --- 带有重试机制的网络操作封装 ---
    def run_git_with_retry(self, cmd_list, max_retries=3):
        """执行涉及网络的Git命令，如果失败自动重试"""
        last_err = ""
        for attempt in range(1, max_retries + 1):
            self.root.after(0, self.update_status, f"正在连接服务器... (尝试 {attempt}/{max_retries})", "#007bff")
            res = subprocess.run(cmd_list, capture_output=True, text=True, creationflags=CREATE_NO_WINDOW)
            if res.returncode == 0:
                return True, res.stdout
            else:
                last_err = res.stderr or res.stdout
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

    # --- 初始化窗口 ---
    def open_init_window(self):
        i_win = tk.Toplevel(self.root)
        i_win.title("仓库初始化向导")
        i_win.geometry("600x320")
        i_win.configure(bg="#f8f9fa")
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

        tk.Button(i_win, text="🚀 立即执行初始化", bg="#28a745", fg="white", font=('微软雅黑', 10, 'bold'), relief="flat", cursor="hand2", command=start_init).grid(row=4, column=0, columnspan=3, pady=(25, 0), ipadx=20, ipady=5)

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
            try:
                os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
                with open(CONFIG_FILE, "w", encoding="utf-8") as f: 
                    f.write(p)
            except Exception:
                pass

    def load_last_path(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    p = f.read().strip()
                    if os.path.exists(p): 
                        self.entry_path.insert(0, p)
            except Exception:
                pass

if __name__ == "__main__":
    root = tk.Tk()
    app = GitTool(root)
    root.mainloop()