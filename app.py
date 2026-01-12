import streamlit as st
from st_supabase_connection import SupabaseConnection, execute_query

# Konfiguracja strony
st.set_page_config(page_title="System WMS", layout="wide")

# Inicjalizacja połączenia z Supabase
# Dane uwierzytelniające będą pobierane z pliku secrets.toml lub ustawień Streamlit Cloud
conn = st.connection("supabase", type=SupabaseConnection)

def get_categories():
    query = conn.table("categories").select("id, name").execute()
    return {item['name']: item['id'] for item in query.data}

def get_products():
    query = conn.table("products").select("*, categories(name)").execute()
    return query.data

st.title("📦 System Zarządzania Magazynem (WMS)")

# Sidebar - Nawigacja
menu = st.sidebar.selectbox("Menu", ["Podgląd Magazynu", "Dodaj Produkt", "Zarządzaj Produktami"])

if menu == "Podgląd Magazynu":
    st.header("Aktualny stan magazynowy")
    products = get_products()
    if products:
        # Formatowanie danych do wyświetlenia
        display_data = []
        for p in products:
            display_data.append({
                "ID": p['id'],
                "Nazwa": p['name'],
                "Kategoria": p['categories']['name'],
                "Cena (PLN)": p['price'],
                "Ilość": p['stock_quantity'],
                "Opis": p['description']
            })
        st.dataframe(display_data, use_container_width=True)
    else:
        st.info("Magazyn jest pusty.")

elif menu == "Dodaj Produkt":
    st.header("Dodaj nowy produkt do bazy")
    
    categories = get_categories()
    
    with st.form("add_product_form"):
        name = st.text_input("Nazwa produktu")
        category_name = st.selectbox("Kategoria", list(categories.keys()))
        price = st.number_input("Cena", min_value=0.0, step=0.01)
        quantity = st.number_input("Ilość na stanie", min_value=0, step=1)
        description = st.text_area("Opis produktu")
        
        submit = st.form_submit_button("Dodaj produkt")
        
        if submit:
            if name:
                new_product = {
                    "name": name,
                    "category_id": categories[category_name],
                    "price": price,
                    "stock_quantity": quantity,
                    "description": description
                }
                try:
                    conn.table("products").insert(new_product).execute()
                    st.success(f"Produkt '{name}' został dodany!")
                except Exception as e:
                    st.error(f"Błąd podczas dodawania: {e}")
            else:
                st.warning("Nazwa produktu jest wymagana.")

elif menu == "Zarządzaj Produktami":
    st.header("Edycja i usuwanie produktów")
    products = get_products()
    
    if products:
        product_to_manage = st.selectbox(
            "Wybierz produkt", 
            products, 
            format_func=lambda x: f"{x['name']} (ID: {x['id']})"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Aktualizuj ilość")
            new_qty = st.number_input("Nowa ilość", value=product_to_manage['stock_quantity'])
            if st.button("Aktualizuj stan"):
                conn.table("products").update({"stock_quantity": new_qty}).eq("id", product_to_manage['id']).execute()
                st.success("Zaktualizowano ilość.")
                st.rerun()
                
        with col2:
            st.subheader("Usuń produkt")
            st.warning("Tej operacji nie można cofnąć.")
            if st.button("Usuń trwale"):
                conn.table("products").delete().eq("id", product_to_manage['id']).execute()
                st.info("Produkt usunięty.")
                st.rerun()
