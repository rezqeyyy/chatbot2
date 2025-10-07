import streamlit as st
from streamlit_option_menu import option_menu
import google.generativeai as genai
import os, datetime, math, json, re
from supabase import create_client, Client

# --------------------------------------------------
# PENGATURAN HALAMAN & CSS
# --------------------------------------------------
st.set_page_config(
    page_title="Asisten Bisnis AI",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_custom_css():
    st.markdown("""
<style>
/* ===== FONT & TAMPILAN DASAR ===== */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ===== SIDEBAR DENGAN FLEXBOX ===== */
[data-testid="stSidebar"] > div:first-child {
    display: flex;
    flex-direction: column;
    height: 95vh;
}
.menu-wrapper { flex-grow: 1; }
.sidebar-footer { margin-top: auto; padding-top: 1rem; }

/* ===== KONTEN UTAMA ===== */
.block-container { padding: 2rem; }
h1 { font-size: 2.25rem; font-weight: 700; }

/* ===== TAMPILAN CHAT ===== */
.chat-wrapper { display: flex; flex-direction: column; gap: 1rem; }
.message-container { display: flex; align-items: flex-end; gap: 10px; }
.message-container.user { justify-content: flex-end; }
.message-container.ai { justify-content: flex-start; }
.avatar { width: 32px; height: 32px; border-radius: 50%; background-color: #4B5563; display: flex; align-items: center; justify-content: center; font-weight: 600; color: white; flex-shrink: 0; }
.text-container { display: flex; flex-direction: column; }
.message-container.user .text-container { align-items: flex-end; }
.message-container.ai .text-container { align-items: flex-start; }
.sender-name { font-size: 0.8rem; color: #9CA3AF; margin: 0 0.75rem 0.2rem; }
.chat-bubble { padding: 0.8rem 1.2rem; line-height: 1.6; display: inline-block; max-width: 100%; position: relative; background: #374151; color: #F9FAFB; border-radius: 1rem; }

/* ===== BLOK INFO PENGGUNA DI SIDEBAR ===== */
.user-block { margin-bottom: 0.5rem; }
.user-info { display: flex; align-items: center; gap: 12px; padding: 12px; background-color: rgba(255, 255, 255, 0.05); border-radius: 10px; border: 1px solid rgba(255, 255, 255, 0.1); }
.user-avatar { width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(135deg, #FF6B6B, #FF8E53); display: flex; align-items: center; justify-content: center; font-weight: 700; color: white; font-size: 1.1rem; flex-shrink: 0; }
.user-email { font-size: 0.9rem; color: #E5E7EB; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

/* ===== [BARU] DESAIN RESPONSIVE UNTUK MOBILE ===== */
@media (max-width: 768px) {
    /* Perkecil padding utama di layar kecil */
    .block-container {
        padding: 1rem;
    }
    /* Perkecil ukuran judul */
    h1 {
        font-size: 1.8rem;
    }
    /* Buat kolom di "Catatan Bisnis" menjadi vertikal */
    .responsive-columns > [data-testid="stHorizontalBlock"] {
        flex-direction: column;
    }
    /* Perkecil padding di chat bubble */
    .chat-bubble {
        padding: 0.7rem 1rem;
    }
}
</style>
    """, unsafe_allow_html=True)

load_custom_css()

# --------------------------------------------------
# KONFIGURASI API & KONEKSI (Tetap sama)
# --------------------------------------------------
GEMINI_API_KEY = "AIzaSyCv1CwT5pWAF-fkj5nHjIrryu6F2gZeL9c" #
SUPABASE_URL = "https://mmacplzzdrpezpfremul.supabase.co" #
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1tYWNwbHp6ZHJwZXpwZnJlbXVsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTkxNDYzMDUsImV4cCI6MjA3NDcyMjMwNX0.h7HMd8xYBz7RnxE1-G5RmowX_-Gn1u_l7NVEFDVwrOg" #

try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"Konfigurasi API gagal: {e}")
    st.stop()

# --- PEMULIHAN SESI LOGIN (Tetap sama) ---
if 'user' not in st.session_state: st.session_state.user = None
if st.session_state.user:
    try:
        supabase.auth.set_session(st.session_state.user.session.access_token, st.session_state.user.session.refresh_token)
    except Exception:
        st.session_state.user = None

