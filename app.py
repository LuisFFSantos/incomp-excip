import streamlit as st
import pandas as pd
from io import BytesIO
import re
from deep_translator import GoogleTranslator
import app_search  # Importando o arquivo app.py

# Configuração do Streamlit
st.set_page_config(
    page_title="Consulta de Incompatibilidade de Excipientes",
    page_icon="https://cdn-icons-png.flaticon.com/512/954/954591.png",
    layout="wide"
)

# Cache para acelerar a tradução e o carregamento dos dados
@st.cache_data
def load_excel_data():
    try:
        data = pd.read_excel("Tabela final.xlsx")
        return data
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo Excel: {e}")
        return pd.DataFrame()

@st.cache_data
def translate_text(text, target_lang='pt'):
    try:
        return GoogleTranslator(source='auto', target=target_lang).translate(text.strip())
    except Exception as e:
        st.warning(f"Erro na tradução: {e}")
        return text

@st.cache_data
def load_handbook_data():
    try:
        with open("Handbook.md", "r", encoding="utf-8") as file:
            content = file.read()

        sections_to_extract = [
            "1 Nonproprietary Names", "2 Synonyms", "3 Chemical Name and CAS Registry Number",
            "4 Empirical Formula and Molecular Weight", "6 Functional Category",
            "7 Applications in Pharmaceutical Formulation or Technology", "8 Description",
            "9 Pharmacopeial Specifications", "11 Stability and Storage Conditions",
            "12 Incompatibilities", "17 Related Substances"
        ]

        section_translations = {
            "1 Nonproprietary Names": "Nomes Não Proprietários",
            "2 Synonyms": "Sinônimos",
            "3 Chemical Name and CAS Registry Number": "Nome Químico e Número CAS",
            "4 Empirical Formula and Molecular Weight": "Fórmula Empírica e Peso Molecular",
            "6 Functional Category": "Categoria Funcional",
            "7 Applications in Pharmaceutical Formulation or Technology": "Aplicações em Formulações Farmacêuticas ou Tecnologia",
            "8 Description": "Descrição",
            "9 Pharmacopeial Specifications": "Especificações Farmacopeicas",
            "11 Stability and Storage Conditions": "Estabilidade e Condições de Armazenamento",
            "12 Incompatibilities": "Incompatibilidades",
            "17 Related Substances": "Substâncias Relacionadas"
        }

        pattern = r"## (.*?)\n(.*?)(?=## |$)"
        matches = re.findall(pattern, content, re.DOTALL)

        data = []
        current_excipient = None

        for section, text in matches:
            if not section[0].isdigit():
                current_excipient = section.strip()
            elif section in sections_to_extract and current_excipient:
                translated_text = translate_text(text.strip())
                translated_section = section_translations.get(section, section)
                data.append({
                    "Excipiente": current_excipient,
                    "Seção": translated_section,
                    "Conteúdo": translated_text
                })

        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Erro ao carregar o Handbook.md: {e}")
        return pd.DataFrame()

# Função para exportar os resultados para Excel
def export_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Resultados')
    return output.getvalue()

# Função para limpar os campos
def clear_fields():
    st.session_state["excipient"] = ""
    st.session_state["functional_group"] = ""
    st.session_state["excipient_function"] = ""
    st.session_state["excipient_handbook"] = ""

# Título da aplicação
st.markdown(
    """<h1 style="display: flex; align-items: center; gap: 10px;">
    <img src="https://cdn-icons-png.flaticon.com/512/954/954591.png" alt="Ícone de Lupa" style="width: 40px; height: 40px;">
    Desenvolvimento Racional de Formulações 
    </h1>""",
    unsafe_allow_html=True
)

# Sidebar
st.sidebar.title("Menu de Navegação")
tab = st.sidebar.radio("Selecione uma opção:", ("💊 Consulta de Incompatibilidade", "📘 Conteúdo Handbook", "🔬 Artigos Científicos"))

# Carregar dados
excel_data = load_excel_data()
handbook_data = load_handbook_data()

# Aba de Levantamento
if tab == "💊 Consulta de Incompatibilidade":
    st.subheader("Consulta das Informações")

    # Adicionando mais um filtro
    col1, col2, col3 = st.columns(3)
    with col1:
        excipient_query = st.text_input("Digite o excipiente que deseja consultar:", key="excipient")
    with col2:
        functional_group_query = st.text_input("Digite o grupo funcional que deseja consultar:", key="functional_group")
    with col3:
        excipient_function_query = st.text_input("Digite a função do excipiente:", key="excipient_function")

    if st.button("Buscar", key="search_excel"):
        if not excel_data.empty:
            results = excel_data.copy()

            # Aplicando os filtros progressivamente
            if excipient_query:
                results = results[results['Excipiente'].str.contains(excipient_query, case=False, na=False)]
            if functional_group_query:
                results = results[results['Grupo funcional'].str.contains(functional_group_query, case=False, na=False)]
            if excipient_function_query:
                results = results[results['Classificação do excipiente'].str.contains(excipient_function_query, case=False, na=False)]

            if not results.empty:
                st.subheader("Resultados da Pesquisa")
                st.dataframe(results)
                st.download_button(
                    label="Exportar para Excel",
                    data=export_to_excel(results),
                    file_name="resultados_excel.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.warning("Nenhuma incompatibilidade encontrada.")
        else:
            st.warning("Arquivo Excel não carregado ou vazio.")

    st.button("Limpar Pesquisa", on_click=clear_fields, key="clear_button_excel")


# Aba de Conteúdo do Handbook
elif tab == "📘 Conteúdo Handbook":
    if handbook_data is not None:
        st.subheader("Consulta de Dados do Handbook")

        excipient_query = st.text_input("Digite o excipiente que deseja consultar:", key="excipient_handbook")

        if st.button("Buscar no Handbook", key="search_handbook"):
            results = handbook_data.copy()
            if excipient_query:
                translated_query = translate_text(excipient_query, target_lang='en')
                results = results[results['Excipiente'].str.contains(translated_query, case=False, na=False)]

            if not results.empty:
                st.markdown(f"<h2 style='color: #2C3E50;'>Excipiente: {results['Excipiente'].iloc[0]}</h2>", unsafe_allow_html=True)

                for _, row in results.iterrows():
                    content = row['Conteúdo'] if row['Conteúdo'] is not None else ""
                    st.markdown(
                        f"""
                        <div style='border: 1px solid #2980B9; padding: 15px; border-radius: 10px; margin-bottom: 15px;'>
                            <h3 style='color: #2980B9;'>{row['Seção']}</h3>
                            <p style='font-size: 16px; color: #FFFFFF; line-height: 1.6;'>{content.replace(';', ';<br>')}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                st.download_button(
                    label="Exportar para Excel",
                    data=export_to_excel(results),
                    file_name="resultados_handbook.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.warning("Nenhuma informação encontrada no Handbook.")

        st.button("Limpar Pesquisa", on_click=clear_fields, key="clear_button_handbook")
        
# Aba de Artigos Científicos
elif tab == "🔬 Artigos Científicos":
    app_search.run_article_search()