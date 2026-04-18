import ReactMarkdown from 'react-markdown'
import styles from './MarkdownContent.module.css'

interface MarkdownContentProps {
  children: string
  className?: string
}

export function MarkdownContent({ children, className }: MarkdownContentProps) {
  return (
    <div className={`${styles.markdown} ${className ?? ''}`}>
      <ReactMarkdown>{children}</ReactMarkdown>
    </div>
  )
}
