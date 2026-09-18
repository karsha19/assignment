export default function Badge({ value }) {
  if (!value) return null
  return <span className={`badge badge-${value.toLowerCase()}`}>{value}</span>
}
