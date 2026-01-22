import csv
from datetime import datetime, timedelta
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

DATE_FORMAT = "%d-%m-%Y"


def calculate_residency(
    from_date: datetime = datetime.now(), lookback_period: int = 365
) -> int:
    total_days_outside = 0
    remote_working = 0
    year_ago = from_date - timedelta(days=lookback_period)

    # Calculate grand total over 5-year period (1825 days)
    five_years_ago = from_date - timedelta(days=1825)
    grand_total = 0

    # Calculate total from February 2023 until now
    feb_2023 = datetime(2023, 2, 1)
    feb_2023_total = 0

    with open("travels.csv", "r") as f:
        reader = csv.reader(f)
        next(reader)

        for row in reader:
            departure_time = datetime.strptime(row[0], DATE_FORMAT)
            arrival_time = datetime.strptime(row[1], DATE_FORMAT)
            if arrival_time < departure_time:
                raise ValueError("Arrival time cannot be before departure time")

            # Count days outside UK within the 5-year period for grand total
            if arrival_time >= five_years_ago and departure_time <= from_date:
                difference = arrival_time - departure_time
                exclude_days = 0
                if departure_time < five_years_ago:
                    exclude_days += (five_years_ago - departure_time).days
                if arrival_time > from_date:
                    exclude_days += (arrival_time - from_date).days
                grand_total += difference.days - exclude_days - 2

            # Count days outside UK from February 2023 until now
            if arrival_time >= feb_2023 and departure_time <= from_date:
                difference = arrival_time - departure_time
                exclude_days = 0
                if departure_time < feb_2023:
                    exclude_days += (feb_2023 - departure_time).days
                if arrival_time > from_date:
                    exclude_days += (arrival_time - from_date).days
                feb_2023_total += difference.days - exclude_days - 2

            if arrival_time < year_ago or departure_time > from_date:
                continue

            difference = arrival_time - departure_time
            exclude_days = 0
            if departure_time < year_ago:
                exclude_days += (year_ago - departure_time).days

            if arrival_time > from_date:
                exclude_days += (arrival_time - from_date).days

            total_days_outside += (
                difference.days - exclude_days - 2
            )  # day of departure and day of arrival are discounted (partial days are not counted as per UK law)
            if row[2] == "false":
                remote_working += difference.days - exclude_days - 2  # same rule: exclude departure and arrival days
                remote_working -= int(row[3])  # remove annual leaves

    return total_days_outside, remote_working, grand_total, feb_2023_total


look_back_from_date = datetime.now()
total, remote_working, grand_total, feb_2023_total = calculate_residency(from_date=look_back_from_date)


# Calculate 5-year period start date for grand total display
five_year_start_date = look_back_from_date - timedelta(days=1825)

print(f"\nGrand total (from {five_year_start_date.strftime('%d %b %Y')}): {grand_total}/450 days\t| Remaining: {450 - grand_total}")
print(f"Grand total (from 01 Feb 2023): {feb_2023_total}/450 days\t| Remaining: {450 - feb_2023_total}")

# Configuration: how far into the future to project (in days from now)
PROJECTION_DAYS = 365  # Project 1 year into the future
look_forward_until_date = datetime.now() + timedelta(days=PROJECTION_DAYS)

# Find the earliest travel date to start calculations from
earliest_date = None
with open("travels.csv", "r") as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        departure_time = datetime.strptime(row[0], DATE_FORMAT)
        if earliest_date is None or departure_time < earliest_date:
            earliest_date = departure_time

# Start calculations from the earliest travel date (or 365 days before if needed for rolling calculation)
calculation_start_date = earliest_date if earliest_date else datetime.now()

delta = timedelta(days=1)
remaining_remote_days = []
remaining_total_days = []
actual_remote_days = []
actual_total_days = []
total = 0
remote_working = 0
grand_total = 0
days = []
date_objects = []

# Collect data for the rolling period - from earliest date to projection date
calculation_date = calculation_start_date
while calculation_date <= look_forward_until_date:
    total, remote_working, grand_total, feb_2023_total = calculate_residency(
        from_date=calculation_date
    )  # lookback 365 days from each date
    days.append(calculation_date.strftime(DATE_FORMAT))
    date_objects.append(calculation_date)

    # Store actual days outside
    actual_total_days.append(total)
    actual_remote_days.append(remote_working)

    # Store remaining days
    remaining_remote_days.append(90 - remote_working)
    remaining_total_days.append(180 - total)

    calculation_date += delta

