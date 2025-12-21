import streamlit as st 
import polars as pl 
import plotly.express as px  


st.set_page_config(
        page_title="Credit Dashboard"
        )



st.title("Credit Dashboard")

with st.sidebar:
    st.subheader("Upload a file") 
    uploaded_file = st.file_uploader("Choose a file", type='csv')
    uploaded = False
    try:
        df = pl.read_csv(uploaded_file)
        uploaded=True

        watch_list_amount = df.filter(pl.col('status') == 'Watch List')['amount'].sum()
        watch_list_pct = (watch_list_amount / df['amount'].sum()) * 100 

        

    except Exception as e:
        pass




def summary_stats(df):
    total_val = df['amount'].sum() / 1e6
    total_num = len(df)
    avg_loan_size = total_val / total_num
    avg_yield = df['rate'].mean()
    quality_mix = df.group_by('credit_rating').agg([
        pl.len().alias("Total Loans"),
        (pl.len() / len(df) * 100).alias("PCT of portfolio")
        ]).sort("PCT of portfolio", descending=True)

    results = {
            'total_value': total_val,
            'num_of_loans': total_num,
            'avg_yield': avg_yield,
            'avg_loan_size': avg_loan_size,
            'quality_mix': quality_mix
            }

    return results

if uploaded:
    if watch_list_amount > 15:
            st.error(f"Warning: {watch_list_pct:.1f}% of portfolio on Watch List (£{watch_list_amount})")
    st.dataframe(df)


    st.subheader("Portfolio Summary")
    col1, col2, col3, col4 = st.columns(4)

    summary_stats = summary_stats(df)

    with col1:
        st.metric("Total Value", value=f"£{summary_stats['total_value']}M")

    with col2:
        st.metric(f"Number of Loans", value=summary_stats['num_of_loans'])
    with col3:
        st.metric("Average Loan Size", value=f"£{summary_stats['avg_loan_size']}M")
    with col4:
        st.metric(f"Average Yield", value=f"{summary_stats['avg_yield']:.2f}%")

    st.subheader("Quality Mix")
    st.dataframe(summary_stats['quality_mix'])

    pie_col1, pie_col2 = st.columns(2)

    with pie_col1:

        # Distribution by sector 
        sector_agg = df.group_by('sector').agg([
            pl.len().alias('count')
            ]).with_columns(
                ((pl.col('count') / pl.col('count').sum()) * 100).alias('pct')
            ).sort("pct", descending=True)

        fig = px.pie(sector_agg, values='pct', names='sector')
        st.subheader("Distribution by Sector")
        st.plotly_chart(fig, theme='streamlit')

    with pie_col2:
        # Distribution by credit rating
        fig = px.pie(summary_stats['quality_mix'], values='PCT of portfolio', names='credit_rating')
        st.subheader("Distribution by Credit Rating")
        st.plotly_chart(fig, theme='streamlit')
    

if not uploaded:
    st.write("Please upload a file!")

        
