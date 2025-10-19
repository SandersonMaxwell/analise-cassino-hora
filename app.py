import streamlit as st
import pandas as pd

st.title("Análise de Jogos - Cassino")

# Upload de 1 CSV por vez
uploaded_file = st.file_uploader("Escolha um arquivo CSV", type="csv")

if uploaded_file:
    # Solicitar nome do jogo
    nome_jogo = st.text_input("Digite o nome do jogo", key="nome_jogo")
    
    if nome_jogo:
        # Lê CSV
        try:
            data = pd.read_csv(uploaded_file, sep=None, engine='python', header=0)
        except Exception as e:
            st.error(f"Erro ao ler o CSV: {e}")
        
        if data.shape[1] != 8:
            st.error(f"O CSV deve ter 8 colunas. Encontradas: {data.shape[1]}")
        else:
            # Renomear colunas para padrão
            data.columns = ["Client_ID", "Nome", "Sobrenome", "Data_Hora", "Quant", "Gastos", "Ganhos", "Resultado"]
            
            # Limpar valores monetários e converter para numérico
            for col in ['Gastos', 'Ganhos', 'Resultado']:
                data[col] = pd.to_numeric(
                    data[col].astype(str)
                        .str.replace('R$', '', regex=False)
                        .str.replace('.', '', regex=False)
                        .str.replace(',', '.', regex=False)
                        .str.strip(),
                    errors='coerce'
                )
            
            # Quantidade de apostas
            data['Quant'] = pd.to_numeric(data['Quant'], errors='coerce').fillna(0)
            
            # Converter Data_Hora
            data['Data_Hora'] = pd.to_datetime(data['Data_Hora'], errors='coerce')
            
            # Adicionar coluna do jogo
            data['Jogo'] = nome_jogo
            
            # --- Resumo por hora ---
            data['Hora'] = data['Data_Hora'].dt.floor('H')  # arredonda para hora
            resumo_hora = data.groupby('Hora').agg({
                'Gastos':'sum',
                'Ganhos':'sum',
                'Resultado':'sum'
            }).reset_index()
            
            # RTP por hora
            resumo_hora['RTP_%'] = resumo_hora['Ganhos'] / resumo_hora['Gastos'] * 100
            
            st.subheader(f"Resumo por Hora - {nome_jogo}")
            
            # Formatar valores como R$
            resumo_hora_display = resumo_hora.copy()
            resumo_hora_display['Gastos'] = resumo_hora_display['Gastos'].apply(lambda x: f"R${x:,.2f}".replace('.', ','))
            resumo_hora_display['Ganhos'] = resumo_hora_display['Ganhos'].apply(lambda x: f"R${x:,.2f}".replace('.', ','))
            resumo_hora_display['Resultado'] = resumo_hora_display['Resultado'].apply(lambda x: f"R${x:,.2f}".replace('.', ','))
            
            st.dataframe(resumo_hora_display)
            
            # --- Análise total mostrando apenas prejuízo ---
            prejuizo = resumo_hora[resumo_hora['Resultado'] < 0].copy()
            
            if not prejuizo.empty:
                st.subheader("Análise Total - Prejuízo")
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
                st.info("Nenhum prejuízo identificado neste jogo.")
