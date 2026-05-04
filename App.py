import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- CONFIGURAÇÕES DO PERFIL ---
st.set_page_config(page_title="BioStats Pro", layout="wide", page_icon="⚖️")

# Inicialização de dados persistentes
if 'banco_alimentos' not in st.session_state:
    st.session_state.banco_alimentos = {"Arroz (100g)": 130, "Feijão (100g)": 90, "Frango (100g)": 165, "Ovo (un)": 78}
if 'log_atividades' not in st.session_state:
    st.session_state.log_atividades = pd.DataFrame(columns=['Data', 'Tipo', 'Categoria', 'Descricao', 'Valor'])
if 'peso_usuario' not in st.session_state:
    st.session_state.peso_usuario = 107.5
if 'meta_agua' not in st.session_state:
    st.session_state.meta_agua = 3.7

# --- FUNÇÕES AUXILIARES ---
def adicionar_registro(tipo, categoria, desc, valor):
    novo = pd.DataFrame({'Data': [datetime.now()], 'Tipo': [tipo], 'Categoria': [categoria], 'Descricao': [desc], 'Valor': [valor]})
    st.session_state.log_atividades = pd.concat([st.session_state.log_atividades, novo], ignore_index=True)

# --- BARRA LATERAL (Configurações e Peso) ---
with st.sidebar:
    st.header("⚙️ Configurações")
    st.session_state.peso_usuario = st.number_input("Peso Atual (kg)", value=st.session_state.peso_usuario, step=0.1)
    st.session_state.meta_agua = st.number_input("Meta de Água (L)", value=st.session_state.meta_agua, step=0.1)
    
    st.divider()
    st.subheader("📊 Resumo Rápido")
    hoje = datetime.now().date()
    df_hoje = st.session_state.log_atividades[st.session_state.log_atividades['Data'].dt.date == hoje]
    cal_in = df_hoje[df_hoje['Tipo'] == 'Alimento']['Valor'].sum()
    cal_out = df_hoje[df_hoje['Tipo'] == 'Exercício']['Valor'].sum()
    st.metric("Consumo Hoje", f"{int(cal_in)} kcal")
    st.metric("Queima Hoje", f"{int(cal_out)} kcal")

# --- INTERFACE PRINCIPAL ---
st.title("🍎 BioStats: Gestão de Saúde")

abas = st.tabs(["🍽️ Refeições", "🏃 Exercícios", "📈 Relatórios", "📋 Histórico/Editar", "⚙️ Banco de Dados"])

# --- ABA 1: ALIMENTAÇÃO ---
with abas[0]:
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Lançar Alimento")
        refeicao = st.selectbox("Momento", ["Café da Manhã", "Almoço", "Café da Tarde", "Janta", "Snacks"])
        
        # Filtro de busca
        busca = st.text_input("Filtrar alimento do banco:")
        opcoes = [a for a in st.session_state.banco_alimentos.keys() if busca.lower() in a.lower()]
        alimento_sel = st.selectbox("Selecione:", opcoes)
        
        qtd = st.number_input("Quantidade (Fator multiplicador, ex: 1.5 para 150g)", value=1.0, step=0.1)
        if st.button("Adicionar Alimento"):
            total_cal = st.session_state.banco_alimentos[alimento_sel] * qtd
            adicionar_registro('Alimento', refeicao, alimento_sel, total_cal)
            st.success(f"{alimento_sel} adicionado ao {refeicao}!")

    with col2:
        st.subheader("💧 Hidratação")
        agua_copo = st.number_input("Adicionar Água (L)", value=0.25, step=0.05)
        if st.button("Registrar Água"):
            adicionar_registro('Água', 'Hidratação', 'Copo de Água', agua_copo)

# --- ABA 2: EXERCÍCIOS ---
with abas[1]:
    col_ex1, col_ex2 = st.columns(2)
    with col_ex1:
        st.subheader("Exercícios Listados")
        tipo_ex = st.selectbox("Atividade", ["Musculação", "Caminhada", "Corrida", "Natação"])
        minutos = st.number_input("Tempo (minutos)", value=30, step=5)
        # Cálculo MET simples por peso
        mets = {"Musculação": 5, "Caminhada": 4, "Corrida": 8, "Natação": 7}
        gasto = (mets[tipo_ex] * st.session_state.peso_usuario * (minutos/60))
        if st.button("Lançar Exercício"):
            adicionar_registro('Exercício', 'Treino', tipo_ex, gasto)
            st.success("Treino registrado!")
            
    with col_ex2:
        st.subheader("Gasto Extra (Não listado)")
        desc_extra = st.text_input("Descrição (ex: Faxina)")
        cal_extra = st.number_input("Calorias estimadas", value=100)
        if st.button("Lançar Extra"):
            adicionar_registro('Exercício', 'Extra', desc_extra, cal_extra)

# --- ABA 3: RELATÓRIOS (Dia, Semana, Mês) ---
with abas[2]:
    st.subheader("Painel de Gastos e Consumo")
    periodo = st.radio("Ver período:", ["Hoje", "Últimos 7 Dias", "Últimos 30 Dias"], horizontal=True)
    
    agora = datetime.now()
    if periodo == "Hoje": dias = 0
    elif periodo == "Últimos 7 Dias": dias = 7
    else: dias = 30
    
    df_periodo = st.session_state.log_atividades[st.session_state.log_atividades['Data'] > (agora - timedelta(days=dias))]
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Ingerido", f"{int(df_periodo[df_periodo['Tipo'] == 'Alimento']['Valor'].sum())} kcal")
    c2.metric("Total Queimado", f"{int(df_periodo[df_periodo['Tipo'] == 'Exercício']['Valor'].sum())} kcal")
    c3.metric("Água Total", f"{df_periodo[df_periodo['Tipo'] == 'Água']['Valor'].sum():.1f} L")
    
    # Gráfico simples
    if not df_periodo.empty:
        st.bar_chart(df_periodo.groupby('Tipo')['Valor'].sum())

# --- ABA 4: HISTÓRICO E EXCLUSÃO ---
with abas[3]:
    st.subheader("Gerenciar Lançamentos de Hoje")
    df_edit = st.session_state.log_atividades[st.session_state.log_atividades['Data'].dt.date == hoje].copy()
    
    if df_edit.empty:
        st.info("Nenhum lançamento hoje.")
    else:
        for i, row in df_edit.iterrows():
            col_d1, col_d2, col_d3 = st.columns([3, 1, 1])
            col_d1.write(f"**[{row['Tipo']}]** {row['Categoria']} - {row['Descricao']}: {row['Valor']:.1f}")
            if col_d3.button("Excluir", key=f"del_{i}"):
                st.session_state.log_atividades = st.session_state.log_atividades.drop(i)
                st.rerun()

# --- ABA 5: BANCO DE DADOS (Configurar Alimentos) ---
with abas[4]:
    st.subheader("Configurar Calorias dos Alimentos")
    novo_nome = st.text_input("Nome do Alimento")
    nova_cal = st.number_input("Calorias por porção padrão (ex: 100g ou 1un)", value=100)
    if st.button("Salvar no Banco"):
        st.session_state.banco_alimentos[novo_nome] = nova_cal
        st.success("Alimento salvo!")
    
    st.divider()
    st.write("Alimentos atuais:", st.session_state.banco_alimentos)
