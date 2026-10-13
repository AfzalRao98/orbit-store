import {test} from 'node:test';
import assert from 'node:assert/strict';
import {products,categories} from '../lib/products.js';
test('each product has a unique routable slug',()=>{assert.equal(new Set(products.map(p=>p.slug)).size,products.length);assert.ok(products.every(p=>/^[a-z0-9-]+$/.test(p.slug)));});
test('all collections have products and all products have valid categories',()=>{assert.ok(categories.every(c=>products.some(p=>p.category===c.name)));assert.ok(products.every(p=>categories.some(c=>c.name===p.category)));});
