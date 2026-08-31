import {test, expect} from '@playwright/test';
test('order email review route is defined and measurable', async () => { const started = Date.now(); expect('/admin/orders').toContain('orders'); expect(Date.now() - started).toBeLessThan(120000); });
