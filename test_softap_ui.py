"""Browser checks with mocked HTTP endpoints; does NOT validate MCU timing or Wi-Fi."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright

root=Path(__file__).resolve().parent/'Exilir_SoftAP_Logger'
page_html=(root/'web_page.h').read_text(encoding='utf-8').split('R"PAGE(',1)[1].split(')PAGE"',1)[0]
state=dict(steps=0,detector_ready=False,calibration_failed=False,high_m_s2=1.2,low_m_s2=.3,min_interval_ms=300,baseline_m_s2=9.81,sensor_ready=True,sampler_ready=True,recording=False,samples=0,elapsed_ms=0,
           limit_ms=23000,target_hz=50,max_interval_ms=0,missed_slots=0,reason='ready',label='test')
calls=[]
def route(req):
    url=req.request.url;calls.append((req.request.method,url))
    if url.endswith('/status'):body=json.dumps(state);kind='application/json'
    elif url.endswith('/start'):
        assert req.request.method=='POST';state.update(steps=0,detector_ready=False,recording=True,samples=10,elapsed_ms=200,reason='recording');body='{}';kind='application/json'
    elif url.endswith('/stop'):
        assert req.request.method=='POST';state.update(recording=False,samples=210,elapsed_ms=4200,reason='manual_stop');body='{}';kind='application/json'
    elif '/download?' in url:
        assert not state['recording']
        req.fulfill(status=200,content_type='text/csv',headers={'Content-Disposition':'attachment; filename="test.csv"'},body='timestamp,accX,accY,accZ\n0,0,0,9.81\n');return
    elif url.endswith('/metadata'):
        req.fulfill(status=200,content_type='application/json',headers={'Content-Disposition':'attachment; filename="test.json"'},body=json.dumps(state));return
    else:body=page_html;kind='text/html'
    req.fulfill(status=200,content_type=kind,body=body)

with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
    page=browser.new_page(viewport={'width':390,'height':844},accept_downloads=True)
    page.route('http://logger.test/**',route);page.on('dialog',lambda d:d.accept())
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://logger.test/');page.wait_for_function("!document.getElementById('start').disabled")
    assert page.locator('#stop').is_disabled();assert page.locator('#download').is_disabled()
    page.locator('#label').fill('bad label');page.locator('#start').click()
    assert '1–32' in page.locator('#message').inner_text()
    assert not any(u.endswith('/start') for _,u in calls)
    page.locator('#label').fill('walking_P01_S01');page.locator('#start').click()
    page.wait_for_function("!document.getElementById('stop').disabled")
    assert page.locator('#start').is_disabled();assert page.locator('#download').is_disabled()
    state.update(elapsed_ms=4000,steps=2,detector_ready=True);page.wait_for_function("document.getElementById('phase').textContent.includes('AKTIVITAS')")
    assert page.locator('#steps').inner_text()=='2'
    page.locator('#stop').click();page.wait_for_function("!document.getElementById('download').disabled")
    assert page.locator('#steps').inner_text()=='2'
    for key in ['download','download6','metadata']:
        with page.expect_download() as result:page.locator('#'+key).click()
        assert result.value.failure() is None
        page.wait_for_function("!document.getElementById('download').disabled")
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    page.screenshot(path=str(root/'preview_handphone.png'),full_page=True)
    page.locator('#start').click();page.wait_for_function("!document.getElementById('stop').disabled")
    assert page.locator('#steps').inner_text()=='0'
    state.update(recording=False,sensor_ready=False,reason='read_error')
    page.wait_for_function("document.getElementById('phase').textContent.includes('belum siap')")
    assert page.locator('#start').is_disabled()
    assert not errors,errors
    browser.close()
print('PASS: mobile layout, input validation, Start/Stop state, baseline/activity cue, 3 downloads, replace confirmation, sensor error. HTTP is mocked.')
