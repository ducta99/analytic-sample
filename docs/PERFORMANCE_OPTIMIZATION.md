# Frontend Performance Optimization Guide

**Status**: Implemented  
**Last Updated**: October 25, 2025

## Code Splitting Strategy

### Dynamic Imports (Next.js)

All heavy components should use Next.js `dynamic()` for route-based code splitting:

```typescript
// pages/analytics.tsx
import dynamic from 'next/dynamic';

const AnalyticsPageDynamic = dynamic(
  () => import('@/app/analytics/page'),
  { loading: () => <LoadingFallback />, ssr: false }
);

export default AnalyticsPageDynamic;
```

### Components to Code-Split

1. **Chart Components** (Recharts is 100KB+ gzipped)
   - `PriceChart` - Conditional lazy load when user navigates to analytics
   - `VolatilityChart` - Only load when viewing technical analysis
   - `AllocationChart` - Load on portfolio page demand

2. **Heavy Libraries** (defer non-critical)
   - `chart.js` / `Recharts` - lazy load on demand
   - `D3.js` - only for advanced visualizations
   - Editor libraries - load when editing

3. **Pages** (route-based splitting)
   - `/analytics` - Heavy computation, load on demand
   - `/portfolio` - Portfolio calculations, lazy load
   - `/sentiment` - News feed parsing, lazy load

## Image Optimization

### Next.js Image Component

```typescript
import Image from 'next/image';

<Image
  src="/bitcoin.png"
  alt="Bitcoin"
  width={200}
  height={200}
  priority // For above-the-fold images only
  loading="lazy" // For below-the-fold
  quality={75} // Optimize compression
  placeholder="blur" // Blur while loading
/>
```

### Lazy Loading Strategy

1. **Critical Images** (above the fold)
   - `priority={true}`
   - Load immediately

2. **Non-critical Images** (below the fold)
   - `loading="lazy"`
   - Load when entering viewport

3. **Intersection Observer**
   - Custom hook for granular control
   - Preload on hover

### Supported Formats

1. WebP (modern browsers) - 30% smaller
2. AVIF (cutting edge) - 50% smaller
3. PNG/JPG fallback (old browsers)

## Bundle Analysis

### Commands

```bash
# Analyze bundle size
ANALYZE=true npm run build

# Enable in next.config.js:
const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
});

module.exports = withBundleAnalyzer({
  compress: true,
  swcMinify: true,
  productionBrowserSourceMaps: false,
});
```

### Target Bundle Sizes

- Initial JS: < 150KB
- CSS: < 50KB
- Per route: < 100KB

## Optimization Techniques

### 1. Reduce JavaScript

- Remove unused dependencies
- Tree-shake dead code
- Use smaller alternatives:
  - `lodash` → `lodash-es`
  - `date-fns` → `day.js`
  - `axios` → `fetch` (built-in)

### 2. Route-Based Splitting

```typescript
// pages.tsx
import { lazy, Suspense } from 'react';

const Analytics = lazy(() => import('@/pages/analytics'));
const Portfolio = lazy(() => import('@/pages/portfolio'));

export default function App() {
  return (
    <Suspense fallback={<Loading />}>
      <Routes>
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/portfolio" element={<Portfolio />} />
      </Routes>
    </Suspense>
  );
}
```

### 3. Component Memoization

```typescript
import { memo } from 'react';

const PriceCard = memo(({ price, symbol }) => (
  <div>{symbol}: ${price}</div>
));

export default PriceCard;
```

### 4. Virtual Scrolling

For large lists (50+ items):

```typescript
import { FixedSizeList } from 'react-window';

<FixedSizeList
  height={600}
  itemCount={1000}
  itemSize={50}
  width="100%"
>
  {({ index, style }) => <div style={style}>{items[index]}</div>}
</FixedSizeList>
```

### 5. Debounce/Throttle

```typescript
import { debounce } from 'lodash-es';

const handleSearch = debounce((query) => {
  // Search after 300ms of user stopping typing
}, 300);
```

## Production Build Optimizations

### next.config.js

```javascript
module.exports = {
  reactStrictMode: true,
  swcMinify: true,  // Use SWC instead of Terser
  compress: true,   // gzip compression
  productionBrowserSourceMaps: false, // Disable source maps
  
  images: {
    formats: ['image/avif', 'image/webp'], // Modern formats first
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  },
  
  headers: async () => [{
    source: '/static/:path*',
    headers: [
      {
        key: 'Cache-Control',
        value: 'public, max-age=31536000, immutable',
      },
    ],
  }],
};
```

### HTTP Caching Headers

```
Static assets (1 year):
Cache-Control: public, max-age=31536000, immutable

HTML (no cache - always check):
Cache-Control: public, max-age=0, must-revalidate

JS/CSS (1 month):
Cache-Control: public, max-age=2592000
```

## Performance Monitoring

### Web Vitals

```typescript
import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals';

export function reportWebVitals(metric) {
  console.log(metric);
  
  // Send to analytics
  fetch('/api/metrics', {
    method: 'POST',
    body: JSON.stringify(metric),
  });
}

getCLS(reportWebVitals);
getFID(reportWebVitals);
getFCP(reportWebVitals);
getLCP(reportWebVitals);
getTTFB(reportWebVitals);
```

### Lighthouse Targets

- Performance: ≥ 90
- Accessibility: ≥ 90
- Best Practices: ≥ 90
- SEO: ≥ 90

## Pre-rendering Strategy

### Static Generation (SSG)

```typescript
// /pages/prices.tsx
export async function getStaticProps() {
  const prices = await fetchPrices();
  
  return {
    props: { prices },
    revalidate: 10, // Regenerate every 10 seconds
  };
}

export default function Prices({ prices }) {
  return <PriceList prices={prices} />;
}
```

### Server-Side Rendering (SSR)

```typescript
// For dynamic data (user-specific)
export async function getServerSideProps(context) {
  const user = await getUser(context.req.cookies.token);
  
  return {
    props: { user },
  };
}
```

### Incremental Static Regeneration (ISR)

```typescript
export async function getStaticProps() {
  return {
    props: { /* data */ },
    revalidate: 60, // Regenerate every 60 seconds
  };
}

export async function getStaticPaths() {
  return {
    paths: [{ params: { coin: 'bitcoin' } }],
    fallback: 'blocking', // Generate missing routes on request
  };
}
```

## Target Performance Metrics

| Metric | Target | Current |
|--------|--------|---------|
| First Contentful Paint (FCP) | < 1.8s | TBD |
| Largest Contentful Paint (LCP) | < 2.5s | TBD |
| Cumulative Layout Shift (CLS) | < 0.1 | TBD |
| First Input Delay (FID) | < 100ms | TBD |
| Time to Interactive (TTI) | < 3.5s | TBD |
| Total Blocking Time (TBT) | < 300ms | TBD |

## Checklist

- [ ] Code splitting enabled for heavy routes
- [ ] Images optimized with Next.js Image component
- [ ] Lazy loading for below-the-fold content
- [ ] Bundle size < 200KB (initial)
- [ ] Lighthouse score ≥ 90 on performance
- [ ] Web Vitals monitoring active
- [ ] Caching headers configured
- [ ] Unnecessary dependencies removed
- [ ] Tree-shaking enabled
- [ ] Minification in production

---

**Implementation Status**: ✅ Documented and ready for implementation  
**Performance Target**: Lighthouse ≥ 90 on all metrics
