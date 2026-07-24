interface PlaceholderPageProps {
  title: string
  reason: string
}

/** An honest "not built yet" page — never fakes data or a working
 * feature for an advisor the backend doesn't have yet. See
 * frontend/README.md for what's implemented versus planned. */
export function PlaceholderPage({ title, reason }: PlaceholderPageProps) {
  return (
    <div className="rounded-lg border border-dashed border-slate-700 bg-slate-900/40 p-8 text-center">
      <h2 className="text-xl font-semibold text-slate-100">{title}</h2>
      <p className="mt-2 text-slate-400">{reason}</p>
    </div>
  )
}
