import {Shop} from '../../components/store';
import {categories} from '../../lib/products';
export default async function Page({searchParams}){const params=await searchParams;const category=categories.some(c=>c.name===params.category)?params.category:'All';return <Shop initialCategory={category}/>;}
