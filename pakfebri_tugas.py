import streamlit as st
import sqlite3
import pandas as pd
import os
import random
import time
from datetime import datetime

# ================= DATABASE & AUTO-UPGRADE =================
os.makedirs("uploads", exist_ok=True)

conn = sqlite3.connect("marketplace.db", check_same_thread=False)
cur = conn.cursor()

# Pembuatan Tabel Utama
cur.execute("""CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT, nama TEXT, email TEXT, username TEXT UNIQUE, password TEXT, role TEXT)""")
cur.execute("""CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY AUTOINCREMENT, nama TEXT, kategori TEXT, harga INTEGER, gambar TEXT, owner TEXT)""")
cur.execute("""CREATE TABLE IF NOT EXISTS transaksi(id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, produk TEXT, total INTEGER, tanggal TEXT)""")
cur.execute("""CREATE TABLE IF NOT EXISTS chat(id INTEGER PRIMARY KEY AUTOINCREMENT, pengirim TEXT, role TEXT, pesan TEXT)""")
cur.execute("""CREATE TABLE IF NOT EXISTS ulasan(id INTEGER PRIMARY KEY AUTOINCREMENT, nama TEXT, bintang INTEGER, teks TEXT)""")
cur.execute("""CREATE TABLE IF NOT EXISTS profil_toko(id INTEGER PRIMARY KEY, nama TEXT, deskripsi TEXT, alamat TEXT, kontak TEXT)""")

# Isi default Profil Toko jika masih kosong
cek_profil = cur.execute("SELECT * FROM profil_toko WHERE id=1").fetchone()
if not cek_profil:
    try:
        cur.execute("INSERT INTO profil_toko (id, nama, deskripsi, alamat, kontak) VALUES (1, 'Bitha Butiq', 'Pusat Fashion Pria & Wanita Terbaik', 'Jl. Mawar No. 12, Jakarta', '0812-3456-7890')")
        conn.commit()
    except: pass

# Auto-upgrade Tabel
for col in ["email", "gambar", "owner", "kategori", "stok", "diskon", "warna", "ukuran", "tanggal", "status", "resi", "metode"]:
    try: cur.execute(f"ALTER TABLE {'users' if col=='email' else 'products' if col in ['gambar','owner','kategori','stok','diskon','warna','ukuran'] else 'transaksi'} ADD COLUMN {col} TEXT")
    except: pass
conn.commit()

# ================= SESSION STATE =================
defaults = {
    "login":False, "user":"", "nama":"", "email":"", "role":"",
    "cart":[], "wishlist":[], "cod_active": True, 
    "vouchers": {"BITHA10": 10, "BITHA20": 20, "GRATIS": 100},
    "edit_profil": False
}
for k,v in defaults.items():
    if k not in st.session_state: st.session_state[k] = v

if "nav_menu" not in st.session_state:
    st.session_state.nav_menu = "🛍️ Etalase Produk"

