/**
 * AgriCrop – Firebase Client Configuration
 * Initialize Firebase SDK for the frontend.
 * Replace the config object values with your actual Firebase project credentials.
 */

// Import Firebase modules from CDN (used via script type="module" or importmap)
// For non-module HTML pages, Firebase is loaded via compat CDN scripts.

const firebaseConfig = {
  apiKey:            window.ENV?.FIREBASE_API_KEY            || "YOUR_API_KEY",
  authDomain:        window.ENV?.FIREBASE_AUTH_DOMAIN        || "your-project.firebaseapp.com",
  projectId:         window.ENV?.FIREBASE_PROJECT_ID         || "your-project-id",
  storageBucket:     window.ENV?.FIREBASE_STORAGE_BUCKET     || "your-project.appspot.com",
  messagingSenderId: window.ENV?.FIREBASE_MESSAGING_SENDER_ID|| "YOUR_SENDER_ID",
  appId:             window.ENV?.FIREBASE_APP_ID             || "YOUR_APP_ID",
  measurementId:     window.ENV?.FIREBASE_MEASUREMENT_ID     || "G-XXXXXXXXXX",
};

const isMock = !firebaseConfig.apiKey || firebaseConfig.apiKey.startsWith("YOUR_") || firebaseConfig.apiKey.includes("your-");

let firebaseAuth;
let firebaseStorage;

if (isMock) {
  console.warn("⚠️ Firebase is NOT configured. Enabling local mock fallback auth mode.");

  class MockUser {
    constructor(email, displayName = "", role = "farmer") {
      this.uid = "mock-uid-" + btoa(email).replace(/=/g, "").slice(0, 10);
      this.email = email;
      this.displayName = displayName || email.split("@")[0];
      this.emailVerified = true;
      this.role = role;
    }
    async getIdToken() {
      return "mock-token-" + this.email;
    }
    async updateProfile(profile) {
      if (profile.displayName) this.displayName = profile.displayName;
    }
    async sendEmailVerification() {
      console.log("Mock verification email sent to:", this.email);
    }
  }

  class MockAuth {
    constructor() {
      this.currentUser = null;
      this.callbacks = [];
      const stored = sessionStorage.getItem("ag_mock_fb_user");
      if (stored) {
        try {
          const u = JSON.parse(stored);
          this.currentUser = new MockUser(u.email, u.displayName, u.role);
          this.currentUser.uid = u.uid;
        } catch (e) {
          this.currentUser = null;
        }
      }
    }
    setPersistence(p) { return Promise.resolve(); }
    onAuthStateChanged(callback) {
      this.callbacks.push(callback);
      callback(this.currentUser);
      return () => { this.callbacks = this.callbacks.filter(c => c !== callback); };
    }
    _trigger() {
      if (this.currentUser) {
        sessionStorage.setItem("ag_mock_fb_user", JSON.stringify({
          uid: this.currentUser.uid,
          email: this.currentUser.email,
          displayName: this.currentUser.displayName,
          role: this.currentUser.role
        }));
      } else {
        sessionStorage.removeItem("ag_mock_fb_user");
      }
      setTimeout(() => {
        this.callbacks.forEach(c => c(this.currentUser));
      }, 100);
    }
    async createUserWithEmailAndPassword(email, password) {
      const role = email.includes("admin") ? "admin" : "farmer";
      this.currentUser = new MockUser(email, "", role);
      this._trigger();
      return { user: this.currentUser };
    }
    async signInWithEmailAndPassword(email, password) {
      const role = email.includes("admin") ? "admin" : "farmer";
      this.currentUser = new MockUser(email, "", role);
      this._trigger();
      return { user: this.currentUser };
    }
    async signOut() {
      this.currentUser = null;
      this._trigger();
      return Promise.resolve();
    }
    async sendPasswordResetEmail(email) {
      console.log("Mock password reset email sent to:", email);
      return Promise.resolve();
    }
  }

  const mockAuthInstance = new MockAuth();
  firebase.auth = () => mockAuthInstance;
  firebase.auth.Auth = { Persistence: { LOCAL: "local", SESSION: "session", NONE: "none" } };
  firebase.auth.EmailAuthProvider = {
    credential: (email, password) => ({ email, password })
  };

  firebaseAuth = mockAuthInstance;

  // Mock Storage
  class MockStorage {
    ref() {
      return {
        put: async (file) => ({ ref: { getDownloadURL: async () => "http://localhost:8000/static/uploads/" + file.name } })
      };
    }
  }
  const mockStorageInstance = new MockStorage();
  firebase.storage = () => mockStorageInstance;
  firebaseStorage = mockStorageInstance;

} else {
  // Initialize Real Firebase SDK
  if (!firebase.apps.length) {
    firebase.initializeApp(firebaseConfig);
  }
  firebaseAuth = firebase.auth();
  firebaseStorage = firebase.storage();
  firebaseAuth.setPersistence(firebase.auth.Auth.Persistence.LOCAL);
}

// ── Auth state change broadcaster ───────────────────────────────────────
firebaseAuth.onAuthStateChanged((user) => {
  window.dispatchEvent(new CustomEvent("ag:authStateChanged", { detail: { user } }));
});

// ── Export for use by other modules ─────────────────────────────────────
window.AgriCropFirebase = {
  auth:    firebaseAuth,
  storage: firebaseStorage,
  config:  firebaseConfig,
};
