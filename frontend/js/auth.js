/**
 * AgriCrop – Frontend Authentication Module
 * Handles login, register, logout, password reset,
 * route protection, and user session management.
 */

const Auth = (() => {
  const auth = () => window.AgriCropFirebase?.auth || firebase.auth();
  const API = () => window.AgriCropAPI;

  // ── Session Storage Keys ────────────────────────────────────────────────
  const TOKEN_KEY   = "ag_token";
  const USER_KEY    = "ag_user";
  const ROLE_KEY    = "ag_role";

  // ── Store Session ───────────────────────────────────────────────────────
  function setSession(token, user) {
    sessionStorage.setItem(TOKEN_KEY, token);
    sessionStorage.setItem(USER_KEY, JSON.stringify(user));
    sessionStorage.setItem(ROLE_KEY, user.role || "farmer");
  }

  function clearSession() {
    sessionStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(USER_KEY);
    sessionStorage.removeItem(ROLE_KEY);
  }

  // ── Getters ─────────────────────────────────────────────────────────────
  function getToken()    { return sessionStorage.getItem(TOKEN_KEY); }
  function getUser()     { const u = sessionStorage.getItem(USER_KEY); try { return u ? JSON.parse(u) : null; } catch { return null; } }
  function getRole()     { return sessionStorage.getItem(ROLE_KEY) || "farmer"; }
  function isLoggedIn()  { return !!getToken(); }
  function isAdmin()     { return getRole() === "admin"; }

  // ── Get Fresh ID Token ──────────────────────────────────────────────────
  async function getFreshToken() {
    const fbUser = auth().currentUser;
    if (!fbUser) return null;
    try {
      const token = await fbUser.getIdToken(/* forceRefresh */ true);
      sessionStorage.setItem(TOKEN_KEY, token);
      return token;
    } catch (e) {
      console.error("Token refresh failed:", e);
      return null;
    }
  }

  // ── Register ────────────────────────────────────────────────────────────
  async function register(name, email, password, role = "farmer", phone = null) {
    try {
      // Create Firebase user
      const cred = await auth().createUserWithEmailAndPassword(email, password);
      const fbUser = cred.user;

      // Update display name
      await fbUser.updateProfile({ displayName: name });

      // Send email verification
      await fbUser.sendEmailVerification();

      // Save to backend (Firestore via FastAPI)
      const token = await fbUser.getIdToken();
      const res = await fetch(`${window.API_BASE}/api/v1/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify({ email, password, name, role, phone }),
      });

      let userProfile = { uid: fbUser.uid, email, name, role };
      if (res.ok) {
        // Fetch full profile to be sure
        const profileRes = await fetch(`${window.API_BASE}/api/v1/auth/me`, {
          headers: { "Authorization": `Bearer ${token}` },
        });
        if (profileRes.ok) userProfile = await profileRes.json();
      }

      setSession(token, userProfile);
      return { success: true, message: "Account created! Please verify your email." };
    } catch (err) {
      return { success: false, message: mapFirebaseError(err) };
    }
  }

  // ── Login ───────────────────────────────────────────────────────────────
  async function login(email, password) {
    try {
      const cred = await auth().signInWithEmailAndPassword(email, password);
      const fbUser = cred.user;
      const token = await fbUser.getIdToken();

      // Store token immediately so subsequent requests have it
      sessionStorage.setItem(TOKEN_KEY, token);

      // Fetch full profile from backend
      const res = await fetch(`${window.API_BASE}/api/v1/auth/me`, {
        headers: { "Authorization": `Bearer ${token}` },
      });

      let userProfile = { uid: fbUser.uid, email, name: fbUser.displayName, role: "farmer" };
      if (res.ok) {
        userProfile = await res.json();
      }

      setSession(token, userProfile);
      return { success: true, user: userProfile };
    } catch (err) {
      return { success: false, message: mapFirebaseError(err) };
    }
  }

  // ── Logout ──────────────────────────────────────────────────────────────
  async function logout() {
    try {
      await auth().signOut();
      clearSession();
      window.location.href = "/login.html";
    } catch (e) {
      console.error("Logout error:", e);
    }
  }

  // ── Forgot Password ─────────────────────────────────────────────────────
  async function forgotPassword(email) {
    try {
      await auth().sendPasswordResetEmail(email);
      return { success: true, message: "Password reset email sent. Check your inbox." };
    } catch (err) {
      return { success: false, message: mapFirebaseError(err) };
    }
  }

  // ── Route Protection ────────────────────────────────────────────────────
  function requireAuth() {
    auth().onAuthStateChanged(async (fbUser) => {
      if (!fbUser) {
        window.location.href = "/login.html";
        return;
      }
      // Refresh token on every protected page load
      const token = await fbUser.getIdToken();
      const existingUser = getUser();
      if (existingUser) {
        setSession(token, existingUser);
      } else {
        // Re-fetch profile
        const res = await fetch(`${window.API_BASE}/api/v1/auth/me`, {
          headers: { "Authorization": `Bearer ${token}` },
        });
        if (res.ok) {
          const profile = await res.json();
          setSession(token, profile);
        }
      }
      // Update navbar with user info
      updateNavbarUser();
    });
  }

  function requireAdmin() {
    auth().onAuthStateChanged(async (fbUser) => {
      if (!fbUser) {
        window.location.href = "/login.html";
        return;
      }
      
      // Ensure token is fresh to get latest custom claims if any
      const token = await fbUser.getIdToken();
      let role = getRole();
      
      // If no role in session or not admin, check backend
      if (role !== "admin") {
        try {
          const res = await fetch(`${window.API_BASE}/api/v1/auth/me`, {
            headers: { "Authorization": `Bearer ${token}` },
          });
          if (res.ok) {
            const profile = await res.json();
            setSession(token, profile);
            role = profile.role || "farmer";
          }
        } catch (e) {
          console.error("Failed to verify admin status", e);
        }
      }

      if (role !== "admin") {
        Utils.showToast("Access denied. Admin only.", "error");
        setTimeout(() => window.location.href = "/dashboard.html", 1500);
      } else {
        updateNavbarUser();
      }
    });
  }

  // ── Update Navbar ───────────────────────────────────────────────────────
  function updateNavbarUser() {
    const user = getUser();
    if (!user) return;
    const nameEl = document.getElementById("nav-user-name");
    const avatarEl = document.getElementById("nav-user-avatar");
    if (nameEl) nameEl.textContent = user.name || user.email;
    if (avatarEl) {
      if (user.profile_picture_url) {
        avatarEl.src = user.profile_picture_url;
      } else {
        avatarEl.textContent = (user.name || "U").charAt(0).toUpperCase();
      }
    }
  }

  // ── Firebase Error Mapper ────────────────────────────────────────────────
  function mapFirebaseError(err) {
    const codes = {
      "auth/email-already-in-use":     "This email is already registered.",
      "auth/invalid-email":            "Please enter a valid email address.",
      "auth/user-not-found":           "No account found with this email.",
      "auth/wrong-password":           "Incorrect password. Please try again.",
      "auth/too-many-requests":        "Too many attempts. Please try again later.",
      "auth/network-request-failed":   "Network error. Check your connection.",
      "auth/weak-password":            "Password must be at least 8 characters.",
      "auth/user-disabled":            "This account has been disabled.",
      "auth/popup-closed-by-user":     "Sign-in popup was closed.",
      "auth/expired-action-code":      "This link has expired. Please request a new one.",
    };
    return codes[err.code] || err.message || "An unexpected error occurred.";
  }

  // ── Listen for auth state and refresh token periodically ────────────────
  setInterval(async () => {
    await getFreshToken();
  }, 45 * 60 * 1000); // Every 45 minutes

  return {
    register, login, logout, forgotPassword,
    requireAuth, requireAdmin,
    getToken, getUser, getRole, isLoggedIn, isAdmin,
    getFreshToken, updateNavbarUser, clearSession,
  };
})();

window.Auth = Auth;
