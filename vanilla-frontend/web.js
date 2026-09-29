// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyA9OsRfONtzFN5eMcuzVOLsdYbUscykczg",
  authDomain: "ai-career-coach-da37b.firebaseapp.com",
  projectId: "ai-career-coach-da37b",
  storageBucket: "ai-career-coach-da37b.firebasestorage.app",
  messagingSenderId: "22864386471",
  appId: "1:22864386471:web:3538e30a4a9c9588603e82",
  measurementId: "G-YTR8ET32L4"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);