import { create } from 'zustand'

export const useRouteStore = create((set) => ({
  origin: "",
  destination: "",
  departureTime: "",
  isSubmitting: false,
  segments: [],
  tripRisk: null,
  confines: null,
  duration: null,

  setIsSubmitting: (send) => set({ isSubmitting: send }),
  setOrigin: (origin) => set({ origin }),
  setDestination: (destination) => set({ destination }),
  setDepartureTime: (time) => set({ departureTime: time }),
  setSegments: (segments) => set({ segments }),
  setTripRisk: (tripRisk) => set({ tripRisk }),
  setConfines: (confines) => set({ confines }),
  setDuration: (duration) => set({ duration }),

  reset: () =>
    set({
      origin: "",
      destination: "",
      departureTime: "",
      isSubmitting: false,
      segments: [],
      tripRisk: null,
      confines: null,
      duration: null,
    }),
}))

