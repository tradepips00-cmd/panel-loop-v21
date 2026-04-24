
import os
import json
import subprocess
import tkinter as tk
from pathlib import Path
from datetime import datetime
from tkinter import messagebox

AUTHOR = "Ahmad Nazari"
VERSION = "v2.1"
PROFILE_FILE = Path(__file__).with_name("panel_loop_profile.json")

GAMELOOP_PATHS = [
    r"C:\Program Files\TxGameAssistant\AppMarket\AppMarket.exe",
    r"C:\Program Files\TxGameAssistant\ui\AppMarket.exe",
    r"C:\Program Files\TxGameAssistant\AndroidEmulatorEx.exe",
    r"C:\Program Files\GameLoop\Launcher.exe",
    r"D:\Program Files\TxGameAssistant\AppMarket\AppMarket.exe",
    r"D:\TxGameAssistant\AppMarket\AppMarket.exe",
]

GAMELOOP_PROCESSES = [
    "AppMarket", "AndroidEmulator", "AndroidEmulatorEx",
    "aow_exe", "ProjectTitan", "AndroidRender", "QMEmulatorService"
]

SAFE_BACKGROUND_PROCESSES = [
    "OneDrive", "Widgets", "YourPhone", "PhoneExperienceHost",
    "GameBar", "XboxGameBar", "XboxAppServices"
]

def run_ps(command):
    try:
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        r = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
            capture_output=True, text=True, timeout=45, creationflags=flags
        )
        return (r.stdout or r.stderr or "").strip()
    except Exception as e:
        return str(e)

def get_wmi(prop, cls):
    out = run_ps(f"(Get-CimInstance {cls} | Select-Object -First 1 -ExpandProperty {prop})")
    return out.strip() if out.strip() else "Unknown"

def cpu_name():
    return get_wmi("Name", "Win32_Processor")

def logical_cores():
    try:
        return int(get_wmi("NumberOfLogicalProcessors", "Win32_Processor"))
    except:
        return os.cpu_count() or 4

def ram_gb():
    try:
        return round(int(get_wmi("TotalPhysicalMemory", "Win32_ComputerSystem")) / 1024 / 1024 / 1024, 2)
    except:
        return 0.0

def gpu_name():
    return get_wmi("Name", "Win32_VideoController")

def find_gameloop():
    for p in GAMELOOP_PATHS:
        if Path(p).exists():
            return p
    return None

def affinity_mask(logical, threads):
    if logical <= 1:
        return 1
    threads = max(1, min(threads, logical - 1))
    mask = 0
    for i in range(1, threads + 1):
        mask |= 1 << i
    return mask

def affinity_mask_skip_first(logical, use_threads, skip=4):
    """
    Voor jouw Ryzen 7 7700 met 16 logical threads:
    skip=4 en use_threads=12 => CPU 4 t/m CPU 15.
    """
    if logical <= 1:
        return 1
    start = min(skip, logical - 1)
    end = min(logical - 1, start + use_threads - 1)
    mask = 0
    for i in range(start, end + 1):
        mask |= 1 << i
    return mask if mask else affinity_mask(logical, use_threads)

