import datetime
from playwright.sync_api import Playwright, sync_playwright

ROOM = "Harvey 1B"

def book_day(page, date: datetime.date):
    # Click "Go To Date"
    page.get_by_role("button", name="Go To Date").click()
    
    # Select the correct month
    month_name = date.strftime("%b")  # e.g., "Mar", "Apr"
    page.get_by_role("columnheader", name="January").click()  # Open month dropdown
    page.get_by_text(month_name).click()

    # Click the correct day (active day only)
    day_num = date.day
    page.locator("td.day", has_text=str(day_num)).first.click()

    # Click the 8:00 AM slot
    slot_label = f"8:00 AM {date.strftime('%A, %B %d, %Y')} - {ROOM} - Available"
    page.get_by_label(slot_label).click()

    # Submit time selection
    page.get_by_role("button", name="Submit Times").click()
    page.get_by_role("button", name="Continue").click()

    # Fill booking form
    page.get_by_role("textbox", name="First Name").fill("Branson")
    page.get_by_role("textbox", name="Last Name").fill("Bailey")
    page.get_by_role("textbox", name="Email *").fill("b.bailey1@andersonuniversity.edu")
    page.get_by_role("textbox", name="How many people are in your").fill("1")
    page.get_by_role("textbox", name="What is your purpose for").fill("Work")

    # Submit booking
    page.get_by_role("button", name="Submit my Booking").click()

    # If more bookings, go back
    page.get_by_role("link", name="Make Another Booking").click()


def run(playwright: Playwright) -> None:
    start_input = input("Enter start date (YYYY-MM-DD): ")
    end_input = input("Enter end date (YYYY-MM-DD): ")

    start_date = datetime.datetime.strptime(start_input, "%Y-%m-%d").date()
    end_date = datetime.datetime.strptime(end_input, "%Y-%m-%d").date()

    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://andersonuniversity.libcal.com/reserve/studyrooms")

    current_date = start_date
    while current_date <= end_date:
        # Only book Monday–Friday
        if current_date.weekday() < 5:
            print(f"Booking {current_date.strftime('%A, %B %d, %Y')} at 8:00 AM")
            book_day(page, current_date)
        current_date += datetime.timedelta(days=1)

    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)

