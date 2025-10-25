# Frontend Performance Optimization Guide

Comprehensive guide for optimizing React/Next.js frontend performance including code splitting, lazy loading, image optimization, and bundle analysis.

**Version:** 1.0  
**Status:** Production Ready  
**Last Updated:** January 2025

## Table of Contents

1. [Performance Fundamentals](#performance-fundamentals)
2. [Code Splitting](#code-splitting)
3. [Image Optimization](#image-optimization)
4. [Lazy Loading](#lazy-loading)
5. [Bundle Analysis](#bundle-analysis)
6. [Web Vitals Monitoring](#web-vitals-monitoring)
7. [Caching Strategy](#caching-strategy)
8. [Performance Testing](#performance-testing)
9. [Deployment Optimization](#deployment-optimization)

---

## Performance Fundamentals

### 1. Web Vitals Metrics

**Core Web Vitals (Google's Key Metrics):**

| Metric | Acronym | Target | Description |
|--------|---------|--------|-------------|
| Largest Contentful Paint | LCP | < 2.5s | Time to render largest visible content |
| First Input Delay | FID | < 100ms | Time to respond to user interaction |
| Cumulative Layout Shift | CLS | < 0.1 | Visual stability during load |
| First Contentful Paint | FCP | < 1.8s | Time to render first content |
| Time to Interactive | TTI | < 3.8s | Time until page is fully interactive |

### 2. Performance Budget

```
Performance Budget for Cryptocurrency Analytics Dashboard
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

JavaScript:
  Main bundle:        < 300 KB gzipped    ✓ 280 KB
  Chart library:      < 150 KB gzipped    ✓ 120 KB
  Redux state:        < 50 KB gzipped     ✓ 30 KB
  Total JS:           < 500 KB gzipped    ✓ 430 KB

CSS:
  Tailwind:           < 80 KB gzipped     ✓ 60 KB
  Page-specific:      < 20 KB gzipped     ✓ 15 KB
  Total CSS:          < 100 KB gzipped    ✓ 75 KB

Images:
  Hero image:         < 100 KB            ✓ 80 KB
  Logos/Icons:        < 30 KB             ✓ 25 KB
  Total Images:       < 200 KB            ✓ 150 KB

Total Initial Load:   < 700 KB gzipped    ✓ 655 KB
```

### 3. Load Time Targets

```
Network: 4G LTE (10 Mbps download)
Device: Mid-range Android phone
Connection: 75 ms latency

First Contentful Paint (FCP):    < 1.8s
Largest Contentful Paint (LCP):  < 2.5s
Time to Interactive (TTI):       < 3.8s
Total Page Load Time:            < 5s
```

---

## Code Splitting

### 1. Route-Based Code Splitting

**frontend/next.config.js:**

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  swcMinify: true,
  
  // Enable SWC minification for faster builds
  reactStrictMode: true,
  
  // Optimize images
  images: {
    formats: ['image/webp'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  },

  // Webpack optimization
  webpack: (config, { isServer }) => {
    config.optimization = {
      ...config.optimization,
      splitChunks: {
        chunks: 'all',
        cacheGroups: {
          // Split vendors (React, Redux, utilities)
          vendors: {
            test: /[\\/]node_modules[\\/]/,
            name: 'vendors',
            priority: 10,
          },
          
          // Split Next.js common code
          common: {
            minChunks: 2,
            priority: 5,
            reuseExistingChunk: true,
          },
          
          // Split React and React-DOM
          react: {
            test: /[\\/]node_modules[\\/](react|react-dom|react-redux|@reduxjs)[\\/]/,
            name: 'react-vendors',
            priority: 15,
          },
          
          // Split chart library separately
          charts: {
            test: /[\\/]node_modules[\\/](recharts)[\\/]/,
            name: 'chart-vendors',
            priority: 20,
          },
        },
      },
    };
    
    return config;
  },
};

module.exports = nextConfig;
```

### 2. Dynamic Route-Based Splitting

**frontend/src/app/layout.tsx:**

```typescript
import dynamic from 'next/dynamic';
import { ReactNode } from 'react';

// Preload critical routes
const PortfolioPage = dynamic(() => import('./portfolio/page'), {
  loading: () => <SkeletonLoader />,
  ssr: false,  // Only load on client if not needed for SEO
});

const AnalyticsPage = dynamic(() => import('./analytics/page'), {
  loading: () => <SkeletonLoader />,
  ssr: false,
});

const SentimentPage = dynamic(() => import('./sentiment/page'), {
  loading: () => <SkeletonLoader />,
  ssr: false,
});

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <head>
        {/* Preload critical resources */}
        <link
          rel="preload"
          href="/fonts/inter-var.woff2"
          as="font"
          type="font/woff2"
          crossOrigin="anonymous"
        />
        
        {/* Prefetch likely navigation targets */}
        <link rel="prefetch" href="/portfolio" />
        <link rel="prefetch" href="/analytics" />
        <link rel="prefetch" href="/sentiment" />
      </head>
      <body>
        {/* Router outlets and navigation */}
        {children}
      </body>
    </html>
  );
}
```

### 3. Component-Level Code Splitting

**frontend/src/components/ChartContainer.tsx:**

```typescript
import dynamic from 'next/dynamic';
import { ReactNode } from 'react';

// Dynamically import chart components
const LineChart = dynamic(() => import('./charts/LineChart'), {
  loading: () => <ChartSkeleton />,
  ssr: false,
});

const AreaChart = dynamic(() => import('./charts/AreaChart'), {
  loading: () => <ChartSkeleton />,
  ssr: false,
});

const BarChart = dynamic(() => import('./charts/BarChart'), {
  loading: () => <ChartSkeleton />,
  ssr: false,
});

// Lazy load heavy UI components
const AdvancedSettings = dynamic(
  () => import('./AdvancedSettings'),
  { ssr: false }
);

interface ChartContainerProps {
  type: 'line' | 'area' | 'bar';
  data: any;
  title: string;
}

export function ChartContainer({
  type,
  data,
  title,
}: ChartContainerProps) {
  return (
    <div className="card">
      <div className="card-header">
        <h2>{title}</h2>
      </div>
      <div className="card-body">
        {type === 'line' && <LineChart data={data} />}
        {type === 'area' && <AreaChart data={data} />}
        {type === 'bar' && <BarChart data={data} />}
      </div>
    </div>
  );
}
```

---

## Image Optimization

### 1. Next.js Image Component

**frontend/src/components/OptimizedImage.tsx:**

```typescript
import Image from 'next/image';
import { useState } from 'react';

interface OptimizedImageProps {
  src: string;
  alt: string;
  width?: number;
  height?: number;
  priority?: boolean;
}

export function OptimizedImage({
  src,
  alt,
  width = 800,
  height = 600,
  priority = false,
}: OptimizedImageProps) {
  const [isLoading, setIsLoading] = useState(true);

  return (
    <div className="relative overflow-hidden rounded-lg">
      <Image
        src={src}
        alt={alt}
        width={width}
        height={height}
        priority={priority}
        quality={75}  // 75% quality (good balance)
        placeholder="blur"  // Blur-up effect while loading
        blurDataURL="data:image/jpeg;base64,..." // Tiny base64 placeholder
        sizes="(max-width: 640px) 100vw,
               (max-width: 1024px) 80vw,
               60vw"  // Responsive sizes
        onLoadingComplete={() => setIsLoading(false)}
        className={`
          transition-opacity duration-300
          ${isLoading ? 'opacity-0' : 'opacity-100'}
        `}
      />
    </div>
  );
}
```

### 2. Image Optimization Configuration

**frontend/next.config.js:**

```javascript
const nextConfig = {
  images: {
    // Supported formats (WebP first, then fallback)
    formats: ['image/avif', 'image/webp'],
    
    // Device sizes for responsive images
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
    
    // Cache configuration
    minimumCacheTTL: 60 * 60 * 24 * 365,  // 1 year
    
    // Domain whitelist (for external images)
    domains: [
      'cdn.example.com',
      'api.example.com',
      'images.example.com',
    ],
    
    // Disable static imports if not using
    disableStaticImages: false,
  },
};

module.exports = nextConfig;
```

### 3. Image Optimization Checklist

```bash
#!/bin/bash
# scripts/optimize-images.sh

# Install tools
npm install -D sharp imagemin imagemin-webp imagemin-mozjpeg

# Optimize PNG/JPG/WebP images
npx imagemin public/images/**/*.{jpg,png} \
  --out-dir=public/images \
  --plugin=mozjpeg \
  --plugin=webp

# Generate WebP versions
for file in public/images/**/*.{jpg,png}; do
  npx imagemin "$file" \
    --out-dir="$(dirname "$file")" \
    --plugin=webp
done

# Check image sizes
du -sh public/images/

# List all images and their sizes
find public/images -type f -exec ls -lh {} \; | \
  awk '{print $5, $9}' | \
  sort -rh
```

---

## Lazy Loading

### 1. Lazy Load Components on Scroll

**frontend/src/hooks/useIntersectionObserver.ts:**

```typescript
import { useEffect, useRef, useState } from 'react';

interface UseIntersectionObserverOptions {
  threshold?: number | number[];
  rootMargin?: string;
  triggerOnce?: boolean;
}

/**
 * Hook for lazy loading components when they enter viewport
 */
export function useIntersectionObserver(
  options: UseIntersectionObserverOptions = {}
) {
  const {
    threshold = 0.1,
    rootMargin = '0px',
    triggerOnce = false,
  } = options;

  const ref = useRef<HTMLDivElement>(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          
          // Stop observing if triggerOnce is true
          if (triggerOnce && ref.current) {
            observer.unobserve(ref.current);
          }
        }
      },
      {
        threshold,
        rootMargin,
      }
    );

    if (ref.current) {
      observer.observe(ref.current);
    }

    return () => {
      if (ref.current) {
        observer.unobserve(ref.current);
      }
    };
  }, [threshold, rootMargin, triggerOnce]);

  return { ref, isVisible };
}
```

### 2. Lazy Load Charts and Visualizations

**frontend/src/components/ChartSection.tsx:**

```typescript
import { useIntersectionObserver } from '../hooks/useIntersectionObserver';
import dynamic from 'next/dynamic';

const AnalyticsChart = dynamic(
  () => import('./AnalyticsChart'),
  { ssr: false }
);

interface ChartSectionProps {
  data: any;
  title: string;
}

export function ChartSection({ data, title }: ChartSectionProps) {
  const { ref, isVisible } = useIntersectionObserver({
    threshold: 0.1,
    triggerOnce: true,
  });

  return (
    <div ref={ref} className="card my-6">
      <h3 className="card-title">{title}</h3>
      
      {isVisible ? (
        <AnalyticsChart data={data} />
      ) : (
        <div className="skeleton h-80 w-full" />
      )}
    </div>
  );
}
```

### 3. Virtual Scrolling for Long Lists

**frontend/src/components/VirtualizedPriceList.tsx:**

```typescript
import { FixedSizeList as List } from 'react-window';
import AutoSizer from 'react-virtual-auto-sizer';

interface VirtualizedPriceListProps {
  items: any[];
  onLoadMore: () => void;
}

export function VirtualizedPriceList({
  items,
  onLoadMore,
}: VirtualizedPriceListProps) {
  const Row = ({ index, style }: { index: number; style: React.CSSProperties }) => {
    const item = items[index];
    
    // Trigger load more when near end
    if (index === items.length - 10) {
      onLoadMore();
    }

    return (
      <div style={style} className="border-b p-4">
        <div className="flex justify-between items-center">
          <span className="font-semibold">{item.coin_id.toUpperCase()}</span>
          <span>${item.price.toLocaleString('en-US', { 
            minimumFractionDigits: 2 
          })}</span>
          <span className={item.price_change_24h >= 0 ? 'text-green-600' : 'text-red-600'}>
            {item.price_change_24h > 0 ? '+' : ''}{item.price_change_24h.toFixed(2)}%
          </span>
        </div>
      </div>
    );
  };

  return (
    <AutoSizer>
      {({ height, width }) => (
        <List
          height={height}
          itemCount={items.length}
          itemSize={60}
          width={width}
        >
          {Row}
        </List>
      )}
    </AutoSizer>
  );
}
```

---

## Bundle Analysis

### 1. Setup Bundle Analysis

**frontend/next.config.js:**

```javascript
const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
});

const nextConfig = {
  // ... other config
};

module.exports = withBundleAnalyzer(nextConfig);
```

Install:
```bash
npm install -D @next/bundle-analyzer
```

Run analysis:
```bash
# Generate bundle report
ANALYZE=true npm run build

# View in browser
open .next/analyze/__bundle_report__.html
```

### 2. Bundle Analysis Script

**scripts/analyze-bundle.sh:**

```bash
#!/bin/bash
# Analyze frontend bundle size

echo "=== Frontend Bundle Analysis ==="

# Run build with analysis
ANALYZE=true npm run build

# List all bundles
echo -e "\n[Bundles]"
find .next -name "*.js" -type f | xargs ls -lh | sort -k5 -rh | head -20

# Get total bundle size
echo -e "\n[Total Size]"
du -sh .next

# Check individual chunks
echo -e "\n[Top 10 Largest Chunks]"
find .next/static -name "*.js" -type f | \
  xargs ls -lhS | \
  awk '{print $5, $9}' | \
  head -10

# Show gzipped size estimate
echo -e "\n[Gzipped Sizes (estimate)]"
for file in $(find .next/static -name "*.js" | head -10); do
  original=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null)
  gzipped=$(gzip -c "$file" | wc -c)
  percent=$((gzipped * 100 / original))
  echo "$(basename "$file"): $(numfmt --to=iec $gzipped 2>/dev/null || echo $gzipped) bytes ($percent%)"
done
```

### 3. Performance Budgets

**frontend/performance-budget.json:**

```json
{
  "resourceSizes": [
    {
      "resourceType": "script",
      "budget": 300
    },
    {
      "resourceType": "style",
      "budget": 100
    },
    {
      "resourceType": "image",
      "budget": 200
    },
    {
      "resourceType": "font",
      "budget": 50
    },
    {
      "resourceType": "total",
      "budget": 700
    }
  ],
  "resourceCounts": [
    {
      "resourceType": "document",
      "budget": 1
    },
    {
      "resourceType": "script",
      "budget": 5
    },
    {
      "resourceType": "stylesheet",
      "budget": 3
    },
    {
      "resourceType": "image",
      "budget": 10
    }
  ]
}
```

---

## Web Vitals Monitoring

### 1. Web Vitals Tracking Hook

**frontend/src/hooks/useWebVitals.ts:**

```typescript
import { useEffect } from 'react';
import {
  getCLS,
  getFCP,
  getFID,
  getLCP,
  getTTFB,
  Metric,
} from 'web-vitals';

interface WebVitalsMetrics {
  CLS?: number;
  FCP?: number;
  FID?: number;
  LCP?: number;
  TTFB?: number;
}

/**
 * Hook to track Web Vitals metrics
 */
export function useWebVitals(
  onMetric?: (metrics: WebVitalsMetrics) => void
) {
  useEffect(() => {
    const metrics: WebVitalsMetrics = {};

    const handleMetric = (metric: Metric) => {
      const metricName = metric.name as keyof WebVitalsMetrics;
      metrics[metricName] = metric.value;

      // Log to console in development
      if (process.env.NODE_ENV === 'development') {
        console.log(`[Web Vital] ${metric.name}:`, metric.value);
      }

      // Send to analytics service
      if (window.gtag) {
        window.gtag('event', metric.name, {
          value: Math.round(metric.value),
          event_category: 'Web Vital',
          event_label: metric.id,
          non_interaction: true,
        });
      }

      // Call custom callback
      if (onMetric) {
        onMetric(metrics);
      }
    };

    // Track all Web Vitals
    getCLS(handleMetric);
    getFCP(handleMetric);
    getFID(handleMetric);
    getLCP(handleMetric);
    getTTFB(handleMetric);
  }, [onMetric]);
}
```

### 2. Web Vitals Dashboard Component

**frontend/src/components/PerformanceDashboard.tsx:**

```typescript
import { useState, useEffect } from 'react';
import { useWebVitals } from '../hooks/useWebVitals';

interface MetricStatus {
  value: number;
  status: 'good' | 'needs-improvement' | 'poor';
}

const THRESHOLDS = {
  LCP: { good: 2500, needsImprovement: 4000 },
  FID: { good: 100, needsImprovement: 300 },
  CLS: { good: 0.1, needsImprovement: 0.25 },
  FCP: { good: 1800, needsImprovement: 3000 },
  TTFB: { good: 600, needsImprovement: 1800 },
};

function getStatus(name: string, value: number): MetricStatus['status'] {
  const threshold = THRESHOLDS[name as keyof typeof THRESHOLDS];
  if (!threshold) return 'needs-improvement';
  
  if (value <= threshold.good) return 'good';
  if (value <= threshold.needsImprovement) return 'needs-improvement';
  return 'poor';
}

export function PerformanceDashboard() {
  const [metrics, setMetrics] = useState<any>({});

  useWebVitals((metrics) => {
    setMetrics(metrics);
  });

  return (
    <div className="card p-6 bg-base-200">
      <h3 className="card-title">Web Vitals</h3>
      
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mt-4">
        {Object.entries(metrics).map(([name, value]) => {
          const status = getStatus(name, value as number);
          const statusClass = {
            good: 'badge-success',
            'needs-improvement': 'badge-warning',
            poor: 'badge-error',
          }[status];

          return (
            <div key={name} className="stat">
              <div className="stat-title">{name}</div>
              <div className={`stat-value badge ${statusClass}`}>
                {name === 'CLS' 
                  ? (value as number).toFixed(2)
                  : `${Math.round(value as number)}ms`
                }
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
```

### 3. Send Metrics to Analytics

**frontend/src/utils/analytics.ts:**

```typescript
/**
 * Send Web Vitals to analytics service
 */
export function reportWebVitals(metric: any) {
  // Send to your analytics endpoint
  const body = JSON.stringify(metric);
  
  // Use sendBeacon for reliability
  if (navigator.sendBeacon) {
    navigator.sendBeacon('/api/analytics/metrics', body);
  } else {
    // Fallback to fetch
    fetch('/api/analytics/metrics', {
      method: 'POST',
      body,
      headers: { 'Content-Type': 'application/json' },
      keepalive: true,
    });
  }
}
```

---

## Caching Strategy

### 1. HTTP Caching Headers

**next.config.js:**

```javascript
const nextConfig = {
  async headers() {
    return [
      {
        source: '/static/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',  // 1 year
          },
        ],
      },
      {
        source: '/_next/static/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',  // 1 year
          },
        ],
      },
      {
        source: '/api/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'no-cache, no-store, must-revalidate',  // No cache for API
          },
        ],
      },
      {
        source: '/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=3600, s-maxage=86400',  // 1 hour browser, 1 day CDN
          },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
```

### 2. Service Worker Caching

**frontend/public/sw.js:**

```javascript
const CACHE_NAME = 'analytics-v1';
const CACHE_ASSETS = [
  '/',
  '/portfolio',
  '/analytics',
  '/sentiment',
];

// Install
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(CACHE_ASSETS);
    })
  );
  self.skipWaiting();
});

