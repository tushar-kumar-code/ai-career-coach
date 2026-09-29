// 1. Firebase Core & Auth Modules import karein
import { initializeApp, getApps, getApp } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";

// 2. Aapke Firebase Console ki Configuration
const firebaseConfig = {
  apiKey: "AIzaSyA9OsRfONtzFN5eMcuzVOLsdYbUscykczg",
  authDomain: "ai-career-coach-da37b.firebaseapp.com",
  projectId: "ai-career-coach-da37b",
  storageBucket: "ai-career-coach-da37b.firebasestorage.app",
  messagingSenderId: "22864386471",
  appId: "1:22864386471:web:3538e30a4a9c9588603e82",
  measurementId: "G-YTR8ET32L4"
};

// 3. Singleton App Initialize karein (baar-baar re-initialize hone se bachane ke liye)
const app = getApps().length > 0 ? getApp() : initializeApp(firebaseConfig);

// 4. Auth & Google Provider Initialize aur Export karein
export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();
googleProvider.setCustomParameters({ prompt: 'select_account' });

// 5. Export flag for AuthContext
export const isFirebaseConfigured: boolean = true;

export { app };
export default app;
