<script setup>
import { pieces, versionFields, runFields } from '@/services/combined'
defineProps({ spec: {type: Object, required: true}, reports: Object, editable: Boolean })
const versions = [
  {label: '學用', paper: 'student_paper', pieces: ['student']},
  {label: '教用', paper: 'teacher_paper', pieces: ['teacher','answer']},
]
</script>
<template>
<section v-for="v in versions" :key="v.paper" class="version-card">
  <h3>{{v.label}}版</h3>
  <div v-if="editable" class="field-grid">
    <label v-for="(label,key) in versionFields" :key="key">{{label}}
      <input v-model="spec[v.paper][key]" maxlength="200">
    </label>
  </div>
  <p v-else>{{spec[v.paper].quantity || '來單數量未填'}} · {{spec[v.paper].paper || '紙質未填'}} · {{spec[v.paper].reams || '—'}} 令</p>
  <section v-for="piece in v.pieces" :key="piece" class="piece">
    <h4>{{pieces[piece]}} <strong v-if="!editable" :class="{pending:reports?.[piece] == null}">{{reports?.[piece] == null ? '待回報' : '已回報 ' + reports[piece]}}</strong></h4>
    <details class="paper-fold" :open="editable">
      <summary>{{pieces[piece]}}印刷明細</summary>
      <label v-if="editable">台數、顏色與特別指示<input v-model="spec[piece].instruction" maxlength="200"></label>
      <p v-else>{{spec[piece].instruction || '未填特別指示'}}</p>
      <div v-for="(row,i) in spec[piece].runs" :key="i" class="run">
        <b>第 {{i+1}} 列</b>
        <div class="field-grid">
          <template v-for="(label,key) in runFields" :key="key">
            <label v-if="editable">{{label}}<input v-model="row[key]" maxlength="200"></label>
            <span v-else-if="row[key]">{{label}}　{{row[key]}}</span>
          </template>
        </div>
        <button v-if="editable" type="button" @click="spec[piece].runs.splice(i,1)">移除此列</button>
      </div>
      <button v-if="editable && spec[piece].runs.length < 100" type="button" @click="spec[piece].runs.push({})">＋ 新增印刷明細列</button>
    </details>
    <slot :piece="piece" :label="pieces[piece]" />
  </section>
</section>
</template>
<style scoped>
.version-card{padding:1rem;background:#faf8f0;border:1px solid #989f94;margin:1rem 0;overflow-wrap:anywhere}
.version-card h3{font-size:1.4rem;font-weight:750}.piece{margin-top:1rem;padding-top:.75rem;border-top:2px solid #808779}
.piece h4{display:flex;align-items:center;flex-wrap:wrap;gap:.6rem;font-weight:700;font-size:1.2rem}
.piece strong{padding:.15rem .6rem;background:#dce9df;font-size:1rem}.piece .pending{background:#f5e2b5;color:#5a3908}
.field-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,10rem),1fr));gap:.65rem}
.version-card input{display:block;width:100%;border:1px solid #737e72;padding:.5rem}.run{margin:.75rem 0;padding:.6rem;border:1px solid #b0b6ab}
.version-card button{min-height:48px;text-decoration:underline}
</style>
