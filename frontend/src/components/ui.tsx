import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode, SelectHTMLAttributes } from 'react'

export function Panel({ title, children }: { title?: string; children: ReactNode }) {
  return (
    <section className="rounded-lg border border-slate-800 bg-slate-900/60 p-5">
      {title && <h3 className="mb-3 text-base font-semibold text-slate-100">{title}</h3>}
      {children}
    </section>
  )
}

export function Button({
  variant = 'primary',
  className = '',
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'secondary' | 'danger' }) {
  const styles = {
    primary: 'bg-violet-600 hover:bg-violet-500 text-white disabled:bg-violet-900',
    secondary: 'bg-slate-800 hover:bg-slate-700 text-slate-100 disabled:bg-slate-900',
    danger: 'bg-red-900 hover:bg-red-800 text-red-100 disabled:bg-red-950',
  }[variant]
  return (
    <button
      type="button"
      className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:text-slate-500 ${styles} ${className}`}
      {...props}
    />
  )
}

export function TextInput(props: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      className={`rounded-md border border-slate-700 bg-slate-950 px-2 py-1 text-sm text-slate-100 placeholder:text-slate-500 focus:border-violet-500 focus:outline-none ${props.className ?? ''}`}
    />
  )
}

export function Select(props: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      {...props}
      className={`rounded-md border border-slate-700 bg-slate-950 px-2 py-1 text-sm text-slate-100 focus:border-violet-500 focus:outline-none ${props.className ?? ''}`}
    />
  )
}

export function ErrorText({ children }: { children: ReactNode }) {
  return <p className="rounded-md bg-red-950/60 px-3 py-2 text-sm text-red-300">{children}</p>
}

export function Badge({ tone = 'neutral', children }: { tone?: 'neutral' | 'positive'; children: ReactNode }) {
  const styles =
    tone === 'positive' ? 'bg-emerald-900 text-emerald-200' : 'bg-slate-800 text-slate-300'
  return <span className={`rounded px-2 py-0.5 text-xs font-medium ${styles}`}>{children}</span>
}
