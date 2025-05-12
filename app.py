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

# === ฟังก์ชันคำนวณค่าเฉลี่ย ADR 2 ปีย้อนหลัง ===
def get_2year_avg_adr(data, current_month, current_year):
    prev_years = sorted(data['Year'].unique())
    if len(prev_years) < 2 or current_year not in prev_years:
        return 0
    current_year_idx = prev_years.index(current_year)
    if current_year_idx < 2:
        return 0
    prev_2_years = prev_years[current_year_idx-2:current_year_idx]
    prev_data = data[(data['Year'].isin(prev_2_years)) & (data['Month'] == current_month)]
    if prev_data.empty:
        return 0
    return prev_data['ADR'].mean()

# === Filter Sidebar ===
st.sidebar.header("Filter Options")
available_years = sorted(data['Year'].unique())  # ดึงปีที่มีอยู่ในข้อมูล
selected_year = st.sidebar.selectbox("Select Year", available_years)
selected_chart = st.sidebar.selectbox("Select Chart", ["Monthly ADR Distribution", "Top 3 ADR Revenue Share", "Year-over-Year Trends", "Monthly Revenue & ADR Comparison", "Channel Mix (OTA Sharing)", "Seasonal Analysis"])

# === Filter Data ===
filtered_data = data[data['Year'] == selected_year]
if selected_year == 2023:
    filtered_data = filtered_data[filtered_data['Month'].isin(months_order[months_order.index('Oct'):])]

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
    for month in enumerate(months_order):
        monthly_data = filtered_data[filtered_data['Month'] == month[1]]
        if not monthly_data.empty:
            revenue_data = monthly_data.groupby('ADR').agg({
                'total_price': 'sum',
                'occupancy': 'sum'
            }).reset_index()
            revenue_data['Percent Share'] = (revenue_data['total_price'] / revenue_data['total_price'].sum()) * 100
            top_3 = revenue_data.sort_values(by='total_price', ascending=False).head(3)
            top_3['Label'] = top_3['ADR'].astype(str) + " THB (" + top_3['Percent Share'].round(2).astype(str) + "%)"
            st.subheader(f"{month[1]} - Top 3 ADR Share")
            fig_pie = px.pie(
                top_3, 
                values='total_price', 
                names='Label', 
                title=f"Top 3 ADR Revenue Share ({month[1]})",
                color_discrete_sequence=px.colors.sequential.Plasma
            )
            unique_key = f"pie-{month[1]}-{uuid.uuid4()}"
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

elif selected_chart == "Channel Mix (OTA Sharing)":
    st.title(f"Channel Mix (OTA Sharing) ({selected_year})")
    st.write("## Revenue Share by Channel")
    channel_mix = filtered_data.groupby('channel').agg({'total_price': 'sum'}).reset_index()
    channel_mix['Percent Share'] = (channel_mix['total_price'] / channel_mix['total_price'].sum()) * 100
    fig = px.pie(channel_mix, values='total_price', names='channel', title=f"Channel Mix Revenue Share ({selected_year})", color_discrete_sequence=px.colors.sequential.Plasma)
    fig.update_layout(height=600, margin=dict(l=10, r=10, t=40, b=20))
    unique_key = f"channel-mix-{uuid.uuid4()}"
    st.plotly_chart(fig, use_container_width=True, key=unique_key)

elif selected_chart == "Seasonal Analysis":
    st.title(f"Seasonal Analysis ({selected_year})")
   

    # สรุปข้อมูลรายเดือน
    monthly_summary = filtered_data.groupby('Month').agg({
        'total_price': 'sum',
        'ADR': 'mean',
        'occupancy': 'sum'
    }).reindex(months_order).reset_index()

    # คำนวณค่าเฉลี่ย ADR 2 ปีย้อนหลังสำหรับแต่ละเดือน
    monthly_summary['ADR_2Year_Avg'] = monthly_summary.apply(
        lambda row: get_2year_avg_adr(data, row['Month'], selected_year), axis=1
    )

    # เพิ่มการเลือกเดือน
    selected_month = st.selectbox("Select Month", months_order)

    # เลือกข้อมูลสำหรับเดือนที่เลือก
    current_month = monthly_summary[monthly_summary['Month'] == selected_month]

    if not current_month.empty:
        # ดึงข้อมูลพื้นฐานและจัดการ NaN
        current_bookings = current_month['occupancy'].iloc[0] if pd.notna(current_month['occupancy'].iloc[0]) else 0
        current_adr = current_month['ADR'].iloc[0] if pd.notna(current_month['ADR'].iloc[0]) else 0
        avg_adr_2year = current_month['ADR_2Year_Avg'].iloc[0] if pd.notna(current_month['ADR_2Year_Avg'].iloc[0]) else 0

        # คำนวณราคาที่แนะนำ (เพิ่ม 10% จากค่าเฉลี่ย 2 ปีย้อนหลัง)
        recommended_adr = avg_adr_2year * 1.10 if avg_adr_2year > 0 else current_adr * 1.10

        # เพิ่ม Slider ให้ผู้ใช้ปรับ ADR
        st.write(f"### Adjust ADR for {selected_month}")
        adjusted_adr = st.slider(
            "Slide to adjust ADR (THB):",
            min_value=0.0,
            max_value=float(max(current_adr * 2, 1000)),  # กำหนดค่าสูงสุดอย่างน้อย 1000 หรือ 2 เท่าของ ADR ปัจจุบัน
            value=float(current_adr if current_adr > 0 else 1000),  # ใช้ค่าเริ่มต้น 1000 หาก current_adr เป็น 0
            step=50.0,
            format="%.2f"
        )

        # คำนวณจำนวนการจองที่เปลี่ยนแปลงตาม ADR (ใช้ความยืดหยุ่นของอุปสงค์)
        elasticity = -1.2  # ความยืดหยุ่น: ถ้า ADR เพิ่ม 1% จำนวนการจองลดลง 1.2%
        if current_adr > 0:  # ป้องกันการหารด้วย 0
            adr_change_percent = (adjusted_adr - current_adr) / current_adr * 100
            bookings_change_percent = adr_change_percent * elasticity
            adjusted_bookings = current_bookings * (1 + bookings_change_percent / 100)
            adjusted_bookings = max(0, round(adjusted_bookings))  # ให้แน่ใจว่าไม่ติดลบและเป็นจำนวนเต็ม
        else:
            adjusted_bookings = current_bookings

        # คำนวณรายได้
        projected_revenue = adjusted_adr * adjusted_bookings
        previous_revenue = avg_adr_2year * adjusted_bookings
        revenue_increase = projected_revenue - previous_revenue

        # แสดงผลการวิเคราะห์
        st.write(f"### Analysis for {selected_month}")
        st.write(f"- จำนวนการจองที่คาดการณ์ : {adjusted_bookings} ครั้ง")
        st.write(f"- ราคาที่แนะนำ: THB {recommended_adr:,.2f}")
        st.write(f"- รายได้รวมที่คาดการณ์ (หลังปรับราคา): THB {projected_revenue:,.2f}")
        st.write(f"- การเพิ่มขึ้นของรายได้: THB {revenue_increase:,.2f}")
    else:
        st.write(f"ไม่มีข้อมูลสำหรับเดือน {selected_month} ในปีที่เลือก")
