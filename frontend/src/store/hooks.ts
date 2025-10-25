/**
 * Custom Redux Hooks
 * 
 * Pre-typed useDispatch and useSelector hooks for type safety
 */

import { useDispatch, useSelector } from 'react-redux';
import type { RootState, AppDispatch } from './index';

// Pre-typed useDispatch hook
export const useAppDispatch = () => useDispatch<AppDispatch>();

// Pre-typed useSelector hook
export const useAppSelector = useSelector.withTypes<RootState>();