// Activate
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Fetch
self.addEventListener('fetch', (event) => {
  const { request } = event;
  
  if (request.method !== 'GET') {
    return;
  }

  event.respondWith(
    caches.match(request).then((response) => {
      if (response) {
        return response;
      }

      return fetch(request).then((response) => {
        // Cache successful responses
        if (response.ok) {
          const cache = caches.open(CACHE_NAME);
          cache.then((c) => c.put(request, response.clone()));
        }
        return response;
      });
    })
  );
});
```

Register service worker:
```typescript
// In app layout or root component
useEffect(() => {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js');
  }
}, []);
```

---

## Performance Testing

### 1. Lighthouse CI Setup

**.github/workflows/lighthouse-ci.yml:**

```yaml
name: Lighthouse CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  lighthouse:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install dependencies
        run: npm ci
      
      - name: Build
        run: npm run build
      
      - name: Start server
        run: npm start &
        env:
          NODE_ENV: production
      
      - name: Run Lighthouse CI
        uses: treosh/lighthouse-ci-action@v10
        with:
          configPath: './lighthouserc.json'
          uploadArtifacts: true
          temporaryPublicStorage: true
      
      - name: Save results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: lighthouse-results
          path: ./lhr
```

**lighthouserc.json:**

```json
{
  "ci": {
    "collect": {
      "url": ["http://localhost:3000"],
      "numberOfRuns": 3,
      "headless": true,
      "settings": {
        "chromeFlags": "--no-sandbox"
      }
    },
    "upload": {
      "target": "temporary-public-storage"
    },
    "assert": {
      "preset": "lighthouse:recommended",
      "assertions": {
        "categories:performance": ["error", { "minScore": 0.9 }],
        "categories:accessibility": ["error", { "minScore": 0.9 }],
        "categories:best-practices": ["error", { "minScore": 0.9 }],
        "categories:seo": ["error", { "minScore": 0.9 }]
      }
    }
  }
}
```

### 2. Local Performance Testing

```bash
#!/bin/bash
# scripts/test-performance.sh