# --- FUNGSI-FUNGSI FITUR ---

def fitur_konsultasi(): # (Fungsi ini tetap sama dari sebelumnya)
    st.title("💬 Konsultasi Bisnis")
    st.markdown("Ajukan pertanyaan apa pun seputar bisnis kepada Konsultan AI.")
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "ai", "name": "Konsultan AI", "content": "Halo! Saya Konsultan AI Anda. Ada yang bisa saya bantu seputar bisnis hari ini?"}]
    st.markdown('<div class="chat-wrapper">', unsafe_allow_html=True)
    for message in st.session_state.messages:
        role = message["role"]
        avatar_char = "🤖" if role == "ai" else "🧑‍💻"
        container_html = f'<div class="message-container {role}">'
        avatar_html = f'<div class="avatar">{avatar_char}</div>'
        text_html = f'<div class="text-container"><div class="sender-name">{message["name"]}</div><div class="chat-bubble {role}">{message["content"]}</div></div>'
        if role == 'ai': st.markdown(container_html + avatar_html + text_html + '</div>', unsafe_allow_html=True)
        else: st.markdown(container_html + text_html + avatar_html + '</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    if prompt := st.chat_input("Tulis pertanyaan Anda…"):
        st.session_state.messages.append({"role": "user", "name": "Anda", "content": prompt})
        st.rerun()
    if st.session_state.messages[-1]["role"] == "user":
        with st.spinner("AI sedang berpikir..."):
            try:
                user_prompt = st.session_state.messages[-1]["content"]
                SYSTEM_PROMPT = """
                Anda adalah seorang konsultan bisnis AI yang ahli dan ramah.
                PERATURAN UTAMA:
                1. Fokus utama Anda adalah topik bisnis: marketing, keuangan, operasional, strategi, ide bisnis, dll.
                2. Anda WAJIB merespons sapaan dan basa-basi singkat (seperti "halo", "hai", "terima kasih", "selamat pagi") dengan ramah dan natural. Setelah merespons, arahkan kembali percakapan ke topik bisnis.
                3. Untuk pertanyaan yang lebih mendalam dan JELAS di luar topik bisnis (misalnya "resep masakan", "ceritakan sebuah lelucon"), Anda HARUS menolak dengan sopan.
                """
                final_prompt = f"{SYSTEM_PROMPT}\n\nRiwayat Percakapan Sejauh Ini:\n{json.dumps(st.session_state.messages[-5:])}\n\nPertanyaan Baru Pengguna: {user_prompt}"
                response = model.generate_content(final_prompt)
                ai_response = response.text
            except Exception as e: ai_response = f"Terjadi kesalahan: {e}"
            st.session_state.messages.append({"role": "ai", "name": "Konsultan AI", "content": ai_response})
            st.rerun()
        
# --- [MODIFIKASI] FUNGSI REKOMENDASI DENGAN PERTANYAAN BARU ---
def fitur_rekomendasi():
    st.title("💡 Rekomendasi Bisnis")
    st.markdown("Isi formulir di bawah ini untuk mendapatkan ide bisnis yang dipersonalisasi.")
    with st.container(border=True):
        with st.form("rec_form"):
            st.subheader("Profil Calon Pebisnis")
            
            # Pertanyaan baru
            modal = st.text_input(
                "Berapa modal awal yang Anda siapkan?",
                placeholder="Contoh: di bawah 5 juta, 5–10 juta, >10 juta"
            )
            minat = st.text_input(
                "Apa minat atau hobi utama Anda?",
                placeholder="Contoh: memasak, fashion, teknologi, olahraga, dll"
            )
            keahlian = st.text_input(
                "Apa keahlian spesifik yang Anda miliki?",
                placeholder="Contoh: desain grafis, masak, jualan online, komunikasi"
            )
            waktu = st.text_input(
                "Berapa waktu luang Anda per minggu?",
                placeholder="Contoh: <10 jam, 10–20 jam, full-time"
            )
            lokasi = st.text_input(
                "Di mana Anda berencana menjalankan usaha ini?",
                placeholder="Contoh: online, rumah, toko, pasar, food court"
            )
            target_pembeli = st.text_input(
                "Siapa calon pembeli utama yang Anda tuju?",
                placeholder="Contoh: mahasiswa, pekerja kantoran, ibu rumah tangga, remaja"
            )
            jenis_produk = st.text_input(
                "Produk atau jasa seperti apa yang paling ingin Anda coba jual?",
                placeholder="Contoh: makanan, pakaian, jasa, produk digital"
            )
            tim = st.text_input(
                "Apakah Anda ingin usaha ini dijalankan sendiri atau bersama tim/partner?",
                placeholder="Sendiri / Partner / Keluarga"
            )
            harapan_profit = st.text_input(
                "Seberapa cepat Anda berharap usaha ini bisa mulai menghasilkan keuntungan?",
                placeholder="Contoh: segera dalam 1–2 bulan, jangka menengah 3–6 bulan, jangka panjang >6 bulan"
            )
            tujuan = st.text_input(
                "Apa tujuan utama Anda berbisnis?",
                placeholder="Contoh: tambahan penghasilan, usaha utama, menyalurkan passion"
            )

            if st.form_submit_button("🚀 Berikan Saya Ide!", use_container_width=True):
                # Validasi untuk semua input baru
                all_inputs = [modal, minat, keahlian, waktu, lokasi, target_pembeli, jenis_produk, tim, harapan_profit, tujuan]
                if not all(all_inputs):
                    st.warning("Mohon lengkapi semua kolom untuk mendapatkan rekomendasi yang akurat.")
                else:
                    # Kumpulkan semua data ke dalam dictionary
                    prompt_data = {
                        "modal_awal": modal,
                        "minat_atau_hobi": minat,
                        "keahlian_spesifik": keahlian,
                        "waktu_luang_per_minggu": waktu,
                        "rencana_lokasi_usaha": lokasi,
                        "target_calon_pembeli": target_pembeli,
                        "jenis_produk_atau_jasa": jenis_produk,
                        "dijalankan_sendiri_atau_tim": tim,
                        "harapan_waktu_profit": harapan_profit,
                        "tujuan_utama_berbisnis": tujuan
                    }
                    # Prompt baru yang lebih detail
                    prompt = f"""
                    Sebagai seorang analis bisnis yang berpengalaman, analisis profil calon pebisnis berikut ini secara mendalam:
                    {json.dumps(prompt_data, indent=2)}

                    Berdasarkan profil tersebut, berikan 3 ide bisnis yang paling relevan dan potensial.
                    Untuk setiap ide, jelaskan:
                    1.  **Nama Ide Bisnis:** (Contoh: Katering Sehat Rumahan)
                    2.  **Deskripsi Singkat:** (Jelaskan konsep bisnisnya dalam 1-2 kalimat)
                    3.  **Alasan Kecocokan:** (Jelaskan mengapa ide ini sangat cocok berdasarkan modal, minat, keahlian, dan faktor lainnya dari profil yang diberikan)
                    
                    Sajikan jawaban dalam format yang jelas dan mudah dibaca menggunakan markdown.
                    """
                    with st.spinner("AI sedang menganalisis profil Anda..."):
                        try:
                            resp = model.generate_content(prompt)
                            st.divider()
                            st.subheader("✨ Berikut Rekomendasi Bisnis Untuk Anda")
                            st.markdown(resp.text)
                        except Exception as e:
                            st.error(f"Terjadi kesalahan saat menghasilkan rekomendasi: {e}")


def fitur_catatan():
    st.title("📝 Catatan Bisnis")
    if not st.session_state.get('user'):
        st.warning("Anda harus login untuk membuat dan melihat catatan bisnis Anda.")
        st.info("Login atau buat akun baru melalui menu di sidebar.")
        return
    
    user_id = st.session_state.user.user.id
    notes = supabase.table('notes').select('*').eq('user_id', user_id).order('created_at', desc=True).execute().data
    
    st.markdown('<div class="responsive-columns">', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.subheader("Catatan Baru")
            with st.form("new_note", clear_on_submit=True):
                judul, isi = st.text_input("Judul Catatan"), st.text_area("Isi Catatan", height=150)
                if st.form_submit_button("Simpan Catatan", use_container_width=True, type="primary"):
                    if judul and isi:
                        supabase.table('notes').insert({"title": judul, "content": isi, "user_id": user_id}).execute()
                        st.success("Catatan berhasil disimpan!"); st.rerun()
                    else: st.warning("Judul dan isi catatan tidak boleh kosong.")
    with col2:
        with st.container(border=True):
            st.subheader("Daftar Catatan")
            if not notes: st.info("Belum ada catatan yang tersimpan.")
            else:
                note_titles = [note['title'] for note in notes]
                pilih = st.selectbox("Pilih catatan", note_titles, label_visibility="collapsed")
                if pilih:
                    selected_note = next((note for note in notes if note['title'] == pilih), None)
                    st.text_area("Isi:", value=selected_note['content'], height=150, disabled=True)
                    if st.button(f"Hapus '{pilih}'", use_container_width=True):
                        supabase.table('notes').delete().eq('id', selected_note['id']).execute()
                        st.success(f"Catatan '{pilih}' dihapus."); st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

def fitur_kalkulator(): # (Fungsi ini tetap sama)
    st.title("🧮 Kalkulator Minimalis")
    st.markdown("Masukkan perhitungan di bawah dan tekan 'Hitung'. Gunakan `*` untuk kali dan `/` untuk bagi.")
    if 'calc_result' not in st.session_state: st.session_state.calc_result = "0"
    st.markdown(f'<div class="calculator-display" style="text-align:right; font-size: 2rem; background:#1F2937; padding:1rem; border-radius:0.5rem; margin-bottom:1rem;">{st.session_state.calc_result}</div>', unsafe_allow_html=True)
    with st.form("calculator_form"):
        expression = st.text_input("Ekspresi matematika", label_visibility="collapsed", placeholder="Contoh: (150000 + 50000) * 2")
        if st.form_submit_button("Hitung", use_container_width=True):
            try:
                expr_to_eval = re.sub(r'[^0-9+\-*/().\s]', '', expression.replace('x', '*').replace('×', '*').replace(':', '/'))
                st.session_state.calc_result = str(eval(expr_to_eval))
            except Exception: st.session_state.calc_result = "Error"
            st.rerun()

# ------------- SIDEBAR & MENU (Tetap sama) -------------
with st.sidebar:
    st.title("✨ Asisten Bisnis AI")
    st.markdown('<div class="menu-wrapper">', unsafe_allow_html=True)
    menu = option_menu(menu_title="", options=["Konsultasi", "Rekomendasi", "Catatan", "Kalkulator"], icons=["chat-quote-fill", "lightbulb-fill", "journal-text", "calculator-fill"], default_index=0)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-footer">', unsafe_allow_html=True)
    st.markdown('<div class="user-block">', unsafe_allow_html=True)
    if st.session_state.get('user'):
        email = st.session_state.user.user.email
        st.markdown(f'<div class="user-info"><div class="user-avatar">{email[0].upper()}</div><div class="user-email">{email}</div></div>', unsafe_allow_html=True)
        if st.button("Logout", use_container_width=True): st.session_state.user = None; st.rerun()
    else:
        with st.expander("🔐 Login / Buat Akun"):
            tab1, tab2 = st.tabs(["Login", "Buat Akun"])
            with tab1, st.form("login_form", clear_on_submit=True):
                email, password = st.text_input("Email"), st.text_input("Password", type="password")
                if st.form_submit_button("Login", use_container_width=True, type="primary"):
                    try: st.session_state['user'] = supabase.auth.sign_in_with_password({"email": email, "password": password}); st.rerun()
                    except: st.error(f"Login gagal.")
            with tab2, st.form("signup_form", clear_on_submit=True):
                email, password = st.text_input("Email Baru"), st.text_input("Buat Password", type="password")
                if st.form_submit_button("Buat Akun", use_container_width=True):
                    try: supabase.auth.sign_up({"email": email, "password": password}); st.session_state['user'] = supabase.auth.sign_in_with_password({"email": email, "password": password}); st.rerun()
                    except: st.error(f"Gagal membuat akun.")
    st.markdown('</div></div>', unsafe_allow_html=True)
    st.caption("© 2025 | Sae Company")
    st.markdown('</div>', unsafe_allow_html=True)

# ------------- ROUTE (Tetap sama) -------------
if menu == "Konsultasi": fitur_konsultasi()
elif menu == "Rekomendasi": fitur_rekomendasi()
elif menu == "Catatan": fitur_catatan()
elif menu == "Kalkulator": fitur_kalkulator()