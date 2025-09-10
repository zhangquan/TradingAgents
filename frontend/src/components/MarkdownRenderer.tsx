'use client'

import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'
import 'highlight.js/styles/github.css'

interface MarkdownRendererProps {
  content: string
  className?: string
}

export function MarkdownRenderer({ content, className = '' }: MarkdownRendererProps) {
  return (
    <div className={`prose prose-gray max-w-none dark:prose-invert ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={{
          // Custom styling for headers
          h1: ({ children }) => (
            <h1 className="text-2xl font-bold text-gray-900 mb-4 pb-2 border-b border-gray-200">
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-xl font-semibold text-gray-800 mb-3 mt-6">
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="text-lg font-medium text-gray-700 mb-2 mt-4">
              {children}
            </h3>
          ),
          // Custom styling for paragraphs
          p: ({ children }) => (
            <p className="text-gray-600 leading-relaxed mb-4">
              {children}
            </p>
          ),
          // Custom styling for lists
          ul: ({ children }) => (
            <ul className="space-y-2 mb-4 ml-4">
              {children}
            </ul>
          ),
          ol: ({ children }) => (
            <ol className="space-y-2 mb-4 ml-4">
              {children}
            </ol>
          ),
          li: ({ children }) => (
            <li className="text-gray-600">
              {children}
            </li>
          ),
          // Custom styling for code blocks
          code: ({ className, children, ...props }) => {
            const match = /language-(\w+)/.exec(className || '')
            if (match) {
              return (
                <code className={`${className} text-sm`} {...props}>
                  {children}
                </code>
              )
            }
            return (
              <code className="bg-gray-100 text-red-600 px-1 py-0.5 rounded text-sm font-mono" {...props}>
                {children}
              </code>
            )
          },
          // Custom styling for blockquotes
          blockquote: ({ children }) => (
            <blockquote className="border-l-4 border-blue-200 pl-4 py-2 bg-blue-50 text-gray-700 italic mb-4">
              {children}
            </blockquote>
          ),
          // Custom styling for tables
          table: ({ children }) => (
            <div className="overflow-x-auto mb-4">
              <table className="min-w-full border border-gray-200 rounded-lg">
                {children}
              </table>
            </div>
          ),
          thead: ({ children }) => (
            <thead className="bg-gray-50">
              {children}
            </thead>
          ),
          th: ({ children }) => (
            <th className="px-4 py-2 text-left text-gray-700 font-semibold border-b border-gray-200">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="px-4 py-2 text-gray-600 border-b border-gray-100">
              {children}
            </td>
          ),
          // Custom styling for links
          a: ({ children, href }) => (
            <a
              href={href}
              className="text-blue-600 hover:text-blue-800 underline"
              target="_blank"
              rel="noopener noreferrer"
            >
              {children}
            </a>
          ),
          // Custom styling for horizontal rules
          hr: () => (
            <hr className="my-6 border-gray-200" />
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}
