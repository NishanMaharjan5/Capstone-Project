const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID

let scriptPromise = null

function loadGoogleScript() {
  if (scriptPromise) return scriptPromise

  scriptPromise = new Promise((resolve, reject) => {
    if (window.google?.accounts?.id) {
      resolve()
      return
    }

    const script = document.createElement('script')
    script.src = 'https://accounts.google.com/gsi/client'
    script.async = true
    script.defer = true
    script.onload = () => resolve()
    script.onerror = () => reject(new Error('Failed to load Google Identity script'))
    document.head.appendChild(script)
  })

  return scriptPromise
}

export function useGoogleIdentity() {
  async function promptGoogle(onCredential) {
    await loadGoogleScript()

    window.google.accounts.id.initialize({
      client_id: GOOGLE_CLIENT_ID,
      callback: (response) => onCredential(response.credential),
    })
    window.google.accounts.id.prompt()
  }

  return { promptGoogle }
}
