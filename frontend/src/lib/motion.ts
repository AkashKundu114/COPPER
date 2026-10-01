/** Forge Design System — Motion Presets */

/** Stiff desktop spring for micro-interactions (card entrances, toggles) */
export const springEnter = {
  type: "spring" as const,
  stiffness: 400,
  damping: 30,
  mass: 0.8,
};

/** Snappy spring for modals and command palette */
export const springModal = {
  type: "spring" as const,
  stiffness: 350,
  damping: 28,
};

/** Smooth glide for active tab/nav indicator (use with layoutId) */
export const springTab = {
  type: "spring" as const,
  stiffness: 500,
  damping: 35,
};

/** Standard page transition variants */
export const pageTransition = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0 },
  exit:    { opacity: 0, y: -4 },
  transition: { duration: 0.15, ease: [0.16, 1, 0.3, 1] },
} as const;

/** Stagger container for card grids (use as parent motion.div) */
export const staggerContainer = {
  animate: { transition: { staggerChildren: 0.04 } },
} as const;

/** Individual stagger child item */
export const staggerItem = {
  initial: { opacity: 0, y: 6 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.12, ease: [0.16, 1, 0.3, 1] },
} as const;
