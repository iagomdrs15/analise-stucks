import streamlit as st
import re
from supabase import create_client, Client

# --- CONFIGURAÇÕES DE CONEXÃO ---
# Mantive suas chaves conforme fornecido
SUPABASE_URL = "https://ntnkfecnbrvragfdahiu.supabase.co"
SUPABASE_KEY = "sb_publishable_PtBIaH2XLw5xzvQiOL91Pg_iLt0HaHG"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def extrair_order_id(url):
    """
    Extrai o ID após 'orderDetail/'. 
    Funciona para BR... e SPXBR...
    """
    # Padrao atualizado para capturar a variável entre barras após orderDetail
    padrao = r"orderDetail/([A-Z0-9]+)/"
    resultado = re.search(padrao, url)
    return resultado.group(1) if resultado else None

def buscar_dados_supabase(id_pedido):
    """Consulta o banco de dados pelo Order ID"""
    try:
        response = supabase.table("pedidos_consolidado") \
            .select("*") \
            .eq("order_id", id_pedido) \
            .execute()
        return response.data
    except Exception as e:
        st.error(f"Erro na consulta: {e}")
        return []

# --- INTERFACE DO USUÁRIO (UI) ---
st.set_page_config(page_title="Gestão Logística - Milorde", layout="wide")

st.title("📦 Sistema de Consulta Consolidada")
st.markdown("---")

# Entrada da URL
url_input = st.text_input("Cole a URL do pedido SPX aqui:", placeholder="https://spx.shopee.com.br/#/orderDetail/...")

if url_input:
    sku_extraido = extrair_order_id(url_input)
    
    if sku_extraido:
        st.info(f"🔎 ID Identificado: **{sku_extraido}**")
        
        # Realiza a busca
        dados = buscar_dados_supabase(sku_extraido)
        
        if dados:
            item = dados[0]
            
            # Layout em colunas
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Order ID", item.get('order_id'))
                # Ajuste os campos abaixo conforme os nomes exatos das colunas no seu SQL
                st.metric("Status", item.get('status_current', item.get('status')))
                st.metric("Aging", f"{item.get('aging_days', item.get('aging'))} dias")

            with col2:
                st.metric("Receive Time", item.get('receive_time'))
                st.metric("Station Destination", item.get('station_destination', item.get('destination_hub')))
                st.metric("Macro Aging", item.get('macro_aging'))

            with col3:
                st.metric("Current Station", item.get('current_station'))
                st.write("**Hub Reason:**")
                st.warning(item.get('hub_reason', item.get('reason')))

            st.markdown("---")
            
            # Botão para acessar o site diretamente usando a URL colada
            st.link_button(f"🔗 Abrir Pedido {sku_extraido} no Painel SPX", url_input)
            
        else:
            st.error(f"O ID {sku_extraido} não foi encontrado na tabela 'Consolidado'.")
    else:
        st.warning("A URL colada não contém um Order ID válido.")

# --- BARRA LATERAL UNIFICADA (Evita erro de DuplicateElementId) ---
with st.sidebar:
    st.header("Recursos Externos")
    url_planilha = "https://docs.google.com/spreadsheets/d/1HPJC9zVzijSQoKJyN7dmJ37AJWFHWzL_GIWDiEn_2Wc/edit?gid=0#gid=0"
    st.link_button("📊 Abrir Planilha Consolidado", url_planilha)
    
    st.markdown("---")
    st.header("Status do Sistema")
    st.success("Conectado ao Supabase")
    
    # Adicionada uma chave única (key) para evitar conflitos se o script rodar duas vezes
    if st.button("Limpar Busca", key="btn_limpar_principal"):
        st.rerun()
