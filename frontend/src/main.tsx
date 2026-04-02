import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { ClerkProvider } from '@clerk/clerk-react'
import './index.css'
import App from './App.tsx'

const publishableKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY

if (!publishableKey) {
  throw new Error('VITE_CLERK_PUBLISHABLE_KEY is not set')
}

const clerkAppearance = {
  variables: {
    colorBackground: '#1a1a1a',
    colorForeground: '#e0e0e0',
    colorPrimary: '#52b788',
    colorNeutral: '#888888',
    colorDanger: '#ff4444',
    colorText: '#e0e0e0',
    colorTextSecondary: '#888888',
    colorInputBackground: '#141414',
    colorInputText: '#e0e0e0',
    fontFamily: "'JetBrains Mono', 'Fira Code', 'SF Mono', 'Cascadia Code', ui-monospace, monospace",
    borderRadius: '0px',
    colorShadow: 'transparent',
  },
  elements: {
    // Modal backdrop
    modalBackdrop: {
      backgroundColor: 'rgba(0, 0, 0, 0.7)',
      backdropFilter: 'blur(4px)',
    },
    // Cards / modal containers
    card: {
      backgroundColor: '#1a1a1a',
      boxShadow: 'none',
      border: '1px solid #2a2a2a',
    },
    cardBox: {
      boxShadow: 'none',
    },
    // Navigation sidebar (account modal)
    navbar: {
      backgroundColor: '#141414',
      borderRight: '1px solid #2a2a2a',
    },
    navbarButton: {
      color: '#888888',
    },
    navbarButton__active: {
      color: '#52b788',
      backgroundColor: 'rgba(82, 183, 136, 0.07)',
    },
    // Page content
    pageScrollBox: {
      backgroundColor: '#1a1a1a',
    },
    profileSection: {
      backgroundColor: '#1a1a1a',
      borderTop: '1px solid #2a2a2a',
    },
    profileSectionContent: {
      backgroundColor: '#1a1a1a',
    },
    // Headers
    headerTitle: {
      color: '#e0e0e0',
    },
    headerSubtitle: {
      color: '#888888',
    },
    // Form fields
    formFieldLabel: {
      color: '#888888',
    },
    formFieldInput: {
      backgroundColor: '#141414',
      border: '1px solid #2a2a2a',
      color: '#e0e0e0',
      boxShadow: 'none',
    },
    formFieldInputShowPasswordButton: {
      color: '#555555',
    },
    // Buttons
    formButtonPrimary: {
      backgroundColor: '#52b788',
      color: '#1a1a1a',
      boxShadow: 'none',
    },
    formButtonReset: {
      color: '#888888',
    },
    // Social sign-in buttons
    socialButtonsBlockButton: {
      backgroundColor: '#141414',
      border: '1px solid #2a2a2a',
      color: '#e0e0e0',
      boxShadow: 'none',
    },
    socialButtonsBlockButtonText: {
      color: '#e0e0e0',
    },
    // Divider
    dividerLine: {
      backgroundColor: '#2a2a2a',
    },
    dividerText: {
      color: '#555555',
    },
    // Identity / avatar
    identityPreviewText: {
      color: '#e0e0e0',
    },
    identityPreviewEditButton: {
      color: '#52b788',
    },
    avatarBox: {
      boxShadow: 'none',
    },
    // Badges / tags
    badge: {
      backgroundColor: 'rgba(82, 183, 136, 0.07)',
      color: '#52b788',
      border: '1px solid #40916c',
    },
    // Footer
    footer: {
      backgroundColor: '#1a1a1a',
      borderTop: '1px solid #2a2a2a',
    },
    footerActionLink: {
      color: '#52b788',
    },
    // Alert
    alertText: {
      color: '#888888',
    },
  },
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ClerkProvider
      publishableKey={publishableKey}
      signInFallbackRedirectUrl={window.location.pathname + window.location.search}
      appearance={clerkAppearance}
    >
      <App />
    </ClerkProvider>
  </StrictMode>,
)
