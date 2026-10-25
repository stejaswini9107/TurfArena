import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE = os.getenv('TURF_URL', 'http://127.0.0.1:5506')
API = os.getenv('TURF_API', 'http://127.0.0.1:5000')
USER_EMAIL = os.getenv('TURF_USER_EMAIL', '')
USER_PASSWORD = os.getenv('TURF_USER_PASSWORD', '')
ADMIN_EMAIL = os.getenv('TURF_ADMIN_EMAIL', '')
ADMIN_PASSWORD = os.getenv('TURF_ADMIN_PASSWORD', '')
results = []

options = webdriver.ChromeOptions()
options.add_argument('--window-size=1440,900')
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 12)

def check(code, name, fn):
    try:
        outcome = fn()
        if outcome is None:
            status, note = 'PASS', 'Verified'
        elif isinstance(outcome, tuple):
            status, note = outcome
        else:
            status, note = ('PASS', str(outcome)) if outcome else ('FAIL', 'Condition not met')
    except Exception as e:
        status = 'FAIL'
        note = str(e).strip().splitlines()
        note = note[0][:85] if note else type(e).__name__
    results.append((code, name, status, note))
    print(f'{code:<5} {name:<29} {status:<5} {note[:52]}', flush=True)

def open_page(path):
    driver.get(BASE.rstrip('/') + '/' + path)
    wait.until(lambda d: d.execute_script('return document.readyState') == 'complete')

def visible(css):
    return any(x.is_displayed() for x in driver.find_elements(By.CSS_SELECTOR, css))

def home():
    open_page('index.html')
    assert 'TurfArena' in driver.title
    assert visible('#turfGrid')
    return 'Homepage and turf container loaded'

def filters():
    open_page('index.html')
    assert visible('#sportFilter') and visible('#priceFilter') and visible('#ratingFilter')
    assert visible('#turfSearchInput')
    return 'Search and filter controls visible'

def turfs():
    open_page('index.html')
    wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, '#turfGrid > *')) > 0)
    return f'{len(driver.find_elements(By.CSS_SELECTOR, "#turfGrid > *"))} turf cards displayed'

def booking_ui():
    open_page('index.html')
    assert driver.find_elements(By.CSS_SELECTOR, '#bookingDate')
    assert driver.find_elements(By.CSS_SELECTOR, '#slotsGrid')
    assert driver.find_elements(By.CSS_SELECTOR, '#weatherRecommendation')
    return 'Booking, slots and weather elements present'

def login_form():
    open_page('login.html')
    assert visible('#signInForm') and visible('#loginEmail') and visible('#loginPass')
    return 'Player sign-in form visible'

def registration_form():
    open_page('login.html')
    driver.find_element(By.ID, 'btnSignUp').click()
    assert visible('#signUpForm') and visible('#regEmail')
    return 'Registration form opens'

def community():
    open_page('community.html')
    assert visible('#lobbySection')
    driver.find_element(By.CSS_SELECTOR, '[onclick*="switchCommTab(\'wars\'"]').click()
    assert visible('#warsSection')
    driver.find_element(By.CSS_SELECTOR, '[onclick*="switchCommTab(\'tournaments\'"]').click()
    assert visible('#tournamentsSection')
    return 'Lobby, wars and tournaments tabs switch'

def admin_form():
    open_page('admin-login.html')
    assert visible('#adminForm') and visible('#adminEmail')
    return 'Admin sign-in form visible'

def api_health():
    open_page('index.html')
    result = driver.execute_async_script('''const done=arguments[arguments.length-1];
      fetch(arguments[0], {method:'GET'}).then(r=>done({ok:r.ok,status:r.status}))
      .catch(e=>done({error:String(e)}));''', API + '/api/health')
    if result.get('error'):
        return 'FAIL', result['error']
    if result.get('ok'):
        return 'PASS', f'API health HTTP {result["status"]}'
    return 'FAIL', f'API health HTTP {result.get("status")}; check endpoint'

def authenticated_login(page, email, password, id_email, id_password, form, destination):
    if not email or not password:
        return 'SKIP', 'Set login credentials via environment variables'
    open_page(page)
    driver.find_element(By.ID, id_email).send_keys(email)
    driver.find_element(By.ID, id_password).send_keys(password)
    driver.find_element(By.ID, form).submit()
    wait.until(lambda d: destination in d.current_url)
    return 'PASS', 'Authenticated redirect verified'

print('\nTURFARENA - SELENIUM TEST EXECUTION')
print('Date:', datetime.now().strftime('%d-%m-%Y %H:%M'))
print('Website:', BASE, '| API:', API)
print('-' * 96)
print(f'{"ID":<5} {"TEST CASE":<29} {"RESULT":<5} OBSERVATION')
print('-' * 96)
try:
    check('TC01', 'Homepage', home)
    check('TC02', 'Search and filters', filters)
    check('TC03', 'Turf listing', turfs)
    check('TC04', 'Booking and weather UI', booking_ui)
    check('TC05', 'Player login UI', login_form)
    check('TC06', 'Registration UI', registration_form)
    check('TC07', 'Community navigation', community)
    check('TC08', 'Admin login UI', admin_form)
    check('TC09', 'Backend health endpoint', api_health)
    check('TC10', 'Player authentication', lambda: authenticated_login('login.html', USER_EMAIL, USER_PASSWORD, 'loginEmail', 'loginPass', 'signInForm', 'index.html'))
    check('TC11', 'Admin authentication', lambda: authenticated_login('admin-login.html', ADMIN_EMAIL, ADMIN_PASSWORD, 'adminEmail', 'adminPass', 'adminForm', 'admin-dashboard.html'))
finally:
    driver.quit()

print('-' * 96)
print('SUMMARY:', ' | '.join(f'{status}: {sum(r[2] == status for r in results)}' for status in ('PASS', 'FAIL', 'SKIP')))
print('Note: UI checks do not prove booking transactions, double-booking prevention or ML accuracy.')
print('Add separate manual/API tests for those workflows before claiming they passed.')
input('\nPress Enter to close this results window...')
