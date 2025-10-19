# Escolher tipo de visualização
opcao_prejuizo = st.radio("Visualizar prejuízo por:", ["Intervalos", "Total do dia"])

prejuizo = resumo_hora[resumo_hora['Resultado_num'] < 0].copy()

if not prejuizo.empty:
    st.subheader("🔥 Jogos e Intervalos com Maior Prejuízo")

    if opcao_prejuizo == "Intervalos":
        # Mostrar por intervalo
        prejuizo = prejuizo.sort_values('Resultado_num')
        for _, row in prejuizo.iterrows():
            st.markdown(f"<span style='font-size:14px'>### {row['Jogo']} - {row['Intervalo']}</span>", unsafe_allow_html=True)
            st.metric(label="Lucro negativo", value=f"R${-row['Resultado_num']:,.2f}".replace('.', ','))

            # Jogadores que contribuíram
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
        # Somar por jogo
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

            # Jogadores que contribuíram
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
