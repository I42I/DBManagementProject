// supprime: null, undefined, "" (vides), objets/tabl. vides
export function scrub<T extends Record<string, any>>(obj: T): T {
  const out: any = Array.isArray(obj) ? [] : {}
  for (const [k, v] of Object.entries(obj)) {
    if (v === null || v === undefined) continue
    if (typeof v === 'string' && v.trim() === '') continue
    if (Array.isArray(v)) {
      const vv = scrub(v)
      if (vv.length === 0) continue
      out[k] = vv
      continue
    }
    if (typeof v === 'object' && !(v instanceof Date)) {
      const vv = scrub(v)
      if (Object.keys(vv).length === 0) continue
      out[k] = vv
      continue
    }
    out[k] = v
  }
  return out
}

