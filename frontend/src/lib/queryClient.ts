// src/lib/queryClient.ts
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 30,        // 30 s — data considered fresh
      gcTime: 1000 * 60 * 5,       // 5 min cache retention
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});
