import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("📊 Relatório de Jogos - Cassino")

# Inicializa lista de arquivos enviados
if "arquivos_enviados" not in st.session_state:
    st.session_state.arquivos_enviados = []

# Upload de CSV individual
uploaded_file = st.file_uploader("Escolha um arquivo CSV", type="csv")

if uploaded_file:
    nome_jogo = st.text_input("Digite o nome do jogo", key=f"nome_jogo_{uploaded_file.name}")
    
    if st.button(f"Adicionar CSV: {uploaded_file.name}") and nome_jogo:
        st.session_state.arquivos_enviados.append((uploaded_file, nome_jogo))
        st.success(f"{uploaded_file.name} adicionado!")

# Mostra arquivos adicionados
if st.session_state.arquivos_enviados:
    st.subheader("Arquivos enviados:")
    for f, jogo in st.session_state.arquivos_enviados:
        st.write(f"- {f.name} -> {jogo}")

    if st.button("Gerar Relatório Final"):
        todos_dados = []
        
        # Processar cada CSV
        for arquivo, jogo in st.session_state.arquivos_enviados:
            try:
                data = pd.read_csv(arquivo, sep=None, engine='python', header=0)
            except Exception as e:
                st.error(f"Erro ao ler {arquivo.name}: {e}")
                continue
            
            if data.shape[1] != 8:
                st.error(f"O CSV {arquivo.name} deve ter 8 colunas. Encontradas: {data.shape[1]}")
                continue
            
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
            data['Jogo'] = jogo
            
            todos_dados.append(data)
        
        if todos_dados:
            df = pd.concat(todos_dados, ignore_index=True)
            
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
            
            # RTP em porcentagem
            resumo_hora['RTP_%'] = (resumo_hora['Ganhos'] / resumo_hora['Gastos'] * 100).round(2)
            resumo_hora['RTP_%'] = resumo_hora['RTP_%'].astype(str) + "%"
            
            # Formatar valores monetários
            for col in ['Gastos', 'Ganhos', 'Resultado']:
                resumo_hora[col] = resumo_hora[col].apply(lambda x: f"R${x:,.2f}".replace('.', ','))
            
            # Função para colorir resultado
            def color_result(val):
                if 'R$' in val:
                    num = float(val.replace('R$', '').replace('.', '').replace(',', '.'))
                    return 'color: green' if num > 0 else 'color: red' if num < 0 else ''
                return ''
            
            st.subheader("📅 Resumo por Hora e Jogo")
            st.dataframe(resumo_hora.style.applymap(color_result, subset=['Resultado']), use_container_width=True)
            
            # Destacar jogos e horários com maior prejuízo
            resumo_hora['Resultado_num'] = df.groupby(['Jogo', 'Intervalo'])['Resultado'].sum().values
            prejuizo = resumo_hora[resumo_hora['Resultado_num'] < 0].copy()
            
            if not prejuizo.empty:
                st.subheader("🔥 Jogos e Intervalos com Maior Prejuízo")
                
                # Ordenar por maior prejuízo
                prejuizo = prejuizo.sort_values('Resultado_num')
                
                for _, row in prejuizo.iterrows():
                    st.markdown(f"### {row['Jogo']} - {row['Intervalo']}")
                    st.metric(label="Lucro negativo", value=f"R${-row['Resultado_num']:,.2f}".replace('.', ','))
                    
                    # Mostrar jogadores que contribuíram
                    interval_data = df[(df['Jogo']==row['Jogo']) & (df['Intervalo']==row['Intervalo'])]
                    jogadores_prejuizo = interval_data[interval_data['Resultado']<0][['Client_ID','Nome','Sobrenome','Resultado']]
                    jogadores_prejuizo['Resultado'] = jogadores_prejuizo['Resultado'].apply(lambda x: f"R${x:,.2f}".replace('.', ','))
                    
                    with st.expander("Ver jogadores que contribuíram para o prejuízo"):
                        st.dataframe(jogadores_prejuizo)
            else:
                st.info("Nenhum prejuízo identificado.")
