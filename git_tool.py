import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import os

class GitTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Git 分步操作工具")
        self.root.geometry("450x300")

        # --- 第一行：项目位置 ---
        tk.Label(root, text="1. 项目目录:").grid(row=0, column=0, sticky="w", padx=10, pady=10)
        self.entry_path = tk.Entry(root, width=40)
        self.entry_path.grid(row=0, column=1, padx=5)
        tk.Button(root, text="选择", command=self.select_path).grid(row=0, column=2, padx=5)

        # --- 第二行：Add 操作 ---
        tk.Label(root, text="2. 暂存文件:").grid(row=1, column=0, sticky="w", padx=10, pady=10)
        tk.Button(root, text="执行 git add .", width=35, command=self.git_add).grid(row=1, column=1, columnspan=2)

        # --- 第三行：Commit 操作 ---
        tk.Label(root, text="3. 提交描述:").grid(row=2, column=0, sticky="w", padx=10, pady=10)
        self.entry_msg = tk.Entry(root, width=40)
        self.entry_msg.grid(row=2, column=1, padx=5)
        tk.Button(root, text="Commit", command=self.git_commit).grid(row=2, column=2, padx=5)

        # --- 第四行：Push 操作 ---
        tk.Label(root, text="4. 推送远端:").grid(row=3, column=0, sticky="w", padx=10, pady=10)
        tk.Button(root, text="执行 git push origin main", width=35, bg="#28a745", fg="white", command=self.git_push).grid(row=3, column=1, columnspan=2)

        # 状态显示
        self.status_label = tk.Label(root, text="状态: 等待操作", fg="blue")
        self.status_label.grid(row=4, column=0, columnspan=3, pady=20)

    def get_path(self):
        path = self.entry_path.get()
        if not path:
            messagebox.showwarning("提示", "请先选择项目目录")
            return None
        os.chdir(path)
        return path

    def select_path(self):
        path = filedialog.askdirectory()
        self.entry_path.delete(0, tk.END)
        self.entry_path.insert(0, path)

    def git_add(self):
        if self.get_path():
            try:
                subprocess.run(["git", "add", "."], check=True)
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
                subprocess.run(["git", "commit", "-m", msg], check=True)
                self.status_label.config(text="状态: Commit 成功", fg="green")
            except Exception as e:
                messagebox.showerror("错误", f"Commit 失败: {e}")

    def git_push(self):
        if self.get_path():
            self.status_label.config(text="状态: 正在 Push...", fg="orange")
            self.root.update() # 刷新界面显示
            try:
                subprocess.run(["git", "push", "origin", "main"], check=True)
                self.status_label.config(text="状态: Push 成功！", fg="green")
                messagebox.showinfo("成功", "已推送到 origin main")
            except Exception as e:
                messagebox.showerror("错误", f"Push 失败: {e}")
                self.status_label.config(text="状态: Push 失败", fg="red")

if __name__ == "__main__":
    root = tk.Tk()
    app = GitTool(root)
    root.mainloop()