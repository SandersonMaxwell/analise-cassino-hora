import streamlit as st
import pandas as pd

st.title("Análise de Jogadores e Jogos - Cassino")

jogos_data = []  # Lista para armazenar dados de cada jogo

uploaded_files = st.file_uploader("Escolha os arquivos CSV", type="csv", accept_multiple_files=True)

if uploaded_files:
    for idx, file in enumerate(uploaded_files):
        st.subheader(f"Arquivo {idx+1}: {file.name}")
        
        # Solicita o nome do jogo
        nome_jogo = st.text_input(f"Digite o nome do jogo para {file.name}", key=f"jogo_{idx}")
        
        if nome_jogo:
            # Lê CSV
            data = pd.read_csv(file, sep=None, engine='python', header=0)
            
            # Renomear colunas para padrão
            data.columns = ["Client_ID", "Nome", "Sobrenome", "Data_Hora", "Quant", "Gastos", "Ganhos", "Resultado"]
            
            # Limpar valores monetários e converter para numérico
            for col in ['Gastos', 'Ganhos', 'Resultado']:
                data[col] = pd.to_numeric(
                    data[col].astype(str)
                        .str.replace('R$', '', regex=False)
                        .str.replace('.', '', regex=False)  # remove separador de milhar
                        .str.replace(',', '.', regex=False)
                        .str.strip(),
                    errors='coerce'
                )
            
            # Garantir Quant como numérico
            data['Quant'] = pd.to_numeric(data['Quant'], errors='coerce').fillna(0)
            
            # Adiciona coluna com nome do jogo
            data['Jogo'] = nome_jogo
            
            jogos_data.append(data)
    
    # Concatena todos os CSVs
    todos_dados = pd.concat(jogos_data, ignore_index=True)
    
    # --- Resumo por jogador ---
    resumo_jogadores = todos_dados.groupby(['Client_ID', 'Nome', 'Sobrenome']).agg({
        'Quant':'sum',
        'Gastos':'sum',
        'Ganhos':'sum',
        'Resultado':'sum'
    }).reset_index()
    resumo_jogadores['RTP_%'] = resumo_jogadores['Ganhos'] / resumo_jogadores['Gastos'] * 100
    
    # Destaque prejuízo para a casa (Resultado < 0)
    prejuizo_jogadores = resumo_jogadores[resumo_jogadores['Resultado'] < 0]
    
    st.subheader("Resumo por Jogador")
    st.dataframe(resumo_jogadores)
    
    if not prejuizo_jogadores.empty:
        st.subheader("Jogadores que deram prejuízo para a casa")
        st.dataframe(prejuizo_jogadores)
    
    # --- Resumo por jogo ---
    resumo_jogos = todos_dados.groupby('Jogo').agg({
        'Quant':'sum',
        'Gastos':'sum',
        'Ganhos':'sum',
        'Resultado':'sum'
    }).reset_index()
    resumo_jogos['RTP_%'] = resumo_jogos['Ganhos'] / resumo_jogos['Gastos'] * 100
    
    # Jogos que deram prejuízo para a casa
    prejuizo_jogos = resumo_jogos[resumo_jogos['Resultado'] < 0]
    
    st.subheader("Resumo por Jogo")
    st.dataframe(resumo_jogos)
    
    if not prejuizo_jogos.empty:
        st.subheader("Jogos que deram prejuízo para a casa")
        st.dataframe(prejuizo_jogos)
    
    # --- Análise total ---
    total_quant = todos_dados['Quant'].sum()
    total_gastos = todos_dados['Gastos'].sum()
    total_ganhos = todos_dados['Ganhos'].sum()
    total_resultado = todos_dados['Resultado'].sum()
    total_rtp = total_ganhos / total_gastos * 100
    
    st.subheader("Análise Total")
    st.markdown(f"- **Total de Apostas:** {total_quant}")
    st.markdown(f"- **Total Gastos:** {total_gastos}")
    st.markdown(f"- **Total Ganhos:** {total_ganhos}")
    st.markdown(f"- **Total Resultado:** {total_resultado}")
    st.markdown(f"- **RTP Total (%):** {total_rtp:.2f}")
