import csv
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import mplcursors
import numpy as np

DATE_FORMAT = "%d-%m-%Y"


def show_info(sel):
    xi = sel.target[0]
    vertical_line = plt.axvline(xi, color="red", ls=":", lw=1)
    sel.extras.append(vertical_line)
    ind = int(sel.target.index)
    sel.annotation.set_text(
        f"Remote Days:{remaining_remote_days[ind]}\nTotal Days:{remaining_total_days[ind]}\nDate: {days[ind]}"
    )


def calculate_residency(
    from_date: datetime = datetime.now(), lookback_period: int = 365
) -> int:
    total_days_outside = 0
    remote_working = 0
    year_ago = from_date - timedelta(days=lookback_period)

    # print(
    #     f"From {year_ago.strftime('%d %b %Y')} to {from_date.strftime('%d %b %Y')}: \n"
    # )
    grand_total = 0
    with open("travels.csv", "r") as f:
        reader = csv.reader(f)
        next(reader)

        for row in reader:
            departure_time = datetime.strptime(row[0], DATE_FORMAT)
            arrival_time = datetime.strptime(row[1], DATE_FORMAT)
            if arrival_time < departure_time:
                raise ValueError("Arrival time cannot be before departure time")
            grand_total += (arrival_time - departure_time).days - 2

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
                remote_working += difference.days - exclude_days
                remote_working -= int(row[3])  # remove annual leaves

            # print(
            #     f"{departure_time.strftime('%d %b %Y')} to {arrival_time.strftime('%d %b %Y')}: {difference.days - exclude_days}"
            # )

    return total_days_outside, remote_working, grand_total


look_back_from_date = datetime.now()
total, remote_working, grand_total = calculate_residency(from_date=look_back_from_date)

print(f"\nTotal days outside: {total}\t| Remaining: {180 - total}")
print(f"Remote work days: {remote_working}\t| Remaining: {90 - remote_working}")

print(f"Grand total so far: {grand_total}\t| Remaining: {450 - grand_total}")

look_forward_until_date = datetime.strptime("01-03-2025", DATE_FORMAT)
delta = timedelta(days=1)
remaining_remote_days = []
remaining_total_days = []
total = 0
remote_working = 0
days = []

while look_back_from_date <= look_forward_until_date:
    total, remote_working, _ = calculate_residency(
        from_date=look_back_from_date
    )  # lookback 365 days from today
    days.append(look_back_from_date.strftime(DATE_FORMAT))
    remaining_remote_days.append(90 - remote_working)
    remaining_total_days.append(180 - total)
    look_back_from_date += delta


print(
    f"Remote work days remaining throughout the future days outside: {remaining_remote_days}"
)

plt.xlabel("Date")
plt.ylabel("No. of days")

plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=10))
plt.plot(days, remaining_remote_days)
plt.plot(remaining_total_days)
plt.gcf().autofmt_xdate()

plt.legend(["Permissible remote Wiser days", "Total permissible days"])
mplcursors.cursor(hover=True).connect("add", show_info)
plt.show()

# print(f"\nTotal days outside: {total}\t| Remaining: {180 - total}")
# print(f"Remote work days: {remote_working}\t| Remaining: {90 - remote_working}")
