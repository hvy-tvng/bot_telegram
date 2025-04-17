from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import UnexpectedAlertPresentException
import time


def interpret_response(response_text):
    if "Kiểm tra thất bại , Duy trì nạp tiền và đặt cược bình thường để có thể nhận thưởng" in response_text:
        return "Thành công"
    elif "Tài khoản không tồn tại" in response_text:
        return "Tài khoản không tồn tại"
    elif "Nhận thưởng không thành công, tài khoản của bạn không đủ điều kiện nhận thưởng" in response_text:
        return "Lạm dung"
    else:
        return f"Không xác định: {response_text}"


def extract_alert_text(error_message):
    if "Alert Text:" in error_message:
        start = error_message.find("Alert Text:") + len("Alert Text:")
        end = error_message.find("Message:", start)
        if end == -1:
            return error_message[start:].strip()
        return error_message[start:end].strip()
    return error_message


def check_username_response(username, driver):
    try:
        driver.get("https://google8ksp50k.vip")

        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//input[@placeholder='Tên tài khoản' or contains(@id, 'username')]"))
        )

        username_field.clear()
        username_field.send_keys(username)

        login_button = driver.find_element(By.XPATH, "//button[text()='Nhận ngay']")
        login_button.click()

        time.sleep(1)

        try:
            alert = driver.switch_to.alert
            alert_text = alert.text
            alert.accept()
            return interpret_response(alert_text)
        except:
            return "Error"

    except UnexpectedAlertPresentException as e:
        alert_text = extract_alert_text(str(e))
        try:
            alert = driver.switch_to.alert
            alert.accept()
        except:
            pass
        return interpret_response(alert_text)

    except Exception as e:
        error_msg = str(e)
        alert_text = extract_alert_text(error_msg)
        return interpret_response(alert_text)


def check_multiple_accounts(accounts_string):
    accounts = accounts_string.strip().split()

    options = webdriver.ChromeOptions()
    options.add_argument("--disable-notifications")
    driver = webdriver.Chrome(options=options)

    results = []

    try:
        for account in accounts:
            try:
                alert = driver.switch_to.alert
                alert.accept()
            except:
                pass

            result = check_username_response(account, driver)
            results.append(f"{account}: {result}")
            time.sleep(1)

    finally:
        driver.quit()

    return results


if __name__ == "__main__":
    accounts_input = input("Enter account names separated by spaces (e.g., 'account1 account2 account3'): ")

    results = check_multiple_accounts(accounts_input)
#thisisfuture2 hungkeek2 j97vodich huytung23 khainiem292 tenktowin21 dongvatkee reolo24 bet8kaka hoihan2340 nhahang23 nuhoang492 giaidau99 tulenbai88 emnonhe99
    # Display results in the clean format requested
    for result in results:
        print(result)