import os
import threading
from urllib.parse import urlparse
from tkinter import messagebox, filedialog

import customtkinter as ctk
import requests
from bs4 import BeautifulSoup
from openai import OpenAI


ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")


class SEOApp(ctk.CTk):
    """Persian product-page SEO checker and content-planning assistant."""

    def __init__(self):
        super().__init__()
        self.title("دستیار بررسی و رشد سئو")
        self.geometry("1120x850")
        self.minsize(850, 650)
        self.page_data = None
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            self,
            text="دستیار بررسی و رشد سئوی فروشگاه",
            font=("Tahoma", 22, "bold"),
        ).grid(row=0, column=0, padx=16, pady=(14, 8), sticky="e")

        body = ctk.CTkFrame(self)
        body.grid(row=1, column=0, padx=14, pady=8, sticky="nsew")
        body.grid_columnconfigure((0, 1), weight=1)
        body.grid_rowconfigure(1, weight=1)

        settings = ctk.CTkFrame(body)
        settings.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        settings.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(settings, text="کلید API:", font=("Tahoma", 13)).grid(
            row=0, column=2, padx=8, pady=7, sticky="e"
        )
        self.api_key_entry = ctk.CTkEntry(
            settings, show="*", placeholder_text="کلید را وارد یا Paste کنید"
        )
        self.api_key_entry.grid(row=0, column=1, padx=6, pady=7, sticky="ew")
        env_key = os.getenv("OPENAI_API_KEY", "")
        if env_key:
            self.api_key_entry.insert(0, env_key)
        self.api_key_entry.bind("<Control-v>", self._paste_api_key)
        self.api_key_entry.bind("<Control-V>", self._paste_api_key)
        ctk.CTkButton(settings, text="Paste", width=72, command=self._paste_api_key).grid(
            row=0, column=0, padx=6, pady=7
        )

        ctk.CTkLabel(settings, text="آدرس پایه API:", font=("Tahoma", 13)).grid(
            row=1, column=2, padx=8, pady=7, sticky="e"
        )
        self.base_url_entry = ctk.CTkEntry(settings)
        self.base_url_entry.insert(0, "https://api.1xai.ir/v1")
        self.base_url_entry.grid(row=1, column=1, padx=6, pady=7, sticky="ew")
        ctk.CTkLabel(settings, text="مدل:", font=("Tahoma", 13)).grid(
            row=1, column=0, padx=8, pady=7, sticky="e"
        )
        self.model_entry = ctk.CTkEntry(settings, width=170)
        self.model_entry.insert(0, "gpt-4o-mini")
        self.model_entry.grid(row=1, column=0, padx=(100, 6), pady=7, sticky="w")

        ctk.CTkLabel(settings, text="لینک صفحه محصول:", font=("Tahoma", 13)).grid(
            row=2, column=2, padx=8, pady=7, sticky="e"
        )
        self.url_entry = ctk.CTkEntry(
            settings, placeholder_text="https://example.com/product"
        )
        self.url_entry.grid(row=2, column=1, padx=6, pady=7, sticky="ew")
        self.url_entry.bind("<Control-v>", self._paste_url)
        self.url_entry.bind("<Control-V>", self._paste_url)
        ctk.CTkButton(settings, text="Paste لینک", width=90, command=self._paste_url).grid(
            row=2, column=0, padx=6, pady=7
        )

        self.audit_button = ctk.CTkButton(
            settings, text="خواندن و بررسی صفحه", command=self.audit_page
        )
        self.audit_button.grid(row=3, column=1, padx=6, pady=8, sticky="e")

        left = ctk.CTkFrame(body)
        left.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(3, weight=1)
        ctk.CTkLabel(left, text="اطلاعات محصول", font=("Tahoma", 17, "bold")).grid(
            row=0, column=0, padx=10, pady=10, sticky="e"
        )
        self.product_entry = ctk.CTkEntry(
            left, placeholder_text="نام محصول و نوع آن را وارد کنید", justify="right"
        )
        self.product_entry.grid(row=1, column=0, padx=10, pady=6, sticky="ew")
        ctk.CTkLabel(
            left,
            text="مشخصات واقعی محصول را تکمیل کنید (جنس، ابعاد، کاربرد، روش نگهداری و ...).",
            font=("Tahoma", 11),
            wraplength=480,
        ).grid(row=2, column=0, padx=10, pady=4, sticky="e")
        self.facts_box = ctk.CTkTextbox(left, height=180, font=("Tahoma", 12))
        self.facts_box.grid(row=3, column=0, padx=10, pady=6, sticky="nsew")
        ctk.CTkLabel(left, text="گزارش فنی صفحه", font=("Tahoma", 15, "bold")).grid(
            row=4, column=0, padx=10, pady=(10, 4), sticky="e"
        )
        self.audit_box = ctk.CTkTextbox(left, height=190, font=("Tahoma", 11))
        self.audit_box.grid(row=5, column=0, padx=10, pady=(4, 10), sticky="ew")

        right = ctk.CTkFrame(body)
        right.grid(row=1, column=1, padx=10, pady=(0, 10), sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(right, text="تحلیل و برنامه رشد سئو", font=("Tahoma", 17, "bold")).grid(
            row=0, column=0, padx=10, pady=10, sticky="e"
        )
        self.result_box = ctk.CTkTextbox(right, font=("Tahoma", 12), wrap="word")
        self.result_box.grid(row=1, column=0, padx=10, pady=6, sticky="nsew")
        actions = ctk.CTkFrame(right, fg_color="transparent")
        actions.grid(row=2, column=0, padx=10, pady=8, sticky="ew")
        self.generate_button = ctk.CTkButton(
            actions, text="تحلیل و نوشتن پیشنهادها", command=self.generate_plan, height=42
        )
        self.generate_button.pack(side="right", padx=5)
        ctk.CTkButton(actions, text="ذخیره گزارش", command=self.save_report, height=42).pack(
            side="left", padx=5
        )

        self.status_label = ctk.CTkLabel(self, text="آماده", font=("Tahoma", 11))
        self.status_label.grid(row=2, column=0, padx=16, pady=(0, 10), sticky="e")

    def _paste(self, entry):
        try:
            entry.delete(0, "end")
            entry.insert(0, self.clipboard_get().strip())
            self.status_label.configure(text="متن از کلیپ‌بورد وارد شد")
        except Exception:
            messagebox.showwarning("کلیپ‌بورد", "متنی در کلیپ‌بورد پیدا نشد.")
        return "break"

    def _paste_api_key(self, _event=None):
        return self._paste(self.api_key_entry)

    def _paste_url(self, _event=None):
        return self._paste(self.url_entry)

    @staticmethod
    def _meta(soup, name):
        tag = soup.find("meta", attrs={"name": name})
        return tag.get("content", "").strip() if tag else ""

    def audit_page(self):
        url = self.url_entry.get().strip()
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            messagebox.showerror(
                "لینک نامعتبر", "لطفاً لینک کامل صفحه با http یا https وارد کنید."
            )
            return
        self.audit_button.configure(state="disabled")
        self.status_label.configure(text="در حال دریافت و بررسی صفحه...")
        threading.Thread(target=self._fetch_page, args=(url,), daemon=True).start()

    def _fetch_page(self, url):
        try:
            response = requests.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; SEOAssistant/1.0)"},
                timeout=25,
            )
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            soup = BeautifulSoup(response.text, "html.parser")
            title = soup.title.get_text(" ", strip=True) if soup.title else ""
            description = self._meta(soup, "description")
            robots = self._meta(soup, "robots")
            canonical_tag = soup.find("link", rel="canonical")
            canonical = canonical_tag.get("href", "").strip() if canonical_tag else ""
            headings = {
                tag: [h.get_text(" ", strip=True) for h in soup.find_all(tag)
                      if h.get_text(" ", strip=True)]
                for tag in ("h1", "h2", "h3")
            }
            images = soup.find_all("img")
            missing_alt = [
                img.get("src", "(بدون آدرس)")
                for img in images
                if not img.get("alt", "").strip()
            ]
            for node in soup(["script", "style", "noscript", "svg"]):
                node.decompose()
            root = soup.find("main") or soup.find("article") or soup.body or soup
            text = " ".join(root.get_text(" ", strip=True).split())[:10000]
            data = {
                "url": url,
                "title": title,
                "description": description,
                "robots": robots,
                "canonical": canonical,
                "headings": headings,
                "image_count": len(images),
                "missing_alt": missing_alt,
                "text": text,
                "http_status": response.status_code,
                "final_url": response.url,
            }
            data["audit"] = self._make_audit(data)
            self.after(0, self._show_audit, data)
        except Exception as exc:
            self.after(0, self._fetch_error, str(exc))

    @staticmethod
    def _make_audit(data):
        h1 = data["headings"]["h1"]
        h2 = data["headings"]["h2"]
        words = len(data["text"].split())
        issues, positives = [], []
        title = data["title"]
        desc = data["description"]

        if not title:
            issues.append("Title پیدا نشد؛ عنوان یکتا و توصیفی برای صفحه تنظیم کنید.")
        else:
            positives.append(f"Title موجود است ({len(title)} کاراکتر).")
            if len(title) < 30 or len(title) > 65:
                issues.append(
                    "طول Title را از نظر وضوح و نمایش مناسب بازبینی کنید؛ طول به‌تنهایی معیار رتبه نیست."
                )
        if not desc:
            issues.append("Meta description پیدا نشد؛ خلاصه‌ای دقیق و ترغیب‌کننده بنویسید.")
        else:
            positives.append(f"Meta description موجود است ({len(desc)} کاراکتر).")
        if len(h1) == 0:
            issues.append("H1 پیدا نشد؛ موضوع اصلی صفحه را با یک عنوان روشن مشخص کنید.")
        elif len(h1) > 1:
            issues.append(f"{len(h1)} عدد H1 پیدا شد؛ سلسله‌مراتب عنوان‌ها را بازبینی کنید.")
        else:
            positives.append("یک H1 پیدا شد.")
        if not h2:
            issues.append("H2 پیدا نشد؛ محتوای صفحه را با بخش‌های کاربردی مرتب کنید.")
        if data["image_count"] and data["missing_alt"]:
            issues.append(f"{len(data['missing_alt'])} تصویر Alt خالی یا ناموجود دارد.")
        if not data["canonical"]:
            issues.append("Canonical پیدا نشد؛ آدرس اصلی صفحه را در CMS بررسی کنید.")
        if data["robots"] and "noindex" in data["robots"].lower():
            issues.append("متای robots شامل noindex است؛ اگر عمدی نیست، ایندکس‌پذیری را بررسی کنید.")
        if words < 100:
            issues.append(
                f"فقط حدود {words} واژهٔ قابل‌استخراج پیدا شد؛ بررسی کنید محتوای اصلی در HTML موجود باشد."
            )
        else:
            positives.append(f"حدود {words} واژه متن قابل‌استخراج وجود دارد.")

        positive_lines = (
            [f"✓ {item}" for item in positives]
            if positives
            else ["موردی تشخیص داده نشد."]
        )
        issue_lines = (
            [f"• {item}" for item in issues]
            if issues
            else ["مورد مهمی در بررسی اولیه تشخیص داده نشد."]
        )

        lines = [
            "گزارش فنی اولیه (نه جایگزین Search Console یا بررسی رتبه)",
            f"وضعیت HTTP: {data['http_status']} | آدرس نهایی: {data['final_url']}",
            f"Title: {title or 'پیدا نشد'}",
            f"Meta description: {desc or 'پیدا نشد'}",
            f"H1: {' | '.join(h1) or 'پیدا نشد'}",
            f"تعداد H2: {len(h2)} | تصاویر: {data['image_count']} | تصاویر بدون Alt: {len(data['missing_alt'])}",
            f"Canonical: {data['canonical'] or 'پیدا نشد'} | Robots: {data['robots'] or 'مشخص نشده'}",
            "",
            "موارد مناسب:",
        ]
        lines.extend(positive_lines)
        lines.extend(["", "موارد قابل بررسی:"])
        lines.extend(issue_lines)
        lines.extend([
            "",
            "این برنامه به آمار سرچ کنسول، رتبه، سرعت واقعی، لینک‌های ورودی یا صفحات رقبا دسترسی ندارد.",
        ])
        return "\n".join(lines)

    def _show_audit(self, data):
        self.page_data = data
        if not self.product_entry.get().strip():
            h1 = data["headings"]["h1"]
            guess = h1[0] if h1 else data["title"]
            if guess:
                self.product_entry.insert(0, guess)
        if not self.facts_box.get("1.0", "end").strip():
            self.facts_box.insert("1.0", data["text"][:5000])
        self.audit_box.delete("1.0", "end")
        self.audit_box.insert("1.0", data["audit"])
        self.audit_button.configure(state="normal")
        self.status_label.configure(text="بررسی صفحه انجام شد؛ مشخصات واقعی محصول را تکمیل کنید.")

    def _fetch_error(self, error):
        self.audit_button.configure(state="normal")
        self.status_label.configure(text="خواندن صفحه ناموفق بود")
        messagebox.showerror(
            "خطا در خواندن صفحه",
            f"صفحه دریافت نشد:\n{error}\n\nممکن است سایت دسترسی خودکار را محدود کند یا محتوا با JavaScript بارگذاری شود.",
        )

    def generate_plan(self):
        if not self.page_data:
            messagebox.showwarning("ابتدا صفحه را بررسی کنید", "ابتدا لینک را بررسی کنید.")
            return
        api_key = self.api_key_entry.get().strip()
        if not api_key:
            messagebox.showerror("کلید API", "کلید API را در کادر وارد یا Paste کنید.")
            return
        model = self.model_entry.get().strip()
        if not model:
            messagebox.showerror("مدل", "نام مدل را وارد کنید.")
            return
        base_url = self.base_url_entry.get().strip()
        product = self.product_entry.get().strip()
        facts = self.facts_box.get("1.0", "end").strip()
        self.generate_button.configure(state="disabled", text="در حال تحلیل...")
        self.status_label.configure(text="در حال ارسال درخواست و تهیه برنامه سئو...")
        threading.Thread(
            target=self._generate,
            args=(api_key, base_url, model, product, facts, self.page_data.copy()),
            daemon=True,
        ).start()

    def _generate(self, api_key, base_url, model, product, facts, page):
        try:
            client = OpenAI(api_key=api_key, base_url=base_url or None)
            heading_summary = "\n".join(
                f"{tag.upper()}: {' | '.join(values)}"
                for tag, values in page["headings"].items()
            )
            prompt = f"""
تو مشاور سئوی فروشگاه اینترنتی فارسی و نویسنده محتوای محصول هستی. بر اساس داده‌های واقعی زیر راهکار و متن کاربردی بده. درباره ویژگی، جنس، ابعاد، موجودی، قیمت، ارسال، گارانتی یا مزیتی که در داده‌ها نیست چیزی نساز؛ به‌جای آن [اطلاعات لازم از فروشنده] بنویس. رتبه‌گرفتن یا افزایش فروش را تضمین نکن. کلمات کلیدی را فرضیه بدان، چون حجم جستجو و سرچ کنسول در اختیارت نیست.

آدرس: {page['url']}
نام محصول: {product}
Title فعلی: {page['title']}
Meta فعلی: {page['description']}
عنوان‌های صفحه:
{heading_summary}
گزارش فنی:
{page['audit']}
متن و مشخصات داده‌شده:
{facts[:9000]}

پاسخ را فارسی و با همین بخش‌ها ارائه کن:
1. جمع‌بندی وضعیت و محدودیت تحلیل
2. پنج اقدام اولویت‌دار؛ برای هرکدام مشکل، اقدام دقیق، اهمیت و روش ارزیابی نتیجه
3. نیت جستجوی محتمل و مخاطب، با ذکر موارد نامطمئن
4. یک عبارت کلیدی اصلی و 5 تا 8 عبارت فرعی/پرسشی به‌عنوان فرضیه برای اعتبارسنجی در Search Console یا ابزار کلمات کلیدی
5. سه گزینه Title و دو Meta description پیشنهادی؛ وعده یا ویژگی اثبات‌نشده نداشته باشند
6. ساختار پیشنهادی H1/H2/H3 متناسب با صفحه محصول
7. متن پیشنهادی صفحه شامل معرفی، مشخصات، کاربرد، نگهداری و CTA؛ فقط اطلاعات تاییدشده را قطعی بنویس و جاهای خالی را علامت بزن
8. پنج FAQ؛ پاسخِ نیازمند اطلاعات ناموجود را با [اطلاعات لازم از فروشنده] مشخص کن
9. پیشنهاد لینک داخلی به نوع صفحه‌ها/دسته‌های مرتبط، بدون ساختن URL
10. چک‌لیست انتشار و سنجش در 2 تا 4 هفته بعد

از توصیه‌های عمومی و تکرار بی‌دلیل کلیدواژه پرهیز کن. اگر صفحه فروش محصول است، متن را برای کمک به تصمیم خرید و پاسخ‌گویی به سؤال واقعی مشتری بنویس.
"""
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
            )
            answer = response.choices[0].message.content or "پاسخی دریافت نشد."
            self.after(0, self._show_result, page["audit"] + "\n\n" + answer)
        except Exception as exc:
            self.after(0, self._generation_error, str(exc))

    def _show_result(self, result):
        self.result_box.delete("1.0", "end")
        self.result_box.insert("1.0", result)
        self.generate_button.configure(state="normal", text="تحلیل و نوشتن پیشنهادها")
        self.status_label.configure(text="تحلیل و پیشنهاد محتوا آماده شد")

    def _generation_error(self, error):
        self.generate_button.configure(state="normal", text="تحلیل و نوشتن پیشنهادها")
        self.status_label.configure(text="درخواست API ناموفق بود")
        messagebox.showerror("خطا در API", error)

    def save_report(self):
        content = "\n\n".join(
            value
            for value in (
                self.audit_box.get("1.0", "end").strip(),
                self.result_box.get("1.0", "end").strip(),
            )
            if value
        )
        if not content:
            messagebox.showinfo("گزارش خالی است", "ابتدا صفحه را بررسی کنید.")
            return
        path = filedialog.asksaveasfilename(
            title="ذخیره گزارش سئو",
            defaultextension=".txt",
            filetypes=[("فایل متنی", "*.txt"), ("همه فایل‌ها", "*.*")],
        )
        if path:
            try:
                with open(path, "w", encoding="utf-8") as file:
                    file.write(content)
                self.status_label.configure(text="گزارش ذخیره شد")
            except OSError as exc:
                messagebox.showerror("خطا در ذخیره گزارش", str(exc))


if __name__ == "__main__":
    app = SEOApp()
    app.mainloop()
