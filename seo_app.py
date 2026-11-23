import json
import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from openai import OpenAI


class SEOApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("دستیار سئو محصولات")
        self.geometry("900x720")
        self.minsize(650, 550)
        self.configure(padx=12, pady=12)
        self.build_ui()

    def build_ui(self):
        ttk.Label(self, text="کلید API").pack(anchor="e")

        api_row = ttk.Frame(self)
        api_row.pack(fill="x", pady=(2, 8))

        ttk.Button(
            api_row,
            text="Paste کلید",
            command=self.paste_api_key,
        ).pack(side="left")

        self.api_key_entry = ttk.Entry(api_row, show="*")
        self.api_key_entry.pack(side="right", fill="x", expand=True)
        self.api_key_entry.insert(0, os.getenv("OPENAI_API_KEY", ""))
        self.api_key_entry.bind("<Control-v>", self.paste_api_key)
        self.api_key_entry.bind("<Control-V>", self.paste_api_key)

        ttk.Label(self, text="آدرس پایه API").pack(anchor="e")

        self.base_url_entry = ttk.Entry(self)
        self.base_url_entry.insert(0, "https://api.1xai.ir/v1")
        self.base_url_entry.pack(fill="x", pady=(2, 8))

        ttk.Label(self, text="لینک صفحه محصول").pack(anchor="e")

        url_row = ttk.Frame(self)
        url_row.pack(fill="x", pady=(2, 8))

        ttk.Button(
            url_row,
            text="Paste لینک",
            command=self.paste_url,
        ).pack(side="left")

        ttk.Button(
            url_row,
            text="خواندن صفحه",
            command=self.read_page,
        ).pack(side="left", padx=(6, 0))

        self.url_entry = ttk.Entry(url_row)
        self.url_entry.pack(side="right", fill="x", expand=True)
        self.url_entry.bind("<Control-v>", self.paste_url)
        self.url_entry.bind("<Control-V>", self.paste_url)
        self.url_entry.bind("<Return>", lambda event: self.read_page())

        ttk.Label(self, text="نام محصول").pack(anchor="e")

        self.name_entry = ttk.Entry(self)
        self.name_entry.pack(fill="x", pady=(2, 8))

        ttk.Label(self, text="توضیحات محصول").pack(anchor="e")

        self.description_text = tk.Text(
            self,
            height=7,
            wrap="word",
            font=("Tahoma", 10),
        )
        self.description_text.pack(fill="x", pady=(2, 8))

        self.generate_button = ttk.Button(
            self,
            text="تولید محتوای سئو",
            command=self.generate_seo,
        )
        self.generate_button.pack(pady=6)

        ttk.Label(self, text="نتیجه").pack(anchor="e")

        self.output_text = tk.Text(
            self,
            height=14,
            wrap="word",
            font=("Tahoma", 10),
        )
        self.output_text.pack(fill="both", expand=True, pady=(2, 6))

        self.status_label = ttk.Label(self, text="آماده")
        self.status_label.pack(anchor="e")

    def paste_api_key(self, event=None):
        try:
            text = self.clipboard_get().strip()
            self.api_key_entry.delete(0, "end")
            self.api_key_entry.insert(0, text)
            self.status_label.config(text="کلید وارد شد")
        except tk.TclError:
            messagebox.showwarning(
                "کلیپ‌بورد",
                "کلید در کلیپ‌بورد پیدا نشد.",
            )
        return "break"

    def paste_url(self, event=None):
        try:
            text = self.clipboard_get().strip()
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, text)
            self.status_label.config(text="لینک وارد شد")
        except tk.TclError:
            messagebox.showwarning(
                "کلیپ‌بورد",
                "لینک در کلیپ‌بورد پیدا نشد.",
            )
        return "break"

    def read_page(self):
        url = self.url_entry.get().strip()
        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            messagebox.showerror(
                "لینک نامعتبر",
                "لینک کامل صفحهٔ محصول را وارد کنید.",
            )
            return

        self.status_label.config(text="در حال خواندن صفحه...")
        threading.Thread(
            target=self.read_page_worker,
            args=(url,),
            daemon=True,
        ).start()

    def read_page_worker(self, url):
        try:
            response = requests.get(
                url,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=20,
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            title = ""
            og_title = soup.find("meta", property="og:title")
            if og_title and og_title.get("content"):
                title = og_title["content"].strip()

            if not title and soup.title:
                title = soup.title.get_text(" ", strip=True)

            description = ""
            for attributes in (
                {"name": "description"},
                {"property": "og:description"},
            ):
                meta = soup.find("meta", attrs=attributes)
                if meta and meta.get("content"):
                    description = meta["content"].strip()
                    break

            for element in soup(["script", "style", "noscript", "svg"]):
                element.decompose()

            page_text = " ".join(
                soup.get_text(" ", strip=True).split()
            )[:3000]

            self.after(
                0,
                self.fill_page_fields,
                title,
                description,
                page_text,
            )
        except Exception as error:
            self.after(0, self.show_read_error, str(error))

    def fill_page_fields(self, title, description, page_text):
        if title:
            self.name_entry.delete(0, "end")
            self.name_entry.insert(0, title)

        content = []
        if description:
            content.append("توضیحات صفحه:\n" + description)
        if page_text:
            content.append("متن صفحه:\n" + page_text)

        self.description_text.delete("1.0", "end")
        self.description_text.insert("1.0", "\n\n".join(content))
        self.status_label.config(text="اطلاعات صفحه وارد شد")

    def show_read_error(self, error):
        self.status_label.config(text="خواندن صفحه ناموفق بود")
        messagebox.showerror(
            "خطا در خواندن صفحه",
            "صفحه خوانده نشد:\n"
            + error
            + "\n\n"
            "صفحه‌های نیازمند ورود یا محتوای کاملاً JavaScript "
            "ممکن است قابل خواندن نباشند.",
        )

    def generate_seo(self):
        api_key = self.api_key_entry.get().strip()
        base_url = self.base_url_entry.get().strip()
        name = self.name_entry.get().strip()
        description = self.description_text.get("1.0", "end").strip()

        if not api_key:
            messagebox.showerror("کلید API", "کلید API را وارد کنید.")
            return

        if not name:
            messagebox.showerror("نام محصول", "نام محصول را وارد کنید.")
            return

        self.generate_button.config(state="disabled")
        self.status_label.config(text="در حال تولید محتوا...")

        threading.Thread(
            target=self.generate_worker,
            args=(api_key, base_url, name, description),
            daemon=True,
        ).start()

    def generate_worker(self, api_key, base_url, name, description):
        try:
            client = OpenAI(
                api_key=api_key,
                base_url=base_url,
            )

            prompt = f"""
برای محصول زیر یک بسته کامل سئو به زبان فارسی بساز.

نام محصول:
{name}

توضیحات و متن محصول:
{description}

فقط JSON معتبر برگردان.
کلیدهای JSON دقیقاً این‌ها باشند:
- title: عنوان جذاب، بهتر است 40 تا 60 کاراکتر باشد
- description: توضیحات متا، بهتر است 120 تا 150 کاراکتر باشد
- keywords: آرایه‌ای شامل 3 تا 5 کلمه کلیدی مرتبط
- image_alt: متن جایگزین کوتاه و توصیفی تصویر
- short_copy: متن معرفی کوتاه و جذاب محصول

برای ویژگی‌هایی که در متن نیستند حدس نزن.
"""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                response_format={"type": "json_object"},
            )

            result = json.loads(response.choices[0].message.content)
            formatted = json.dumps(
                result,
                ensure_ascii=False,
                indent=2,
            )
            self.after(0, self.show_result, formatted)

        except Exception as error:
            self.after(0, self.show_generation_error, str(error))

    def show_result(self, result):
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", result)
        self.generate_button.config(state="normal")
        self.status_label.config(text="تولید محتوا انجام شد")

    def show_generation_error(self, error):
        self.generate_button.config(state="normal")
        self.status_label.config(text="تولید ناموفق بود")
        messagebox.showerror(
            "خطا در تولید محتوا",
            str(error),
        )


if __name__ == "__main__":
    app = SEOApp()
    app.mainloop()
