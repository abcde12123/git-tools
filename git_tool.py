import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import os
import shutil

# 隐藏 cmd 窗口
CREATE_NO_WINDOW = 0x08000000

# 配置文件路径
CONFIG_FILE = os.path.join(os.getenv('APPDATA'), "git_tool_config.txt")
INIT_CONFIG_FILE = os.path.join(os.getenv('APPDATA'), "git_init_tool_config.txt")

class GitTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Git 自动化工具")
        self.root.geometry("520x350")
        
        # 左右居中
        self.root.grid_columnconfigure(0, weight=1) # 左侧弹性空间
        self.root.grid_columnconfigure(3, weight=1) # 右侧弹性空间

        try:
            self.root.iconbitmap("1.ico")
        except:
            pass # 防止没有图标文件时程序崩溃

        # 项目位置 
        tk.Label(root, text="项目目录:").grid(row=0, column=1, sticky="e", padx=5, pady=10)
        self.entry_path = tk.Entry(root, width=40)
        self.entry_path.grid(row=0, column=2, sticky="w", padx=5)
        # 将选择按钮放在与输入框同一单元格或相邻列
        btn_frame = tk.Frame(root) # 小容器放置输入框后的按钮
        btn_frame.grid(row=0, column=2, sticky="e", padx=5)
        # 为了不破坏原有 grid 结构，我们直接在 col 2 后面加个小偏移
        tk.Button(root, text="选择", command=self.select_path).grid(row=0, column=3, sticky="w")

        self.load_last_path()

        # Add 操作
        tk.Label(root, text="暂存文件:").grid(row=1, column=1, sticky="e", padx=5, pady=10)
        tk.Button(root, text="执行 git add .", width=42, command=self.git_add).grid(row=1, column=2, columnspan=2, sticky="w")

        # Commit 操作
        tk.Label(root, text="提交描述:").grid(row=2, column=1, sticky="e", padx=5, pady=10)
        self.entry_msg = tk.Entry(root, width=40)
        self.entry_msg.grid(row=2, column=2, sticky="w", padx=5)
        tk.Button(root, text="Commit", command=self.git_commit).grid(row=2, column=3, sticky="w")

        # Push 操作
        tk.Label(root, text="推送至GitHub:").grid(row=3, column=1, sticky="e", padx=5, pady=10)
        tk.Button(root, text="执行 git push", width=42, bg="#28a745", fg="white", command=self.git_push).grid(row=3, column=2, columnspan=2, sticky="w")

        # 初始化入口
        tk.Label(root, text="新项目?").grid(row=4, column=1, sticky="e", padx=5, pady=10)
        tk.Button(root, text="初始化新仓库 (Git Init)", width=42, bg="#007bff", fg="white", command=self.open_init_window).grid(row=4, column=2, columnspan=2, sticky="w")

        self.status_label = tk.Label(root, text="状态: 等待操作", fg="blue", wraplength=400)
        self.status_label.grid(row=5, column=0, columnspan=4, pady=10)

    # 基础功能逻辑
    def load_last_path(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    path = f.read().strip()
                    if os.path.exists(path):
                        self.entry_path.insert(0, path)
            except: pass

    def save_path(self, path):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                f.write(path)
        except: pass

    def translate_error(self, error_msg):
        if "rejected" in error_msg and "fetch first" in error_msg: return "推送失败：远程有新更新，请先 pull。"
        if "could not resolve host" in error_msg: return "推送失败：网络异常。"
        if "permission denied" in error_msg or "403" in error_msg: return "推送失败：权限不足。"
        if "nothing to commit" in error_msg: return "无需提交：工作树干净。"
        return f"错误：{error_msg}"

    def get_path(self):
        path = self.entry_path.get()
        if not path or not os.path.exists(path):
            messagebox.showwarning("提示", "请选择有效的项目目录")
            return None
        os.chdir(path)
        return path

    def select_path(self, entry_widget=None):
        path = filedialog.askdirectory()
        if path:
            target = entry_widget if entry_widget else self.entry_path
            target.delete(0, tk.END)
            target.insert(0, path)
            if not entry_widget: self.save_path(path)

    def browse_file(self, entry_widget):
        file_path = filedialog.askopenfilename()
        if file_path:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, file_path)

    def git_add(self):
        if self.get_path():
            try:
                subprocess.run(["git", "add", "."], check=True, creationflags=CREATE_NO_WINDOW)
                self.status_label.config(text="状态: Add 成功", fg="green")
            except Exception as e: messagebox.showerror("错误", f"Add 失败: {e}")

    def git_commit(self):
        msg = self.entry_msg.get()
        if not msg: messagebox.showwarning("提示", "请填写描述"); return
        if self.get_path():
            try:
                result = subprocess.run(["git", "commit", "-m", msg], capture_output=True, text=True, creationflags=CREATE_NO_WINDOW)
                if result.returncode == 0:
                    self.status_label.config(text="状态: Commit 成功", fg="green")
                    self.entry_msg.delete(0, tk.END)
                else: messagebox.showinfo("提示", self.translate_error(result.stderr))
            except Exception as e: messagebox.showerror("系统错误", str(e))

    def git_push(self):
        if not self.get_path(): return
        self.status_label.config(text="状态: 正在尝试推送...", fg="orange")
        self.root.update()
        try:
            result = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True, creationflags=CREATE_NO_WINDOW)
            if result.returncode == 0:
                self.status_label.config(text="状态: Push 成功！", fg="green")
                messagebox.showinfo("成功", "已推送到远程仓库")
            else:
                self.status_label.config(text="状态: Push 失败", fg="red")
                messagebox.showerror("失败", self.translate_error(result.stderr))
        except Exception as e: messagebox.showerror("错误", str(e))

    # 初始化窗口
    def open_init_window(self):
        init_win = tk.Toplevel(self.root)
        init_win.title("仓库初始化设置")
        init_win.geometry("600x320")
        
        # 子窗口同样设置列权重实现居中
        init_win.grid_columnconfigure(0, weight=1)
        init_win.grid_columnconfigure(3, weight=1)

        # 路径 + 选择按钮
        tk.Label(init_win, text="项目路径:").grid(row=0, column=1, padx=10, pady=10, sticky="e")
        e_path = tk.Entry(init_win, width=45)
        e_path.grid(row=0, column=2, sticky="w")
        e_path.insert(0, self.entry_path.get())
        tk.Button(init_win, text="选择", command=lambda: self.select_path(e_path)).grid(row=0, column=3, padx=5, sticky="w")

        # 2 .gitignore
        tk.Label(init_win, text=".gitignore 源:").grid(row=1, column=1, padx=10, pady=10, sticky="e")
        e_ignore = tk.Entry(init_win, width=45)
        e_ignore.grid(row=1, column=2, sticky="w")
        tk.Button(init_win, text="浏览", command=lambda: self.browse_file(e_ignore)).grid(row=1, column=3, padx=5, sticky="w")

        # 3 .gitattributes
        tk.Label(init_win, text=".gitattributes 源:").grid(row=2, column=1, padx=10, pady=10, sticky="e")
        e_attr = tk.Entry(init_win, width=45)
        e_attr.grid(row=2, column=2, sticky="w")
        tk.Button(init_win, text="浏览", command=lambda: self.browse_file(e_attr)).grid(row=2, column=3, padx=5, sticky="w")

        # 4. Git URL
        tk.Label(init_win, text="GitHub URL:").grid(row=3, column=1, padx=10, pady=10, sticky="e")
        e_url = tk.Entry(init_win, width=45)
        e_url.grid(row=3, column=2, sticky="w")

        # 加载记忆
        init_data = self.load_init_config()
        if init_data.get('ignore'): e_ignore.insert(0, init_data['ignore'])
        if init_data.get('attr'): e_attr.insert(0, init_data['attr'])
        if init_data.get('url'): e_url.insert(0, init_data['url'])

        def start_init():
            path = e_path.get()
            url = e_url.get()
            ignore_src = e_ignore.get()
            attr_src = e_attr.get()

            if not path or not url: messagebox.showwarning("提示", "路径和URL不能为空"); return
            self.save_init_config(ignore_src, attr_src, url)
            
            try:
                os.chdir(path)
                subprocess.run(["git", "init"], check=True, creationflags=CREATE_NO_WINDOW)
                if ignore_src and os.path.exists(ignore_src):
                    shutil.copy(ignore_src, os.path.join(path, ".gitignore"))
                if attr_src and os.path.exists(attr_src):
                    shutil.copy(attr_src, os.path.join(path, ".gitattributes"))
                subprocess.run(["git", "remote", "add", "origin", url], creationflags=CREATE_NO_WINDOW)
                subprocess.run(["git", "branch", "-M", "main"], creationflags=CREATE_NO_WINDOW)
                
                messagebox.showinfo("完成", "Git 初始化成功！")
                init_win.destroy()
            except Exception as e: messagebox.showerror("初始化错误", str(e))

        tk.Button(init_win, text="开始初始化仓库", bg="#007bff", fg="white", width=40, command=start_init).grid(row=4, column=1, columnspan=3, pady=20)

    def save_init_config(self, ignore, attr, url):
        try:
            with open(INIT_CONFIG_FILE, "w", encoding="utf-8") as f:
                f.write(f"{ignore}\n{attr}\n{url}")
        except: pass

    def load_init_config(self):
        if os.path.exists(INIT_CONFIG_FILE):
            try:
                with open(INIT_CONFIG_FILE, "r", encoding="utf-8") as f:
                    lines = f.read().splitlines()
                    return {'ignore': lines[0], 'attr': lines[1], 'url': lines[2]}
            except: pass
        return {}

if __name__ == "__main__":
    root = tk.Tk()
    app = GitTool(root)
    root.mainloop()