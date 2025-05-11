import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import uuid

# === โหลดข้อมูล ===
data = pd.read_csv('Cleaned_Merged_Data.csv')
data['total_price'] = data['total_price'].str.replace('THB ', '').astype(float)
data['occupancy'] = data['occupancy'].str.split(' - ').str[0].astype(int)
data['Date'] = pd.to_datetime(data['check_-_in'])
data['Year'] = data['Date'].dt.year
data['Month'] = data['Date'].dt.strftime('%b')
data['ADR'] = data['total_price'] / data['occupancy']

# === ทำความสะอาดข้อมูล ===
data['ADR'] = data['ADR'].fillna(0)
data = data[data['occupancy'] > 0]  # ลบแถวที่ occupancy = 0

# === สมมติคอลัมน์ channel ถ้าไม่มีในข้อมูลจริงให้เพิ่มใน CSV ===
if 'channel' not in data.columns:
    data['channel'] = 'OTA'  # สมมติค่าเริ่มต้น

# === สร้างตัวแปร months_order ===
months_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# === Filter Sidebar ===
st.sidebar.header("Filter Options")
available_years = sorted(data['Year'].unique())  # ดึงปีที่มีอยู่ในข้อมูล
selected_year = st.sidebar.selectbox("Select Year", available_years)
selected_chart = st.sidebar.selectbox("Select Chart", ["Monthly ADR Distribution", "Top 3 ADR Revenue Share", "Year-over-Year Trends", "Monthly Revenue & ADR Comparison", "Seasonal Analysis", "Channel Mix (OTA Sharing)"])

# === Filter Data ===
filtered_data = data[data['Year'] == selected_year]

# === Display Metrics ===
if selected_chart == "Monthly ADR Distribution":
    st.title(f"Monthly ADR Distribution ({selected_year})")
    st.write("### ADR Distribution by Month")
    cols = st.columns(3)
    for idx, month in enumerate(months_order):
        with cols[idx % 3]:
            st.subheader(month)
            monthly_data = filtered_data[filtered_data['Month'] == month]
            if not monthly_data.empty:
                fig = px.scatter(
                    monthly_data, 
                    x='total_price', 
                    y='ADR', 
                    size='occupancy',
                    color='occupancy',
                    hover_data={'occupancy': True, 'ADR': True, 'total_price': True},
                    color_continuous_scale=px.colors.sequential.Viridis,
                    opacity=0.8,
                    size_max=15
                )
                fig.update_layout(
                    margin=dict(l=10, r=10, t=20, b=10),
                    height=400,
                    xaxis_title='Total Revenue (THB)',
                    yaxis_title='ADR (THB)',
                    yaxis=dict(range=[0, 4000]), 
                    xaxis=dict(range=[0, 8000]),
                    coloraxis_colorbar=dict(
                        title="No. of Bookings",
                        ticks="outside"
                    )
                )
                unique_key = f"plot-{month}-{uuid.uuid4()}"
                st.plotly_chart(fig, use_container_width=True, key=unique_key)
            else:
                st.write("No Data Available")

elif selected_chart == "Top 3 ADR Revenue Share":
    st.title(f"Top 3 ADR Revenue Share ({selected_year})")
    st.write("## Top 3 ADR Revenue Share by Month (Pie Chart)")
    for month in months_order:
        monthly_data = filtered_data[filtered_data['Month'] == month]
        if not monthly_data.empty:
            revenue_data = monthly_data.groupby('ADR').agg({
                'total_price': 'sum',
                'occupancy': 'sum'
            }).reset_index()
            revenue_data['Percent Share'] = (revenue_data['total_price'] / revenue_data['total_price'].sum()) * 100
            top_3 = revenue_data.sort_values(by='total_price', ascending=False).head(3)
            top_3['Label'] = top_3['ADR'].astype(str) + " THB (" + top_3['Percent Share'].round(2).astype(str) + "%)"
            st.subheader(f"{month} - Top 3 ADR Share")
            fig_pie = px.pie(
                top_3, 
                values='total_price', 
                names='Label', 
                title=f"Top 3 ADR Revenue Share ({month})",
                color_discrete_sequence=px.colors.sequential.Plasma
            )
            unique_key = f"pie-{month}-{uuid.uuid4()}"
            st.plotly_chart(fig_pie, use_container_width=True, key=unique_key)

