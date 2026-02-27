import { create } from "zustand";
import type { LoanApplication } from "@/types";

interface AppStore {
  loans: LoanApplication[];
  setLoans: (loans: LoanApplication[]) => void;
  addLoan: (loan: LoanApplication) => void;
  selectedLoanId: string | null;
  setSelectedLoanId: (id: string | null) => void;
}

export const useAppStore = create<AppStore>((set) => ({
  loans: [],
  setLoans: (loans) => set({ loans }),
  addLoan: (loan) => set((s) => ({ loans: [loan, ...s.loans] })),
  selectedLoanId: null,
  setSelectedLoanId: (id) => set({ selectedLoanId: id }),
}));
