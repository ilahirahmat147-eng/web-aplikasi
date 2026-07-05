import streamlit as st
import sqlite3
import pandas as pd
import os
import random
import time
from datetime import datetime

# ================= INTERFASIS / SELEKSI CABANG TOKO =================
if "cabang" not in st.session_state:
    st.session_state.cabang = "Pusat (Bitha Butiq)"

# Dropdown Pemilihan Aplikasi/Cabang di Sidebar paling atas
st.sidebar.markdown("### 🏢 Pilih Toko / Cabang")
pilihan_cabang = st.sidebar.selectbox(
    "Cabang", 
    ["Pusat (Bitha Butiq)", "Cabang (Bitha Fashion)"], 
    label_visibility="collapsed"
)

if pilihan_cabang != st.session_state.cabang:
    st.session_state.cabang = pilihan_cabang
    # Reset navigasi menu agar tidak bentrok saat pindah cabang
    st.session_state.nav_menu = "🛍️ Etalase Produk"
    st.rerun()

# Konfigurasi Dinamis Berdasarkan Cabang yang Dipilih
if st.session_state.cabang == "Pusat (Bitha Butiq)":
    nama_toko_default = "Bitha Butiq"
    db_id = 1
    theme_bg = "#0f172a"
    theme_sidebar = "#111827"
    theme_border = "#1e293b"
    theme_hover = "#2563eb"
    theme_text_accent = "#60a5fa"
    theme_card = "#1e293b"
    theme_banner = "linear-gradient(90deg, #1e293b 0%, #0f172a 100%)"
else:
    nama_toko_default = "Bitha Fashion cabang"
    db_id = 2  # ID dibedakan agar profil toko di database tidak tumpang tindih
    theme_bg = "#0a0a0a"
    theme_sidebar = "#000000"
    theme_border = "#3f0000"
    theme_hover = "#dc2626"
    theme_text_accent = "#ef4444"
    theme_card = "#121212"
    theme_banner = "linear-gradient(90deg, #450a0a 0%, #000000 100%)"

# ================= DATABASE & AUTO-UPGRADE =================
os.makedirs("uploads", exist_ok=True)
conn = sqlite3.connect("marketplace.db", check_same_thread=False)
cur = conn.cursor()

# Pembuatan Tabel Utama
cur.execute("""CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT, nama TEXT, email TEXT, username TEXT UNIQUE, password TEXT, role TEXT)""")
cur.execute("""CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY AUTOINCREMENT, nama TEXT, kategori TEXT, harga INTEGER, gambar TEXT, owner TEXT, cabang TEXT)""")
cur.execute("""CREATE TABLE IF NOT EXISTS transaksi(id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, produk TEXT, total INTEGER, tanggal TEXT, cabang TEXT)""")
cur.execute("""CREATE TABLE IF NOT EXISTS chat(id INTEGER PRIMARY KEY AUTOINCREMENT, pengirim TEXT, role TEXT, pesan TEXT, cabang TEXT)""")
cur.execute("""CREATE TABLE IF NOT EXISTS ulasan(id INTEGER PRIMARY KEY AUTOINCREMENT, nama TEXT, bintang INTEGER, teks TEXT, cabang TEXT)""")
cur.execute("""CREATE TABLE IF NOT EXISTS profil_toko(id INTEGER PRIMARY KEY, nama TEXT, deskripsi TEXT, alamat TEXT, kontak TEXT)""")

# Isi default Profil Toko jika masih kosong
cek_profil = cur.execute("SELECT * FROM profil_toko WHERE id=?", (db_id,)).fetchone()
if not cek_profil:
    try:
        cur.execute("INSERT INTO profil_toko (id, nama, deskripsi, alamat, kontak) VALUES (?, ?, 'Pusat Fashion Pria & Wanita Terbaik', 'Jl. Mawar No. 12, Jakarta', '0812-3456-7890')", (db_id, nama_toko_default))
        conn.commit()
    except: pass

