import customtkinter as ctk
from tkinter import messagebox
import sqlite3
from datetime import date, timedelta
import requests
import threading
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# ---------------- SETTINGS ----------------
API_KEY = "pxWltwCBX2NabhrQ2TXjco3IunvfWNhUg3fWniA6"
DAILY_GOAL = 2000

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

# ---------------- DATABASE ----------------
conn = sqlite3.connect("diet.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS diet(
    id INTEGER PRIMARY KEY AUTOINCREMENT, meal TEXT, food TEXT, 
    weight REAL, calories REAL, date TEXT
)
""")
conn.commit()


# ---------------- LOGIC ----------------
class DietTracker:
    def __init__(self):
        self.validation_timer = None
        self.current_cal100 = None
        self.cache = {}
        self.view_date = date.today()
        # Non-food items to block
        self.BLACKLIST = ["metal", "rock", "wood", "plastic", "glass", "paper", "stone", "iron", "steel", "copper"]
        # Legitimate food words that might contain a blacklisted word
        self.EXCEPTIONS = ["mushroom", "candy", "apple", "bean", "water", "salt"]

    def get_usda_data(self, food):
        """Deep search with a strict 'Real Food' filter"""
        food_query = food.lower().strip()

        # 1. Immediate Blacklist Check
        if food_query in self.BLACKLIST:
            return None

        if food_query in self.cache:
            return self.cache[food_query]

        try:
            url = "https://api.nal.usda.gov/fdc/v1/foods/search"
            params = {"query": food_query, "pageSize": 10, "api_key": API_KEY}
            r = requests.get(url, params=params, timeout=5)
            data = r.json()

            if "foods" in data and len(data["foods"]) > 0:
                for item in data["foods"]:
                    item_name = item.get("description", "").lower()

                    # 2. Check if the result name contains a blacklisted word
                    has_bad_word = any(word in item_name for word in self.BLACKLIST)
                    # 3. Check if it's a valid exception (e.g., 'Rock Candy')
                    is_exception = any(ex in item_name for ex in self.EXCEPTIONS)

                    if has_bad_word and not is_exception:
                        continue  # Skip this result, it's probably non-food packaging

                    for n in item.get("foodNutrients", []):
                        if "energy" in n.get("nutrientName", "").lower():
                            val = float(n.get("value", 0))
                            unit = n.get("unitName", "").upper()
                            if unit == "KJ": val *= 0.239

                            if val > 0:
                                self.cache[food_query] = val
                                return val
            return None
        except:
            return None

    def validate_food_live(self, event):
        food = food_entry.get().strip()
        if not food:
            food_entry.configure(border_color=["#979797", "#565b5e"])
            return
        if food.lower() in self.cache:
            self.current_cal100 = self.cache[food.lower()]
            food_entry.configure(border_color="green")
            return

        if self.validation_timer:
            app.after_cancel(self.validation_timer)

        food_entry.configure(border_color="yellow")
        self.validation_timer = app.after(600, self.perform_validation, food)

    def perform_validation(self, food):
        def thread_task():
            cals = self.get_usda_data(food)
            app.after(0, self.update_ui_validation, cals)

        threading.Thread(target=thread_task, daemon=True).start()

    def update_ui_validation(self, cals):
        if cals:
            food_entry.configure(border_color="green")
            self.current_cal100 = cals
        else:
            food_entry.configure(border_color="red")
            self.current_cal100 = None

    def change_date(self, days):
        self.view_date += timedelta(days=days)
        date_label.configure(text=self.view_date.strftime("%B %d, %Y"))
        update_ui_elements()

    def add_meal(self):
        food = food_entry.get().strip()
        weight_str = weight_entry.get().strip()
        if self.current_cal100 is None:
            messagebox.showerror("Invalid", f"'{food}' is not recognized as a food item.")
            return
        try:
            weight = float(weight_str)
            if weight <= 0: raise ValueError
            calories = (weight / 100) * self.current_cal100
            cursor.execute("INSERT INTO diet(meal,food,weight,calories,date) VALUES(?,?,?,?,?)",
                           (meal_var.get(), food, weight, calories, str(self.view_date)))
            conn.commit()
            food_entry.delete(0, "end")
            weight_entry.delete(0, "end")
            food_entry.configure(border_color=["#979797", "#565b5e"])
            update_ui_elements()
            messagebox.showinfo("Success", f"Added {round(calories, 1)} kcal")
        except:
            messagebox.showerror("Error", "Please enter a valid weight.")


tracker = DietTracker()


# ---------------- UI UPDATES ----------------
def update_ui_elements():
    output.delete("1.0", "end")
    cursor.execute("SELECT meal,food,weight,calories FROM diet WHERE date=?", (str(tracker.view_date),))
    rows = cursor.fetchall()
    total = 0
    if not rows:
        output.insert("end", f"No records found for this date.")
    else:
        for r in rows:
            total += r[3]
            output.insert("end", f"• [{r[0]}] {r[1].title()}: {round(r[3], 1)} kcal ({r[2]}g)\n")

    percent = min(total / DAILY_GOAL, 1)
    progress.set(percent)
    progress_label.configure(text=f"{round(total, 1)} / {DAILY_GOAL} kcal")


def draw_graph():
    for w in graph_frame.winfo_children(): w.destroy()
    days, cals = [], []
    for i in range(6, -1, -1):
        d = str(date.today() - timedelta(days=i))
        cursor.execute("SELECT SUM(calories) FROM diet WHERE date=?", (d,))
        v = cursor.fetchone()[0]
        days.append((date.today() - timedelta(days=i)).strftime("%a"))
        cals.append(v if v else 0)
    fig = Figure(figsize=(5, 3), dpi=100)
    ax = fig.add_subplot(111);
    ax.bar(days, cals, color="#2fa572")
    ax.set_title("Weekly Trends")
    FigureCanvasTkAgg(fig, graph_frame).get_tk_widget().pack(fill="both", expand=True)


# ---------------- MAIN UI ----------------
app = ctk.CTk()
app.geometry("900x850")
app.title("Smart Diet Tracker v3.0")

nav = ctk.CTkFrame(app)
nav.pack(fill="x", pady=5)

# Date Navigation
date_nav = ctk.CTkFrame(app)
date_nav.pack(fill="x", pady=5)
ctk.CTkButton(date_nav, text="←", width=40, command=lambda: tracker.change_date(-1)).pack(side="left", padx=20)
date_label = ctk.CTkLabel(date_nav, text=date.today().strftime("%B %d, %Y"), font=("Arial", 18, "bold"))
date_label.pack(side="left", expand=True)
ctk.CTkButton(date_nav, text="→", width=40, command=lambda: tracker.change_date(1)).pack(side="right", padx=20)

dashboard = ctk.CTkFrame(app);
today_page = ctk.CTkFrame(app);
graph_page = ctk.CTkFrame(app)


def show(p):
    for page in [dashboard, today_page, graph_page]: page.pack_forget()
    p.pack(fill="both", expand=True, padx=20, pady=20)


ctk.CTkButton(nav, text="Dashboard", command=lambda: show(dashboard)).pack(side="left", padx=10, pady=10)
ctk.CTkButton(nav, text="Today Log", command=lambda: [show(today_page), update_ui_elements()]).pack(side="left",
                                                                                                    padx=10, pady=10)
ctk.CTkButton(nav, text="Weekly Graph", command=lambda: [show(graph_page), draw_graph()]).pack(side="left", padx=10,
                                                                                               pady=10)

# Dashboard Widgets
progress_label = ctk.CTkLabel(dashboard, text="0 / 2000 kcal", font=("Arial", 20));
progress_label.pack(pady=10)
progress = ctk.CTkProgressBar(dashboard, width=500, height=15);
progress.set(0);
progress.pack(pady=10)

meal_var = ctk.StringVar(value="Breakfast")
ctk.CTkOptionMenu(dashboard, values=["Breakfast", "Lunch", "Dinner", "Snacks"], variable=meal_var).pack(pady=10)

food_entry = ctk.CTkEntry(dashboard, placeholder_text="Food Name (Watch for green border)", width=350, border_width=2)
food_entry.pack(pady=10)
food_entry.bind("<KeyRelease>", tracker.validate_food_live)

weight_entry = ctk.CTkEntry(dashboard, placeholder_text="Weight in grams", width=350)
weight_entry.pack(pady=10)

ctk.CTkButton(dashboard, text="Add Entry to Date", command=tracker.add_meal, font=("Arial", 14, "bold")).pack(pady=20)

# Log Widgets
output = ctk.CTkTextbox(today_page, width=700, height=500, font=("Arial", 15));
output.pack(pady=10)

# Graph
graph_frame = ctk.CTkFrame(graph_page);
graph_frame.pack(fill="both", expand=True)

show(dashboard)
update_ui_elements()
app.mainloop()