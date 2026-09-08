import customtkinter as ctk
import tkinter as tk
import requests
import threading
import time
import sys
import pywinstyles

# تنظیم تم تاریک برای کل برنامه
ctk.set_appearance_mode("dark")

class CryptoLiveWidget:
    def __init__(self, root):
        self.root = root
        self.root.title("Crypto Live Widget")
        
        # حذف نوار عنوان و قرار دادن پنجره روی تمام برنامه‌ها
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", False)
        self.root.lower()  # این دستور ویجت را مستقیماً به پایین‌ترین لایه (روی دسکتاپ) می‌فرستد
        self.root.geometry("220x100+200+200")

        # ایجاد پس‌زمینه با افکت شیشه‌ای براق و تار (مخصوص ویندوز)
        self.root.configure(fg_color="#050505") # پایه مشکی عمیق تیتانیومی
        pywinstyles.apply_style(self.root, "acrylic") # افکت براق اکریلیک
        
        self.current_coin = "usdt"
        self.last_price = 0
        self.running = True

        # --- طراحی رابط کاربری ---
        self.title_label = ctk.CTkLabel(root, text="USDT / TOMAN", font=("Arial", 12, "bold"), text_color="#9da0a8")
        self.title_label.pack(pady=(10, 0))

        self.price_label = ctk.CTkLabel(root, text="Fetching...", font=("Arial", 22, "bold"), text_color="#ffffff")
        self.price_label.pack()

        self.change_label = ctk.CTkLabel(root, text="% 0.00", font=("Arial", 11), text_color="#9da0a8")
        self.change_label.pack(pady=(0, 5))

        # بایند کردن کلیک و درگ به تمام اجزای پنجره تا همه‌جا قابل گرفتن باشد
        widgets = [self.root, self.title_label, self.price_label, self.change_label]
        for w in widgets:
            w.bind("<ButtonPress-1>", self.start_move)
            w.bind("<ButtonRelease-1>", self.stop_move)
            w.bind("<B1-Motion>", self.do_move)
            w.bind("<Button-3>", self.show_context_menu)

        # --- ساخت منوی کلیک راست ---
        self.context_menu = tk.Menu(self.root, tearoff=0, bg="#2b2b2b", fg="white", activebackground="#4a4a4a")
        
        # بخش انتخاب ارز
        self.coin_menu = tk.Menu(self.context_menu, tearoff=0, bg="#2b2b2b", fg="white")
        self.coin_menu.add_command(label="Tether (USDT)", command=lambda: self.change_coin("usdt", "USDT"))
        self.coin_menu.add_command(label="Bitcoin (BTC)", command=lambda: self.change_coin("btc", "BTC"))
        self.coin_menu.add_command(label="Ethereum (ETH)", command=lambda: self.change_coin("eth", "ETH"))
        self.context_menu.add_cascade(label="Change Currency", menu=self.coin_menu)
        
        self.context_menu.add_separator()
        
        # بخش تنظیم شفافیت شیشه
        self.opacity_menu = tk.Menu(self.context_menu, tearoff=0, bg="#2b2b2b", fg="white")
        self.opacity_menu.add_command(label="100%", command=lambda: self.root.attributes("-alpha", 1.0))
        self.opacity_menu.add_command(label="85%", command=lambda: self.root.attributes("-alpha", 0.85))
        self.opacity_menu.add_command(label="50%", command=lambda: self.root.attributes("-alpha", 0.5))
        self.context_menu.add_cascade(label="Opacity", menu=self.opacity_menu)
        
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Exit", command=self.close_app)

        # اجرای Thread پس‌زمینه برای گرفتن قیمت‌ها
        self.fetch_thread = threading.Thread(target=self.fetch_price, daemon=True)
        self.fetch_thread.start()

    # --- توابع مربوط به درگ کردن (جابه‌جایی) پنجره ---
    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def stop_move(self, event):
        self.x = None
        self.y = None

    def do_move(self, event):
        x = self.root.winfo_x() + (event.x - self.x)
        y = self.root.winfo_y() + (event.y - self.y)
        self.root.geometry(f"+{x}+{y}")

    # --- توابع مربوط به منو و عملیات رابط کاربری ---
    def show_context_menu(self, event):
        self.context_menu.tk_popup(event.x_root, event.y_root)

    def change_coin(self, coin_code, coin_name):
        self.current_coin = coin_code
        self.title_label.configure(text=f"{coin_name} / TOMAN")
        self.price_label.configure(text="Loading...", text_color="#ffffff")
        self.last_price = 0 

    def close_app(self):
        self.running = False
        self.root.destroy()
        sys.exit(0)

    # --- موتور دریافت اطلاعات (API والکس + دور زدن کش سرور) ---
    def fetch_price(self):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        }
        
        wallex_symbols = {
            "usdt": "USDTTMN",
            "btc": "BTCTMN",
            "eth": "ETHTMN"
        }
        
        while self.running:
            try:
                # اضافه کردن زمان فعلی به URL برای جلوگیری از دریافت اطلاعات تکراری
                current_time = int(time.time())
                url = f"https://api.wallex.ir/v1/markets?t={current_time}"
                
                response = requests.get(url, headers=headers, timeout=7)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("success") == True:
                        target_symbol = wallex_symbols[self.current_coin]
                        stats = data["result"]["symbols"][target_symbol]["stats"]
                        
                        toman_price = int(float(stats["lastPrice"]))
                        day_change = round(float(stats["24h_ch"]), 2)
                        
                        # انتقال دستور آپدیت UI به Thread اصلی
                        self.root.after(0, self.update_ui, toman_price, day_change)
                elif response.status_code == 403:
                    self.root.after(0, self.update_error, "IP Blocked!")
                else:
                    self.root.after(0, self.update_error, f"HTTP {response.status_code}")
                    
            except requests.exceptions.RequestException:
                self.root.after(0, self.update_error, "No Internet")
            except Exception:
                self.root.after(0, self.update_error, "API Error")
            
            # وقفه ۳ ثانیه‌ای
            time.sleep(3)

    # --- توابع آپدیت کننده رابط کاربری ---
    def update_error(self, error_msg):
        self.price_label.configure(text=error_msg, text_color="#ff4444")

    def update_ui(self, new_price, day_change):
        # بررسی صعودی یا نزولی بودن قیمت
        if self.last_price != 0:
            if new_price > self.last_price:
                self.price_label.configure(text_color="#00ff88") # روند صعودی -> سبز
            elif new_price < self.last_price:
                self.price_label.configure(text_color="#ff4444") # روند نزولی -> قرمز
        
        self.last_price = new_price
        
        # جدا کردن اعداد با کاما (هزارگان)
        formatted_price = f"{new_price:,} T"
        self.price_label.configure(text=formatted_price)
        
        change_sign = "+" if day_change > 0 else ""
        self.change_label.configure(text=f"% {change_sign}{day_change}")

if __name__ == "__main__":
    root = ctk.CTk()
    app = CryptoLiveWidget(root)
    root.mainloop()
