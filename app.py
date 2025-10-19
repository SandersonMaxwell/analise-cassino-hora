import streamlit as st
import pandas as pd
import csv

st.set_page_config(layout="wide")
st.title("📊 Relatório de Jogos - Cassino")

# --- Sessão para arquivos e dados ---
if "arquivos_enviados" not in st.session_state:
    st.session_state.arquivos_enviados = []
if "df_processado" not in st.session_state:
    st.session_state.df_processado = None
if "resumo_hora" not in st.session_state:
    st.session_state.resumo_hora = None

# --- Upload de CSV individual ---
uploaded_file = st.file_uploader("Escolha um arquivo CSV", type="csv")

if uploaded_file:
    nome_jogo = st.text_input("Digite o nome do jogo", key=f"nome_jogo_{uploaded_file.name}")
    if st.button(f"Adicionar CSV: {uploaded_file.name}") and nome_jogo:
        st.session_state.arquivos_enviados.append((uploaded_file, nome_jogo))
        st.success(f"{uploaded_file.name} adicionado!")

# --- Listar arquivos enviados com opção de remover ---
if st.session_state.arquivos_enviados:
    st.subheader("Arquivos enviados:")
    remove_idx = None
    for i, (f, jogo) in enumerate(st.session_state.arquivos_enviados):
        col1, col2 = st.columns([0.9, 0.1])
        with col1:
            st.write(f"- {f.name} -> {jogo}")
        with col2:
            if st.button("❌", key=f"remover_{i}"):
                remove_idx = i
    if remove_idx is not None:
        st.session_state.arquivos_enviados.pop(remove_idx)
        st.success("Arquivo removido")
        st.experimental_rerun()

