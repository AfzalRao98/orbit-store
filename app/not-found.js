import Link from 'next/link';
export default function NotFound(){return <main className="page-content"><div className="empty"><h1>That essential is missing.</h1><p>We couldn’t find this page.</p><Link href="/shop" className="shop-button">Explore the collection</Link></div></main>;}
