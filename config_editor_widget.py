import tkinter as tk
import tkinter.scrolledtext as scrolledtext
from tkinter import messagebox

class ConfigEditorWidget(tk.Frame):
    def __init__(self, parent, config_path, callback_reload=None):
        super().__init__(parent, bg='#1a1a1a')
        self.config_path = config_path
        self.callback_reload = callback_reload

        tk.Label(self, text="Édition directe du fichier config.txt :", fg="white", bg="#1a1a1a", font=('Arial', 10, 'bold')).pack(anchor='w', padx=5, pady=(10,0))
        self.text = scrolledtext.ScrolledText(self, height=12, width=100, bg="#232323", fg="white", insertbackground='white', font=('Courier', 10))
        self.text.pack(fill='x', expand=False, padx=5, pady=(0,5))
        self.refresh()

        tk.Button(self, text="💾 Enregistrer config.txt", command=self.save, bg='#007acc', fg='white', font=('Arial', 10, 'bold')).pack(anchor='e', padx=10, pady=5)

    def refresh(self):
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            content = f"Erreur de lecture : {e}"
        self.text.config(state='normal')
        self.text.delete(1.0, tk.END)
        self.text.insert(1.0, content)
        self.text.config(state='normal')

    def save(self):
        content = self.text.get(1.0, 'end-1c')
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                f.write(content)
            if self.callback_reload:
                self.callback_reload()
            self.refresh()
            messagebox.showinfo("Succès", "config.txt enregistré et rechargé")
        except Exception as e:
            messagebox.showerror("Erreur", str(e))
