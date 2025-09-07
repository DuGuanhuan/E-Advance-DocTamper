<template>
  <header class="app-header">
    <h1>智能图像鉴伪辅助平台</h1>
    <nav>
      <router-link to="/" :class="{ active: $route.name === 'TaskList' }">
        审核任务
      </router-link>
      <router-link to="/cases" :class="{ active: $route.name === 'CaseLibrary' }">
        案例库
      </router-link>
      <a href="#" class="nav-link">个人中心</a>
    </nav>
  </header>
</template>

<script setup>
// 无需额外逻辑
</script>

<style scoped>
.app-header {
  background-color: #fff;
  padding: 16px 24px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.app-header h1 {
  color: var(--primary-color);
  font-size: 24px;
  margin: 0;
}

nav {
  display: flex;
  align-items: center;
}

nav a {
  color: var(--text-light-color);
  text-decoration: none;
  margin-left: 20px;
  font-weight: 500;
  padding-bottom: 4px;
  transition: all 0.3s;
}

nav a:hover {
  color: var(--primary-color);
}

nav a.active {
  color: var(--primary-color);
  border-bottom: 2px solid var(--primary-color);
}

.nav-link {
  color: var(--text-light-color);
  text-decoration: none;
  margin-left: 20px;
  font-weight: 500;
}
</style>