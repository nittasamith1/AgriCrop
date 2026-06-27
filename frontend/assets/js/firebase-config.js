/**
 * AgriCrop – auth-config.js
 * Firebase has been fully removed.
 * Authentication is now handled via JWT tokens (see auth.js and api.js).
 * This file is intentionally left as a no-op stub for backward compatibility
 * with any page that still includes it via a <script> tag.
 */
console.info("ℹ️ AgriCrop: Firebase SDK removed. JWT auth is active.");

// Expose an empty stub so any stray firebase.auth() calls fail gracefully
window.firebase = window.firebase || {
  auth: () => ({
    onAuthStateChanged: () => {},
    currentUser: null,
  }),
  storage: () => ({}),
};
