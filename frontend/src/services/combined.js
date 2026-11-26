export const pieces = { student: '學用', teacher: '教用正文', answer: '解答' }
export const versionFields = { quantity: '來單數量', paper: '紙張尺寸與紙質', reams: '紙張用料合計（令）' }
export const runFields = { colors: '色數', presses: '台數', demand: '實際需求', waste: '放損', reams: '令數', note: '備註' }
export function emptyCombined() {
  const paper = () => ({ quantity: '', paper: '', reams: '' })
  const piece = () => ({ instruction: '', runs: [] })
  return { student_paper: paper(), teacher_paper: paper(), student: piece(), teacher: piece(), answer: piece() }
}
