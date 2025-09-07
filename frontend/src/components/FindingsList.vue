<template>
  <div class="findings">
    <div class="title">检测发现</div>
    <ul>
      <li class="finding">
        <div class="type">历史相似度比对</div>
        <div class="detail">{{ historicalFinding || '暂无' }}</div>
      </li>
      <li v-for="(f, idx) in aiFindings" :key="idx" class="finding">
        <div class="type">{{ f.type || 'AI发现' }}</div>
        <div class="detail">{{ f.detail || '' }}</div>
      </li>
      <li v-if="aiFindings.length === 0" class="finding empty">暂无 AI 发现</li>
    </ul>
  </div>
</template>

<script setup>
defineProps({
  historicalFinding: { type: String, default: '' },
  aiFindings: { type: Array, default: () => [] }
})
</script>

<style scoped>
.title { font-weight: 600; margin-bottom: 8px; }
.findings { background: #fff; border: 1px solid var(--border-color); border-radius: 8px; padding: 12px; }
ul { list-style: none; padding: 0; margin: 0; }
.finding { padding: 8px 0; border-bottom: 1px solid #f0f0f0; }
.finding:last-child { border-bottom: 0; }
.type { font-weight: 600; color: var(--text-color); }
.detail { color: var(--text-light-color); margin-top: 4px; white-space: pre-wrap; }
.empty { color: var(--text-light-color); font-style: italic; }
</style>