elif selected_chart == "Year-over-Year Trends":
    st.title(f"Year-over-Year Trends")
    st.write("## Year-over-Year Trends")
    yearly_summary = data.groupby('Year').agg({
        'occupancy': 'sum',
        'ADR': 'mean'
    }).reset_index()
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=yearly_summary['Year'], 
        y=yearly_summary['occupancy'], 
        mode='lines+markers+text',
        name='Total Bookings',
        line=dict(color='blue', shape='spline', smoothing=1.3),
        yaxis='y1',
        text=yearly_summary['occupancy'].map('{:,.0f}'.format),
        textposition="top center"
    ))
    fig_trend.add_trace(go.Scatter(
        x=yearly_summary['Year'], 
        y=yearly_summary['ADR'], 
        mode='lines+markers+text',
        name='Average ADR',
        line=dict(color='green', shape='spline', smoothing=1.3),
        yaxis='y2',
        text=yearly_summary['ADR'].map('{:,.2f}'.format),
        textposition="top center"
    ))
    fig_trend.update_layout(
        height=600,
        margin=dict(l=10, r=10, t=40, b=20),
        xaxis=dict(
            title='Year',
            showgrid=True,
            tickmode='linear',
            dtick=1
        ),
        yaxis=dict(
            title='Bookings',
            side='left',
            showgrid=True,
            tickformat=",",
            tickmode='linear',
            dtick=2000,
            range=[0, 22000]
        ),
        yaxis2=dict(
            title='ADR (THB)',
            side='right',
            overlaying='y',
            showgrid=False,
            tick0=900,
            dtick=200,
            range=[900, 7000]
        ),
        legend=dict(x=0.01, y=0.99)
    )
    unique_key = f"trend-{uuid.uuid4()}"
    st.plotly_chart(fig_trend, use_container_width=True, key=unique_key)

elif selected_chart == "Monthly Revenue & ADR Comparison":
    st.title(f"Monthly Revenue & ADR Comparison ({selected_year})")
    st.write("## Monthly Revenue & ADR Comparison")
    monthly_summary = filtered_data.groupby('Month').agg({
        'total_price': 'sum',
        'ADR': 'mean'
    }).reindex(months_order).reset_index()
    st.write("### Monthly Summary Data")
    st.write(monthly_summary)
    fig_comparison = go.Figure()
    fig_comparison.add_trace(go.Bar(
        x=monthly_summary['Month'],
        y=monthly_summary['total_price'],
        name='Total Revenue (THB)',
        marker_color='lightblue',
        yaxis='y1'
    ))
    fig_comparison.add_trace(go.Scatter(
        x=monthly_summary['Month'],
        y=monthly_summary['ADR'],
        mode='lines+markers',
        name='Average ADR (THB)',
        line=dict(color='red', shape='spline', smoothing=1.3),
        yaxis='y2'
    ))
    fig_comparison.update_layout(
        height=600,
        margin=dict(l=10, r=10, t=40, b=20),
        xaxis=dict(
            title='Month',
            showgrid=True,
            categoryorder='array',
            categoryarray=months_order
        ),
        yaxis=dict(
            title='Revenue (THB)',
            side='left',
            showgrid=True,
            tickformat=",",
            range=[0, monthly_summary['total_price'].max() * 1.2]
        ),
        yaxis2=dict(
            title='ADR (THB)',
            side='right',
            overlaying='y',
            showgrid=False,
            range=[0, monthly_summary['ADR'].max() * 1.2]
        ),
        legend=dict(x=0.01, y=0.99),
        barmode='group'
    )
    unique_key = f"comparison-{uuid.uuid4()}"
    st.plotly_chart(fig_comparison, use_container_width=True, key=unique_key)

elif selected_chart == "Seasonal Analysis":
    st.title(f"Seasonal Analysis ({selected_year})")
    st.write("## Seasonal Trends of Revenue and ADR")
    monthly_summary = filtered_data.groupby('Month').agg({'total_price': 'sum', 'ADR': 'mean'}).reindex(months_order).reset_index()
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=monthly_summary['Month'],
        y=monthly_summary['total_price'],
        name='Total Revenue (THB)',
        marker_color='lightblue',
        yaxis='y1'
    ))
    fig.add_trace(go.Scatter(
        x=monthly_summary['Month'],
        y=monthly_summary['ADR'],
        mode='lines+markers',
        name='Average ADR (THB)',
        line=dict(color='red', shape='spline', smoothing=1.3),
        yaxis='y2'
    ))
    fig.update_layout(
        height=600,
        margin=dict(l=10, r=10, t=40, b=20),
        xaxis=dict(title='Month', showgrid=True, categoryorder='array', categoryarray=months_order),
        yaxis=dict(title='Revenue (THB)', side='left', showgrid=True, tickformat=",", range=[0, monthly_summary['total_price'].max() * 1.2]),
        yaxis2=dict(title='ADR (THB)', side='right', overlaying='y', showgrid=False, range=[0, monthly_summary['ADR'].max() * 1.2]),
        legend=dict(x=0.01, y=0.99),
        barmode='group'
    )
    unique_key = f"seasonal-{uuid.uuid4()}"
    st.plotly_chart(fig, use_container_width=True, key=unique_key)

elif selected_chart == "Channel Mix (OTA Sharing)":
    st.title(f"Channel Mix (OTA Sharing) ({selected_year})")
    st.write("## Revenue Share by Channel")
    channel_mix = filtered_data.groupby('channel').agg({'total_price': 'sum'}).reset_index()
    channel_mix['Percent Share'] = (channel_mix['total_price'] / channel_mix['total_price'].sum()) * 100
    fig = px.pie(channel_mix, values='total_price', names='channel', title=f"Channel Mix Revenue Share ({selected_year})", color_discrete_sequence=px.colors.sequential.Plasma)
    fig.update_layout(height=600, margin=dict(l=10, r=10, t=40, b=20))
    unique_key = f"channel-mix-{uuid.uuid4()}"
    st.plotly_chart(fig, use_container_width=True, key=unique_key)