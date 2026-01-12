import streamlit as st
from supabase import create_client, Client
import pandas as pd

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

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Inwentaryzacja IT", layout="wide", page_icon="💻")
st.title("🖥️ System Zarządzania Zasobami IT")
st.markdown("Automatyczna ewidencja sprzętu i licencji w podziale na działy.")
st.markdown("---")

# --- ZAKŁADKI ---
tab1, tab2, tab3 = st.tabs(["📦 Ewidencja Sprzętu", "🏢 Działy i Kategorie", "📊 Raporty"])

# --- TAB 2: DZIAŁY I KATEGORIE (Tabela Kategorie) ---
with tab2:
    st.header("Zarządzanie strukturą")
    col_a, col_b = st.columns([1, 2])
    
    with col_a:
        st.subheader("Dodaj nową kategorię")
        # Przykłady profesjonalnych kategorii w placeholderach
        with st.form("dept_form", clear_on_submit=True):
            nazwa_dzialu = st.text_input("Nazwa (np. Infrastruktura, Deweloperzy, Zarząd)")
            opis_dzialu = st.text_area("Opis kategorii/lokalizacja")
            submit_dept = st.form_submit_button("Zatwierdź kategorię")

            if submit_dept and nazwa_dzialu:
                try:
                    supabase.table("Kategorie").insert({"nazwa": nazwa_dzialu, "opis": opis_dzialu}).execute()
                    st.success(f"Dodano kategorię: {nazwa_dzialu}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Błąd zapisu: {e}")

    with col_b:
        st.subheader("Zdefiniowane działy")
        try:
            depts = supabase.table("Kategorie").select("id, nazwa, opis").execute()
            if depts.data:
                # Wyświetlamy ładną tabelę bez kolumny ID dla użytkownika
                df_depts = pd.DataFrame(depts.data)
                st.dataframe(df_depts[['nazwa', 'opis']], use_container_width=True)
            else:
                st.info("Brak zdefiniowanych kategorii. Dodaj pierwszą, np. 'Sprzęt Biurowy'.")
        except:
            st.error("Nie udało się pobrać kategorii.")

# --- TAB 1: EWIDENCJA SPRZĘTU (Tabela Produkty) ---
with tab1:
    st.header("Rejestracja Zasobów")
    
    # Pobranie kategorii do selectboxa
    kat_res = supabase.table("Kategorie").select("id, nazwa").execute()
    kat_list = {item['nazwa']: item['id'] for item in kat_res.data} if kat_res.data else {}

    if not kat_list:
        st.warning("⚠️ Baza kategorii jest pusta. Przejdź do zakładki 'Działy i Kategorie', aby zacząć.")
    else:
        with st.form("asset_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                model = st.text_input("Nazwa urządzenia (np. MacBook Pro M3, Monitor Dell 27')")
                ilosc = st.number_input("Sztuk w magazynie", min_value=1, step=1)
            with c2:
                cena_zakupu = st.number_input("Wartość netto (PLN)", min_value=0.0, format="%.2f")
                przypisanie = st.selectbox("Przypisz do kategorii", options=list(kat_list.keys()))
            
            submit_asset = st.form_submit_button("Zapisz w ewidencji")

            if submit_asset and model:
                try:
                    asset_data = {
                        "nazwa": model,
                        "liczba": ilosc,
                        "cena": cena_zakupu,
                        "kategorie_id": kat_list[przypisanie]
                    }
                    supabase.table("Produkty").insert(asset_data).execute()
                    st.success(f"Pomyślnie zarejestrowano: {model}")
                except Exception as e:
                    st.error(f"Błąd RLS lub bazy: {e}")

# --- TAB 3: RAPORTY ---
with tab3:
    st.header("Analityka Zasobów")
    
    # Pobieramy produkty i łączymy z kategoriami (jeśli to możliwe)
    res = supabase.table("Produkty").select("nazwa, liczba, cena, kategorie_id").execute()
    
    if res.data:
        df = pd.DataFrame(res.data)
        df['Wartość łączna'] = df['liczba'] * df['cena']
        
        # Dashboard
        m1, m2, m3 = st.columns(3)
        m1.metric("Liczba urządzeń", f"{int(df['liczba'].sum())} szt.")
        m2.metric("Wartość majątku", f"{df['Wartość łączna'].sum():,.2f} PLN")
        
        # Mapowanie ID kategorii na nazwę dla czytelności
        if not df.empty:
            cat_map = {v: k for k, v in kat_list.items()}
            df['Kategoria'] = df['kategorie_id'].map(cat_map)
            
            st.subheader("Szczegółowa lista inwentarzowa")
            st.dataframe(df[['Kategoria', 'nazwa', 'liczba', 'cena', 'Wartość łączna']], use_container_width=True)
            
            # Prosty wykres kołowy podziału wartości
            st.subheader("Podział wartości na urządzenia")
            st.bar_chart(df.set_index('nazwa')['Wartość łączna'])
    else:
        st.info("Brak danych do wygenerowania raportu.")
