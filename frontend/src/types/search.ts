export interface SearchValue {
  tags: string[]
  text: string
}

export interface SearchResult {
  type: string
  id: number
  title: string
  subtitle?: string
  snippet?: string
  tags: string[]
  url: string
}