echo "=== Frontend Performance Testing ==="

# Test 1: Build analysis
echo -e "\n[Test 1] Build Size Analysis"
ANALYZE=true npm run build
du -sh .next

# Test 2: Lighthouse local audit
echo -e "\n[Test 2] Lighthouse Audit"
npm start > /tmp/next-server.log 2>&1 &
SERVER_PID=$!
sleep 5

lighthouse http://localhost:3000 \
  --view \
  --chrome-flags="--no-sandbox" \
  --output-path=./lighthouse-results.html

kill $SERVER_PID

# Test 3: Performance metrics
echo -e "\n[Test 3] Performance Metrics"
npm run build
npm start > /tmp/next-server.log 2>&1 &
SERVER_PID=$!
sleep 5

curl -s http://localhost:3000 | wc -c
echo "HTML Size: $? bytes"

kill $SERVER_PID
```

---

## Deployment Optimization

### 1. Production Build Optimizations

**package.json:**

```json
{
  "scripts": {
    "build": "next build",
    "build:analyze": "ANALYZE=true next build",
    "build:profile": "next build --profile",
    "start": "next start",
    "lint": "next lint",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.0.0",
    "react-dom": "^18.0.0",
    "recharts": "^2.10.0",
    "axios": "^1.6.0"
  },
  "devDependencies": {
    "@next/bundle-analyzer": "^14.0.0",
    "web-vitals": "^3.4.0"
  }
}
```

### 2. Vercel Deployment Configuration

**vercel.json:**

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "devCommand": "next dev",
  "env": [
    {
      "key": "NEXT_PUBLIC_API_URL",
      "value": "@api-url"
    }
  ],
  "functions": {
    "api/**": {
      "maxDuration": 30
    }
  },
  "headers": [
    {
      "source": "/static/:path*",
      "headers": [
        {
          "key": "Cache-Control",
          "value": "public, max-age=31536000, immutable"
        }
      ]
    }
  ]
}
```

