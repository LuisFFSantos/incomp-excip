import streamlit as st
import requests
import pandas as pd
import re
from io import BytesIO

# Função para destacar o termo pesquisado nos textos
def highlight_text(text, keyword):
    if not text or not keyword:
        return text
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    return pattern.sub(f'<mark>{keyword}</mark>', text)

# Função principal para busca de artigos científicos
def run_article_search():
    # Opções de pesquisa para o usuário escolher
    search_options = {
        "Incompatibilidades de Excipientes": "excipient incompatibility",
        "Formulações Farmacêuticas": "excipient formulation",
        "Interação com Fármacos": "drug interaction",
        "Tecnologia Farmacêutica": "pharmaceutical technology"
    }

    # APIs disponíveis para busca
    api_options = ["Semantic Scholar", "CORE", "PubMed", "Todos"]

    # Inicializando a sessão de estado para armazenar os valores dos campos
    if "results" not in st.session_state:
        st.session_state.results = pd.DataFrame()
    if "excipient" not in st.session_state:
        st.session_state.excipient = ""
    if "search_type" not in st.session_state:
        st.session_state.search_type = list(search_options.keys())[0]
    if "min_year" not in st.session_state:
        st.session_state.min_year = 2000
    if "sort_by" not in st.session_state:
        st.session_state.sort_by = "Relevância"
    if "advanced_query" not in st.session_state:
        st.session_state.advanced_query = ""

    # Interface do Streamlit
    st.subheader("Busca de Artigos Científicos")

    # Entrada do usuário
    st.session_state.excipient = st.text_input("Digite o nome do excipiente:", value=st.session_state.excipient)
    st.session_state.search_type = st.selectbox("Escolha o tipo de pesquisa:", list(search_options.keys()), index=list(search_options.keys()).index(st.session_state.search_type))

    # Filtros de "Ano mínimo" e "Ordenar por" lado a lado
    col1, col2 = st.columns([1, 1])
    with col1:
        st.session_state.min_year = st.number_input("Ano mínimo de publicação:", min_value=1900, max_value=2025, value=st.session_state.min_year, step=1)
    with col2:
        st.session_state.sort_by = st.selectbox("Ordenar por:", ["Relevância", "Ano"], index=["Relevância", "Ano"].index(st.session_state.sort_by))

    # Campo para pesquisa avançada
    st.session_state.advanced_query = st.text_input("Busca avançada (opcional):", value=st.session_state.advanced_query)

    # Escolha do Site para busca
    api_choice = st.selectbox("Escolha o Site para busca:", api_options)

    # Função para buscar artigos na API do Semantic Scholar
    def search_semantic_scholar(excipient, search_type):
        query = f"{excipient} {search_type}"
        url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={query}&fields=title,url,authors,year,journal,abstract&limit=10"

        response = requests.get(url)
        if response.status_code != 200:
            return []

        data = response.json()
        results = []
        for paper in data.get("data", []):
            year = paper.get("year", None)
            if st.session_state.min_year and year and year < st.session_state.min_year:
                continue

            results.append({
                "Título": paper.get("title", "Título não disponível"),
                "Link": paper.get("url", "Sem link disponível"),
                "Autores": ", ".join([author["name"] for author in paper.get("authors", [])]) if paper.get("authors") else "Autor desconhecido",
                "Ano": year,
                "Revista": paper.get("journal")["name"] if paper.get("journal") else "Revista desconhecida",
                "Resumo": paper.get("abstract", "Resumo não disponível")
            })

        return pd.DataFrame(results)  # Retornar diretamente como DataFrame

    # Botão de busca
    if st.button("Buscar"):
        if st.session_state.excipient.strip() == "":
            st.warning("Por favor, digite o nome de um excipiente.")
        else:
            with st.spinner("Buscando artigos..."):
                st.session_state.results = search_semantic_scholar(st.session_state.excipient, search_options[st.session_state.search_type])

                if st.session_state.sort_by == "Ano" and not st.session_state.results.empty:
                    st.session_state.results = st.session_state.results.sort_values(by="Ano", ascending=False)

    # Exibir resultados
    if not st.session_state.results.empty:
        st.subheader("📄 Artigos encontrados:")
        for idx, row in st.session_state.results.iterrows():
            highlighted_title = highlight_text(row["Título"], st.session_state.excipient)
            highlighted_abstract = highlight_text(row["Resumo"], st.session_state.excipient)

            st.markdown(f"### {idx+1}. {highlighted_title}", unsafe_allow_html=True)
            st.markdown(f"📅 **Ano:** {row['Ano']} | 🏛 **Revista:** {row['Revista']}")
            st.markdown(f"👨‍🔬 **Autores:** {row['Autores']}")
            st.markdown(f"📖 **Resumo:** {highlighted_abstract}", unsafe_allow_html=True)
            st.markdown(f"[🔗 Acesse o artigo]({row['Link']})")
            st.markdown("---")

        # Criando botão para exportar os resultados
        excel_data = BytesIO()
        with pd.ExcelWriter(excel_data, engine="xlsxwriter") as writer:
            st.session_state.results.to_excel(writer, index=False, sheet_name="Artigos")
        excel_data.seek(0)

        st.download_button("📥 Baixar Resultados (Excel)", data=excel_data, file_name="artigos.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # Botão para limpar tudo (campos e resultados)
    if st.button("🗑️ Limpar Tudo"):
        st.session_state.results = pd.DataFrame()
        st.session_state.excipient = ""
        st.session_state.search_type = list(search_options.keys())[0]
        st.session_state.min_year = 2000
        st.session_state.sort_by = "Relevância"
        st.session_state.advanced_query = ""
        st.rerun()
