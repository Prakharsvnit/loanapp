import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Loan Dashboard", layout="wide", page_icon="🏦")

st.markdown("""
    <style>
    .main { padding: 0rem 1rem; background-color: #f0f4f8; }
    .stMetric { background: linear-gradient(135deg, #FF9933 0%, #138808 100%); padding: 20px; border-radius: 12px; color: white; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
    .stMetric label { color: rgba(255, 255, 255, 0.95) !important; font-weight: 600 !important; }
    .stMetric [data-testid="stMetricValue"] { color: white !important; font-weight: 700 !important; }
    h1 { color: #FF9933; font-weight: 800; }
    h2, h3 { color: #138808; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏦 Loan Comparison Dashboard")
st.markdown("<p style='color: #666; font-size: 18px;'>Compare Loans with EMI Calculator & Analysis</p>", unsafe_allow_html=True)

# Sidebar
st.sidebar.header("📋 Loan Details")
num_loans = st.sidebar.number_input("Number of Loans", min_value=1, max_value=5, value=2)

loans = []
for i in range(num_loans):
    with st.sidebar.expander(f"🏦 Loan {i+1}", expanded=True):
        loan = {
            'name': st.text_input(f"Bank Name", f"Bank {i+1}", key=f"name_{i}"),
            'principal': st.number_input(f"Loan Amount (₹)", min_value=10000, value=2500000, step=50000, key=f"principal_{i}"),
            'interest_rate': st.number_input(f"Interest Rate (% p.a.)", min_value=0.01, max_value=30.0, value=8.5 + i*0.5, step=0.01, key=f"rate_{i}"),
            'years': st.number_input(f"Tenure (Years)", min_value=1, max_value=40, value=20, key=f"years_{i}"),
        }
        loans.append(loan)

st.sidebar.markdown("### 💰 Prepayment")
prepayment_amount = st.sidebar.number_input("Yearly Prepayment (₹)", min_value=0, value=0, step=10000)
prepayment_start_year = st.sidebar.number_input("Start from Year", min_value=1, value=1, step=1)

# Functions
def calculate_emi(principal, annual_rate, years):
    if annual_rate == 0:
        return principal / (years * 12)
    monthly_rate = annual_rate / 100 / 12
    num_payments = years * 12
    numerator = monthly_rate * ((1 + monthly_rate) ** num_payments)
    denominator = ((1 + monthly_rate) ** num_payments) - 1
    return principal * (numerator / denominator)

def generate_schedule(principal, annual_rate, years, yearly_prepay=0, prepay_start_year=1):
    monthly_rate = annual_rate / 100 / 12
    emi = calculate_emi(principal, annual_rate, years)
    balance = principal
    schedule = []
    month = 1
    
    while balance > 1:
        interest = balance * monthly_rate
        principal_paid = emi - interest
        
        # Add yearly prepayment at year end
        current_year = ((month - 1) // 12) + 1
        is_year_end = month % 12 == 0
        if is_year_end and current_year >= prepay_start_year and yearly_prepay > 0:
            principal_paid += yearly_prepay
        
        if principal_paid > balance:
            principal_paid = balance
        
        balance -= principal_paid
        
        schedule.append({
            'Month': month,
            'EMI': emi,
            'Principal': principal_paid,
            'Interest': interest,
            'Balance': max(balance, 0)
        })
        
        month += 1
        if month > years * 12 * 3:
            break
    
    return pd.DataFrame(schedule)

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Comparison", "💰 Prepayment", "📈 Interest Analysis", "📋 Amortization"])

with tab1:
    st.header("💳 Loan Comparison")
    
    comparison = []
    for loan in loans:
        emi = calculate_emi(loan['principal'], loan['interest_rate'], loan['years'])
        schedule = generate_schedule(loan['principal'], loan['interest_rate'], loan['years'])
        total_interest = schedule['Interest'].sum()
        total_amount = emi * len(schedule)
        
        comparison.append({
            'Bank': loan['name'],
            'Loan Amount': f"₹{loan['principal']:,.0f}",
            'Rate': f"{loan['interest_rate']:.2f}%",
            'Tenure': f"{loan['years']} years",
            'Monthly EMI': f"₹{emi:,.0f}",
            'Total Interest': f"₹{total_interest:,.0f}",
            'Total Payment': f"₹{total_amount:,.0f}"
        })
    
    st.dataframe(pd.DataFrame(comparison), use_container_width=True, hide_index=True)
    
    st.markdown("### 💰 Key Metrics")
    cols = st.columns(len(loans))
    for i, loan in enumerate(loans):
        with cols[i]:
            emi = calculate_emi(loan['principal'], loan['interest_rate'], loan['years'])
            schedule = generate_schedule(loan['principal'], loan['interest_rate'], loan['years'])
            st.markdown(f"#### {loan['name']}")
            st.metric("Monthly EMI", f"₹{emi:,.0f}")
            st.metric("Total Interest", f"₹{schedule['Interest'].sum():,.0f}")
            st.metric("Interest/Principal", f"{(schedule['Interest'].sum()/loan['principal']*100):.1f}%")

with tab2:
    st.header("💰 Prepayment Benefits")
    
    if prepayment_amount > 0:
        for loan in loans:
            st.markdown(f"### 🏦 {loan['name']}")
            
            schedule_without = generate_schedule(loan['principal'], loan['interest_rate'], loan['years'])
            schedule_with = generate_schedule(loan['principal'], loan['interest_rate'], loan['years'], prepayment_amount, prepayment_start_year)
            
            interest_saved = schedule_without['Interest'].sum() - schedule_with['Interest'].sum()
            time_saved = len(schedule_without) - len(schedule_with)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("💰 Interest Saved", f"₹{interest_saved:,.0f}")
            with col2:
                st.metric("⏰ Time Saved", f"{time_saved//12}y {time_saved%12}m")
            with col3:
                st.metric("✅ Net Benefit", f"₹{interest_saved - (prepayment_amount * (len(schedule_with)//12)):,.0f}")
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=schedule_without['Month'],
                y=schedule_without['Balance'],
                name='❌ Without Prepayment',
                line=dict(color='#ef4444', width=3, dash='dash'),
                hovertemplate='<b>Month:</b> %{x}<br><b>Balance:</b> ₹%{y:,.0f}<extra></extra>'
            ))
            
            fig.add_trace(go.Scatter(
                x=schedule_with['Month'],
                y=schedule_with['Balance'],
                name='✅ With Yearly Prepayment',
                line=dict(color='#10b981', width=3),
                hovertemplate='<b>Month:</b> %{x}<br><b>Balance:</b> ₹%{y:,.0f}<extra></extra>'
            ))
            
            fig.update_layout(
                title=f"Balance Comparison - {loan['name']}",
                xaxis_title="Month",
                yaxis_title="Outstanding Balance (₹)",
                height=400,
                plot_bgcolor='#ffffff',
                hovermode='x unified',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(size=12))
            )
            
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("---")
    else:
        st.info("💡 Set yearly prepayment in sidebar to see savings")

with tab3:
    st.header("📈 Total Interest Comparison")
    
    interest_data = []
    for loan in loans:
        schedule = generate_schedule(loan['principal'], loan['interest_rate'], loan['years'])
        interest_data.append({
            'Bank': loan['name'],
            'Principal': loan['principal'],
            'Interest': schedule['Interest'].sum()
        })
    
    df_int = pd.DataFrame(interest_data)
    
    # Bar chart for interest comparison
    fig_bar = go.Figure()
    
    fig_bar.add_trace(go.Bar(
        name='💰 Principal Amount',
        x=df_int['Bank'],
        y=df_int['Principal'],
        marker_color='#10b981',
        text=df_int['Principal'],
        texttemplate='₹%{text:,.0f}',
        textposition='inside',
        textfont=dict(color='white', size=12, family='Arial Black'),
        hovertemplate='<b>%{x}</b><br>Principal: ₹%{y:,.0f}<extra></extra>'
    ))
    
    fig_bar.add_trace(go.Bar(
        name='💸 Total Interest',
        x=df_int['Bank'],
        y=df_int['Interest'],
        marker_color='#ef4444',
        text=df_int['Interest'],
        texttemplate='₹%{text:,.0f}',
        textposition='inside',
        textfont=dict(color='white', size=12, family='Arial Black'),
        hovertemplate='<b>%{x}</b><br>Interest: ₹%{y:,.0f}<extra></extra>'
    ))
    
    fig_bar.update_layout(
        barmode='stack',
        title="Principal vs Total Interest Payment",
        xaxis_title="Bank",
        yaxis_title="Amount (₹)",
        height=500,
        plot_bgcolor='#ffffff',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(size=13))
    )
    
    st.plotly_chart(fig_bar, use_container_width=True)
    
    # Interest only comparison
    st.markdown("### 💸 Interest Payment Breakdown")
    
    fig_int = go.Figure()
    
    colors_gradient = ['#ef4444', '#f87171', '#fca5a5', '#fecaca', '#fee2e2']
    
    fig_int.add_trace(go.Bar(
        x=df_int['Bank'],
        y=df_int['Interest'],
        marker=dict(
            color=colors_gradient[:len(df_int)],
            line=dict(color='#1e293b', width=2)
        ),
        text=df_int['Interest'],
        texttemplate='₹%{text:,.0f}',
        textposition='outside',
        textfont=dict(color='#1e293b', size=14, family='Arial Black'),
        hovertemplate='<b>%{x}</b><br>Total Interest: ₹%{y:,.0f}<extra></extra>',
        name='Total Interest'
    ))
    
    fig_int.update_layout(
        title="Total Interest Payment by Bank",
        xaxis_title="Bank",
        yaxis_title="Total Interest (₹)",
        height=450,
        plot_bgcolor='#ffffff',
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(size=13))
    )
    
    st.plotly_chart(fig_int, use_container_width=True)
    
    # Summary table
    st.markdown("### 📊 Interest Summary")
    summary = []
    for i, loan in enumerate(loans):
        schedule = generate_schedule(loan['principal'], loan['interest_rate'], loan['years'])
        total_interest = schedule['Interest'].sum()
        summary.append({
            'Bank': loan['name'],
            'Loan Amount': f"₹{loan['principal']:,.0f}",
            'Interest Rate': f"{loan['interest_rate']:.2f}%",
            'Total Interest': f"₹{total_interest:,.0f}",
            'Interest as % of Principal': f"{(total_interest/loan['principal']*100):.1f}%"
        })
    
    st.dataframe(pd.DataFrame(summary), use_container_width=True, hide_index=True)

with tab4:
    st.header("📋 Detailed Amortization Schedule")
    
    selected = st.selectbox("🏦 Select Bank", [loan['name'] for loan in loans])
    loan_idx = [loan['name'] for loan in loans].index(selected)
    loan = loans[loan_idx]
    
    schedule = generate_schedule(loan['principal'], loan['interest_rate'], loan['years'])
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=schedule['Month'],
        y=schedule['Interest'],
        name='💸 Interest Payment',
        marker_color='#ef4444',
        hovertemplate='<b>Month:</b> %{x}<br><b>Interest:</b> ₹%{y:,.0f}<extra></extra>'
    ))
    
    fig.add_trace(go.Bar(
        x=schedule['Month'],
        y=schedule['Principal'],
        name='💰 Principal Payment',
        marker_color='#10b981',
        hovertemplate='<b>Month:</b> %{x}<br><b>Principal:</b> ₹%{y:,.0f}<extra></extra>'
    ))
    
    fig.add_trace(go.Scatter(
        x=schedule['Month'],
        y=schedule['Balance'],
        name='📊 Outstanding Balance',
        line=dict(color='#3b82f6', width=4),
        yaxis='y2',
        hovertemplate='<b>Month:</b> %{x}<br><b>Balance:</b> ₹%{y:,.0f}<extra></extra>'
    ))
    
    fig.update_layout(
        title=f"Amortization Schedule - {selected}",
        xaxis=dict(title="Month", showgrid=True, gridcolor='#e5e7eb'),
        yaxis=dict(title="EMI Amount (₹)", showgrid=True, gridcolor='#e5e7eb'),
        yaxis2=dict(title="Outstanding Balance (₹)", overlaying='y', side='right'),
        barmode='stack',
        hovermode='x unified',
        height=600,
        plot_bgcolor='#ffffff',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(size=13))
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Statistics
    st.markdown("### 📊 Loan Statistics")
    emi = calculate_emi(loan['principal'], loan['interest_rate'], loan['years'])
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Monthly EMI", f"₹{emi:,.0f}")
    with col2:
        st.metric("Total Interest", f"₹{schedule['Interest'].sum():,.0f}")
    with col3:
        st.metric("Total Payment", f"₹{(emi * len(schedule)):,.0f}")
    with col4:
        st.metric("First Month Interest", f"₹{schedule['Interest'].iloc[0]:,.0f}")
    with col5:
        st.metric("Last Month Interest", f"₹{schedule['Interest'].iloc[-1]:,.0f}")
    
    # Yearly summary
    st.markdown("### 📅 Year-wise Summary")
    yearly = schedule.groupby((schedule['Month'] - 1) // 12).agg({
        'Principal': 'sum',
        'Interest': 'sum',
        'Balance': 'last'
    }).reset_index()
    yearly['Year'] = yearly['Month'] + 1
    yearly['Total Paid'] = yearly['Principal'] + yearly['Interest']
    yearly = yearly[['Year', 'Total Paid', 'Principal', 'Interest', 'Balance']]
    yearly.columns = ['Year', 'Total Paid (₹)', 'Principal (₹)', 'Interest (₹)', 'Balance (₹)']
    
    st.dataframe(yearly.style.format({
        'Total Paid (₹)': '₹{:,.0f}',
        'Principal (₹)': '₹{:,.0f}',
        'Interest (₹)': '₹{:,.0f}',
        'Balance (₹)': '₹{:,.0f}'
    }), use_container_width=True, hide_index=True)

st.markdown("---")
st.markdown("<div style='text-align: center; color: #718096;'><p>💡 Adjust parameters in sidebar • All calculations use standard formulas</p></div>", unsafe_allow_html=True)