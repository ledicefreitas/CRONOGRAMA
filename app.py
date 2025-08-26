import io
from datetime import date, timedelta, datetime
import requests

import streamlit as st
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.section import WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import locale

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

# ----------------- DATAS FIXAS -----------------
# Dia com conteúdo pré-definido
DATA_MULTIDISCIPLINAR = date(2026, 2, 11)
TEXTO_MULTIDISCIPLINAR = "Avaliação Multidisciplinar"

# Avaliações de Etapa
AVALIACOES_FIXAS = {
    # Semana da Etapa 1
    **{date(2025, 10, d): "AVALIAÇÃO DE ETAPA 1" for d in range(6, 11)},
    # Dia único da Etapa 2
    **{date(2025, 12, d): "AVALIAÇÃO DE ETAPA 2" for d in range(8, 13)},
    #date(2025, 12, 8): "AVALIAÇÃO DE ETAPA 2",
    # Multidisciplinar
    DATA_MULTIDISCIPLINAR: TEXTO_MULTIDISCIPLINAR
}

# URL da logo no GitHub (RAW)
LOGO_URL = "https://raw.githubusercontent.com/ledicefreitas/CRONOGRAMA/refs/heads/main/logo%20expoente.png"

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

#def adicionar_tabela_etapa(doc, titulo_etapa, periodo, datas_etapa, inicio_index):
#    table = doc.add_table(rows=1, cols=5)
#    table.autofit = True
#
#    hdr = table.rows[0].cells
#    hdr[0].merge(hdr[-1])
#    p = hdr[0].paragraphs[0]
#    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
#    run = p.add_run(f"{titulo_etapa} ({periodo[0].strftime('%d/%m/%Y')} a {periodo[1].strftime('%d/%m/%Y')})")
#    run.font.color.rgb = RGBColor(255, 255, 255)
#    run.font.bold = True
#    run.font.name = "Arial"
#    run.font.size = Pt(11)
#
#    shading = OxmlElement('w:shd')
#    shading.set(qn('w:fill'), "0A1F44")
#    hdr[0]._tc.get_or_add_tcPr().append(shading)
#    definir_bordas(hdr[0])
#
#    headers = ["DATA", "AULA", "CONTEÚDO", "MATERIAL DE APOIO", "AVALIAÇÃO"]
#    row_hdr = table.add_row().cells
#    for i, h in enumerate(headers):
#        row_hdr[i].text = h
#        for cell in table.columns[i].cells:
#            definir_bordas(cell)
#            for p in cell.paragraphs:
#                for r in p.runs:
#                    r.font.name = "Arial"
#                    r.font.size = Pt(10)
#                    r.font.bold = True
#
#    for idx, d in enumerate(datas_etapa, start=inicio_index):
#        row_cells = table.add_row().cells
#        row_cells[0].text = d.strftime("%d/%m/%Y")
#        row_cells[1].text = str(idx)
#        # Usa o texto fixo se a data estiver em AVALIACOES_FIXAS
#        row_cells[2].text = AVALIACOES_FIXAS.get(d, "")
#        row_cells[3].text = ""
#        row_cells[4].text = ""
#        for cell in row_cells:
#            definir_bordas(cell)
#            for p in cell.paragraphs:
#                for r in p.runs:
#                    r.font.name = "Arial"
#                    r.font.size = Pt(10)
#    return inicio_index + len(datas_etapa)


# converte cm -> twips (1 cm ≈ 567 twips)
_CM_TO_TWIPS = 567

def fix_table_grid(table, widths_cm):
    tbl = table._tbl
    tblGrid = OxmlElement('w:tblGrid')
    for w in widths_cm:
        gridCol = OxmlElement('w:gridCol')
        # usar qn para criar o atributo corretamente com namespace
        gridCol.set(qn('w:w'), str(int(w * _CM_TO_TWIPS)))
        tblGrid.append(gridCol)
    # insere o tblGrid no XML da tabela (na posição 0)
    tbl.insert(0, tblGrid)

