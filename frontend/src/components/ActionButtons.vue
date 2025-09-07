<template>
  <div class="actions">
    <el-button 
      type="danger" 
      :disabled="status !== 'pending_review'"
      @click="$emit('confirm-forgery')"
    >确认伪造并归档</el-button>
    <el-button 
      type="success" 
      :disabled="status !== 'pending_review'"
      @click="$emit('mark-safe')"
    >标记为无风险</el-button>
  </div>
</template>

<script setup>
defineProps({
  status: { type: String, default: '' }
})
</script>

<style scoped>
.actions { display: flex; gap: 12px; }
</style>

