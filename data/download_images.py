from playwright.sync_api import sync_playwright
import os
import time
import re

BASE_PATH = r"C:\DEV\RoboticImaging\data\test_data"
URL = "https://discover.matterport.com/space/QTgiKQhGTfh"


def run():
    os.makedirs(BASE_PATH, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        page.goto(URL)
        page.wait_for_timeout(5000)

        # Try to access iframe, fallback to page
        frame = None
        iframe = page.locator("iframe").first

        if iframe.count() > 0:
            try:
                frame = iframe.element_handle().content_frame()
                print("Using iframe context")
            except:
                print("Iframe not accessible, fallback to main page")

        if not frame:
            frame = page

        spot_index = 1

        while True:
            print(f"\n--- Spot {spot_index} ---")

            # Open gallery (click on visible large image)
            try:
                frame.locator('[role="button"]').filter(has=frame.locator("img")).first.click()
            except:
                print("Failed to open gallery")
                break

            process_gallery(frame, page, BASE_PATH, spot_index)

            # Move to next spot
            next_spot = frame.locator("span.icon-dpad-right").first

            if not next_spot.is_visible():
                print("No more spots")
                break

            next_spot.click()
            time.sleep(2)

            spot_index += 1

        browser.close()


def process_gallery(frame, page, base_path, spot_index):
    spot_dir = os.path.join(base_path, f"spot_{spot_index:03d}")
    os.makedirs(spot_dir, exist_ok=True)

    while True:
        try:
            label = frame.locator("span.list-nav-label").inner_text()
            current, total = map(int, label.split(" of "))
        except:
            print("Failed reading index")
            break

        print(f"Image {current}/{total}")

        # Download
        try:
            download_btn = frame.locator("button").filter(has=frame.locator("svg")).last

            with page.expect_download() as download_info:
                download_btn.click()

            download = download_info.value
            path = os.path.join(spot_dir, f"img_{current:03d}.jpg")
            download.save_as(path)

        except Exception as e:
            print("Download failed:", e)

        if current >= total:
            break

        # Next image
        try:
            frame.locator("span.icon-dpad-right").last.click()
            time.sleep(1)
        except:
            print("Failed next image")
            break

    # Close gallery
    page.keyboard.press("Escape")
    time.sleep(1)


if __name__ == "__main__":
    run()