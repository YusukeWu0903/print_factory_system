import { authState, markLoggedOut } from './auth'
export async function staffRequest(path, method='GET', body) {
  const r=await fetch('/api/staff/'+path,{method,cache:'no-store',headers:{'Content-Type':'application/json','X-CSRF-Token':authState.csrfToken},body:body===undefined?undefined:JSON.stringify(body)})
  if(r.status===401)markLoggedOut()
  const value=await r.json()
  if(!r.ok)throw new Error(typeof value.detail==='string'?value.detail:'資料格式不正確')
  return value
}
