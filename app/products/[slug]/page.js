import {notFound} from 'next/navigation';
import {products} from '../../../lib/products';
import {ProductDetail} from '../../../components/store';
export function generateStaticParams(){return products.map(p=>({slug:p.slug}));}
export default async function Page({params}){const {slug}=await params;const product=products.find(p=>p.slug===slug);if(!product)notFound();return <ProductDetail product={product}/>;}