def adicionar_tabela_etapa(doc, titulo_etapa, periodo, datas_etapa, inicio_index, footer_text=""):
    table = doc.add_table(rows=1, cols=5)
    table.autofit = False
    table.allow_autofit = False

    # larguras em cm
    col_widths = [2.5, 1.5, 12, 2.5, 2.5]
    fix_table_grid(table, col_widths)

    for i, w in enumerate(col_widths):
        for cell in table.columns[i].cells:
            cell.width = Cm(w)

    # Cabeçalho mesclado azul
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

    # Linha de títulos
    headers = ["DATA", "AULA", "CONTEÚDO", "MATERIAL DE APOIO", "AVALIAÇÃO"]
    row_hdr = table.add_row().cells
    for i, h in enumerate(headers):
        row_hdr[i].text = h
        for cell in table.columns[i].cells:
            definir_bordas(cell)
            for p in cell.paragraphs:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for r in p.runs:
                    r.font.name = "Arial"
                    r.font.size = Pt(10)
                    r.font.bold = True

    # >>> ALTERAÇÃO: adicionar linha de mês automaticamente
    ultimo_mes = None

    # Linhas de dados
    for idx, d in enumerate(datas_etapa, start=inicio_index):
        # linha de mês
        if ultimo_mes != d.month:
            meses_pt = [
                        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
                        ]

            mes_texto = f"{meses_pt[d.month - 1]}/{d.year}".upper()  # >>> caixa alta
            #mes_texto = d.strftime("%B/%Y")  # ex: "Outubro 2025"
            month_row = table.add_row().cells
            month_row[0].merge(month_row[-1])
            p_mes = month_row[0].paragraphs[0]
            p_mes.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run_mes = p_mes.add_run(mes_texto)
            run_mes.font.bold = True
            run_mes.font.name = "Arial"
            run_mes.font.size = Pt(10)
            # run_mes.font.color.rgb = RGBColor(255, 255, 255)
            shading = OxmlElement('w:shd')
            # shading.set(qn('w:fill'), "0A1F44")  # azul
            month_row[0]._tc.get_or_add_tcPr().append(shading)
            definir_bordas(month_row[0])
            ultimo_mes = d.month

        # linha normal da aula
        row_cells = table.add_row().cells
        row_cells[0].text = d.strftime("%d/%m/%Y")
        row_cells[1].text = str(idx)
        row_cells[2].text = AVALIACOES_FIXAS.get(d, "")
        row_cells[3].text = ""
        row_cells[4].text = ""
        for i, cell in enumerate(row_cells):
            definir_bordas(cell)
            cell.width = Cm(col_widths[i])
            for p in cell.paragraphs:
                for r in p.runs:
                    r.font.name = "Arial"
                    r.font.size = Pt(10)

    # >>> ALTERAÇÃO: Linha de rodapé com suporte a múltiplas linhas (\n)
    if footer_text:
        footer_row = table.add_row().cells
        footer_row[0].merge(footer_row[-1])
        
        tc = footer_row[0]._tc
        for p in tc.xpath(".//w:p"):
            tc.remove(p)

        for linha in footer_text.split("\n"):
            p = footer_row[0].add_paragraph()
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            run = p.add_run(linha)
            run.font.name = "Arial"
            run.font.size = Pt(10)
            run.font.color.rgb = RGBColor(0, 0, 0)
        shading = OxmlElement('w:shd')
        shading.set(qn('w:fill'), "D9D9D9")  # fundo cinza
        footer_row[0]._tc.get_or_add_tcPr().append(shading)
        definir_bordas(footer_row[0])

    return inicio_index + len(datas_etapa)




#def gerar_docx(disciplina, curso, professor, turma, total_aulas, dias_semana_dict, compensacoes):
#    datas_aulas = gerar_datas(
#        INICIO, FIM,
#        dias_semana_dict, FERIADOS, RECESSOS, DIAS_NAO_LETIVOS,
#        total_aulas, compensacoes
#    )
#
#    doc = Document()
#    section = doc.sections[0]
#    section.orientation = WD_ORIENT.LANDSCAPE
#    section.page_width, section.page_height = section.page_height, section.page_width
#
#    table_header = doc.add_table(rows=1, cols=2)
#    table_header.autofit = True
#
#    # Baixar logo direto do GitHub
#    try:
#        response = requests.get(LOGO_URL)
#        if response.status_code == 200:
#            logo_bytes = io.BytesIO(response.content)
#            cell_logo = table_header.rows[0].cells[0]
#            cell_logo.paragraphs[0].add_run().add_picture(logo_bytes, width=Pt(60))
#    except Exception:
#        pass  # se não carregar a logo, segue sem ela
#
#    cell_info = table_header.rows[0].cells[1]
#    p = cell_info.paragraphs[0]
#    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
#    run = p.add_run(
#        f"COLÉGIO EXPOENTE\n"
#        f"CURSO TÉCNICO EM {curso}\n"
#        f"DISCIPLINA: {disciplina}\n"
#        f"Professor(a): {professor}\n"
#        f"TURMA: {turma}\n"
#        f"CRONOGRAMA 1ª ETAPA e 2ª ETAPA - 2º PERÍODO - 2025"
#    )
#    run.font.bold = True
#    run.font.name = "Arial"
#    run.font.size = Pt(12)
#
#    for row in table_header.rows:
#        for cell in row.cells:
#            definir_bordas(cell)
#
#    doc.add_paragraph("\n")
#
#    datas_etapa1 = [d for d in datas_aulas if ETAPA1[0] <= d <= ETAPA1[1]]
#    datas_etapa2 = [d for d in datas_aulas if ETAPA2[0] <= d <= ETAPA2[1]]
#
#    idx = 1
#    idx = adicionar_tabela_etapa(doc, "ETAPA 1", ETAPA1, datas_etapa1, idx)
#    adicionar_tabela_etapa(doc, "ETAPA 2", ETAPA2, datas_etapa2, idx)
#
#    buffer = io.BytesIO()
#    doc.save(buffer)
#    buffer.seek(0)
#    return buffer

