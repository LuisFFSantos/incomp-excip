import streamlit as st
import pandas as pd
from io import BytesIO

# Carregar a base de dados do Excel
def load_data():
    try:
        data = pd.read_excel("Tabela final.xlsx")  # Nome fixo para o arquivo de base de dados
        return data
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo: {e}")
        return None

# Função para buscar incompatibilidades
def search_incompatibilities(data, excipient, functional_group):
    results = data
    if excipient:
        results = results[results['Excipientes'].str.contains(excipient, case=False, na=False)]
    if functional_group:
        results = results[results['Grupo funcional'].str.contains(functional_group, case=False, na=False)]
    return results

# Função para exportar os resultados para Excel
def export_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Resultados')
    processed_data = output.getvalue()
    return processed_data

# Função para limpar os campos
def clear_fields():
    st.session_state["excipient"] = ""
    st.session_state["functional_group"] = ""

# Configuração do Streamlit
st.set_page_config(page_title="Consulta de Incompatibilidade de Excipientes", layout="wide")

# Título da aplicação com ícone de lupa
st.markdown(
    """<h1 style="display: flex; align-items: center; gap: 10px;">
    <img src="https://cdn-icons-png.flaticon.com/512/954/954591.png" alt="Ícone de Lupa" style="width: 40px; height: 40px;">
    Consulta de Incompatibilidade de Excipientes
    </h1>""",
    unsafe_allow_html=True
)

# Carregar os dados ao iniciar a aplicação
data = load_data()

if data is not None:
    # Campos de busca
    st.subheader("Filtros de Pesquisa")
    col1, col2 = st.columns(2)
    with col1:
        excipient_query = st.text_input("Digite o excipiente que deseja consultar:", key="excipient")
    with col2:
        functional_group_query = st.text_input("Digite o grupo funcional que deseja consultar:", key="functional_group")

    # Botão de busca
    if st.button("Buscar", key="search_button"):
        results = search_incompatibilities(data, excipient_query, functional_group_query)
        
        # Exibir resultados
        if not results.empty:
            st.subheader("Resultados da Pesquisa")
            st.dataframe(results)
            
            # Botão para exportar os resultados
            excel_data = export_to_excel(results)
            st.download_button(
                label="Exportar para Excel",
                data=excel_data,
                file_name="resultados_incompatibilidades.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("Nenhuma incompatibilidade encontrada com os critérios fornecidos.")

    # Botão para limpar a pesquisa
    st.button("Limpar Pesquisa", on_click=clear_fields, key="clear_button")
else:
    st.error("Não foi possível carregar os dados do Excel.")