# Auto-upgrade Tabel
for col in ["email", "gambar", "owner", "kategori", "stok", "diskon", "warna", "ukuran", "tanggal", "status", "resi", "metode", "cabang"]:
    try: 
        if col == "email":
            cur.execute("ALTER TABLE users ADD COLUMN email TEXT")
        elif col in ['gambar','owner','kategori','stok','diskon','warna','ukuran', 'cabang']:
            cur.execute(f"ALTER TABLE products ADD COLUMN {col} TEXT")
        elif col in ['tanggal', 'status', 'resi', 'metode', 'cabang']:
            cur.execute(f"ALTER TABLE transaksi ADD COLUMN {col} TEXT")
        elif col == "cabang":
            cur.execute("ALTER TABLE chat ADD COLUMN cabang TEXT")
            cur.execute("ALTER TABLE ulasan ADD COLUMN cabang TEXT")
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

# ================= STYLE & CSS INJEKSI OTOMATIS =================
st.set_page_config(page_title=nama_toko_default, layout="wide", initial_sidebar_state="expanded")

st.markdown(f"""
<style>
.stApp {{ background: {theme_bg}; color: white; }}
[data-testid="stSidebar"] {{ background: {theme_sidebar} !important; border-right: 1px solid {theme_border}; }}
div[role="radiogroup"] > label {{ background: {theme_card}; padding: 12px 15px; border-radius: 12px; margin-bottom: 10px; border: 1px solid {theme_border}; cursor: pointer; transition: all 0.3s; color: white; }}
div[role="radiogroup"] > label:hover {{ background: {theme_hover}; border-color: {theme_text_accent}; transform: translateX(5px); }}
.title {{ text-align: center; font-size: 50px; font-weight: 800; color: {theme_text_accent}; margin-bottom: 10px; text-shadow: 0px 4px 10px rgba(96, 165, 250, 0.3); }}
.card {{ background: {theme_card}; padding: 20px; border-radius: 18px; margin-bottom: 20px; border: 1px solid {theme_border}; box-shadow: 0px 5px 15px rgba(0,0,0,0.4); transition: all 0.3s; }}
.card:hover {{ transform: translateY(-5px); border-color: {theme_hover}; }}
.profil-banner {{ background: {theme_banner}; padding: 25px; border-radius: 15px; border-left: 5px solid {theme_text_accent}; margin-bottom: 25px; box-shadow: 0px 4px 10px rgba(0,0,0,0.3); }}
.stButton>button {{ background: {theme_hover}; color: white; border-radius: 10px; font-weight: bold; border: none; padding: 10px; transition: all 0.3s; font-size: 15px; white-space: nowrap; }}
.stButton>button:hover {{ background: {theme_hover}; transform: scale(1.03); }}
.btn-beli button {{ background: #ea580c !important; font-size: 16px; }}
.btn-beli button:hover {{ background: #c2410c !important; }}
.btn-checkout button {{ background: {theme_text_accent} !important; font-size: 16px; margin-top: 10px;}}
.btn-checkout button:hover {{ background: {theme_hover} !important; }}
.badge-diskon {{ background: #ef4444; color: white; padding: 3px 8px; border-radius: 5px; font-size: 12px; font-weight: bold; }}
.keranjang-sidebar {{ background: {theme_card}; padding: 15px; border-radius: 10px; border: 1px dashed {theme_text_accent}; margin-bottom: 10px;}}
.ulasan-card {{ background: {theme_card}; padding: 15px; border-radius: 12px; border-left: 5px solid #fbbf24; margin-bottom: 15px; }}
</style>
""", unsafe_allow_html=True)

