import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- CONFIGURAÇÕES DO PERFIL ---
st.set_page_config(page_title="BioStats Pro", layout="wide", page_icon="⚖️")

# --- INICIALIZAÇÃO DE DADOS (Correção de Erros de Estado) ---
if 'banco_alimentos' not in st.session_state:
    st.session_state.banco_alimentos = {"Arroz (100g)": 130.0, "Feijão (100g)": 90.0, "Frango (100g)": 165.0, "Ovo (un)": 78.0}

if 'log_atividades' not in st.session_state:
    # Criando o DataFrame com tipos de dados definidos para evitar erros de concatenação
    st.session_state.log_atividades = pd.DataFrame({
        'Data': pd.to_datetime([]),
        'Tipo': pd.Series([], dtype='str'),
        'Categoria': pd.Series([], dtype='str'),
        'Descricao': pd.Series([], dtype='str'),
        'Valor': pd.Series([], dtype='float')
    })

if 'peso_usuario' not in st.session_state:
    st.session_state.peso_usuario = 107.5

if 'meta_agua' not in st.session_state:
    st.session_state.meta_agua = 3.7

# --- FUNÇÕES AUXILIARES ---
def adicionar_registro(tipo, categoria, desc, valor):
    novo_registro = pd.DataFrame([{
        'Data': datetime.now(),
        'Tipo': tipo,
        'Categoria': categoria,
        'Descricao': desc,
        'Valor': float(valor)
    }])
    st.session_state.log_atividades = pd.concat([st.session_state.log_atividades, novo_registro], ignore_index=True)

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("⚙️ Configurações")
    st.session_state.peso_usuario = st.number_input("Peso Atual (kg)", value=float(st.session_state.peso_usuario), step=0.1)
    st.session_state.meta_agua = st.number_input("Meta de Água (L)", value=float(st.session_state.meta_agua), step=0.1)
    
    st.divider()
    st.subheader("📊 Resumo de Hoje")
    
    df = st.session_state.log_atividades
    if not df.empty:
        # Filtro corrigido para comparação de datas
        hoje = datetime.now().date()
        df_hoje = df[df['Data'].dt.date == hoje]
        
        cal_in = df_hoje[df_hoje['Tipo'] == 'Alimento']['Valor'].sum()
        cal_out = df_hoje[df_hoje['Tipo'] == 'Exercício']['Valor'].sum()
        agua_total = df_hoje[df_hoje['Tipo'] == 'Água']['Valor'].sum()
        
        st.metric("Consumo", f"{int(cal_in)} kcal")
        st.metric("Queima", f"{int(cal_out)} kcal")
        st.metric("Água", f"{agua_total:.1f} L")
    else:
        st.write("Sem registros hoje.")

# --- INTERFACE PRINCIPAL ---
st.title("🍎 BioStats: Gestão de Saúde")

abas = st.tabs(["🍽️ Refeições", "🏃 Exercícios", "📈 Relatórios", "📋 Histórico", "⚙️ Banco"])

# --- ABA 1: ALIMENTAÇÃO ---
with abas[0]:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Lançar Alimento")
        momento = st.selectbox("Momento", ["Café da Manhã", "Almoço", "Café da Tarde", "Janta", "Snacks"])
        busca = st.text_input("Filtrar alimento:")
        
        opcoes = [a for a in st.session_state.banco_alimentos.keys() if busca.lower() in a.lower()]
        if opcoes:
            alimento_sel = st.selectbox("Selecione:", opcoes)
            qtd = st.number_input("Quantidade (Fator, ex: 1.0 = 100g/1un)", value=1.0, step=0.1)
            
            if st.button("Adicionar Alimento"):
                total_cal = st.session_state.banco_alimentos[alimento_sel] * qtd
                adicionar_registro('Alimento', momento, alimento_sel, total_cal)
                st.success("Adicionado!")
        else:
            st.warning("Alimento não encontrado. Cadastre na aba 'Banco'.")

    with col2:
        st.subheader("💧 Hidratação")
        vol = st.number_input("Litros (L)", value=0.25, step=0.05)
        if st.button("Registrar Água"):
            adicionar_registro('Água', 'Hidratação', 'Água', vol)
            st.rerun()

# --- ABA 2: EXERCÍCIOS ---
with abas[1]:
    col_ex1, col_ex2 = st.columns(2)
    with col_ex1:
        st.subheader("Atividades")
        tipo_ex = st.selectbox("Tipo", ["Musculação", "Caminhada", "Corrida", "Natação"])
        minutos = st.number_input("Minutos", value=30, step=5)
        mets = {"Musculação": 5.0, "Caminhada": 4.0, "Corrida": 8.0, "Natação": 7.0}
        
        if st.button("Lançar Treino"):
            gasto = (mets[tipo_ex] * st.session_state.peso_usuario * (minutos/60))
            adicionar_registro('Exercício', 'Treino', tipo_ex, gasto)
            st.rerun()

    with col_ex2:
        st.subheader("Gasto Extra")
        desc_extra = st.text_input("Descrição (Ex: Faxina)")
        cal_extra = st.number_input("Kcal estimadas", value=100)
        if st.button("Lançar Extra"):
            adicionar_registro('Exercício', 'Extra', desc_extra, cal_extra)
            st.rerun()

# --- ABA 3: RELATÓRIOS ---
with abas[2]:
    periodo = st.radio("Período:", ["Hoje", "7 Dias", "30 Dias"], horizontal=True)
    dias = 0 if periodo == "Hoje" else (7 if periodo == "7 Dias" else 30)
    
    data_limite = datetime.now() - timedelta(days=dias)
    df_f = st.session_state.log_atividades
    
    if not df_f.empty:
        mask = df_f['Data'] >= pd.to_datetime(data_limite).normalize()
        df_periodo = df_f.loc[mask]
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Ingerido", f"{int(df_periodo[df_periodo['Tipo'] == 'Alimento']['Valor'].sum())} kcal")
        c2.metric("Queimado", f"{int(df_periodo[df_periodo['Tipo'] == 'Exercício']['Valor'].sum())} kcal")
        c3.metric("Água", f"{df_periodo[df_periodo['Tipo'] == 'Água']['Valor'].sum():.1f} L")
        
        if not df_periodo.empty:
            chart_data = df_periodo.groupby('Tipo')['Valor'].sum()
            st.bar_chart(chart_data)
    else:
        st.info("Sem dados para exibir.")

# --- ABA 4: HISTÓRICO / EDITAR ---
with abas[3]:
    st.subheader("Lançamentos de Hoje")
    df_h = st.session_state.log_atividades
    if not df_h.empty:
        hoje_dt = datetime.now().date()
        indices_hoje = df_h[df_h['Data'].dt.date == hoje_dt].index
        
        for i in indices_hoje:
            row = df_h.loc[i]
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.write(f"**
            
