import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import os

# Windows 专用标志，用于彻底隐藏 cmd 窗口
CREATE_NO_WINDOW = 0x08000000

# --- 修改点：将配置文件指向系统 AppData 目录 ---
# 这会保存在 C:\Users\用户名\AppData\Roaming\git_tool_config.txt
CONFIG_FILE = os.path.join(os.getenv('APPDATA'), "git_tool_config.txt")

class GitTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Git 自动化工具")
        self.root.geometry("500x250")

        # --- 第一行：项目位置 ---
        tk.Label(root, text="1. 项目目录:").grid(row=0, column=0, sticky="w", padx=10, pady=10)
        self.entry_path = tk.Entry(root, width=40)
        self.entry_path.grid(row=0, column=1, padx=5)
        tk.Button(root, text="选择", command=self.select_path).grid(row=0, column=2, padx=5)

        # 启动时加载上次记忆的路径
        self.load_last_path()

        # --- 第二行：Add 操作 ---
        tk.Label(root, text="2. 暂存文件:").grid(row=1, column=0, sticky="w", padx=10, pady=10)
        tk.Button(root, text="执行 git add .", width=35, command=self.git_add).grid(row=1, column=1, columnspan=2)

        # --- 第三行：Commit 操作 ---
        tk.Label(root, text="3. 提交描述:").grid(row=2, column=0, sticky="w", padx=10, pady=10)
        self.entry_msg = tk.Entry(root, width=40)
        self.entry_msg.grid(row=2, column=1, padx=5)
        tk.Button(root, text="Commit", command=self.git_commit).grid(row=2, column=2, padx=5)

        # --- 第四行：Push 操作 ---
        tk.Label(root, text="4. 推送至GitHub:").grid(row=3, column=0, sticky="w", padx=10, pady=10)
        tk.Button(root, text="执行 git push", width=35, bg="#28a745", fg="white", command=self.git_push).grid(row=3, column=1, columnspan=2)

        # 状态显示
        self.status_label = tk.Label(root, text="状态: 等待操作", fg="blue", wraplength=400)
        self.status_label.grid(row=4, column=0, columnspan=3, pady=20)

    def load_last_path(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    path = f.read().strip()
                    if os.path.exists(path):
                        self.entry_path.insert(0, path)
            except:
                pass

    def save_path(self, path):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                f.write(path)
        except:
            pass

    def translate_error(self, error_msg):
        """将常见的 Git 错误翻译成中文"""
        if "rejected" in error_msg and "fetch first" in error_msg:
            return "推送失败：远程仓库有新的更新，请先执行 git pull 合并代码。"
        if "could not resolve host" in error_msg:
            return "推送失败：网络连接超时，请检查你的互联网连接或代理设置。"
        if "permission denied" in error_msg or "403" in error_msg:
            return "推送失败：权限不足。请检查你的 SSH Key 或 Git 账号登录状态。"
        if "nothing to commit, working tree clean" in error_msg:
            return "提交失败：当前没有任何文件修改，无需提交。"
        return f"未知错误：\n{error_msg}"

    def get_path(self):
        path = self.entry_path.get()
        if not path or not os.path.exists(path):
            messagebox.showwarning("提示", "请选择有效的项目目录")
            return None
        os.chdir(path)
        return path

    def select_path(self):
        path = filedialog.askdirectory()
        if path:
            self.entry_path.delete(0, tk.END)
            self.entry_path.insert(0, path)
            self.save_path(path)

    def git_add(self):
        if self.get_path():
            try:
                subprocess.run(["git", "add", "."], check=True, creationflags=CREATE_NO_WINDOW)
                self.status_label.config(text="状态: Add 成功", fg="green")
            except Exception as e:
                messagebox.showerror("错误", f"Add 失败: {e}")

    def git_commit(self):
        msg = self.entry_msg.get()
        if not msg:
            messagebox.showwarning("提示", "请填写 Commit 描述")
            return
        if self.get_path():
            try:
                result = subprocess.run(["git", "commit", "-m", msg], 
                                     capture_output=True, text=True, creationflags=CREATE_NO_WINDOW)
                if result.returncode == 0:
                    self.status_label.config(text="状态: Commit 成功", fg="green")
                    self.entry_msg.delete(0, tk.END)
                else:
                    messagebox.showinfo("提示", self.translate_error(result.stderr))
            except Exception as e:
                messagebox.showerror("系统错误", str(e))

    def git_push(self):
        if not self.get_path(): return

        max_retries = 3
        last_error = ""
        
        for i in range(1, max_retries + 1):
            self.status_label.config(text=f"状态: 正在尝试推送 ({i}/{max_retries})...", fg="orange")
            self.root.update()
            
            try:
                result = subprocess.run(["git", "push", "origin", "main"], 
                                     capture_output=True, text=True, creationflags=CREATE_NO_WINDOW)
                
                if result.returncode == 0:
                    self.status_label.config(text="状态: Push 成功！", fg="green")
                    messagebox.showinfo("成功", "已成功推送到远程仓库")
                    return
                else:
                    last_error = result.stderr
                    if "fetch first" in last_error:
                        break
                        
            except Exception as e:
                last_error = str(e)
            
        self.status_label.config(text="状态: Push 失败", fg="red")
        messagebox.showerror("推送最终失败", self.translate_error(last_error))

if __name__ == "__main__":
    root = tk.Tk()
    app = GitTool(root)
    root.mainloop()