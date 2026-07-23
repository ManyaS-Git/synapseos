/**
 * Custom hook for memory operations.
 *
 * TODO: Implement using TanStack Query:
 * - useMemories: Query hook for memory list
 * - useCreateMemory: Mutation hook for creating memories
 * - useUpdateMemory: Mutation hook for updating memories
 * - useDeleteMemory: Mutation hook for deleting memories
 * - useSearchMemories: Query hook for memory search
 */

import { useQuery } from '@tanstack/react-query';
import { memoryService } from '@/services/memory';

export function useMemories() {
  return useQuery({
    queryKey: ['memories'],
    queryFn: () => memoryService.getAll(),
  });
}
