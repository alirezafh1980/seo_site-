import customtkinter as ctk
from tkinter import messagebox
from openai import OpenAI
import threading
import json

# ==========================================
# ۱. تنظیمات ظاهری
# ==========================================
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

# ==========================================
# ۲. تنظیمات API
# ==========================================
client = OpenAI(
    api_key=1xai-YUCRNuvScvYOWRto5GW_ej9FKDBdKDhOTm7pTVNwl64
    base_url="https://api.1xai.ir/v1"
)

# ==========================================
# ۳. کلاس اصلی برنامه
# ==========================================
class SEOApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("دستیار سئوی کارگاه نجاری")
        self.geometry("900x700")

        # --- بخش چپ: ورودی‌ها ---
        self.frame_left = ctk.CTkFrame(self, width=350, corner_radius=0)
        self.frame_left.pack(side="left", fill="y", padx=10, pady=10)

        self.label_title = ctk.CTkLabel(self.frame_left, text="اطلاعات محصول", font=("Tahoma", 20, "bold"))
        self.label_title.pack(pady=(20, 10))

        self.label_name = ctk.CTkLabel(self.frame_left, text="نام محصول:", font=("Tahoma", 14))
        self.label_name.pack(anchor="e", padx=20)
        self.entry_name = ctk.CTkEntry(self.frame_left, placeholder_text="مثلا: کاسه چوبی دست‌ساز", font=("Tahoma", 14), justify="right")
        self.entry_name.pack(pady=(0, 10), padx=20, fill="x")

        self.label_desc = ctk.CTkLabel(self.frame_left, text="توضیحات فنی (اختیاری):", font=("Tahoma", 14))
        self.label_desc.pack(anchor="e", padx=20)
        self.textbox_desc = ctk.CTkTextbox(self.frame_left, height=100, font=("Tahoma", 14))
        self.textbox_desc.pack(pady=(0, 10), padx=20, fill="x")

        self.btn_generate = ctk.CTkButton(self.frame_left, text="  تولید محتوای سئو", font=("Tahoma", 16, "bold"), 
                                          command=self.start_generation, height=50, fg_color="#2fa572", hover_color="#106a43")
        self.btn_generate.pack(pady=20, padx=20, fill="x")

        self.label_status = ctk.CTkLabel(self.frame_left, text="", font=("Tahoma", 12), text_color="gray")
        self.label_status.pack(pady=5)

        # --- بخش راست: خروجی‌ها ---
        self.frame_right = ctk.CTkFrame(self, corner_radius=0)
        self.frame_right.pack(side="right", fill="both", expand=True, padx=(0, 10), pady=10)

        self.label_out_title = ctk.CTkLabel(self.frame_right, text="خروجی سئو", font=("Tahoma", 20, "bold"))
        self.label_out_title.pack(pady=(20, 10))

        self.outputs = {}
        fields = [
            ("title", "عنوان (Title):"),
            ("description", "توضیحات متا (Description):"),
            ("keywords", "کلمات کلیدی (Keywords):"),
            ("image_alt", "متن جایگزین تصویر (Image Alt):"),
            ("short_copy", "متن معرفی کوتاه:")
        ]

        for key, label_text in fields:
            lbl = ctk.CTkLabel(self.frame_right, text=label_text, font=("Tahoma", 14, "bold"))
            lbl.pack(anchor="e", padx=20, pady=(5, 0))
            
            txt = ctk.CTkTextbox(self.frame_right, height=60, font=("Tahoma", 14))
            txt.pack(padx=20, pady=(0, 10), fill="x")
            self.outputs[key] = txt

    def start_generation(self):
        name = self.entry_name.get().strip()
        if not name:
            # پیام خطا رو انگلیسی گذاشتیم که کرش نکنه
            messagebox.showwarning("Error", "Please enter product name.")
            return
        
        for txt in self.outputs.values():
            txt.delete("1.0", "end")

        self.btn_generate.configure(state="disabled", text="در حال پردازش...")
        self.label_status.configure(text="در حال ارتباط با هوش مصنوعی...", text_color="orange")

        threading.Thread(target=self.generate_content, args=(name,), daemon=True).start()

    def generate_content(self, name):
        desc = self.textbox_desc.get("1.0", "end").strip()
        
        prompt = f"""
        تو یک متخصص ارشد سئو و کپی‌رایتر حرفه‌ای برای یک فروشگاه اینترنتی محصولات چوبی دست‌ساز در ایران هستی.
        برای محصول زیر، یک "بسته کامل سئو" تولید کن.

        نام محصول: {name}
        توضیحات فنی: {desc if desc else "ندارد"}

        قوانین خروجی (بسیار مهم):
        عنوان (Title): بین ۴۰ تا ۶۰ کاراکتر، کلمه کلیدی اصلی در ابتدا.
        توضیحات (Meta Description): بین ۱۲۰ تا ۱۵۰ کاراکتر، شامل دعوت به اقدام.
        کلمات کلیدی (Keywords): ۳ تا ۵ کلمه کلیدی.
        متن جایگزین تصویر (Image Alt): یک جمله کوتاه و توصیفی.
        متن کوتاه معرفی (Short Copy): یک پاراگراف ۲ خطی جذاب.

        خروجی را دقیقاً به فرمت JSON زیر برگردان:
        {{
            "title": "عنوان",
            "description": "توضیحات",
            "keywords": "کلمه۱, کلمه۲",
            "image_alt": "متن تصویر",
            "short_copy": "متن معرفی"
        }}
        """

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                response_format={ "type": "json_object" }
            )
            result = json.loads(response.choices[0].message.content)
            self.after(0, self.update_ui_success, result)
            
        except Exception as e:
            # تبدیل خطا به رشته انگلیسی برای جلوگیری از کرش
            self.after(0, self.update_ui_error, str(e))

    def update_ui_success(self, result):
        for key, txt_box in self.outputs.items():
            value = result.get(key, "")
            txt_box.insert("1.0", value)
        
        self.btn_generate.configure(state="normal", text="  تولید محتوای سئو")
        self.label_status.configure(text="  با موفقیت تولید شد!", text_color="green")

    def update_ui_error(self, error_msg):
        # پیام خطا رو انگلیسی نشون می‌دیم تا کرش نکنه
        messagebox.showerror("API Error", f"An error occurred:\n{error_msg}")
        self.btn_generate.configure(state="normal", text="  تولید محتوای سئو")
        self.label_status.configure(text="  خطا در تولید", text_color="red")


if __name__ == "__main__":
    app = SEOApp()
    app.mainloop()

