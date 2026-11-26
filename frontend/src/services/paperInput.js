export function splitPaperInput(value) {
  const text = (value || '').normalize('NFKC').trim()
  const match = text.match(/^(?:(\d+(?:\.\d+)?)\s*令)?\s*(?:\+\s*)?(?:(\d+)\s*張)?$/u)
  if (match && (match[1] || match[2])) return [match[1] || '', match[2] || '']
  if (/^\d+(?:\.\d+)?$/.test(text)) return [text, '']
  return ['', '']
}

export function formatPaperInput(reams, sheets) {
  return [reams === '' ? '' : reams + ' 令', sheets === '' ? '' : sheets + ' 張'].filter(Boolean).join('＋')
}
