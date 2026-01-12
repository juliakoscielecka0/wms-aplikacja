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

# --- ZAKŁADKI ---
tab1, tab2, tab3, tab4 = st.tabs([
    "📦 Ewidencja", 
    "🏢 Kategorie", 
    "📊 Raporty i Usuwanie", 
    "🚨 Zgłoś Szkodę"
])

# --- TAB 2: KATEGORIE ---
with tab2:
    st.header("Zarządzanie strukturą")
    col_a, col_b = st.columns([1, 2])
    with col_a:
        with st.form("dept_form", clear_on_submit=True):
            nazwa_dzialu = st.text_input("Nowa kategoria (np. Laptopy)")
            submit_dept = st.form_submit_button("Dodaj")
            if submit_dept and nazwa_dzialu:
                supabase.table("Kategorie").insert({"nazwa": nazwa_dzialu}).execute()
                st.success("Dodano!")
                st.rerun()
    with col_b:
        depts = supabase.table("Kategorie").select("nazwa").execute()
        if depts.data:
            st.write("Istniejące kategorie:", ", ".join([d['nazwa'] for d in depts.data]))

# --- TAB 1: EWIDENCJA ---
with tab1:
    st.header("Rejestracja Zasobów")
    kat_res = supabase.table("Kategorie").select("id, nazwa").execute()
    kat_list = {item['nazwa']: item['id'] for item in kat_res.data} if kat_res.data else {}

    if not kat_list:
        st.warning("Najpierw dodaj kategorię!")
    else:
        with st.form("asset_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            model = c1.text_input("Nazwa urządzenia")
            ilosc = c1.number_input("Sztuk", min_value=1)
            cena = c2.number_input("Wartość (PLN)", min_value=0.0)
            kat = c2.selectbox("Kategoria", options=list(kat_list.keys()))
            if st.form_submit_button("Zapisz"):
                supabase.table("Produkty").insert({
                    "nazwa": model, "liczba": ilosc, "cena": cena, "kategorie_id": kat_list[kat]
                }).execute()
                st.success("Zapisano!")

# --- TAB 3: RAPORTY I USUWANIE ---
with tab3:
    st.header("Pełna Lista i Zarządzanie")
    res = supabase.table("Produkty").select("*").execute()
    
    if res.data:
        df = pd.DataFrame(res.data)
        st.dataframe(df[['id', 'nazwa', 'liczba', 'cena']], use_container_width=True)
        
        st.subheader("🗑️ Usuń produkt z bazy")
        with st.form("delete_form"):
            id_to_delete = st.number_input("Podaj ID produktu do usunięcia", min_value=1, step=1)
            confirm = st.checkbox("Potwierdzam chęć trwałego usunięcia")
            if st.form_submit_button("Usuń bezpowrotnie"):
                if confirm:
                    try:
                        supabase.table("Produkty").delete().eq("id", id_to_delete).execute()
                        st.success(f"Usunięto produkt o ID {id_to_delete}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Błąd: {e}")
                else:
                    st.warning("Musisz zaznaczyć potwierdzenie!")
    else:
        st.info("Brak danych.")

# --- TAB 4: ZGŁASZANIE SZKODY ---
with tab4:
    st.header("🚨 Formularz zgłoszenia uszkodzenia")
    st.write("Wybierz produkt z listy, aby zgłosić jego uszkodzenie lub awarię.")
    
    prod_res = supabase.table("Produkty").select("id, nazwa, liczba").execute()
    
    if prod_res.data:
        prod_options = {f"{p['nazwa']} (ID: {p['id']})": p for p in prod_res.data}
        
        with st.form("damage_form", clear_on_submit=True):
            wybrany_label = st.selectbox("Wybierz uszkodzony sprzęt", options=list(prod_options.keys()))
            opis_szkody = st.text_area("Opis usterki")
            czy_wycofac = st.checkbox("Wycofaj jedną sztukę ze stanu magazynowego")
            
            if st.form_submit_button("Zgłoś szkodę"):
                sprzet = prod_options[wybrany_label]
                nowa_nazwa = f"⚠️ [SZKODA] {sprzet['nazwa']}"
                nowa_liczba = sprzet['liczba'] - 1 if czy_wycofac and sprzet['liczba'] > 0 else sprzet['liczba']
                
                try:
                    supabase.table("Produkty").update({
                        "nazwa": nowa_nazwa, 
                        "liczba": nowa_liczba
                    }).eq("id", sprzet['id']).execute()
                    
                    st.warning(f"Zgłoszono szkodę dla: {sprzet['nazwa']}.")
                    if czy_wycofac:
                        st.write(f"Zaktualizowano stan magazynowy: {nowa_liczba} szt.")
                except Exception as e:
                    st.error(f"Błąd podczas aktualizacji: {e}")
    else:
        st.info("Brak produktów w bazie do zgłoszenia szkody.")
