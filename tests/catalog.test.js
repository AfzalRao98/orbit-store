import {test} from 'node:test';
import assert from 'node:assert/strict';
import {products,categories} from '../lib/products.js';
test('each product has a unique routable slug',()=>{assert.equal(new Set(products.map(p=>p.slug)).size,products.length);assert.ok(products.every(p=>/^[a-z0-9-]+$/.test(p.slug)));});
test('all collections have products and all products have valid categories',()=>{assert.ok(categories.every(c=>products.some(p=>p.category===c.name)));assert.ok(products.every(p=>categories.some(c=>c.name===p.category)));});
test('Accessories includes three distinct, complete demo essentials',()=>{
 const accessories=products.filter(p=>p.category==='Accessories');
 assert.ok(categories.some(c=>c.name==='Accessories'));
 assert.deepEqual(accessories.map(p=>p.slug),['everyday-earphones','carry-on-power','neat-charge-adapter']);
 assert.equal(new Set(products.map(p=>p.id)).size,products.length);
 assert.ok(accessories.every(p=>Number.isInteger(p.price)&&p.price>0&&p.description&&p.features.length&&p.color&&p.art));
});
