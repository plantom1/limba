import streamlit as st
import streamlit.web.cli as stcli
import math
import os
import sys

# --- FUNGSI WRAPPER UNTUK EXECUTABLE ---
def resolve_path(path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, path)
    return os.path.abspath(os.path.join(os.getcwd(), path))

def hitung_volume_miring(luas_alas, h, sudut_derajat=60):
    # Luas alas dianggap bujur sangkar (sisi x sisi)
    s_bawah = math.sqrt(luas_alas)
    
    # Menghitung tambahan lebar karena kemiringan (x)
    # tan(60) = h / x  => x = h / tan(60)
    sudut_rad = math.radians(sudut_derajat)
    x = h / math.tan(sudut_rad)
    
    s_atas = s_bawah + (2 * x)
    luas_atas = s_atas ** 2
    
    # Rumus Volume Limas Terpancung (Frustum)
    volume = (h / 3) * (luas_alas + luas_atas + math.sqrt(luas_alas * luas_atas))
    return volume, s_atas

def run_streamlit_app():
    st.set_page_config(page_title="Kalkulator Desain Pengendapan", layout="wide")
    st.title("🌊 Sistem Desain Kolam Pengendapan (Dinding Miring 60°)")
    st.markdown("---")

    # --- SIDEBAR: INPUT PARAMETER ---
    st.sidebar.header("📥 Parameter Input")
    
    with st.sidebar.expander("1. Operasional & TSS", expanded=True):
        tss_max = st.number_input("TSS Maksimal (mg/L)", value=100.0, step=1.0)
        debit_max = st.number_input("Debit Air Maksimal (m³/s)", value=0.5, step=0.01)
        massa_jenis_g = st.number_input("Massa Jenis Padatan (g/m³)", value=2500000.0, step=1000.0)

    with st.sidebar.expander("2. Fisika (Stokes)", expanded=True):
        d_mm = st.number_input("Diameter Partikel (mm)", value=0.05, format="%.4f")
        pa = st.number_input("Massa Jenis Air (kg/m³)", value=1000.0, step=1.0)
        miu = st.number_input("Viskositas/Miu (Pa·s)", value=0.001, format="%.4f")

    with st.sidebar.expander("3. Konstruksi", expanded=True):
        kedalaman = st.number_input("Kedalaman Kolam (m)", value=2.0, step=0.1)
        jumlah_kolam = st.number_input("Total Jumlah Kolam", min_value=1, value=3, step=1)
        kemiringan = 60 # Sudut statis sesuai permintaan

    # --- LOGIKA PERHITUNGAN ---
    ps_kg = massa_jenis_g / 1000
    g = 9.8 
    d_m = d_mm / 1000 
    v_stokes = (g * (d_m**2) * (ps_kg - pa)) / (18 * miu) if miu > 0 else 0
    luas_total_butuh = debit_max / v_stokes if v_stokes > 0 else 0

    # Perhitungan Unit 1 (1/3 dari total luas)
    luas_kol_1 = luas_total_butuh / 3
    vol_1, s_atas_1 = hitung_volume_miring(luas_kol_1, kedalaman, kemiringan)
    v_air_1 = (debit_max * 1.25) / luas_kol_1 if luas_kol_1 > 0 else 0
    waktu_alir_1 = math.sqrt(luas_kol_1) / v_air_1 if v_air_1 > 0 else 0

    # Perhitungan Unit Secondary (2/3 dari total luas)
    if jumlah_kolam > 1:
        n_secondary = jumlah_kolam - 1
        luas_sisa = ((2/3) * luas_total_butuh) / n_secondary
        vol_sisa, s_atas_sisa = hitung_volume_miring(luas_sisa, kedalaman, kemiringan)
        v_air_sisa = (debit_max * 1.25) / luas_sisa if luas_sisa > 0 else 0
        waktu_alir_sisa = math.sqrt(luas_sisa) / v_air_sisa if v_air_sisa > 0 else 0
        
        # VOLUME TOTAL SISTEM
        volume_total_sistem = vol_1 + (vol_sisa * n_secondary)
    else:
        vol_sisa, s_atas_sisa, luas_sisa, waktu_alir_sisa, n_secondary = 0, 0, 0, 0, 0
        volume_total_sistem = vol_1

    # --- TAMPILAN DASHBOARD ---
    # Menambahkan kolom ke-4 untuk Volume Total Sistem
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Luas Total (m²)", f"{luas_total_butuh:.2f}")
    c2.metric("V. Stokes (m/s)", f"{v_stokes:.6f}")
    c3.metric("Sudut Dinding", f"{kemiringan}°")
    c4.metric("VOL. TOTAL SISTEM", f"{volume_total_sistem:.2f} m³")

    tab1, tab2 = st.tabs(["Unit 1 (Primary)", f"Unit 2 - {jumlah_kolam} (Secondary)"])

    with tab1:
        col_a, col_b = st.columns(2)
        with col_a:
            st.write(f"**Sisi Bawah:** {math.sqrt(luas_kol_1):.2f} m")
            st.write(f"**Sisi Atas:** {s_atas_1:.2f} m")
            st.write(f"**Luas Alas:** {luas_kol_1:.2f} m²")
        with col_b:
            st.success(f"**Volume Kolam:** {vol_1:.2f} m³")
            st.info(f"**Waktu Keluar:** {waktu_alir_1:.2f} detik")

    with tab2:
        if jumlah_kolam > 1:
            col_a, col_b = st.columns(2)
            with col_a:
                st.write(f"**Sisi Bawah:** {math.sqrt(luas_sisa):.2f} m")
                st.write(f"**Sisi Atas:** {s_atas_sisa:.2f} m")
                st.write(f"**Luas Alas (per unit):** {luas_sisa:.2f} m²")
            with col_b:
                st.success(f"**Volume Per Unit:** {vol_sisa:.2f} m³")
                st.info(f"**Waktu Keluar:** {waktu_alir_sisa:.2f} detik")
            
            st.markdown("---")
            st.write(f"**Total Volume Secondary ({n_secondary} unit):** {vol_sisa * n_secondary:.2f} m³")
        else:
            st.info("Hanya menggunakan satu kolam utama.")

    st.markdown("---")
    st.caption("Volume dihitung menggunakan rumus Frustum (Limas Terpancung) untuk akurasi galian.")

