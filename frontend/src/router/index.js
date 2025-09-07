import { createRouter, createWebHistory } from 'vue-router'
import TaskList from '../views/TaskList.vue'

const routes = [
  {
    path: '/',
    name: 'TaskList',
    component: TaskList
  },
  {
    path: '/report/:taskId',
    name: 'AnalysisReport',
    component: () => import('../views/AnalysisReport.vue')
  },
  {
    path: '/cases',
    name: 'CaseLibrary',
    component: () => import('../views/CaseLibrary.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router