# --- Botão para gerar relatório ---
if st.button("Gerar Relatório Final") or st.session_state.df_processado is not None:
    if st.session_state.df_processado is None:
        todos_dados = []
        for arquivo, jogo in st.session_state.arquivos_enviados:
            try:
                arquivo.seek(0)
                sample = arquivo.read(1024).decode('utf-8')
                arquivo.seek(0)
                dialect = csv.Sniffer().sniff(sample, delimiters=";,")
                sep = dialect.delimiter
                data = pd.read_csv(arquivo, sep=sep, engine='python', header=0)
            except Exception as e:
                st.error(f"Erro ao ler {arquivo.name}: {e}")
                continue

            if data.shape[1] != 8:
                st.error(f"O CSV {arquivo.name} deve ter 8 colunas. Encontradas: {data.shape[1]}")
                continue

            # Padroniza colunas
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
            df['Hora'] = df['Data_Hora'].dt.floor('H')
            df['Intervalo'] = df['Hora'].dt.strftime('%H:%M') + " - " + (df['Hora'] + pd.Timedelta(hours=1)).dt.strftime('%H:%M')
            resumo_hora = df.groupby(['Jogo', 'Intervalo']).agg({
                'Quant':'sum',
                'Gastos':'sum',
                'Ganhos':'sum',
                'Resultado':'sum'
            }).reset_index()
            resumo_hora['RTP_%'] = (resumo_hora['Ganhos'] / resumo_hora['Gastos'] * 100).round(2)
            resumo_hora['RTP_%'] = resumo_hora['RTP_%'].astype(str) + '%'
            resumo_hora['Resultado_num'] = resumo_hora['Resultado'].copy()

            # Salva em session_state
            st.session_state.df_processado = df
            st.session_state.resumo_hora = resumo_hora
    else:
        df = st.session_state.df_processado
        resumo_hora = st.session_state.resumo_hora

    # --- Mostrar resumo por hora ---
    resumo_hora_display = resumo_hora.copy()
    for col in ['Gastos', 'Ganhos', 'Resultado']:
        resumo_hora_display[col] = resumo_hora_display[col].apply(lambda x: f"R${x:,.2f}".replace('.', ','))

    def color_result(val, val_num):
        if val_num > 0:
            return 'color: green'
        elif val_num < 0:
            return 'color: red'
        else:
            return ''

    st.subheader("📅 Resumo por Hora e Jogo")
    st.dataframe(
        resumo_hora_display.style.set_table_styles(
            [{'selector': 'td', 'props': [('font-size', '12px')]},
             {'selector': 'th', 'props': [('font-size', '12px')]}]
        ).apply(
            lambda x: [color_result(v, resumo_hora['Resultado_num'].iloc[i]) for i, v in enumerate(x)],
            subset=['Resultado']
        ),
        use_container_width=True
    )

    # --- Visualizar maior prejuízo ---
    prejuizo = resumo_hora[resumo_hora['Resultado_num'] < 0].copy()
    if not prejuizo.empty:
        opcao_prejuizo = st.radio("Visualizar prejuízo por:", ["Intervalos", "Total do dia"], index=0)

        st.subheader("🔥 Jogos e Intervalos com Maior Prejuízo")

        if opcao_prejuizo == "Intervalos":
            prejuizo = prejuizo.sort_values('Resultado_num')
            for _, row in prejuizo.iterrows():
                st.markdown(f"<span style='font-size:14px'>### {row['Jogo']} - {row['Intervalo']}</span>", unsafe_allow_html=True)
                st.metric(label="Lucro negativo", value=f"R${-row['Resultado_num']:,.2f}".replace('.', ','))

                interval_data = df[(df['Jogo']==row['Jogo']) & (df['Intervalo']==row['Intervalo'])]
                jogadores_prejuizo = interval_data[interval_data['Resultado']<0].groupby(
                    ['Client_ID','Nome','Sobrenome']
                ).agg({
                    'Quant':'sum',
                    'Gastos':'sum',
                    'Ganhos':'sum',
                    'Resultado':'sum'
                }).reset_index()

                for col in ['Gastos','Ganhos','Resultado']:
                    jogadores_prejuizo[col] = jogadores_prejuizo[col].apply(lambda x: f"R${x:,.2f}".replace('.', ','))

                jogadores_prejuizo.rename(columns={'Quant':'Rodadas'}, inplace=True)

                with st.expander("Ver jogadores que contribuíram para o prejuízo"):
                    st.dataframe(jogadores_prejuizo.style.set_table_styles(
                        [{'selector': 'td', 'props': [('font-size', '12px')]},
                         {'selector': 'th', 'props': [('font-size', '12px')]}]
                    ))
        elif opcao_prejuizo == "Total do dia":
            prejuizo_total = df.groupby('Jogo').agg({
                'Quant':'sum',
                'Gastos':'sum',
                'Ganhos':'sum',
                'Resultado':'sum'
            }).reset_index()
            prejuizo_total = prejuizo_total[prejuizo_total['Resultado']<0].sort_values('Resultado')

            for _, row in prejuizo_total.iterrows():
                st.markdown(f"<span style='font-size:14px'>### {row['Jogo']}</span>", unsafe_allow_html=True)
                st.metric(label="Lucro negativo total do dia", value=f"R${-row['Resultado']:,.2f}".replace('.', ','))

                jogadores_prejuizo = df[(df['Jogo']==row['Jogo']) & (df['Resultado']<0)].groupby(
                    ['Client_ID','Nome','Sobrenome']
                ).agg({
                    'Quant':'sum',
                    'Gastos':'sum',
                    'Ganhos':'sum',
                    'Resultado':'sum'
                }).reset_index()

                for col in ['Gastos','Ganhos','Resultado']:
                    jogadores_prejuizo[col] = jogadores_prejuizo[col].apply(lambda x: f"R${x:,.2f}".replace('.', ','))

                jogadores_prejuizo.rename(columns={'Quant':'Rodadas'}, inplace=True)

                with st.expander("Ver jogadores que contribuíram para o prejuízo"):
                    st.dataframe(jogadores_prejuizo.style.set_table_styles(
                        [{'selector': 'td', 'props': [('font-size', '12px')]},
                         {'selector': 'th', 'props': [('font-size', '12px')]}]
                    ))
    else:
        st.info("Nenhum prejuízo identificado.")
