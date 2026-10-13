# Orbit ecommerce demo
A runnable Next.js App Router storefront using the approved Orbit visual concept. Products are illustrative CSS artwork, not real merchandise. Browse categories, search, sort prices, add products, adjust quantities, and preview checkout. No payments or real orders.

## Run on Ubuntu
Install Node.js 24 first, then:
```bash
npm ci
npm run dev
```
Open http://localhost:3000. For production: `npm run build` then `npm start`.

## Architecture and limits
Next.js hosts the page and a minimal GET /api/products endpoint. The frontend uses React components and a shared cart context. Catalog data is shared by the frontend and API. The endpoint is illustrative, not a database. Cart quantities persist in localStorage and are shared across pages. No accounts, checkout payments, order storage or database. Six products and USD prices. Product illustrations are CSS, not photography.

## Hermes demonstration
First confirm the working baseline:
```bash
npm test
npm run build
```
On a dedicated demo branch, run `npm run demo:bug`. This introduces a frontend cart bug: increasing quantity does not increase the subtotal. Tests will fail as expected. Commit that intentional demo baseline only in your test repository.

Report through WhatsApp: "When I add two Quiet One headphones, the bag still shows $129 instead of $258. Please investigate, fix it on a new branch, run checks, review the diff and open a PR. Do not merge."

Hermes works in the local clone and uses authenticated GitHub CLI to push/open a PR. Authenticate separately with `gh auth login`; never send credentials in chat. `npm run demo:reset` restores the working baseline manually if needed. This deliberately seeded bug demonstrates a bounded workflow, not guaranteed resolution of arbitrary issues.

## GitHub and Vercel
Create a personal GitHub repository named orbit-store and push these files. Import it in Vercel; select Next.js. No environment variables required. GitHub Actions runs tests/build on PRs, and Vercel generates previews. Configure required checks before merging where available. Vercel previews can build independently of failed tests. WhatsApp/Hermes connections and account authentication are not included in this source archive.

## Validation
Unit tests and production build are run during preparation. Browser visual verification is not performed in the build environment; check interactions on your Ubuntu computer before presenting.

## Pages
- `/`: landing page and featured products
- `/shop`: searchable catalog, category filters and price sorting
- `/categories`: collection navigation
- `/products/[slug]`: six product detail pages with quantity selection
- `/cart`: persisted cart, quantity edits, removal and subtotal
- `/checkout`: validated demo contact/delivery form and completion state

Checkout uses fictional details only and never sends form data to a server. Shipping below $150 remains unpriced; totals are explicitly subtotals. The app does not create a real order.
