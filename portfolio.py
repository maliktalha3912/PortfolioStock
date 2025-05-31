import tkinter as tk
from tkinter import ttk, messagebox
import yfinance as yf
import sqlite3
from datetime import datetime

class StockPortfolioApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Stock Portfolio Tracker")
        self.root.geometry("900x600")
        
        # Database setup
        self.conn = sqlite3.connect('portfolio.db')
        self.create_table()
        
        # GUI Elements
        self.create_widgets()
        self.load_portfolio()
    
    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS stocks
                          (symbol TEXT PRIMARY KEY, 
                           shares REAL, 
                           buy_price REAL, 
                           date_added TEXT)''')
        self.conn.commit()
    
    def load_portfolio(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM stocks")
        rows = cursor.fetchall()
        for row in rows:
            self.tree.insert("", tk.END, values=row)
    
    def create_widgets(self):
        # Frame for Add Stock
        add_frame = tk.LabelFrame(self.root, text="Add New Stock", padx=10, pady=10)
        add_frame.pack(pady=10, padx=10, fill="x")
        
        tk.Label(add_frame, text="Symbol:").grid(row=0, column=0)
        self.symbol_entry = tk.Entry(add_frame)
        self.symbol_entry.grid(row=0, column=1, padx=5)
        
        tk.Label(add_frame, text="Shares:").grid(row=0, column=2)
        self.shares_entry = tk.Entry(add_frame)
        self.shares_entry.grid(row=0, column=3, padx=5)
        
        tk.Label(add_frame, text="Buy Price:").grid(row=0, column=4)
        self.price_entry = tk.Entry(add_frame)
        self.price_entry.grid(row=0, column=5, padx=5)
        
        add_btn = tk.Button(add_frame, text="Add Stock", command=self.add_stock)
        add_btn.grid(row=0, column=6, padx=10)
        
        # Frame for Portfolio Display
        tree_frame = tk.Frame(self.root)
        tree_frame.pack(pady=10, fill="both", expand=True)
        
        # Treeview (Table)
        self.tree = ttk.Treeview(tree_frame, columns=("Symbol", "Shares", "Buy Price", "Date"), show="headings")
        self.tree.heading("Symbol", text="Symbol")
        self.tree.heading("Shares", text="Shares")
        self.tree.heading("Buy Price", text="Buy Price")
        self.tree.heading("Date", text="Date Added")
        
        self.tree.pack(fill="both", expand=True)
        
        # Refresh and Remove Buttons
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)
        
        refresh_btn = tk.Button(btn_frame, text="Refresh Prices", command=self.refresh_prices)
        refresh_btn.pack(side="left", padx=5)
        
        remove_btn = tk.Button(btn_frame, text="Remove Selected", command=self.remove_stock)
        remove_btn.pack(side="left", padx=5)
        
        # Summary Label
        self.summary_label = tk.Label(self.root, text="", font=('Arial', 10))
        self.summary_label.pack(pady=10)
    
    def add_stock(self):
        symbol = self.symbol_entry.get().upper()
        shares = self.shares_entry.get()
        price = self.price_entry.get()
        
        if not (symbol and shares and price):
            messagebox.showerror("Error", "All fields are required!")
            return
        
        try:
            shares = float(shares)
            price = float(price)
            
            # Verify stock exists
            stock = yf.Ticker(symbol)
            if stock.history(period='1d').empty:
                messagebox.showerror("Error", f"Invalid stock symbol: {symbol}")
                return
            
            cursor = self.conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO stocks VALUES (?, ?, ?, ?)",
                         (symbol, shares, price, datetime.now().strftime('%Y-%m-%d')))
            self.conn.commit()
            
            self.tree.insert("", tk.END, values=(symbol, shares, price, datetime.now().strftime('%Y-%m-%d')))
            self.refresh_prices()
            
            self.symbol_entry.delete(0, tk.END)
            self.shares_entry.delete(0, tk.END)
            self.price_entry.delete(0, tk.END)
            
            messagebox.showinfo("Success", f"{symbol} added to portfolio!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add stock: {e}")
    
    def remove_stock(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a stock to remove")
            return
        
        symbol = self.tree.item(selected[0])['values'][0]
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM stocks WHERE symbol=?", (symbol,))
            self.conn.commit()
            self.tree.delete(selected[0])
            self.refresh_prices()
            messagebox.showinfo("Success", f"{symbol} removed from portfolio")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to remove stock: {e}")
    
    def refresh_prices(self):
        try:
            total_investment = 0
            total_current = 0
            
            for item in self.tree.get_children():
                symbol = self.tree.item(item)['values'][0]
                shares = float(self.tree.item(item)['values'][1])
                buy_price = float(self.tree.item(item)['values'][2])
                
                # Get current price
                stock = yf.Ticker(symbol)
                current_price = stock.history(period='1d')['Close'].iloc[-1]
                
                # Update values
                self.tree.item(item, values=(
                    symbol, 
                    shares, 
                    buy_price, 
                    self.tree.item(item)['values'][3],
                    f"${current_price:.2f}",
                    f"${shares * current_price:.2f}",
                    f"${(current_price - buy_price) * shares:.2f}",
                    f"{((current_price - buy_price)/buy_price)*100:.2f}%"
                ))
                
                total_investment += shares * buy_price
                total_current += shares * current_price
            
            # Update summary
            profit_loss = total_current - total_investment
            pct_change = (profit_loss / total_investment * 100) if total_investment > 0 else 0
            
            summary_text = (
                f"Total Invested: ${total_investment:.2f} | "
                f"Current Value: ${total_current:.2f} | "
                f"Profit/Loss: ${profit_loss:.2f} ({pct_change:.2f}%)"
            )
            self.summary_label.config(text=summary_text)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh prices: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = StockPortfolioApp(root)
    root.mainloop()