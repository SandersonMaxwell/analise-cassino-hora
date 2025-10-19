import streamlit as st
import pandas as pd

st.title("Análise de Jogadores - CSV")

uploaded_files = st.file_uploader("Escolha um ou mais arquivos CSV", type="csv", accept_multiple_files=True)

if uploaded_files:
    dfs = [pd.read_csv(file) for file in uploaded_files]
    data = pd.concat(dfs, ignore_index=True)
    
    # Limpar nomes de colunas
    data.columns = [col.strip().replace(' ', '_').replace('\ufeff','') for col in data.columns]
    
    # Identificar a coluna de data
    possible_date_cols = ['Data_Hora', 'DataHora', 'data_hora', 'datahora']
    date_col = None
    for col in possible_date_cols:
        if col in data.columns:
            date_col = col
            break

    if date_col is None:
        st.error("Não foi possível encontrar a coluna de data no CSV. Verifique os nomes das colunas.")
    else:
        # Convertendo para datetime
        data['Data_Hora'] = pd.to_datetime(data[date_col])
        
        # Resumo por jogador
        resumo_jogadores = data.groupby(['Client_ID', 'Nome', 'Sobrenome']).agg({
            'Gastos':'sum',
            'Ganhos':'sum',
            'Resultado':'sum'
        }).reset_index()
        resumo_jogadores['RTP_%'] = resumo_jogadores['Ganhos'] / resumo_jogadores['Gastos'] * 100
        st.subheader("Resumo por Jogador")
        st.dataframe(resumo_jogadores)
        
        # Análise por hora
        data['Hora'] = data['Data_Hora'].dt.floor('H')
        resumo_hora = data.groupby('Hora').agg({
            'Gastos':'sum',
            'Ganhos':'sum',
            'Resultado':'sum'
        }).reset_index()
        resumo_hora['RTP_%'] = resumo_hora['Ganhos'] / resumo_hora['Gastos'] * 100
        st.subheader("Análise por Hora")
        st.dataframe(resumo_hora)
        
        # Análise total
        total_gastos = data['Gastos'].sum()
        total_ganhos = data['Ganhos'].sum()
        total_resultado = data['Resultado'].sum()
        total_rtp = total_ganhos / total_gastos * 100
        st.subheader("Análise Total")
        st.markdown(f"- **Total Gastos:** {total_gastos}")
        st.markdown(f"- **Total Ganhos:** {total_ganhos}")
        st.markdown(f"- **Total Resultado:** {total_resultado}")
        st.markdown(f"- **RTP Total (%):** {total_rtp:.2f}")
