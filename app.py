import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests
from io import BytesIO
from docx import Document
from docx.shared import Inches
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

st.title("📅 Gerador de Cronograma de Aulas")

# ------------------------------
# Função para aplicar bordas em tabelas do Word
# ------------------------------
def definir_bordas(cell):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = OxmlElement('w:tcBorders')
    for b in ("top", "left", "bottom", "right"):
        border = OxmlElement(f"w:{b}")
        border.set(qn("w:val"), "single")
        border.set(qn("w:sz"), "6")
        border.set(qn("w:space"), "0")
        border.set(qn("w:color"), "000000")
        tcBorders.append(border)
    tcPr.append(tcBorders)

# ------------------------------
# Logo direto do GitHub
# ------------------------------
logo_url = "https://raw.githubusercontent.com/ledicefreitas/CRONOGRAMA/main/logo%20expoente.png"
response = requests.get(logo_url)
logo_image = BytesIO(response.content)

# ------------------------------
# Formulário principal
# ------------------------------
with st.form("form"):
    col1, col2 = st.columns(2)
    with col1:
        disciplina = st.text_input("Disciplina*", "")
        curso = st.text_input("Curso*", "Vendas")
        professor = st.text_input("Professor(a)*", "")
    with col2:
        turma = st.text_input("Turma*", "")
        total_aulas = st.number_input("Número total de aulas*", min_value=1, step=1, value=30)
        data_inicio = st.date_input("Data de início*", value=datetime(2025, 8, 4))

    gerar = st.form_submit_button("Gerar cronograma")

# ------------------------------
# Seleção de dias da semana
# ------------------------------
st.markdown("### 📌 Dias da semana e quantidade de aulas")
dias_semana_dict = {}
dias = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
for i, dia in enumerate(dias):
    marcar = st.checkbox(dia, key=f"dia_{i}")
    if marcar:
        qtd = st.number_input(f"Aulas na {dia}", min_value=1, step=1, key=f"aulas_{i}")
        dias_semana_dict[i] = qtd

# ------------------------------
# Compensações
# ------------------------------
st.markdown("### 🔄 Compensações")
st.markdown("Formato: `dd/mm/aaaa->n` (n = 0 seg ... 6 dom). Exemplo: `10/10/2025->2`")
comps_txt = st.text_input("Compensações (opcional)", "10/10/2025->2")

# ------------------------------
# Datas fixas: avaliações
# ------------------------------
avaliacoes = [
    {"nome": "ETAPA 1", "inicio": datetime(2025, 10, 6).date(), "fim": datetime(2025, 10, 10).date()},
    {"nome": "ETAPA 2", "inicio": datetime(2025, 12, 8).date(), "fim": datetime(2025, 12, 8).date()},
    {"nome": "Multidisciplinar", "inicio": datetime(2025, 9, 25).date(), "fim": datetime(2025, 9, 25).date()},
]

# ------------------------------
# Gerar cronograma
# ------------------------------
if gerar:
    if not disciplina or not professor or not turma:
        st.error("⚠️ Preencha todos os campos obrigatórios!")
    elif not dias_semana_dict:
        st.error("⚠️ Selecione pelo menos um dia da semana!")
    else:
        # Processar compensações
        compensacoes = {}
        if comps_txt.strip():
            for item in comps_txt.split(","):
                try:
                    data_str, dia_semana = item.split("->")
                    data = datetime.strptime(data_str.strip(), "%d/%m/%Y").date()
                    compensacoes[data] = int(dia_semana)
                except:
                    pass

        # Construir cronograma
        data_atual = data_inicio
        aulas_restantes = total_aulas
        registros = []

        while aulas_restantes > 0:
            dia_semana = data_atual.weekday()
            if data_atual in compensacoes:
                dia_semana = compensacoes[data_atual]

            # Verificar se data é semana de avaliação
            avaliacao_nome = None
            for etapa in avaliacoes:
                if etapa["inicio"] <= data_atual <= etapa["fim"]:
                    avaliacao_nome = etapa["nome"]

            if avaliacao_nome:
                registros.append((data_atual.strftime("%d/%m/%Y"), f"AVALIAÇÃO DE {avaliacao_nome}"))
            elif dia_semana in dias_semana_dict:
                qtd_aulas = min(dias_semana_dict[dia_semana], aulas_restantes)
                registros.append((data_atual.strftime("%d/%m/%Y"), f"{qtd_aulas} aulas"))
                aulas_restantes -= qtd_aulas

            data_atual += timedelta(days=1)

        # Criar DataFrame
        df = pd.DataFrame(registros, columns=["Data", "Atividade"])
        st.dataframe(df)

        # Criar documento Word
        doc = Document()
        sec = doc.sections[0]
        header = sec.header
        pl = header.add_paragraph()
        run = pl.add_run()
        run.add_picture(logo_image, width=Inches(0.9))
        pl.add_run(f"\n{curso} - {turma}\nProfessor(a): {professor}")

        doc.add_paragraph(f"Disciplina: {disciplina}")
        doc.add_paragraph(f"Total de aulas: {total_aulas}")
        doc.add_paragraph("")

        tabela = doc.add_table(rows=1, cols=2)
        hdr = tabela.rows[0].cells
        hdr[0].text = "Data"
        hdr[1].text = "Atividade"
        for cell in hdr:
            definir_bordas(cell)

        for data, atividade in registros:
            row = tabela.add_row().cells
            row[0].text = data
            row[1].text = atividade
            for cell in row:
                definir_bordas(cell)

        output = BytesIO()
        doc.save(output)
        st.download_button("📥 Baixar cronograma em Word", data=output.getvalue(), file_name="cronograma.docx")
