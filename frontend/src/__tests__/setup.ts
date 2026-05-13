import '@testing-library/jest-dom'
import { vi } from 'vitest'

vi.mock('@testing-library/react', async () => {
  const actual =
    await vi.importActual<typeof import('@testing-library/react')>('@testing-library/react')
  const React = await vi.importActual<typeof import('react')>('react')
  const { QueryClient, QueryClientProvider } =
    await vi.importActual<typeof import('@tanstack/react-query')>('@tanstack/react-query')
  const { ToastProvider } =
    await vi.importActual<typeof import('../components/toast')>('../components/toast')

  type RenderArgs = Parameters<typeof actual.render>
  const render: typeof actual.render = (ui, options) => {
    const client = new QueryClient({
      defaultOptions: {
        queries: { retry: false, gcTime: 0, staleTime: 0, refetchOnWindowFocus: false },
        mutations: { retry: false },
      },
    })
    const ExistingWrapper = options?.wrapper
    const Wrapper = ({ children }: { children: React.ReactNode }) => {
      const inner = ExistingWrapper
        ? React.createElement(ExistingWrapper, null, children)
        : (children as React.ReactElement)
      return React.createElement(
        QueryClientProvider,
        { client },
        React.createElement(ToastProvider, null, inner),
      )
    }
    return actual.render(ui, { ...options, wrapper: Wrapper } as RenderArgs[1])
  }

  return { ...actual, render }
})
