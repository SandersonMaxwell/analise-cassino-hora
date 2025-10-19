import streamlit as st
import pandas as pd

st.title("Análise de Jogos - Cassino")

# Inicializa lista de dados acumulados no session_state
if "todos_dados" not in st.session_state:
    st.session_state.todos_dados = []

# Upload de CSV individual
uploaded_file = st.file_uploader("Escolha um arquivo CSV", type="csv")

if uploaded_file:
    nome_jogo = st.text_input("Digite o nome do jogo", key=f"nome_jogo_{uploaded_file.name}")
    
    if st.button(f"Adicionar CSV: {uploaded_file.name}") and nome_jogo:
        try:
            data = pd.read_csv(uploaded_file, sep=None, engine='python', header=0)
        except Exception as e:
            st.error(f"Erro ao ler CSV: {e}")
        
        if data.shape[1] != 8:
            st.error(f"O CSV deve ter 8 colunas. Encontradas: {data.shape[1]}")
        else:
            # Renomear colunas
            data.columns = ["Client_ID", "Nome", "Sobrenome", "Data_Hora", "Quant", "Gastos", "Ganhos", "Resultado"]
            
            # Limpar valores monetários
            for col in ['Gastos', 'Ganhos', 'Resultado']:
                data[col] = pd.to_numeric(
                    data[col].astype(str)
                        .str.replace('R$', '', regex=False)
                        .str.replace('.', '', regex=False)
                        .str.replace(',', '.', regex=False)
                        .str.strip(),
                    errors='coerce'
                )
            
            data['Quant'] = pd.to_numeric(data['Quant'], errors='coerce').fillna(0)
            data['Data_Hora'] = pd.to_datetime(data['Data_Hora'], errors='coerce')
            data['Jogo'] = nome_jogo
            
            # Adiciona ao session_state
            st.session_state.todos_dados.append(data)
            st.success(f"{uploaded_file.name} adicionado com sucesso!")
            
# Processa análise se houver dados
if st.session_state.todos_dados:
    df = pd.concat(st.session_state.todos_dados, ignore_index=True)
    
    # Criar coluna de intervalo simplificado
    df['Hora'] = df['Data_Hora'].dt.floor('H')
    df['Intervalo'] = df['Hora'].dt.strftime('%H:%M') + " - " + (df['Hora'] + pd.Timedelta(hours=1)).dt.strftime('%H:%M')
    
    # Resumo por jogo e intervalo
    resumo_hora = df.groupby(['Jogo', 'Intervalo']).agg({
        'Quant':'sum',
        'Gastos':'sum',
        'Ganhos':'sum',
        'Resultado':'sum'
    }).reset_index()
    
    resumo_hora['RTP_%'] = resumo_hora['Ganhos'] / resumo_hora['Gastos'] * 100
    
    st.subheader("Resumo por Hora e Jogo")
    resumo_hora_display = resumo_hora.copy()
    for col in ['Gastos', 'Ganhos', 'Resultado']:
        resumo_hora_display[col] = resumo_hora_display[col].apply(lambda x: f"R${x:,.2f}".replace('.', ','))
    st.dataframe(resumo_hora_display)
    
    # Análise total – apenas prejuízo
    prejuizo = resumo_hora[resumo_hora['Resultado'] < 0].copy()
    if not prejuizo.empty:
        st.subheader("Análise Total - Prejuízo por Jogo e Intervalo")
        prejuizo_display = prejuizo.copy()
        prejuizo_display['Gastos'] = prejuizo_display['Gastos'].apply(lambda x: f"R${x:,.2f}".replace('.', ','))
        prejuizo_display['Ganhos'] = prejuizo_display['Ganhos'].apply(lambda x: f"R${x:,.2f}".replace('.', ','))
        prejuizo_display['Resultado'] = prejuizo_display['Resultado'].apply(lambda x: f"R${x:,.2f}".replace('.', ','))
        prejuizo_display = prejuizo_display.rename(columns={
            'Gastos': 'Total Apostado',
            'Ganhos': 'Payout',
            'Resultado': 'Lucro'
        })
        st.dataframe(prejuizo_display)
    else:
        st.info("Nenhum prejuízo identificado.")
