import { useDispatch, useSelector, TypedUseSelectorHook } from 'react-redux';
import type { RootState, AppDispatch } from '../store/store';

// Custom hook for accessing Redux dispatch function with proper typing
// This ensures type safety when dispatching actions throughout the app
export const useAppDispatch = () => useDispatch<AppDispatch>();

// Custom hook for selecting data from Redux store with proper typing
// This provides intellisense and type checking for state selection
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;

// Usage examples:
// const dispatch = useAppDispatch(); // Typed dispatch function
// const user = useAppSelector(state => state.auth.user); // Typed state selection