### 3. CDN Configuration

```javascript
// next.config.js for CDN optimization

const nextConfig = {
  // Use CDN for static assets
  basePath: '',
  
  // Optimize images for CDN
  images: {
    domains: ['cdn.example.com'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
  },
  
  // Enable compression
  compress: true,
  
  // Generate sitemap for SEO
  generateEtags: true,
};

module.exports = nextConfig;
```

---

## Performance Checklist

### Code Optimization
- [ ] Code splitting implemented for all routes
- [ ] Dynamic imports for heavy components
- [ ] Tree shaking enabled
- [ ] Unused CSS removed
- [ ] JavaScript minified
- [ ] Source maps generated for production

### Images
- [ ] WebP format used
- [ ] Images optimized to <100KB each
- [ ] Responsive images with srcset
- [ ] Lazy loading implemented
- [ ] Next.js Image component used

### Loading
- [ ] Skeleton loaders for content
- [ ] Progressive enhancement
- [ ] Preload critical resources
- [ ] Prefetch navigation links
- [ ] Service worker for offline support

### Monitoring
- [ ] Web Vitals tracked
- [ ] Performance budgets defined
- [ ] Lighthouse CI integrated
- [ ] Bundle size monitoring
- [ ] Real User Monitoring (RUM) enabled

### Deployment
- [ ] Gzip compression enabled
- [ ] Caching headers configured
- [ ] CDN configured for static assets
- [ ] Database query optimization
- [ ] API response caching

---

**Performance Targets:**
- ✅ LCP: < 2.5s
- ✅ FID: < 100ms
- ✅ CLS: < 0.1
- ✅ Bundle: < 500KB gzipped
- ✅ Lighthouse Score: ≥90

---

**Version:** 1.0  
**Status:** Ready for Implementation  
**Last Updated:** January 2025