def gerar_docx(disciplina, curso, professor, turma, total_aulas, dias_semana_dict, compensacoes):
    datas_aulas = gerar_datas(
        INICIO, FIM,
        dias_semana_dict, FERIADOS, RECESSOS, DIAS_NAO_LETIVOS,
        total_aulas, compensacoes
    )

    doc = Document()
    section = doc.sections[0]
    section.orientation = WD_ORIENT.LANDSCAPE
    section.page_width, section.page_height = section.page_height, section.page_width

    # Cabeçalho com 2 colunas
    table_header = doc.add_table(rows=1, cols=2)
    table_header.autofit = False
    table_header.allow_autofit = False

    # fixa largura 2 cm + 18,5 cm
    fix_table_grid(table_header, [3.5, 17.5])
    for i, w in enumerate([3.5, 17.5]):
        for cell in table_header.columns[i].cells:
            cell.width = Cm(w)

    # Baixar logo direto do GitHub
    # try:
    #     response = requests.get(LOGO_URL)
    #     if response.status_code == 200:
    #         logo_bytes = io.BytesIO(response.content)
    #         cell_logo = table_header.rows[0].cells[0]
    #         cell_logo.paragraphs[0].add_run().add_picture(logo_bytes, width=Pt(60))
    # except Exception:
    #     pass  # se não carregar a logo, segue sem ela

    try:
        response = requests.get(LOGO_URL)
        if response.status_code == 200:
            logo_bytes = io.BytesIO(response.content)
            cell_logo = table_header.rows[0].cells[0]

            # limpa qualquer parágrafo vazio pré-existente
            cell_logo.text = ""

            # cria um parágrafo novo, centralizado
            p_logo = cell_logo.add_paragraph()
            p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER

            # adiciona a imagem com tamanho maior (ex: 2.5 cm de largura)
            run_logo = p_logo.add_run()
            run_logo.add_picture(logo_bytes, width=Cm(2.5))
    except Exception:
        pass  # se não carregar a logo, segue sem ela

    # Texto da direita
    #cell_info = table_header.rows[0].cells[1]
    #p = cell_info.paragraphs[0]
    #p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    #run = p.add_run(
    #    f"COLÉGIO EXPOENTE\n"
    #    f"CURSO TÉCNICO EM {curso}\n"
    #    f"CRONOGRAMA 1ª ETAPA e 2ª ETAPA - 2º PERÍODO - 2025\n"
    #    f"DISCIPLINA: {disciplina}\n"
    #    f"Professor(a): {professor}\n"
    #    f"TURMA: {turma}           CARGA HORARIA: {total_aulas}h/a".upper()
    #)
    #run.font.bold = True
    #run.font.name = "Arial"
    #run.font.size = Pt(12)

    
    
    cell_info = table_header.rows[0].cells[1]

    # Zera margens internas da célula
    cell_info.top_margin = Pt(0)
    cell_info.bottom_margin = Pt(0)
    cell_info.left_margin = Pt(0)
    cell_info.right_margin = Pt(0)

    cell_info.text = ""  # Limpa conteúdo existente

    # 3 primeiras linhas - centralizado e negrito
    p1 = cell_info.paragraphs[0]
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p1.paragraph_format.space_before = Pt(0)
    p1.paragraph_format.space_after = Pt(0)

    for linha in [
        "COLÉGIO EXPOENTE",
        f"CURSO TÉCNICO EM {curso}".upper(),
        "CRONOGRAMA 1ª ETAPA e 2ª ETAPA - 2º PERÍODO - 2025"
    ]:
        run = p1.add_run(linha + "\n")
        run.font.bold = True
        run.font.name = "Arial"
        run.font.size = Pt(12)

    # 3 últimas linhas - alinhadas à esquerda, sem negrito
    p2 = cell_info.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p2.paragraph_format.space_before = Pt(0)
    p2.paragraph_format.space_after = Pt(0)

    ultimas = [
        f"DISCIPLINA: {disciplina}".upper(),
        f"Professor(a): {professor}".upper(),
        f"TURMA: {turma}                                               CARGA HORARIA: {total_aulas}h/a".upper()
    ]

    for i, linha in enumerate(ultimas):
        texto = linha if i == len(ultimas)-1 else linha + "\n"
        run = p2.add_run(texto)
        run.font.bold = False
        run.font.name = "Arial"
        run.font.size = Pt(12)

    # Bordas
    for row in table_header.rows:
        for cell in row.cells:
            definir_bordas(cell)

    doc.add_paragraph("\n")

    # Divide etapas
    datas_etapa1 = [d for d in datas_aulas if ETAPA1[0] <= d <= ETAPA1[1]]
    datas_etapa2 = [d for d in datas_aulas if ETAPA2[0] <= d <= ETAPA2[1]]

    idx = 1
    #idx = adicionar_tabela_etapa(doc, "ETAPA 1", ETAPA1, datas_etapa1, idx)
    #adicionar_tabela_etapa(doc, "ETAPA 2", ETAPA2, datas_etapa2, idx)

    rodape_etapa1 = "Obs: Na 1ª etapa serão trabalhadas 02 práticas de formação: \n1ª prática – deverá ser aplicada até o dia 05/09/25 \n2ª prática – deverá ser aplicada até o dia 03/10/25 \nAs datas das práticas devem constar no cronograma de aulas."
    rodape_etapa2 = "Obs: Na 2ª etapa serão trabalhadas 02 práticas de formação: \n1ª prática – deverá ser aplicada até o dia xx/xx/25 \n2ª prática – deverá ser aplicada até o dia xx/xx/xx \nAs datas das práticas devem constar no cronograma de aulas."
    #"Obs: Na 2ª etapa, a prática de formação será avaliada através da Expotec Expoente no dia 01/07/25."
    idx = adicionar_tabela_etapa(doc, "ETAPA 1", ETAPA1, datas_etapa1, idx, footer_text=rodape_etapa1)
    adicionar_tabela_etapa(doc, "ETAPA 2", ETAPA2, datas_etapa2, idx, footer_text=rodape_etapa2)



    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer


