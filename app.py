import streamlit as st
from supabase import create_client, Client

# --- KONFIGURACJA POŁĄCZENIA ---
# Dane połączenia z Twojego panelu Supabase
URL = "https://ljydyjsvbeiwuxsrsyqq.supabase.co"
KEY = "sb_publishable_wTpRY0fzrU0VhXLFJDmREg_ArcKGKlM"

@st.cache_resource
def init_connection():
    """Inicjalizuje połączenie z bazą danych raz, aby nie powtarzać tego przy każdym odświeżeniu."""
    return create_client(URL, KEY)

# Inicjalizacja klienta
try:
    supabase = init_connection()
except Exception as e:
    st.error(f"Błąd połączenia z Supabase: {e}")
    st.stop()

# Konfiguracja strony Streamlit
st.set_page_config(page_title="Zarządzanie Magazynem", layout="centered")
st.title("📦 System Zarządzania Produktami")

# --- ZAKŁADKI ---
tab1, tab2, tab3 = st.tabs(["📦 Dodaj Produkt", "➕ Dodaj Kategorię", "📊 Podgląd Bazy"])

# --- TAB 2: DODAWANIE KATEGORII ---
with tab2:
    st.header("Nowa Kategoria")
    with st.form("category_form", clear_on_submit=True):
        kat_nazwa = st.text_input("Nazwa kategorii")
        kat_opis = st.text_area("Opis")
        submit_kat = st.form_submit_button("Zapisz kategorię")

        if submit_kat:
            if kat_nazwa:
                try:
                    data = {"nazwa": kat_nazwa, "opis": kat_opis}
                    supabase.table("Kategorie").insert(data).execute()
                    st.success(f"Dodano kategorię: {kat_nazwa}")
                except Exception as e:
                    st.error(f"Błąd zapisu: {e}")
            else:
                st.error("Nazwa kategorii jest wymagana!")

# --- TAB 1: DODAWANIE PRODUKTU ---
with tab1:
    st.header("Nowy Produkt")
    
    # Pobranie aktualnych kategorii do listy rozwijanej
    try:
        categories_res = supabase.table("Kategorie").select("id, nazwa").execute()
        categories_data = categories_res.data
    except Exception as e:
        st.error(f"Nie udało się pobrać kategorii: {e}")
        categories_data = []
    
    if not categories_data:
        st.warning("Najpierw dodaj przynajmniej jedną kategorię w zakładce obok!")
    else:
        # Mapowanie nazwy na ID
        cat_options = {item['nazwa']: item['id'] for item in categories_data}
        
        with st.form("product_form", clear_on_submit=True):
            prod_nazwa = st.text_input("Nazwa produktu")
            prod_liczba = st.number_input("Liczba (sztuki)", min_value=0, step=1)
            prod_cena = st.number_input("Cena", min_value=0.0, step=0.01, format="%.2f")
            prod_kat_nazwa = st.selectbox("Kategoria", options=list(cat_options.keys()))
            
            submit_prod = st.form_submit_button("Dodaj produkt")
            
            if submit_prod:
                if prod_nazwa:
                    try:
                        product_data = {
                            "nazwa": prod_nazwa,
                            "liczba": prod_liczba,
                            "cena": prod_cena,
                            "kategorie_id": cat_options[prod_kat_nazwa]
                        }
                        supabase.table("Produkty").insert(product_data).execute()
                        st.success(f"Produkt '{prod_nazwa}' został dodany.")
                    except Exception as e:
                        st.error(f"Błąd podczas dodawania produktu: {e}")
                else:
                    st.error("Nazwa produktu jest wymagana!")

# --- TAB 3: PODGLĄD DANYCH ---
with tab3:
    st.header("Aktualny stan bazy")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Kategorie")
        try:
            kat_view = supabase.table("Kategorie").select("id, nazwa, opis").execute()
            if kat_view.data:
                st.dataframe(kat_view.data, use_container_width=True)
            else:
                st.info("Brak kategorii.")
        except Exception as e:
            st.error(f"Błąd pobierania kategorii: {e}")
    
    with col2:
        st.subheader("Produkty")
        try:
            prod_view = supabase.table("Produkty").select("id, nazwa, liczba, cena, kategorie_id").execute()
            if prod_view.data:
                st.dataframe(prod_view.data, use_container_width=True)
            else:
                st.info("Brak produktów.")
        except Exception as e:
            st.error(f"Błąd pobierania produktów: {e}")
