import {initializeApp,getApps} from "firebase/app";
import {getAuth,GoogleAuthProvider,signInWithPopup,signOut,onAuthStateChanged,User} from "firebase/auth";

const firebaseConfig={
 apiKey:import.meta.env.VITE_FIREBASE_API_KEY,
 authDomain:import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
 projectId:import.meta.env.VITE_FIREBASE_PROJECT_ID,
 appId:import.meta.env.VITE_FIREBASE_APP_ID
};
const configured=Boolean(firebaseConfig.apiKey&&firebaseConfig.authDomain&&firebaseConfig.projectId);
const app=configured?(getApps()[0]||initializeApp(firebaseConfig)):null;
export const auth=app?getAuth(app):null;
export const provider=app?new GoogleAuthProvider():null;

export async function loginGoogle(){
 if(!auth||!provider)throw new Error("Firebase web configuration is missing");
 return signInWithPopup(auth,provider);
}
export async function logout(){if(auth)await signOut(auth)}
export async function idToken(){return auth?.currentUser?auth.currentUser.getIdToken():null}
export function watchAuth(cb:(user:User|null)=>void){return auth?onAuthStateChanged(auth,cb):()=>{}}
export {configured};
