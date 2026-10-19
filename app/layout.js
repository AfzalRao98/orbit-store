import './globals.css';
import './accessories.css';
import {StoreProvider} from '../components/store';
export const metadata={title:'Orbit — Everyday essentials',description:'Thoughtful tech, carefully considered. An ecommerce demo for Hermes.'};
export default function Layout({children}){return <html lang="en"><body><StoreProvider>{children}</StoreProvider></body></html>;}