# --- ENTRY POINT ---
if __name__ == "__main__":
    if st.runtime.exists():
        run_streamlit_app()
    else:
        sys.argv = [
            "streamlit", "run", resolve_path(__file__),
            "--server.headless=false",
            "--global.developmentMode=false",
        ]

import streamlit as st
import streamlit.web.cli as stcli
import math
import os
import sys

# --- FUNGSI WRAPPER UNTUK EXECUTABLE ---
def resolve_path(path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, path)
    return os.path.abspath(os.path.join(os.getcwd(), path))

def hitung_volume_miring(luas_alas, h, sudut_derajat=60):
    # Luas alas dianggap bujur sangkar (sisi x sisi)
    s_bawah = math.sqrt(luas_alas)
    
    # Menghitung tambahan lebar karena kemiringan (x)
    # tan(60) = h / x  => x = h / tan(60)
    sudut_rad = math.radians(sudut_derajat)
    x = h / math.tan(sudut_rad)
    
    s_atas = s_bawah + (2 * x)
    luas_atas = s_atas ** 2
    
    # Rumus Volume Limas Terpancung (Frustum)
    volume = (h / 3) * (luas_alas + luas_atas + math.sqrt(luas_alas * luas_atas))
    return volume, s_atas

def run_streamlit_app():
    st.set_page_config(page_title="Kalkulator Desain Pengendapan", layout="wide")
    st.title("🌊 Sistem Desain Kolam Pengendapan (Dinding Miring 60°)")
    st.markdown("---")

    # --- SIDEBAR: INPUT PARAMETER ---
    st.sidebar.header("📥 Parameter Input")
    
    with st.sidebar.expander("1. Operasional & TSS", expanded=True):
        tss_max = st.number_input("TSS Maksimal (mg/L)", value=100.0, step=1.0)
        debit_max = st.number_input("Debit Air Maksimal (m³/s)", value=0.5, step=0.01)
        massa_jenis_g = st.number_input("Massa Jenis Padatan (g/m³)", value=2500000.0, step=1000.0)

    with st.sidebar.expander("2. Fisika (Stokes)", expanded=True):
        d_mm = st.number_input("Diameter Partikel (mm)", value=0.05, format="%.4f")
        pa = st.number_input("Massa Jenis Air (kg/m³)", value=1000.0, step=1.0)
        miu = st.number_input("Viskositas/Miu (Pa·s)", value=0.001, format="%.4f")

    with st.sidebar.expander("3. Konstruksi", expanded=True):
        kedalaman = st.number_input("Kedalaman Kolam (m)", value=2.0, step=0.1)
        jumlah_kolam = st.number_input("Total Jumlah Kolam", min_value=1, value=3, step=1)
        kemiringan = 60 # Sudut statis sesuai permintaan

    # --- LOGIKA PERHITUNGAN ---
    ps_kg = massa_jenis_g / 1000
    g = 9.8 
    d_m = d_mm / 1000 
    v_stokes = (g * (d_m**2) * (ps_kg - pa)) / (18 * miu) if miu > 0 else 0
    luas_total_butuh = debit_max / v_stokes if v_stokes > 0 else 0

    # Perhitungan Unit 1 (1/3 dari total luas)
    luas_kol_1 = luas_total_butuh / 3
    vol_1, s_atas_1 = hitung_volume_miring(luas_kol_1, kedalaman, kemiringan)
    v_air_1 = (debit_max * 1.25) / luas_kol_1 if luas_kol_1 > 0 else 0
    waktu_alir_1 = math.sqrt(luas_kol_1) / v_air_1 if v_air_1 > 0 else 0

    # Perhitungan Unit Secondary (2/3 dari total luas)
    if jumlah_kolam > 1:
        n_secondary = jumlah_kolam - 1
        luas_sisa = ((2/3) * luas_total_butuh) / n_secondary
        vol_sisa, s_atas_sisa = hitung_volume_miring(luas_sisa, kedalaman, kemiringan)
        v_air_sisa = (debit_max * 1.25) / luas_sisa if luas_sisa > 0 else 0
        waktu_alir_sisa = math.sqrt(luas_sisa) / v_air_sisa if v_air_sisa > 0 else 0
        
        # VOLUME TOTAL SISTEM
        volume_total_sistem = vol_1 + (vol_sisa * n_secondary)
    else:
        vol_sisa, s_atas_sisa, luas_sisa, waktu_alir_sisa, n_secondary = 0, 0, 0, 0, 0
        volume_total_sistem = vol_1

    # --- TAMPILAN DASHBOARD ---
    # Menambahkan kolom ke-4 untuk Volume Total Sistem
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Luas Total (m²)", f"{luas_total_butuh:.2f}")
    c2.metric("V. Stokes (m/s)", f"{v_stokes:.6f}")
    c3.metric("Sudut Dinding", f"{kemiringan}°")
    c4.metric("VOL. TOTAL SISTEM", f"{volume_total_sistem:.2f} m³")

    tab1, tab2 = st.tabs(["Unit 1 (Primary)", f"Unit 2 - {jumlah_kolam} (Secondary)"])

    with tab1:
        col_a, col_b = st.columns(2)
        with col_a:
            st.write(f"**Sisi Bawah:** {math.sqrt(luas_kol_1):.2f} m")
            st.write(f"**Sisi Atas:** {s_atas_1:.2f} m")
            st.write(f"**Luas Alas:** {luas_kol_1:.2f} m²")
        with col_b:
            st.success(f"**Volume Kolam:** {vol_1:.2f} m³")
            st.info(f"**Waktu Keluar:** {waktu_alir_1:.2f} detik")

    with tab2:
        if jumlah_kolam > 1:
            col_a, col_b = st.columns(2)
            with col_a:
                st.write(f"**Sisi Bawah:** {math.sqrt(luas_sisa):.2f} m")
                st.write(f"**Sisi Atas:** {s_atas_sisa:.2f} m")
                st.write(f"**Luas Alas (per unit):** {luas_sisa:.2f} m²")
            with col_b:
                st.success(f"**Volume Per Unit:** {vol_sisa:.2f} m³")
                st.info(f"**Waktu Keluar:** {waktu_alir_sisa:.2f} detik")
            
            st.markdown("---")
            st.write(f"**Total Volume Secondary ({n_secondary} unit):** {vol_sisa * n_secondary:.2f} m³")
        else:
            st.info("Hanya menggunakan satu kolam utama.")

    st.markdown("---")
    st.caption("Volume dihitung menggunakan rumus Frustum (Limas Terpancung) untuk akurasi galian.")

# --- ENTRY POINT ---
if __name__ == "__main__":
    if st.runtime.exists():
        run_streamlit_app()
    else:
        sys.argv = [
            "streamlit", "run", resolve_path(__file__),
            "--server.headless=false",
            "--global.developmentMode=false",
        ]
sys.exit(stcli.main())