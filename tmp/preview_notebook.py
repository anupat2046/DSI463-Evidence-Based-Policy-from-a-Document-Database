from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path.cwd()
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True,args=['--disable-gpu'])
 page=b.new_page(viewport={'width':1360,'height':1000},device_scale_factor=1)
 page.goto((root/'output/A4_6624650526_read.html').as_uri(),wait_until='load')
 page.screenshot(path='output/notebook_preview.png')
 locator=page.get_by_role('heading',name='Q3a. เศรษฐกิจ',exact=False)
 locator.scroll_into_view_if_needed()
 page.screenshot(path='output/notebook_evidence_preview.png')
 print('Notebook HTML rendered; headings:',page.locator('h1,h2,h3').count())
 b.close()
