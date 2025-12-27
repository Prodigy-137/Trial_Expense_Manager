import customtkinter as ctk
import json
import os
import csv
from datetime import datetime
from tkinter import messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkcalendar import DateEntry


ctk.set_appearance_mode("Dark")
ACCENT_COLOR = "#38BDF8"  
BG_COLOR = "#0F172A"     
CARD_COLOR = "#1E293B"    
SUCCESS_COLOR = "#10B981" 
ERROR_COLOR = "#F43F5E"   

class ModernFinancePro(ctk.CTk):
    def __init__(self):
        super().__init__()

        
        self.title("NEURAL FINANCE • PRO")
        self.geometry("1200x800")
        self.configure(fg_color=BG_COLOR)    
        self.data_file = "data.json"
        self.settings_file = "settings.json"   
        self.records = self.load_data()
        self.settings = self.load_settings()
        self.currency = self.settings.get("currency", "$")
        self.process_recurring()
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.sidebar = ctk.CTkFrame(self, width=240, fg_color="#020617", corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.logo_label = ctk.CTkLabel(self.sidebar, text="NEURAL\nFINANCE", font=("Impact", 24, "bold"), text_color=ACCENT_COLOR)
        self.logo_label.pack(pady=(40, 40))

        
        self.create_nav_btn("Dashboard", self.show_dashboard)
        self.create_nav_btn("Add Transaction", self.show_add_form)
        self.create_nav_btn("History", self.show_history)
        self.create_nav_btn("Subscriptions", self.show_recurring_manager)
        self.create_nav_btn("Monthly Budgets", self.show_budgets)
        self.create_nav_btn("Settings", self.show_settings)

        
        self.main_frame = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=15)
        self.main_frame.grid(row=0, column=1, padx=30, pady=30, sticky="nsew")
        
        self.show_dashboard()

    def create_nav_btn(self, text, command):
       
        btn = ctk.CTkButton(self.sidebar, text=text, command=command, 
                            height=45, fg_color="transparent", 
                            text_color="white", hover_color=CARD_COLOR,
                            anchor="w", font=("Segoe UI", 14, "bold")) 
        btn.pack(pady=5, padx=20, fill="x")

   
    def load_data(self):
        if not os.path.exists(self.data_file): return []
        with open(self.data_file, 'r') as f:
            try: return json.load(f)
            except: return []

    def load_settings(self):
        default = {"currency": "$", "budgets": {}, "expense_categories": ["Food", "Transport", "Rent", "Utilities", "Entertainment"], "recurring": []}
        if not os.path.exists(self.settings_file): return default
        with open(self.settings_file, 'r') as f:
            try:
                data = json.load(f)
                for key in default:
                    if key not in data: data[key] = default[key]
                return data
            except: return default

    def save_settings(self):
        with open(self.settings_file, 'w') as f: json.dump(self.settings, f, indent=4)

    def save_data(self):
        with open(self.data_file, 'w') as f: json.dump(self.records, f, indent=4)

    def process_recurring(self):
        today = datetime.now()
        updated = False
        for item in self.settings.get("recurring", []):
            last_date = datetime.strptime(item['last_billed'], "%Y-%m-%d")
            if (today.year > last_date.year) or (today.month > last_date.month):
                self.records.append({"type": item['type'], "amount": item['amount'], "category": item['category'], "desc": f"AUTOPAY: {item['desc']}", "date": today.strftime("%Y-%m-%d")})
                item['last_billed'] = today.strftime("%Y-%m-%d")
                updated = True
        if updated: self.save_data(); self.save_settings()

    
    def clear_frame(self):
        for widget in self.main_frame.winfo_children(): widget.destroy()

    def show_dashboard(self):
        self.clear_frame()
        cur_month = datetime.now().strftime("%Y-%m")
        inc = sum(r['amount'] for r in self.records if r['type'] == 'Income' and r['date'].startswith(cur_month))
        exp = sum(r['amount'] for r in self.records if r['type'] == 'Expense' and r['date'].startswith(cur_month))
        
        
        ctk.CTkLabel(self.main_frame, text=f"DASHBOARD OVERVIEW", font=("Inter", 12, "bold"), text_color=ACCENT_COLOR).pack(anchor="w", padx=20)
        ctk.CTkLabel(self.main_frame, text=f"{datetime.now().strftime('%B %Y')}", font=("Inter", 32, "bold")).pack(anchor="w", padx=20, pady=(0, 20))

        
        stats_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        stats_frame.pack(fill="x", padx=10)
        
        self.create_hero_card(stats_frame, "Monthly Inflow", inc, SUCCESS_COLOR).grid(row=0, column=0, padx=10)
        self.create_hero_card(stats_frame, "Monthly Outflow", exp, ERROR_COLOR).grid(row=0, column=1, padx=10)
        self.create_hero_card(stats_frame, "Net Liquid", inc-exp, ACCENT_COLOR).grid(row=0, column=2, padx=10)

       
        if self.settings["budgets"]:
            ctk.CTkLabel(self.main_frame, text="BUDGET THRESHOLDS", font=("Inter", 12, "bold"), text_color=ACCENT_COLOR).pack(anchor="w", padx=20, pady=(40, 10))
            for cat, limit in self.settings["budgets"].items():
                spent = sum(r['amount'] for r in self.records if r['category'].lower() == cat.lower() and r['type'] == 'Expense' and r['date'].startswith(cur_month))
                progress = spent / limit if limit > 0 else 0
                p_color = SUCCESS_COLOR if progress < 0.8 else ("#F59E0B" if progress < 1.0 else ERROR_COLOR)
                
                card = ctk.CTkFrame(self.main_frame, fg_color=CARD_COLOR, height=80, corner_radius=15)
                card.pack(fill="x", padx=20, pady=5)
                ctk.CTkLabel(card, text=f"{cat} • {self.currency}{spent}/{self.currency}{limit}", font=("Inter", 14)).pack(side="left", padx=20)
                bar = ctk.CTkProgressBar(card, progress_color=p_color, fg_color="#334155", width=400)
                bar.pack(side="right", padx=20)
                bar.set(min(progress, 1.0))

        if exp > 0: self.show_chart()

    def create_hero_card(self, master, title, val, color):
        card = ctk.CTkFrame(master, width=280, height=140, fg_color=CARD_COLOR, corner_radius=20, border_width=1, border_color="#334155")
        card.grid_propagate(False)
        ctk.CTkLabel(card, text=title, font=("Inter", 14), text_color="#94A3B8").pack(pady=(20, 0))
        ctk.CTkLabel(card, text=f"{self.currency}{val:,.2f}", font=("Inter", 28, "bold"), text_color=color).pack(pady=10)
        return card

    def show_chart(self):
        categories = {}
        for r in self.records:
            if r['type'] == 'Expense':
                cat = r['category']
                categories[cat] = categories.get(cat, 0) + r['amount']
        
        fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
        fig.patch.set_facecolor(BG_COLOR)
        colors = ['#38BDF8', '#818CF8', '#C084FC', '#E879F9', '#FB7185']
        ax.pie(categories.values(), labels=categories.keys(), autopct='%1.1f%%', textprops={'color':"w", 'weight':'bold'}, colors=colors, wedgeprops={'width': 0.4})
        ax.set_title("EXPENSE ALLOCATION", color=ACCENT_COLOR, fontdict={'weight':'bold', 'size':12})
        
        canvas = FigureCanvasTkAgg(fig, master=self.main_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(pady=30)

    def show_add_form(self):
        self.clear_frame()
        ctk.CTkLabel(self.main_frame, text="LOG NEW TRANSACTION", font=("Inter", 12, "bold"), text_color=ACCENT_COLOR).pack(pady=(20,0))
        
        panel = ctk.CTkFrame(self.main_frame, fg_color=CARD_COLOR, corner_radius=20, border_width=1, border_color="#334155")
        panel.pack(pady=20, padx=50, fill="x")

        self.type_var = ctk.StringVar(value="Expense")
        self.type_toggle = ctk.CTkSegmentedButton(panel, values=["Income", "Expense"], variable=self.type_var, 
                                                 command=self.toggle_category_input, fg_color="#0F172A", 
                                                 selected_color=ACCENT_COLOR, height=40)
        self.type_toggle.pack(pady=30, padx=40, fill="x")

        
        ctk.CTkLabel(panel, text="Date & Value").pack()
        date_frame = ctk.CTkFrame(panel, fg_color="transparent")
        date_frame.pack()
        
        self.ent_date = DateEntry(date_frame, width=15, background=ACCENT_COLOR, date_pattern='yyyy-mm-dd')
        self.ent_date.pack(side="left", padx=10, pady=10)
        
        self.ent_amt = ctk.CTkEntry(panel, placeholder_text="0.00", width=300, height=45, fg_color=BG_COLOR, border_color="#334155")
        self.ent_amt.pack(pady=10)

        self.cat_container = ctk.CTkFrame(panel, fg_color="transparent")
        self.cat_container.pack(pady=10)
        self.toggle_category_input("Expense")

        self.ent_desc = ctk.CTkEntry(panel, placeholder_text="Description (Optional)", width=400, height=45, fg_color=BG_COLOR, border_color="#334155")
        self.ent_desc.pack(pady=10)

        ctk.CTkButton(panel, text="EXECUTE LOG", command=self.save_record, height=50, width=250, 
                      fg_color=ACCENT_COLOR, text_color=BG_COLOR, font=("Inter", 16, "bold")).pack(pady=40)

    def toggle_category_input(self, selection):
        for widget in self.cat_container.winfo_children(): widget.destroy()
        if selection == "Expense":
            self.cat_input = ctk.CTkOptionMenu(self.cat_container, values=self.settings["expense_categories"], width=400, height=45, fg_color=BG_COLOR, button_color=ACCENT_COLOR)
            self.cat_input.pack()
        else:
            self.cat_input = ctk.CTkEntry(self.cat_container, placeholder_text="Source (Salary, Freelance...)", width=400, height=45, fg_color=BG_COLOR)
            self.cat_input.pack()

    def save_record(self):
        try:
            amt = float(self.ent_amt.get())
            self.records.append({"type": self.type_var.get(), "amount": amt, "category": self.cat_input.get(), 
                                 "desc": self.ent_desc.get(), "date": self.ent_date.get_date().strftime("%Y-%m-%d")})
            self.save_data(); messagebox.showinfo("SYSTEM", "Transaction Authenticated."); self.show_dashboard()
        except: messagebox.showerror("SYSTEM ERROR", "Invalid Monetary Value.")

    def show_history(self, filter_query=None, filter_type="All", filter_cat="All"):
        self.clear_frame()
        ctk.CTkLabel(self.main_frame, text="TRANSACTION LEDGER", font=("Inter", 32, "bold")).pack(pady=20)
        
     
        f_bar = ctk.CTkFrame(self.main_frame, fg_color=CARD_COLOR, corner_radius=15)
        f_bar.pack(fill="x", padx=20, pady=10)
        
        self.search_ent = ctk.CTkEntry(f_bar, placeholder_text="Keyword Search...", width=200, fg_color=BG_COLOR)
        self.search_ent.grid(row=0, column=0, padx=10, pady=15)
        
        self.type_filter = ctk.CTkOptionMenu(f_bar, values=["All", "Income", "Expense"], width=100, fg_color=BG_COLOR)
        self.type_filter.grid(row=0, column=1, padx=5)
        
        self.cat_filter = ctk.CTkOptionMenu(f_bar, values=["All"] + self.settings["expense_categories"], width=120, fg_color=BG_COLOR)
        self.cat_filter.grid(row=0, column=2, padx=5)

        ctk.CTkButton(f_bar, text="FILTER", width=80, fg_color=ACCENT_COLOR, text_color=BG_COLOR, command=self.apply_history_filters).grid(row=0, column=3, padx=10)
        ctk.CTkButton(f_bar, text="EXPORT", width=80, fg_color=SUCCESS_COLOR, command=self.export_to_csv).grid(row=0, column=4, padx=5)

       
        data = self.records
        if filter_query: data = [r for r in data if filter_query.lower() in r.get('desc', "").lower()]
        if filter_type != "All": data = [r for r in data if r['type'] == filter_type]
        if filter_cat != "All": data = [r for r in data if r['category'] == filter_cat]

        for i, r in enumerate(reversed(data)):
            real_idx = self.records.index(r)
            row = ctk.CTkFrame(self.main_frame, fg_color=CARD_COLOR, height=60, corner_radius=10)
            row.pack(fill="x", padx=20, pady=3)
            
            dot_color = SUCCESS_COLOR if r['type'] == "Income" else ERROR_COLOR
            ctk.CTkLabel(row, text="●", text_color=dot_color, width=20).pack(side="left", padx=(20, 10))
            ctk.CTkLabel(row, text=r['date'], font=("Inter", 12), width=100).pack(side="left")
            ctk.CTkLabel(row, text=r['category'].upper(), font=("Inter", 12, "bold"), width=150, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=f"{self.currency}{r['amount']:,.2f}", font=("Inter", 14, "bold"), width=150).pack(side="left")
            ctk.CTkButton(row, text="DELETE", fg_color="transparent", text_color=ERROR_COLOR, width=60, command=lambda idx=real_idx: self.delete_record(idx)).pack(side="right", padx=20)

    def apply_history_filters(self):
        self.show_history(self.search_ent.get(), self.type_filter.get(), self.cat_filter.get())

    def delete_record(self, idx):
        if messagebox.askyesno("VERIFICATION", "Permanently delete this entry?"):
            self.records.pop(idx); self.save_data(); self.show_history()

    def export_to_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if path:
            with open(path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Date", "Type", "Category", "Amount", "Description"])
                for r in self.records: writer.writerow([r['date'], r['type'], r['category'], r['amount'], r.get('desc', "")])
            messagebox.showinfo("EXPORT", "Data synchronized to CSV.")

    def show_budgets(self):
        self.clear_frame()
        ctk.CTkLabel(self.main_frame, text="ALLOCATION CONTROLS", font=("Inter", 32, "bold")).pack(pady=20)
        panel = ctk.CTkFrame(self.main_frame, fg_color=CARD_COLOR, corner_radius=20)
        panel.pack(fill="x", padx=20, pady=10)
        
        self.budget_cat = ctk.CTkOptionMenu(panel, values=self.settings["expense_categories"], fg_color=BG_COLOR)
        self.budget_cat.grid(row=0, column=0, padx=20, pady=20)
        self.budget_amt = ctk.CTkEntry(panel, placeholder_text="Limit Amount", fg_color=BG_COLOR)
        self.budget_amt.grid(row=0, column=1, padx=10)
        ctk.CTkButton(panel, text="SET LIMIT", fg_color=ACCENT_COLOR, text_color=BG_COLOR, command=self.save_budget).grid(row=0, column=2, padx=20)

        for cat, amt in self.settings["budgets"].items():
            row = ctk.CTkFrame(self.main_frame, fg_color=CARD_COLOR)
            row.pack(fill="x", padx=40, pady=2)
            ctk.CTkLabel(row, text=f"{cat}: {self.currency}{amt}").pack(side="left", padx=20)
            ctk.CTkButton(row, text="REMOVE", fg_color="transparent", text_color=ERROR_COLOR, width=80, command=lambda c=cat: self.remove_budget(c)).pack(side="right", padx=10)

    def save_budget(self):
        try:
            self.settings["budgets"][self.budget_cat.get()] = float(self.budget_amt.get())
            self.save_settings(); self.show_budgets()
        except: pass

    def remove_budget(self, cat):
        del self.settings["budgets"][cat]; self.save_settings(); self.show_budgets()

    def show_recurring_manager(self):
        self.clear_frame()
        ctk.CTkLabel(self.main_frame, text="AUTOMATED FLOWS", font=("Inter", 32, "bold")).pack(pady=20)
        form = ctk.CTkFrame(self.main_frame, fg_color=CARD_COLOR, corner_radius=15)
        form.pack(fill="x", padx=20, pady=10)
        self.rec_type = ctk.CTkSegmentedButton(form, values=["Expense"], fg_color=BG_COLOR)
        self.rec_type.set("Expense")
        self.rec_type.grid(row=0, column=0, padx=10, pady=10)
        self.rec_amt = ctk.CTkEntry(form, placeholder_text="Amount", fg_color=BG_COLOR, width=100)
        self.rec_amt.grid(row=0, column=1, padx=5)
        self.rec_cat = ctk.CTkOptionMenu(form, values=self.settings["expense_categories"], fg_color=BG_COLOR, width=120)
        self.rec_cat.grid(row=0, column=2, padx=5)
        self.rec_desc = ctk.CTkEntry(form, placeholder_text="Flow Name", fg_color=BG_COLOR, width=120)
        self.rec_desc.grid(row=0, column=3, padx=5)
        ctk.CTkButton(form, text="ACTIVATE", fg_color=ACCENT_COLOR, text_color=BG_COLOR, command=self.add_recurring).grid(row=0, column=4, padx=10)

        for i, item in enumerate(self.settings["recurring"]):
            row = ctk.CTkFrame(self.main_frame, fg_color=CARD_COLOR)
            row.pack(fill="x", padx=40, pady=2)
            ctk.CTkLabel(row, text=f"LOOP: {item['desc']} • {self.currency}{item['amount']}").pack(side="left", padx=20)
            ctk.CTkButton(row, text="TERMINATE", fg_color="transparent", text_color=ERROR_COLOR, command=lambda idx=i: self.remove_recurring(idx)).pack(side="right", padx=10)

    def add_recurring(self):
        try:
            self.settings["recurring"].append({"type": self.rec_type.get(), "amount": float(self.rec_amt.get()), 
                                              "category": self.rec_cat.get(), "desc": self.rec_desc.get(), 
                                              "last_billed": datetime.now().strftime("%Y-%m-%d")})
            self.save_settings(); self.show_recurring_manager()
        except: pass

    def remove_recurring(self, idx):
        self.settings["recurring"].pop(idx); self.save_settings(); self.show_recurring_manager()

    def show_settings(self):
        self.clear_frame()
        ctk.CTkLabel(self.main_frame, text="SYSTEM CONFIGURATION", font=("Inter", 32, "bold")).pack(pady=20)
        
      
        box = ctk.CTkFrame(self.main_frame, fg_color=CARD_COLOR, corner_radius=15)
        box.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(box, text="GLOBAL CURRENCY SYMBOL").pack(pady=5)
        self.curr_menu = ctk.CTkOptionMenu(box, values=["$", "€", "£", "¥", "A$", "Custom"], fg_color=BG_COLOR, command=self.change_currency_preset)
        self.curr_menu.set(self.currency if self.currency in ["$", "€", "£", "¥", "A$"] else "Custom")
        self.curr_menu.pack(pady=10)
        self.custom_curr_entry = ctk.CTkEntry(box, placeholder_text="Custom Tag", fg_color=BG_COLOR)
        self.custom_curr_entry.pack(pady=5)
        ctk.CTkButton(box, text="UPDATE CURRENCY", fg_color=ACCENT_COLOR, text_color=BG_COLOR, command=self.apply_custom_currency).pack(pady=10)

        
        cat_box = ctk.CTkFrame(self.main_frame, fg_color=CARD_COLOR, corner_radius=15)
        cat_box.pack(fill="x", padx=20, pady=20)
        ctk.CTkLabel(cat_box, text="EXPENSE CATEGORY REGISTRY").pack(pady=10)
        self.new_cat_entry = ctk.CTkEntry(cat_box, placeholder_text="New Identifier", fg_color=BG_COLOR)
        self.new_cat_entry.pack(side="left", padx=20, pady=20)
        ctk.CTkButton(cat_box, text="REGISTER", fg_color=ACCENT_COLOR, text_color=BG_COLOR, command=self.add_new_category).pack(side="left")

        for cat in self.settings["expense_categories"]:
            r = ctk.CTkFrame(self.main_frame, fg_color=CARD_COLOR)
            r.pack(fill="x", padx=60, pady=2)
            ctk.CTkLabel(r, text=cat).pack(side="left", padx=20)
            ctk.CTkButton(r, text="DE-REGISTER", fg_color="transparent", text_color=ERROR_COLOR, width=30, command=lambda c=cat: self.remove_category(c)).pack(side="right", padx=10)

    def change_currency_preset(self, choice):
        if choice != "Custom": self.currency = choice; self.settings["currency"] = choice; self.save_settings()

    def apply_custom_currency(self):
        val = self.custom_curr_entry.get().strip()
        if val: self.currency = val; self.settings["currency"] = val; self.save_settings()

    def add_new_category(self):
        c = self.new_cat_entry.get().strip()
        if c and c not in self.settings["expense_categories"]: self.settings["expense_categories"].append(c); self.save_settings(); self.show_settings()

    def remove_category(self, c):
        if len(self.settings["expense_categories"]) > 1: self.settings["expense_categories"].remove(c); self.save_settings(); self.show_settings()

if __name__ == "__main__":
    app = ModernFinancePro()
    app.mainloop()
