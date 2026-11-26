import { createRouter, createWebHistory } from 'vue-router'
import WorkOrderList from '@/views/WorkOrderList.vue'
import CreateWorkOrder from '@/views/CreateWorkOrder.vue'
import Reconciliation from '@/views/Reconciliation.vue'
import Clients from '@/views/Clients.vue'

import CustomerProgress from '@/views/CustomerProgress.vue'

const routes = [
  {path:'/progress', component: CustomerProgress},
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
  {
    path: '/clients',
    name: 'Clients',
    component: Clients,
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