# ================= LOGIN =================
def login_page():
    _, col_center, _ = st.columns([1, 1.5, 1])
    with col_center:
        st.markdown(f"<div class='title'>👗 {nama_toko_default}</div>", unsafe_allow_html=True)
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
    st.sidebar.markdown(f"<h2 style='text-align: center; color: {theme_text_accent};'>👋 Halo, {st.session_state.nama}!</h2>", unsafe_allow_html=True)
    st.sidebar.caption(f"<p style='text-align: center;'>Masuk sebagai: <b>{st.session_state.role}</b> ({st.session_state.cabang})</p>", unsafe_allow_html=True)
    st.sidebar.markdown("---")

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
        profil = cur.execute("SELECT nama, deskripsi, alamat, kontak FROM profil_toko WHERE id=?", (db_id,)).fetchone()
        p_nama, p_desc, p_alamat, p_kontak = profil if profil else (nama_toko_default, "Toko Fashion", "-", "-")
        
        st.markdown(f"""
        <div class='profil-banner'>
            <h1 style='color: {theme_text_accent}; margin-top: 0;'>🏪 {p_nama}</h1>
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
                        cur.execute("UPDATE profil_toko SET nama=?, deskripsi=?, alamat=?, kontak=? WHERE id=?", (n_nama, n_desc, n_alamat, n_kontak, db_id))
                        conn.commit()
                        st.session_state.edit_profil = False
                        st.success("Profil Toko Berhasil Diperbarui!")
                        time.sleep(1)
                        st.rerun()

        st.title("🛍️ Daftar Produk")
        cari = st.text_input("🔍 Cari Barang...")
        
        # FILTER PRODUK BERDASARKAN CABANG YANG SEDANG DIBUKA
        data = cur.execute("SELECT id, nama, kategori, harga, gambar, owner, stok, diskon, warna, ukuran FROM products WHERE cabang=?", (st.session_state.cabang,)).fetchall()
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
                            if st.button("🛒", key=f"k{pid}", use_container_width=True):
                                st.session_state.cart.append({"nama":nama, "harga":harga_final})
                                st.toast("Masuk keranjang!")
                                st.rerun() 
                        with col_w:
                            if st.button("❤️", key=f"w{pid}", use_container_width=True):
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
                            if st.button("💾 Simpan", key=f"sv{pid}", use_container_width=True):
                                cur.execute("UPDATE products SET nama=?, harga=?, stok=?, diskon=? WHERE id=?", (n_nama, n_harga, n_stok, n_diskon, pid))
                                conn.commit(); st.session_state[f"edit_mode_{pid}"] = False; st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                i += 1

    # ================= 2. TAMBAH PRODUK =================
    elif menu == "📦 Tambah Produk":
        st.title(f"Tambah Produk Baru ({st.session_state.cabang})")
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
                # MENYIMPAN INFORMASI CABANG
                cur.execute("INSERT INTO products (nama,kategori,harga,gambar,owner,stok,diskon,warna,ukuran,cabang) VALUES(?,?,?,?,?,?,?,?,?,?)", (nama, kategori, harga, path, st.session_state.user, stok, diskon, warna, ukuran, st.session_state.cabang))
                conn.commit(); st.success("✅ Produk ditambahkan ke cabang ini!")

    # ================= 3. PESANAN MASUK =================
    elif menu == "📋 Pesanan Masuk":
        st.title("Manajemen Pesanan Pembeli")
        data_tx = cur.execute("SELECT id, tanggal, username, produk, total, status, resi, metode FROM transaksi WHERE cabang=? ORDER BY id DESC", (st.session_state.cabang,)).fetchall()
        
        tab1, tab2, tab3 = st.tabs(["Menunggu Konfirmasi", "Perlu Dikirim", "Telah Selesai/Dikirim"])
        for tx in data_tx:
            tid, tgl, usr, prd, tot, stat, resi, met = tx
            active_tab = tab1 if stat == "Menunggu Konfirmasi" else tab2 if stat == "Dikemas" else tab3
            with active_tab:
                with st.container(border=True):
                    st.write(f"🏷️ **Order #{tid}** | 📅 {tgl} | 👤 Pembeli: {usr}")
                    st.write(f"📦 **Barang:** {prd} | 💰 **Total: Rp {tot:,}**")
                    if stat == "Menunggu Konfirmasi" and st.button("📦 Konfirmasi & Kemas", key=f"km_{tid}"):
                        cur.execute("UPDATE transaksi SET status='Dikemas' WHERE id=?", (tid,))
                        conn.commit(); st.rerun()
                    elif stat == "Dikemas":
                        input_resi = st.text_input("Input Resi", key=f"res_{tid}")
                        if st.button("🚚 Kirim", key=f"kr_{tid}") and input_resi:
                            cur.execute("UPDATE transaksi SET status='Dikirim', resi=? WHERE id=?", (input_resi, tid))
                            conn.commit(); st.rerun()

    # ================= 4. PROMO & DISKON =================
    elif menu == "📢 Promo & Diskon":
        st.title("Voucher & Diskon Toko")
        with st.container(border=True):
            kode_baru = st.text_input("Kode Voucher Unik")
            potongan = st.slider("Potongan Harga (%)", 1, 100, 10)
            if st.button("Aktifkan Voucher"):
                st.session_state.vouchers[kode_baru] = potongan
                st.success(f"Voucher {kode_baru} Aktif!")

    # ================= 5. LAPORAN PENJUALAN =================
    elif menu == "📈 Laporan Penjualan":
        st.title("📈 Dashboard Data Penjualan")
        data_report = cur.execute("SELECT id, tanggal, username, produk, total, status, metode FROM transaksi WHERE cabang=?", (st.session_state.cabang,)).fetchall()
        df_report = pd.DataFrame(data_report, columns=["ID Pesanan", "Tanggal", "Pembeli", "Produk", "Total (Rp)", "Status", "Metode"])
        if df_report.empty:
            st.info("Belum ada data transaksi di cabang ini.")
        else:
            st.metric("Total Penjualan", f"Rp {df_report['Total (Rp)'].sum():,}")
            st.dataframe(df_report, use_container_width=True)

    # ================= 6. PEMBAYARAN =================
    elif menu == "💳 Pembayaran":
        st.title("💳 Pembayaran & Pengiriman")
        total_belanja = sum([item['harga'] for item in st.session_state.cart])
        if total_belanja > 0:
            alamat = st.text_area("Alamat Lengkap")
            kota = st.text_input("Kota Tujuan")
            metode_bayar = st.selectbox("Metode", ["Transfer Bank", "COD"])
            if st.button("💳 Konfirmasi Pembayaran") and kota and alamat:
                produk_list = ", ".join([i['nama'] for i in st.session_state.cart])
                tgl_skrg = datetime.today().strftime('%Y-%m-%d %H:%M')
                cur.execute("INSERT INTO transaksi (username, produk, total, tanggal, status, resi, metode, cabang) VALUES (?, ?, ?, ?, 'Menunggu Konfirmasi', '-', ?, ?)", 
                            (st.session_state.user, produk_list, total_belanja, tgl_skrg, metode_bayar, st.session_state.cabang))
                conn.commit(); st.session_state.cart = []; st.success("🎉 Pesanan Berhasil!"); time.sleep(1); st.rerun()
        else:
            st.info("Keranjang kosong.")

    # ================= 7. LAIN-LAIN (CHATS & REVIEWS) =================
    elif menu in ["💬 Chat Pembeli", "💬 Chat Penjual"]:
        st.title("Pesan In-App")
        riwayat_chat = cur.execute("SELECT pengirim, role, pesan FROM chat WHERE cabang=?", (st.session_state.cabang,)).fetchall()
        for chat in riwayat_chat:
            with st.chat_message(chat[1]): st.write(f"**{chat[0]}:** {chat[2]}")
        prompt = st.chat_input("Ketik pesan...")
        if prompt:
            role_sender = "assistant" if st.session_state.role == "Penjual" else "user"
            cur.execute("INSERT INTO chat (pengirim, role, pesan, cabang) VALUES (?, ?, ?, ?)", (st.session_state.nama, role_sender, prompt, st.session_state.cabang))
            conn.commit(); st.rerun()

    elif menu == "⭐ Ulasan Toko" or menu == "⭐ Beri Ulasan":
        st.title("Ulasan Cabang")
        if st.session_state.role == "Pembeli":
            rating = st.slider("Bintang:", 1, 5, 5)
            ulasan = st.text_area("Tulis Ulasan:")
            if st.button("Kirim"):
                cur.execute("INSERT INTO ulasan (nama, bintang, teks, cabang) VALUES (?, ?, ?, ?)", (st.session_state.nama, rating, ulasan, st.session_state.cabang))
                conn.commit(); st.success("Terima kasih!")
        else:
            data_ulasan = cur.execute("SELECT nama, bintang, teks FROM ulasan WHERE cabang=?", (st.session_state.cabang,)).fetchall()
            for u in data_ulasan: st.write(f"👤 {u[0]} - {'⭐'*u[1]} : *{u[2]}*")

    elif menu == "❤️ Wishlist":
        st.title("Daftar Keinginan")
        for item in st.session_state.wishlist: st.write(f"✨ {item}")

# ================= RUN UTAMA =================
if st.session_state.login: app()
else: login_page()
