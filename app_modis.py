import os
import json
import threading
import pandas as pd
import numpy as np
import customtkinter as ctk
from tkinter import filedialog, messagebox

# --- SETUP TEMA CUSTOMTKINTER ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

CONFIG_FILE = "config_master.json"

class AplikasiEvaluasiSales(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Aplikasi Evaluasi Sales Modis V.0001")
        self.geometry("1150x650")
        self.minsize(1050, 600)
        self.configure(fg_color="#F8FAFC")

        # Variabel Path File & Folder
        self.path_sales = ctk.StringVar()
        self.path_produk = ctk.StringVar()
        self.path_output = ctk.StringVar(value="")
        
        self.path_dasar = ctk.StringVar()
        self.path_lm = ctk.StringVar()
        self.path_l2m = ctk.StringVar()
        self.path_l3m = ctk.StringVar()

        # Load konfigurasi yang tersimpan sebelumnya
        self.muat_config_master()

        self.buat_tampilan_ui()

    def muat_config_master(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    self.path_sales.set(data.get("sales", ""))
                    self.path_produk.set(data.get("produk", ""))
                    self.path_output.set(data.get("output_dir", ""))
            except Exception:
                pass

    def simpan_config_master(self):
        data = {
            "sales": self.path_sales.get(),
            "produk": self.path_produk.get(),
            "output_dir": self.path_output.get()
        }
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Gagal menyimpan config: {e}")

    def buat_tampilan_ui(self):
        # --- HEADER TITLE & MENU ATAS ---
        header_frame = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=0, height=60)
        header_frame.pack(fill="x", side="top")
        
        lbl_title = ctk.CTkLabel(
            header_frame, 
            text="GABUNG SALES MODIS", 
            font=ctk.CTkFont(family="Arial", size=15, weight="bold"),
            text_color="white"
        )
        lbl_title.pack(side="left", padx=20, pady=15)

        btn_output_menu = ctk.CTkButton(
            header_frame, text="📂 Set Folder Output", 
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#0F766E", hover_color="#115E59", width=140, height=32,
            command=self.buka_pengaturan_output
        )
        btn_output_menu.pack(side="right", padx=(0, 20), pady=15)

        btn_master_menu = ctk.CTkButton(
            header_frame, text="⚙️ Set File Master", 
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#334155", hover_color="#475569", width=130, height=32,
            command=self.buka_pengaturan_master
        )
        btn_master_menu.pack(side="right", padx=(0, 10), pady=15)

        # --- CONTAINER UTAMA (SPLIT 2 KOLOM) ---
        main_layout = ctk.CTkFrame(self, fg_color="transparent")
        main_layout.pack(fill="both", expand=True, padx=15, pady=15)

        main_layout.grid_columnconfigure(0, weight=3)
        main_layout.grid_columnconfigure(1, weight=2)
        main_layout.grid_rowconfigure(0, weight=1)

        # ==========================================
        # KOLOM KIRI: FORM INPUT & KONTROL
        # ==========================================
        left_panel = ctk.CTkScrollableFrame(main_layout, fg_color="transparent")
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=0)

        # 1. Status File Master (1 Baris)
        lbl_sec1 = ctk.CTkLabel(left_panel, text="1. Status File Master & Referensi", font=ctk.CTkFont(size=12, weight="bold"), text_color="#334155")
        lbl_sec1.pack(anchor="w", pady=(0, 4))

        frame_statis_info = ctk.CTkFrame(left_panel, fg_color="white", corner_radius=8, border_width=1, border_color="#E2E8F0")
        frame_statis_info.pack(fill="x", pady=(0, 12), padx=2)

        self.lbl_status_master = ctk.CTkLabel(frame_statis_info, text="", font=ctk.CTkFont(size=11, weight="bold"), anchor="w")
        self.lbl_status_master.pack(anchor="w", padx=15, pady=10)
        self.update_status_master()

        # 2. File Data Historis Bulanan
        lbl_sec2 = ctk.CTkLabel(left_panel, text="2. File Data Historis Bulanan", font=ctk.CTkFont(size=12, weight="bold"), text_color="#334155")
        lbl_sec2.pack(anchor="w", pady=(0, 4))

        frame_dinamis = ctk.CTkFrame(left_panel, fg_color="white", corner_radius=8, border_width=1, border_color="#E2E8F0")
        frame_dinamis.pack(fill="x", pady=(0, 12), padx=2)

        self.buat_baris_file(frame_dinamis, "File Dasar (Update):", self.path_dasar, 0)
        self.buat_baris_file(frame_dinamis, "File LM (1 Bln Lalu):", self.path_lm, 1)
        self.buat_baris_file(frame_dinamis, "File L2M (2 Bln Lalu):", self.path_l2m, 2)
        self.buat_baris_file(frame_dinamis, "File L3M (3 Bln Lalu):", self.path_l3m, 3)

        # 3. Tombol Eksekusi
        self.btn_proses = ctk.CTkButton(
            left_panel, 
            text="⚡ Gasss Bestiii", 
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#6366F1", hover_color="#4F46E5",
            height=42, corner_radius=8,
            command=self.mulai_proses_thread
        )
        self.btn_proses.pack(fill="x", pady=(5, 10), padx=2)

        # ==========================================
        # KOLOM KANAN: TERMINAL LOG MONITOR
        # ==========================================
        right_panel = ctk.CTkFrame(main_layout, fg_color="transparent")
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=0)

        lbl_log = ctk.CTkLabel(right_panel, text="🖥️ Terminal Log Proses:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#334155")
        lbl_log.pack(anchor="w", pady=(0, 4))

        self.textbox_log = ctk.CTkTextbox(
            right_panel, 
            fg_color="#0F172A", text_color="#38BDF8", 
            font=ctk.CTkFont(family="Consolas", size=11), 
            corner_radius=8
        )
        self.textbox_log.pack(fill="both", expand=True, padx=0, pady=(0, 0))
        self.textbox_log.configure(state="disabled")

        # --- FOOTER ---
        footer_frame = ctk.CTkFrame(self, fg_color="#E2E8F0", corner_radius=0, height=28)
        footer_frame.pack(fill="x", side="bottom")
        lbl_footer = ctk.CTkLabel(footer_frame, text="Powered By : Y. Adhihouse", font=ctk.CTkFont(size=11, slant="italic"), text_color="#64748B")
        lbl_footer.pack(pady=4)

    def update_status_master(self):
        if self.path_sales.get() and self.path_produk.get():
            self.lbl_status_master.configure(text="Status File Master : Sudah Diset ✅", text_color="#10B981")
        else:
            self.lbl_status_master.configure(text="Status File Master : Belum Diset ❌", text_color="#EF4444")

    def buka_pengaturan_master(self):
        top = ctk.CTkToplevel(self)
        top.title("Pengaturan File Master")
        top.geometry("600x250")
        top.grab_set()

        lbl = ctk.CTkLabel(top, text="Pengaturan File Master (Jarang Berubah)", font=ctk.CTkFont(weight="bold"))
        lbl.pack(pady=10)

        f_frame = ctk.CTkFrame(top, fg_color="transparent")
        f_frame.pack(fill="both", expand=True, padx=20, pady=10)

        ctk.CTkLabel(f_frame, text="File Data Sales:").grid(row=0, column=0, sticky="w", pady=5)
        e_sales = ctk.CTkEntry(f_frame, textvariable=self.path_sales, width=350)
        e_sales.grid(row=0, column=1, padx=5, pady=5)
        ctk.CTkButton(f_frame, text="Browse", width=70, command=lambda: [self.browse_file(self.path_sales, is_dir=False), self.simpan_config_master(), self.update_status_master()]).grid(row=0, column=2, pady=5)

        ctk.CTkLabel(f_frame, text="File Produk Khusus:").grid(row=1, column=0, sticky="w", pady=5)
        e_produk = ctk.CTkEntry(f_frame, textvariable=self.path_produk, width=350)
        e_produk.grid(row=1, column=1, padx=5, pady=5)
        ctk.CTkButton(f_frame, text="Browse", width=70, command=lambda: [self.browse_file(self.path_produk, is_dir=False), self.simpan_config_master(), self.update_status_master()]).grid(row=1, column=2, pady=5)

        btn_tutup = ctk.CTkButton(top, text="Simpan & Tutup", fg_color="#10B981", hover_color="#059669", command=lambda: [self.simpan_config_master(), self.update_status_master(), top.destroy()])
        btn_tutup.pack(pady=10)

    def buka_pengaturan_output(self):
        top = ctk.CTkToplevel(self)
        top.title("Pengaturan Folder Output")
        top.geometry("550x200")
        top.grab_set()

        lbl = ctk.CTkLabel(top, text="Pilih Folder Tempat Menyimpan Hasil Evaluasi", font=ctk.CTkFont(weight="bold"))
        lbl.pack(pady=10)

        f_frame = ctk.CTkFrame(top, fg_color="transparent")
        f_frame.pack(fill="both", expand=True, padx=20, pady=10)

        ctk.CTkLabel(f_frame, text="Folder Output:").grid(row=0, column=0, sticky="w", pady=5)
        e_out = ctk.CTkEntry(f_frame, textvariable=self.path_output, width=300)
        e_out.grid(row=0, column=1, padx=5, pady=5)
        ctk.CTkButton(f_frame, text="Browse", width=70, command=lambda: self.browse_file(self.path_output, is_dir=True)).grid(row=0, column=2, pady=5)

        btn_tutup = ctk.CTkButton(top, text="Simpan & Tutup", fg_color="#0F766E", hover_color="#115E59", command=lambda: [self.simpan_config_master(), top.destroy()])
        btn_tutup.pack(pady=10)

    def buat_baris_file(self, parent, label_text, var_path, row_idx):
        lbl = ctk.CTkLabel(parent, text=label_text, font=ctk.CTkFont(size=11), text_color="#475569", anchor="w")
        lbl.grid(row=row_idx, column=0, sticky="w", padx=10, pady=6)

        entry = ctk.CTkEntry(parent, textvariable=var_path, width=280, fg_color="#F1F5F9", text_color="#1E293B", border_color="#CBD5E1")
        entry.grid(row=row_idx, column=1, sticky="ew", padx=5, pady=6)

        btn = ctk.CTkButton(
            parent, text="Browse", width=70, 
            fg_color="#475569", hover_color="#334155",
            command=lambda v=var_path: self.browse_file(v, is_dir=False)
        )
        btn.grid(row=row_idx, column=2, padx=10, pady=6)
        parent.grid_columnconfigure(1, weight=1)

    def browse_file(self, var_target, is_dir=False):
        if is_dir:
            foldername = filedialog.askdirectory()
            if foldername:
                var_target.set(foldername)
                self.simpan_config_master()
        else:
            filename = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx;*.xls"), ("All Files", "*.*")])
            if filename:
                var_target.set(filename)

    def log(self, pesan):
        self.textbox_log.configure(state="normal")
        self.textbox_log.insert("end", pesan + "\n")
        self.textbox_log.see("end")
        self.textbox_log.configure(state="disabled")

    def mulai_proses_thread(self):
        self.btn_proses.configure(state="disabled", fg_color="#94A3B8")
        threading.Thread(target=self.jalankan_backend_evaluasi, daemon=True).start()

    def jalankan_backend_evaluasi(self):
        f_sales = self.path_sales.get()
        f_produk = self.path_produk.get()
        f_dasar = self.path_dasar.get()
        f_lm = self.path_lm.get()
        f_l2m = self.path_l2m.get()
        f_l3m = self.path_l3m.get()
        out_dir = self.path_output.get()

        if not all([f_sales, f_produk, f_dasar, f_lm, f_l2m, f_l3m]):
            messagebox.showerror("Error", "Pastikan File Master (Sales & Produk Khusus) serta 4 File Dinamis sudah lengkap terpilih!")
            self.btn_proses.configure(state="normal", fg_color="#6366F1")
            return

        if not out_dir or not os.path.exists(out_dir):
            out_dir = os.getcwd()

        self.log("\n[INFO] Memulai proses evaluasi data...")
        try:
            self.log(" -> Membaca file master produk dan sales...")
            df_produk = pd.read_excel(f_produk, dtype=str)
            df_sales = pd.read_excel(f_sales, dtype=str)

            self.log(" -> Membaca file data historis bulanan (LM, L2M, L3M)...")
            df_lm = pd.read_excel(f_lm, dtype={'prdcd': str})[['prdcd', 'sales_net', 'margin']].rename(columns={'sales_net': 'Sales LM', 'margin': 'Mrgin LM'})
            df_l2m = pd.read_excel(f_l2m, dtype={'prdcd': str})[['prdcd', 'sales_net', 'margin']].rename(columns={'sales_net': 'Sales L2M', 'margin': 'Mrgin L2M'})
            df_l3m = pd.read_excel(f_l3m, dtype={'prdcd': str})[['prdcd', 'sales_net', 'margin']].rename(columns={'sales_net': 'Sales L3M', 'margin': 'Mrgin L3M'})

            self.log(" -> Menggabungkan data historis (HSL1)...")
            hsl1 = df_lm.merge(df_l2m, on='prdcd', how='outer').merge(df_l3m, on='prdcd', how='outer').fillna(0)

            self.log(" -> Membaca File Dasar & merapikan Modis (6 char)...")
            df_dasar_full = pd.read_excel(f_dasar, dtype={'prdcd': str})
            
            kode_toko_target = str(df_dasar_full['toko'].iloc[0]).split('-')[0].strip()

            df_dasar = df_dasar_full[['prdcd', 'kode_paket']].copy()
            df_dasar['kode_paket'] = df_dasar['kode_paket'].fillna('0').astype(str).str.strip()
            df_dasar['kode_paket'] = np.where(
                df_dasar['kode_paket'].str.startswith('1'),
                df_dasar['kode_paket'].str[1:7],
                df_dasar['kode_paket'].str[:6]
            )

            self.log(" -> Melakukan VLOOKUP Modis & Produk Khusus (HSL2)...")
            hsl2 = hsl1.merge(df_dasar, on='prdcd', how='left')
            hsl2 = hsl2.merge(df_produk, left_on='prdcd', right_on='PRDCD', how='left')

            hsl2['Modis_Final'] = np.where(hsl2['MODUL'].notnull(), hsl2['MODUL'], 
                                           np.where((hsl2['kode_paket'] == '0') | (hsl2['kode_paket'].isnull()), 'R', hsl2['kode_paket']))

            self.log(" -> Membuat Pivot akhir berdasarkan Modis...")
            pivot_akhir = hsl2.groupby('Modis_Final').agg({
                'Sales L3M': 'sum', 'Mrgin L3M': 'sum',
                'Sales L2M': 'sum', 'Mrgin L2M': 'sum',
                'Sales LM': 'sum', 'Mrgin LM': 'sum'
            }).reset_index()

            pivot_akhir['Total Sales'] = pivot_akhir['Sales L3M'] + pivot_akhir['Sales L2M'] + pivot_akhir['Sales LM']
            pivot_akhir['Total Margin'] = pivot_akhir['Mrgin L3M'] + pivot_akhir['Mrgin L2M'] + pivot_akhir['Mrgin LM']

            pivot_akhir = pivot_akhir[pivot_akhir['Total Sales'] != 0].copy()

            # --- REKONSILIASI SELISIH DENGAN DATA SALES (ANTI-DOBEL) ---
            self.log(f" -> Cek selisih dengan Data Sales (Toko: {kode_toko_target})...")
            data_toko = df_sales[df_sales['KODE'] == kode_toko_target]

            if not data_toko.empty:
                target_sls_lm = float(data_toko['SLS NET LM'].iloc[0])
                target_mrg_lm = float(data_toko['MRG NET LM'].iloc[0])
                target_sls_l2m = float(data_toko['SLS NET L2M'].iloc[0])
                target_mrg_l2m = float(data_toko['MRG NET L2M'].iloc[0])
                target_sls_l3m = float(data_toko['SLS NET L3M'].iloc[0])
                target_mrg_l3m = float(data_toko['MRG NET L3M'].iloc[0])

                # Jika baris 'R' sudah ada dari hasil pivot, nolkan dulu nilainya di kalkulasi awal 
                # supaya kita bisa menghitung murni item non-R, atau kita hitung langsung selisihnya terhadap total master.
                mask_not_r = pivot_akhir['Modis_Final'] != 'R'
                sum_sls_lm = pivot_akhir.loc[mask_not_r, 'Sales LM'].sum()
                sum_mrg_lm = pivot_akhir.loc[mask_not_r, 'Mrgin LM'].sum()
                sum_sls_l2m = pivot_akhir.loc[mask_not_r, 'Sales L2M'].sum()
                sum_mrg_l2m = pivot_akhir.loc[mask_not_r, 'Mrgin L2M'].sum()
                sum_sls_l3m = pivot_akhir.loc[mask_not_r, 'Sales L3M'].sum()
                sum_mrg_l3m = pivot_akhir.loc[mask_not_r, 'Mrgin L3M'].sum()

                diff_sls_lm = target_sls_lm - sum_sls_lm
                diff_mrg_lm = target_mrg_lm - sum_mrg_lm
                diff_sls_l2m = target_sls_l2m - sum_sls_l2m
                diff_mrg_l2m = target_mrg_l2m - sum_mrg_l2m
                diff_sls_l3m = target_sls_l3m - sum_sls_l3m
                diff_mrg_l3m = target_mrg_l3m - sum_mrg_l3m

                # Pastikan baris 'R' ada (hanya 1 baris)
                if 'R' not in pivot_akhir['Modis_Final'].values:
                    baris_r = {
                        'Modis_Final': 'R', 
                        'Sales L3M': 0, 'Mrgin L3M': 0, 
                        'Sales L2M': 0, 'Mrgin L2M': 0, 
                        'Sales LM': 0, 'Mrgin LM': 0, 
                        'Total Sales': 0, 'Total Margin': 0
                    }
                    pivot_akhir = pd.concat([pivot_akhir, pd.DataFrame([baris_r])], ignore_index=True)

                # Ambil index baris 'R' dan TIMPA (overwrite) langsung nilainya dengan selisih murni
                idx_r = pivot_akhir.index[pivot_akhir['Modis_Final'] == 'R'][0]
                
                pivot_akhir.loc[idx_r, 'Sales LM'] = diff_sls_lm
                pivot_akhir.loc[idx_r, 'Mrgin LM'] = diff_mrg_lm
                pivot_akhir.loc[idx_r, 'Sales L2M'] = diff_sls_l2m
                pivot_akhir.loc[idx_r, 'Mrgin L2M'] = diff_mrg_l2m
                pivot_akhir.loc[idx_r, 'Sales L3M'] = diff_sls_l3m
                pivot_akhir.loc[idx_r, 'Mrgin L3M'] = diff_mrg_l3m

                pivot_akhir.loc[idx_r, 'Total Sales'] = diff_sls_lm + diff_sls_l2m + diff_sls_l3m
                pivot_akhir.loc[idx_r, 'Total Margin'] = diff_mrg_lm + diff_mrg_l2m + diff_mrg_l3m
            else:
                self.log(f" [PERINGATAN] Data toko {kode_toko_target} tidak ditemukan di file Data Sales.")

            # --- URUTKAN KOLOM AKHIR ---
            kolom_urutan = [
                'Modis_Final', 
                'Sales L3M', 'Mrgin L3M', 
                'Sales L2M', 'Mrgin L2M', 
                'Sales LM', 'Mrgin LM', 
                'Total Sales', 'Total Margin'
            ]
            pivot_akhir = pivot_akhir[kolom_urutan]
            pivot_akhir.rename(columns={'Modis_Final': 'MODIS'}, inplace=True)

            # --- SIMPAN KE FOLDER OUTPUT ---
            file_name = f"Hasil_Evaluasi_{kode_toko_target}.xlsx"
            output_filepath = os.path.join(out_dir, file_name)
            
            pivot_akhir.to_excel(output_filepath, index=False)
            
            self.log(f"\n[SUKSES] Evaluasi Selesai!")
            self.log(f"Disimpan di: {output_filepath}")
            messagebox.showinfo("Berhasil", f"Proses evaluasi selesai!\nFile disimpan di:\n{output_filepath}")

        except Exception as e:
            self.log(f"\n[ERROR] Terjadi kesalahan: {str(e)}")
            messagebox.showerror("Error", str(e))

        finally:
            self.btn_proses.configure(state="normal", fg_color="#6366F1")

if __name__ == "__main__":
    app = AplikasiEvaluasiSales()
    app.mainloop()