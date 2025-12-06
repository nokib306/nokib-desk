import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import os
import threading
import urllib.parse
import urllib.request
import json
import random
import time
import re
import sys
import subprocess
from datetime import datetime, timedelta

# ==========================================
# AUTO-INSTALL DEPENDENCY
# ==========================================
try:
    from huggingface_hub import InferenceClient
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "huggingface_hub"])
    from huggingface_hub import InferenceClient

# ==========================================
# CONFIGURATION
# ==========================================
CONTENT_DIR = "content"
CONFIG_FILE = "ai_config.json"

COLORS = {
    "bg": "#0f172a", "card": "#1e293b", "text": "#f8fafc",
    "primary": "#38bdf8", "success": "#22c55e", "danger": "#ef4444", "input": "#334155"
}

FONTS = {
    "header": ("Segoe UI", 20, "bold"),
    "label": ("Segoe UI", 11),
    "mono": ("Consolas", 10)
}

# FREE BACKUP MODELS (Hugging Face)
HF_MODELS = [
    "HuggingFaceTB/SmolLM2-1.7B-Instruct",
    "Qwen/Qwen2.5-7B-Instruct",
    "google/gemma-2-2b-it",
    "microsoft/Phi-3.5-mini-instruct",
    "mistralai/Mistral-7B-Instruct-v0.3"
]

class MegaChampApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Mega Champ - Ultimate AI Content Factory 🚀")
        self.root.geometry("1250x900")
        self.root.configure(bg=COLORS["bg"])
        
        self.stop_flag = False
        
        # API Keys
        self.hf_token = tk.StringVar()
        self.grok_key = tk.StringVar()
        self.deepseek_key = tk.StringVar()
        
        # Links
        self.cta_link_1 = tk.StringVar(value="https://learn2build.site")
        self.cta_link_2 = tk.StringVar(value="https://learn2build.site")
        self.cta_link_3 = tk.StringVar(value="https://learn2build.site")
        self.subfolder = tk.StringVar(value="posts")
        
        self.load_config()
        self.build_ui()

    def build_ui(self):
        header = tk.Frame(self.root, bg=COLORS["card"], pady=20)
        header.pack(fill="x")
        tk.Label(header, text="🦁 MEGA CHAMP (Grok + DeepSeek + HF)", font=FONTS["header"], bg=COLORS["card"], fg=COLORS["primary"]).pack()

        main_frame = tk.Frame(self.root, bg=COLORS["bg"], padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)

        # === LEFT PANEL: SETTINGS ===
        left_panel = tk.Frame(main_frame, bg=COLORS["bg"])
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 20))

        # API KEY SECTION
        api_box = tk.LabelFrame(left_panel, text="API Keys (Priority: Grok > DeepSeek > HF)", bg=COLORS["bg"], fg="white", font=("Segoe UI", 10, "bold"))
        api_box.pack(fill="x", pady=5, ipadx=10, ipady=10)

        tk.Label(api_box, text="1. Grok API Key (xAI):", bg=COLORS["bg"], fg=COLORS["success"]).pack(anchor="w")
        tk.Entry(api_box, textvariable=self.grok_key, bg=COLORS["input"], fg="lightgreen", show="*", font=FONTS["mono"]).pack(fill="x", pady=2)

        tk.Label(api_box, text="2. DeepSeek API Key:", bg=COLORS["bg"], fg=COLORS["primary"]).pack(anchor="w", pady=(5,0))
        tk.Entry(api_box, textvariable=self.deepseek_key, bg=COLORS["input"], fg="cyan", show="*", font=FONTS["mono"]).pack(fill="x", pady=2)

        tk.Label(api_box, text="3. Hugging Face Token (Free Backup):", bg=COLORS["bg"], fg="yellow").pack(anchor="w", pady=(5,0))
        tk.Entry(api_box, textvariable=self.hf_token, bg=COLORS["input"], fg="yellow", show="*", font=FONTS["mono"]).pack(fill="x", pady=2)

        # SETTINGS SECTION
        settings_box = tk.LabelFrame(left_panel, text="Settings & CTAs", bg=COLORS["bg"], fg="white", font=("Segoe UI", 10, "bold"))
        settings_box.pack(fill="x", pady=15, ipadx=10, ipady=10)

        tk.Label(settings_box, text="Save To Folder:", bg=COLORS["bg"], fg="white").pack(anchor="w")
        folder_options = ["posts", "resources", "blog", "tutorials", "reviews", "news", "guides"]
        self.combo_folder = ttk.Combobox(settings_box, textvariable=self.subfolder, values=folder_options, font=FONTS["mono"])
        self.combo_folder.pack(fill="x", pady=(2, 10))
        if not self.subfolder.get(): self.combo_folder.current(0) 

        tk.Label(settings_box, text="CTA 1 (Intro):", bg=COLORS["bg"], fg="white").pack(anchor="w")
        tk.Entry(settings_box, textvariable=self.cta_link_1, bg=COLORS["input"], fg="white", font=FONTS["mono"]).pack(fill="x", pady=2)
        
        tk.Label(settings_box, text="CTA 2 (Middle):", bg=COLORS["bg"], fg="white").pack(anchor="w")
        tk.Entry(settings_box, textvariable=self.cta_link_2, bg=COLORS["input"], fg="white", font=FONTS["mono"]).pack(fill="x", pady=2)
        
        tk.Label(settings_box, text="CTA 3 (End):", bg=COLORS["bg"], fg="white").pack(anchor="w")
        tk.Entry(settings_box, textvariable=self.cta_link_3, bg=COLORS["input"], fg="white", font=FONTS["mono"]).pack(fill="x", pady=2)

        # TOPICS INPUT
        tk.Label(left_panel, text="Paste Topics Here:", font=FONTS["label"], bg=COLORS["bg"], fg=COLORS["primary"]).pack(anchor="w", pady=(10, 0))
        self.txt_topics = scrolledtext.ScrolledText(left_panel, height=8, bg=COLORS["input"], fg="white", font=FONTS["mono"])
        self.txt_topics.pack(fill="both", expand=True, pady=5)
        self.txt_topics.insert("1.0", "How to Build SaaS Tools\nProgrammatic SEO Guide 2025\nAffiliate Marketing for Developers")

        # BUTTONS
        btn_row = tk.Frame(left_panel, bg=COLORS["bg"])
        btn_row.pack(fill="x", pady=20)
        tk.Button(btn_row, text="🚀 START GENERATING", command=self.start_process, bg=COLORS["success"], fg="white", font=("Segoe UI", 12, "bold"), height=2).pack(side="left", fill="x", expand=True, padx=(0, 5))
        tk.Button(btn_row, text="🛑 STOP", command=self.stop_process, bg=COLORS["danger"], fg="white", font=("Segoe UI", 12, "bold"), height=2).pack(side="right", fill="x", expand=True, padx=(5, 0))

        # === RIGHT PANEL: LOGS ===
        right_panel = tk.Frame(main_frame, bg=COLORS["card"], width=500)
        right_panel.pack(side="right", fill="y", padx=10)
        tk.Label(right_panel, text="📜 Process Log", font=("Segoe UI", 12, "bold"), bg=COLORS["card"], fg="white").pack(pady=10)
        self.log_area = scrolledtext.ScrolledText(right_panel, width=60, bg="black", fg="#4ade80", font=("Consolas", 9))
        self.log_area.pack(fill="both", expand=True, padx=10, pady=10)

    def log(self, msg):
        self.root.after(0, self._log_ui, msg)

    def _log_ui(self, msg):
        self.log_area.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        self.log_area.see(tk.END)

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    self.hf_token.set(data.get("hf_token", ""))
                    self.grok_key.set(data.get("grok_key", ""))
                    self.deepseek_key.set(data.get("deepseek_key", ""))
                    
                    default = "https://learn2build.site"
                    self.cta_link_1.set(data.get("cta_link_1", default))
                    self.cta_link_2.set(data.get("cta_link_2", default))
                    self.cta_link_3.set(data.get("cta_link_3", default))
                    self.subfolder.set(data.get("subfolder", "posts"))
            except: pass

    def save_config(self):
        data = {
            "hf_token": self.hf_token.get(),
            "grok_key": self.grok_key.get(),
            "deepseek_key": self.deepseek_key.get(),
            "cta_link_1": self.cta_link_1.get(),
            "cta_link_2": self.cta_link_2.get(),
            "cta_link_3": self.cta_link_3.get(),
            "subfolder": self.subfolder.get()
        }
        with open(CONFIG_FILE, "w") as f: json.dump(data, f)

    def get_image(self, topic):
        safe_topic = urllib.parse.quote(f"professional tech photo of {topic}, minimal, 4k")
        return f"https://image.pollinations.ai/prompt/{safe_topic}?width=1200&height=630&nologo=true"

    def inject_links(self, text):
        l1, l2, l3 = self.cta_link_1.get(), self.cta_link_2.get(), self.cta_link_3.get()
        parts = text.split('\n\n')
        if len(parts) > 2: parts.insert(1, f"\n\n> **🔥 Start Here: [{l1}]({l1})**\n\n")
        if len(parts) > 6: parts.insert(len(parts)//2, f"\n\n> **💡 Pro Tip: [Check This]({l2})**\n\n")
        parts.append(f"\n\n> **🚀 Launch: [Join Now]({l3})**")
        return "\n\n".join(parts)

    # --- UNIVERSAL API CALLER ---
    def call_premium_api(self, url, api_key, model, prompt):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        payload = {
            "messages": [
                {"role": "system", "content": "You are an expert technical blog writer."},
                {"role": "user", "content": prompt}
            ],
            "model": model,
            "stream": False,
            "temperature": 0.7
        }
        
        req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers)
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            return result['choices'][0]['message']['content']

    def generate_ai_text(self, topic):
        prompt = f"""
Write a comprehensive blog post about: "{topic}".
Format: Markdown.
Structure:
- Introduction (Hook the reader)
- Phase 1: The Concept
- Phase 2: Implementation (Include code snippets if relevant)
- Phase 3: Monetization
- Conclusion
Do NOT output the frontmatter/metadata. Just the body content.
"""
        # 1. TRY GROK (Priority 1)
        if self.grok_key.get():
            self.log(f"   ⏳ Trying Grok (xAI)...")
            try:
                content = self.call_premium_api("https://api.x.ai/v1/chat/completions", self.grok_key.get(), "grok-beta", prompt)
                if content: return content
            except Exception as e:
                self.log(f"   ⚠️ Grok Failed: {e}")

        # 2. TRY DEEPSEEK (Priority 2)
        if self.deepseek_key.get():
            self.log(f"   ⏳ Trying DeepSeek...")
            try:
                content = self.call_premium_api("https://api.deepseek.com/chat/completions", self.deepseek_key.get(), "deepseek-chat", prompt)
                if content: return content
            except Exception as e:
                self.log(f"   ⚠️ DeepSeek Failed: {e}")

        # 3. TRY HUGGING FACE (Free Backup)
        if self.hf_token.get():
            try:
                client = InferenceClient(token=self.hf_token.get())
                for model in HF_MODELS:
                    if self.stop_flag: return None
                    self.log(f"   ⏳ Trying HF Model: {model.split('/')[-1]}...")
                    try:
                        stream = client.chat_completion(
                            messages=[{"role": "user", "content": prompt}],
                            model=model, max_tokens=1500, stream=True
                        )
                        full_content = ""
                        for chunk in stream:
                            if chunk.choices and chunk.choices[0].delta.content:
                                full_content += chunk.choices[0].delta.content
                        if len(full_content) > 100: return full_content
                    except Exception:
                        pass
                    time.sleep(1)
            except Exception as e:
                self.log(f"   ⚠️ HF Error: {e}")

        return None

    def start_process(self):
        self.save_config()
        self.stop_flag = False
        threading.Thread(target=self.run_batch, daemon=True).start()

    def stop_process(self):
        self.stop_flag = True
        self.log("🛑 Stopping...")

    def run_batch(self):
        topics = [t.strip() for t in self.txt_topics.get("1.0", tk.END).split('\n') if t.strip()]
        if not topics: return

        folder_name = self.subfolder.get().strip() or "posts"
        save_path = os.path.join(CONTENT_DIR, folder_name)
        if not os.path.exists(save_path): os.makedirs(save_path)

        self.log(f"🚀 Starting Batch: {len(topics)} Topics")
        
        for i, topic in enumerate(topics):
            if self.stop_flag: break
            self.log(f"\n🤖 Processing [{i+1}/{len(topics)}]: {topic}")

            body = self.generate_ai_text(topic)
            if not body:
                self.log("❌ AI Failed (All providers failed). Skipping.")
                continue

            body = self.inject_links(body)
            img = self.get_image(topic)
            slug = re.sub(r'[^\w\s-]', '', topic.lower()).replace(" ", "-")
            date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%dT09:00:00+06:00')
            summary = body[:150].replace("\n", " ") + "..."

            hugo = f"""---
title: "{topic}"
date: {date}
draft: false
summary: "{summary}"
cover:
    image: "{img}"
tags: ["Dev", "Business"]
---

{body}
"""
            with open(f"{save_path}/{slug}.md", "w", encoding="utf-8") as f: f.write(hugo)
            self.log(f"✅ Saved: {slug}.md")
            time.sleep(2)

        self.log("\n🎉 ALL DONE!")
        messagebox.showinfo("Success", "Completed!")

if __name__ == "__main__":
    root = tk.Tk()
    app = MegaChampApp(root)
    root.mainloop()