# ----------------- UI (Streamlit) -----------------
st.set_page_config(page_title="Gerador de Cronograma", page_icon="📅", layout="centered")

st.title("📅 Gerador Modelo de Cronograma ")
st.caption("Preencha os dados, clique em Gerar e baixe o .docx já com as \ndatas preenchidas. Fácil, rápido e sem drama 😉")

# ---- FORMULÁRIO PRINCIPAL ----
with st.form("form"):
    col1, col2 = st.columns(2)
    with col1:
        disciplina = st.text_input("Disciplina*", "")
        curso = st.text_input("Curso*", "Vendas")
        professor = st.text_input("Professor(a)* (Nome Completo)", "")
    with col2:
        turma = st.text_input("Turma*", "")
        total_aulas = st.number_input("Número total de aulas*", min_value=1, step=1, value=30)

    gerar = st.form_submit_button("Gerar cronograma")

# ---- DIAS DA SEMANA (FORA DO FORM PARA SER REATIVO) ----
st.markdown("**Selecione os dias da semana e quantidade de aulas**")
dias_semana_dict = {}
dias = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
for i, dia in enumerate(dias):
    marcar = st.checkbox(dia, key=f"dia_{i}")
    if marcar:
        qtd = st.number_input(f"Aulas na {dia}", min_value=1, step=1, key=f"aulas_{i}")
        dias_semana_dict[i] = qtd

# ---- COMPENSAÇÕES ----
st.markdown("**Compensações** no formato `dd/mm/aaaa->n` (n = 0 seg ... 6 dom). Ex.: `10/10/2025->2` (horário de quarta).")
comps_txt = st.text_input("Compensações (opcional)", "10/10/2025->2")

# ----------------- FUNÇÃO AUXILIAR -----------------
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

# ----------------- BOTÃO GERAR -----------------
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
                compensacoes=compensacoes
            )
            filename = f"cronograma_{disciplina.strip().replace(' ', '_')}.docx"
            st.success("✅ Cronograma gerado!")
            st.download_button("⬇️ Baixar .docx", data=docx_bytes, file_name=filename, mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    except Exception as e:
        st.error(f"Erro: {e}")
