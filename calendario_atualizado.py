import json
import locale
import streamlit as st
from datetime import datetime, timedelta, date
from collections import Counter
import pandas as pd
import calendar
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from uuid import uuid4



try:
    locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")
except:
    locale.setlocale(locale.LC_TIME, "Portuguese_Brazil.1252")


# ----------------- Funções auxiliares -----------------
def datas_sobrepostas(inicio1, fim1, inicio2, fim2):
    return not (fim1 < inicio2 or fim2 < inicio1)

def dentro_do_periodo(data, inicio, fim):
    return inicio <= data <= fim

def ja_existe(data, lista):
    return data.strftime("%Y-%m-%d") in lista

def gerar_datas_intervalo(inicio, fim):
    """Gera lista de datas (YYYY-MM-DD) entre inicio e fim"""
    datas = []
    atual = inicio
    while atual <= fim:
        datas.append(atual.strftime("%Y-%m-%d"))
        atual += timedelta(days=1)
    return datas

# ----------------- Carregar JSON -----------------
with open("calendario.json", "r", encoding="utf-8") as f:
    calendario = json.load(f)

from uuid import uuid4

if "rodapes" not in st.session_state:
    st.session_state.rodapes = calendario.get("rodapes", {})

# --- Inicialização / Migração Compensações ---
if "compensacoes" not in st.session_state:
    # Carrega do JSON só na primeira execução
    st.session_state.compensacoes = []
    for c in calendario.get("compensacoes", []):
        try:
            st.session_state.compensacoes.append({"id": uuid4().hex, "data": c[0], "dia": int(c[1])})
        except Exception:
            pass

# Se estava no formato antigo (lista de listas), migra para dicts com id
if st.session_state.compensacoes and isinstance(st.session_state.compensacoes[0], list):
    migrated = []
    for item in st.session_state.compensacoes:
        try:
            migrated.append({"id": uuid4().hex, "data": item[0], "dia": int(item[1])})
        except Exception:
            continue
    st.session_state.compensacoes = migrated



st.title("Configuração Calendário Escolar")

# ----------------- Agrupar Avaliações em Intervalos -----------------
if "avaliacoes_etapas" not in st.session_state:
    avaliacoes_json = calendario.get("avaliacoes", {})
    agrupadas = {}
    for data_str, desc in avaliacoes_json.items():
        desc_lower = desc.lower()
        if "avaliação de etapa" in desc_lower:
            try:
                etapa_num = desc_lower.split("avaliação de etapa")[-1].strip()
            except:
                etapa_num = "1"  # fallback
            if etapa_num not in agrupadas:
                agrupadas[etapa_num] = []
            agrupadas[etapa_num].append(datetime.strptime(data_str, "%Y-%m-%d").date())

    st.session_state.avaliacoes_etapas = {
        f"etapa{etapa}": [
            min(datas).strftime("%Y-%m-%d"),
            max(datas).strftime("%Y-%m-%d")
        ]
        for etapa, datas in agrupadas.items()
    }

# ----------------- Período Letivo -----------------
with st.container():
    st.markdown("""
        <div style="border:2px solid #004aad; border-radius:8px;background-color:#e6f0ff; padding:10px; margin-top:20px;">
            <h4 style="color:#004aad; font-weight:bold; text-align:center;">Período Letivo</h4>
        </div>
    """, unsafe_allow_html=True)
    #st.subheader("Período Letivo")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            "<p style='color:#004aad; font-weight:bold; text-align:center;'>Data de Início</p>", 
            unsafe_allow_html=True
        )
        #inicio = st.date_input(" ", datetime.strptime(calendario["inicio"], "%Y-%m-%d").date())
        inicio = st.date_input(
            label="Inicio",  # ainda precisa de algo como identificador
            value=datetime.strptime(calendario["inicio"], "%Y-%m-%d").date(),
            label_visibility="collapsed"
        )
    with col2:
        # fim = st.date_input(" ", datetime.strptime(calendario["fim"], "%Y-%m-%d").date())
        st.markdown(
            "<p style='color:#004aad; font-weight:bold; text-align:center;'>Data de fim</p>", 
            unsafe_allow_html=True
        )
        fim = st.date_input(
            label="Fim",  # ainda precisa de algo como identificador
            value=datetime.strptime(calendario["fim"], "%Y-%m-%d").date(),
            label_visibility="collapsed"
        )