# Function to aggregate data to monthly granularity
def aggregate_monthly(dates, total_days, remote_days):
    """Aggregate daily data into monthly maximums to catch limit breaches"""
    aggregated_dates = []
    aggregated_total = []
    aggregated_remote = []

    # Group by month
    current_month = (dates[0].year, dates[0].month)
    month_dates = []
    month_total = []
    month_remote = []

    for i, date in enumerate(dates):
        date_month = (date.year, date.month)

        if date_month != current_month:
            if month_total:
                # Use the middle date of the month for better representation
                aggregated_dates.append(month_dates[len(month_dates)//2])
                # Use max to catch the worst-case scenario (highest violation)
                aggregated_total.append(int(np.max(month_total)))
                aggregated_remote.append(int(np.max(month_remote)))
            current_month = date_month
            month_dates = []
            month_total = []
            month_remote = []

        month_dates.append(date)
        month_total.append(total_days[i])
        month_remote.append(remote_days[i])

    # Add the last month
    if month_total:
        aggregated_dates.append(month_dates[len(month_dates)//2])
        aggregated_total.append(int(np.max(month_total)))
        aggregated_remote.append(int(np.max(month_remote)))

    return aggregated_dates, aggregated_total, aggregated_remote

# Aggregate data to monthly granularity
agg_dates, agg_total, agg_remote = aggregate_monthly(date_objects, actual_total_days, actual_remote_days)

# Create subplots with plotly for interactive zooming and panning
fig = make_subplots(
    rows=2, cols=1,
    subplot_titles=('Total Days Outside UK (Rolling 365 Days)',
                    'Remote Working Days (Rolling 365 Days)'),
    vertical_spacing=0.25,  # Increased spacing between plots to avoid overlap
    row_heights=[0.5, 0.5]
)

# Plot 1: Total days outside UK (180-day limit)
fig.add_trace(
    go.Scatter(
        x=agg_dates,
        y=agg_total,
        mode='lines+markers',
        name='Days outside UK',
        line=dict(color='blue', width=2),
        marker=dict(size=8),
        fill='tozeroy',
        fillcolor='rgba(0, 0, 255, 0.3)',
        hovertemplate='<b>Date:</b> %{x|%d %b %Y}<br>' +
                      '<b>Days outside:</b> %{y}<br>' +
                      '<b>Remaining:</b> %{customdata}<br>' +
                      '<extra></extra>',
        customdata=[180 - val for val in agg_total]
    ),
    row=1, col=1
)

# Add 180-day limit line
fig.add_trace(
    go.Scatter(
        x=agg_dates,
        y=[180] * len(agg_dates),
        mode='lines',
        name='180-day limit',
        line=dict(color='red', width=2, dash='dash'),
        hovertemplate='<b>180-day limit</b><extra></extra>'
    ),
    row=1, col=1
)

# Plot 2: Remote working days (90-day limit)
fig.add_trace(
    go.Scatter(
        x=agg_dates,
        y=agg_remote,
        mode='lines+markers',
        name='Remote working days',
        line=dict(color='green', width=2),
        marker=dict(size=8),
        fill='tozeroy',
        fillcolor='rgba(0, 255, 0, 0.3)',
        hovertemplate='<b>Date:</b> %{x|%d %b %Y}<br>' +
                      '<b>Remote days:</b> %{y}<br>' +
                      '<b>Remaining:</b> %{customdata}<br>' +
                      '<extra></extra>',
        customdata=[90 - val for val in agg_remote]
    ),
    row=2, col=1
)

# Add 90-day limit line
fig.add_trace(
    go.Scatter(
        x=agg_dates,
        y=[90] * len(agg_dates),
        mode='lines',
        name='90-day limit',
        line=dict(color='red', width=2, dash='dash'),
        hovertemplate='<b>90-day limit</b><extra></extra>'
    ),
    row=2, col=1
)

# Update layout
fig.update_layout(
    title_text='UK Residency Tracking - Rolling 365 Days<br><sub>Scroll to zoom, drag to pan</sub>',
    title_font_size=16,
    showlegend=True,
    height=1000,  # Increased height to accommodate spacing and range sliders
    hovermode='x unified',
    xaxis=dict(
        rangeslider=dict(
            visible=True,
            thickness=0.05  # Make range slider thinner to save space
        ),
        type='date',
        tickformat='%b %Y',
        dtick='M1'  # Show every month
    ),
    xaxis2=dict(
        rangeslider=dict(
            visible=True,
            thickness=0.05  # Make range slider thinner to save space
        ),
        type='date',
        tickformat='%b %Y',
        dtick='M1'
    )
)

# Update y-axes labels
fig.update_yaxes(title_text="Days outside UK", row=1, col=1, gridcolor='lightgray')
fig.update_yaxes(title_text="Remote working days", row=2, col=1, gridcolor='lightgray')

# Update x-axes labels
fig.update_xaxes(title_text="Date", row=2, col=1, gridcolor='lightgray')
fig.update_xaxes(row=1, col=1, gridcolor='lightgray')

# Show the interactive plot
fig.show()
