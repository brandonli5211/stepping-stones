import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

// shadcn's usual class joiner
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
