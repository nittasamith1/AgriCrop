# Firebase Setup Guide for AgriCrop

This guide explains how to set up Firebase for the AgriCrop project. AgriCrop uses both the **Firebase Web SDK** (frontend client authentication) and the **Firebase Admin SDK** (backend database, storage, and token validation).

---

## 1. Create a Firebase Project
1. Go to the [Firebase Console](https://console.firebase.google.com/).
2. Click **Add Project** (or **Create a Project**).
3. Name your project (e.g., `agricrop-intelligence`).
4. Choose whether to enable Google Analytics (recommended but optional).
5. Click **Create Project** and wait for it to provision.

---

## 2. Enable Email/Password Authentication
1. In the left-hand navigation sidebar, click on **Build** → **Authentication**.
2. Click **Get Started**.
3. Under the **Sign-in method** tab, select **Email/Password**.
4. Toggle the **Email/Password** status to **Enabled** (do not enable the passwordless option unless desired).
5. Click **Save**.

---

## 3. Create Firestore Database
1. In the left-hand navigation sidebar, click on **Build** → **Firestore Database**.
2. Click **Create Database**.
3. Set your **Database ID** (default is `(default)`).
4. Choose a location close to your users (e.g., `asia-south1` or `us-central1`).
5. Choose **Start in production mode** or **Start in test mode** (production is recommended; we will define security rules below).
6. Click **Create**.

---

## 4. Enable Firebase Storage
1. In the left sidebar, click on **Build** → **Storage**.
2. Click **Get Started**.
3. Choose **Start in production mode**.
4. Select the location (this should match your Firestore database location).
5. Click **Done**.

---

## 5. Generate a Firebase Web App
1. Go to your **Project Overview** page (click the gear icon ⚙ next to "Project Overview" and choose **Project settings**).
2. Under the **General** tab, scroll down to the **Your apps** section.
3. Click the Web icon (represented by `</>`).
4. Register your app with a nickname (e.g., `AgriCrop Frontend`).
5. Check or uncheck Firebase Hosting (optional). Click **Register app**.
6. You will see a `firebaseConfig` object containing:
   - `apiKey`
   - `authDomain`
   - `projectId`
   - `storageBucket`
   - `messagingSenderId`
   - `appId`
   - `measurementId`
7. Keep these values handy; you will copy them into the `.env` file.

---

## 6. Download the Firebase Admin SDK Service Account JSON
1. Under **Project settings** (gear icon ⚙), navigate to the **Service accounts** tab.
2. Select the **Firebase Admin SDK** option (default Node.js/Python credentials).
3. Click the button at the bottom labeled **Generate new private key**.
4. Confirm by clicking **Generate key**.
5. A `.json` file containing your credentials will automatically download.

---

## 7. Place the JSON File in the Project
1. Rename the downloaded `.json` file to `serviceAccountKey.json`.
2. Move this file into the root folder of your local `AgriCrop` project workspace.
   - Path: `c:\Users\NITTA SAMITH\Downloads\SKILLS Notes and Projects\Projects\AgriCrop\serviceAccountKey.json`
3. ⚠️ **WARNING**: Never commit this file to your Git repository! It is already added to `.gitignore`.

---

## 8. Update the `.env` File
Open the `.env` file in the project root and fill in the values you copied in Steps 5 & 6:

```ini
# ----- Firebase Admin SDK (Backend) -----
FIREBASE_PROJECT_ID=your-project-id-from-step-5
FIREBASE_PRIVATE_KEY_ID=your-private-key-id-from-serviceAccountKey.json
# Enter the private key here with newlines represented as \n
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nYOUR_KEY_HERE\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@your-project-id.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=your-client-id-from-serviceAccountKey.json
FIREBASE_AUTH_URI=https://accounts.google.com/o/oauth2/auth
FIREBASE_TOKEN_URI=https://oauth2.googleapis.com/token
FIREBASE_SERVICE_ACCOUNT_PATH=./serviceAccountKey.json

# ----- Firebase Client (Frontend) -----
FIREBASE_API_KEY=your-api-key-from-step-5
FIREBASE_AUTH_DOMAIN=your-project-id.firebaseapp.com
FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com
FIREBASE_MESSAGING_SENDER_ID=your-messaging-sender-id-from-step-5
FIREBASE_APP_ID=your-app-id-from-step-5
FIREBASE_MEASUREMENT_ID=G-XXXXXXXXXX

# ----- Firebase Storage -----
FIREBASE_STORAGE_URL=gs://your-project-id.appspot.com
```

---

## 9. Required Firebase Security Rules

### Firestore Security Rules
Go to **Firestore Database** → **Rules** tab, paste the following rules, and click **Publish**:

```javascript
rules_version = '2';

service cloud.firestore {
  match /databases/{database}/documents {
    // Helper to check if user is logged in
    function isLoggedIn() {
      return request.auth != null;
    }

    // Helper to check if request is from the document owner
    function isOwner(userId) {
      return isLoggedIn() && request.auth.uid == userId;
    }

    // Users Collection
    match /users/{userId} {
      allow read, write: if isOwner(userId) || (isLoggedIn() && resource.data.role == 'admin');
    }

    // Farms Collection
    match /farms/{farmId} {
      allow read, write: if isLoggedIn();
    }

    // Disease Predictions Collection
    match /disease_predictions/{predId} {
      allow read, write: if isLoggedIn();
    }

    // Soil Predictions Collection
    match /soil_predictions/{predId} {
      allow read, write: if isLoggedIn();
    }

    // Notifications Collection
    match /notifications/{notifId} {
      allow read, write: if isLoggedIn() && (resource.data.user_id == request.auth.uid);
    }

    // Reports Collection
    match /reports/{reportId} {
      allow read, write: if isLoggedIn();
    }

    // Default rule
    match /{document=**} {
      allow read, write: if isLoggedIn() && request.auth.token.role == 'admin';
    }
  }
}
```

### Storage Security Rules
Go to **Storage** → **Rules** tab, paste the following rules, and click **Publish**:

```javascript
rules_version = '2';

service firebase.storage {
  match /b/{bucket}/o {
    // Helper
    function isLoggedIn() {
      return request.auth != null;
    }

    // Allow read access to uploaded images & reports for authorized users
    match /leaf_images/{userId}/{allPaths=**} {
      allow read, write: if isLoggedIn() && request.auth.uid == userId;
    }

    match /reports/{userId}/{allPaths=**} {
      allow read, write: if isLoggedIn() && request.auth.uid == userId;
    }

    match /profile_pictures/{userId}/{allPaths=**} {
      allow read, write: if isLoggedIn();
    }
  }
}
```

---

## 10. How to Verify the Firebase Connection
1. Launch the backend:
   ```bash
   python -m uvicorn backend.main:app --reload
   ```
2. Check the console log. If everything is configured correctly, you will see:
   `✅ Firebase Admin SDK initialized successfully`
   instead of the mock mode warnings.
3. Launch the frontend, open `login.html`, and try to register a new user. Inspect the Firestore Console under the `users` collection to verify that the profile record is written successfully.