def auto_profile():
    logical = logical_cores()
    ram = ram_gb()
    gpu = gpu_name()
    gpu_upper = gpu.upper()
    high_gpu = any(x in gpu_upper for x in ["RTX 4090", "RTX 4080", "RTX 4070", "RX 7900", "RX 7800"])
    dedicated = any(x in gpu_upper for x in ["NVIDIA", "AMD", "RADEON", "RTX", "GTX", "RX"])

    if logical >= 16 and ram >= 24 and high_gpu:
        tier = "PUBG Ultra Competitive"
        threads = min(12, max(1, logical - 4))
        ram_mb = 8192
        mask = affinity_mask_skip_first(logical, threads, 4)
    elif logical >= 16 and ram >= 24 and dedicated:
        tier = "High-End Competitive"
        threads = min(10, max(1, logical - 4))
        ram_mb = 8192
        mask = affinity_mask_skip_first(logical, threads, 4)
    elif logical >= 12 and ram >= 16:
        tier = "Competitive"
        threads = 8
        ram_mb = 8192
        mask = affinity_mask(logical, threads)
    elif logical >= 8 and ram >= 8:
        tier = "Balanced"
        threads = 6
        ram_mb = 4096
        mask = affinity_mask(logical, threads)
    else:
        tier = "Safe Mode"
        threads = 4
        ram_mb = 3072
        mask = affinity_mask(logical, threads)

    return {
        "tier": tier,
        "cpu": cpu_name(),
        "gpu": gpu,
        "logical": logical,
        "ram_gb": ram,
        "threads": threads,
        "ram_mb": ram_mb,
        "affinity": mask,
        "gameloop_path": find_gameloop()
    }

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"PANEL LOOP NEXT LEVEL - {AUTHOR} {VERSION}")
        self.geometry("1240x800")
        self.minsize(1140, 740)
        self.configure(bg="#07090d")
        self.profile = auto_profile()
        self.glow_state = True
        self.build_ui()
        self.refresh_cards()
        self.log("Panel Loop Next Level v2.1 started.")
        self.log("Auto profile ready.")
        self.animate_glow()

    def build_ui(self):
        header = tk.Frame(self, bg="#07090d", height=130)
        header.pack(fill="x")

        self.title_label = tk.Label(header, text="PANEL LOOP", bg="#07090d", fg="#00ffd5",
                 font=("Consolas", 38, "bold"))
        self.title_label.place(x=25, y=20)

        tk.Label(header, text="NEXT LEVEL PUBG GAMELOOP OPTIMIZER", bg="#07090d", fg="#00ffd5",
                 font=("Consolas", 16, "bold")).place(x=32, y=78)
        tk.Label(header, text=f"Made by {AUTHOR} © 2026  |  VERSION {VERSION}", bg="#07090d", fg="#a0a0a0",
                 font=("Consolas", 11)).place(x=32, y=106)

        self.badge = tk.Label(header, text="FULLY ACTIVATED ☑", bg="#07090d", fg="#31ff47",
                 font=("Consolas", 14, "bold"), relief="solid", bd=1,
                 padx=15, pady=6)
        self.badge.place(x=950, y=30)

        self.engine_status = tk.Label(header, text="ENGINE STATUS: ● READY", bg="#07090d",
                                      fg="#31ff47", font=("Consolas", 13, "bold"))
        self.engine_status.place(x=920, y=84)

        tk.Frame(self, bg="#00ffd5", height=2).pack(fill="x")

        body = tk.Frame(self, bg="#07090d")
        body.pack(fill="both", expand=True, padx=22, pady=18)

        left = tk.Frame(body, bg="#07090d", width=360)
        left.pack(side="left", fill="y")

        tk.Label(left, text="⚡ EXECUTION PROTOCOLS", bg="#07090d", fg="white",
                 font=("Consolas", 16, "bold")).pack(anchor="w", pady=(0, 12))

        self.button(left, "🚀 ONE CLICK CPU/GPU/RAM", "#00ffd5", self.one_click)
        self.button(left, "🎮 PUBG ULTRA MODE", "#31ff47", self.pubg_ultra_mode)
        self.button(left, "🧠 AUTO 12 THREAD AFFINITY", "#ffdf5d", self.auto_12_thread_affinity)
        self.button(left, "⚡ START GAMELOOP OPTIMIZED", "#4aa3ff", self.start_gameloop)
        self.button(left, "🔁 RE-APPLY AFFINITY NOW", "#ffdf5d", self.apply_process_tuning)
        self.button(left, "🧠 AUTO DETECT PROFILE", "#4aa3ff", self.detect_profile)
        self.button(left, "🎯 FORCE GPU MODE", "#ffd43b", self.force_gpu)
        self.button(left, "⌨ SAFE INPUT BOOST", "#9b5cff", self.safe_input_boost)
        self.button(left, "🧹 CLEAN STUTTER CACHE", "#ff6b6b", self.clean_cache)
        self.button(left, "🛡 STABLE RESTORE DEFAULTS", "#aaaaaa", self.restore_defaults)
        self.button(left, "❌ EXIT PANEL", "#ff4d6d", self.destroy)

        right = tk.Frame(body, bg="#07090d")
        right.pack(side="left", fill="both", expand=True, padx=(20, 0))

        cards = tk.Frame(right, bg="#07090d")
        cards.pack(fill="x")

        self.cpu_label = self.card(cards, "SYSTEM CPU", "#4aa3ff", 0, 0)
        self.ram_label = self.card(cards, "SYSTEM RAM", "#4aa3ff", 0, 1)
        self.gpu_label = self.card(cards, "SYSTEM GPU", "#31ff9f", 1, 0)
        self.engine_label = self.card(cards, "PUBG/GAMELOOP ENGINE", "#ffd43b", 1, 1)
        self.latency_label = self.card(cards, "LATENCY PROFILE", "#9b5cff", 2, 0)
        self.status_label = self.card(cards, "SESSION STATUS", "#31ff47", 2, 1)

        cards.columnconfigure(0, weight=1)
        cards.columnconfigure(1, weight=1)

        log_frame = tk.Frame(right, bg="#101217", relief="solid", bd=1)
        log_frame.pack(fill="both", expand=True, pady=(18, 0))

        tk.Label(log_frame, text="> LIVE LOG CONSOLE", bg="#101217", fg="white",
                 font=("Consolas", 15, "bold")).pack(anchor="w", padx=15, pady=10)

        self.log_box = tk.Text(log_frame, bg="#000000", fg="#31ff47",
                               insertbackground="#31ff47", font=("Consolas", 11),
                               height=13, relief="flat")
        self.log_box.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    def button(self, parent, text, color, command):
        b = tk.Button(parent, text=text, command=command, bg="#15191f", fg=color,
                      activebackground="#232a33", activeforeground=color,
                      relief="flat", font=("Consolas", 11, "bold"),
                      anchor="w", padx=18, pady=10)
        b.pack(fill="x", pady=4)

    def card(self, parent, title, color, row, col):
        frame = tk.Frame(parent, bg="#101217", relief="solid", bd=1, width=360, height=118)
        frame.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)
        frame.pack_propagate(False)
        tk.Label(frame, text=title, bg="#101217", fg=color,
                 font=("Consolas", 13, "bold")).pack(anchor="w", padx=18, pady=(13, 0))
        label = tk.Label(frame, text="", bg="#101217", fg="white",
                         font=("Consolas", 11), justify="left")
        label.pack(anchor="w", padx=18, pady=8)
        return label

    def animate_glow(self):
        self.glow_state = not self.glow_state
        self.title_label.config(fg="#00ffd5" if self.glow_state else "#00bfa8")
        self.after(700, self.animate_glow)

    def refresh_cards(self):
        p = self.profile
        self.cpu_label.config(text=f"CPU: {p['cpu']}\nThreads: {p['logical']}\nProfile: {p['tier']}")
        self.ram_label.config(text=f"System RAM: {p['ram_gb']} GB\nTarget RAM: {p['ram_mb']} MB")
        self.gpu_label.config(text=f"GPU: {p['gpu']}\nStatus: High Performance Target")
        self.engine_label.config(text=f"CPU target: {p['threads']} threads\nRAM target: {p['ram_mb']} MB\nAffinity: {p['affinity']}")
        self.latency_label.config(text="Input: Safe Boost\nGPU: High Perf Target\nMode: Stable Competitive")
        self.status_label.config(text="Recommended flow:\n1) Auto 12 Thread Affinity\n2) Start GameLoop")

    def log(self, msg):
        self.log_box.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        self.log_box.see("end")

    def detect_profile(self):
        self.profile = auto_profile()
        self.refresh_cards()
        self.log(f"Auto profile: {self.profile['tier']}")
        self.log(f"CPU target: {self.profile['threads']} threads")
        self.log(f"RAM target: {self.profile['ram_mb']} MB")

    def auto_12_thread_affinity(self):
        logical = logical_cores()
        if logical >= 16:
            threads = 12
            mask = affinity_mask_skip_first(logical, 12, 4)
            self.profile["threads"] = threads
            self.profile["affinity"] = mask
            self.profile["ram_mb"] = 8192
            self.profile["tier"] = "Manual 12 Thread PUBG Mode"
            self.refresh_cards()
            self.log("AUTO 12 THREAD AFFINITY selected: CPU 4 through CPU 15.")
            self.log(f"Affinity mask: {mask}")
            self.apply_process_tuning_repeated()
            self.save_profile()
        else:
            self.log("CPU has less than 16 threads. Using auto profile instead.")
            self.detect_profile()
            self.apply_process_tuning_repeated()

    def one_click(self):
        self.detect_profile()
        self.log("ONE CLICK: applying CPU/GPU/RAM profile...")
        self.set_high_performance()
        self.force_gpu()
        self.safe_input_boost(silent=True)
        self.apply_process_tuning_repeated()
        self.save_profile()
        self.log("SUCCESS: One Click CPU/GPU/RAM complete.")
        messagebox.showinfo("Panel Loop", "One Click complete.\nSet GameLoop Memory to 8192M and Processor to max available.\nAffinity is applied by this tool.")

    def pubg_ultra_mode(self):
        self.detect_profile()
        if self.profile["logical"] >= 16:
            self.profile["threads"] = 12
            self.profile["affinity"] = affinity_mask_skip_first(self.profile["logical"], 12, 4)
            self.profile["ram_mb"] = 8192
        self.refresh_cards()
        self.log("PUBG ULTRA MODE: Starting safe full optimization...")
        self.set_high_performance()
        self.force_gpu()
        self.safe_input_boost(silent=True)
        self.safe_background_cleanup()
        self.apply_network_stability()
        self.apply_process_tuning_repeated()
        self.save_profile()
        self.log("SUCCESS: PUBG Ultra Mode applied.")
        messagebox.showinfo("PUBG Ultra Mode", "PUBG Ultra Mode applied.\nRecommended GameLoop: DirectX+, VSync OFF, AA OFF, 1920x1080, RAM 8192M.")

    def start_gameloop(self):
        path = self.profile.get("gameloop_path")
        if not path:
            self.log("GameLoop not found.")
            messagebox.showwarning("GameLoop not found", "GameLoop was not found in default paths.")
            return
        self.log(f"Launching GameLoop: {path}")
        try:
            subprocess.Popen([path])
        except Exception as e:
            self.log(f"Launch failed: {e}")
            return
        self.set_high_performance()
        self.log("Waiting for GameLoop processes, then applying affinity repeatedly...")
        self.after(10000, self.apply_process_tuning)
        self.after(18000, self.apply_process_tuning)
        self.after(26000, self.apply_process_tuning)
        self.after(34000, self.apply_process_tuning)

    def apply_process_tuning_repeated(self):
        self.apply_process_tuning()
        self.after(5000, self.apply_process_tuning)
        self.after(10000, self.apply_process_tuning)
        self.after(15000, self.apply_process_tuning)

    def apply_process_tuning(self):
        mask = self.profile["affinity"]
        names = ",".join([f"'{n}'" for n in GAMELOOP_PROCESSES])
        ps = f"""
        $names=@({names});
        foreach($n in $names){{
          Get-Process -Name $n -ErrorAction SilentlyContinue | ForEach-Object {{
            try {{ if($_.ProcessName -ne 'adb'){{$_.PriorityClass='High'}} }} catch {{}}
            try {{ if($_.ProcessName -ne 'QMEmulatorService'){{$_.ProcessorAffinity={mask}}} }} catch {{}}
          }}
        }}
        """
        run_ps(ps)
        self.log(f"Applied High priority + CPU affinity mask {mask}.")
        self.engine_status.config(text="ENGINE STATUS: ● ONLINE", fg="#31ff47")

    def set_high_performance(self):
        run_ps("powercfg /S SCHEME_MIN")
        self.log("Power plan set to High Performance.")

    def force_gpu(self):
        paths = []
        if self.profile.get("gameloop_path"):
            paths.append(self.profile["gameloop_path"])
        paths.extend(GAMELOOP_PATHS)
        for exe in dict.fromkeys(paths):
            ps = f"""
            New-Item -Path 'HKCU:\\Software\\Microsoft\\DirectX\\UserGpuPreferences' -Force | Out-Null
            New-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\DirectX\\UserGpuPreferences' -Name '{exe}' -Value 'GpuPreference=2;' -PropertyType String -Force | Out-Null
            """
            run_ps(ps)
        self.log("GPU preference set to High Performance for GameLoop paths.")

    def safe_input_boost(self, silent=False):
        ps = r"""
        Set-ItemProperty -Path 'HKCU:\Control Panel\Keyboard' -Name 'KeyboardDelay' -Value 0
        Set-ItemProperty -Path 'HKCU:\Control Panel\Keyboard' -Name 'KeyboardSpeed' -Value 31
        Set-ItemProperty -Path 'HKCU:\Control Panel\Mouse' -Name 'MouseSpeed' -Value 0
        Set-ItemProperty -Path 'HKCU:\Control Panel\Mouse' -Name 'MouseThreshold1' -Value 0
        Set-ItemProperty -Path 'HKCU:\Control Panel\Mouse' -Name 'MouseThreshold2' -Value 0
        New-Item -Path 'HKCU:\Software\Microsoft\GameBar' -Force | Out-Null
        New-ItemProperty -Path 'HKCU:\Software\Microsoft\GameBar' -Name 'AllowAutoGameMode' -Value 1 -PropertyType DWORD -Force | Out-Null
        """
        run_ps(ps)
        self.log("Safe Input Boost applied.")
        if not silent:
            messagebox.showinfo("Panel Loop", "Safe Input Boost applied.\nRestart Windows for best result.")

    def safe_background_cleanup(self):
        names = ",".join([f"'{n}'" for n in SAFE_BACKGROUND_PROCESSES])
        ps = f"""
        $names=@({names});
        foreach($n in $names){{
            Get-Process -Name $n -ErrorAction SilentlyContinue | ForEach-Object {{
                try {{ Stop-Process -Id $_.Id -Force }} catch {{}}
            }}
        }}
        """
        run_ps(ps)
        self.log("Safe background cleanup completed.")

    def apply_network_stability(self):
        run_ps("powercfg -change -standby-timeout-ac 0; powercfg -change -monitor-timeout-ac 0")
        self.log("Session stability preferences applied.")

    def clean_cache(self, silent=False):
        self.log("Cleaning stutter cache...")
        dirs = [
            os.path.join(os.getenv("LOCALAPPDATA", ""), "D3DSCache"),
            os.path.join(os.getenv("LOCALAPPDATA", ""), "NVIDIA", "DXCache"),
            os.path.join(os.getenv("LOCALAPPDATA", ""), "NVIDIA", "GLCache"),
            os.getenv("TEMP", "")
        ]
        cleaned = 0
        for d in dirs:
            if d and os.path.exists(d):
                for root, _, files in os.walk(d):
                    for f in files:
                        try:
                            os.remove(os.path.join(root, f))
                            cleaned += 1
                        except:
                            pass
        self.log(f"Cache clean finished. Files cleaned: {cleaned}")
        if not silent:
            messagebox.showinfo("Panel Loop", "Cache clean finished.")

    def restore_defaults(self):
        if not messagebox.askyesno("Restore Defaults", "Restore keyboard/mouse/power defaults?"):
            return
        ps = r"""
        Set-ItemProperty -Path 'HKCU:\Control Panel\Keyboard' -Name 'KeyboardDelay' -Value 1
        Set-ItemProperty -Path 'HKCU:\Control Panel\Keyboard' -Name 'KeyboardSpeed' -Value 15
        Set-ItemProperty -Path 'HKCU:\Control Panel\Mouse' -Name 'MouseSpeed' -Value 1
        Set-ItemProperty -Path 'HKCU:\Control Panel\Mouse' -Name 'MouseThreshold1' -Value 6
        Set-ItemProperty -Path 'HKCU:\Control Panel\Mouse' -Name 'MouseThreshold2' -Value 10
        powercfg /S SCHEME_BALANCED
        New-Item -Path 'HKCU:\Software\Microsoft\GameBar' -Force | Out-Null
        New-ItemProperty -Path 'HKCU:\Software\Microsoft\GameBar' -Name 'AllowAutoGameMode' -Value 0 -PropertyType DWORD -Force | Out-Null
        """
        run_ps(ps)
        self.log("Defaults restored. Restart recommended.")

    def save_profile(self):
        try:
            PROFILE_FILE.write_text(json.dumps(self.profile, indent=2), encoding="utf-8")
            self.log("Profile saved.")
        except Exception as e:
            self.log(f"Profile save failed: {e}")

if __name__ == "__main__":
    App().mainloop()
