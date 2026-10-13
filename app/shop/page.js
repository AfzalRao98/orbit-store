import {Shop} from '../../components/store';
export default async function Page({searchParams}){const params=await searchParams;const category=['Audio','Workspace','Lighting'].includes(params.category)?params.category:'All';return <Shop initialCategory={category}/>;}
