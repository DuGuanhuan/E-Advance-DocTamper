<template>
  <div id="app">
    <AppHeader />
    <router-view />
  </div>
</template>

<script setup>
import AppHeader from './components/AppHeader.vue'
</script>

<style>
#app {
  min-height: 100vh;
  background-color: var(--secondary-color);
}
</style>