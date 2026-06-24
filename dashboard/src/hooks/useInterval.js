import { useEffect, useRef } from "react";

/*
 * Hook generique pour repeter une fonction toutes les `delay` ms.
 *
 * Pourquoi pas juste setInterval(callback, delay) directement dans le composant ?
 * Parce que `callback` est recree a chaque rendu (nouvelle fonction = nouvelle
 * reference), et setInterval ne doit pas pour autant etre relance a chaque
 * rendu (sinon le polling ne serait jamais stable). On stocke donc la derniere
 * version de `callback` dans une ref, et un seul setInterval (relance
 * uniquement si `delay` change) va lire cette ref a chaque tick.
 *
 * useEffect avec cleanup : le `return () => clearInterval(id)` est essentiel
 * pour ne pas laisser tourner un setInterval apres que le composant a
 * disparu (sinon : fuite memoire + appels a un composant demonte).
 */
export function useInterval(callback, delay) {
  const callbackRef = useRef(callback);

  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  useEffect(() => {
    if (delay === null) return;

    const id = setInterval(() => callbackRef.current(), delay);
    return () => clearInterval(id);
  }, [delay]);
}
