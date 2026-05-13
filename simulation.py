import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import random
import simpy

class PizzeriaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Optimale Anzahl der Fahrer")
        self.root.geometry("800x600")
        self.setup_gui()

    def setup_gui(self):
        input_frame = tk.Frame(self.root, pady=20)
        input_frame.pack(side=tk.TOP, fill=tk.X)

        tk.Label(input_frame, text="Bestellungen pro Tag", font=("Times New Roman", 14)).grid(row=0,column=0, padx=10)

        self.entry_base = tk.Entry(input_frame)
        self.entry_base.insert(0, "40")
        self.entry_base.grid(row=0, column=1)

        self.btn_run = tk.Button(input_frame, text="Start",
                                 command=self.run_comparison, bg="#2E86C1", fg="white", font=("Times New Roman", 14, "bold"),
                                 padx=20)
        self.btn_run.grid(row=0, column=2, padx=30)

        self.figure = plt.Figure(figsize=(8, 5), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.root)
        self.canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

    def get_seasonal_factor(self, month):
        factors = {1: 1.5, 2: 1.3, 12: 1.6, 6: 0.8, 7: 0.7, 8: 0.7}
        return factors.get(month, 1.0)

    def run_comparison(self):
        try:
            base_demand = float(self.entry_base.get())
            self.entry_base.config(bg="white")
        except ValueError:
            self.entry_base.config(bg="#ffcccc")
            return
        self.btn_run.config(state="disabled")
        self.root.update_idletasks()

        days = 365
        avg_pizza_price = 25
        rent_per_day = 60
        salary_per_driver = 80
        cost_per_pizza_pct = 0.40
        driver_capacity = 15
        final_profits = []
        simulations = 10

        for n_drivers in range(1, 6):
            total_profit = 0

            for sim in range(simulations):
                yearly_total = 0

                for d in range(1, days + 1):
                    month = (d // 30) % 12 + 1
                    s_factor = self.get_seasonal_factor(month)

                    w_rand = random.random()
                    w_factor = 1.4 if w_rand > 0.7 else 1.0

                    orders = max(0, int(base_demand * s_factor * w_factor + random.randint(-3, 3)))
                    avg_wait = simulate_deliveries(min(orders, 40), n_drivers)
                    delay_penalty = avg_wait * 0.5

                    revenue = sum(max(10, np.random.normal(avg_pizza_price, 4)) for _ in range(orders))

                    prod_costs = revenue * cost_per_pizza_pct
                    personal_costs = n_drivers * salary_per_driver

                    capacity = n_drivers * driver_capacity
                    penalty = 0
                    if orders > capacity:
                        penalty = (orders - capacity) * (avg_pizza_price * 0.5)

                    daily_profit = revenue - (prod_costs + rent_per_day + personal_costs + penalty + delay_penalty)
                    yearly_total += daily_profit

                total_profit += yearly_total

            avg_yearly_profit = total_profit / simulations
            final_profits.append(avg_yearly_profit)

        self.update_plot(final_profits)
        self.btn_run.config(state="normal")

    def update_plot(self, profits):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        drivers_labels = ['1 Fahrer', '2 Fahrer', '3 Fahrer', '4 Fahrer', '5 Fahrer']

        bars = ax.bar(drivers_labels, profits, color=['#AED6F1', '#85C1E9', '#3498DB', '#2E86C1', '#21618C'])

        ax.set_ylabel("Gesamtgewinn pro Jahr (BGN)")

        for bar in bars:
            yval = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, yval + 500, f"{int(yval)}", ha='center', va='bottom')

        self.canvas.draw()

def simulate_deliveries(orders, drivers):
    env = simpy.Environment()
    drivers_resource = simpy.Resource(env, capacity=drivers)
    waiting_times = []

    if orders == 0:
        return 0

    workday_minutes = 720
    avg_interarrival = workday_minutes / orders

    def order(env):
        arrival_time = env.now

        with drivers_resource.request() as req:
            yield req

            wait = env.now - arrival_time
            waiting_times.append(wait)

            delivery_time = random.uniform(10, 20)
            yield env.timeout(delivery_time)

    def order_generator(env):
        for _ in range(orders):
            env.process(order(env))
            interarrival = max(1, random.uniform(avg_interarrival * 0.7, avg_interarrival * 1.3))
            yield env.timeout(interarrival)

    env.process(order_generator(env))
    env.run()

    return np.mean(waiting_times) if waiting_times else 0

if __name__ == "__main__":
    root = tk.Tk()
    app = PizzeriaApp(root)
    root.mainloop()