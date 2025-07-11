#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# --- Page Configuration ---
st.set_page_config(
    page_title="Advanced Loan Amortization Calculator",
    layout="wide", # Set layout to wide for landscape view
    initial_sidebar_state="expanded"
)

# --- Custom CSS for better aesthetics ---
st.markdown("""
    <style>
        /* General styling for the app */
        .stApp {
            background-color: #f0f2f6; /* Light gray background */
            color: #333333; /* Darker text */
        }
        /* Header styling */
        h1, h2, h3 {
            color: #1a73e8; /* Google Blue */
        }
        /* Buttons styling */
        .stButton>button {
            background-color: #4285f4; /* Google Blue */
            color: white;
            border-radius: 8px;
            padding: 10px 20px;
            font-size: 16px;
            border: none;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            background-color: #357ae8; /* Darker blue on hover */
            box-shadow: 3px 3px 8px rgba(0,0,0,0.3);
            transform: translateY(-2px);
        }
        /* Input fields styling */
        .stTextInput>div>div>input {
            border-radius: 8px;
            border: 1px solid #ccc;
            padding: 8px 12px;
        }
        .stNumberInput>div>div>input {
            border-radius: 8px;
            border: 1px solid #ccc;
            padding: 8px 12px;
        }
        /* Expander styling */
        .streamlit-expanderHeader {
            background-color: #e8f0fe; /* Light blue for expander header */
            border-radius: 8px;
            padding: 10px;
            font-weight: bold;
            color: #1a73e8;
        }
        /* Metrics styling */
        [data-testid="stMetric"] {
            background-color: #ffffff;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            margin-bottom: 15px;
        }
        [data-testid="stMetricLabel"] {
            font-size: 1.1em;
            color: #555555;
        }
        [data-testid="stMetricValue"] {
            font-size: 1.8em;
            font-weight: bold;
            color: #1a73e8;
        }
        /* Table styling */
        .dataframe {
            font-size: 0.9em;
        }
    </style>
""", unsafe_allow_html=True)

# --- Title and Description ---
st.title("🏡 Advanced Loan Amortization Calculator")
st.write("Calculate your loan payments, generate a detailed amortization schedule, and visualize your repayment journey.")

# --- Input Section (Sidebar for better organization) ---
st.sidebar.header("Loan Details")

principal = st.sidebar.number_input("Principal Amount (₹)", min_value=1000.0, value=200000.0, step=1000.0)
annual_rate = st.sidebar.number_input("Annual Interest Rate (%)", min_value=0.01, value=4.5, step=0.01)
term_years = st.sidebar.number_input("Loan Term (Years)", min_value=1, value=30, step=1)

payment_frequency = st.sidebar.selectbox(
    "Payment Frequency",
    ("Monthly", "Bi-Weekly", "Quarterly", "Annually")
)

extra_payment = st.sidebar.number_input("Optional: Extra Payment (₹)", min_value=0.0, value=0.0, step=10.0)

calculate_button = st.sidebar.button("Calculate Amortization")

# --- Helper function to calculate amortization ---
def calculate_amortization_schedule(principal, annual_rate, term_years, payment_frequency, extra_payment):
    """
    Calculates the amortization schedule based on provided loan details.
    Returns a DataFrame with the schedule, base monthly payment, total interest paid, and loan duration.
    """
    # Adjust rates and terms based on payment frequency
    if payment_frequency == "Monthly":
        payments_per_year = 12
    elif payment_frequency == "Bi-Weekly":
        payments_per_year = 26
    elif payment_frequency == "Quarterly":
        payments_per_year = 4
    elif payment_frequency == "Annually":
        payments_per_year = 1

    periodic_rate = (annual_rate / 100) / payments_per_year
    total_payments_periods = term_years * payments_per_year

    # Calculate base periodic payment
    if periodic_rate == 0: # Handle zero interest rate case
        base_periodic_payment = principal / total_payments_periods
    else:
        base_periodic_payment = principal * (periodic_rate * (1 + periodic_rate)**total_payments_periods) / ((1 + periodic_rate)**total_payments_periods - 1)

    total_periodic_payment = base_periodic_payment + extra_payment

    schedule_data = []
    current_balance = principal
    total_interest_paid = 0
    total_principal_paid = 0
    payment_number = 0

    # Safety break for very long loans or small extra payments
    max_iterations = total_payments_periods * 2 if total_payments_periods > 0 else 10000

    while current_balance > 0.01 and payment_number < max_iterations:
        payment_number += 1
        interest_for_period = current_balance * periodic_rate
        principal_for_period = total_periodic_payment - interest_for_period

        # Adjust last payment to not overpay
        if current_balance < principal_for_period:
            principal_for_period = current_balance
            # If extra payment makes it pay off early, the last payment is just remaining principal + interest
            total_periodic_payment = principal_for_period + interest_for_period
            current_balance = 0
        else:
            current_balance -= principal_for_period

        total_interest_paid += interest_for_period
        total_principal_paid += principal_for_period

        schedule_data.append({
            "Payment No.": payment_number,
            "Payment Amount": total_periodic_payment,
            "Principal Paid": principal_for_period,
            "Interest Paid": interest_for_period,
            "Remaining Balance": current_balance
        })

    df_schedule = pd.DataFrame(schedule_data)
    return df_schedule, base_periodic_payment, total_interest_paid, payment_number

