import {test} from 'node:test';
import assert from 'node:assert/strict';
import {lineTotal,subtotal} from '../public/cart.js';
test('quantity increases line total',()=>assert.equal(lineTotal(129,2),258));
test('removing all units gives zero',()=>assert.equal(lineTotal(129,0),0));
test('mixed items sum correctly',()=>assert.equal(subtotal([{price:129,quantity:2},{price:69,quantity:1}]),327));
test('empty cart gives zero',()=>assert.equal(subtotal([]),0));
test('invalid quantity rejected',()=>assert.throws(()=>lineTotal(129,-1)));
