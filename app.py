import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime, date
import altair as alt

api_url = 'http://b3f9eddc972c.mylabserver.com:8081/'
#api_url = 'http://127.0.0.1:5001/'
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


def get_portfolio_projection(portfolio_name):
    response = requests.get(api_url + 'projection/portfolios/{0}'.format(portfolio_name))
    projection_detail = json.loads(response.text)
    stocks_projection = pd.DataFrame(projection_detail['pd_result']).rename(columns={'_2050_Value': 'Forecasted Value'})
    plot_projection = pd.DataFrame(projection_detail['result_df_grouped']).rename(columns={'CreatedDate': 'Date', 'Invested_Value': 'Invested Value', 'Invested_Value_NoImpact': 'Forecasted Value'})
    final_date = datetime.strptime(projection_detail['final_date'], '%a, %d %b %Y %H:%M:%S GMT').date()

    stocks_projection.set_index('Ticker', inplace=True)
    plot_projection['Date'] = plot_projection['Date'].map(lambda cd: datetime.strptime(cd, '%a, %d %b %Y %H:%M:%S GMT').date())
    plot_projection = plot_projection.loc[plot_projection['Date'] > date.today()]
    plot_projection.drop('Unnamed: 0', axis=1, inplace=True)
    plot_projection.set_index('Date', inplace=True)

    return {
        'final_date': final_date,
        'stocks_projection': stocks_projection,
        'plot_projection': plot_projection
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

        projection_data = get_portfolio_projection(portfolio)
        stocks_projection = projection_data['stocks_projection']
        plot_projection = projection_data['plot_projection']



        tab_current, tab_forecast = st.tabs(['🗃 Current', '📈 Projection'])
        with tab_current:
            expander = st.expander(f"View {portfolio} Data:", True)
            with expander:
                col_stocks, col_summary = st.columns(2, gap="small")
                with col_stocks:
                    st.write(f"### {len(portfolio_stocks)} stocks in {portfolio}")
                    cols = ['Current_Value', 'Invested_Value', 'Impact']
                    df = portfolio_stocks[cols]
                    st.dataframe(df.style.format(subset=['Current_Value', 'Invested_Value'], formatter='{:,.0f}'), use_container_width=True)

                with col_summary:
                    st.write('### Portfolio Summary')
                    st.dataframe(portfolio_summary.style.format(formatter='{:,.0f}'))

                    st.write('### Benchmark Summary')
                    st.dataframe(benchmark_summary.style.format(formatter='{:,.0f}'))

            col_inv_val, col_esg_score = st.columns(2, gap="small")
            with col_inv_val:
                st.header('Invested Value')
                st.line_chart(data=plot_inv_value_data, x='Date', y='Invested_Value')
            
            with col_esg_score:
                st.header('Avg ESG Score')
                st.line_chart(plot_esg_score_data, x='Date', y='ESGScore')

            col_pf_return, col_bn_return = st.columns(2, gap="small")
            with col_pf_return:
                st.header('Portfolio Returns')
                st.line_chart(data=plot_portfolio_returns_data, x='Date', y='ROIC')

            with col_bn_return:
                st.header('Benchmark Returns')
                st.line_chart(data=plot_benchmark_returns_data, x='Date', y='Invested_Value')

        with tab_forecast:
            col_stocks, col_plot = st.columns(2, gap="small")
            with col_stocks:
                st.header('Projection for 1 deg increase in temp')
                columns = ['Company', 'Country', 'Invested_Value', 'Forecasted Value']
                st.dataframe((stocks_projection[columns]).style.format(subset=['Invested_Value', 'Forecasted Value'], formatter='{:,.0f}'))
            with col_plot:
                st.header('Projection Plot')
                data = plot_projection.reset_index().melt('Date')
                chart = alt.Chart(data).mark_line().encode(
                    x = alt.X('Date:T'),
                    y = alt.Y('value:Q', scale = alt.Scale(zero=False)),
                    color = 'variable')
                st.altair_chart(chart, use_container_width=True)


if (__name__ == "__main__"):
    main()
