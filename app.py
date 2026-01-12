import streamlit as st
from supabase import create_client, Client

# --- KONFIGURACJA POŁĄCZENIA ---
URL = "https://ljydyjsvbeiwuxsrsyqq.supabase.co"
KEY = "sb_publishable_wTpRY0fzrU0VhXLFJDmREg_ArcKGKlM"

@st.cache_resource
def init_connection():
    return create_client(URL, KEY)

try:
    supabase = init_connection()
except Exception as e:
    st.error(f"Błąd połączenia: {e}")
    st.stop()

# --- NOWY STYL I KONFIGURACJA ---
st.set_page_config(page_title="Inwentaryzacja IT", layout="wide")
st.title("🖥️ System Inwentaryzacji Sprzętu IT")
st.markdown("---")

# --- ZAKŁADKI ---
tab1, tab2, tab3 = st.tabs(["📋 Ewidencja Sprzętu", "📁 Zarządzanie Działami", "📈 Raport i Statystyki"])

# --- TAB 2: ZARZĄDZANIE DZIAŁAMI (Tabela Kategorie) ---
with tab2:
    st.header("Konfiguracja Działów/Grup")
    col_a, col_b = st.columns([1, 2])
    
    with col_a:
        with st.form("dept_form", clear_on_submit=True):
            nazwa_dzialu = st.text_input("Nazwa grupy (np. Serwerownia, Biuro)")
            opis_dzialu = st.text_area("Notatki dodatkowe")
            submit_dept = st.form_submit_button("Utwórz grupę")

            if submit_dept and nazwa_dzialu:
                try:
                    supabase.table("Kategorie").insert({"nazwa": nazwa_dzialu, "opis": opis_dzialu}).execute()
                    st.success("Grupa została utworzona!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Błąd: {e}")

    with col_b:
        st.subheader("Istniejące grupy")
        depts = supabase.table("Kategorie").select("nazwa, opis").execute()
        if depts.data:
            st.table(depts.data)

# --- TAB 1: EWIDENCJA SPRZĘTU (Tabela Produkty) ---
with tab1:
    st.header("Rejestracja Nowego Urządzenia")
    
    # Pobranie kategorii
    kat_res = supabase.table("Kategorie").select("id, nazwa").execute()
    kat_list = {item['nazwa']: item['id'] for item in kat_res.data} if kat_res.data else {}

    if not kat_list:
        st.info("⚠️ Najpierw zdefiniuj grupy w zakładce 'Zarządzanie Działami'.")
    else:
        with st.form("asset_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                model = st.text_input("Model/Nazwa urządzenia")
                ilosc = st.number_input("Ilość jednostek", min_value=1, step=1)
            with c2:
                cena_zakupu = st.number_input("Wartość jednostkowa (PLN)", min_value=0.0)
                przypisanie = st.selectbox("Lokalizacja/Grupa", options=list(kat_list.keys()))
            
            submit_asset = st.form_submit_button("Dodaj do ewidencji")

            if submit_asset and model:
                try:
                    asset_data = {
                        "nazwa": model,
                        "liczba": ilosc,
                        "cena": cena_zakupu,
                        "kategorie_id": kat_list[przypisanie]
                    }
                    supabase.table("Produkty").insert(asset_data).execute()
                    st.success(f"Dodano: {model}")
                except Exception as e:
                    st.error(f"Błąd zapisu: {e}")

# --- TAB 3: RAPORT I STATYSTYKI ---
with tab3:
    st.header("Podsumowanie zasobów")
    
    # Pobranie danych do raportu
    res = supabase.table("Produkty").select("nazwa, liczba, cena").execute()
    
    if res.data:
        import pandas as pd
        df = pd.DataFrame(res.data)
        df['Wartość całkowita'] = df['liczba'] * df['cena']
        
        # Statystyki u góry
        m1, m2, m3 = st.columns(3)
        m1.metric("Suma urządzeń", int(df['liczba'].sum()))
        m2.metric("Łączna wartość sprzętu", f"{df['Wartość całkowita'].sum():,.2f} PLN")
        m3.metric("Najdroższy typ", df.loc[df['cena'].idxmax()]['nazwa'])
        
        st.subheader("Pełna lista inwentarzowa")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Baza jest pusta.")
