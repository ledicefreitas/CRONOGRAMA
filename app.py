import io
from datetime import date, timedelta, datetime

import streamlit as st
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.section import WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# ----------------- REGRAS FIXAS DO SEU CALENDÁRIO -----------------
INICIO = date(2025, 8, 6)
FIM = date(2026, 2, 24)

FERIADOS = {
    date(2025, 9, 7),
    date(2025, 10, 12),
    date(2025, 11, 2),
    date(2025, 11, 15),
    date(2025, 11, 20),
    date(2025, 12, 25),
    date(2026, 1, 1),
    date(2026, 2, 17),
}

RECESSOS = [
    (date(2025, 10, 13), date(2025, 10, 17)),
    (date(2025, 12, 15), date(2026, 1, 31)),
    (date(2026, 2, 16), date(2026, 2, 18)),
]

DIAS_NAO_LETIVOS = {date(2025, 10, 29)}  # formatura

# Etapas
ETAPA1 = (date(2025, 8, 6), date(2025, 10, 21))
ETAPA2 = (date(2025, 10, 22), date(2026, 2, 24))

# Dia com conteúdo pré-definido
DATA_MULTIDISCIPLINAR = date(2026, 2, 11)
TEXTO_MULTIDISCIPLINAR = "Avaliação Multidisciplinar"

# ----------------- LÓGICA DE GERAÇÃO -----------------
def gerar_datas(inicio, fim, dias_semana_aulas, feriados, recessos, dias_nao_letivos, total_aulas, compensacoes):
    datas = []
    aulas_geradas = 0
    atual = inicio
    comp_dict = {orig: weekday_comp for orig, weekday_comp in compensacoes}

    while atual <= fim and aulas_geradas < total_aulas:
        weekday = atual.weekday()
        if atual in comp_dict:
            comp_weekday = comp_dict[atual]
            if comp_weekday in dias_semana_aulas:
                qtd_aulas = dias_semana_aulas[comp_weekday]
                for _ in range(qtd_aulas):
                    if aulas_geradas < total_aulas and atual not in datas:
                        datas.append(atual)
                        aulas_geradas += 1
            atual += timedelta(days=1)
            continue

        if weekday in dias_semana_aulas:
            em_recesso = any(r[0] <= atual <= r[1] for r in recessos)
            if atual not in feriados and not em_recesso and atual not in dias_nao_letivos:
                qtd_aulas = dias_semana_aulas[weekday]
                for _ in range(qtd_aulas):
                    if aulas_geradas < total_aulas:
                        datas.append(atual)
                        aulas_geradas += 1
        atual += timedelta(days=1)

    datas.sort()
    return datas

def definir_bordas(celula, tamanho=4, cor="000000"):
    tc = celula._tc
    tcPr = tc.get_or_add_tcPr()
    tblBorders = OxmlElement('w:tcBorders')
    for edge in ('top','left','bottom','right','insideH','insideV'):
        border = OxmlElement(f'w:{edge}')
        border.set(qn('w:val'), 'single')
        border.set(qn('w:sz'), str(tamanho))
        border.set(qn('w:color'), cor)
        tblBorders.append(border)
    tcPr.append(tblBorders)

def adicionar_tabela_etapa(doc, titulo_etapa, periodo, datas_etapa, inicio_index):
    table = doc.add_table(rows=1, cols=5)
    table.autofit = True  # deixa o Word ajustar automaticamente

    hdr = table.rows[0].cells
    hdr[0].merge(hdr[-1])
    p = hdr[0].paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(f"{titulo_etapa} ({periodo[0].strftime('%d/%m/%Y')} a {periodo[1].strftime('%d/%m/%Y')})")
    run.font.color.rgb = RGBColor(255, 255, 255)
    run.font.bold = True
    run.font.name = "Arial"
    run.font.size = Pt(11)

    shading = OxmlElement('w:shd')
    shading.set(qn('w:fill'), "0A1F44")
    hdr[0]._tc.get_or_add_tcPr().append(shading)
    definir_bordas(hdr[0])

    headers = ["DATA", "AULA", "CONTEÚDO", "MATERIAL DE APOIO", "AVALIAÇÃO"]
    row_hdr = table.add_row().cells
    for i, h in enumerate(headers):
        row_hdr[i].text = h
        for cell in table.columns[i].cells:
            definir_bordas(cell)
            for p in cell.paragraphs:
                for r in p.runs:
                    r.font.name = "Arial"
                    r.font.size = Pt(10)
                    r.font.bold = True

    for idx, d in enumerate(datas_etapa, start=inicio_index):
        row_cells = table.add_row().cells
        row_cells[0].text = d.strftime("%d/%m/%Y")
        row_cells[1].text = str(idx)
        row_cells[2].text = TEXTO_MULTIDISCIPLINAR if d == DATA_MULTIDISCIPLINAR else ""
        row_cells[3].text = ""
        row_cells[4].text = ""
        for cell in row_cells:
            definir_bordas(cell)
            for p in cell.paragraphs:
                for r in p.runs:
                    r.font.name = "Arial"
                    r.font.size = Pt(10)
    return inicio_index + len(datas_etapa)

