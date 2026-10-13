import {products} from '../../../lib/products.js';
export async function GET(){return Response.json({products,currency:'USD',demo:true});}