# Inicializar session_state
if "recessos" not in st.session_state:
    st.session_state.recessos = calendario.get("recessos", [])
if "dias_nao_letivos" not in st.session_state:
    st.session_state.dias_nao_letivos = calendario.get("dias_nao_letivos", [])
if "etapas" not in st.session_state:
    st.session_state.etapas = calendario.get("etapas", {})
if "avaliacoes_etapas" not in st.session_state:
    st.session_state.avaliacoes_etapas = {}
if "avaliacao_multidisciplinar" not in st.session_state:
    multi = [d for d, v in calendario.get("avaliacoes", {}).items() if "multidisciplinar" in v.lower()]
    st.session_state.avaliacao_multidisciplinar = multi[0] if multi else None

# ----------------- Recessos -----------------
with st.container():
    st.markdown("""
        <div style="border:2px solid #004aad; border-radius:8px;background-color:#e6f0ff; padding:10px; margin-top:20px;">
            <h4 style="color:#004aad; font-weight:bold; text-align:center;">Recessos</h4>
        </div>
    """, unsafe_allow_html=True)
    #st.subheader("Recessos")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            "<p style='color:#004aad; font-weight:bold; text-align:center;'>Adicionar Novo Recesso - Início</p>", 
            unsafe_allow_html=True
        )
        novo_inicio_rec = st.date_input(
            label = "Adicionar Novo Recesso - Início", 
            value = inicio, key="novo_inicio_rec",
            label_visibility="collapsed"
            )
    with col2:
        st.markdown(
            "<p style='color:#004aad; font-weight:bold; text-align:center;'>Adicionar Novo Recesso - Fim</p>", 
            unsafe_allow_html=True
        )
        novo_fim_rec = st.date_input(
            label = "Novo recesso - Fim", 
            value = fim, key="novo_fim_rec",
            label_visibility="collapsed"
            )
        #novo_fim_rec = st.date_input("Novo recesso - Fim", fim, key="novo_fim_rec")

