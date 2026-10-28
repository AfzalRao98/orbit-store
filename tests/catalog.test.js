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
test('Headphones category has three distinct, complete products',()=>{
 const headphones=products.filter(p=>p.category==='Headphones');
 assert.ok(categories.some(c=>c.name==='Headphones'&&c.art==='headphones'&&c.description));
 assert.deepEqual(headphones.map(p=>p.slug),['studio-calm','commute-fold','open-air']);
 assert.equal(new Set(products.map(p=>p.id)).size,products.length);
 assert.ok(headphones.every(p=>p.art==='headphones'&&Number.isInteger(p.price)&&p.price>0&&p.description&&p.features.length&&p.color));
});
test('Data Cable category has three distinct, complete cables',()=>{
 const cables=products.filter(p=>p.category==='Data Cable');
 assert.ok(categories.some(c=>c.name==='Data Cable'&&c.art==='cable'&&c.description));
 assert.deepEqual(cables.map(p=>p.slug),['everyday-usb-c-cable','braided-usb-c-cable','travel-usb-a-cable']);
 assert.equal(new Set(products.map(p=>p.id)).size,products.length);
 assert.ok(cables.every(p=>p.art==='cable'&&Number.isInteger(p.price)&&p.price>0&&p.description&&p.features.length&&p.color));
});
