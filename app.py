import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime, date

api_url = 'http://b3f9eddc972c.mylabserver.com:8081/'
pd.options.display.float_format = '{:,.2f}'.format

def get_portfolio_list():
    try:
        response = requests.get(api_url + 'portfoliomanagement/portfolios')
        portfolios = json.loads(response.text)['portfolios']
        return ['Select a Portfolio'] + portfolios
    except Exception as e:
        print('Failed to fetch list of portfolios: ' + str(e))
        return ['Select a Portfolio']


def str_to_date(text):
    # '4/2/2019' -> 2019-04-02
    items =  [int(i) for i in text.split('/')]
    return date(items[2], items[0], items[1])

def get_portfolio_data(portfolio_name):
    response = requests.get(api_url + 'portfoliomanagement/portfolios/{0}'.format(portfolio_name))
    portfolio_detail = json.loads(response.text)
    portfolio_stocks = pd.DataFrame(portfolio_detail['portfolio_stocks']).rename(columns={'Climate': 'Impact'})
    portfolio_summary = pd.DataFrame(portfolio_detail['portfolio_summary'])
    benchmark_summary = pd.DataFrame(portfolio_detail['benchmark_summary'])

    portfolio_stocks.set_index('Ticker', inplace=True)

    plot_inv_value_data = pd.DataFrame(portfolio_detail['plot_data']).rename(columns={'CreatedDate': 'Date'})
    plot_esg_score_data = pd.DataFrame(portfolio_detail['plot_data_esg']).rename(columns={'CreatedDate': 'Date'})

    plot_portfolio_returns_data = pd.DataFrame(portfolio_detail['returns_data']).rename(columns={'CreatedDate': 'Date'})
    plot_benchmark_returns_data = pd.DataFrame(portfolio_detail['benchmark']).rename(columns={'CreatedDate': 'Date'})

    plot_inv_value_data['Date'] = plot_inv_value_data['Date'].map(lambda cd: datetime.strptime(cd, '%a, %d %b %Y %H:%M:%S GMT').date())
    plot_esg_score_data['Date'] = plot_esg_score_data['Date'].map(lambda cd: datetime.strptime(cd, '%a, %d %b %Y %H:%M:%S GMT').date())
    plot_portfolio_returns_data['Date'] = plot_portfolio_returns_data['Date'].map(lambda cd: datetime.strptime(cd, '%a, %d %b %Y %H:%M:%S GMT').date())
    plot_benchmark_returns_data['Date'] = plot_benchmark_returns_data['Date'].map(lambda cd: str_to_date(cd))

    return {
        'portfolio_stocks': portfolio_stocks,
        'portfolio_summary': portfolio_summary,
        'benchmark_summary': benchmark_summary,
        'plot_inv_value_data': plot_inv_value_data,
        'plot_esg_score_data': plot_esg_score_data,
        'plot_portfolio_returns_data': plot_portfolio_returns_data,
        'plot_benchmark_returns_data': plot_benchmark_returns_data
    }


def main():
    st.set_page_config(
        page_title="GROW ESG Analysis Visualizer", 
        layout="wide")
    
    style = ("text-align:center; padding: 0px; font-family: arial black;, "
             "font-size: 400%")
    title = f"<h1 style='{style}'>GROW ESG<sup>viz</sup></h1><br><br>"
    st.write(title, unsafe_allow_html=True)

    portfolio_list = get_portfolio_list()
    portfolio = st.selectbox("Select a Portfolio to Visualize", portfolio_list)
    if portfolio and portfolio != 'Select a Portfolio':
        portfolio_data = get_portfolio_data(portfolio)
        portfolio_summary = portfolio_data['portfolio_summary']
        benchmark_summary = portfolio_data['benchmark_summary']
        portfolio_stocks = portfolio_data['portfolio_stocks']
        plot_inv_value_data = portfolio_data['plot_inv_value_data']
        plot_esg_score_data = portfolio_data['plot_esg_score_data']
        plot_portfolio_returns_data = portfolio_data['plot_portfolio_returns_data']
        plot_benchmark_returns_data = portfolio_data['plot_benchmark_returns_data']


        expander = st.expander(f"View {portfolio} Data:", True)
        with expander:
            col_stocks, col_summary = st.columns(2, gap="small")
            with col_stocks:
                st.write(f"### {len(portfolio_stocks)} stocks in {portfolio}")
                cols = ['Current_Value', 'Invested_Value', 'Impact']
                df = portfolio_stocks[cols]
                st.dataframe(df.style.format(subset=['Current_Value', 'Invested_Value'], formatter='{:,.0f}'))

            with col_summary:
                st.write('### Portfolio Summary')
                st.dataframe(portfolio_summary.style.format(formatter='{:,.0f}'))

                st.write('### Benchmark Summary')
                st.dataframe(benchmark_summary.style.format(formatter='{:,.0f}'))

        col1, col2 = st.columns(2, gap="small")
        with col1:
            st.header('Invested Value')
            st.line_chart(data=plot_inv_value_data, x='Date', y='Invested_Value')
        
        with col2:
            st.header('Avg ESG Score')
            st.line_chart(plot_esg_score_data, x='Date', y='ESGScore')

        col3, col4 = st.columns(2, gap="small")
        with col3:
            st.header('Portfolio Returns')
            st.line_chart(data=plot_portfolio_returns_data, x='Date', y='ROIC')

        with col4:
            st.header('Benchmark Returns')
            st.line_chart(data=plot_benchmark_returns_data, x='Date', y='Invested_Value')



if (__name__ == "__main__"):
    main()
