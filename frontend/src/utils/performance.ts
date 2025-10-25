/**
 * Frontend Code Splitting and Performance Optimization
 *
 * Utilities for lazy loading components, image optimization,
 * dynamic imports, and bundle analysis.
 */

import React, { ReactNode } from 'react';

/**
 * Loading fallback component
 */
const LoadingFallback = () => {
  return React.createElement(
    'div',
    { className: 'flex items-center justify-center h-full bg-gray-900 rounded-lg' },
    React.createElement(
      'div',
      { className: 'animate-spin' },
      React.createElement(
        'svg',
        { className: 'w-8 h-8 text-blue-500', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' },
        React.createElement('path', {
          strokeLinecap: 'round',
          strokeLinejoin: 'round',
          strokeWidth: 2,
          d: 'M13 10V3L4 14h7v7l9-11h-7z',
        })
      )
    )
  );
};

/**
 * Lazy load heavy components with Next.js dynamic import
 */

// Page components - heavy analysis charts
export const AnalyticsPageDynamic = dynamic(
  () => import('@/app/analytics/page').then(mod => mod.default),
  {
    loading: () => <LoadingFallback />,
    ssr: false, // Don't render on server for better performance
  }
);

// Portfolio page with complex calculations
export const PortfolioPageDynamic = dynamic(
  () => import('@/app/portfolio/page').then(mod => mod.default),
  {
    loading: () => <LoadingFallback />,
    ssr: false,
  }
);

// Sentiment page with large news feed
export const SentimentPageDynamic = dynamic(
  () => import('@/app/sentiment/page').then(mod => mod.default),
  {
    loading: () => <LoadingFallback />,
    ssr: true, // Render on server for SEO
  }
);

// Chart components - heavy Recharts
export const PriceChartDynamic = dynamic(
  () => import('@/components/PriceChart').then(mod => mod.default),
  {
    loading: () => <LoadingFallback />,
    ssr: false,
  }
);

export const VolatilityChartDynamic = dynamic(
  () => import('@/components/VolatilityChart').then(mod => mod.default),
  {
    loading: () => <LoadingFallback />,
    ssr: false,
  }
);

export const AllocationChartDynamic = dynamic(
  () => import('@/components/AllocationChart').then(mod => mod.default),
  {
    loading: () => <LoadingFallback />,
    ssr: false,
  }
);

/**
 * Image optimization utilities
 */

/**
 * Get optimized image URL with Next.js Image Optimization
 */
export const getOptimizedImage = (
  src: string,
  width: number = 800,
  quality: number = 80
): string => {
  if (typeof window === 'undefined') return src;

  // Use Next.js Image Optimization API
  const params = new URLSearchParams({
    url: src,
    w: width.toString(),
    q: quality.toString(),
  });

  return `/_next/image?${params.toString()}`;
};

/**
 * Preload critical resources
 */
export const preloadResource = (href: string, as: 'script' | 'style' | 'image' = 'script') => {
  if (typeof window === 'undefined') return;

  const link = document.createElement('link');
  link.rel = 'preload';
  link.as = as;
  link.href = href;

  document.head.appendChild(link);
};

/**
 * Prefetch route on hover/focus
 */
export const prefetchRoute = (href: string) => {
  if (typeof window === 'undefined') return;

  const link = document.createElement('link');
  link.rel = 'prefetch';
  link.href = href;

  document.head.appendChild(link);
};

/**
 * Virtual scroller for large lists
 */
interface VirtualScrollerProps<T> {
  items: T[];
  itemHeight: number;
  renderItem: (item: T, index: number) => ReactNode;
  containerHeight?: number;
}

export const VirtualScroller = <T extends any>({
  items,
  itemHeight,
  renderItem,
  containerHeight = 500,
}: VirtualScrollerProps<T>) => {
  const [scrollTop, setScrollTop] = React.useState(0);

  const visibleRange = Math.ceil(containerHeight / itemHeight);
  const startIndex = Math.floor(scrollTop / itemHeight);
  const endIndex = Math.min(startIndex + visibleRange + 1, items.length);

  const visibleItems = items.slice(startIndex, endIndex);
  const offsetY = startIndex * itemHeight;

  return (
    <div
      className="overflow-y-auto border border-gray-700 rounded-lg bg-gray-900"
      style={{ height: containerHeight }}
      onScroll={(e) => setScrollTop(e.currentTarget.scrollTop)}
    >
      <div style={{ height: items.length * itemHeight, position: 'relative' }}>
        <div
          style={{
            transform: `translateY(${offsetY}px)`,
            position: 'absolute',
            width: '100%',
          }}
        >
          {visibleItems.map((item, idx) => (
            <div key={startIndex + idx} style={{ height: itemHeight }}>
              {renderItem(item, startIndex + idx)}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

/**
 * Debounced search handler
 */
export const useDebounce = <T,>(value: T, delay: number = 300): T => {
  const [debouncedValue, setDebouncedValue] = React.useState<T>(value);

  React.useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => clearTimeout(handler);
  }, [value, delay]);

  return debouncedValue;
};

/**
 * Intersection Observer hook for lazy loading
 */
export const useIntersectionObserver = (
  ref: React.RefObject<HTMLElement>,
  options?: IntersectionObserverInit
): boolean => {
  const [isVisible, setIsVisible] = React.useState(false);

  React.useEffect(() => {
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {
        setIsVisible(true);
        observer.unobserve(entry.target);
      }
    }, options);

    if (ref.current) {
      observer.observe(ref.current);
    }

    return () => observer.disconnect();
  }, [ref, options]);

  return isVisible;
};

/**
 * Lazy load images with intersection observer
 */
export const LazyImage = ({
  src,
  alt,
  width,
  height,
  className,
}: {
  src: string;
  alt: string;
  width?: number;
  height?: number;
  className?: string;
}) => {
  const ref = React.useRef<HTMLImageElement>(null);
  const isVisible = useIntersectionObserver(ref, { rootMargin: '50px' });

  return (
    <img
      ref={ref}
      src={isVisible ? src : 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300"%3E%3C/svg%3E'}
      alt={alt}
      width={width}
      height={height}
      className={className}
      loading="lazy"
    />
  );
};

/**
 * Bundle analysis configuration
 *
 * Add to next.config.js:
 *
 * const withBundleAnalyzer = require('@next/bundle-analyzer')({
 *   enabled: process.env.ANALYZE === 'true',
 * })
 *
 * module.exports = withBundleAnalyzer({
 *   reactStrictMode: true,
 *   swcMinify: true,
 *   compress: true,
 *   productionBrowserSourceMaps: false, // Disable in production
 * })
 *
 * Run analysis:
 * ANALYZE=true npm run build
 */

/**
 * Next.js Image Optimization
 *
 * Usage in components:
 *
 * import Image from 'next/image'
 * import bitcoin from '@/public/bitcoin.png'
 *
 * <Image
 *   src={bitcoin}
 *   alt="Bitcoin"
 *   width={200}
 *   height={200}
 *   priority // For above-the-fold
 * />
 */

/**
 * Production build optimizations
 *
 * 1. Enable SWC minification (faster than Terser)
 * 2. Disable source maps in production
 * 3. Use dynamic imports for routes
 * 4. Compress responses with gzip/brotli
 * 5. Add HTTP/2 push headers
 * 6. Enable caching headers (1 year for static assets)
 */

/**
 * Frontend performance metrics tracking
 */
export const trackWebVitals = (metric: any) => {
  // Send to analytics service
  if (metric.label === 'web-vital') {
    console.log(metric);
    // Example: send to your analytics backend
    fetch('/api/metrics', {
      method: 'POST',
      body: JSON.stringify(metric),
    }).catch(() => {});
  }
};

/**
 * Component memoization helper
 */
export const useMemoComponent = <P extends object>(
  Component: React.FC<P>,
  deps?: React.DependencyList
): React.FC<P> => {
  return React.memo(Component) as React.FC<P>;
};

/**
 * Batch state updates
 */
export const useBatchUpdate = <T extends Record<string, any>>(initialState: T) => {
  const [state, setState] = React.useState<T>(initialState);
  const [updates, setUpdates] = React.useState<Partial<T>>({});

  const batchUpdate = (newUpdates: Partial<T>) => {
    setUpdates(prev => ({ ...prev, ...newUpdates }));
  };

  const flushUpdates = () => {
    if (Object.keys(updates).length > 0) {
      setState(prev => ({ ...prev, ...updates }));
      setUpdates({});
    }
  };

  return { state, batchUpdate, flushUpdates };
};

import React from 'react';