st.markdown("""
    <style>
    div.stButton > button:first-child {
        background-color: #3498DB;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        height: 40px;
    }
    div.stButton > button:hover {
        background-color: #2980B9;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

if st.button("Adicionar recesso"):
    if dentro_do_periodo(novo_inicio_rec, inicio, fim) and dentro_do_periodo(novo_fim_rec, inicio, fim):
        conflito = False
        for rec in st.session_state.recessos:
            if datas_sobrepostas(
                novo_inicio_rec, novo_fim_rec,
                datetime.strptime(rec[0], "%Y-%m-%d").date(),
                datetime.strptime(rec[1], "%Y-%m-%d").date()
            ):
                st.error("⚠️ Conflito com recesso existente!")
                conflito = True
                break
        if not conflito:
            st.session_state.recessos.append([
                novo_inicio_rec.strftime("%Y-%m-%d"),
                novo_fim_rec.strftime("%Y-%m-%d")
            ])
    else:
        st.error("⚠️ Recesso fora do período letivo!")

st.markdown(
            "<h5 style='color:#004aad; font-weight:bold; text-align:center;'>Recessos Cadastrados</h5>", 
            unsafe_allow_html=True
        )
# Editar/remover recessos
recessos_novos = []
for i, rec in enumerate(st.session_state.recessos):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            f"<p style='color:#004aad; font-weight:bold; text-align:center;'>Recessos Cadastrados {i+1}</p>", 
            unsafe_allow_html=True
        )
        inicio_rec = st.date_input(
            label = "Início recesso {i+1}", 
            value = datetime.strptime(rec[0], "%Y-%m-%d").date(), key=f"inicio_{i}",
            label_visibility="collapsed"
            )
        #inicio_rec = st.date_input(
        #    f"Início recesso {i+1}",
        #    datetime.strptime(rec[0], "%Y-%m-%d").date(),
        #    key=f"inicio_{i}"
        #)
    with col2:
        st.markdown(
            f"<p style='color:#004aad; font-weight:bold; text-align:center;'>Fim recesso {i+1}</p>", 
            unsafe_allow_html=True
        )
        fim_rec = st.date_input(
            label = "Fim recesso {i+1}", 
            value = datetime.strptime(rec[1], "%Y-%m-%d").date(), key=f"fim_{i}",
            label_visibility="collapsed"
            )
        #fim_rec = st.date_input(
        #    f"Fim recesso {i+1}",
        #    datetime.strptime(rec[1], "%Y-%m-%d").date(),
        #    key=f"fim_{i}"
        #)

    colb1, colb2 = st.columns([0.8, 0.2])
    remover = False
    with colb2:
        if st.button("Remover", key=f"remover_recesso_{i}"):
            remover = True  

    if not remover:
        recessos_novos.append([
            inicio_rec.strftime("%Y-%m-%d"),
            fim_rec.strftime("%Y-%m-%d")
        ])
st.session_state.recessos = recessos_novos

# ----------------- Dias Não Letivos -----------------
with st.container():
    st.markdown("""
        <div style="border:2px solid #004aad; border-radius:8px;background-color:#e6f0ff; padding:10px; margin-top:20px;">
            <h4 style="color:#004aad; font-weight:bold; text-align:center;">Dias Não Letivos</h4>
        </div>
    """, unsafe_allow_html=True)
#st.subheader("Dias Não Letivos")
st.markdown(
            f"<p style='color:#004aad; font-weight:bold; text-align:center;'>Adicionar novo dia não letivo</p>", 
            unsafe_allow_html=True
        )
novo_dia = st.date_input(
    label = "Adicionar novo dia não letivo", 
    value = datetime.strptime(rec[0], "%Y-%m-%d").date(), key="novo_dia",
    label_visibility="collapsed"
)
#novo_dia = st.date_input("Adicionar novo dia não letivo", key="novo_dia")
if st.button("Adicionar dia não letivo"):
    if dentro_do_periodo(novo_dia, inicio, fim) and not ja_existe(novo_dia, st.session_state.dias_nao_letivos):
        st.session_state.dias_nao_letivos.append(novo_dia.strftime("%Y-%m-%d"))
    else:
        st.error("⚠️ Data inválida ou duplicada.")

dias_novos = []
for i, dia in enumerate(st.session_state.dias_nao_letivos):
    st.markdown(
            f"<p style='color:#004aad; font-weight:bold; text-align:center;'>Dia não letivo {i+1}</p>", 
            unsafe_allow_html=True
        )
    data_input = st.date_input(
        label = "Dia não letivo",
        value = datetime.strptime(dia, "%Y-%m-%d").date(), key=f"dia_{i}",
        label_visibility="collapsed"
    )

    col1, col2 = st.columns([0.8, 0.2])
    remover = False
    with col2:
        if st.button("Remover", key=f"remover_dia_{i}"):
            remover = True  

    if not remover:
        if dentro_do_periodo(data_input, inicio, fim) and data_input.strftime("%Y-%m-%d") not in dias_novos:
            dias_novos.append(data_input.strftime("%Y-%m-%d"))
        else:
            st.error("⚠️ Data inválida ou duplicada.")
st.session_state.dias_nao_letivos = dias_novos

# ----------------- Etapas -----------------
with st.container():
    st.markdown("""
        <div style="border:2px solid #004aad; border-radius:8px;background-color:#e6f0ff; padding:10px; margin-top:20px;">
            <h4 style="color:#004aad; font-weight:bold; text-align:center;">Etapas</h4>
        </div>
    """, unsafe_allow_html=True)
#st.subheader("Etapas")
etapas_novas = {}
for idx, (etapa, datas) in enumerate(st.session_state.etapas.items()):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            f"<p style='color:#004aad; font-weight:bold; text-align:center;'>Início {etapa}</p>", 
            unsafe_allow_html=True
        )
        inicio_etapa = st.date_input(
            label = "Início {etapa}",
            value = datetime.strptime(datas[0], "%Y-%m-%d").date(), key=f"inicio_etapa_{idx}",
            label_visibility="collapsed"
        )
        #inicio_etapa = st.date_input(f"Início {etapa}", datetime.strptime(datas[0], "%Y-%m-%d").date(), key=f"inicio_etapa_{idx}")
    with col2:
        st.markdown(
            f"<p style='color:#004aad; font-weight:bold; text-align:center;'>Fim {etapa}</p>", 
            unsafe_allow_html=True
        )
        fim_etapa = st.date_input(
            label = "Fim {etapa}",
            value = datetime.strptime(datas[1], "%Y-%m-%d").date(), key=f"fim_etapa_{idx}",
            label_visibility="collapsed"
        )
        #fim_etapa = st.date_input(f"Fim {etapa}", datetime.strptime(datas[1], "%Y-%m-%d").date(), key=f"fim_etapa_{idx}")
    if dentro_do_periodo(inicio_etapa, inicio, fim) and dentro_do_periodo(fim_etapa, inicio, fim):
        etapas_novas[etapa] = [inicio_etapa.strftime("%Y-%m-%d"), fim_etapa.strftime("%Y-%m-%d")]
    else:
        st.error(f"⚠️ Datas da {etapa} fora do período letivo!")
st.session_state.etapas = etapas_novas

# ----------------- Avaliações de Etapas -----------------
with st.container():
    st.markdown("""
        <div style="border:2px solid #004aad; border-radius:8px;background-color:#e6f0ff; padding:10px; margin-top:20px;">
            <h4 style="color:#004aad; font-weight:bold; text-align:center;">Avaliações de Etapas</h4>
        </div>
    """, unsafe_allow_html=True)
#st.subheader("Avaliações de Etapas")
avaliacoes_etapas_novas = {}
for idx, etapa in enumerate(st.session_state.etapas.keys()):
    if etapa in st.session_state.avaliacoes_etapas:
        datas = st.session_state.avaliacoes_etapas[etapa]
    else:
        datas = [inicio.strftime("%Y-%m-%d"), fim.strftime("%Y-%m-%d")]
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            f"<p style='color:#004aad; font-weight:bold; text-align:center;'>Início avaliação {etapa}</p>", 
            unsafe_allow_html=True
        )
        inicio_av = st.date_input(
            label = "Início avaliação {etapa}",
            value = datetime.strptime(datas[0], "%Y-%m-%d").date(), key=f"inicio_av_{idx}",
            label_visibility="collapsed"
        )
        #inicio_av = st.date_input(f"Início avaliação {etapa}", datetime.strptime(datas[0], "%Y-%m-%d").date(), key=f"inicio_av_{idx}")
    with col2:
        st.markdown(
            f"<p style='color:#004aad; font-weight:bold; text-align:center;'>Fim avaliação {etapa}</p>", 
            unsafe_allow_html=True
        )
        fim_av = st.date_input(
            label = "Fim avaliação {etapa}",
            value = datetime.strptime(datas[1], "%Y-%m-%d").date(), key=f"fim_av_{idx}",
            label_visibility="collapsed"
        )
        #fim_av = st.date_input(f"Fim avaliação {etapa}", datetime.strptime(datas[1], "%Y-%m-%d").date(), key=f"fim_av_{idx}")
    if dentro_do_periodo(inicio_av, inicio, fim) and dentro_do_periodo(fim_av, inicio, fim):
        avaliacoes_etapas_novas[etapa] = [inicio_av.strftime("%Y-%m-%d"), fim_av.strftime("%Y-%m-%d")]
    else:
        st.error(f"⚠️ Avaliação de {etapa} fora do período letivo!")
st.session_state.avaliacoes_etapas = avaliacoes_etapas_novas

# ----------------- Avaliação Multidisciplinar -----------------
with st.container():
    st.markdown("""
        <div style="border:2px solid #004aad; border-radius:8px;background-color:#e6f0ff; padding:10px; margin-top:20px;">
            <h4 style="color:#004aad; font-weight:bold; text-align:center;">Avaliação Multidisciplinar</h4>
        </div>
    """, unsafe_allow_html=True)
#st.subheader("Avaliação Multidisciplinar")
st.markdown(
            f"<p style='color:#004aad; font-weight:bold; text-align:center;'>Data da Avaliação Multidisciplinar</p>", 
            unsafe_allow_html=True
        )
data_multi = st.date_input(
    label = "Data da Avaliação Multidisciplinar",
    value = datetime.strptime(st.session_state.avaliacao_multidisciplinar, "%Y-%m-%d").date()
                           if st.session_state.avaliacao_multidisciplinar else inicio,
                           key="aval_multi",
    label_visibility="collapsed"
)

#data_multi = st.date_input("Data da Avaliação Multidisciplinar",
#                           datetime.strptime(st.session_state.avaliacao_multidisciplinar, "%Y-%m-%d").date()
#                           if st.session_state.avaliacao_multidisciplinar else inicio,
#                           key="aval_multi")
if dentro_do_periodo(data_multi, inicio, fim):
    st.session_state.avaliacao_multidisciplinar = data_multi.strftime("%Y-%m-%d")
else:
    st.error("⚠️ Avaliação multidisciplinar fora do período letivo!")

# ----------------- Rodapés -----------------
with st.container():
    st.markdown("""
        <div style="border:2px solid #004aad; border-radius:8px;background-color:#e6f0ff; padding:10px; margin-top:20px;">
            <h4 style="color:#004aad; font-weight:bold; text-align:center;">Rodapés para Cronograma</h4>
        </div>
    """, unsafe_allow_html=True)

    rodapes_novos = {}
    for etapa, texto in st.session_state.rodapes.items():
        st.markdown(
            f"<p style='color:#004aad; font-weight:bold; text-align:left;'>{etapa.upper()}</p>",
            unsafe_allow_html=True
        )
        rodapes_novos[etapa] = st.text_area(
            label=f"Rodapé {etapa}",
            value=texto,
            key=f"rodape_{etapa}",
            height=150,
            label_visibility="collapsed"
        )

    st.session_state.rodapes = rodapes_novos

# ----------------- Compensações -----------------

DIAS_SEMANA = ["Segunda-feira","Terça-feira","Quarta-feira","Quinta-feira","Sexta-feira","Sábado","Domingo"]

# --- Inicialização / Migração ---
if "compensacoes" not in st.session_state:
    # Carrega do JSON só na primeira execução
    st.session_state.compensacoes = []
    for c in calendario.get("compensacoes", []):
        try:
            st.session_state.compensacoes.append({"id": uuid4().hex, "data": c[0], "dia": int(c[1])})
        except Exception:
            pass

# migra formato antigo (se existir no session_state)
if st.session_state.compensacoes and isinstance(st.session_state.compensacoes[0], list):
    migrated = []
    for item in st.session_state.compensacoes:
        try:
            migrated.append({"id": uuid4().hex, "data": item[0], "dia": int(item[1])})
        except Exception:
            continue
    st.session_state.compensacoes = migrated


with st.container():
    st.markdown("""
        <div style="border:2px solid #004aad; border-radius:8px;background-color:#e6f0ff; padding:10px; margin-top:20px;">
            <h3 style="color:#004aad; font-weight:bold; text-align:center;">Compensações</h3>
        </div>
    """, unsafe_allow_html=True)

    # --- Adicionar ---
    st.markdown("<p style='color:#004aad; font-weight:bold; text-align:center;'>Adicionar nova compensação</p>", unsafe_allow_html=True)

    col_add1, col_add2 = st.columns([0.65, 0.35])
    with col_add1:
        nova_data = st.date_input("Data da compensação", value=date.today(), key="nova_data_comp", label_visibility="collapsed")
    with col_add2:
        novo_dia = st.selectbox("Dia da semana", options=DIAS_SEMANA, index=0, key="novo_dia_sem_comp", label_visibility="collapsed")

    if st.button("Adicionar compensação", key="btn_add_comp"):
        new_item = {"id": uuid4().hex, "data": nova_data.strftime("%Y-%m-%d"), "dia": DIAS_SEMANA.index(novo_dia)}
        if not dentro_do_periodo(nova_data, inicio, fim):
            st.error("⚠️ Data fora do período letivo.")
        elif any(i["data"] == new_item["data"] and i["dia"] == new_item["dia"] for i in st.session_state.compensacoes):
            st.error("⚠️ Compensação duplicada.")
        else:
            st.session_state.compensacoes.append(new_item)
            st.success("Compensação adicionada.")

    st.markdown("---")

    # --- Remover ---
    if st.session_state.compensacoes:
        display_map = {f"{c['data']} — {DIAS_SEMANA[c['dia']]}": c['id'] for c in st.session_state.compensacoes}
        selected_display = st.selectbox("Selecionar compensação para remover", options=list(display_map.keys()), key="select_comp_to_remove")
        if st.button("Remover selecionada", key="btn_remove_selected"):
            sel_id = display_map[selected_display]
            st.session_state.compensacoes = [c for c in st.session_state.compensacoes if c["id"] != sel_id]
            st.success("Compensação removida.")
    else:
        st.info("Nenhuma compensação cadastrada.")

    st.markdown("---")

    # --- Editar ---
    atualizadas = []
    for comp in list(st.session_state.compensacoes):
        uid = comp["id"]
        try:
            data_val = datetime.strptime(comp["data"], "%Y-%m-%d").date()
        except Exception:
            data_val = date.today()

        col1, col2 = st.columns([0.65, 0.35])
        with col1:
            data_input = st.date_input("Data", value=data_val, key=f"data_{uid}", label_visibility="collapsed")
        with col2:
            default_index = comp.get("dia", 0)
            if not (0 <= default_index <= 6):
                default_index = 0
            dia_input = st.selectbox("Dia", options=DIAS_SEMANA, index=default_index, key=f"dia_{uid}", label_visibility="collapsed")

        if dentro_do_periodo(data_input, inicio, fim):
            atualizadas.append({"id": uid, "data": data_input.strftime("%Y-%m-%d"), "dia": DIAS_SEMANA.index(dia_input)})
        else:
            st.error(f"⚠️ {data_input.strftime('%Y-%m-%d')} fora do período letivo.")

    st.session_state.compensacoes = atualizadas

    ## --- Preview ---
    #preview = [[c["data"], c["dia"]] for c in st.session_state.compensacoes]
    #st.markdown("<p style='text-align:center;'><b>Preview JSON</b></p>", unsafe_allow_html=True)
    #st.json({"compensacoes": preview})



# -----------------Botão salvar -----------------
st.subheader(" ")
if st.button("💾 Salvar alterações"):
    calendario["inicio"] = inicio.strftime("%Y-%m-%d")
    calendario["fim"] = fim.strftime("%Y-%m-%d")
    calendario["recessos"] = st.session_state.recessos
    calendario["dias_nao_letivos"] = st.session_state.dias_nao_letivos
    calendario["compensacoes"] = [[c['data'], c['dia']] for c in st.session_state.compensacoes]
    calendario["etapas"] = st.session_state.etapas
    calendario["rodapes"] = st.session_state.rodapes
    avaliacoes = {}
    for etapa, datas in st.session_state.avaliacoes_etapas.items():
        intervalo = gerar_datas_intervalo(datetime.strptime(datas[0], "%Y-%m-%d").date(),
                                          datetime.strptime(datas[1], "%Y-%m-%d").date())
        for d in intervalo:
            avaliacoes[d] = f"AVALIAÇÃO DE {etapa.upper()}"
    if st.session_state.avaliacao_multidisciplinar:
        avaliacoes[st.session_state.avaliacao_multidisciplinar] = "Avaliação Multidisciplinar"

    calendario["avaliacoes"] = avaliacoes

    with open("calendario.json", "w", encoding="utf-8") as f:
        json.dump(calendario, f, ensure_ascii=False, indent=2)

    st.success("✅ Alterações salvas com sucesso!")


st.markdown("---")
st.subheader(" ")

st.subheader("INFORMAÇÕES - DIAS LETIVOS")

# ----------------- Preparar sets para checagem -----------------
feriados = calendario.get("feriados", [])
recessos_set = set()
for r in st.session_state.recessos:
    recessos_set.update(gerar_datas_intervalo(datetime.strptime(r[0], "%Y-%m-%d").date(),
                                               datetime.strptime(r[1], "%Y-%m-%d").date()))
dias_nao_letivos_set = set(st.session_state.dias_nao_letivos)
feriados_set = set(feriados)

todos_os_dias = gerar_datas_intervalo(inicio, fim)
dias_letivos = []
for d_str in todos_os_dias:
    d = datetime.strptime(d_str, "%Y-%m-%d").date()
    if d.weekday() >= 5:
        continue
    if d_str in recessos_set or d_str in dias_nao_letivos_set or d_str in feriados_set:
        continue
    dias_letivos.append(d)

st.info(f" Total de dias letivos do período: {len(dias_letivos)}")
dias_semana_count = Counter(d.weekday() for d in dias_letivos)
st.subheader("Distribuição de dias letivos por dia da semana (Seg a Sex)")
for i, nome_dia in enumerate(["Segunda", "Terça", "Quarta", "Quinta", "Sexta"]):
    st.write(f"{nome_dia}: {dias_semana_count.get(i,0)} dias")

# ----------------- Cores -----------------
CORES = {
    "LETIVO": "#A9DFBF",
    "FE": "#E74C3C",
    "RE": "#5DADE2",
    "DN": "#B2BABB",
    "FIM_SEMANA": "#F2F4F4",
    "VAZIO": "#FFFFFF"
}

raw_feriados = calendario.get("feriados", {})
if isinstance(raw_feriados, dict):
    feriados_set = set(raw_feriados.keys())
    feriados_map = raw_feriados
else:
    feriados_set = set(raw_feriados)
    feriados_map = {d: "" for d in raw_feriados}

recessos_set = set()
for r in st.session_state.recessos:
    recessos_set.update(gerar_datas_intervalo(
        datetime.strptime(r[0], "%Y-%m-%d").date(),
        datetime.strptime(r[1], "%Y-%m-%d").date()
    ))
dias_nao_letivos_set = set(st.session_state.dias_nao_letivos)

# ----------------- Funções calendário -----------------
def months_between(start_date, end_date):
    cur = date(start_date.year, start_date.month, 1)
    last = date(end_date.year, end_date.month, 1)
    meses = []
    while cur <= last:
        meses.append((cur.year, cur.month))
        if cur.month == 12:
            cur = date(cur.year + 1, 1, 1)
        else:
            cur = date(cur.year, cur.month + 1, 1)
    return meses

def gerar_calendario_mes_fig(inicio_periodo, fim_periodo, ano, mes,
                            feriados_set, recessos_set, dias_nao_letivos_set, feriados_map):
    cal = calendar.Calendar(firstweekday=6)
    semanas = cal.monthdatescalendar(ano, mes)

    fig, ax = plt.subplots(figsize=(6,5))
    ax.set_axis_off()
    total_letivos = 0
    dias_semana = ["D", "S", "T", "Q", "Q", "S", "S"]

    for y, semana in enumerate(semanas):
        for x, dia in enumerate(semana):
            dia_iso = dia.isoformat()
            if dia.month != mes or dia < inicio_periodo or dia > fim_periodo:
                tipo = "VAZIO"
            elif dia_iso in recessos_set:
                tipo = "RE"
            elif dia_iso in dias_nao_letivos_set:
                tipo = "DN"
            elif dia_iso in feriados_set:
                tipo = "FE"
            elif dia.weekday() >= 5:
                tipo = "FIM_SEMANA"
            else:
                tipo = "LETIVO"

            cor = CORES[tipo]
            ax.add_patch(plt.Rectangle((x, len(semanas)-y-1), 1, 1,
                                       facecolor=cor, edgecolor="black"))
            if dia.month == mes:
                ax.text(x+0.5, len(semanas)-y-0.5, str(dia.day),
                        ha="center", va="center", fontsize=11, weight="bold")
                if tipo == "LETIVO":
                    total_letivos += 1

    nome_mes = f"{calendar.month_name[mes].upper()} - {total_letivos} DIAS LETIVOS"
    ax.set_title(nome_mes, fontsize=14, weight="bold", pad=14)
    for i, d in enumerate(dias_semana):
        ax.text(i+0.5, len(semanas)+0.3, d, ha="center", va="center",
                fontsize=10, weight="bold", color="white",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="#2E86C1", edgecolor="none"))

    ax.set_xlim(0,7)
    ax.set_ylim(0, len(semanas)+0.8)
    plt.tight_layout()
    return fig

# ----------------- Exibir calendário -----------------
meses = months_between(inicio, fim)
cols_por_linha = 2
st.subheader("Calendário Visual (mês a mês)")

for i in range(0, len(meses), cols_por_linha):
    bloco = meses[i:i+cols_por_linha]
    while len(bloco) < cols_por_linha:
        bloco.append(None)
    cols = st.columns(len(bloco))
    for col, item in zip(cols, bloco):
        if item is None:
            with col:
                st.write("")
        else:
            ano, mes = item
            fig = gerar_calendario_mes_fig(inicio, fim, ano, mes,
                                          feriados_set, recessos_set, dias_nao_letivos_set, feriados_map)
            with col:
                st.pyplot(fig)
            plt.close(fig)

CORES = {
    "DIA LETIVO": "#A9DFBF",
    "FERIADO ": "#E74C3C",
    "RECESSO ": "#5DADE2",
    "DIA NÃO LETIVO": "#B2BABB",
    "FIM_SEMANA": "#F2F4F4",
}

st.markdown("###  Legenda do Calendário")

cols = st.columns(len(CORES))

for idx, (label, color) in enumerate(CORES.items()):
    with cols[idx]:
        st.markdown(
            f"""
            <div style='display: flex; align-items: center;'>
                <div style='width: 20px; height: 20px; background-color:{color}; 
                            border: 1px solid #000; margin-right: 8px;'></div>
                <span>{label}</span>
            </div>
            """,
            unsafe_allow_html=True
        )