# --- Calculation Logic ---
if calculate_button:
    if principal <= 0 or annual_rate < 0 or term_years <= 0:
        st.error("Please enter positive values for Principal, Rate, and Term.")
    else:
        # Calculate schedule with extra payment
        df_schedule_with_extra, base_payment_with_extra, total_interest_with_extra, duration_with_extra = \
            calculate_amortization_schedule(principal, annual_rate, term_years, payment_frequency, extra_payment)

        # Calculate schedule WITHOUT extra payment for comparison
        df_schedule_no_extra, base_payment_no_extra, total_interest_no_extra, duration_no_extra = \
            calculate_amortization_schedule(principal, annual_rate, term_years, payment_frequency, 0) # 0 extra payment

        st.subheader("Summary")

        # --- Summary Metrics ---
        col1, col2, col3, col4 = st.columns(4)
        col1.metric(f"Base {payment_frequency} Payment", f"₹{base_payment_with_extra:,.2f}")
        col2.metric(f"Total {payment_frequency} Payment", f"₹{base_payment_with_extra + extra_payment:,.2f}")
        col3.metric("Total Interest Paid", f"₹{total_interest_with_extra:,.2f}")
        col4.metric("Loan Duration (Periods)", f"{duration_with_extra}")

        # --- Comparison Section ---
        st.subheader("Comparison with No Extra Payment")
        comp_col1, comp_col2, comp_col3 = st.columns(3)

        interest_saved = total_interest_no_extra - total_interest_with_extra
        duration_reduced = duration_no_extra - duration_with_extra

        comp_col1.metric("Interest Saved", f"₹{interest_saved:,.2f}")
        comp_col2.metric("Duration Reduced (Periods)", f"{duration_reduced}")
        comp_col3.metric("Original Loan Duration (Periods)", f"{duration_no_extra}")


        # --- Visualizations Section ---
        st.subheader("Visualizations")

        # Plot 1: Principal vs. Interest Paid Over Time
        fig_payments = px.line(df_schedule_with_extra, x="Payment No.", y=["Principal Paid", "Interest Paid"],
                               title=f"Principal vs. Interest Paid Over Time ({payment_frequency} Payments)",
                               labels={"value": "Amount (₹)", "variable": "Component"},
                               hover_data={"Payment No.": True, "value": ":,.2f", "variable": True})
        fig_payments.update_layout(hovermode="x unified")
        st.plotly_chart(fig_payments, use_container_width=True)

        # Plot 2: Remaining Balance Over Time
        fig_balance = px.area(df_schedule_with_extra, x="Payment No.", y="Remaining Balance",
                              title=f"Remaining Loan Balance Over Time ({payment_frequency} Payments)",
                              labels={"Remaining Balance": "Balance (₹)"},
                              line_shape="spline",
                              hover_data={"Payment No.": True, "Remaining Balance": ":,.2f"})
        fig_balance.update_layout(hovermode="x unified")
        st.plotly_chart(fig_balance, use_container_width=True)

        # --- Amortization Schedule Section (Expandable) ---
        with st.expander("View Full Amortization Schedule"):
            st.dataframe(df_schedule_with_extra.style.format({
                "Payment Amount": "₹{:,.2f}",
                "Principal Paid": "₹{:,.2f}",
                "Interest Paid": "₹{:,.2f}",
                "Remaining Balance": "₹{:,.2f}"
            }), use_container_width=True)

            # Download button for the schedule
            csv = df_schedule_with_extra.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Schedule as CSV",
                data=csv,
                file_name=f"loan_amortization_schedule_{principal:.0f}₹_{annual_rate}%.csv",
                mime="text/csv",
                help="Download the full amortization schedule as a CSV file."
            )

else:
    st.info("Enter loan details in the sidebar and click 'Calculate Amortization' to generate the schedule.")
