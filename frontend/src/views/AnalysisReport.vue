<template>
  <div class="container">
    <div class="page-header">
      <h2>分析报告</h2>
      <el-button @click="$router.go(-1)">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
    </div>

    <div class="card">
      <el-result
        icon="info"
        title="分析报告页面"
        sub-title="此页面将在后续阶段实现"
      >
        <template #extra>
          <p>任务ID: {{ $route.params.taskId }}</p>
          <el-button type="primary" @click="$router.push('/')">
            返回任务列表
          </el-button>
        </template>
      </el-result>
    </div>
  </div>
</template>

<script setup>
import { ArrowLeft } from '@element-plus/icons-vue'
</script>
