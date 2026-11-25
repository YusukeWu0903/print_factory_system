<script setup>
import { computed } from 'vue'
const props = defineProps({ notes: String })
// Only tabulate explicitly labelled lines that match all four units.
const blocks = computed(() => (props.notes || '').split(/\r?\n|(?<=。)/u).map(s=>s.trim()).filter(Boolean).map(text=>{
  const match=text.match(/^澤福印刷明細（色數／台數／實數／放損）：(.+)。$/u)
  if(match){
    const rows=match[1].split('；').map(line=>line.match(/^(.+?)\s+(正\d+反\d+)／([\d.]+台)／([\d,]+車)／([\d,]+車)(?:，(.+))?$/u))
    if(rows.every(Boolean)) return { rows:rows.map(row=>row.slice(1)) }
  }
  return {text}
}))
</script>
<template>
<div class="order-notes">
<h4>作業明細與備註</h4>
<template v-for="(block,i) in blocks" :key="i">
<table v-if="block.rows" class="runs">
<caption>澤福印刷明細</caption>
<thead><tr><th v-for="label in ['項目','色數','台數','實數','放損','說明']" :key="label" scope="col">{{label}}</th></tr></thead>
<tbody><tr v-for="(row,j) in block.rows" :key="j"><td v-for="(value,k) in row" :key="k">{{value || '—'}}</td></tr></tbody>
</table>
<p v-else>{{block.text}}</p>
</template>
</div>
</template>
