"""Optional real-browser checks against an already running local app.

Requires Playwright in the test environment, not the dashboard runtime.
Example: python dashboard/tests/browser_smoke.py --channel msedge
"""
import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

parser = argparse.ArgumentParser()
parser.add_argument('--channel',default='msedge')
parser.add_argument('--url',default='http://127.0.0.1:8501')
args = parser.parse_args()

with sync_playwright() as p:
    browser = p.chromium.launch(channel=args.channel,headless=True)
    page = browser.new_page(viewport={'width':1440,'height':1500},device_scale_factor=1)
    errors = []
    page.on('pageerror',lambda error: errors.append(str(error)))
    page.goto(args.url)
    expect(page.get_by_text('Put demand at the center of fleet planning',exact=True)).to_be_visible(timeout=60000)
    figures = Path('reports/figures')
    figures.mkdir(exist_ok=True)
    for section,count in [('Executive Overview',1),('Demand and Hotspots',6),('OD and Time Patterns',2),('Forecasting',1),('Recommendations',0)]:
        page.get_by_text(section,exact=True).first.click()
        if section=='Demand and Hotspots':
            page.get_by_text('Weekday volume · all zones',exact=True).click()
        expect(page.locator('[data-testid="stPlotlyChart"] .js-plotly-plot')).to_have_count(count,timeout=30000)
        expect(page.get_by_role('button',name='Stop',exact=True)).to_have_count(0,timeout=30000)
        for plot in page.locator('[data-testid="stPlotlyChart"] .js-plotly-plot').all():
            plot.scroll_into_view_if_needed()
            expect(plot).to_be_visible()
            assert plot.evaluate('(el) => Array.isArray(el.data) && el.data.length > 0'), 'Empty Plotly figure'
        assert page.locator('[data-testid="stException"]').count()==0
        if section in ('Executive Overview','Forecasting'):
            page.locator('[data-testid="stMain"]').evaluate('(el) => el.scrollTop = 0')
            if section=='Forecasting':
                expect(page.locator('[data-testid="stDataFrame"] canvas').first).to_be_visible(timeout=30000)
            page.screenshot(path=str(figures/('bonus_track6_'+('overview' if section=='Executive Overview' else 'forecasting')+'.png')),full_page=True)
        print(section+': browser charts rendered',flush=True)
    assert not errors,errors
    browser.close()
print('Browser smoke checks passed.')
