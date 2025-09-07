<template>
  <div class="container">
    <div class="page-header">
      <h2>案例库</h2>
      <div class="actions">
        <el-radio-group v-model="viewMode" size="small">
          <el-radio-button label="gallery">图墙</el-radio-button>
          <el-radio-button label="list">列表</el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <!-- 统计信息已移除，根据需求简化页面 -->

    <div class="card">
      <!-- 筛选栏 -->
      <CaseFilterBar
        :forgery-type-options="forgeryTypeOptions"
        :loading="loading"
        @change="handleFilterChange"
        @reset="handleReset"
      />

      <!-- 内容区域 -->
      <div class="content-area">
        <template v-if="viewMode === 'gallery'">
          <div v-if="cases.length" class="gallery-grid">
            <CaseCard
              v-for="item in cases"
              :key="item.case_id"
              :item="item"
              @click="openDetail(item.case_id)"
            />
          </div>
          <el-empty v-else-if="!loading" description="暂无案例" :image-size="120" />
        </template>

        <template v-else>
          <el-table :data="cases" v-loading="loading" style="width: 100%">
            <el-table-column label="缩略图" width="120">
              <template #default="{ row }">
                <img v-if="row.image_url" :src="row.image_url" class="thumb" />
                <span v-else class="text-placeholder">无图</span>
              </template>
            </el-table-column>
            <el-table-column prop="case_id" label="案例ID" width="140" />
            <el-table-column prop="source_task_id" label="来源任务" width="140" />
            <el-table-column label="伪造类型" min-width="180">
              <template #default="{ row }">
                <el-tag v-for="t in row.forgery_types" :key="t" style="margin-right: 6px">{{ t }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="置信度" width="120">
              <template #default="{ row }">
                <el-rate v-if="row.confidence_score != null" :model-value="row.confidence_score * 5" disabled allow-half />
                <span v-else class="text-placeholder">-</span>
              </template>
            </el-table-column>
            <el-table-column label="时间" width="180">
              <template #default="{ row }">{{ formatDateTime(row.confirmed_at) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-link type="primary" @click="openDetail(row.case_id)">查看</el-link>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!loading && cases.length === 0" description="暂无案例" :image-size="120" />
        </template>
      </div>

      <!-- 分页 -->
      <div v-if="total > 0" class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>

    <CaseDetailModal
      v-if="detailVisible"
      :visible="detailVisible"
      :case-id="activeCaseId"
      @update:visible="detailVisible = $event"
    />
  </div>
  
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { caseAPI } from '../utils/api'
import { formatDateTime } from '../utils/constants'
import CaseCard from '../components/CaseCard.vue'
import CaseFilterBar from '../components/CaseFilterBar.vue'
import CaseDetailModal from '../components/CaseDetailModal.vue'

const loading = ref(false)
const cases = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const viewMode = ref('gallery')
const forgeryTypeOptions = ref([])
const filters = reactive({
  types: [],
  search: '',
  dateRange: []
})

const detailVisible = ref(false)
const activeCaseId = ref('')

const fetchTypes = async () => {
  try {
    const list = await caseAPI.getForgeryTypes()
    forgeryTypeOptions.value = list.map(i => ({ label: i.label, value: i.value }))
  } catch (e) {
    // ignore
  }
}

const fetchCases = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value,
      sort_by: 'confirmed_at',
      sort_order: 'desc'
    }
    if (filters.search) params.search_term = filters.search
    if (filters.types && filters.types.length === 1) params.forgery_type = filters.types[0]
    if (filters.dateRange && filters.dateRange.length === 2) {
      params.date_from = filters.dateRange[0]
      params.date_to = filters.dateRange[1]
    }
    const res = await caseAPI.getCases(params)
    cases.value = res.items || []
    total.value = res.total || 0
  } catch (e) {
    ElMessage.error('获取案例失败')
  } finally {
    loading.value = false
  }
}

const handleFilterChange = (payload) => {
  filters.types = payload.types
  filters.search = payload.search
  filters.dateRange = payload.dateRange
  currentPage.value = 1
  fetchCases()
}

const handleReset = () => {
  filters.types = []
  filters.search = ''
  filters.dateRange = []
  currentPage.value = 1
  fetchCases()
}

const handleCurrentChange = (page) => {
  currentPage.value = page
  fetchCases()
}

const handleSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
  fetchCases()
}

const openDetail = (caseId) => {
  activeCaseId.value = caseId
  detailVisible.value = true
}

onMounted(() => {
  fetchTypes()
  fetchCases()
})
</script>

<style scoped>
.container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  background: white;
  padding: 24px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  border: 1px solid #E4E7ED;
  animation: fadeInUp 0.6s ease-out;
}

.page-header h2 {
  margin: 0;
  color: #303133;
  font-size: 24px;
  font-weight: 600;
  position: relative;
}

/* 统计展示已移除 */

.card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  border: 1px solid #E4E7ED;
  overflow: hidden;
  animation: fadeInUp 0.6s ease-out 0.1s both;
}

.content-area { padding: 16px; }

.gallery-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
}

.thumb {
  width: 80px;
  height: 60px;
  object-fit: cover;
  border-radius: 4px;
  border: 1px solid #eee;
}

.text-placeholder { color: #C0C4CC; }

.pagination-wrapper {
  padding: 16px;
  display: flex;
  justify-content: center;
  border-top: 1px solid #E4E7ED;
}

/* 动画效果 */
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