# ================= STYLE & CSS =================
st.set_page_config(page_title="Bitha Butiq", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
.stApp { background: #0f172a; color: white; }
[data-testid="stSidebar"] { background: #111827 !important; border-right: 1px solid #1e293b; }
div[role="radiogroup"] > label { background: #1e293b; padding: 12px 15px; border-radius: 12px; margin-bottom: 10px; border: 1px solid #334155; cursor: pointer; transition: all 0.3s; }
div[role="radiogroup"] > label:hover { background: #2563eb; border-color: #60a5fa; transform: translateX(5px); }
.title { text-align: center; font-size: 50px; font-weight: 800; color: #60a5fa; margin-bottom: 10px; text-shadow: 0px 4px 10px rgba(96, 165, 250, 0.3); }
.card { background: #1e293b; padding: 20px; border-radius: 18px; margin-bottom: 20px; border: 1px solid #334155; box-shadow: 0px 5px 15px rgba(0,0,0,0.4); transition: all 0.3s; }
.card:hover { transform: translateY(-5px); border-color: #3b82f6; }
.profil-banner { background: linear-gradient(90deg, #1e293b 0%, #0f172a 100%); padding: 25px; border-radius: 15px; border-left: 5px solid #3b82f6; margin-bottom: 25px; box-shadow: 0px 4px 10px rgba(0,0,0,0.3); }
.stButton>button { background: #2563eb; color: white; border-radius: 10px; font-weight: bold; border: none; padding: 10px; transition: all 0.3s; font-size: 15px; white-space: nowrap; }
.stButton>button:hover { background: #1d4ed8; transform: scale(1.03); }
.btn-beli button { background: #ea580c !important; font-size: 16px; }
.btn-beli button:hover { background: #c2410c !important; }
.btn-checkout button { background: #10b981 !important; font-size: 16px; margin-top: 10px;}
.btn-checkout button:hover { background: #059669 !important; }
.badge-diskon { background: #ef4444; color: white; padding: 3px 8px; border-radius: 5px; font-size: 12px; font-weight: bold; }
.keranjang-sidebar { background: #1e293b; padding: 15px; border-radius: 10px; border: 1px dashed #60a5fa; margin-bottom: 10px;}
.ulasan-card { background: #1e293b; padding: 15px; border-radius: 12px; border-left: 5px solid #fbbf24; margin-bottom: 15px; }
</style>
""", unsafe_allow_html=True)

# ================= LOGIN =================
def login_page():
    _, col_center, _ = st.columns([1, 1.5, 1])
    with col_center:
        st.markdown("<div class='title'>👗 Bitha Butiq</div>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:gray; margin-bottom:30px;'>Selamat datang di Butik Impian Anda</p>", unsafe_allow_html=True)
        with st.container(border=True):
            tab1,tab2 = st.tabs(["🔑 Login", "📝 Buat Akun"])
            with tab1:
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                if st.button("Masuk", use_container_width=True):
                    cur.execute("SELECT nama,email,username,role FROM users WHERE username=? AND password=?", (username, password))
                    data = cur.fetchone()
                    if data:
                        st.session_state.login, st.session_state.nama, st.session_state.email, st.session_state.user, st.session_state.role = True, data[0], data[1], data[2], data[3]
                        st.rerun()
                    else: st.error("Username atau Password salah!")
            with tab2:
                nama, email, role = st.text_input("Nama Lengkap"), st.text_input("Email"), st.selectbox("Daftar Sebagai", ["Pembeli","Penjual"])
                new_username, new_password, confirm = st.text_input("Username Baru"), st.text_input("Password Baru", type="password"), st.text_input("Konfirmasi Password", type="password")
                if st.button("Buat Akun", use_container_width=True):
                    if new_password == confirm and new_username:
                        try:
                            cur.execute("INSERT INTO users (nama,email,username,password,role) VALUES(?,?,?,?,?)", (nama, email, new_username, new_password, role))
                            conn.commit()
                            st.success("Akun berhasil dibuat! Silakan Login.")
                        except: st.error("Username sudah dipakai.")

# ================= APP UTAMA =================
def app():
    st.sidebar.markdown(f"<h2 style='text-align: center; color: #60a5fa;'>👋 Halo, {st.session_state.nama}!</h2>", unsafe_allow_html=True)
    st.sidebar.caption(f"<p style='text-align: center;'>Masuk sebagai: <b>{st.session_state.role}</b></p>", unsafe_allow_html=True)
    st.sidebar.markdown("---")

    # ================= KERANJANG DI SIDEBAR =================
    if st.session_state.role != "Penjual":
        st.sidebar.markdown("### 🛒 Isi Keranjang")
        if len(st.session_state.cart) > 0:
            st.sidebar.markdown("<div class='keranjang-sidebar'>", unsafe_allow_html=True)
            total_belanja = 0
            for item in st.session_state.cart:
                st.sidebar.write(f"🛍️ {item['nama']}")
                total_belanja += item['harga']
            
            st.sidebar.markdown("---")
            st.sidebar.markdown(f"<h4 style='color:#fbbf24; margin:0;'>Total Belanja: Rp {total_belanja:,}</h4>", unsafe_allow_html=True)
            st.sidebar.markdown("</div>", unsafe_allow_html=True)
            
            st.sidebar.markdown("<div class='btn-checkout'>", unsafe_allow_html=True)
            if st.sidebar.button("💳 Langsung Checkout ➔", use_container_width=True):
                st.session_state.nav_menu = "💳 Pembayaran"
                st.rerun()
            st.sidebar.markdown("</div>", unsafe_allow_html=True)
        else:
            st.sidebar.caption("Keranjang masih kosong.")
        st.sidebar.markdown("---")

    # Pilihan Menu
    if st.session_state.role == "Penjual":
        pilihan_menu = ["🛍️ Etalase Produk", "📦 Tambah Produk", "📋 Pesanan Masuk", "📢 Promo & Diskon", "📈 Laporan Penjualan", "💬 Chat Pembeli", "⭐ Ulasan Toko"]
    else:
        pilihan_menu = ["🛍️ Etalase Produk", "💳 Pembayaran", "📍 Status Pesanan", "❤️ Wishlist", "💬 Chat Penjual", "⭐ Beri Ulasan"]

    if st.session_state.nav_menu not in pilihan_menu:
        st.session_state.nav_menu = pilihan_menu[0]

    idx = pilihan_menu.index(st.session_state.nav_menu)
    menu = st.sidebar.radio("Navigasi Menu", pilihan_menu, index=idx, label_visibility="collapsed")
    
    if menu != st.session_state.nav_menu:
        st.session_state.nav_menu = menu
        st.rerun()

    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        for k,v in defaults.items(): st.session_state[k]=v
        st.rerun()

    # ================= 1. ETALASE & KELOLA PRODUK =================
    if menu == "🛍️ Etalase Produk":
        
        # --- FITUR PROFIL TOKO ---
        profil = cur.execute("SELECT nama, deskripsi, alamat, kontak FROM profil_toko WHERE id=1").fetchone()
        if profil:
            p_nama, p_desc, p_alamat, p_kontak = profil
        else:
            p_nama, p_desc, p_alamat, p_kontak = "Bitha Butiq", "Toko Fashion", "-", "-"
        
        st.markdown(f"""
        <div class='profil-banner'>
            <h1 style='color: #60a5fa; margin-top: 0;'>🏪 {p_nama}</h1>
            <p style='font-size: 16px; margin-bottom: 5px;'>📝 <i>{p_desc}</i></p>
            <p style='margin-bottom: 5px;'>📍 <b>Alamat:</b> {p_alamat}</p>
            <p style='margin-bottom: 0;'>📞 <b>Kontak:</b> {p_kontak}</p>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.role == "Penjual":
            if st.button("✏️ Edit Profil Toko"):
                st.session_state.edit_profil = not st.session_state.edit_profil
                st.rerun()
                
            if st.session_state.edit_profil:
                with st.container(border=True):
                    st.subheader("Edit Informasi Toko")
                    n_nama = st.text_input("Nama Toko", value=p_nama)
                    n_desc = st.text_area("Deskripsi Toko", value=p_desc)
                    n_alamat = st.text_area("Alamat Toko", value=p_alamat)
                    n_kontak = st.text_input("Nomor Kontak / WhatsApp", value=p_kontak)
                    if st.button("💾 Simpan Perubahan Profil", type="primary"):
                        cur.execute("UPDATE profil_toko SET nama=?, deskripsi=?, alamat=?, kontak=? WHERE id=1", (n_nama, n_desc, n_alamat, n_kontak))
                        conn.commit()
                        st.session_state.edit_profil = False
                        st.success("Profil Toko Berhasil Diperbarui!")
                        time.sleep(1)
                        st.rerun()
                st.markdown("<br>", unsafe_allow_html=True)
        # -------------------------------

        st.title("🛍️ Daftar Produk")
        cari = st.text_input("🔍 Cari Barang...")
        data = cur.execute("SELECT id, nama, kategori, harga, gambar, owner, stok, diskon, warna, ukuran FROM products").fetchall()
        cols = st.columns(3)
        i=0

        for p in data:
            pid, nama, kat, harga_asli, gambar, owner, stok, diskon, warna, ukuran = p
            if cari.lower() in nama.lower():
                harga_final = int(harga_asli - (harga_asli * diskon / 100))
                with cols[i%3]:
                    st.markdown("<div class='card'>", unsafe_allow_html=True)
                    if gambar and gambar != "None":
                        try: st.image(gambar, use_container_width=True)
                        except: pass
                    st.subheader(nama)
                    st.caption(f"Kategori: {kat} | Stok: {stok}")
                    if diskon > 0: st.markdown(f"<span class='badge-diskon'>Diskon {diskon}%</span> <strike style='color:gray; font-size:14px;'>Rp {harga_asli:,}</strike>", unsafe_allow_html=True)
                    st.markdown(f"<h3 style='color: #fbbf24; margin-top:0px;'>Rp {harga_final:,}</h3>", unsafe_allow_html=True)
                    st.caption(f"🎨 Warna: {warna} | 📏 Ukuran: {ukuran}")
                    st.markdown("<br>", unsafe_allow_html=True)

                    if st.session_state.role != "Penjual":
                        col_b, col_k, col_w = st.columns([3, 1, 1]) 
                        with col_b:
                            st.markdown("<div class='btn-beli'>", unsafe_allow_html=True)
                            if st.button("🛍️ Beli", key=f"b{pid}", use_container_width=True):
                                st.session_state.cart.append({"nama":nama, "harga":harga_final})
                                st.rerun() 
                            st.markdown("</div>", unsafe_allow_html=True)
                        with col_k:
                            if st.button("🛒", key=f"k{pid}", help="Masukkan Keranjang", use_container_width=True):
                                st.session_state.cart.append({"nama":nama, "harga":harga_final})
                                st.toast("Masuk keranjang!")
                                st.rerun() 
                        with col_w:
                            if st.button("❤️", key=f"w{pid}", help="Tambah ke Wishlist", use_container_width=True):
                                st.session_state.wishlist.append(nama)
                                st.toast("Masuk Wishlist!")

                    if st.session_state.role == "Penjual":
                        col_e, col_h = st.columns(2)
                        with col_e:
                            if st.button("✏️ Edit", key=f"e{pid}", use_container_width=True):
                                st.session_state[f"edit_mode_{pid}"] = not st.session_state.get(f"edit_mode_{pid}", False)
                                st.rerun()
                        with col_h:
                            if st.button("🗑️ Hapus", key=f"h{pid}", use_container_width=True):
                                cur.execute("DELETE FROM products WHERE id=?", (pid,))
                                conn.commit(); st.rerun()
                        
                        if st.session_state.get(f"edit_mode_{pid}", False):
                            st.markdown("---")
                            n_nama = st.text_input("Nama", value=nama, key=f"n{pid}")
                            n_harga = st.number_input("Harga", value=harga_asli, key=f"hg{pid}")
                            n_stok = st.number_input("Stok", value=stok, key=f"st{pid}")
                            n_diskon = st.slider("Diskon %", 0, 100, diskon, key=f"ds{pid}")
                            n_gambar = st.file_uploader("Ganti Gambar", type=["png","jpg"], key=f"gb{pid}")
                            if st.button("💾 Simpan Perubahan", key=f"sv{pid}", use_container_width=True):
                                if n_gambar:
                                    path = "uploads/" + n_gambar.name
                                    with open(path, "wb") as f: f.write(n_gambar.getbuffer())
                                    cur.execute("UPDATE products SET nama=?, harga=?, stok=?, diskon=?, gambar=? WHERE id=?", (n_nama, n_harga, n_stok, n_diskon, path, pid))
                                else:
                                    cur.execute("UPDATE products SET nama=?, harga=?, stok=?, diskon=? WHERE id=?", (n_nama, n_harga, n_stok, n_diskon, pid))
                                conn.commit(); st.session_state[f"edit_mode_{pid}"] = False; st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                i += 1

    # ================= 2. TAMBAH PRODUK =================
    elif menu == "📦 Tambah Produk":
        st.title("Tambah Produk Baru")
        with st.container(border=True):
            col1, col2 = st.columns(2)
            with col1:
                nama = st.text_input("Nama Produk")
                kategori = st.selectbox("Kategori", ["Pakaian Laki-laki", "Pakaian Perempuan", "Aksesoris"])
                harga = st.number_input("Harga Normal (Rp)", min_value=0)
                diskon = st.slider("Diskon Promosi (%)", 0, 100, 0)
            with col2:
                stok = st.number_input("Jumlah Stok", min_value=1, value=10)
                warna = st.text_input("Variasi Warna", placeholder="Hitam, Putih")
                ukuran = st.text_input("Variasi Ukuran", placeholder="S, M, L")
                gambar = st.file_uploader("Upload Gambar", type=["png","jpg","jpeg"])
            if st.button("Simpan Produk", use_container_width=True):
                path = "None"
                if gambar:
                    path = "uploads/" + gambar.name
                    with open(path,"wb") as f: f.write(gambar.getbuffer())
                cur.execute("INSERT INTO products (nama,kategori,harga,gambar,owner,stok,diskon,warna,ukuran) VALUES(?,?,?,?,?,?,?,?,?)", (nama, kategori, harga, path, st.session_state.user, stok, diskon, warna, ukuran))
                conn.commit(); st.success("✅ Produk ditambahkan!")

    # ================= 3. PESANAN MASUK (SELLER) =================
    elif menu == "📋 Pesanan Masuk":
        st.title("Manajemen Pesanan Pembeli")
        data_tx = cur.execute("SELECT id, tanggal, username, produk, total, status, resi, metode FROM transaksi ORDER BY id DESC").fetchall()
        
        tab1, tab2, tab3 = st.tabs(["Menunggu Konfirmasi", "Perlu Dikirim", "Telah Selesai/Dikirim"])
        
        for tx in data_tx:
            tid, tgl, usr, prd, tot, stat, resi, met = tx
            if stat == "Menunggu Konfirmasi": active_tab = tab1
            elif stat == "Dikemas": active_tab = tab2
            else: active_tab = tab3
            
            with active_tab:
                with st.container(border=True):
                    col_info, col_act = st.columns([2,1])
                    with col_info:
                        st.write(f"🏷️ **Order #{tid}** | 📅 {tgl}")
                        st.write(f"👤 **Pembeli:** {usr} | 💳 **Metode:** {met}")
                        st.write(f"📦 **Barang & Tujuan:** {prd}")
                        st.write(f"💰 **Total Tagihan: Rp {tot:,}**")
                        
                        if stat == "Menunggu Konfirmasi": progress = 25
                        elif stat == "Dikemas": progress = 50
                        elif stat == "Dikirim": progress = 80
                        else: progress = 100
                        st.progress(progress)
                        
                        st.markdown(f"Status Saat Ini: **<span style='color:#3b82f6;'>{stat}</span>**", unsafe_allow_html=True)
                        if resi != "-": st.info(f"Nomor Resi: **{resi}**")
                    
                    with col_act:
                        if stat == "Menunggu Konfirmasi":
                            if st.button("📦 Konfirmasi & Kemas", key=f"kemas_{tid}", use_container_width=True):
                                cur.execute("UPDATE transaksi SET status='Dikemas' WHERE id=?", (tid,))
                                conn.commit(); st.rerun()
                        elif stat == "Dikemas":
                            input_resi = st.text_input("Input Resi Pengiriman", key=f"in_resi_{tid}")
                            if st.button("🚚 Kirim Pesanan", key=f"kirim_{tid}", use_container_width=True):
                                if input_resi:
                                    cur.execute("UPDATE transaksi SET status='Dikirim', resi=? WHERE id=?", (input_resi, tid))
                                    conn.commit(); st.rerun()
                                else: st.warning("Masukkan nomor resi terlebih dahulu!")

    # ================= 4. PROMO & DISKON (SELLER) =================
    elif menu == "📢 Promo & Diskon":
        st.title("Voucher & Diskon Toko")
        with st.container(border=True):
            st.subheader("Buat Voucher Belanja")
            kode_baru = st.text_input("Kode Voucher Unik (Cth: MERDEKA20)")
            potongan = st.slider("Potongan Harga (%)", 1, 100, 10)
            if st.button("Aktifkan Voucher", use_container_width=True):
                st.session_state.vouchers[kode_baru] = potongan
                st.success(f"Voucher {kode_baru} berhasil diaktifkan dengan diskon {potongan}%!")
        st.markdown("**Voucher Aktif Saat Ini:**")
        st.write(st.session_state.vouchers)

    # ================= 5. LAPORAN PENJUALAN & DATA PENJUALAN (SELLER) =================
    elif menu == "📈 Laporan Penjualan":
        st.title("📈 Dashboard & Data Penjualan")
        
        # Ambil data transaksi secara lengkap
        data_report = cur.execute("SELECT id, tanggal, username, produk, total, status, metode FROM transaksi ORDER BY id DESC").fetchall()
        df_report = pd.DataFrame(data_report, columns=["ID Pesanan", "Tanggal", "Pembeli", "Produk", "Total (Rp)", "Status", "Metode Pembayaran"])
        
        if df_report.empty:
            st.info("Belum ada data transaksi yang dapat ditampilkan.")
        else:
            # Menghitung Metrik Utama
            total_pendapatan = df_report["Total (Rp)"].sum()
            total_order = len(df_report)
            
            # Ekstrak tanggal saja untuk perhitungan harian
            df_report['Tanggal_Only'] = pd.to_datetime(df_report['Tanggal'], errors='coerce').dt.date
            jumlah_hari_aktif = max(1, df_report["Tanggal_Only"].nunique())
            pendapatan_harian = int(total_pendapatan / jumlah_hari_aktif)
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Penjualan Keseluruhan", f"Rp {total_pendapatan:,}")
            col2.metric("Rata-Rata Omset Harian", f"Rp {pendapatan_harian:,}")
            col3.metric("Total Pesanan Masuk", f"{total_order} Order")
            
            st.markdown("---")
            
            # Grafik Penjualan Harian (MENGGUNAKAN DATA REAL DATABASE)
            st.markdown("### 📊 Tren Pendapatan Harian")
            df_grafik = df_report.groupby('Tanggal_Only')['Total (Rp)'].sum().reset_index()
            df_grafik.set_index('Tanggal_Only', inplace=True)
            
            if not df_grafik.empty:
                st.line_chart(df_grafik, use_container_width=True)
            else:
                st.caption("Data belum cukup untuk membuat grafik.")
            
            st.markdown("---")
            
            # Tabel Rincian Data Penjualan
            st.markdown("### 📋 Rincian Data Penjualan")
            
            # Fitur Pencarian & Filter
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                filter_status = st.multiselect("Filter Status Pesanan:", options=df_report["Status"].unique(), default=df_report["Status"].unique())
            with col_f2:
                cari_pembeli = st.text_input("🔍 Cari Username Pembeli:")
                
            # Terapkan Filter
            df_filtered = df_report[df_report["Status"].isin(filter_status)]
            if cari_pembeli:
                df_filtered = df_filtered[df_filtered["Pembeli"].str.contains(cari_pembeli, case=False, na=False)]
            
            # Format tampilan tabel agar uang ada pemisah ribuan
            df_tampilan = df_filtered.copy()
            df_tampilan["Total (Rp)"] = df_tampilan["Total (Rp)"].apply(lambda x: f"Rp {x:,}")
            df_tampilan = df_tampilan.drop(columns=['Tanggal_Only']) # Sembunyikan kolom bantuan
            
            st.dataframe(df_tampilan, use_container_width=True, hide_index=True)
            
            # Fitur Export/Download Data CSV
            @st.cache_data
            def convert_df(df):
                return df.to_csv(index=False).encode('utf-8')
                
            csv = convert_df(df_filtered.drop(columns=['Tanggal_Only'], errors='ignore'))
            
            st.download_button(
                label="📥 Download Data Penjualan (CSV)",
                data=csv,
                file_name=f"Data_Penjualan_Butiq_{datetime.today().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                type="primary"
            )

    # ================= 6. CHECKOUT & PEMBAYARAN (BUYER) =================
    elif menu == "💳 Pembayaran":
        st.title("💳 Pembayaran & Pengiriman")
        total_belanja = sum([item['harga'] for item in st.session_state.cart])
        
        for idx, item in enumerate(st.session_state.cart):
            with st.container(border=True):
                col1, col2 = st.columns([5,1])
                with col1:
                    st.write(f"📦 **{item['nama']}** - Rp {item['harga']:,}")
                with col2:
                    if st.button("❌ Hapus", key=f"del_{idx}"):
                        st.session_state.cart.pop(idx)
                        st.rerun() 
        st.markdown("---")
        
        if total_belanja > 0:
            col_kiri, col_kanan = st.columns([1.2, 1])
            
            with col_kiri:
                st.subheader("📍 Alamat & Pengiriman")
                alamat = st.text_area("Alamat Lengkap", placeholder="Jln. Mawar No. 12, RT/RW...")
                kota = st.text_input("Kota Tujuan", placeholder="Cth: Jakarta, Bandung, Surabaya...")
                
                ongkos_kirim = 0
                if kota and alamat:
                    random.seed(kota.strip().lower())
                    ongkos_kirim = random.randint(10, 50) * 1000
                    random.seed() 
                    st.success(f"🚚 Ongkos kirim ke **{kota.title()}**: Rp {ongkos_kirim:,}")
                
                st.subheader("💳 Opsi Bayar & Voucher")
                opsi_metode = ["Transfer Bank", "E-Wallet (GoPay/OVO/Dana)"]
                if st.session_state.cod_active: opsi_metode.append("COD (Bayar di Tempat)")
                metode_bayar = st.selectbox("Pilih Metode Pembayaran", opsi_metode)
                
                input_voucher = st.text_input("Gunakan Kode Voucher", placeholder="Contoh: BITHA10")
                diskon_voucher = st.session_state.vouchers.get(input_voucher.upper(), 0)
                if diskon_voucher > 0: st.success(f"Voucher Berhasil! Diskon {diskon_voucher}% diterapkan.")
                
            with col_kanan:
                st.subheader("Rincian Tagihan")
                potongan_harga = int(total_belanja * (diskon_voucher / 100))
                total_akhir = total_belanja - potongan_harga + ongkos_kirim
                
                st.write(f"Total Produk: Rp {total_belanja:,}")
                st.write(f"Diskon Voucher: - Rp {potongan_harga:,}")
                st.write(f"Ongkos Kirim: + Rp {ongkos_kirim:,}")
                st.markdown(f"### Total Bayar: Rp {total_akhir:,}")
                
                if not kota or not alamat:
                    st.warning("⚠️ Silakan isi Alamat Lengkap dan Kota Tujuan agar ongkir muncul secara otomatis.")
                else:
                    if st.button("💳 Konfirmasi Pembayaran", use_container_width=True, type="primary"):
                        produk_list = ", ".join([i['nama'] for i in st.session_state.cart])
                        produk_dan_tujuan = f"{produk_list} (Tujuan: {kota.title()})"
                        
                        tgl_skrg = datetime.today().strftime('%Y-%m-%d %H:%M')
                        cur.execute("INSERT INTO transaksi (username, produk, total, tanggal, status, resi, metode) VALUES (?, ?, ?, ?, 'Menunggu Konfirmasi', '-', ?)", (st.session_state.user, produk_dan_tujuan, total_akhir, tgl_skrg, metode_bayar))
                        conn.commit()
                        
                        st.session_state.cart = []
                        st.balloons()
                        st.success("🎉 Pesanan Berhasil Dibuat! Silakan cek menu 'Status Pesanan'.")
                        
                        time.sleep(2)
                        st.session_state.nav_menu = "📍 Status Pesanan"
                        st.rerun()
        else:
            st.info("Keranjang Anda masih kosong. Yuk belanja dulu!")

    # ================= 7. STATUS PESANAN (BUYER) =================
    elif menu == "📍 Status Pesanan":
        st.title("Lacak Pesanan Anda")
        my_orders = cur.execute("SELECT id, tanggal, produk, total, status, resi, metode FROM transaksi WHERE username=? ORDER BY id DESC", (st.session_state.user,)).fetchall()
        
        if not my_orders:
            st.info("Anda belum memiliki riwayat pesanan.")
        else:
            for ord in my_orders:
                oid, otgl, oprd, otot, ostat, oresi, omet = ord
                with st.container(border=True):
                    st.write(f"**Tanggal:** {otgl} | **Metode:** {omet}")
                    st.write(f"**Produk:** {oprd} | **Total Tagihan:** Rp {otot:,}")
                    
                    if ostat == "Menunggu Konfirmasi": progress = 25
                    elif ostat == "Dikemas": progress = 50
                    elif ostat == "Dikirim": progress = 80
                    else: progress = 100
                    
                    st.progress(progress)
                    st.markdown(f"Status Saat Ini: **<span style='color:#3b82f6;'>{ostat}</span>**", unsafe_allow_html=True)
                    
                    if oresi != "-":
                        st.info(f"Nomor Resi: **{oresi}**")
                        if ostat == "Dikirim":
                            if st.button("✅ Pesanan Diterima", key=f"terima_{oid}", use_container_width=True):
                                cur.execute("UPDATE transaksi SET status='Selesai' WHERE id=?", (oid,))
                                conn.commit(); st.rerun()

    # ================= 8. CHAT & ULASAN =================
    elif menu in ["💬 Chat Pembeli", "💬 Chat Penjual"]:
        st.title("Pesan In-App")
        st.markdown("---")
        
        riwayat_chat = cur.execute("SELECT pengirim, role, pesan FROM chat").fetchall()
        for chat in riwayat_chat:
            with st.chat_message(chat[1]): 
                st.write(f"**{chat[0]}:** {chat[2]}")
                
        prompt = st.chat_input("Ketik pesan Anda...")
        if prompt:
            role_sender = "assistant" if st.session_state.role == "Penjual" else "user"
            cur.execute("INSERT INTO chat (pengirim, role, pesan) VALUES (?, ?, ?)", (st.session_state.nama, role_sender, prompt))
            conn.commit()
            st.rerun()

    elif menu == "⭐ Ulasan Toko":
        st.title("Rating & Ulasan Pelanggan")
        data_ulasan = cur.execute("SELECT nama, bintang, teks FROM ulasan ORDER BY id DESC").fetchall()
        if not data_ulasan:
            st.info("Belum ada ulasan dari pembeli.")
        else:
            for u in data_ulasan:
                st.markdown(f"""
                <div class='ulasan-card'>
                    <h4 style='color:#fbbf24; margin-top:0;'>{'⭐'*u[1]}</h4>
                    <p style='margin: 0; font-weight: bold;'>👤 {u[0]}</p>
                    <p style='margin: 5px 0 0 0; font-style: italic;'>"{u[2]}"</p>
                </div>
                """, unsafe_allow_html=True)

    elif menu == "⭐ Beri Ulasan":
        st.title("Beri Ulasan Pembelian")
        with st.container(border=True):
            rating = st.slider("Bintang Penilaian:", 1, 5, 5)
            ulasan = st.text_area("Tulis pengalaman belanja Anda:")
            if st.button("Kirim Ulasan", use_container_width=True):
                cur.execute("INSERT INTO ulasan (nama, bintang, teks) VALUES (?, ?, ?)", (st.session_state.nama, rating, ulasan))
                conn.commit()
                st.success("Ulasan berhasil terkirim! Terima kasih.")
                
    elif menu == "❤️ Wishlist":
        st.title("Daftar Keinginan (Wishlist)")
        for item in st.session_state.wishlist: 
            st.markdown(f"<div style='background: #1e293b; padding: 15px; border-radius: 10px; margin-bottom: 10px;'>✨ <b>{item}</b></div>", unsafe_allow_html=True)

# ================= RUN UTAMA =================
if st.session_state.login: app()
else: login_page()