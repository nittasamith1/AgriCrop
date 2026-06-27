/**
 * AgriCrop – Firebase Client Configuration
 * Production credentials for agricrop-a8352 Firebase project.
 *
 * NOTE: Firebase client config keys are designed to be public.
 * They identify the Firebase project but do NOT grant admin access.
 * Security is enforced by Firestore rules and Storage rules.
 */

// ── Firebase Configuration ────────────────────────────────────────────────────
const firebaseConfig = {
  apiKey:            "AIzaSyAR128kYe3qWnpP9cg8_YXPq4xI3ax6vN4",
  authDomain:        "agricrop-a8352.firebaseapp.com",
  projectId:         "agricrop-a8352",
  storageBucket:     "agricrop-a8352.firebasestorage.app",
  messagingSenderId: "360768814490",
  appId:             "1:360768814490:web:5d4b2d32d42c32db964e23",
  measurementId:     "G-85R9GZ2JCL",
};

// ── Determine if real Firebase credentials are present ────────────────────────
const isMock = !firebaseConfig.apiKey
  || firebaseConfig.apiKey === "YOUR_API_KEY"
  || firebaseConfig.apiKey.startsWith("YOUR_");

let firebaseAuth;
let firebaseStorage;

if (isMock) {
  // ── Mock Fallback Mode (local dev without credentials) ─────────────────────
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
        put: async (file) => ({
          ref: { getDownloadURL: async () => window.API_BASE + "/static/uploads/" + file.name }
        })
      };
    }
  }
  const mockStorageInstance = new MockStorage();
  firebase.storage = () => mockStorageInstance;
  firebaseStorage = mockStorageInstance;

} else {
  // ── Initialize Real Firebase SDK ───────────────────────────────────────────
  try {
    if (!firebase.apps || !firebase.apps.length) {
      firebase.initializeApp(firebaseConfig);
    }
    firebaseAuth = firebase.auth();
    try {
      firebaseStorage = firebase.storage();
    } catch (e) {
      console.warn("Firebase Storage NOT loaded, maybe CDN script missing.");
    }

    // Persist auth session in localStorage (survives browser close)
    firebaseAuth.setPersistence(firebase.auth.Auth.Persistence.LOCAL).catch(e => {
      console.warn("Firebase persistence error:", e);
    });

    // Enable Firestore offline persistence if available
    if (firebase.firestore) {
      firebase.firestore().enablePersistence({ synchronizeTabs: true }).catch(e => {
        if (e.code !== "failed-precondition" && e.code !== "unimplemented") {
          console.warn("Firestore persistence error:", e);
        }
      });
    }

  } catch (initErr) {
    console.error("Firebase initialization failed:", initErr);
  }
}

// ── Auth state change broadcaster ─────────────────────────────────────────────
if (firebaseAuth) {
  firebaseAuth.onAuthStateChanged((user) => {
    window.dispatchEvent(new CustomEvent("ag:authStateChanged", { detail: { user } }));
  });
}

// ── Export for use by other modules ───────────────────────────────────────────
window.AgriCropFirebase = {
  auth:    firebaseAuth,
  storage: firebaseStorage,
  config:  firebaseConfig,
  isMock:  isMock,
};