def gerar_docx(disciplina, curso, professor, turma, total_aulas, dias_semana_dict, compensacoes, logo_file):
    datas_aulas = gerar_datas(
        INICIO, FIM,
        dias_semana_dict, FERIADOS, RECESSOS, DIAS_NAO_LETIVOS,
        total_aulas, compensacoes
    )

    doc = Document()
    section = doc.sections[0]
    section.orientation = WD_ORIENT.LANDSCAPE
    section.page_width, section.page_height = section.page_height, section.page_width

    table_header = doc.add_table(rows=1, cols=2)
    table_header.autofit = True

    cell_logo = table_header.rows[0].cells[0]
    if logo_file is not None:
        cell_logo.paragraphs[0].add_run().add_picture(logo_file, width=Pt(60))

    cell_info = table_header.rows[0].cells[1]
    p = cell_info.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(
        f"COLÉGIO EXPOENTE\n"
        f"CURSO TÉCNICO EM {curso}\n"
        f"DISCIPLINA: {disciplina}\n"
        f"Professor(a): {professor}\n"
        f"TURMA: {turma}\n"
        f"CRONOGRAMA 1ª ETAPA e 2ª ETAPA - 2º PERÍODO - 2025"
    )
    run.font.bold = True
    run.font.name = "Arial"
    run.font.size = Pt(12)

    for row in table_header.rows:
        for cell in row.cells:
            definir_bordas(cell)

    doc.add_paragraph("\n")

    datas_etapa1 = [d for d in datas_aulas if ETAPA1[0] <= d <= ETAPA1[1]]
    datas_etapa2 = [d for d in datas_aulas if ETAPA2[0] <= d <= ETAPA2[1]]

    idx = 1
    idx = adicionar_tabela_etapa(doc, "ETAPA 1", ETAPA1, datas_etapa1, idx)
    adicionar_tabela_etapa(doc, "ETAPA 2", ETAPA2, datas_etapa2, idx)

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# ----------------- UI (Streamlit) -----------------
st.set_page_config(page_title="Gerador de Cronograma", page_icon="📅", layout="centered")

st.title("📅 Gerador de Cronograma – Web")
st.caption("Preencha os dados, clique em Gerar e baixe o .docx. Fácil, rápido e sem drama 😉")

with st.form("form"):
    col1, col2 = st.columns(2)
    with col1:
        disciplina = st.text_input("Disciplina*", "")
        curso = st.text_input("Curso*", "Vendas")
        professor = st.text_input("Professor(a)*", "")
    with col2:
        turma = st.text_input("Turma*", "")
        total_aulas = st.number_input("Número total de aulas*", min_value=1, step=1, value=30)
        logo = st.image("https://raw.githubusercontent.com/ledicefreitas/CRONOGRAMA/main/logo%20expoente.png", width=200)

    # Dias da semana interativos
    st.markdown("**Selecione os dias da semana e quantidade de aulas**")
    dias_semana_dict = {}
    dias = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
    for i, dia in enumerate(dias):
        marcar = st.checkbox(dia, key=f"dia_{i}")
        if marcar:
            qtd = st.number_input(f"Aulas na {dia}", min_value=1, step=1, key=f"aulas_{i}")
            dias_semana_dict[i] = qtd

    st.markdown("**Compensações** no formato `dd/mm/aaaa->n` (n = 0 seg ... 6 dom). Ex.: `10/10/2025->2` (horário de quarta).")
    comps_txt = st.text_input("Compensações (opcional)", "10/10/2025->2")

    gerar = st.form_submit_button("Gerar cronograma")

def parse_compensacoes(txt: str):
    res = []
    if not txt.strip():
        return res
    for part in txt.split(","):
        if "->" not in part:
            continue
        data_str, wd_str = part.split("->")
        data_dt = datetime.strptime(data_str.strip(), "%d/%m/%Y").date()
        wd = int(wd_str.strip())
        if wd < 0 or wd > 6:
            raise ValueError("Compensação com weekday inválido (0..6).")
        res.append((data_dt, wd))
    return res

if gerar:
    try:
        compensacoes = parse_compensacoes(comps_txt)
        if not all([disciplina.strip(), curso.strip(), professor.strip(), turma.strip()]):
            st.error("Preencha todos os campos obrigatórios (*)")
        else:
            docx_bytes = gerar_docx(
                disciplina=disciplina.strip(),
                curso=curso.strip(),
                professor=professor.strip(),
                turma=turma.strip(),
                total_aulas=int(total_aulas),
                dias_semana_dict=dias_semana_dict,
                compensacoes=compensacoes,
                logo_file=logo if logo is not None else None
            )
            filename = f"cronograma_{disciplina.strip().replace(' ', '_')}.docx"
            st.success("✅ Cronograma gerado!")
            st.download_button("⬇️ Baixar .docx", data=docx_bytes, file_name=filename, mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    except Exception as e:
        st.error(f"Erro: {e}")
