import { createRouter, createWebHistory } from 'vue-router'
import WorkOrderList from '@/views/WorkOrderList.vue'
import CreateWorkOrder from '@/views/CreateWorkOrder.vue'
import Reconciliation from '@/views/Reconciliation.vue'

const routes = [
  {
    path: '/',
    name: 'WorkOrderList',
    component: WorkOrderList,
  },
  {
    path: '/create',
    name: 'CreateWorkOrder',
    component: CreateWorkOrder,
  },
  {
    path: '/reconciliation',
    name: 'Reconciliation',
    component: Reconciliation,
  },
  // Redirect any unknown routes to home
  {
    path: '/:pathMatch(.*)*',
    redirect: '/',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router