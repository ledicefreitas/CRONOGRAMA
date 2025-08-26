import streamlit as st
from datetime import datetime, timedelta
from docx import Document
from docx.shared import Inches
import requests
from io import BytesIO

# ------------------------------
# Função para criar documento
# ------------------------------
def gerar_cronograma(disciplina, curso, professor, turma, total_aulas, dias_semana_dict, compensacoes, logo_url):
    doc = Document()

    # Cabeçalho com logo
    if logo_url:
        response = requests.get(logo_url)
        if response.status_code == 200:
            logo_img = BytesIO(response.content)
            doc.add_picture(logo_img, width=Inches(0.9))

    doc.add_heading("CRONOGRAMA DE AULAS", level=1)

    doc.add_paragraph(f"Disciplina: {disciplina}")
    doc.add_paragraph(f"Curso: {curso}")
    doc.add_paragraph(f"Professor(a): {professor}")
    doc.add_paragraph(f"Turma: {turma}")
    doc.add_paragraph(f"Total de aulas: {total_aulas}")
    doc.add_paragraph("")

    # ------------------------------
    # Datas fixas já existentes
    # ------------------------------
    datas_fixas = {
        datetime(2025, 9, 25): "Avaliação Multidisciplinar",
        datetime(2025, 11, 20): "Dia da Consciência Negra",
    }

    # ------------------------------
    # Semana de provas (etapas)
    # ------------------------------
    etapa1_inicio = datetime(2025, 10, 6)
    etapa1_fim = datetime(2025, 10, 10)
    for i in range((etapa1_fim - etapa1_inicio).days + 1):
        datas_fixas[etapa1_inicio + timedelta(days=i)] = "AVALIAÇÃO DE ETAPA 1"

    etapa2 = datetime(2025, 12, 8)
    datas_fixas[etapa2] = "AVALIAÇÃO DE ETAPA 2"

    # ------------------------------
    # Início do cronograma
    # ------------------------------
    data_inicio = datetime(2025, 8, 4)  # data de início padrão
    aulas_restantes = total_aulas
    cronograma = []

    while aulas_restantes > 0 and data_inicio.year == 2025:
        dia_semana = data_inicio.weekday()  # 0=Segunda ... 6=Domingo
        atividade = ""

        if data_inicio in datas_fixas:
            atividade = datas_fixas[data_inicio]
        elif dia_semana in dias_semana_dict:
            qtd_aulas = dias_semana_dict[dia_semana]
            if aulas_restantes >= qtd_aulas:
                atividade = f"{qtd_aulas} aulas"
                aulas_restantes -= qtd_aulas
            else:
                atividade = f"{aulas_restantes} aulas"
                aulas_restantes = 0

        # Compensações
        if data_inicio.strftime("%d/%m/%Y") in compensacoes:
            atividade = f"Compensação -> {compensacoes[data_inicio.strftime('%d/%m/%Y')]}"

        if atividade:
            cronograma.append((data_inicio.strftime("%d/%m/%Y"), atividade))

        data_inicio += timedelta(days=1)

    # ------------------------------
    # Escrevendo no Word
    # ------------------------------
    table = doc.add_table(rows=1, cols=2)
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = "Data"
    hdr_cells[1].text = "Atividade"

    for data, atividade in cronograma:
        row_cells = table.add_row().cells
        row_cells[0].text = data
        row_cells[1].text = atividade

    return doc


# ------------------------------
# Interface Streamlit
# ------------------------------
st.title("Gerador de Cronograma de Aulas")

with st.form("form"):
    col1, col2 = st.columns(2)
    with col1:
        disciplina = st.text_input("Disciplina*", "")
        curso = st.text_input("Curso*", "Vendas")
        professor = st.text_input("Professor(a)*", "")
    with col2:
        turma = st.text_input("Turma*", "")
        total_aulas = st.number_input("Número total de aulas*", min_value=1, step=1, value=30)

    gerar = st.form_submit_button("Gerar cronograma")

# Seleção de dias da semana fora do form
st.markdown("**Selecione os dias da semana e quantidade de aulas**")
dias_semana_dict = {}
dias = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
for i, dia in enumerate(dias):
    marcar = st.checkbox(dia, key=f"dia_{i}")
    if marcar:
        qtd = st.number_input(f"Aulas na {dia}", min_value=1, step=1, key=f"aulas_{i}")
        dias_semana_dict[i] = qtd

st.markdown("**Compensações** no formato `dd/mm/aaaa->n` (n = 0 seg ... 6 dom).")
comps_txt = st.text_input("Compensações (opcional)", "10/10/2025->2")
compensacoes = {}
if comps_txt:
    for item in comps_txt.split(","):
        try:
            data, dia = item.split("->")
            compensacoes[data.strip()] = int(dia.strip())
        except:
            pass

# Logo direto do GitHub
logo_url = "https://raw.githubusercontent.com/ledicefreitas/CRONOGRAMA/main/logo%20expoente.png"

# Geração
if gerar:
    doc = gerar_cronograma(disciplina, curso, professor, turma, total_aulas, dias_semana_dict, compensacoes, logo_url)

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    st.download_button(
        label="📥 Baixar cronograma",
        data=buffer,
        file_name="cronograma.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
